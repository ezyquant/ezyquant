# Ezyquant

powerful backtest python library for Thai stocks

## Features

- Backtest
- Signal Creator
- Data Reader

## Installation

```
pip install ezyquant
```

or

```
pip install git+https://github.com/ezyquant/ezyquant
```

## Quick Example

```
import pandas as pd

import ezyquant as ez
from ezyquant import SETDataReader, backtest
from ezyquant.backtest import Context

ez.connect_sqlite("psims.db")

start_date = "2010-01-01"
end_date = "2019-12-31"
initial_cash = 1e6

# Signal
sdr = SETDataReader()

trade_date_list = sdr.get_trading_dates(start_date, end_date)

signal_df = pd.DataFrame(index=pd.DatetimeIndex(trade_date_list), columns=["AOT"])


def backtest_algorithm(ctx: Context) -> float:
    return 100


# Backtest
report = backtest(
    signal_df=signal_df,
    backtest_algorithm=backtest_algorithm,
    start_date=start_date,
    end_date=end_date,
    initial_cash=initial_cash,
    pct_commission=0.25,
)
```

result

```
                               port_value port_value_with_dividend
pct_net_profit                   7.265485                 7.727443
cagr                             0.235385                 0.242127
pct_maximum_drawdown            -0.324056                -0.321664
cagr_divided_maxdd               0.726372                 0.752734
pct_win_per_trade                     1.0                      1.0
std                              0.210757                 0.205193
cagr_divided_std                 1.116854                 1.179995
pct_exposure                     0.723671                 0.699671
total_commission                 2490.125                 2490.125
initial_capital                 1000000.0                1000000.0
ending_capital                8265484.875              8727443.475
net_profit                    7265484.875              7727443.475
maximum_drawdown               -1474725.0               -1379007.0
all_trades                              1                        1
avg_profit_loss               7265484.875              7727443.475
pct_avg_profit_loss                   NaN                      NaN
avg_bar_held                       1985.0                   1985.0
win_trades                              1                        1
total_profit                 7244824.8125             7244824.8125
avg_profit                   7244824.8125             7244824.8125
pct_avg_profit                   7.273555                 7.273555
avg_win_bar_held                   1985.0                   1985.0
max_win_consecutive                     1                        1
loss_trades                             0                        0
total_loss                            0.0                      0.0
avg_loss                              NaN                      NaN
pct_avg_loss                          NaN                      NaN
avg_lose_bar_held                     NaN                      NaN
max_lose_consecutive                    0                        0
start_date            2010-01-04 00:00:00      2010-01-04 00:00:00
end_date              2019-12-30 00:00:00      2019-12-30 00:00:00
pct_commission                       0.25                     0.25
pct_buy_slip                          0.0                      0.0
pct_sell_slip                         0.0                      0.0
```

You can find more examples in the examples directory.
