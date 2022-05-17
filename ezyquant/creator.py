from functools import lru_cache
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
        sqlite_path: str,
    ):
        self._index_list = index_list
        self._symbol_list = symbol_list
        self._sector_list = sector_list
        self._industry_list = industry_list
        self._start_date = start_date
        self._end_date = end_date
        self._sqlite_path = sqlite_path

        self._sdr = SETDataReader(self._sqlite_path)

    def get_data(
        self,
        field: str,
        timeframe: str,
        value_by: str,
        method: str,
        period: int,
        shift: int,
    ) -> pd.DataFrame:
        timeframe = timeframe.lower()
        value_by = value_by.lower()
        method = method.lower()

        if timeframe == fld.TIMEFRAME_DAILY:
            if value_by == fld.VALUE_BY_STOCK:
                df = self._sdr.get_data_symbol_daily(
                    field=field,
                    symbol_list=self._symbol_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
                df = self._reindex_trade_date(df)

                # Forward fill 0 and NaN with prior
                if field in {
                    fld.D_OPEN,
                    fld.D_HIGH,
                    fld.D_LOW,
                    fld.D_CLOSE,
                    fld.D_AVERAGE,
                    fld.D_LAST_BID,
                    fld.D_LAST_OFFER,
                }:
                    prior_df = self._sdr.get_data_symbol_daily(
                        field=fld.D_PRIOR,
                        symbol_list=self._symbol_list,
                        start_date=self._start_date,
                        end_date=self._end_date,
                    )
                    prior_df = self._reindex_trade_date(prior_df)
                    prior_df = prior_df.replace(0, np.nan)
                    prior_df = prior_df.fillna(method="ffill")

                    df = df.replace(0, np.nan)
                    df = df.fillna(prior_df)

            elif value_by == fld.VALUE_BY_INDEX:
                df = self._sdr.get_data_index_daily(
                    field=field,
                    index_list=self._index_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            elif value_by == fld.VALUE_BY_SECTOR:
                df = self._sdr.get_data_sector_daily(
                    field=field,
                    sector_list=self._sector_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            elif value_by == fld.VALUE_BY_INDUSTRY:
                df = self._sdr.get_data_industry_daily(
                    field=field,
                    industry_list=self._industry_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            else:
                raise InputError("Invalid value_by")

            df = df.shift(shift)

            if method != fld.METHOD_CONSTANT:
                roll = df.rolling(period)
                try:
                    df = getattr(roll, method)()
                except AttributeError:
                    raise InputError("Invalid method")

        elif timeframe in (
            fld.TIMEFRAME_QUARTERLY,
            fld.TIMEFRAME_YEARLY,
            fld.TIMEFRAME_TTM,
            fld.TIMEFRAME_YTD,
        ):
            if value_by == fld.VALUE_BY_STOCK:
                df = self._sdr._get_fundamental_data(
                    field=field,
                    symbol_list=self._symbol_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                    timeframe=timeframe,
                    fillna_value=np.inf,
                )

                df = self._reindex_trade_date(df)

                df = df.apply(
                    lambda x: self._rolling_skip_na_keep_inf(
                        x, method=method, period=period, shift=shift
                    ),
                    axis=0,
                )
                df = df.fillna(method="ffill")
                df = df.replace(np.inf, np.nan)
            else:
                raise InputError("Invalid value_by")

        else:
            raise InputError("Invalid timeframe {}".format(timeframe))

        return df

    """
    Protected methods
    """

    @lru_cache
    def _get_trading_dates(self) -> List[str]:
        return self._sdr.get_trading_dates(
            start_date=self._start_date, end_date=self._end_date
        )

    def _reindex_trade_date(self, df: pd.DataFrame) -> pd.DataFrame:
        trade_dates = self._get_trading_dates()
        df = df.reindex(pd.DatetimeIndex(trade_dates))  # type: ignore
        return df

    @staticmethod
    def _rolling_skip_na_keep_inf(
        series: pd.Series, method: str, period: int, shift: int
    ) -> pd.Series:
        series = series.dropna().shift(shift)
        is_inf = np.isinf(series)

        if method != fld.METHOD_CONSTANT:
            roll = series.rolling(period)

            try:
                series = getattr(roll, method)()
            except AttributeError:
                raise InputError("Invalid method")

            series = series.mask(is_inf, np.inf)

        series = series.fillna(method="ffill")

        return series
