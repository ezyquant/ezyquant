from dataclasses import fields
from typing import Callable, List, Tuple

import pandas as pd

from .. import utils
from . import validators as vld
from .portfolio import Portfolio
from .position import Position
from .trade import Trade

position_df_columns = ["timestamp"] + [i.name for i in fields(Position)]
trade_df_columns = [i.name for i in fields(Trade)]


def _backtest(
    initial_cash: float,
    signal_df: pd.DataFrame,
    apply_trade_volume: Callable[[pd.Timestamp, float, str, Portfolio], float],
    buy_price_df: pd.DataFrame,
    sell_price_df: pd.DataFrame,
    close_price_df: pd.DataFrame,
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
                - matched_at
                - symbol
                - volume
                - price
                - pct_commission
    """
    vld.check_initial_cash(initial_cash)
    vld.check_pct_commission(pct_commission)
    # TODO: check close price df
    vld.check_price_df(buy_price_df, sell_price_df)
    vld.check_signal_df(
        signal_df,
        trade_date_list=buy_price_df.index.to_list(),
        symbol_list=buy_price_df.columns.to_list(),
    )

    # Select only symbol in signal
    buy_price_df = buy_price_df[signal_df.columns]
    sell_price_df = sell_price_df[signal_df.columns]
    close_price_df = close_price_df[signal_df.columns]

    # reindex signal_df
    signal_df = signal_df.reindex(index=close_price_df.index)  # type: ignore

    pf = Portfolio(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: [EZ-79] initial position dict
        trade_list=[],  # TODO: initial trade
    )

    position_df_list: List[pd.DataFrame] = [
        # First dataframe for sort columns
        pd.DataFrame(columns=position_df_columns, dtype="float64"),
    ]

    def on_interval(close_price_s: pd.Series) -> float:
        ts: pd.Timestamp = close_price_s.name  # type: ignore

        signal_s = signal_df.loc[ts]  # type: ignore

        def on_symbol(x):
            pf.symbol = x[0]
            return apply_trade_volume(ts, x[1], x[0], pf)

        trade_volume_s = pd.Series(
            signal_s.reset_index().apply(on_symbol, axis=1).values,
            index=signal_s.index,
        )

        trade_volume_s = utils.round_df_100(trade_volume_s)

        # TODO: buy/sell with enough cash/volume
        # Sell
        sell_price_s = sell_price_df.loc[ts]  # type: ignore
        for k, v in trade_volume_s[trade_volume_s < 0].items():
            pf._match_order(
                matched_at=ts,
                symbol=k,  # type: ignore
                volume=v,
                price=sell_price_s[k],
            )

        # Buy
        buy_price_s = buy_price_df.loc[ts]  # type: ignore
        for k, v in trade_volume_s[trade_volume_s > 0].items():
            pf._match_order(
                matched_at=ts,
                symbol=k,  # type: ignore
                volume=v,
                price=buy_price_s[k],
            )

        pf._update_market_price(close_price_s)

        pos_df = pf.position_df
        pos_df["timestamp"] = ts
        position_df_list.append(pos_df)

        return pf.cash

    cash_s = close_price_df.apply(on_interval, axis=1)
    assert isinstance(cash_s, pd.Series)

    position_df = pd.concat(position_df_list, ignore_index=True)
    position_df["timestamp"] = pd.to_datetime(position_df["timestamp"])

    trade_df = pd.DataFrame(pf.trade_list, columns=trade_df_columns)
    trade_df["matched_at"] = pd.to_datetime(trade_df["matched_at"])

    return cash_s, position_df, trade_df
