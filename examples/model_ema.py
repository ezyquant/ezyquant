import pandas as pd

import ezyquant as ez
from ezyquant import SETSignalCreator, backtest
from ezyquant import utils as ezutils
from ezyquant.backtesting import Context
from ezyquant.reader import SETBusinessDay

ez.connect_sqlite("ezyquant.db")

start_date = "2010-01-01"
start_load_date = ezutils.date_to_str(
    pd.Timestamp(start_date) - SETBusinessDay(20)
)  # load more data for signal calculation
end_date = "2019-12-31"

# %% create signal
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

# filter signal by universe and banned
signal_df *= ssc.is_universe(["SET100"]) * ~ssc.is_banned()

# drop nan columns (no signal) for faster backtest
signal_df = signal_df.dropna(axis=1, how="all")


def backtest_algorithm(ctx: Context) -> float:
    return ctx.buy_pct_port(ctx.signal)


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
result.to_excel("model_ema_report.xlsx")
