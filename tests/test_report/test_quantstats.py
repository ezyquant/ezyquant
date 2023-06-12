import numpy as np
import pandas as pd
import pytest

from ezyquant.report import SETBacktestReport

trade_in_columns = ["matched_at", "symbol", "volume", "price", "pct_commission"]
date_range = pd.bdate_range(start="2000-01-03", periods=400)


@pytest.mark.parametrize(
    "cash_series",
    [pd.Series(np.random.rand(len(date_range)) + 100.0, index=date_range, name="cash")],
)
@pytest.mark.parametrize(
    "trade_df",
    [
        pd.DataFrame([], columns=trade_in_columns),
        pd.DataFrame(
            [[date, "AAA", 100.0, 0.1, 0.01] for date in date_range],
            columns=trade_in_columns,
        ),
    ],
)
@pytest.mark.parametrize("with_dividend", [True, False])
@pytest.mark.parametrize(
    "benchmark",
    [
        None,
        pd.Series(
            np.random.rand(len(date_range)) + 100.0, index=date_range, name="benchmark"
        ),
    ],
)
class TestQuantStats:
    def _sbr(self, cash_series: pd.Series, trade_df: pd.DataFrame):
        return SETBacktestReport(
            initial_capital=1.0,
            pct_commission=0.0,
            pct_buy_slip=0.0,
            pct_sell_slip=0.0,
            cash_series=cash_series,
            position_df=pd.DataFrame(),
            trade_df=trade_df,
        )

    def test_to_snapshot(
        self,
        cash_series: pd.Series,
        trade_df: pd.DataFrame,
        with_dividend: bool,
        benchmark: pd.DataFrame,
    ):
        sbr = self._sbr(cash_series, trade_df)

        sbr.to_snapshot(with_dividend=with_dividend)

    def test_to_html(
        self,
        cash_series: pd.Series,
        trade_df: pd.DataFrame,
        with_dividend: bool,
        benchmark: pd.DataFrame,
    ):
        sbr = self._sbr(cash_series, trade_df)

        sbr.to_html(with_dividend=with_dividend, benchmark=benchmark, output="")

    def test_to_basic(
        self,
        cash_series: pd.Series,
        trade_df: pd.DataFrame,
        with_dividend: bool,
        benchmark: pd.DataFrame,
    ):
        sbr = self._sbr(cash_series, trade_df)

        sbr.to_basic(with_dividend=with_dividend, benchmark=benchmark)

    def test_to_full(
        self,
        cash_series: pd.Series,
        trade_df: pd.DataFrame,
        with_dividend: bool,
        benchmark: pd.DataFrame,
    ):
        sbr = self._sbr(cash_series, trade_df)

        sbr.to_full(with_dividend=with_dividend, benchmark=benchmark)
