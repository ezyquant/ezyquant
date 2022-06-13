from typing import Tuple

import numpy as np
import pandas as pd

from .. import fields as fld
from .. import utils
from ..creator import SETSignalCreator
from ..errors import InputError
from . import result as res
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
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
        percent commission
    pct_buy_slip : float, by default 0.0
        percent of buy price increase
    pct_sell_slip : float, by default 0.0
        percent of sell price decrease
    buy_price_match_mode : str, by default "open"
        buy price match mode.
            - open
            - high
            - low
            - close
            - average
    sell_price_match_mode : str, by default "open"
        sell price match mode.
            - open
            - high
            - low
            - close
            - average
    signal_delay_bar : int, by default 1
        delay bar for signal.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Return following dataframe:
            - summary_df
                - timestamp (index)
                - port_value_with_dividend
                - port_value
                - total_market_value
                - cash
                - cashflow
                - dividend
                - cumulative_dividend
                - commission
            - position_df
                - timestamp
                - symbol
                - volume
                - avg_cost_price
                - close_price
                - close_value
            - trade_df
                - timestamp
                - symbol
                - side
                - volume
                - price
                - commission
            - dividend_df
                - TODO
            - stat_df
                - TODO
    """
    symbol_list = signal_df.columns.tolist()
    ssc = SETSignalCreator(
        start_date=start_date,
        end_date=end_date,
        index_list=[],
        symbol_list=symbol_list,
    )

    # Price df
    # TODO: [EZ-80] more price mode
    vld.check_price_mode(buy_price_match_mode)
    vld.check_price_mode(sell_price_match_mode)

    # TODO: cache load price
    buy_price_df = ssc.get_data(
        field=buy_price_match_mode, timeframe=fld.TIMEFRAME_DAILY
    )
    sell_price_df = ssc.get_data(
        field=sell_price_match_mode, timeframe=fld.TIMEFRAME_DAILY
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

    # Position df
    close_price_df = ssc.get_data(field=fld.D_CLOSE, timeframe=fld.TIMEFRAME_DAILY)
    position_df = res.make_position_df(position_df, close_price_df)

    # Trade df
    trade_df = res.make_trade_df(trade_df)

    # Dividend df
    # TODO: [EZ-77] dividend_df
    dividend_df = pd.DataFrame(columns=["timestamp", "amount"])

    # Summary df
    summary_df = res.make_summary_df(
        cash_series=cash_series,
        trade_df=trade_df,
        position_df=position_df,
        dividend_df=dividend_df,
    )

    # Stat df
    # TODO: [EZ-76] stat_df
    stat_df = pd.DataFrame()

    return summary_df, position_df, trade_df, dividend_df, stat_df
