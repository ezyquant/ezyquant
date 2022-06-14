from typing import List

import numpy as np
import pandas as pd

from .. import fields as fld
from .. import utils
from ..creator import SETSignalCreator
from ..errors import InputError
from ..result import SETResult
from . import validators as vld
from ._backtest import _backtest_target_weight


def backtest_target_weight(
    signal_df: pd.DataFrame,
    rebalance_freq: str,
    rebalance_at: int,
    # common param
    start_date: str,
    end_date: str,
    initial_cash: float,
    pct_commission: float = 0.0,
    pct_buy_slip: float = 0.0,
    pct_sell_slip: float = 0.0,
    buy_price_match_mode: str = "open",
    sell_price_match_mode: str = "open",
    signal_delay_bar: int = 1,
) -> SETResult:
    """Backtest target weight. Rebalance with rebalance_freq, rebalance_at or
    if signal was changed from yesterday.

    Parameters
    ----------
    signal_df : pd.DataFrame
        signal dataframe.
    rebalance_freq : str
        rebalance frequency.
            - no
            - daily
            - weekly
            - monthly
    rebalance_at : int
        rebalance at. can be 1 to 31 depending on rebalance_freq.
            - 1: first day of month or Monday
            - 5: fifth day of month or Friday
    start_date : str
        start date in format YYYY-MM-DD
    end_date : str
        end date in format YYYY-MM-DD
    initial_cash : float
        initial cash
    pct_commission : float, by default 0.0
        percent commission ex. 0.01 means 1% commission
    pct_buy_slip : float, by default 0.0
        percent of buy price increase ex. 0.01 means 1% increase
    pct_sell_slip : float, by default 0.0
        percent of sell price decrease ex. 0.01 means 1% decrease
    buy_price_match_mode : str, by default "open"
        buy price match mode.
            - open
            - high
            - low
            - close
            - median - (high + low)/2
            - typical - (high + low + close)/3
            - weighted - (high + low + close + close)/4
    sell_price_match_mode : str, by default "open"
        sell price match mode.
            - open
            - high
            - low
            - close
            - median - (high + low)/2
            - typical - (high + low + close)/3
            - weighted - (high + low + close + close)/4
    signal_delay_bar : int, by default 1
        delay bar for signal.

    Returns
    -------
    SETResult
    """
    # Price df
    symbol_list = signal_df.columns.tolist()
    buy_price_df = _get_price(
        start_date=start_date,
        end_date=end_date,
        symbol_list=symbol_list,
        mode=buy_price_match_mode,
    )
    sell_price_df = _get_price(
        start_date=start_date,
        end_date=end_date,
        symbol_list=symbol_list,
        mode=sell_price_match_mode,
    )

    # Slip
    buy_price_df *= 1 + pct_buy_slip
    sell_price_df *= 1 - pct_sell_slip

    # Signal df
    signal_df = signal_df.shift(signal_delay_bar)

    # Rebalance
    assert isinstance(signal_df.index, pd.DatetimeIndex)
    if rebalance_freq == fld.REBALANCE_FREQ_NO:
        is_rebalance_freq = False
    elif rebalance_freq == fld.REBALANCE_FREQ_DAILY:
        is_rebalance_freq = True
    elif rebalance_freq == fld.REBALANCE_FREQ_WEEKLY:
        is_rebalance_freq = utils.is_rebalance_weekly(signal_df.index, rebalance_at)
    elif rebalance_freq == fld.REBALANCE_FREQ_MONTHLY:
        is_rebalance_freq = utils.is_rebalance_monthly(signal_df.index, rebalance_at)
    else:
        raise InputError(f"Invalid rebalance_freq: {rebalance_freq}")

    is_signal_change = (signal_df != signal_df.shift(1)).any(axis=1)

    is_rebalance = is_signal_change | is_rebalance_freq  # type: ignore

    signal_df = signal_df.where(is_rebalance, np.nan)

    # Baned symbol
    is_banned = buy_price_df.isna() | sell_price_df.isna()
    is_force_sell = is_banned & ~is_banned.shift(1, fill_value=False)
    signal_df = signal_df.mask(is_force_sell, 0)

    # Drop NaN row
    signal_df = signal_df.dropna(axis=0, how="all")
    signal_df = signal_df.dropna(axis=1, how="all")

    # Backtest
    # TODO: [EZ-79] initial_position_dict
    cash_series, position_df, trade_df = _backtest_target_weight(
        initial_cash=initial_cash,
        signal_weight_df=signal_df,
        buy_price_df=buy_price_df,
        sell_price_df=sell_price_df,
        pct_commission=pct_commission,
    )

    return SETResult(cash_series, position_df, trade_df)


def _get_price(
    start_date: str,
    end_date: str,
    symbol_list: List[str],
    mode: str,
) -> pd.DataFrame:
    ssc = SETSignalCreator(
        start_date=start_date,
        end_date=end_date,
        index_list=[],
        symbol_list=symbol_list,
    )

    def _get_data(field: str) -> pd.DataFrame:
        return ssc.get_data(field=field, timeframe=fld.TIMEFRAME_DAILY)

    if mode in (
        fld.PRICE_MATCH_MODE_OPEN,
        fld.PRICE_MATCH_MODE_HIGH,
        fld.PRICE_MATCH_MODE_LOW,
        fld.PRICE_MATCH_MODE_CLOSE,
    ):
        out = _get_data(mode)
    elif mode == fld.PRICE_MATCH_MODE_MEDIAN:
        h = _get_data(fld.PRICE_MATCH_MODE_HIGH)
        l = _get_data(fld.PRICE_MATCH_MODE_LOW)
        out = (h + l) / 2
    elif mode == fld.PRICE_MATCH_MODE_TYPICAL:
        h = _get_data(fld.PRICE_MATCH_MODE_HIGH)
        l = _get_data(fld.PRICE_MATCH_MODE_LOW)
        c = _get_data(fld.PRICE_MATCH_MODE_CLOSE)
        out = (h + l + c) / 3
    elif mode == fld.PRICE_MATCH_MODE_WEIGHTED:
        h = _get_data(fld.PRICE_MATCH_MODE_HIGH)
        l = _get_data(fld.PRICE_MATCH_MODE_LOW)
        c = _get_data(fld.PRICE_MATCH_MODE_CLOSE)
        out = (h + l + c + c) / 4
    else:
        raise InputError(f"Invalid price_match_mode: {mode}")

    return out
