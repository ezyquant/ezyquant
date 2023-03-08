import copy
import string
from typing import List, Tuple
from unittest.mock import Mock, call

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from ezyquant import utils


@pytest.mark.parametrize("base", [10, 10.0])
@pytest.mark.parametrize(
    ("value", "expect_result"),
    [(-10, -10), (-9.0, 0), (-1.0, 0), (0, 0), (1.0, 0), (9.0, 0), (10, 10)],
)
def test_round_down(value, base, expect_result):
    assert utils.round_down(value, base) == expect_result


class TestIsRebalanceWeekly:
    @pytest.mark.parametrize(
        ("trade_date_index", "rebalance_at", "expected_rebalance_date_index"),
        [
            (
                pd.DatetimeIndex(
                    [
                        "2021-01-04",  # Monday
                        "2021-01-05",  # Tuesday
                        "2021-01-06",  # Wednesday
                        "2021-01-07",  # Thursday
                        "2021-01-08",  # Friday
                        "2021-01-11",  # Monday
                        "2021-01-12",  # Tuesday
                        "2021-01-13",  # Wednesday
                        "2021-01-14",  # Thursday
                        "2021-01-15",  # Friday
                    ]
                ),
                2,
                pd.DatetimeIndex(
                    [
                        "2021-01-04",  # Monday
                        "2021-01-05",  # Tuesday
                        "2021-01-12",  # Tuesday
                    ]
                ),
            ),
            (
                pd.DatetimeIndex(
                    [
                        "2021-01-04",  # Monday
                        "2021-01-05",  # Tuesday
                        "2021-01-06",  # Wednesday
                        "2021-01-07",  # Thursday
                        "2021-01-08",  # Friday
                        "2021-01-11",  # Monday
                        # "2021-01-12",  # Assume not trade date
                        "2021-01-13",  # Wednesday
                        "2021-01-14",  # Thursday
                        "2021-01-15",  # Friday
                    ]
                ),
                2,
                pd.DatetimeIndex(
                    [
                        "2021-01-04",  # Monday
                        "2021-01-05",  # Tuesday
                        "2021-01-13",  # Wednesday
                    ]
                ),
            ),
        ],
    )
    def test_simple(
        self,
        trade_date_index: pd.DatetimeIndex,
        rebalance_at: int,
        expected_rebalance_date_index: pd.DatetimeIndex,
    ):
        result = utils.is_rebalance_weekly(
            trade_date_index=trade_date_index,
            rebalance_at=rebalance_at,
        )

        # Check
        expected_result = trade_date_index.to_series().isin(
            expected_rebalance_date_index
        )
        assert_series_equal(result, expected_result)

    @pytest.mark.parametrize(
        "trade_date_index",
        [
            pd.DatetimeIndex(["2021-01-01"]),
            pd.bdate_range("2021-01-01", "2021-01-31"),
            pd.bdate_range("2021-01-01", "2021-12-31"),
        ],
    )
    @pytest.mark.parametrize("rebalance_at", [1, 2, 3, 4, 5])
    def test_no_holiday(self, trade_date_index: pd.DatetimeIndex, rebalance_at: int):
        result = utils.is_rebalance_weekly(
            trade_date_index=trade_date_index,
            rebalance_at=rebalance_at,
        )

        # Check
        dayofweek_s = pd.Series(
            trade_date_index.dayofweek,  # type:ignore
            index=trade_date_index,
        )
        expected_s = (dayofweek_s == rebalance_at - 1) | (
            dayofweek_s.index == dayofweek_s.index.min()
        )
        assert_series_equal(result, expected_s)


