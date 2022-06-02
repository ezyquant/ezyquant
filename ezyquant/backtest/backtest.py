from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .. import utils
from .portfolio import Portfolio
from .position import Position


def backtest(
    initial_cash: float,
    signal_weight_df: pd.DataFrame,
    match_price_df: pd.DataFrame,
    close_price_df: pd.DataFrame,
    pct_commission: float = 0.0,
    pct_buy_match_price: float = 0.0,
    pct_sell_match_price: float = 0.0,
    initial_position_dict: Optional[Dict[str, Position]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    r_buy_match = 1.0 + pct_buy_match_price
    r_sell_match = 1.0 - pct_sell_match_price
    r_min_match = min(r_buy_match, r_sell_match)
    r_max_match = max(r_buy_match, r_sell_match)

    pf = Portfolio(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict=initial_position_dict if initial_position_dict else {},
    )

    sig_by_price_df = signal_weight_df / (match_price_df * r_max_match)

    position_df_list: List[pd.DataFrame] = []

    def on_interval(close_s: pd.Series) -> pd.Series:
        ts = close_s.name

        match_price_s = match_price_df.loc[ts]  # type: ignore

        trade_value = pf.cash + (pf.volume_series * match_price_s * r_min_match).sum()
        target_volume_s = trade_value * sig_by_price_df.loc[ts]  # type: ignore
        target_volume_s = utils.round_df_100(target_volume_s)
        trade_volume_s = target_volume_s.sub(pf.volume_series, fill_value=0)

        # Sell
        for k, v in trade_volume_s[trade_volume_s < 0].items():
            price = match_price_s[k] * r_sell_match
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
                price=price,
                timestamp=ts,  # type: ignore
            )

        # Buy
        for k, v in trade_volume_s[trade_volume_s > 0].items():
            price = match_price_s[k] * r_buy_match
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
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

    summary_df = close_price_df.apply(on_interval, axis=1)
    position_df = pd.concat(position_df_list)
    trade_df = pd.DataFrame(pf.trade_list)

    return summary_df, position_df, trade_df
