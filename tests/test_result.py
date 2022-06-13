from unittest.mock import Mock

import pandas as pd
import pytest
import utils
from pandas.testing import assert_frame_equal

from ezyquant.result import SETResult, position_columns, trade_columns

position_in_columns = ["timestamp", "symbol", "volume", "avg_cost_price"]
trade_in_columns = ["timestamp", "symbol", "volume", "price", "pct_commission"]


@pytest.mark.parametrize(
    "close_price_df",
    [
        utils.make_data_df(
            [[1.0, 4.0, 7.0], [2.0, 5.0, 8.0], [3.0, 6.0, 9.0]], n_col=3, n_row=3
        )
    ],
)
@pytest.mark.parametrize(
    ("position_df", "expect_result"),
    [
        (
            pd.DataFrame(columns=position_in_columns),
            pd.DataFrame(columns=position_columns),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1],
                ],
                columns=position_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0],
                ],
                columns=position_columns,
            ),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1],
                ],
                columns=position_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0],
                    [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1, 2.0, 200.0],
                ],
                columns=position_columns,
            ),
        ),
    ],
)
def test_position_df(
    position_df: pd.DataFrame, close_price_df: pd.DataFrame, expect_result: pd.DataFrame
):
    # Mock
    srs = SETResult(
        cash_series=pd.Series(),
        position_df=position_df,
        trade_df=pd.DataFrame(),
    )
    srs._sdr.get_data_symbol_daily = Mock(return_value=close_price_df)

    # Test
    result = srs.position_df

    # Check
    assert_frame_equal(result, expect_result, check_dtype=False)  # type: ignore


@pytest.mark.parametrize(
    ("trade_df", "expect_result"),
    [
        (
            pd.DataFrame(columns=trade_in_columns),
            pd.DataFrame(columns=trade_columns),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 0.01],
                ],
                columns=trade_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", "buy", 100.0, 0.1, 0.1],
                ],
                columns=trade_columns,
            ),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 0.01],
                    [pd.Timestamp("2000-01-04"), "AAA", -100.0, 0.1, 0.01],
                ],
                columns=trade_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", "buy", 100.0, 0.1, 0.1],
                    [pd.Timestamp("2000-01-04"), "AAA", "sell", 100.0, 0.1, 0.1],
                ],
                columns=trade_columns,
            ),
        ),
    ],
)
def test_trade_df(trade_df: pd.DataFrame, expect_result: pd.DataFrame):
    # Mock
    srs = SETResult(
        cash_series=pd.Series(), position_df=pd.DataFrame(), trade_df=trade_df
    )

    # Test
    result = srs.trade_df

    # Check
    assert_frame_equal(result, expect_result, check_dtype=False)  # type: ignore


class TestMakeSummaryDf:
    # TODO: TestMakeSummaryDf
    pass
