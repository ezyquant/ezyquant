from datetime import date
from typing import List, Optional

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
        start_date : Optional[date]
            start of D_TRADE, by default None
        end_date : Optional[date]
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
        symbol_list: Optional[List[str]] = None,
        market: Optional[str] = None,
        industry: Optional[str] = None,
        sector: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        market : Optional[str]
            I_MARKET e.g. 'SET', 'MAI', by default None
        industry : Optional[str]
            SECTOR.N_INDUSTRY, by default None
        sector : Optional[str]
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
                - sec_type: str - I_SEC_TYPE
                - native: str - I_NATIVE

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_company_info(self, symbol_list: Optional[List[str]] = None) -> pd.DataFrame:
        """Data from table COMPANY.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            SECURITY.N_SECURITY in symbol_list, case insensitive, must be unique, by default None

        Returns
        -------
        pd.DataFrame
            company info dataframe contain columns:
                - company_id: int - I_COMPANY
                - symbol: str - SECURITY.N_SECURITY
                - company_name_t: str - N_COMPANY_T
                - company_name_e: str - N_COMPANY_E
                - zip: str - I_ZIP
                - tel: str - E_TEL
                - fax: str - E_FAX
                - email: str - E_EMAIL
                - url: str - E_URL
                - establish: date - D_ESTABLISH
                - dvd_policy_t: str - E_DVD_POLICY_T
                - dvd_policy_e: str - E_DVD_POLICY_E

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_change_name(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table CHANGE_NAME_SECURITY.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of effect_date (D_EFFECT), by default None
        end_date : Optional[date]
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
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Data from table RIGHTS_BENEFIT. Include only Cash Dividend (CA) and
        Stock Dividend (SD). Not include Cancelled (F_CANCEL='C').

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of ex_date (D_SIGN), by default None
        end_date : Optional[date]
            end of ex_date (D_SIGN), by default None
        ca_type : Optional[List[str]]
            Coperatie Action Type (N_CA_TYPE), by default None
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
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_DETAIL. Include only Delisted
        (D_DELISTED!=None).

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of delisted_date (D_DELISTED), by default None
        end_date : Optional[date]
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

    def get_sign_posting(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sign_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Data from table SIGN_POSTING.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of hold_date (D_HOLD), by default None
        end_date : Optional[date]
            end of hold_date (D_HOLD), by default None
        sign_list : Optional[List[str]]
            N_SIGN in sign_list, by default None
                - C - Caution Flag
                - CM - Call Market
                - DS - Designated
                - H - Halt
                - NC - Non Compliance
                - NP - Notice Pending
                - SP - Suspension
                - ST

        Returns
        -------
        pd.DataFrame
            sp dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - hold_date: date - D_HOLD
                - sign: str - N_SIGN

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_symbols_by_index(
        self,
        index_list: Optional[List[str]],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_INDEX.

        Parameters
        ----------
        index_list : Optional[List[str]]
            index (SECTOR.N_SECTOR), case insensitive
                - SETWB
                - SETTHSI
                - SETCLMV
                - SETHD
                - sSET
                - SET100
                - SET50
        start_date : Optional[date]
            start of as_of_date (D_AS_OF), by default None
        end_date : Optional[date]
            end of as_of_date (D_AS_OF), by default None

        Returns
        -------
        pd.DataFrame
            - as_of_date: date - D_AS_OF
            - symbol: str - SECURITY.N_SECURITY
            - index: str - SECTOR.N_SECTOR

        Note
        -------
        - SET50 filter S_SEQ 1-50
        - SET100 filter S_SEQ 1-100
        - SETHD filter S_SEQ 1-30

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_adjust_factor(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Data from table ADJUST_FACTOR.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of effect_date (D_EFFECT), by default None
        end_date : Optional[date]
            end of effect_date (D_EFFECT), by default None
        ca_type : Optional[List[str]]
            Coperatie Action Type (N_CA_TYPE), by default None
                - '  '
                - 'CR' - Capital Reduction
                - 'PC' - Par Change
                - 'RC' - Ratio Change
                - 'SD' - Stock Dividend
                - 'XR' - Rights

        Returns
        -------
        pd.DataFrame
            adjust factor dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - effect_date: date - D_EFFECT
                - ca_type: str - N_CA_TYPE
                - adjust_factor: float - F_FACTOR

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_data_symbol_daily(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjusted_par: bool = True,
        adjusted_stock_dividend: bool = True,
    ) -> pd.DataFrame:
        """Data from table DAILY_STOCK_TRADE, DAILY_STOCK_STAT.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'open', 'high', 'low', 'close', 'volume'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade_date (D_TRADE), by default None
        end_date : Optional[date]
            end of trade_date (D_TRADE), by default None
        adjusted_par : bool
            TODO, by default True
        adjusted_stock_dividend : bool
            TODO, by default True

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol: str as column
                - trade_date: date as index

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_data_symbol_quarterly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of as_of_date (D_AS_OF), by default None
        end_date : Optional[date]
            end of as_of_date (D_AS_OF), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol: str as column
                - as_of_date: date as index

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_data_symbol_yearly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of as_of_date (D_AS_OF), by default None
        end_date : Optional[date]
            end of as_of_date (D_AS_OF), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol: str as column
                - as_of_date: date as index

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_data_symbol_ttm(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of as_of_date (D_AS_OF), by default None
        end_date : Optional[date]
            end of as_of_date (D_AS_OF), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol: str as column
                - as_of_date: date as index

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_data_symbol_ytd(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of as_of_date (D_AS_OF), by default None
        end_date : Optional[date]
            end of as_of_date (D_AS_OF), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol: str as column
                - as_of_date: date as index

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_data_index_daily(
        self,
        field: str,
        index_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table MKTSTAT_DAILY_INDEX, MKTSTAT_DAILY_MARKET.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'high', 'low', 'close'. More fields can be found in ezyquant.fields
        index_list : Optional[List[str]]
            N_SECTOR in index_list, case insensitive, by default None. More index can be found in ezyquant.fields
        start_date : Optional[date]
            start of trade_date (D_TRADE), by default None
        end_date : Optional[date]
            end of trade_date (D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - index: str as column
                - trade_date: date as index

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()

    def get_data_sector_daily(
        self,
        field: str,
        sector_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table DAILY_SECTOR_INFO.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'high', 'low', 'close'. More fields can be found in ezyquant.fields
        sector_list : Optional[List[str]]
            N_SECTOR in sector_list, case insensitive, by default None. More sector can be found in ezyquant.fields
        start_date : Optional[date]
            start of trade_date (D_TRADE), by default None
        end_date : Optional[date]
            end of trade_date (D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - sector: str as column
                - trade_date: date as index

        Examples
        --------
        TODO: examples
        """
        return pd.DataFrame()
