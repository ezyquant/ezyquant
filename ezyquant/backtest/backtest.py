from typing import Callable, List

import pandas as pd

from .. import fields as fld
from .. import utils
from ..creator import SETSignalCreator
from ..errors import InputError
from ..reader import SETDataReader
from ..report import SETBacktestReport
from ._backtest import _backtest
from .account import SETAccount


def backtest(
    signal_df: pd.DataFrame,
    apply_trade_volume: Callable[[pd.Timestamp, str, float, float, SETAccount], float],
    start_date: str,
    end_date: str,
    initial_cash: float,
    pct_commission: float = 0.0,
    pct_buy_slip: float = 0.0,
    pct_sell_slip: float = 0.0,
    price_match_mode: str = "open",
    signal_delay_bar: int = 1,
) -> SETBacktestReport:
    """Backtest target weight. Rebalance with rebalance_freq, rebalance_at or
    if signal was changed from yesterday.

    # TODO: Update doc

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
    SETBacktestReport
    """
    # Price df
    before_start_date = utils.date_to_str(
        pd.Timestamp(start_date) - SETDataReader()._custom_business_day()
    )
    symbol_list = signal_df.columns.tolist()
    price_match_df = _get_price(
        start_date=start_date,
        end_date=end_date,
        symbol_list=symbol_list,
        mode=price_match_mode,
    )
    close_price_df = _get_price(
        start_date=before_start_date,
        end_date=end_date,
        symbol_list=symbol_list,
        mode=fld.D_CLOSE,
    )

    # Signal df
    signal_df = signal_df.shift(signal_delay_bar)

    # Backtest
    # TODO: [EZ-79] initial_position_dict
    cash_series, position_df, trade_df = _backtest(
        initial_cash=initial_cash,
        signal_df=signal_df,
        apply_trade_volume=apply_trade_volume,
        close_price_df=close_price_df,
        price_match_df=price_match_df,
        pct_buy_slip=pct_buy_slip,
        pct_sell_slip=pct_sell_slip,
        pct_commission=pct_commission,
    )

    return SETBacktestReport(
        initial_capital=initial_cash,
        pct_commission=pct_commission,
        pct_buy_slip=pct_buy_slip,
        pct_sell_slip=pct_sell_slip,
        cash_series=cash_series,
        position_df=position_df,
        trade_df=trade_df,
    )


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
