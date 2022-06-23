from unittest.mock import Mock

import pandas as pd
import pandas.api.types as ptypes
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

from ezyquant.report import SETBacktestReport, position_columns
from tests import utils

position_in_columns = ["timestamp", "symbol", "volume", "avg_cost_price"]


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
    srs = SETBacktestReport(
        initial_capital=0.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=pd.Series(),
        position_df=position_df,
        trade_df=pd.DataFrame(),
    )
    srs._sdr.get_data_symbol_daily = Mock(return_value=close_price_df)

    # Test
    result = srs.position_df

    # Check
    _check_position_df(result)
    assert_frame_equal(result, expect_result, check_dtype=False)  # type: ignore


def _check_position_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(position_columns))

    # Data type
    if not df.empty:
        assert ptypes.is_datetime64_any_dtype(df["timestamp"])
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["avg_cost_price"])
        assert ptypes.is_float_dtype(df["close_price"])
        assert ptypes.is_float_dtype(df["close_value"])

    # Value
    assert (df["volume"] > 0).all()
    assert (df["avg_cost_price"] > 0).all()
    assert (df["close_price"] > 0).all()
    assert (df["close_value"] > 0).all()
