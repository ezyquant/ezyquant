from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .portfolio import Portfolio
from .position import Position


def backtest(
    signal_df: pd.DataFrame,
    close_df: pd.DataFrame,
    match_price_df: pd.DataFrame,
    rebalance_df: pd.DataFrame,
    initial_cash: float,
    pct_commission: float = 0.0,
    pct_buy_match: float = 0.0,
    pct_sell_match: float = 0.0,
    initial_position_dict: Optional[Dict[str, Position]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    r_buy_match = 1.0 + pct_buy_match
    r_sell_match = 1.0 + pct_sell_match

    if initial_position_dict == None:
        initial_position_dict = {}

    pf = Portfolio(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict=initial_position_dict,
    )

    cash_signal_df = 1 - signal_df.sum(axis=1)
    signal_df = signal_df.where(rebalance_df, np.nan)
    signal_df = signal_df.div(signal_df.sum(axis=1) + cash_signal_df, axis=0)

    sig_by_price_df = signal_df / match_price_df * r_buy_match

    position_df_list: List[pd.DataFrame] = []

    def on_interval(close_s: pd.Series) -> pd.Series:
        ts = close_s.name

        match_price_s = match_price_df.loc[ts]  # type: ignore

        # value for trade today
        trade_value = (pf.volume_series * match_price_s).sum() + pf.cash

        vol_s = (trade_value * sig_by_price_df.loc[ts] // 100 * 100).sub(  # type: ignore
            pf.volume_series, fill_value=0
        )

        # Sell
        for k, v in vol_s[vol_s < 0].items():
            price = match_price_s[k] * r_sell_match
            pf.place_order(
                symbol=str(k),
                volume=v,
                price=price,
                timestamp=ts,  # type: ignore
            )

        # Buy
        for k, v in vol_s[vol_s > 0].items():
            price = match_price_s[k] * r_buy_match
            pf.place_order(
                symbol=str(k),
                volume=v,
                price=price,
                timestamp=ts,  # type: ignore
            )

        pf.set_position_market_price(close_s)

        pos_df = pf.get_position_df()
        pos_df["timestamp"] = ts
        position_df_list.append(pos_df)

        return pd.Series(
            {
                "port_value": pf.port_value,
                "cash": pf.cash,
                "total_market_value": pf.total_market_value,
            }
        )

    port_df = close_df.apply(on_interval, axis=1)
    position_df = pd.concat(position_df_list)
    trade_df = pd.DataFrame(pf.trade_list)

    return port_df, position_df, trade_df
