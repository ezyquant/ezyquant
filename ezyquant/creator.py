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
        sqlite_path: str,
        start_date: str,
        end_date: str,
        index_list: List[str] = ["SET100"],
        symbol_list: List[str] = [],
    ):
        """Initialize SETSignalCreator.

        Parameters
        ----------
        sqlite_path : str
            path to sqlite file e.g. /path/to/sqlite.db
        start_date : str
            Start date of data.
        end_date : str
            End date of data.
        index_list : List[str]
            List of index name. by default ['SET100']
                - SET
                - mai
                - SETWB
                - SETTHSI
                - SETCLMV
                - SETHD
                - sSET
                - SET100
                - SET50
        symbol_list : List[str]
            List of symbol name. by default []
        """
        self._index_list = [i.upper() for i in index_list]
        self._symbol_list = [i.upper() for i in symbol_list]
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
        """_summary_

        Parameters
        ----------
        field : str
            Name of data field.
        timeframe : str
            - daily
            - quarterly
            - yearly
            - ttm
            - ytd
        value_by : str
            - stock
            - index
            - industry
            - sector
        method : str
            - constant
            - count
            - sum
            - mean
            - median
            - var
            - std
            - min
            - max
            - corr
            - cov
            - skew
            - kurt
            - apply
            - aggregate
            - quantile
            - sem
            - rank
        period : int
            Number of observations used for each window.
        shift : int
            Number of periods to shift. Can be positive or negative.

        Returns
        -------
        pd.DataFrame
            - symbol : str as column
            - trade date : date as index

        Examples
        --------
        >>> from ezyquant import SETSignalCreator
        >>> from ezyquant import fields as fld
        >>> ssc = SETSignalCreator(
        ...     index_list=[],
        ...     symbol_list=["COM7", "MALEE"],
        ...     sector_list=[],
        ...     industry_list=[],
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ...     sqlite_path="psims.db",
        ... )
        >>> ssc.get_data(
        ...     field=fld.D_CLOSE,
        ...     timeframe=fld.TIMEFRAME_DAILY,
        ...     value_by=fld.VALUE_BY_STOCK,
        ...     method=fld.METHOD_CONSTANT,
        ...     period=0,
        ...     shift=0,
        ... )
                      COM7  MALEE
        2022-01-04  41.875   6.55
        2022-01-05  41.625   6.50
        2022-01-06  41.500   6.50
        2022-01-07  41.000   6.40
        2022-01-10  40.875   6.30
        ...            ...    ...
        2022-03-28  42.750   5.75
        2022-03-29  41.500   5.75
        2022-03-30  42.250   5.70
        2022-03-31  43.000   5.70
        2022-04-01  42.500   5.70

        >>> ssc.get_data(
        ...     field=fld.Q_CASH,
        ...     timeframe=fld.TIMEFRAME_QUARTERLY,
        ...     value_by=fld.VALUE_BY_STOCK,
        ...     method=fld.METHOD_CONSTANT,
        ...     period=0,
        ...     shift=0,
        ... )
                          COM7     MALEE
        2022-01-04         NaN       NaN
        2022-01-05         NaN       NaN
        2022-01-06         NaN       NaN
        2022-01-07         NaN       NaN
        2022-01-10         NaN       NaN
        ...                ...       ...
        2022-03-28  1656882.22  80321.08
        2022-03-29  1656882.22  80321.08
        2022-03-30  1656882.22  80321.08
        2022-03-31  1656882.22  80321.08
        2022-04-01  1656882.22  80321.08
        """
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

                    df = self._reindex_trade_date(df)
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
                    sector_list=[],
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            elif value_by == fld.VALUE_BY_INDUSTRY:
                df = self._sdr.get_data_industry_daily(
                    field=field,
                    industry_list=[],
                    start_date=self._start_date,
                    end_date=self._end_date,
                )
            else:
                raise InputError(
                    f"{value_by} is invalid value_by. Please read document to check valid value_by."
                )

            df = self._reindex_trade_date(df)

            df = df.shift(shift)

            if method != fld.METHOD_CONSTANT:
                df = self._rolling(df, method=method, period=period)

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

                df = df.apply(
                    lambda x: self._rolling_skip_na_keep_inf(
                        x, method=method, period=period, shift=shift
                    ),
                    axis=0,
                )
                df = self._reindex_trade_date(df)
                df = df.fillna(method="ffill")
                df = df.replace(np.inf, np.nan)
            else:
                raise InputError(
                    f"{value_by} is invalid value_by. Please read document to check valid value_by."
                )

        else:
            raise InputError(
                f"{timeframe} is invalid timeframe. Please read document to check valid timeframe."
            )

        df.index.freq = None  # type: ignore

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
        td = self._get_trading_dates()
        df = df.reindex(pd.DatetimeIndex(td))  # type: ignore
        return df

    def _rolling_skip_na_keep_inf(
        self, series: pd.Series, method: str, period: int, shift: int
    ) -> pd.Series:
        series = series.dropna().shift(shift)

        if method != fld.METHOD_CONSTANT:
            is_inf = np.isinf(series)
            series = self._rolling(series, method=method, period=period)
            series = series.mask(is_inf, np.inf)

        series = series.fillna(method="ffill")

        return series

    def _rolling(self, data, method: str, period: int):
        roll = data.rolling(period)
        try:
            data = getattr(roll, method)()
        except AttributeError:
            raise InputError(
                f"{method} is invalid method. Please read document to check valid method."
            )
        return data

    def _get_symbol_in_universe(self) -> List[str]:
        out = set()
        if self._symbol_list:
            df = self._sdr.get_symbol_info(symbol_list=self._symbol_list)
            out.update(df["symbol"].tolist())
        if fld.MARKET_SET in self._index_list:
            df = self._sdr.get_symbol_info(market=fld.MARKET_SET)
            out.update(df["symbol"].tolist())
        if fld.MARKET_MAI.upper() in self._index_list:
            df = self._sdr.get_symbol_info(market=fld.MARKET_MAI)
            out.update(df["symbol"].tolist())
        if self._index_list:
            df = self._get_symbols_by_index()
            out.update(df["symbol"].tolist())
        return list(out)

    def _get_symbol_info(self):
        s = self._get_symbol_in_universe()
        return self._sdr.get_symbol_info(symbol_list=s)

    def _get_symbols_by_index(self):
        l = []
        for i in self._index_list:
            start_date = self._sdr._get_prior_as_of_date_symbol_index(
                index_name=i, current_date=self._start_date
            )

            df = self._sdr.get_symbols_by_index(
                index_list=[i],
                start_date=start_date,
                end_date=self._end_date,
            )

            l.append(df)

        return pd.concat(l)
