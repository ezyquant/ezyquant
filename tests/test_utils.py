import copy
import string
from unittest.mock import Mock

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from ezyquant import utils


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
