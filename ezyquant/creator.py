from typing import List

import numpy as np
import pandas as pd

from . import fields as fld
from .errors import InputError
from .reader import SETDataReader


class SETSignalCreator:
    def __init__(
        self,
        index_list: List[str],
        symbol_list: List[str],
        sector_list: List[str],
        industry_list: List[str],
        start_date: str,
        end_date: str,
    ):
        self._index_list = index_list
        self._symbol_list = symbol_list
        self._sector_list = sector_list
        self._industry_list = industry_list
        self._start_date = start_date
        self._end_date = end_date

        self._sdr = SETDataReader("psims.db")

    def get_data(
        self,
        field: str,
        timeframe: str,
        value_by: str,
        method: str,
        period: int,
        shift: int,
        row_trading_date: bool,
    ) -> pd.DataFrame:
        if value_by == fld.VALUE_BY_STOCK:
            if timeframe == fld.TIMEFRAME_DAILY:
                df = self._sdr.get_data_symbol_daily(
                    field=field,
                    symbol_list=self._symbol_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            elif timeframe in (
                fld.TIMEFRAME_QUARTERLY,
                fld.TIMEFRAME_YEARLY,
                fld.TIMEFRAME_TTM,
                fld.TIMEFRAME_YTD,
            ):
                df = self._sdr._get_fundamental_data(
                    field=field,
                    symbol_list=self._symbol_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                    period=timeframe,
                    fillna_value=np.inf,
                )
            else:
                raise InputError("Invalid timeframe")
        elif value_by == fld.VALUE_BY_INDEX:
            if timeframe == fld.TIMEFRAME_DAILY:
                df = self._sdr.get_data_index_daily(
                    field=field,
                    index_list=self._index_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            else:
                raise InputError("Invalid timeframe")
        elif value_by == fld.VALUE_BY_SECTOR:
            if timeframe == fld.TIMEFRAME_DAILY:
                df = self._sdr.get_data_sector_daily(
                    field=field,
                    sector_list=self._sector_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            else:
                raise InputError("Invalid timeframe")
        elif value_by == fld.VALUE_BY_INDUSTRY:
            if timeframe == fld.TIMEFRAME_DAILY:
                df = self._sdr.get_data_industry_daily(
                    field=field,
                    industry_list=self._industry_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            else:
                raise InputError("Invalid timeframe")
        else:
            raise InputError("Invalid value_by")

        if row_trading_date:
            df = self._reindex_tradeing_dates(
                df=df, start_date=self._start_date, end_date=self._end_date
            )

        df = self._manipulate_df(df=df, method=method, period=period, shift=shift)

        return df

    """
    Protected methods
    """

    def _reindex_tradeing_dates(
        self, df: pd.DataFrame, start_date: str, end_date: str
    ) -> pd.DataFrame:
        trade_dates = self._sdr.get_trading_dates(start_date, end_date)
        df = df.reindex(pd.DatetimeIndex(trade_dates))  # type: ignore
        return df

    @staticmethod
    def _manipulate_df(df: pd.DataFrame, method: str, period: int, shift: int):
        if method != fld.METHOD_CONSTANT:
            df = df.apply(
                lambda x: SETSignalCreator._rolling_skip_na_keep_inf(
                    x, method=method, period=period, shift=shift
                ),
                axis=0,
            )
        df = df.fillna(method="ffill")
        df = df.replace(np.inf, np.nan)
        return df

    @staticmethod
    def _rolling_skip_na_keep_inf(
        series: pd.Series, method: str, period: int, shift: int
    ) -> pd.Series:
        series = series.dropna().shift(shift)

        roll = series.rolling(period)

        if method == fld.METHOD_SUM:
            out = roll.sum()
        elif method == fld.METHOD_MEAN:
            out = roll.mean()
        else:
            raise InputError("Invalid method")

        out = out.mask(np.isinf(series), np.inf)
        out = out.fillna(method="ffill")

        assert isinstance(out, pd.Series)
        return out
