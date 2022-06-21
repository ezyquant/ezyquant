from datetime import datetime

import numpy as np

import ezyquant as ez
from ezyquant import SETSignalCreator, backtest
from ezyquant.backtest.account import SETAccount

ez.connect_sqlite("psims.db")

start_date = "2010-01-01"
end_date = "2019-12-31"

#%% create signal
ssc = SETSignalCreator(
    start_date=start_date,
    end_date=end_date,
    index_list=["SET100"],
)
pe_df = ssc.get_data("pe", "daily")
pe_df *= ssc.is_universe("SET100")
pe_df = pe_df.replace(0, np.nan)

signal_df = (pe_df.rank(axis=1, method="max") <= 10) / 10.00001


def apply_trade_volume(
    ts: datetime, symbol: str, signal: float, close_price: float, acct: SETAccount
):
    return acct.target_pct_port(signal)


#%% Backtest
initial_cash = 1e6

result = backtest(
    signal_df=signal_df,
    apply_trade_volume=apply_trade_volume,
    start_date=start_date,
    end_date=end_date,
    initial_cash=initial_cash,
)

print(result.stat_df)
