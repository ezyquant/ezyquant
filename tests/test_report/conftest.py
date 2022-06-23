import pandas as pd
import pytest

from ezyquant.report import SETBacktestReport


@pytest.fixture
def sbr():
    return _make_empty_backtest_report()


def _make_empty_backtest_report():
    return SETBacktestReport(
        initial_capital=0.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=pd.Series(),
        position_df=pd.DataFrame(),
        trade_df=pd.DataFrame(),
    )
