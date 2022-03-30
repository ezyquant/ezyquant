import sqlite3
from datetime import date, datetime
from typing import List, Optional
import string
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, and_, create_engine, func, or_, select


class SETDataReader:
    """SETDataReader read PSIMS data."""

    def __init__(self, sqlite_path: str) -> None:
        self.__sqlite_path = sqlite_path
        self.__engine = sa.create_engine(f"sqlite:///{self.__sqlite_path}")
        print(f"sqlite:///{self.__sqlite_path}")
        self.__metadata = MetaData(self.__engine)

    def get_trading_dates(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[date]:
        t = Table("CALENDAR", self.__metadata, autoload=True)

        stmt = select([t.c.D_TRADE])
        if start_date is not None:
            stmt = stmt.where(t.c.D_TRADE >= start_date)
        if end_date is not None:
            stmt = stmt.where(t.c.D_TRADE <= end_date)

        stmt = stmt.order_by(t.c.D_TRADE)

        res = self.__engine.execute(stmt).all()
        return [i[0].date() for i in res]

    def is_trading_date(self, check_date: date) -> bool:
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
        >>> from ezyquant.reader import SETDataReader
        >>> from ezyquant.fields import *
        >>> sdr = SETDataReader("ssetdi_db.db")
        >>> sdr.get_symbol_info(["SET"])
                symbol_id symbol market  industry    sector sec_type native
        0          0         SET      A  -         --------        S      L
        >>> sdr.get_symbol_info(sector=SECTOR_MINE)
                symbol_id symbol market  industry  sector sec_type native
        0           61     THL-F      A  RESOURC   MINE          F      F
        1           61       THL      A  RESOURC   MINE          S      L
        2           61     THL-R      A  RESOURC   MINE          S      R
        3           61     THL-U      A  RESOURC   MINE          S      U
        """
        security = Table("SECURITY", self.__metadata, autoload=True)
        sect = Table("SECTOR", self.__metadata, autoload=True)
        j = security.join(
            sect,
            and_(
                security.c.I_MARKET == sect.c.I_MARKET,
                security.c.I_INDUSTRY == sect.c.I_INDUSTRY,
                security.c.I_SECTOR == sect.c.I_SECTOR,
            ),
        )
        stmt = select(
            [
                security.c.I_COMPANY.label("symbol_id"),
                func.trim(security.c.N_SECURITY).label("symbol"),
                security.c.I_MARKET.label("market"),
                sect.c.N_INDUSTRY.label("industry"),
                sect.c.N_SECTOR.label("sector"),
                security.c.I_SEC_TYPE.label("sec_type"),
                security.c.I_NATIVE.label("native"),
            ]
        ).select_from(j)
        if market != None:
            stmt = stmt.where(security.c.I_MARKET == market)
        if symbol_list != None:
            stmt = stmt.where(
                func.trim(security.c.N_SECURITY).in_([s.upper() for s in symbol_list])
            )
        if industry != None:
            stmt = stmt.where(func.trim(sect.c.N_INDUSTRY) == industry)
        if sector != None:
            stmt = stmt.where(func.trim(sect.c.N_SECTOR) == sector)

        res_df = pd.read_sql(stmt, self.__engine)
        return res_df

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
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("ssetdi_db.db")
        >>> sdr.get_company_info(symbol_list=["BBL", "PTT"])
            company_id symbol             company_name_t  ...   establish                      dvd_policy_t                                      dvd_policy_e
        0           1     BBL  ธนาคารกรุงเทพ จำกัด (มหาชน)  ...   1/12/1944   เมื่อผลประกอบการของธนาคารมีกำไร...  Pays when company has profit (with additional ...
        1         646     PTT    บริษัท ปตท. จำกัด (มหาชน)  ...   1/10/2001   ไม่ต่ำกว่าร้อยละ 25 ของกำไรสุทธิที่...  Not less than 25% of net income after deductio...

        """
        company = Table("COMPANY", self.__metadata, autoload=True)
        security = Table("SECURITY", self.__metadata, autoload=True)
        j = security.join(company, company.c.I_COMPANY == security.c.I_COMPANY)
        stmt = select(
            [
                company.c.I_COMPANY.label("company_id"),
                func.trim(security.c.N_SECURITY).label("symbol"),
                company.c.N_COMPANY_T.label("company_name_t"),
                company.c.N_COMPANY_E.label("company_name_e"),
                company.c.I_ZIP.label("zip"),
                company.c.E_TEL.label("tel"),
                company.c.E_FAX.label("fax"),
                company.c.E_EMAIL.label("email"),
                company.c.E_URL.label("url"),
                company.c.D_ESTABLISH.label("establish"),
                company.c.E_DVD_POLICY_T.label("dvd_policy_t"),
                company.c.E_DVD_POLICY_E.label("dvd_policy_e"),
            ]
        ).select_from(j)
        if symbol_list != None:
            stmt = stmt.where(
                func.trim(security.c.N_SECURITY).in_([s.upper() for s in symbol_list])
            )
        # stmt.join(security, company.c.I_COMPANY == security.c.I_COMPANY)
        res_df = pd.read_sql(stmt, self.__engine)

        return res_df

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
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("ssetdi_db.db")
        >>> sdr.get_change_name(["SMG"])
           symbol_id symbol effect_date symbol_old symbol_new
        0        220    SMG  2006-07-31        SMG      SCSMG
        1        220    SMG  2014-08-28      SCSMG        SMG
        >>> sdr.get_change_name(start_date=datetime.date(2014, 8, 28),end_date=datetime.date(2014, 8, 29))
           symbol_id    symbol effect_date  symbol_old symbol_new
        0        220       SMG  2014-08-28       SCSMG        SMG
        1        221     SMG-F  2014-08-28     SCSMG-F      SMG-F
        2        222     SMG-R  2014-08-28     SCSMG-R      SMG-R
        3       2793    SMG-W1  2014-08-28    SCSMG-W1     SMG-W1
        4       2794    SMG-WB  2014-08-28    SCSMG-WB     SMG-WB
        5       3375  SMG-W1-R  2014-08-28  SCSMG-W1-R   SMG-W1-R
        """
        security = Table("SECURITY", self.__metadata, autoload=True)
        change_name = Table("CHANGE_NAME_SECURITY", self.__metadata, autoload=True)

        j = change_name.join(
            security, security.c.I_SECURITY == change_name.c.I_SECURITY
        )
        stmt = select(
            [
                change_name.c.I_SECURITY.label("symbol_id"),
                func.trim(security.c.N_SECURITY).label("symbol"),
                change_name.c.D_EFFECT.label("effect_date"),
                func.trim(change_name.c.N_SECURITY_OLD).label("symbol_old"),
                func.trim(change_name.c.N_SECURITY_NEW).label("symbol_new"),
            ]
        ).select_from(j)
        stmt = self._list_start_end_condition(
            query_object=stmt,
            list_condition=symbol_list,
            start_date=start_date,
            end_date=end_date,
            col_list=security.c.N_SECURITY,
            col_date=change_name.c.D_EFFECT,
        )

        res_df = pd.read_sql(stmt, self.__engine)
        return res_df

    def get_dividend(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type_list: Optional[List[str]] = None,
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
        ca_type_list : Optional[List[str]]
            Coperatie action type (N_CA_TYPE), by default None
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
        security = Table("SECURITY", self.__metadata, autoload=True)
        right = Table("RIGHTS_BENEFIT", self.__metadata, autoload=True)
        j = right.join(security, security.c.I_SECURITY == right.c.I_SECURITY)
        stmt = (
            select(
                [
                    func.trim(security.c.N_SECURITY).label("symbol"),
                    right.c.D_SIGN.label("ex_date"),
                    right.c.D_BEG_PAID.label("pay_date"),
                    right.c.N_CA_TYPE.label("ca_type"),
                    right.c.Z_RIGHTS.label("dps"),
                ]
            )
            .select_from(j)
            .where(right.c.N_CA_TYPE.in_(["CD", "SD"]))
        )

        stmt = self._list_start_end_condition(
            query_object=stmt,
            list_condition=symbol_list,
            start_date=start_date,
            end_date=end_date,
            col_list=security.c.N_SECURITY,
            col_date=right.c.D_SIGN,
        )
        if ca_type_list != None:
            stmt = stmt.where(right.c.N_CA_TYPE == ca_type_list)
        res_df = pd.read_sql(stmt, self.__engine)
        return res_df

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
        security = Table("SECURITY", self.__metadata, autoload=True)
        detail = Table("SECURITY_DETAIL", self.__metadata, autoload=True)
        j = detail.join(security, security.c.I_SECURITY == detail.c.I_SECURITY)
        stmt = (
            select(
                [
                    func.trim(security.c.N_SECURITY).label("symbol"),
                    detail.c.D_DELISTED.label("delisted_date"),
                ]
            )
            .select_from(j)
            .where(detail.c.D_DELISTED != None)
        )
        stmt = self._list_start_end_condition(
            query_object=stmt,
            list_condition=symbol_list,
            start_date=start_date,
            end_date=end_date,
            col_list=security.c.N_SECURITY,
            col_date=detail.c.D_DELISTED,
        )
        res_df = pd.read_sql(stmt, self.__engine)
        return res_df

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
        ca_type_list: Optional[List[str]] = None,
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
        ca_type_list : Optional[List[str]]
            Coperatie action type (N_CA_TYPE), by default None
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
        adjusted_list: List[str] = ["  ", "CR", "PC", "RC", "SD", "XR"],
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
        adjusted_list : List[str]
            Adjust data by ca_type, empty list for no adjust, by default ["  ", "CR", "PC", "RC", "SD", "XR"]

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
        adjusted_list = list(adjusted_list)  # copy to avoid modify original list
        return pd.DataFrame()

    def get_data_symbol_quarterly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD. If field is
        duplicate in FINANCIAL_SCREEN and FINANCIAL_STAT_STD, the data from
        FINANCIAL_SCREEN will be used.

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
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD. If field is
        duplicate in FINANCIAL_SCREEN and FINANCIAL_STAT_STD, the data from
        FINANCIAL_SCREEN will be used.

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
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD. If field is
        duplicate in FINANCIAL_SCREEN and FINANCIAL_STAT_STD, the data from
        FINANCIAL_SCREEN will be used.

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
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD. If field is
        duplicate in FINANCIAL_SCREEN and FINANCIAL_STAT_STD, the data from
        FINANCIAL_SCREEN will be used.

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

    def _list_start_end_condition(
        self,
        query_object,
        list_condition: Optional[List[str]],
        col_list,
        start_date: Optional[date],
        end_date: Optional[date],
        col_date,
    ):
        """
        helper function for make query

        Parameters
        ----------
        query_object : query_object that want to fill query
        list_condition : list will be condition for col_list to be in
        col_list : column to apply list condition
        start_date : start date condition
        end_date : end date condition
        col_date : column to apply date condition that date in this column must between start_data and end_date
        """
        if list_condition != None:
            query_object = query_object.where(
                func.trim(col_list).in_([s.upper() for s in list_condition])
            )
        if start_date != None:
            query_object = query_object.where(col_date >= start_date)
        if end_date != None:
            query_object = query_object.where(col_date <= end_date)
        return query_object