class TestIsRebalanceMonthly:
    @pytest.mark.parametrize(
        ("trade_date_index", "rebalance_at", "expected_rebalance_date_index"),
        [
            (
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-01-02",
                        "2021-01-03",
                        "2021-01-04",
                        "2021-01-05",
                        "2021-01-06",
                    ]
                ),
                5,
                pd.DatetimeIndex(["2021-01-01", "2021-01-05"]),
            ),
            (
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-01-02",
                        "2021-01-03",
                        "2021-01-04",
                        # "2021-01-05",
                        "2021-01-06",
                    ]
                ),
                5,
                pd.DatetimeIndex(["2021-01-01", "2021-01-06"]),
            ),
            (
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-01-02",
                        "2021-01-03",
                        # "2021-01-04",
                        # "2021-01-05",
                        "2021-01-06",
                    ]
                ),
                5,
                pd.DatetimeIndex(["2021-01-01", "2021-01-06"]),
            ),
            (
                pd.bdate_range("2021-01-01", "2021-12-31"),
                1,
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-02-01",
                        "2021-03-01",
                        "2021-04-01",
                        "2021-05-03",
                        "2021-06-01",
                        "2021-07-01",
                        "2021-08-02",
                        "2021-09-01",
                        "2021-10-01",
                        "2021-11-01",
                        "2021-12-01",
                    ]
                ),
            ),
            (
                pd.bdate_range("2021-01-01", "2021-06-01"),
                15,
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-01-15",
                        "2021-02-15",
                        "2021-03-15",
                        "2021-04-15",
                        "2021-05-17",
                    ]
                ),
            ),
            (
                pd.bdate_range("2021-01-01", "2021-06-01"),
                28,
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-01-28",
                        "2021-03-01",
                        "2021-03-29",
                        "2021-04-28",
                        "2021-05-28",
                    ]
                ),
            ),
            (
                pd.bdate_range("2016-01-01", "2016-06-01"),  # leap year
                29,
                pd.DatetimeIndex(
                    [
                        "2016-01-01",
                        "2016-01-29",
                        "2016-02-29",
                        "2016-03-29",
                        "2016-04-29",
                        "2016-05-30",
                    ]
                ),
            ),
            (
                pd.bdate_range("2021-01-01", "2021-06-01"),
                30,
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-02-01",
                        "2021-03-01",
                        "2021-03-30",
                        "2021-04-30",
                        "2021-05-31",
                    ]
                ),
            ),
            (
                pd.bdate_range("2021-01-01", "2021-06-01"),
                31,
                pd.DatetimeIndex(
                    [
                        "2021-01-01",
                        "2021-02-01",
                        "2021-03-01",
                        "2021-03-31",
                        "2021-05-03",
                        "2021-05-31",
                    ]
                ),
            ),
        ],
    )
    def test_simple(
        self,
        trade_date_index: pd.DatetimeIndex,
        rebalance_at: int,
        expected_rebalance_date_index: pd.DatetimeIndex,
    ):
        result = utils.is_rebalance_monthly(
            trade_date_index=trade_date_index,
            rebalance_at=rebalance_at,
        )

        # Check
        expected_result = trade_date_index.to_series().isin(
            expected_rebalance_date_index
        )
        assert_series_equal(result, expected_result)

    @pytest.mark.parametrize(
        "trade_date_index",
        [
            pd.DatetimeIndex(["2021-01-01"]),
            pd.date_range("2021-01-01", "2021-01-31"),
            pd.date_range("2021-01-01", "2021-12-31"),
        ],
    )
    @pytest.mark.parametrize("rebalance_at", [1, 2, 28])
    def test_no_weekend(self, trade_date_index: pd.DatetimeIndex, rebalance_at: int):
        result = utils.is_rebalance_monthly(
            trade_date_index=trade_date_index,
            rebalance_at=rebalance_at,
        )

        # Check
        day_s = pd.Series(
            trade_date_index.day,  # type:ignore
            index=trade_date_index,
        )
        expected_s = (day_s == rebalance_at) | (day_s.index == day_s.index.min())
        assert_series_equal(result, expected_s)


@pytest.mark.parametrize(
    ("series", "expect_result"),
    [
        (pd.Series([], dtype=bool), pd.Series([], dtype="int64")),
        (pd.Series([False]), pd.Series([0])),
        (pd.Series([True]), pd.Series([1])),
        (pd.Series([False, False]), pd.Series([0, 0])),
        (pd.Series([False, True]), pd.Series([0, 1])),
        (pd.Series([True, False]), pd.Series([1, 0])),
        (pd.Series([True, True]), pd.Series([1, 2])),
        (pd.Series([False, False, False]), pd.Series([0, 0, 0])),
        (pd.Series([False, False, True]), pd.Series([0, 0, 1])),
        (pd.Series([False, True, False]), pd.Series([0, 1, 0])),
        (pd.Series([False, True, True]), pd.Series([0, 1, 2])),
        (pd.Series([True, False, False]), pd.Series([1, 0, 0])),
        (pd.Series([True, False, True]), pd.Series([1, 0, 1])),
        (pd.Series([True, True, False]), pd.Series([1, 2, 0])),
        (pd.Series([True, True, True]), pd.Series([1, 2, 3])),
    ],
)
def test_count_true_consecutive(series: pd.Series, expect_result: pd.Series):
    result = utils.count_true_consecutive(series)
    assert_series_equal(result, expect_result)


