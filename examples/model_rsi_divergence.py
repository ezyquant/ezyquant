import pandas as pd

import ezyquant as ez
from ezyquant import utils as ezutils
from ezyquant.backtesting import Context
from ezyquant.reader import SETBusinessDay

nan = float("nan")

# Connect Database
ez.connect_sqlite("ezyquant.db")

# Prepare Data
start_date = "2020-01-01"
start_load_date = ezutils.date_to_str(
    pd.Timestamp(start_date) - SETBusinessDay(14)
)  # load more data for signal calculation
end_date = "2022-12-31"
ssc = ez.SETSignalCreator(
    start_date=start_date,
    index_list=["SET50"],
)

# Generate Signal
df_high = ssc.get_data("high", "daily")
df_low = ssc.get_data("low", "daily")
df_close = ssc.get_data("close", "daily")

signal_df = ssc.ta.rsi_divergence(high=df_high, low=df_low, close=df_close)


# Backtest Algorithm
def backtest_algorithm(c: Context):
    # Buy signal
    if c.signal > 0:
        return c.target_pct_port(0.1)
    # Take profit
    if 1.1 * c.cost_price < c.close_price:
        return c.target_pct_port(0)
    # Stop loss
    if c.close_price < 0.95 * c.cost_price:
        return c.target_pct_port(0)

    return 0


# Backtest
result = ez.backtest(
    signal_df=signal_df,
    backtest_algorithm=backtest_algorithm,
    start_date=start_date,
    end_date=end_date,
    initial_cash=1e6,
    pct_commission=0.25,
    pct_buy_slip=0.0,
    pct_sell_slip=0.0,
    price_match_mode="weighted",
    signal_delay_bar=1,
)

# Show Result
print(result.stat_df)
