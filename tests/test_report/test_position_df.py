import pandas as pd
import pandas.api.types as ptypes
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

from ezyquant.report import SETBacktestReport, position_columns

position_in_columns = ["timestamp", "symbol", "volume", "cost_price", "close_price"]


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
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0],
                ],
                columns=position_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0, 9.0],
                ],
                columns=position_columns,
            ),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0],
                    [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1, 2.0],
                ],
                columns=position_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0, 9.0],
                    [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1, 2.0, 200.0, 19.0],
                ],
                columns=position_columns,
            ),
        ),
    ],
)
def test_position_df(position_df: pd.DataFrame, expect_result: pd.DataFrame):
    # Mock
    sbr = SETBacktestReport(
        initial_capital=0.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=pd.Series(),
        position_df=position_df,
        trade_df=pd.DataFrame(),
    )
    # Test
    result = sbr.position_df

    # Check
    _check_position_df(result)
    assert_frame_equal(result, expect_result, check_dtype=False)


def _check_position_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(position_columns))

    # Data type
    if not df.empty:
        assert ptypes.is_datetime64_any_dtype(df["timestamp"])
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["cost_price"])
        assert ptypes.is_float_dtype(df["close_price"])
        assert ptypes.is_float_dtype(df["close_value"])

    # Value
    assert (df["volume"] > 0).all()
    assert (df["cost_price"] > 0).all()
    assert (df["close_price"] > 0).all()
    assert (df["close_value"] > 0).all()
