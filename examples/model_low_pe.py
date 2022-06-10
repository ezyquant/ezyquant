import numpy as np

from ezyquant import SETSignalCreator, backtest_target_weight

sqlite_path = "psims.db"
start_date = "2010-01-01"
end_date = "2019-12-31"

#%% create signal
ssc = SETSignalCreator(
    sqlite_path=sqlite_path,
    start_date=start_date,
    end_date=end_date,
    index_list=["SET100"],
)
pe_df = ssc.get_data("pe", "daily")
pe_df *= ssc.is_universe("SET100")
pe_df = pe_df.replace(0, np.nan)

signal_df = (pe_df.rank(axis=1, method="max") <= 10) / 10.00001

#%% Backtest
initial_cash = 1e6

result = backtest_target_weight(
    signal_df=signal_df,
    rebalance_freq="no",
    rebalance_at=0,
    # common param
    sqlite_path=sqlite_path,
    start_date=start_date,
    end_date=end_date,
    initial_cash=initial_cash,
)

print(result)
