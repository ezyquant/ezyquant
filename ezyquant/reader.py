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
        return []

    def is_today_trading_date(self) -> bool:
        return True

    def get_symbol_info(self, symbols: Optional[Iterable[str]] = None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_company_info(self, symbols: Optional[Iterable[str]] = None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_change_name(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def get_dividend(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def get_delisted(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def get_sp(
        self,
        symbols: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def get_symbols_by_index(
        self,
        index_list: Optional[Iterable[str]],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def get_adjust_factor(
        self,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
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
        return pd.DataFrame()

    def get_data_symbol_ytd(
        self,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_adjusted: bool = True,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def get_data_index_daily(
        self,
        field: str,
        index_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def get_data_sector_daily(
        self,
        field: str,
        index_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()
