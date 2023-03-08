import numpy as np
import pandas as pd

import ezyquant as ez
from ezyquant import SETSignalCreator, backtest
from ezyquant import utils as ezutils
from ezyquant.backtesting import Context
from ezyquant.reader import SETBusinessDay

ez.connect_sqlite("ezyquant.db")

start_date = "2010-01-01"
start_load_date = ezutils.date_to_str(pd.Timestamp(start_date) - SETBusinessDay(1))
end_date = "2019-12-31"

# %% create signal
ssc = SETSignalCreator(
    start_date=start_load_date,
    end_date=end_date,
    index_list=["SET100"],
)
pe_df = ssc.get_data("pe", "daily")

# filter signal by universe and banned
pe_df *= ssc.is_universe(["SET100"]) * ~ssc.is_banned()

pe_df = pe_df.replace(0, np.nan)

# rank top 10% of pe
signal_df = (pe_df.rank(axis=1, method="max") <= 10) / 10.00001

# drop nan columns (no signal) for faster backtest
signal_df = signal_df.dropna(axis=1, how="all")


def backtest_algorithm(ctx: Context) -> float:
    return ctx.target_pct_port(ctx.signal)


# %% Backtest
initial_cash = 1e6

result = backtest(
    signal_df=signal_df,
    backtest_algorithm=backtest_algorithm,
    start_date=start_date,
    end_date=end_date,
    initial_cash=initial_cash,
    pct_commission=0.25,
)

print(result.stat_df)
result.to_excel("model_low_pe_report.xlsx")
