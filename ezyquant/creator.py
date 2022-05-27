from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from ta.volatility import (
    AverageTrueRange,
    BollingerBands,
    DonchianChannel,
    KeltnerChannel,
)

from . import fields as fld
from . import utils
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

        Symbol in universe is union of symbol_list and symbols in index_list.

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
        value_by: str = "stock",
        method: str = "constant",
        period: int = 1,
        shift: int = 0,
    ) -> pd.DataFrame:
        """Get DataFrame which columns are symbol in universe and index is
        trade date from start_date to end_date.

        Parameters
        ----------
        field : str
            Name of data field depends on timeframe and value_by.
        timeframe : str
            - daily
            - quarterly
            - yearly
            - ttm
            - ytd
        value_by : str, default 'stock'
            - stock
            - index
            - industry
            - sector
        method : str, default 'constant'
            Name of Dataframe rolling window functions. See <https://pandas.pydata.org/docs/reference/window.html#rolling-window-functions> for details.
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
        period : int, default 1
            Number of periods for rolling Dataframe. Period must be greater than 0.
        shift : int, default 0
            Number of periods to shift Dataframe. Shift must be greater than or equal to 0.

        Returns
        -------
        pd.DataFrame
            - symbol : str as column
            - trade date : date as index

        Examples
        --------
        >>> from ezyquant import SETSignalCreator
        >>> ssc = SETSignalCreator(
        ...     sqlite_path="psims.db",
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ...     index_list=[],
        ...     symbol_list=["COM7", "MALEE"],
        ... )
        >>> ssc.get_data(
        ...     field="close",
        ...     timeframe="daily",
        ...     value_by="stock",
        ...     method="constant",
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
        ...     field="cash",
        ...     timeframe="quarterly",
        ...     value_by="stock",
        ...     method="constant",
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

        if period < 1:
            raise InputError(f"period must be greater than 0. but {period} is given.")
        if shift < 0:
            raise InputError(
                f"shift must be greater than or equal to 0, but {shift} is given."
            )
        if method == fld.METHOD_CONSTANT and period != 1:
            raise InputError(f"{fld.METHOD_CONSTANT} method only support period=1")

        symbol_list = self._get_symbol_in_universe()

        if timeframe == fld.TIMEFRAME_DAILY:
            if value_by == fld.VALUE_BY_STOCK:
                df = self._sdr.get_data_symbol_daily(
                    field=field,
                    symbol_list=symbol_list,
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
                        symbol_list=symbol_list,
                        start_date=self._start_date,
                        end_date=self._end_date,
                    )
                    prior_df = self._reindex_trade_date(prior_df)
                    prior_df = prior_df.replace(0, np.nan)
                    prior_df = prior_df.fillna(method="ffill")

                    df = self._reindex_trade_date(df)
                    df = df.replace(0, np.nan)
                    df = df.fillna(prior_df)

            elif value_by == fld.VALUE_BY_SECTOR:
                df = self._sdr._get_daily_sector_info_by_security(
                    field=field,
                    symbol_list=symbol_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                    f_data="S",
                )
            elif value_by == fld.VALUE_BY_INDUSTRY:
                df = self._sdr._get_daily_sector_info_by_security(
                    field=field,
                    symbol_list=symbol_list,
                    start_date=self._start_date,
                    end_date=self._end_date,
                    f_data="I",
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
                    symbol_list=symbol_list,
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

    def is_universe(self, universe: str) -> pd.DataFrame:
        """Return Dataframe of boolean is universe.

        Parameters
        ----------
        universe : str
            Can be Market, Sector, Industry, or Index.

        Returns
        -------
        pd.DataFrame of boolean
            - symbol : str as column
            - trade date : date as index

        Examples
        --------
        >>> from ezyquant import SETSignalCreator
        >>> ssc = SETSignalCreator(
        ...     sqlite_path="psims.db",
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ...     index_list=[],
        ...     symbol_list=["COM7", "MALEE"],
        ... )
        >>> ssc.is_universe("SET100")
                    COM7  MALEE
        2022-01-04  True  False
        2022-01-05  True  False
        2022-01-06  True  False
        2022-01-07  True  False
        2022-01-10  True  False
        """
        universe = universe.upper()

        try:
            return self._is_universe_static(universe)
        except InputError:
            return self._is_universe_dynamic(universe)

    def is_banned(self) -> pd.DataFrame:
        """Return Dataframe of boolean is banned by Delisted or Suspension (SP).
        Returns
        -------
        pd.DataFrame of boolean
            - symbol : str as column
            - trade date : date as index

        Examples
        --------
        >>> from ezyquant import SETSignalCreator
        >>> ssc = SETSignalCreator(
        ...     sqlite_path="psims.db",
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ...     index_list=[],
        ...     symbol_list=["COM7", "MALEE", "THAI"],
        ... )
        >>> ssc.is_banned()
                     COM7  MALEE  THAI
        2022-01-04  False  False  True
        2022-01-05  False  False  True
        2022-01-06  False  False  True
        2022-01-07  False  False  True
        2022-01-10  False  False  True
        """
        return self._is_banned_delisted() | self._is_banned_sp()

    """
    Technical indicator
    """

    """
    Volatility Indicators
    """

    @staticmethod
    def average_true_range(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 14,
        fillna: bool = False,
    ) -> pd.DataFrame:
        """Average True Range (ATR)

        Parameters
        ----------
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 14
            n period.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Average True Range (ATR)
        """
        ind_df = close.apply(
            lambda x: AverageTrueRange(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )
        out = ind_df.apply(lambda x: x.average_true_range()).T
        return out  # type: ignore

    @staticmethod
    def bollinger_bands(
        close: pd.DataFrame, window: int = 20, window_dev: int = 2, fillna: bool = False
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
    ]:
        """Bollinger Bands.

        Parameters
        ----------
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 20
            n period.
        window_dev : int, default 2
            n factor standard deviation.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Bollinger Channel High Band
                - Bollinger Channel Indicator Crossing High Band (binary).
                - Bollinger Channel Low Band
                - Bollinger Channel Indicator Crossing Low Band (binary).
                - Bollinger Channel Middle Band
                - Bollinger Channel Percentage Band
                - Bollinger Channel Band Width
        """
        ind_df = close.apply(
            lambda x: BollingerBands(
                close=x,
                window=window,
                window_dev=window_dev,
                fillna=fillna,
            )
        )
        out = (
            ind_df.apply(lambda x: x.bollinger_hband()).T,
            ind_df.apply(lambda x: x.bollinger_hband_indicator()).T,
            ind_df.apply(lambda x: x.bollinger_lband()).T,
            ind_df.apply(lambda x: x.bollinger_lband_indicator()).T,
            ind_df.apply(lambda x: x.bollinger_mavg()).T,
            ind_df.apply(lambda x: x.bollinger_pband()).T,
            ind_df.apply(lambda x: x.bollinger_wband()).T,
        )
        return out  # type: ignore

    @staticmethod
    def donchian_channel(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Donchian Channel.

        Parameters
        ----------
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 20
            n period.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Donchian Channel High Band
                - Donchian Channel Low Band
                - Donchian Channel Middle Band
                - Donchian Channel Percentage Band
                - Donchian Channel Band Width
        """
        ind_df = close.apply(
            lambda x: DonchianChannel(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )
        out = (
            ind_df.apply(lambda x: x.donchian_channel_hband()).T,
            ind_df.apply(lambda x: x.donchian_channel_lband()).T,
            ind_df.apply(lambda x: x.donchian_channel_mband()).T,
            ind_df.apply(lambda x: x.donchian_channel_pband()).T,
            ind_df.apply(lambda x: x.donchian_channel_wband()).T,
        )
        return out  # type: ignore

    @staticmethod
    def keltner_channel(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        window_atr: int = 10,
        fillna: bool = False,
        original_version: bool = True,
        multiplier: int = 2,
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
    ]:
        """Keltner Channel.

        Parameters
        ----------
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 20
            n period.
        window_atr : int, default 10
            n atr period. Only valid if original_version param is False.
        fillna : bool, default False
            if True, fill nan values.
        original_version : bool, default True
            if True, use the original version.
        multiplier : int, default 2
            The multiplier has the most effect on the channel width.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Keltner Channel High Band
                - Keltner Channel Indicator Crossing High Band (binary)
                - Keltner Channel Low Band
                - Keltner Channel Indicator Crossing Low Band (binary)
                - Keltner Channel Middle Band
                - Keltner Channel Percentage Band
                - Keltner Channel Band Width
        """
        ind_df = close.apply(
            lambda x: KeltnerChannel(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
                multiplier=multiplier,
            )
        )
        out = (
            ind_df.apply(lambda x: x.keltner_channel_hband()).T,
            ind_df.apply(lambda x: x.keltner_channel_hband_indicator()).T,
            ind_df.apply(lambda x: x.keltner_channel_lband()).T,
            ind_df.apply(lambda x: x.keltner_channel_lband_indicator()).T,
            ind_df.apply(lambda x: x.keltner_channel_mband()).T,
            ind_df.apply(lambda x: x.keltner_channel_pband()).T,
            ind_df.apply(lambda x: x.keltner_channel_wband()).T,
        )
        return out  # type: ignore

    """
    Protected methods
    """

    @lru_cache
    def _get_trading_dates(self) -> List[str]:
        return self._sdr.get_trading_dates(
            start_date=self._start_date, end_date=self._end_date
        )

    @lru_cache
    def _get_symbol_in_universe(self) -> List[str]:
        out = set()
        if self._symbol_list:
            df = self._sdr.get_symbol_info(
                symbol_list=self._symbol_list, sec_type="S", native="L"
            )
            out.update(df["symbol"])
        if fld.MARKET_SET in self._index_list:
            df = self._sdr.get_symbol_info(
                market=fld.MARKET_SET, sec_type="S", native="L"
            )
            out.update(df["symbol"])
        if fld.MARKET_MAI.upper() in self._index_list:
            df = self._sdr.get_symbol_info(
                market=fld.MARKET_MAI, sec_type="S", native="L"
            )
            out.update(df["symbol"])

        index_list = [i for i in self._index_list if i not in (fld.MARKET_MAP_UPPER)]
        for i in index_list:
            df = self._get_symbols_by_index(i)
            out.update(df["symbol"])

        return sorted(list(out))

    def _get_symbol_info(self) -> pd.DataFrame:
        s = self._get_symbol_in_universe()
        return self._sdr.get_symbol_info(symbol_list=s, sec_type="S", native="L")

    def _reindex_trade_date(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        td = self._get_trading_dates()
        return self._reindex_date(df=df, index=td, **kwargs)

    def _reindex_columns_symbol(
        self, df: pd.DataFrame, fill_value=None
    ) -> pd.DataFrame:
        s = self._get_symbol_in_universe()
        return df.reindex(columns=s, fill_value=fill_value)  # type: ignore

    def _rolling(self, data, method: str, period: int):
        roll = data.rolling(period)
        try:
            data = getattr(roll, method)()
        except AttributeError:
            raise InputError(
                f"{method} is invalid method. Please read document to check valid method."
            )
        return data

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

    @lru_cache
    def _get_start_as_of_security_index(self) -> Dict[str, str]:
        out = self._sdr._get_last_as_of_date_in_security_index(
            current_date=self._start_date
        )
        return {k.upper(): v for k, v in out.items()}

    def _get_symbols_by_index(self, index: str) -> pd.DataFrame:
        start_as_of_dict = self._get_start_as_of_security_index()

        return self._sdr.get_symbols_by_index(
            index_list=[index],
            start_date=start_as_of_dict[index],
            end_date=self._end_date,
        )

    def _is_universe_static(self, universe: str) -> pd.DataFrame:
        if universe in fld.MARKET_MAP_UPPER:
            index_type = "market"
        elif universe in fld.INDUSTRY_LIST:
            index_type = "industry"
        elif universe in fld.SECTOR_LIST:
            index_type = "sector"
        else:
            raise InputError(
                f"{universe} is invalid universe. Please read document to check valid universe."
            )

        df = self._get_symbol_info().set_index("symbol")
        tds = self._get_trading_dates()

        is_uni_dict = (df[index_type].str.upper() == universe).to_dict()
        df = pd.DataFrame(is_uni_dict, index=pd.DatetimeIndex(tds))

        # Reindex columns
        df = df.reindex(columns=sorted(df.columns))  # type: ignore

        return df

    def _is_universe_dynamic(self, universe: str) -> pd.DataFrame:
        if universe not in fld.INDEX_LIST_UPPER:
            raise InputError(
                f"{universe} is invalid universe. Please read document to check valid universe."
            )

        df = self._get_symbols_by_index(universe)

        # Pivot
        df = utils.pivot_remove_index_name(
            df=df, index="as_of_date", columns="symbol", values="index"
        )

        # To bool
        df = df.notna()

        # Reindex
        df = self._reindex_trade_date(df, method="ffill", fill_value=False)
        df = self._reindex_columns_symbol(df, fill_value=False)

        return df

    def _is_banned_delisted(self) -> pd.DataFrame:
        symbol_list = self._get_symbol_in_universe()

        df = self._sdr.get_delisted(
            symbol_list=symbol_list,
            end_date=self._end_date,
        )

        df["true"] = True
        df = utils.pivot_remove_index_name(
            df=df, index="delisted_date", columns="symbol", values="true"
        )

        # Reindex
        df = self._reindex_trade_date(df, method="ffill", fill_value=False)
        df = self._reindex_columns_symbol(df, fill_value=False)

        return df

    def _is_banned_sp(self) -> pd.DataFrame:
        symbol_list = self._get_symbol_in_universe()

        df = self._sdr.get_sign_posting(
            symbol_list=symbol_list,
            end_date=self._end_date,
            sign_list=["SP"],
        )

        # hold_date and release_date can be with time
        df["hold_date"] = df["hold_date"].dt.normalize()
        df["release_date"] = df["release_date"].dt.normalize()

        df["true"] = 1
        df["false"] = 0

        # pivot_table also drop duplicated index
        df_hold = df.pivot_table(index="hold_date", columns="symbol", values="true")
        df_release = df.pivot_table(
            index="release_date", columns="symbol", values="false"
        )

        df_hold, df_release = df_hold.align(df_release)

        df = df_release.fillna(df_hold)
        df.index.name = None
        df.columns.name = None

        # Reindex
        df = self._reindex_trade_date(df, method="ffill", fill_value=0)
        df = self._reindex_columns_symbol(df, fill_value=0)

        df = df.astype(bool)

        return df

    """
    Static methods
    """

    @staticmethod
    def _reindex_date(
        df: pd.DataFrame, index, method: Optional[str] = None, fill_value=None
    ) -> pd.DataFrame:
        """Reindex and fillna with method and fill_value."""
        index = pd.DatetimeIndex(index)

        start = pd.Series([df.index.min(), index.min()]).min()
        end = pd.Series([df.index.max(), index.max()]).max()
        dr = pd.date_range(start=start, end=end)
        df = df.reindex(dr)  # type: ignore

        if method != None:
            df = df.fillna(method=method)  # type: ignore
        if fill_value != None:
            df = df.fillna(fill_value)

        return df.reindex(index=index)  # type: ignore
