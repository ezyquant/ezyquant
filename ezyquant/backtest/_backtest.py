from dataclasses import fields
from typing import Callable, Dict, List, Tuple

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
    apply_trade_volume: Callable[[pd.Timestamp, str, float, float, SETAccount], float],
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
    # TODO: check price and signal

    ratio_buy_slip = 1.0 + pct_buy_slip
    ratio_sell_slip = 1.0 - pct_sell_slip
    ratio_commission = 1.0 + pct_commission

    # Account
    acct = SETAccount(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: [EZ-79] initial position dict
        trade_list=[],  # TODO: initial trade
        market_price_dict=close_price_df.iloc[0].to_dict(),
    )

    # remove first close row
    close_price_df = close_price_df.iloc[1:]  # type: ignore

    # Dict
    signal_dict: Dict[pd.Timestamp, Dict[str, float]] = signal_df.to_dict("index")  # type: ignore
    close_price_dict: Dict[pd.Timestamp, Dict[str, float]] = close_price_df.to_dict(
        "index"
    )  # type: ignore
    price_match_dict: Dict[pd.Timestamp, Dict[str, float]] = price_match_df.to_dict(
        "index"
    )  # type: ignore

    position_df_list: List[pd.DataFrame] = [
        # First dataframe for sort columns
        pd.DataFrame(columns=position_df_columns, dtype="float64"),
    ]

    def on_interval(ts: pd.Timestamp, close_price_dict: Dict[str, float]) -> float:
        signal_d = signal_dict.get(ts, dict())

        buy_volume_d: Dict[str, float] = dict()
        sell_volume_d: Dict[str, float] = dict()

        for k, v in signal_d.items():
            acct.selected_symbol = k
            trade_volume = apply_trade_volume(ts, k, v, acct.market_price_dict[k], acct)

            if trade_volume > 0:
                buy_volume_d[k] = trade_volume
            elif trade_volume < 0:
                sell_volume_d[k] = trade_volume

        price_match_d = price_match_dict[ts]

        # Sell
        for k, v in sell_volume_d.items():
            price = price_match_d[k] * ratio_sell_slip

            if not price > 0:
                # continue if 0, negative, nan
                continue

            # sell with enough volume
            if k not in acct.position_dict:
                continue

            v = max(v, -acct.position_dict[k].volume)
            v = utils.round_df_100(v)

            acct._match_order(
                matched_at=ts,
                symbol=k,
                volume=v,
                price=price,
            )

        # Buy
        for k, v in buy_volume_d.items():
            price = price_match_d[k] * ratio_buy_slip

            if not price > 0:
                # continue if 0, negative, nan
                continue

            # buy with enough cash
            v = min(v, acct.cash / price / ratio_commission)
            v = utils.round_df_100(v)

            if v == 0.0:
                continue

            acct._match_order(
                matched_at=ts,
                symbol=k,
                volume=v,
                price=price,
            )

        acct._cache_clear()
        acct.market_price_dict = close_price_dict

        pos_df = acct.position_df
        pos_df["timestamp"] = ts
        position_df_list.append(pos_df)

        return acct.cash

    cash_s = pd.Series({k: on_interval(k, v) for k, v in close_price_dict.items()})
    assert isinstance(cash_s, pd.Series)

    position_df = pd.concat(position_df_list, ignore_index=True)
    position_df["timestamp"] = pd.to_datetime(position_df["timestamp"])

    trade_df = pd.DataFrame(acct.trade_list, columns=trade_df_columns)
    trade_df["matched_at"] = pd.to_datetime(trade_df["matched_at"])

    return cash_s, position_df, trade_df
