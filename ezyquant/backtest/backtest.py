from typing import Tuple

import numpy as np
import pandas as pd

from .. import fields as fld
from .. import utils
from ..creator import SETSignalCreator
from . import backtest_logic as btl
from . import validators as vld


def backtest_target_weight(
    signal_df: pd.DataFrame,
    rebalance_freq: str,
    rebalance_at: int,
    # common param
    sqlite_path: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    pct_commission: float = 0.0,
    pct_buy_slip: float = 0.0,
    pct_sell_slip: float = 0.0,
    trigger_buy_price_mode: str = "close",
    trigger_buy_price_delay_bar: int = 0,
    trigger_sell_price_mode: str = "close",
    trigger_sell_price_delay_bar: int = 0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Backtest target weight. Rebalance with rebalance_freq, rebalance_at or
    if signal was changed from yesterday.

    Parameters
    ----------
    signal_df : pd.DataFrame
        signal dataframe.
    rebalance_freq : str
        rebalance frequency.
            - none
            - daily
            - weekly
            - monthly
    rebalance_at : int
        rebalance at. can be 1 to 31 depending on rebalance_freq.
            - 1: first day of month or Monday
            - 5: fifth day of month or Friday
    sqlite_path : str
        path to sqlite file e.g. /path/to/sqlite.db
    start_date : str
        start date in format YYYY-MM-DD
    end_date : str
        end date in format YYYY-MM-DD
    initial_cash : float
        initial cash
    pct_commission : float, by default 0.0
        percent commission
    pct_buy_slip : float, by default 0.0
        percent of buy price increase
    pct_sell_slip : float, by default 0.0
        percent of sell price decrease
    trigger_buy_price_mode : str, by default "close"
        trigger buy price mode.
            - open
            - high
            - low
            - close
            - average
    trigger_buy_price_delay_bar : int, by default 0
        trigger buy price delay bar.
    trigger_sell_price_mode : str, by default "close"
        trigger sell price mode.
            - open
            - high
            - low
            - close
            - average
    trigger_sell_price_delay_bar : int, by default 0
        trigger sell price delay bar.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Return following dataframe:
            - summary_df
            - position_df
            - trade_df
            - dividend_df
            - stat_df
    """
    signal_df = signal_df.dropna(axis=1, how="all")
    symbol_list = signal_df.columns.tolist()

    ssc = SETSignalCreator(
        sqlite_path=sqlite_path,
        start_date=start_date,
        end_date=end_date,
        index_list=[],
        symbol_list=symbol_list,
    )

    # Price df
    # TODO: more price mode
    vld.check_price_mode(trigger_buy_price_mode)
    vld.check_price_mode(trigger_sell_price_mode)

    # TODO: load more data for delay bar
    buy_price_df = ssc.get_data(
        field=trigger_buy_price_mode,
        timeframe=fld.TIMEFRAME_DAILY,
        shift=trigger_buy_price_delay_bar,
    )
    sell_price_df = ssc.get_data(
        field=trigger_sell_price_mode,
        timeframe=fld.TIMEFRAME_DAILY,
        shift=trigger_sell_price_delay_bar,
    )

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
        raise ValueError(f"Invalid rebalance_freq: {rebalance_freq}")

    is_signal_change = (signal_df != signal_df.shift(1)).any(axis=1)

    is_rebalance = is_signal_change | is_rebalance_freq  # type: ignore

    signal_df = signal_df.where(is_rebalance, np.nan)

    # Baned symbol
    # TODO: backtest_target_weight_logic must allow sell all, but not rebalance
    is_banned = buy_price_df.isna() | sell_price_df.isna()
    is_force_sell = is_banned & ~is_banned.shift(1, fill_value=False)
    signal_df = signal_df.mask(is_force_sell, 0)

    # Drop NaN row
    signal_df = signal_df.dropna(axis=0, how="all")
    signal_df = signal_df.dropna(axis=1, how="all")

    # Slip
    buy_price_df *= 1 + pct_buy_slip
    sell_price_df *= 1 - pct_sell_slip

    # Backtest
    # TODO: initial_position_dict
    cash_series, position_df, trade_df = btl.backtest_target_weight_logic(
        initial_cash=initial_cash,
        signal_weight_df=signal_df,
        buy_price_df=buy_price_df,
        sell_price_df=sell_price_df,
        pct_commission=pct_commission,
    )

    # Dividend df
    # TODO: dividend_df
    dividend_df = pd.DataFrame()

    # Stat df
    # TODO: stat_df
    stat_df = pd.DataFrame()

    # Summary df
    # TODO: summary_df
    summary_df = cash_series.to_frame("cash")

    return summary_df, position_df, trade_df, dividend_df, stat_df
