from unittest.mock import Mock, PropertyMock, patch

import pandas as pd
import pandas.api.types as ptypes
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

from ezyquant.report import SETBacktestReport, summary_columns
from tests import utils


class TestSummaryDf:
    def setup_method(self, _):
        self.position_df = SETBacktestReport.position_df
        self.trade_df = SETBacktestReport.trade_df
        self.dividend_df = SETBacktestReport.dividend_df

    def teardown_method(self, _):
        SETBacktestReport.position_df = self.position_df
        SETBacktestReport.trade_df = self.trade_df
        SETBacktestReport.dividend_df = self.dividend_df

    @pytest.mark.kwparametrize(
        # Empty
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["matched_at", "commission"]),
            "dividend_df": pd.DataFrame(columns=["pay_date", "amount"]),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Position
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]],
                columns=["timestamp", "close_value"],
            ),
            "trade_df": pd.DataFrame(columns=["matched_at", "commission"]),
            "dividend_df": pd.DataFrame(columns=["pay_date", "amount"]),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 2.0, 2.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Trade
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]],
                columns=["matched_at", "commission"],
            ),
            "dividend_df": pd.DataFrame(columns=["pay_date", "amount"]),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]],
                columns=summary_columns,
            ),
        },
        # Dividend
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["matched_at", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 2.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Dividend non trade date
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["matched_at", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-02"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 2.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Dividend after cash
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["matched_at", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-04"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Cumulative dividend
        {
            "cash_series": pd.Series(
                {pd.Timestamp("2000-01-03"): 1.0, pd.Timestamp("2000-01-04"): 1.0}
            ),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["matched_at", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [
                    [
                        pd.Timestamp("2000-01-03"),
                        2.0,
                        1.0,
                        0.0,
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        0.0,
                    ],
                    [
                        pd.Timestamp("2000-01-04"),
                        2.0,
                        1.0,
                        0.0,
                        1.0,
                        0.0,
                        0.0,
                        1.0,
                        0.0,
                    ],
                ],
                columns=summary_columns,
            ),
        },
    )
    def test_summary_df(
        self,
        cash_series: pd.Series,
        position_df: pd.DataFrame,
        trade_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        # Mock
        sbr = SETBacktestReport(
            initial_capital=1.0,
            pct_commission=0.0,
            pct_buy_slip=0.0,
            pct_sell_slip=0.0,
            cash_series=cash_series,
            position_df=pd.DataFrame(),
            trade_df=pd.DataFrame(),
        )
        sbr._sdr.get_trading_dates = Mock(return_value=utils.make_trading_dates())

        # Test
        with patch(
            "ezyquant.report.SETBacktestReport.position_df", new_callable=PropertyMock
        ) as mock_position_df, patch(
            "ezyquant.report.SETBacktestReport.trade_df", new_callable=PropertyMock
        ) as mock_trade_df, patch(
            "ezyquant.report.SETBacktestReport.dividend_df", new_callable=PropertyMock
        ) as mock_dividend_df:
            mock_position_df.return_value = position_df
            mock_trade_df.return_value = trade_df
            mock_dividend_df.return_value = dividend_df

            result = sbr.summary_df

        # Check
        _check_summary_df(result)
        assert_frame_equal(result, expect_result)


def _check_summary_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(summary_columns))

    # Data type
    assert ptypes.is_datetime64_any_dtype(df["timestamp"])
    assert ptypes.is_float_dtype(df["port_value_with_dividend"])
    assert ptypes.is_float_dtype(df["port_value"])
    assert ptypes.is_float_dtype(df["total_market_value"])
    assert ptypes.is_float_dtype(df["cash"])
    assert ptypes.is_float_dtype(df["cashflow"])
    assert ptypes.is_float_dtype(df["dividend"])
    assert ptypes.is_float_dtype(df["cumulative_dividend"])
    assert ptypes.is_float_dtype(df["commission"])

    # Value
    assert (df["port_value_with_dividend"] >= 0).all()
    assert (df["port_value"] >= 0).all()
    assert (df["total_market_value"] >= 0).all()
    assert (df["cash"] >= 0).all()
    assert (df["dividend"] >= 0).all()
    assert (df["cumulative_dividend"] >= 0).all()
    assert (df["commission"] >= 0).all()

    assert df["cumulative_dividend"].is_monotonic_increasing

    assert not df.empty