@pytest.mark.parametrize(
    ("series", "expect_result"),
    [
        (pd.Series([], dtype=bool), 0),
        (pd.Series([False]), 0),
        (pd.Series([True]), 1),
        (pd.Series([False, False]), 0),
        (pd.Series([False, True]), 1),
        (pd.Series([True, False]), 1),
        (pd.Series([True, True]), 2),
        (pd.Series([False, False, False]), 0),
        (pd.Series([False, False, True]), 1),
        (pd.Series([False, True, False]), 1),
        (pd.Series([False, True, True]), 2),
        (pd.Series([True, False, False]), 1),
        (pd.Series([True, False, True]), 1),
        (pd.Series([True, True, False]), 2),
        (pd.Series([True, True, True]), 3),
    ],
)
def test_count_max_true_consecutive(series: pd.Series, expect_result):
    result = utils.count_max_true_consecutive(series)
    assert result == expect_result


class TestWrapCacheClass:
    def _test(
        self,
        args1: tuple = tuple(),
        kwargs1: dict = dict(),
        args2: tuple = tuple(),
        kwargs2: dict = dict(),
        expect_call_count: int = 1,
    ):
        # Mock
        m = Mock(return_value=pd.DataFrame())

        class A:
            def m1(self, *args, **kwargs):
                return m()

        # Test
        A1 = utils.wrap_cache_class(A)

        a: A = A1()  # type: ignore

        r1 = a.m1(*args1, **kwargs1)
        r2 = a.m1(*args2, **kwargs2)

        # Check
        assert_frame_equal(r1, r2)
        assert id(r1) != id(r2)
        assert m.call_count == expect_call_count

    def test_no_param(self):
        self._test()

    @pytest.mark.parametrize(
        "args",
        [(None,), (1,), ("A",), ("A", "A"), (True,), ([],), (["A"],), (["A", "B"],)],
    )
    def test_same_param(self, args: tuple):
        # args
        self._test(
            args1=copy.deepcopy(args), args2=copy.deepcopy(args), expect_call_count=1
        )

        # kwargs
        kwargs = {string.ascii_lowercase[i]: args[i] for i in range(len(args))}
        self._test(
            kwargs1=copy.deepcopy(kwargs),
            kwargs2=copy.deepcopy(kwargs),
            expect_call_count=1,
        )

    @pytest.mark.parametrize(
        ("args1", "args2", "expect_call_count"),
        [
            ((1,), (1.0,), 1),
            ((1,), ("1",), 2),
            ((1,), (2,), 2),
            ((["A", "B"],), (["B", "A"],), 1),
            ((1, 1), (1, 2), 2),
        ],
    )
    def test_diff_args(self, args1: tuple, args2: tuple, expect_call_count: int):
        self._test(args1=args1, args2=args2, expect_call_count=expect_call_count)

        # kwargs
        kwargs1 = {string.ascii_lowercase[i]: args1[i] for i in range(len(args1))}
        kwargs2 = {string.ascii_lowercase[i]: args2[i] for i in range(len(args2))}
        self._test(
            kwargs1=kwargs1, kwargs2=kwargs2, expect_call_count=expect_call_count
        )


