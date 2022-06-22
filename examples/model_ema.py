from datetime import datetime

import pandas as pd

import ezyquant as ez
from ezyquant import SETSignalCreator, backtest
from ezyquant import utils as ezutils
from ezyquant.backtest.account import SETAccount
from ezyquant.reader import SETBusinessDay

ez.connect_sqlite("psims.db")

start_date = "2010-01-01"
start_load_date = ezutils.date_to_str(pd.Timestamp(start_date) - SETBusinessDay(20))
end_date = "2019-12-31"

#%% create signal
ssc = SETSignalCreator(
    start_date=start_load_date,
    end_date=end_date,
    index_list=["SET100"],
)

close_df = ssc.get_data("close", "daily")

ema10_df = ssc.ta.ema(close_df, 10)
ema20_df = ssc.ta.ema(close_df, 20)

cross_up_df = ema10_df > ema20_df
first_cross_up_df = cross_up_df & ~cross_up_df.shift(1, fill_value=True)
first_cross_down_df = ~cross_up_df & cross_up_df.shift(1, fill_value=False)

signal_df = (first_cross_up_df * 0.1) + (first_cross_down_df * -0.1)
signal_df *= ssc.is_universe("SET100")
signal_df = signal_df.shift(1)
signal_df = signal_df[signal_df.index >= pd.Timestamp(start_date)]  # type: ignore
assert isinstance(signal_df, pd.DataFrame)


def apply_trade_volume(
    ts: datetime, symbol: str, signal: float, close_price: float, acct: SETAccount
):
    return acct.buy_pct_port(signal)


#%% Backtest
initial_cash = 1e6

result = backtest(
    signal_df=signal_df,
    apply_trade_volume=apply_trade_volume,
    start_date=start_date,
    end_date=end_date,
    initial_cash=initial_cash,
    signal_delay_bar=0,
)

print(result.stat_df)