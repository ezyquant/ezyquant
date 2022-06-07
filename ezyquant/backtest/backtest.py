from dataclasses import fields
from typing import List, Tuple

import pandas as pd

from .. import utils
from .portfolio import Portfolio
from .position import Position
from .trade import Trade


def backtest_target_weight(
    initial_cash: float,
    signal_weight_df: pd.DataFrame,
    price_df: pd.DataFrame,
    pct_commission: float = 0.0,
    pct_buy_match_price: float = 0.0,
    pct_sell_match_price: float = 0.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Backtest.

    Parameters
    ----------
    initial_cash : float
        cash at the beginning of the backtest
    signal_weight_df : pd.DataFrame
        dataframe of signal weight.
        index is datetime, columns are symbol, values are weight.
        values must be positive and sum must not more than 1 each day.
        nan values are ignored (not rebalance).
    price_df : pd.DataFrame
        dataframe of match price.
        index is datetime, columns are symbol, values are weight.
        index and columns must be same as or more than signal_weight_df.
    pct_commission : float, default 0.0
        percentage of commission fee
    pct_buy_match_price : float, default 0.0
        percentage of buy match price
    pct_sell_match_price : float, default 0.0
        percentage of sell match price

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Return snapshot at end of day:
            - cash_df
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
    """
    r_buy_match = 1.0 + pct_buy_match_price
    r_sell_match = 1.0 - pct_sell_match_price
    r_min_match = min(r_buy_match, r_sell_match)
    r_max_match = max(r_buy_match, r_sell_match)
    r_commission = 1.0 + pct_commission

    pf = Portfolio(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: initial position
        trade_list=[],  # TODO: initial trade
    )

    sig_by_price_df = signal_weight_df / (price_df * r_max_match * r_commission)

    position_df_list: List[pd.DataFrame] = [
        pd.DataFrame(
            columns=["timestamp"] + [i.name for i in fields(Position)], dtype="float64"
        )
    ]

    def on_interval(match_price_s: pd.Series) -> float:
        ts = match_price_s.name

        trade_value = pf.cash + (pf.volume_series * match_price_s * r_min_match).sum()
        target_volume_s = trade_value * sig_by_price_df.loc[ts]  # type: ignore
        trade_volume_s = target_volume_s - pf.volume_series.reindex(
            target_volume_s.index, fill_value=0
        )
        trade_volume_s = utils.round_df_100(trade_volume_s)

        # Sell
        for k, v in trade_volume_s[trade_volume_s < 0].items():
            price = match_price_s[k] * r_sell_match  # type: ignore
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
                price=price,
                timestamp=ts,  # type: ignore
            )

        # Buy
        for k, v in trade_volume_s[trade_volume_s > 0].items():
            price = match_price_s[k] * r_buy_match  # type: ignore
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
                price=price,
                timestamp=ts,  # type: ignore
            )

        pos_df = pf.get_position_df()
        pos_df["timestamp"] = ts
        position_df_list.append(pos_df)

        return pf.cash

    cash_df = price_df.apply(on_interval, axis=1).to_frame("cash")
    position_df = pd.concat(position_df_list, ignore_index=True)
    trade_df = pd.DataFrame(
        pf.trade_list, columns=[i.name for i in fields(Trade)], dtype="float64"
    )

    return cash_df, position_df, trade_df