class TestCacheDataframeWrapper:
    @pytest.mark.parametrize(
        ("field_list", "expected_field_list"),
        [
            (["A"], ["A"]),
            (["A", "B"], ["A", "B"]),
            (["A", "A"], ["A"]),
        ],
    )
    def test_field(self, field_list: List[str], expected_field_list: List[str]):
        # Mock
        m = Mock(return_value=pd.DataFrame())

        # Test
        func = utils.cache_dataframe_wrapper(utils.cache_wrapper(m))
        for i in field_list:
            result = func(field=i)
            # Check
            assert_frame_equal(result, pd.DataFrame())

        # Check
        m.assert_has_calls(
            [
                call(
                    field=i,
                    symbol_list=None,
                    start_date=None,
                    end_date=None,
                )
                for i in expected_field_list
            ]
        )

    @pytest.mark.parametrize(
        ("symbol_lists", "expected_symbol_lists"),
        [
            ([None, None], [None]),
            ([None, ["AAA"]], [None]),
            ([None, ["AAA", "AAB"]], [None]),
            ([None, ["AAB", "AAA"]], [None]),
            ([["AAA"], None], [("AAA",), None]),
            ([["AAA"], ["AAA"]], [("AAA",)]),
            ([["AAA"], ["AAA", "AAB"]], [("AAA",), ("AAA", "AAB")]),
            ([["AAA"], ["AAB", "AAA"]], [("AAA",), ("AAA", "AAB")]),
            ([["AAA", "AAB"], None], [("AAA", "AAB"), None]),
            ([["AAA", "AAB"], ["AAA"]], [("AAA", "AAB")]),
            ([["AAA", "AAB"], ["AAA", "AAB"]], [("AAA", "AAB")]),
            ([["AAA", "AAB"], ["AAB", "AAA"]], [("AAA", "AAB")]),
            ([["AAB", "AAA"], None], [("AAA", "AAB"), None]),
            ([["AAB", "AAA"], ["AAA"]], [("AAA", "AAB")]),
            ([["AAB", "AAA"], ["AAA", "AAB"]], [("AAA", "AAB")]),
            ([["AAB", "AAA"], ["AAB", "AAA"]], [("AAA", "AAB")]),
        ],
    )
    def test_symbol_list(
        self, symbol_lists: List[List[str]], expected_symbol_lists: List[Tuple[str]]
    ):
        # Mock
        field = "A"
        df_none = pd.DataFrame(columns=["AAA", "AAB", "AAC"])
        m = Mock(
            side_effect=[
                pd.DataFrame(columns=list(i)) if i is not None else df_none.copy()
                for i in expected_symbol_lists
            ]
        )

        # Test
        func = utils.cache_dataframe_wrapper(utils.cache_wrapper(m))
        for i in symbol_lists:
            result = func(field=field, symbol_list=i)
            # Check
            assert_frame_equal(
                result,
                pd.DataFrame(columns=i) if i is not None else df_none.copy(),
            )

        # Check
        m.assert_has_calls(
            [
                call(
                    field=field,
                    symbol_list=i,
                    start_date=None,
                    end_date=None,
                )
                for i in expected_symbol_lists
            ]
        )

    @pytest.mark.parametrize(
        ("start_date_list", "expected_start_date_list"),
        [
            ([None, None], [None]),
            ([None, "2000-01-01"], [None]),
            ([None, "2000-01-02"], [None]),
            (["2000-01-01", None], ["2000-01-01", None]),
            (["2000-01-01", "2000-01-01"], ["2000-01-01"]),
            (["2000-01-01", "2000-01-02"], ["2000-01-01"]),
            (["2000-01-02", None], ["2000-01-02", None]),
            (["2000-01-02", "2000-01-01"], ["2000-01-02", "2000-01-01"]),
            (["2000-01-02", "2000-01-02"], ["2000-01-02"]),
        ],
    )
    def test_start_date(
        self,
        start_date_list: List[str],
        expected_start_date_list: List[str],
    ):
        # Mock
        field = "A"
        df_none = pd.DataFrame(index=pd.bdate_range(start="2000-01-01", periods=4))
        m = Mock(
            side_effect=[
                pd.DataFrame(index=pd.bdate_range(start=i, periods=4))
                if i is not None
                else df_none.copy()
                for i in expected_start_date_list
            ]
        )

        # Test
        func = utils.cache_dataframe_wrapper(utils.cache_wrapper(m))
        for i in start_date_list:
            result = func(field=field, start_date=i)
            # Check
            assert_frame_equal(
                result,
                pd.DataFrame(index=pd.bdate_range(start=i, periods=4))
                if i is not None
                else df_none.copy(),
            )

        # Check
        m.assert_has_calls(
            [
                call(
                    field=field,
                    symbol_list=None,
                    start_date=i,
                    end_date=None,
                )
                for i in expected_start_date_list
            ]
        )

    @pytest.mark.parametrize(
        ("end_date_list", "expected_end_date_list"),
        [
            ([None, None], [None]),
            ([None, "2000-01-01"], [None]),
            ([None, "2000-01-02"], [None]),
            (["2000-01-01", None], ["2000-01-01", None]),
            (["2000-01-01", "2000-01-01"], ["2000-01-01"]),
            (["2000-01-01", "2000-01-02"], ["2000-01-01", "2000-01-02"]),
            (["2000-01-02", None], ["2000-01-02", None]),
            (["2000-01-02", "2000-01-01"], ["2000-01-02"]),
            (["2000-01-02", "2000-01-02"], ["2000-01-02"]),
        ],
    )
    def test_end_date(
        self,
        end_date_list: List[str],
        expected_end_date_list: List[str],
    ):
        # Mock
        field = "A"
        df_none = pd.DataFrame(index=pd.bdate_range(end="2000-01-01", periods=4))
        m = Mock(
            side_effect=[
                pd.DataFrame(index=pd.bdate_range(end=i, periods=4))
                if i is not None
                else df_none.copy()
                for i in expected_end_date_list
            ]
        )

        # Test
        func = utils.cache_dataframe_wrapper(utils.cache_wrapper(m))
        for i in end_date_list:
            result = func(field=field, end_date=i)
            # Check
            assert_frame_equal(
                result,
                pd.DataFrame(index=pd.bdate_range(end=i, periods=4))
                if i is not None
                else df_none.copy(),
            )

        # Check
        m.assert_has_calls(
            [
                call(
                    field=field,
                    symbol_list=None,
                    start_date=None,
                    end_date=i,
                )
                for i in expected_end_date_list
            ]
        )
