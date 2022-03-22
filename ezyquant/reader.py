from datetime import date
from typing import Dict, Iterable, List, Optional

import pandas as pd


class SETDataReader:
    def __init__(self, sqlite_path: str) -> None:
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
        """Data from table CALENDAR."""
        return True

    def is_today_trading_date(self) -> bool:
        return is_trading_date(date.today())

    def get_symbol_info(self, symbols: Optional[Iterable[str]] = None) -> pd.DataFrame:
        """Data from table SECURITY."""
        return pd.DataFrame()

    def get_company_info(self, symbols: Optional[Iterable[str]] = None) -> pd.DataFrame:
        """Data from table COMPANY."""
        return pd.DataFrame()

    def get_change_name(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table CHANGE_NAME_SECURITY."""
        return pd.DataFrame()

    def get_dividend(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table RIGHTS_BENEFIT."""
        return pd.DataFrame()

    def get_delisted(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_DETAIL."""
        return pd.DataFrame()

    def get_sp(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sign: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table SIGN_POSTING."""
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
