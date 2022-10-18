import pandas as pd
import pandas.api.types as ptypes
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

import ezyquant.fields as fld
from ezyquant.report import SETBacktestReport, trade_columns

trade_in_columns = ["matched_at", "symbol", "volume", "price", "pct_commission"]


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
                    [pd.Timestamp("2000-01-03"), "AAA", fld.SIDE_BUY, 100.0, 0.1, 0.1],
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
                    [pd.Timestamp("2000-01-03"), "AAA", fld.SIDE_BUY, 100.0, 0.1, 0.1],
                    [pd.Timestamp("2000-01-04"), "AAA", fld.SIDE_SELL, 100.0, 0.1, 0.1],
                ],
                columns=trade_columns,
            ),
        ),
    ],
)
def test_trade_df(trade_df: pd.DataFrame, expect_result: pd.DataFrame):
    # Mock
    sbr = SETBacktestReport(
        initial_capital=0.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=pd.Series(),
        position_df=pd.DataFrame(),
        trade_df=trade_df,
    )

    # Test
    result = sbr.trade_df

    # Check
    _check_trade_df(result)
    assert_frame_equal(result, expect_result, check_dtype=False)


def _check_trade_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(trade_columns))

    # Data type
    if not df.empty:
        assert ptypes.is_datetime64_any_dtype(df["matched_at"])
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_string_dtype(df["side"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["price"])
        assert ptypes.is_float_dtype(df["commission"])

    # Value
    assert (df["volume"] > 0).all()
    assert (df["price"] > 0).all()
    assert (df["commission"] >= 0).all()
