from datetime import date
from typing import Iterable, List, Optional

import pandas as pd


class SETDataReader:
    """SETDataReader read PSIMS data."""

    def __init__(self, sqlite_path: str) -> None:
        """SETDataReader constructor.

        Parameters
        ----------
        sqlite_path : str
            path to sqlite file e.g. /path/to/sqlite.db
        """
        self.__sqlite_path = sqlite_path

    def get_trading_dates(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[date]:
        """Data from table CALENDAR.

        Parameters
        ----------
        start_date : Optional[date], optional
            start of D_TRADE, by default None
        end_date : Optional[date], optional
            end of D_TRADE, by default None

        Returns
        -------
        List[date]
            list of trading dates
        """
        return []

    def is_trading_date(self, date_: date) -> bool:
        """Data from table CALENDAR.

        Parameters
        ----------
        date_ : date
            D_TRADE

        Returns
        -------
        bool
            is trading date
        """
        return True

    def is_today_trading_date(self) -> bool:
        """Data from table CALENDAR.

        Returns
        -------
        bool
            is today trading date
        """
        return self.is_trading_date(date.today())

    def get_symbol_info(
        self,
        symbols: Optional[Iterable[str]] = None,
        market: Optional[str] = None,
        industry: Optional[str] = None,
        sector: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY.

        Parameters
        ----------
        symbols : Optional[Iterable[str]], optional
            N_SECURITY in symbols, case insensitive, by default None
        market : Optional[str], optional
            I_MARKET e.g. 'SET', 'MAI', by default None
        industry : Optional[str], optional
            SECTOR.N_INDUSTRY, by default None
        sector : Optional[str], optional
            SECTOR.N_SECTOR, by default None

        Returns
        -------
        pd.DataFrame
            symbol info dataframe contain columns:
                - symbol_id: int - I_SECURITY
                - symbol: str - N_SECURITY
                - market: str - I_MARKET
                - industry: str - SECTOR.N_INDUSTRY
                - sector: str - SECTOR.N_SECTOR
                - TODO: ...

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_company_info(self, symbols: Optional[Iterable[str]] = None) -> pd.DataFrame:
        """Data from table COMPANY.

        Parameters
        ----------
        symbols : Optional[Iterable[str]], optional
            SECURITY.N_SECURITY in symbols, case insensitive, by default None

        Returns
        -------
        pd.DataFrame
            company info dataframe contain columns:
                - company_id: int - I_COMPANY
                - symbol: str - SECURITY.N_SECURITY
                - company_name_t: str - N_COMPANY_T
                - company_name_e: str - N_COMPANY_E
                - TODO: ...

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_change_name(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table CHANGE_NAME_SECURITY.

        Parameters
        ----------
        symbols : Optional[List[str]], optional
            N_SECURITY in symbols, case insensitive, by default None
        start_date : Optional[date], optional
            start of effect_date (D_EFFECT), by default None
        end_date : Optional[date], optional
            end of effect_date (D_EFFECT), by default None

        Returns
        -------
        pd.DataFrame
            change name dataframe contain columns:
                - symbol_id: int - I_SECURITY
                - symbol: str - SECURITY.N_SECURITY
                - effect_date: date - D_EFFECT
                - symbol_old: str - N_SECURITY_OLD
                - symbol_new: str - N_SECURITY_NEW

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_dividend(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table RIGHTS_BENEFIT. Include only Cash Dividend (CA) and
        Stock Dividend (SD). Not include Cancelled (F_CANCEL='C').

        Parameters
        ----------
        symbols : Optional[Iterable[str]], optional
            N_SECURITY in symbols, case insensitive, by default None
        start_date : Optional[date], optional
            start of ex_date (D_SIGN), by default None
        end_date : Optional[date], optional
            end of ex_date (D_SIGN), by default None
        ca_type : Optional[str], optional
            N_CA_TYPE, by default None
                - CD - cash dividend
                - SD - stock dividend

        Returns
        -------
        pd.DataFrame
            dividend dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - ex_date: date - D_SIGN
                - pay_date: date - D_BEG_PAID
                - ca_type: str - N_CA_TYPE
                - dps: int - Z_RIGHTS

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_delisted(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_DETAIL. Include only Delisted
        (D_DELISTED!=None).

        Parameters
        ----------
        symbols : Optional[Iterable[str]], optional
            N_SECURITY in symbols, case insensitive, by default None
        start_date : Optional[date], optional
            start of delisted_date (D_DELISTED), by default None
        end_date : Optional[date], optional
            end of delisted_date (D_DELISTED), by default None

        Returns
        -------
        pd.DataFrame
            delisted dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - delisted_date: date - D_DELISTED

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_sp(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table SIGN_POSTING. Include only Suspension (N_SIGN='SP').

        Parameters
        ----------
        symbols : Optional[Iterable[str]], optional
            N_SECURITY in symbols, case insensitive, by default None
        start_date : Optional[date], optional
            start of hold_date (D_HOLD), by default None
        end_date : Optional[date], optional
            end of hold_date (D_HOLD), by default None

        Returns
        -------
        pd.DataFrame
            sp dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - hold_date: date - D_HOLD

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_symbols_by_index(
        self,
        index_list: Optional[Iterable[str]],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_INDEX."""
        return pd.DataFrame()

    def get_adjust_factor(
        self,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table ADJUST_FACTOR."""
        return pd.DataFrame()

    def get_data_symbol_daily(
        self,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjusted_par: bool = True,
        adjusted_stock_dividend: bool = True,
        adjusted_cash_dividend: bool = True,
    ) -> pd.DataFrame:
        """Data from table DAILY_STOCK_STAT, DAILY_STOCK_TRADE."""
        return pd.DataFrame()

    def get_data_symbol_quarterly(
        self,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjusted_par: bool = True,
        adjusted_stock_dividend: bool = True,
        adjusted_cash_dividend: bool = True,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD."""
        return pd.DataFrame()

    def get_data_symbol_yearly(
        self,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjusted_par: bool = True,
        adjusted_stock_dividend: bool = True,
        adjusted_cash_dividend: bool = True,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD."""
        return pd.DataFrame()

    def get_data_symbol_ttm(
        self,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjusted_par: bool = True,
        adjusted_stock_dividend: bool = True,
        adjusted_cash_dividend: bool = True,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD."""
        return pd.DataFrame()

    def get_data_symbol_ytd(
        self,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_adjusted: bool = True,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD."""
        return pd.DataFrame()

    def get_data_index_daily(
        self,
        field: str,
        index_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table MKTSTAT_DAILY_INDEX, MKTSTAT_DAILY_MARKET."""
        return pd.DataFrame()

    def get_data_sector_daily(
        self,
        field: str,
        index_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table DAILY_SECTOR_INFO."""
        return pd.DataFrame()
