from datetime import datetime

import numpy as np
import pandas as pd

import ezyquant as ez
from ezyquant import SETSignalCreator, backtest
from ezyquant import utils as ezutils
from ezyquant.backtest import SETAccount, SETPosition
from ezyquant.reader import SETBusinessDay

ez.connect_sqlite("psims.db")

start_date = "2010-01-01"
start_load_date = ezutils.date_to_str(pd.Timestamp(start_date) - SETBusinessDay(1))
end_date = "2019-12-31"

#%% create signal
ssc = SETSignalCreator(
    start_date=start_load_date,
    end_date=end_date,
    index_list=["SET100"],
)
pe_df = ssc.get_data("pe", "daily")
pe_df *= ssc.is_universe("SET100")
pe_df = pe_df.replace(0, np.nan)

signal_df = (pe_df.rank(axis=1, method="max") <= 10) / 10.00001

signal_df = signal_df.dropna(axis=1, how="all")


def backtest_algorithm(
    ts: datetime, sig: float, pos: SETPosition, acct: SETAccount
) -> float:
    return acct.target_pct_port(sig)


#%% Backtest
initial_cash = 1e6

result = backtest(
    signal_df=signal_df,
    backtest_algorithm=backtest_algorithm,
    start_date=start_date,
    end_date=end_date,
    initial_cash=initial_cash,
    pct_commission=0.25,
    signal_delay_bar=1,
)

print(result.stat_df)
result.to_excel("result.xlsx")
