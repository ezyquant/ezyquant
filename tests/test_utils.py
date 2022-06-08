from typing import List

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from ezyquant import utils


class TestIsRebalanceWeekly:
    @pytest.mark.parametrize(
        ("trade_date_index", "rebalance_day", "expected_result"),
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
                [True, True, False, False, False, False, True, False, False, False],
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
                [True, True, False, False, False, False, True, False, False],
            ),
        ],
    )
    def test_normal(
        self,
        trade_date_index: pd.DatetimeIndex,
        rebalance_day: int,
        expected_result: List[bool],
    ):
        result = utils.is_rebalance_weekly(
            trade_date_index=trade_date_index,
            rebalance_day=rebalance_day,
        )

        # Check
        expected_s = pd.Series(expected_result, index=trade_date_index)
        assert_series_equal(result, expected_s)

    @pytest.mark.parametrize(
        "trade_date_index",
        [
            pd.DatetimeIndex(["2021-01-01"]),
            pd.bdate_range("2021-01-01", "2021-01-31"),
            pd.bdate_range("2021-01-01", "2021-12-31"),
        ],
    )
    @pytest.mark.parametrize("rebalance_day", [1, 2, 3, 4, 5])
    def test_no_holiday(self, trade_date_index: pd.DatetimeIndex, rebalance_day: int):
        result = utils.is_rebalance_weekly(
            trade_date_index=trade_date_index,
            rebalance_day=rebalance_day,
        )

        # Check
        dayofweek_s = pd.Series(
            trade_date_index.dayofweek,  # type:ignore
            index=trade_date_index,
        )
        expected_s = dayofweek_s == rebalance_day - 1
        expected_s.iloc[0] = True
        assert_series_equal(result, expected_s)
