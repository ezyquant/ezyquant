import numpy as np
import pandas as pd
import pytest

from ezyquant.report import SETBacktestReport

trade_in_columns = ["matched_at", "symbol", "volume", "price", "pct_commission"]
date_range = pd.bdate_range(start="2000-01-03", periods=30)


@pytest.mark.parametrize(
    ("cash_series", "trade_df"),
    [
        (
            pd.Series(1.0, index=date_range),
            pd.DataFrame(
                [[date, "AAA", 100.0, 0.1, 0.01] for date in date_range],
                columns=trade_in_columns,
            ),
        )
    ],
)
def test_generate_basic_with_dividend(cash_series: pd.Series, trade_df: pd.DataFrame):
    sbr = SETBacktestReport(
        initial_capital=1.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=cash_series,
        position_df=pd.DataFrame(),
        trade_df=trade_df,
    )

    sbr.to_basic(with_dividend=True)


@pytest.mark.parametrize(
    ("cash_series", "trade_df", "benchmark"),
    [
        (
            pd.Series(1.0, index=date_range),
            pd.DataFrame(
                [[date, "AAA", 100.0, 0.1, 0.01] for date in date_range],
                columns=trade_in_columns,
            ),
            pd.DataFrame(
                {"SET": [np.random.normal(0, 1) for _ in date_range]}, index=date_range
            ),
        )
    ],
)
def test_generate_basic_with_benchmark(
    cash_series: pd.Series, trade_df: pd.DataFrame, benchmark: pd.DataFrame
):
    sbr = SETBacktestReport(
        initial_capital=1.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=cash_series,
        position_df=pd.DataFrame(),
        trade_df=trade_df,
    )

    sbr.to_basic(with_dividend=False, benchmark=benchmark)
