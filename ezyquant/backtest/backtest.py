from typing import List, Tuple

import pandas as pd

from .. import utils
from .portfolio import Portfolio


def backtest(
    initial_cash: float,
    signal_weight_df: pd.DataFrame,
    match_price_df: pd.DataFrame,
    pct_commission: float = 0.0,
    pct_buy_match_price: float = 0.0,
    pct_sell_match_price: float = 0.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    r_buy_match = 1.0 + pct_buy_match_price
    r_sell_match = 1.0 - pct_sell_match_price
    r_min_match = min(r_buy_match, r_sell_match)
    r_max_match = max(r_buy_match, r_sell_match)

    pf = Portfolio(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: initial position
        trade_list=[],  # TODO: initial trade for result
    )

    sig_by_price_df = signal_weight_df / (match_price_df * r_max_match)

    position_df_list: List[pd.DataFrame] = []

    def on_interval(match_price_s: pd.Series) -> float:
        ts = match_price_s.name

        trade_value = pf.cash + (pf.volume_series * match_price_s * r_min_match).sum()
        target_volume_s = trade_value * sig_by_price_df.loc[ts]  # type: ignore
        target_volume_s = utils.round_df_100(target_volume_s)
        trade_volume_s = target_volume_s.sub(pf.volume_series, fill_value=0)

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

    cash_df = match_price_df.apply(on_interval, axis=1).to_frame("cash")
    position_df = pd.concat(position_df_list)
    trade_df = pd.DataFrame(pf.trade_list)

    return cash_df, position_df, trade_df
