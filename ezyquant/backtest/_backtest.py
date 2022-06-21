from dataclasses import fields
from typing import Callable, List, Tuple

import pandas as pd

from .. import utils
from . import validators as vld
from .account import SETAccount
from .position import Position
from .trade import Trade

position_df_columns = ["timestamp"] + [i.name for i in fields(Position)]
trade_df_columns = [i.name for i in fields(Trade)]


def _backtest(
    initial_cash: float,
    signal_df: pd.DataFrame,
    apply_trade_volume: Callable[[pd.Timestamp, float, str, SETAccount], float],
    close_price_df: pd.DataFrame,
    price_match_df: pd.DataFrame,
    pct_buy_slip: float,
    pct_sell_slip: float,
    pct_commission: float,
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
    # TODO: check close_price_df and price_match_df

    ratio_buy_slip = 1.0 + pct_buy_slip
    ratio_sell_slip = 1.0 - pct_sell_slip
    ratio_commission = 1.0 + pct_commission

    # Select only symbol in signal
    price_match_df = price_match_df[signal_df.columns]
    close_price_df = close_price_df[signal_df.columns]

    # reindex signal_df
    signal_df = signal_df.reindex(index=close_price_df.index)  # type: ignore

    pf = SETAccount(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: [EZ-79] initial position dict
        trade_list=[],  # TODO: initial trade
        market_price_series=close_price_df.iloc[0],
    )

    close_price_df = close_price_df.iloc[1:]

    position_df_list: List[pd.DataFrame] = [
        # First dataframe for sort columns
        pd.DataFrame(columns=position_df_columns, dtype="float64"),
    ]

    def on_interval(close_price_s: pd.Series) -> float:
        ts: pd.Timestamp = close_price_s.name  # type: ignore

        signal_s = signal_df.loc[ts]  # type: ignore

        def on_symbol(x):
            pf.selected_symbol = x[0]
            return apply_trade_volume(ts, x[1], x[0], pf)

        trade_volume_s = pd.Series(
            signal_s.reset_index().apply(on_symbol, axis=1).values,
            index=signal_s.index,
        )
        trade_volume_s = utils.round_df_100(trade_volume_s)

        match_price_s = price_match_df.loc[ts]  # type: ignore

        # Sell
        for k, v in trade_volume_s[trade_volume_s < 0].items():
            symbol: str = k  # type: ignore
            price = match_price_s[k] * ratio_sell_slip

            # sell with enough volume
            if symbol not in pf.position_dict:
                continue

            v = max(v, -pf.position_dict[symbol].volume)

            pf._match_order(
                matched_at=ts,
                symbol=symbol,
                volume=v,
                price=price,
            )

        # Buy
        for k, v in trade_volume_s[trade_volume_s > 0].items():
            symbol: str = k  # type: ignore
            price = match_price_s[k] * ratio_buy_slip

            # buy with enough cash
            v = min(v, pf.cash / price / ratio_commission)
            v = utils.round_df_100(v)

            if v == 0.0:
                continue

            pf._match_order(
                matched_at=ts,
                symbol=symbol,
                volume=v,
                price=price,
            )

        pf.market_price_series = close_price_s
        pf._cache_clear()

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
