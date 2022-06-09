from typing import List

import pandas as pd

from .. import fields as fld


def check_price_mode(price_mode: str) -> None:
    if price_mode not in [
        fld.D_OPEN,
        fld.D_HIGH,
        fld.D_LOW,
        fld.D_CLOSE,
        fld.D_AVERAGE,
    ]:
        raise ValueError(f"Invalid price mode: {price_mode}")


def check_initial_cash(initial_cash: float) -> None:
    if initial_cash < 0:
        raise ValueError("initial_cash must be positive")


def check_pct_commission(pct_commission: float) -> None:
    if pct_commission < 0 or pct_commission > 1:
        raise ValueError("pct_commission must be between 0 and 1")


def check_price_df(buy_price_df: pd.DataFrame, sell_price_df: pd.DataFrame):
    idx = buy_price_df.index

    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("buy_price_df index must be DatetimeIndex")
    if not idx.is_monotonic:
        raise ValueError("buy_price_df index must be monotonic increasing")
    if not idx.is_unique:
        raise ValueError("buy_price_df index must be unique")
    if not idx.equals(sell_price_df.index):
        raise ValueError("buy_price_df and sell_price_df index must be same")
    if not buy_price_df.columns.equals(sell_price_df.columns):
        raise ValueError("buy_price_df and sell_price_df columns must be same")

    if buy_price_df.empty:
        raise ValueError("buy_price_df must not be empty")
    if sell_price_df.empty:
        raise ValueError("sell_price_df must not be empty")


def check_signal_df(
    signal_df: pd.DataFrame, trade_date_list: List, symbol_list: List[str]
):
    idx = signal_df.index

    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("signal_df index must be DatetimeIndex")
    if not idx.is_monotonic:
        raise ValueError("signal_df index must be monotonic increasing")
    if not idx.is_unique:
        raise ValueError("signal_df index must be unique")
    if not idx.isin(trade_date_list).all():
        raise ValueError("signal_df index must be in buy_price_df index")
    if not signal_df.columns.isin(symbol_list).all():
        raise ValueError("signal_df columns must be in buy_price_df columns")

    if signal_df.empty:
        raise ValueError("signal_df must not be empty")
    if (signal_df < 0).values.any():
        raise ValueError("signal_df cannot have negative value")
    if (signal_df.isna().any(axis=1) & (signal_df > 0).any(axis=1)).any():
        raise ValueError("signal_df cannot have NaN among non zero value")
    if not signal_df.sum(axis=1).between(0, 1).all():
        raise ValueError(
            "signal_df must be positive and sum must not more than 1 each day"
        )
