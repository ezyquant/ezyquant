from dataclasses import fields
from typing import List, Tuple

import pandas as pd

from .. import utils
from . import validators as vld
from .portfolio import Portfolio
from .position import Position
from .trade import Trade

position_df_columns = ["timestamp"] + [i.name for i in fields(Position)]


def backtest_target_weight_logic(
    initial_cash: float,
    signal_weight_df: pd.DataFrame,
    buy_price_df: pd.DataFrame,
    sell_price_df: pd.DataFrame,
    pct_commission: float = 0.0,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Backtest Target Weight.

    Parameters
    ----------
    initial_cash : float
        cash at the beginning of the backtest
    signal_weight_df : pd.DataFrame
        dataframe of signal weight.
        index is trade date, columns are symbol, values are weight.
        values must be positive and sum must not more than 1 each day.
        missing index or nan row is not rebalance.
    buy_price_df : pd.DataFrame
        dataframe of buy price.
        index is trade date, columns are symbol, values are weight.
        index and columns must be same as or more than signal_weight_df.
    sell_price_df : pd.DataFrame
        dataframe of sell price.
        index is trade date, columns are symbol, values are weight.
        index and columns must be same as or more than signal_weight_df.
    pct_commission : float, default 0.0
        percentage of commission fee

    Returns
    -------
    Tuple[pd.Series, pd.DataFrame, pd.DataFrame]
        Return snapshot at end of day:
            - cash_series
                - timestamp (index)
                - cash
            - position_df
                - timestamp
                - symbol
                - volume
                - avg_cost_price
            - trade_df
                - timestamp
                - symbol
                - volume
                - price
                - pct_commission
    """
    vld.check_initial_cash(initial_cash)
    vld.check_pct_commission(pct_commission)
    vld.check_price_df(buy_price_df, sell_price_df)
    vld.check_signal_df(
        signal_weight_df,
        trade_date_list=buy_price_df.index.to_list(),
        symbol_list=buy_price_df.columns.to_list(),
    )

    # Select only symbol in signal
    buy_price_df = buy_price_df[signal_weight_df.columns]
    sell_price_df = sell_price_df[signal_weight_df.columns]

    group_price = pd.concat([buy_price_df, sell_price_df]).groupby(level=0)
    min_price_df = group_price.min() * (1.0 - pct_commission)
    max_price_df = group_price.max() * (1.0 + pct_commission)

    pf = Portfolio(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: initial position
        trade_list=[],  # TODO: initial trade
    )

    sig_by_price_df = signal_weight_df / max_price_df

    position_df_list: List[pd.DataFrame] = [
        # First dataframe for sort columns
        pd.DataFrame(columns=position_df_columns, dtype="float64"),
    ]

    def on_interval(buy_price_s: pd.Series) -> float:
        ts = buy_price_s.name

        trade_value = pf.cash + (pf.volume_series * min_price_df.loc[ts]).sum()  # type: ignore
        target_volume_s = trade_value * sig_by_price_df.loc[ts]  # type: ignore
        trade_volume_s = target_volume_s - pf.volume_series.reindex(
            target_volume_s.index, fill_value=0
        )
        trade_volume_s = utils.round_df_100(trade_volume_s)

        # Sell
        sell_price_s = sell_price_df.loc[ts]  # type: ignore
        for k, v in trade_volume_s[trade_volume_s < 0].items():
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
                price=sell_price_s[k],
                timestamp=ts,  # type: ignore
            )

        # Buy
        for k, v in trade_volume_s[trade_volume_s > 0].items():
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
                price=buy_price_s[k],  # type: ignore
                timestamp=ts,  # type: ignore
            )

        pos_df = pf.get_position_df()
        pos_df["timestamp"] = ts
        position_df_list.append(pos_df)

        return pf.cash

    cash_s = buy_price_df.apply(on_interval, axis=1)
    assert isinstance(cash_s, pd.Series)

    position_df = pd.concat(position_df_list, ignore_index=True)
    position_df["timestamp"] = pd.to_datetime(position_df["timestamp"])

    trade_df = pd.DataFrame(pf.trade_list, columns=[i.name for i in fields(Trade)])
    return cash_s, position_df, trade_df
