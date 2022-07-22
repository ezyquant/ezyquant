# Ezyquant

Powerful backtest python library for Thai stocks

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

ez.connect_sqlite("ezyquant.db")

start_date = "2020-01-01"
end_date = "2020-12-31"
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

Backtest report:

```
                               port_value port_value_with_dividend
pct_net_profit                   0.024916                 0.024916
cagr                             0.025055                 0.025055
pct_maximum_drawdown            -0.223604                -0.223604
cagr_divided_maxdd               0.112052                 0.112052
pct_win_per_trade                     1.0                      1.0
std                               0.32582                  0.32582
cagr_divided_std                 0.076899                 0.076899
pct_exposure                     0.665873                 0.665873
total_commission                  2483.75                  2483.75
initial_capital                 1000000.0                1000000.0
ending_capital                 1024916.25               1024916.25
net_profit                       24916.25                 24916.25
maximum_drawdown              -235340.125              -235340.125
all_trades                              1                        1
avg_profit_loss                  24916.25                 24916.25
pct_avg_profit_loss                   NaN                      NaN
avg_bar_held                        120.0                    120.0
win_trades                              1                        1
total_profit                      22364.0                  22364.0
avg_profit                        22364.0                  22364.0
pct_avg_profit                    0.02251                  0.02251
avg_win_bar_held                    120.0                    120.0
max_win_consecutive                     1                        1
loss_trades                             0                        0
total_loss                            0.0                      0.0
avg_loss                              NaN                      NaN
pct_avg_loss                          NaN                      NaN
avg_lose_bar_held                     NaN                      NaN
max_lose_consecutive                    0                        0
start_date            2020-01-02 00:00:00      2020-01-02 00:00:00
end_date              2020-12-30 00:00:00      2020-12-30 00:00:00
pct_commission                       0.25                     0.25
pct_buy_slip                          0.0                      0.0
pct_sell_slip                         0.0                      0.0
```

You can find more examples in the examples directory.
