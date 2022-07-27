from typing import Callable, List

import pandas as pd

from .. import fields as fld
from .. import utils
from ..creator import SETSignalCreator
from ..errors import InputError
from ..reader import SETBusinessDay
from ..report import SETBacktestReport
from ._backtesting import _backtest
from .context import Context


def backtest(
    signal_df: pd.DataFrame,
    backtest_algorithm: Callable[[Context], float],
    start_date: str,
    end_date: str,
    initial_cash: float,
    pct_commission: float = 0.0,
    pct_buy_slip: float = 0.0,
    pct_sell_slip: float = 0.0,
    price_match_mode: str = "open",
    signal_delay_bar: int = 1,
) -> SETBacktestReport:
    """Backtest function.

    Parameters
    ----------
    signal_df: pd.DataFrame
        Dataframe of signal.
        Index is trade date, columns are symbol, values are signal.
        Missing signal in trade date will be filled with nan.
    backtest_algorithm: Callable[[Context], float],
        function for calculate trade volume.

        Parameters:
            - context: Context
                  context for backtest

        Return:
            - trade_volume: float
                  positive for buy, negative for sell, 0 or nan for no trade
    start_date: str
        Start date in format YYYY-MM-DD.
    end_date: str
        End date in format YYYY-MM-DD.
    initial_cash: float
        Initial cash.
    pct_buy_slip: float = 0.0
        Percentage of buy slip, higher value means higher buy price (ex. 1.0 means 1% increase).
    pct_sell_slip: float = 0.0
        Percentage of sell slip, higher value means lower sell price (ex. 1.0 means 1% decrease).
    pct_commission: float = 0.0
        Percentage of commission fee (ex. 1.0 means 1% fee).
    price_match_mode: str = "open"
        Price match mode
            - open
            - high
            - low
            - close
            - median - (high + low)/2
            - typical - (high + low + close)/3
            - weighted - (high + low + close + close)/4
    signal_delay_bar: int = 1
        Delay bar for shifting signal.

    Returns
    -------
    SETBacktestReport
    """
    # Price df
    before_start_date = utils.date_to_str(pd.Timestamp(start_date) - SETBusinessDay())
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
    signal_df = signal_df[
        (signal_df.index >= pd.Timestamp(start_date))  # type: ignore
        & (signal_df.index <= pd.Timestamp(end_date))  # type: ignore
    ]

    # Percentage
    pct_commission /= 100
    pct_buy_slip /= 100
    pct_sell_slip /= 100

    # Backtest
    # TODO: [EZ-79] initial_position_dict
    cash_series, position_df, trade_df = _backtest(
        initial_cash=initial_cash,
        signal_df=signal_df,
        backtest_algorithm=backtest_algorithm,
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
