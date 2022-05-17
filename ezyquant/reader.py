import os.path
from datetime import date
from functools import lru_cache
from typing import List, Optional

import numpy as np
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import Column, MetaData, Table, and_, case, func, select
from sqlalchemy.sql import Select

from . import fields as fld
from . import utils
from . import validators as vld
from .errors import InputError


class SETDataReader:
    """SETDataReader read PSIMS data."""

    def __init__(self, sqlite_path: str, ping: bool = True):
        """SETDataReader constructor.

        Parameters
        ----------
        sqlite_path : str
            path to sqlite file e.g. /path/to/sqlite.db
        ping : bool, optional
            check database connection, by default True
        """
        self.__sqlite_path = sqlite_path

        self.__engine = sa.create_engine(f"sqlite:///{self.__sqlite_path}")
        self.__metadata = MetaData(self.__engine)

        if ping:
            if not os.path.isfile(self.__sqlite_path):
                raise InputError(f"{self.__sqlite_path} is not found")

            self.last_update()

    def last_table_update(self, table_name: str) -> str:
        """Last D_TRADE in table.

        Parameters
        ----------
        table_name : str
            name of table

        Returns
        -------
        str
            string with format YYYY-MM-DD
        """
        t = self._table(table_name)
        stmt = select([func.max(func.DATE(t.c.D_TRADE))])
        return self.__engine.execute(stmt).scalar()

    def last_update(self) -> str:
        """Last database update, checking from last D_TRADE in following
        tables:

            - DAILY_STOCK_TRADE
            - DAILY_STOCK_STAT
            - MKTSTAT_DAILY_INDEX
            - MKTSTAT_DAILY_MARKET
            - DAILY_SECTOR_INFO

        Returns
        -------
        str
            string with format YYYY-MM-DD
        """
        d1 = self.last_table_update("DAILY_STOCK_TRADE")
        d2 = self.last_table_update("DAILY_STOCK_STAT")
        d3 = self.last_table_update("MKTSTAT_DAILY_INDEX")
        d4 = self.last_table_update("MKTSTAT_DAILY_MARKET")
        d5 = self.last_table_update("DAILY_SECTOR_INFO")
        assert d1 == d2 == d3 == d4 == d5, "database is not consistent"
        return d1

    def get_trading_dates(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[str]:
        """Data from table CALENDAR.

        Parameters
        ----------
        start_date : Optional[str]
            start of D_TRADE, by default None
        end_date : Optional[str]
            end of D_TRADE, by default None

        Returns
        -------
        List[str]
            list of string with format YYYY-MM-DD
        """
        calendar_t = self._table("CALENDAR")

        stmt = select([func.DATE(calendar_t.c.D_TRADE)]).order_by(
            func.DATE(calendar_t.c.D_TRADE)
        )

        stmt = self._filter_stmt_by_date(
            stmt=stmt,
            column=calendar_t.c.D_TRADE,
            start_date=start_date,
            end_date=end_date,
        )

        res = self.__engine.execute(stmt).all()

        return [i[0] for i in res]

    def is_trading_date(self, check_date: str) -> bool:
        """Data from table CALENDAR.

        Parameters
        ----------
        check_date : str
            string with format YYYY-MM-DD

        Returns
        -------
        bool
            is trading date
        """
        calendar_t = self._table("CALENDAR")

        stmt = select([func.count(calendar_t.c.D_TRADE)]).where(
            func.DATE(calendar_t.c.D_TRADE) == check_date
        )

        res = self.__engine.execute(stmt).scalar()

        assert isinstance(res, int)
        return res > 0

    def is_today_trading_date(self) -> bool:
        """Data from table CALENDAR.

        Returns
        -------
        bool
            is today trading date
        """
        return self.is_trading_date(utils.date_to_str(date.today()))

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
            I_MARKET e.g. 'SET', 'mai', by default None
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
        >>> from ezyquant import fields as fld
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_symbol_info(["BBL"])
           symbol_id symbol market industry sector sec_type native
        0          1    BBL    SET  FINCIAL   BANK        S      L
        >>> sdr.get_symbol_info(sector=fld.SECTOR_MINE)
           symbol_id symbol market industry sector sec_type native
        0        167    THL    SET  RESOURC   MINE        S      L
        1        168  THL-R    SET  RESOURC   MINE        S      R
        2        169  THL-U    SET  RESOURC   MINE        S      U
        3       2968  THL-F    SET  RESOURC   MINE        F      F
        """
        security_t = self._table("SECURITY")
        sector_t = self._table("SECTOR")

        j = self._join_sector_table(security_t, isouter=True)
        stmt = (
            select(
                [
                    security_t.c.I_SECURITY.label("symbol_id"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    security_t.c.I_MARKET.label("market"),
                    func.trim(sector_t.c.N_INDUSTRY).label("industry"),
                    func.trim(sector_t.c.N_SECTOR).label("sector"),
                    security_t.c.I_SEC_TYPE.label("sec_type"),
                    security_t.c.I_NATIVE.label("native"),
                ]
            )
            .select_from(j)
            .order_by(security_t.c.I_SECURITY)
        )

        stmt = self._filter_str_in_list(
            stmt=stmt, column=security_t.c.N_SECURITY, values=symbol_list
        )
        if market != None:
            market = market.upper()
            stmt = stmt.where(security_t.c.I_MARKET == fld.MARKET_MAP_UPPER[market])
        if industry != None:
            industry = industry.upper()
            stmt = stmt.where(func.trim(sector_t.c.N_INDUSTRY) == industry)
        if sector != None:
            sector = sector.upper()
            stmt = stmt.where(func.trim(sector_t.c.N_SECTOR) == sector)

        res_df = pd.read_sql_query(stmt, self.__engine)

        map_market = {v: k for k, v in fld.MARKET_MAP.items()}
        res_df["market"] = res_df["market"].replace(map_market)

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
                - address_t: str - A_COMPANY_T
                - address_e: str - A_COMPANY_E
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
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_company_info(symbol_list=["BBL", "PTT"])
           company_id symbol               company_name_t  ...  establish                                       dvd_policy_t                                       dvd_policy_e
        0           1    BBL  ธนาคารกรุงเทพ จำกัด (มหาชน)  ...  1/12/1944  เมื่อผลประกอบการของธนาคารมีกำไร (โดยมีเงื่อนไข...  Pays when company has profit (with additional ...
        1         646    PTT    บริษัท ปตท. จำกัด (มหาชน)  ...  1/10/2001  ไม่ต่ำกว่าร้อยละ 25 ของกำไรสุทธิที่เหลือหลังหั...  Not less than 25% of net income after deductio...
        """
        company_t = self._table("COMPANY")
        security_t = self._table("SECURITY")

        j = security_t.join(company_t, company_t.c.I_COMPANY == security_t.c.I_COMPANY)
        stmt = (
            select(
                [
                    company_t.c.I_COMPANY.label("company_id"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    company_t.c.N_COMPANY_T.label("company_name_t"),
                    company_t.c.N_COMPANY_E.label("company_name_e"),
                    company_t.c.A_COMPANY_T.label("address_t"),
                    company_t.c.A_COMPANY_E.label("address_e"),
                    company_t.c.I_ZIP.label("zip"),
                    company_t.c.E_TEL.label("tel"),
                    company_t.c.E_FAX.label("fax"),
                    company_t.c.E_EMAIL.label("email"),
                    company_t.c.E_URL.label("url"),
                    func.trim(company_t.c.D_ESTABLISH).label("establish"),
                    company_t.c.E_DVD_POLICY_T.label("dvd_policy_t"),
                    company_t.c.E_DVD_POLICY_E.label("dvd_policy_e"),
                ]
            )
            .select_from(j)
            .order_by(company_t.c.I_COMPANY)
        )

        stmt = self._filter_str_in_list(
            stmt=stmt, column=security_t.c.N_SECURITY, values=symbol_list
        )

        res_df = pd.read_sql_query(stmt, self.__engine)
        return res_df

    def get_change_name(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table CHANGE_NAME_SECURITY.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of effect_date (D_EFFECT), by default None
        end_date : Optional[str]
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
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_change_name(["SMG"])
           symbol_id symbol effect_date symbol_old symbol_new
        0        220    SMG  2006-07-31        SMG      SCSMG
        1        220    SMG  2014-08-28      SCSMG        SMG
        >>> sdr.get_change_name(start_date="2014-08-28", end_date="2014-08-29")
           symbol_id    symbol effect_date  symbol_old symbol_new
        0        220       SMG  2014-08-28       SCSMG        SMG
        1        221     SMG-F  2014-08-28     SCSMG-F      SMG-F
        2        222     SMG-R  2014-08-28     SCSMG-R      SMG-R
        3       2793    SMG-W1  2014-08-28    SCSMG-W1     SMG-W1
        4       2794    SMG-WB  2014-08-28    SCSMG-WB     SMG-WB
        5       3375  SMG-W1-R  2014-08-28  SCSMG-W1-R   SMG-W1-R
        """
        security_t = self._table("SECURITY")
        change_name_t = self._table("CHANGE_NAME_SECURITY")

        j = change_name_t.join(
            security_t, security_t.c.I_SECURITY == change_name_t.c.I_SECURITY
        )
        stmt = (
            select(
                [
                    change_name_t.c.I_SECURITY.label("symbol_id"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    change_name_t.c.D_EFFECT.label("effect_date"),
                    func.trim(change_name_t.c.N_SECURITY_OLD).label("symbol_old"),
                    func.trim(change_name_t.c.N_SECURITY_NEW).label("symbol_new"),
                ]
            )
            .select_from(j)
            .where(change_name_t.c.D_EFFECT != None)
            .where(
                func.trim(change_name_t.c.N_SECURITY_OLD)
                != func.trim(change_name_t.c.N_SECURITY_NEW)
            )
            .order_by(func.DATE(change_name_t.c.D_EFFECT))
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=change_name_t.c.D_EFFECT,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        res_df = pd.read_sql_query(stmt, self.__engine)
        res_df = res_df.drop_duplicates(ignore_index=True)
        return res_df

    def get_dividend(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ca_type_list: Optional[List[str]] = None,
        adjusted_list: List[str] = ["  ", "CR", "PC", "RC", "SD", "XR"],
    ) -> pd.DataFrame:
        """Data from table RIGHTS_BENEFIT. Include only Cash Dividend (CD) and
        Stock Dividend (SD). Not include Cancelled (F_CANCEL!='C') and dps more
        than 0 (Z_RIGHTS>0). ex_date and pay_date can be null.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of ex_date (D_SIGN), by default None
        end_date : Optional[str]
            end of ex_date (D_SIGN), by default None
        ca_type_list : Optional[List[str]]
            Coperatie action type (N_CA_TYPE), by default None
                - CD - cash dividend
                - SD - stock dividend
        adjusted_list : List[str]
            Adjust data by ca_type, empty list for no adjust, by default ["  ", "CR", "PC", "RC", "SD", "XR"]

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
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_dividend(["M"])
           symbol     ex_date    pay_date ca_type  dps
        0       M  2014-05-06  2014-05-21      CD  1.6
        1       M  2014-08-20  2014-09-04      CD  0.8
        2       M  2015-04-30  2015-05-21      CD  1.0
        3       M  2015-08-24  2015-09-08      CD  0.9
        4       M  2016-04-28  2016-05-19      CD  1.0
        5       M  2016-08-23  2016-09-08      CD  1.0
        6       M  2017-05-04  2017-05-23      CD  1.1
        7       M  2017-08-22  2017-09-08      CD  1.1
        8       M  2018-05-07  2018-05-23      CD  1.2
        9       M  2018-08-22  2018-09-07      CD  1.2
        10      M  2019-05-07  2019-05-23      CD  1.3
        11      M  2019-08-26  2019-09-11      CD  1.3
        12      M  2020-04-22  2020-05-08      CD  1.3
        13      M  2020-08-24  2020-09-10      CD  0.5
        14      M  2021-05-10  2021-05-25      CD  0.5
        15      M  2022-05-10  2022-05-25      CD  0.8
        >>> sdr.get_dividend(["M"], start_date="2020-07-28", end_date="2022-05-11")
            symbol     ex_date    pay_date ca_type  dps
        0        M  2020-08-24  2020-09-10      CD  0.5
        1        M  2021-05-10  2021-05-25      CD  0.5
        2        M  2022-05-10  2022-05-25      CD  0.8
        """
        security_t = self._table("SECURITY")
        rights_benefit_t = self._table("RIGHTS_BENEFIT")

        j = rights_benefit_t.join(
            security_t, security_t.c.I_SECURITY == rights_benefit_t.c.I_SECURITY
        )
        stmt = (
            select(
                [
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    rights_benefit_t.c.D_SIGN.label("ex_date"),
                    rights_benefit_t.c.D_BEG_PAID.label("pay_date"),
                    func.trim(rights_benefit_t.c.N_CA_TYPE).label("ca_type"),
                    rights_benefit_t.c.Z_RIGHTS.label("dps"),
                ]
            )
            .select_from(j)
            .where(func.trim(rights_benefit_t.c.N_CA_TYPE).in_(["CD", "SD"]))
            .where(func.trim(rights_benefit_t.c.F_CANCEL) != "C")
            .where(rights_benefit_t.c.Z_RIGHTS > 0)
            .order_by(func.DATE(rights_benefit_t.c.D_SIGN))
        )

        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=rights_benefit_t.c.D_SIGN,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )
        stmt = self._filter_str_in_list(
            stmt=stmt, column=rights_benefit_t.c.N_CA_TYPE, values=ca_type_list
        )

        res_df = pd.read_sql_query(stmt, self.__engine)

        res_df = self._merge_adjust_factor_dividend(res_df, adjusted_list=adjusted_list)

        return res_df

    def get_delisted(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_DETAIL. Filter delisted by D_DELISTED !=
        None.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of delisted_date (D_DELISTED), by default None
        end_date : Optional[str]
            end of delisted_date (D_DELISTED), by default None

        Returns
        -------
        pd.DataFrame
            delisted dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - delisted_date: date - D_DELISTED

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_delisted(start_date="2020-02-20", end_date="2020-02-20")
             symbol delisted_date
        0    ROBINS    2020-02-20
        1    KK202A    2020-02-20
        2  CB20220A    2020-02-20
        3  CB20220B    2020-02-20
        """
        security_t = self._table("SECURITY")
        security_detail_t = self._table("SECURITY_DETAIL")

        j = security_detail_t.join(
            security_t, security_t.c.I_SECURITY == security_detail_t.c.I_SECURITY
        )
        stmt = (
            select(
                [
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    security_detail_t.c.D_DELISTED.label("delisted_date"),
                ]
            )
            .select_from(j)
            .where(security_detail_t.c.D_DELISTED != None)
            .order_by(func.DATE(security_detail_t.c.D_DELISTED))
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=security_detail_t.c.D_DELISTED,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        res_df = pd.read_sql_query(stmt, self.__engine)
        return res_df

    def get_sign_posting(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sign_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Data from table SIGN_POSTING.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of hold_date (D_HOLD), by default None
        end_date : Optional[str]
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
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_sign_posting(symbol_list=["THAI"], start_date="2020-11-12", end_date="2021-02-25")
          symbol  hold_date sign
        0   THAI 2020-11-12   SP
        1   THAI 2021-02-25   SP
        """
        security_t = self._table("SECURITY")
        sign_posting_t = self._table("SIGN_POSTING")

        j = sign_posting_t.join(
            security_t, security_t.c.I_SECURITY == sign_posting_t.c.I_SECURITY
        )
        stmt = (
            select(
                [
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    sign_posting_t.c.D_HOLD.label("hold_date"),
                    func.trim(sign_posting_t.c.N_SIGN).label("sign"),
                ]
            )
            .select_from(j)
            .order_by(func.DATE(sign_posting_t.c.D_HOLD))
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=sign_posting_t.c.D_HOLD,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )
        stmt = self._filter_str_in_list(
            stmt=stmt, column=sign_posting_t.c.N_SIGN, values=sign_list
        )

        res_df = pd.read_sql_query(stmt, self.__engine)
        return res_df

    def get_symbols_by_index(
        self,
        index_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
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
        start_date : Optional[str]
            start of as_of_date (D_AS_OF), by default None
        end_date : Optional[str]
            end of as_of_date (D_AS_OF), by default None

        Returns
        -------
        pd.DataFrame
            - as_of_date: date - D_AS_OF
            - index: str - SECTOR.N_SECTOR
            - symbol: str - SECURITY.N_SECURITY
            - seq: int - SECURITY_INDEX.S_SEQ

        Note
        -------
        - SET50 filter S_SEQ 1-50
        - SET100 filter S_SEQ 1-100
        - SETHD filter S_SEQ 1-30

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_symbols_by_index(index_list=["SET50"], start_date="2022-01-04", end_date="2022-01-04")
           as_of_date  index  symbol  seq
        0  2022-01-04  SET50     OSP    1
        1  2022-01-04  SET50     CBG    2
        2  2022-01-04  SET50      TU    3
        3  2022-01-04  SET50    MINT    4
        4  2022-01-04  SET50     CPF    5
        5  2022-01-04  SET50    STGT    6
        6  2022-01-04  SET50   TISCO    7
        7  2022-01-04  SET50     KTB    8
        8  2022-01-04  SET50     TTB    9
        9  2022-01-04  SET50     SCB   10
        10 2022-01-04  SET50   KBANK   11
        11 2022-01-04  SET50     BBL   12
        12 2022-01-04  SET50  TIDLOR   13
        13 2022-01-04  SET50     MTC   14
        14 2022-01-04  SET50   SAWAD   15
        15 2022-01-04  SET50     KTC   16
        16 2022-01-04  SET50   PTTGC   17
        17 2022-01-04  SET50     IVL   18
        18 2022-01-04  SET50    SCGP   19
        19 2022-01-04  SET50     SCC   20
        20 2022-01-04  SET50     AWC   21
        21 2022-01-04  SET50     CPN   22
        22 2022-01-04  SET50      LH   23
        23 2022-01-04  SET50      OR   24
        24 2022-01-04  SET50    GULF   25
        25 2022-01-04  SET50   BGRIM   26
        26 2022-01-04  SET50    GPSC   27
        27 2022-01-04  SET50      EA   28
        28 2022-01-04  SET50     TOP   29
        29 2022-01-04  SET50     PTT   30
        30 2022-01-04  SET50   RATCH   31
        31 2022-01-04  SET50    IRPC   32
        32 2022-01-04  SET50    EGCO   33
        33 2022-01-04  SET50   PTTEP   34
        34 2022-01-04  SET50   BANPU   35
        35 2022-01-04  SET50     CRC   36
        36 2022-01-04  SET50    COM7   37
        37 2022-01-04  SET50  GLOBAL   38
        38 2022-01-04  SET50   CPALL   39
        39 2022-01-04  SET50   HMPRO   40
        40 2022-01-04  SET50    BDMS   41
        41 2022-01-04  SET50      BH   42
        42 2022-01-04  SET50     BEM   43
        43 2022-01-04  SET50     AOT   44
        44 2022-01-04  SET50     BTS   45
        45 2022-01-04  SET50    DTAC   46
        46 2022-01-04  SET50    TRUE   47
        47 2022-01-04  SET50  ADVANC   48
        48 2022-01-04  SET50  INTUCH   49
        49 2022-01-04  SET50     KCE   50
        """
        security_t = self._table("SECURITY")
        sector_t = self._table("SECTOR")
        security_index_t = self._table("SECURITY_INDEX")

        j = self._join_sector_table(security_index_t).join(
            security_t, security_t.c.I_SECURITY == security_index_t.c.I_SECURITY
        )
        stmt = (
            select(
                [
                    security_index_t.c.D_AS_OF.label("as_of_date"),
                    func.trim(sector_t.c.N_SECTOR).label("index"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    security_index_t.c.S_SEQ.label("seq"),
                ]
            )
            .select_from(j)
            .where(
                case(
                    (
                        func.trim(sector_t.c.N_SECTOR) == fld.INDEX_SET50,
                        security_index_t.c.S_SEQ <= 50,
                    ),
                    (
                        func.trim(sector_t.c.N_SECTOR) == fld.INDEX_SET100,
                        security_index_t.c.S_SEQ <= 100,
                    ),
                    (
                        func.trim(sector_t.c.N_SECTOR) == fld.INDEX_SETHD,
                        security_index_t.c.S_SEQ <= 30,
                    ),
                    else_=True,
                )
            )
            .order_by(
                func.DATE(security_index_t.c.D_AS_OF),
                sector_t.c.N_SECTOR,
                security_index_t.c.S_SEQ,
            )
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=sector_t.c.N_SECTOR,
            date_column=security_index_t.c.D_AS_OF,
            symbol_list=index_list,
            start_date=start_date,
            end_date=end_date,
        )

        res_df = pd.read_sql_query(stmt, self.__engine)

        return res_df

    def get_adjust_factor(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ca_type_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Data from table ADJUST_FACTOR.

        Parameters
        ----------
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of effect_date (D_EFFECT), by default None
        end_date : Optional[str]
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
                - adjust_factor: float - R_ADJUST_FACTOR

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_adjust_factor(symbol_list=["RAM"])
          symbol effect_date ca_type  adjust_factor
        0    RAM  2019-06-17      PC           0.05
        1    RAM  2021-11-09      PC           0.20
        """
        security_t = self._table("SECURITY")
        adjust_factor_t = self._table("ADJUST_FACTOR")

        j = adjust_factor_t.join(
            security_t, security_t.c.I_SECURITY == adjust_factor_t.c.I_SECURITY
        )
        stmt = (
            select(
                [
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    adjust_factor_t.c.D_EFFECT.label("effect_date"),
                    adjust_factor_t.c.N_CA_TYPE.label("ca_type"),
                    adjust_factor_t.c.R_ADJUST_FACTOR.label("adjust_factor"),
                ]
            )
            .select_from(j)
            .order_by(func.DATE(adjust_factor_t.c.D_EFFECT))
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=adjust_factor_t.c.D_EFFECT,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )
        stmt = self._filter_str_in_list(
            stmt=stmt, column=adjust_factor_t.c.N_CA_TYPE, values=ca_type_list
        )

        res_df = pd.read_sql_query(stmt, self.__engine)

        return res_df

    def get_data_symbol_daily(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjusted_list: List[str] = ["  ", "CR", "PC", "RC", "SD", "XR"],
    ) -> pd.DataFrame:
        """Data from table DAILY_STOCK_TRADE, DAILY_STOCK_STAT. Filter only
        Auto Matching (I_TRADING_METHOD='A'). Replace 0 with NaN in following
        field e.g. prior, open, high, low, close, average, last_bid,
        last_offer.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'open', 'high', 'low', 'close', 'volume'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of trade_date (D_TRADE), by default None
        end_date : Optional[str]
            end of trade_date (D_TRADE), by default None
        adjusted_list : List[str]
            Adjust data by ca_type, empty list for no adjust, by default ["  ", "CR", "PC", "RC", "SD", "XR"]

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade_date(D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_symbol_daily(
        ...    field=fld.D_CLOSE,
        ...    symbol_list=["COM7", "MALEE"],
        ...    start_date="2022-01-01",
        ...    end_date="2022-01-10",
        ... )
                      COM7  MALEE
        2022-01-04  41.875   6.55
        2022-01-05  41.625   6.50
        2022-01-06  41.500   6.50
        2022-01-07  41.000   6.40
        2022-01-10  40.875   6.30
        """
        adjusted_list = list(adjusted_list)  # copy to avoid modify original list

        field = field.lower()
        if symbol_list:
            symbol_list = [i.upper() for i in symbol_list]

        security_t = self._table("SECURITY")

        if field in fld.DAILY_STOCK_TRADE_MAP:
            daily_stock_t = self._table("DAILY_STOCK_TRADE")
            field_col = daily_stock_t.c[fld.DAILY_STOCK_TRADE_MAP[field]].label(field)
        elif field in fld.DAILY_STOCK_STAT_MAP:
            daily_stock_t = self._table("DAILY_STOCK_STAT")
            field_col = daily_stock_t.c[fld.DAILY_STOCK_STAT_MAP[field]].label(field)
        else:
            raise InputError(
                f"{field} is not a valid field. More fields can be found in ezyquant.fields"
            )

        j = daily_stock_t.join(
            security_t, daily_stock_t.c.I_SECURITY == security_t.c.I_SECURITY
        )

        stmt = (
            select(
                [
                    daily_stock_t.c.D_TRADE.label("trade_date"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    field_col,
                ]
            )
            .select_from(j)
            .order_by(func.DATE(daily_stock_t.c.D_TRADE))
        )
        if "I_TRADING_METHOD" in daily_stock_t.c:
            stmt = stmt.where(
                func.trim(daily_stock_t.c.I_TRADING_METHOD) == "A"
            )  # Auto Matching

        vld.check_start_end_date(
            start_date=start_date,
            end_date=end_date,
            last_update_date=self.last_table_update(daily_stock_t.name),
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=daily_stock_t.c.D_TRADE,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = pd.read_sql_query(
            stmt, self.__engine, index_col="trade_date", parse_dates="trade_date"
        )

        df = df.pivot(columns="symbol", values=field)

        df.index.name = None
        df.columns.name = None

        if field in {
            fld.D_PRIOR,
            fld.D_OPEN,
            fld.D_HIGH,
            fld.D_LOW,
            fld.D_CLOSE,
            fld.D_AVERAGE,
            fld.D_LAST_BID,
            fld.D_LAST_OFFER,
            fld.D_DPS,
            fld.D_EPS,
            fld.D_ACC_DPS,
        }:
            df = self._merge_adjust_factor(
                df, is_multiply=True, adjusted_list=adjusted_list
            )
        elif field in {
            fld.D_VOLUME,
            fld.D_TOTAL_VOLUME,
        }:
            df = self._merge_adjust_factor(
                df, is_multiply=False, adjusted_list=adjusted_list
            )

        if symbol_list != None:
            df = df.reindex(columns=[i for i in symbol_list if i in df.columns])  # type: ignore

        return df

    def get_data_symbol_quarterly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from tables FINANCIAL_STAT_STD and FINANCIAL_SCREEN. If field
        is in both table, the data from FINANCIAL_STAT_STD will be used.
        FINANCIAL_STAT_STD using data from column M_ACCOUNT. FINANCIAL_SCREEN
        filter by I_PERIOD_TYPE='QY' and I_PERIOD in ('Q1','Q2','Q3','Q4').
        Index date is trade date (DAILY_STOCK_STAT.D_TRADE). Data is showing at
        first trade date which join on D_AS_OF.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[str]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_symbol_quarterly(
        ...     field=fld.Q_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7      MALEE
        2022-02-01          NaN        NaN
        2022-02-02          NaN        NaN
        2022-02-03          NaN        NaN
        2022-02-04          NaN        NaN
        2022-02-07          NaN        NaN
        2022-02-08          NaN        NaN
        2022-02-09          NaN        NaN
        2022-02-10          NaN        NaN
        2022-02-11          NaN        NaN
        2022-02-14          NaN        NaN
        2022-02-15          NaN        NaN
        2022-02-17          NaN        NaN
        2022-02-18          NaN        NaN
        2022-02-21          NaN        NaN
        2022-02-22          NaN        NaN
        2022-02-23          NaN        NaN
        2022-02-24          NaN        NaN
        2022-02-25          NaN        NaN
        2022-02-28          NaN        NaN
        2022-03-01          NaN  953995.79
        2022-03-02          NaN        NaN
        2022-03-03          NaN        NaN
        2022-03-04  17573710.66        NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            period="Q",
        )

    def get_data_symbol_yearly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_STAT_STD and FINANCIAL_SCREEN. If field is
        in both table, the data from FINANCIAL_STAT_STD will be used.
        FINANCIAL_STAT_STD filter by "I_QUARTER"='9' and using data from column
        M_ACCOUNT. FINANCIAL_SCREEN filter by I_PERIOD_TYPE='QY' and
        I_PERIOD='YE'. Index date is trade date (DAILY_STOCK_STAT.D_TRADE).
        Data is showing at first trade date which join on D_AS_OF.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[str]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_symbol_yearly(
        ...     field=fld.Y_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7       MALEE
        2022-02-01          NaN         NaN
        2022-02-02          NaN         NaN
        2022-02-03          NaN         NaN
        2022-02-04          NaN         NaN
        2022-02-07          NaN         NaN
        2022-02-08          NaN         NaN
        2022-02-09          NaN         NaN
        2022-02-10          NaN         NaN
        2022-02-11          NaN         NaN
        2022-02-14          NaN         NaN
        2022-02-15          NaN         NaN
        2022-02-17          NaN         NaN
        2022-02-18          NaN         NaN
        2022-02-21          NaN         NaN
        2022-02-22          NaN         NaN
        2022-02-23          NaN         NaN
        2022-02-24          NaN         NaN
        2022-02-25          NaN         NaN
        2022-02-28          NaN         NaN
        2022-03-01          NaN  3488690.79
        2022-03-02          NaN         NaN
        2022-03-03          NaN         NaN
        2022-03-04  51154660.73         NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            period="Y",
        )

    def get_data_symbol_ttm(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Trailing 12 months (TTM) is a term used to describe the past 12
        consecutive months of a company's performance data. TTM can be
        calculate only Income Statement and Cashflow, but not Financial Ratio
        and Balance Sheet. Data from table FINANCIAL_STAT_STD,
        FINANCIAL_SCREEN. If field is in both table, the data from
        FINANCIAL_SCREEN will be used. FINANCIAL_STAT_STD filter by using data
        from column M_ACC_ACCOUNT_12M. FINANCIAL_SCREEN don't have TTM data.
        Index date is trade date (DAILY_STOCK_STAT.D_TRADE). Data is showing at
        first trade date which join on D_AS_OF.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[str]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_symbol_ttm(
        ...     field=fld.Q_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7       MALEE
        2022-02-01          NaN         NaN
        2022-02-02          NaN         NaN
        2022-02-03          NaN         NaN
        2022-02-04          NaN         NaN
        2022-02-07          NaN         NaN
        2022-02-08          NaN         NaN
        2022-02-09          NaN         NaN
        2022-02-10          NaN         NaN
        2022-02-11          NaN         NaN
        2022-02-14          NaN         NaN
        2022-02-15          NaN         NaN
        2022-02-17          NaN         NaN
        2022-02-18          NaN         NaN
        2022-02-21          NaN         NaN
        2022-02-22          NaN         NaN
        2022-02-23          NaN         NaN
        2022-02-24          NaN         NaN
        2022-02-25          NaN         NaN
        2022-02-28          NaN         NaN
        2022-03-01          NaN  3488690.79
        2022-03-02          NaN         NaN
        2022-03-03          NaN         NaN
        2022-03-04  51154660.73         NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            period="TTM",
        )

    def get_data_symbol_ytd(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Year to date (YTD) refers to the period of time beginning the first
        day of the current calendar year or fiscal year up to the current date.
        Data from table FINANCIAL_STAT_STD and FINANCIAL_SCREEN. If field is in
        both table, the data from FINANCIAL_STAT_STD will be used.
        FINANCIAL_STAT_STD using data from column M_ACC_ACCOUNT.
        FINANCIAL_SCREEN filter by I_PERIOD_TYPE='QY' and I_PERIOD in
        ('Q1','6M','9M','YE'). Index date is trade date
        (DAILY_STOCK_STAT.D_TRADE). Data is showing at first
        DAILY_STOCK_STAT.D_TRADE which join on D_AS_OF.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[str]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[str]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_symbol_ytd(
        ...     field=fld.Q_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7       MALEE
        2022-02-01          NaN         NaN
        2022-02-02          NaN         NaN
        2022-02-03          NaN         NaN
        2022-02-04          NaN         NaN
        2022-02-07          NaN         NaN
        2022-02-08          NaN         NaN
        2022-02-09          NaN         NaN
        2022-02-10          NaN         NaN
        2022-02-11          NaN         NaN
        2022-02-14          NaN         NaN
        2022-02-15          NaN         NaN
        2022-02-17          NaN         NaN
        2022-02-18          NaN         NaN
        2022-02-21          NaN         NaN
        2022-02-22          NaN         NaN
        2022-02-23          NaN         NaN
        2022-02-24          NaN         NaN
        2022-02-25          NaN         NaN
        2022-02-28          NaN         NaN
        2022-03-01          NaN  3488690.79
        2022-03-02          NaN         NaN
        2022-03-03          NaN         NaN
        2022-03-04  51154660.73         NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            period="YTD",
        )

    def get_data_index_daily(
        self,
        field: str,
        index_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table MKTSTAT_DAILY_INDEX, MKTSTAT_DAILY_MARKET.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'high', 'low', 'close'. More fields can be found in ezyquant.fields
        index_list : Optional[List[str]]
            N_SECTOR in index_list, case insensitive, by default None. More index can be found in ezyquant.fields
        start_date : Optional[str]
            start of trade_date (D_TRADE), by default None
        end_date : Optional[str]
            end of trade_date (D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - index: str as column
                - trade_date: date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_index_daily(
        ...     field=fld.D_INDEX_CLOSE,
        ...     index_list=[fld.INDEX_SET, fld.INDEX_SET100],
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ... )
                        SET   SET100
        2022-01-04  1670.28  2283.56
        2022-01-05  1676.79  2291.71
        2022-01-06  1653.03  2251.78
        2022-01-07  1657.62  2257.40
        2022-01-10  1657.06  2256.14
        """
        sector_t = self._table("SECTOR")

        field = field.lower()
        if field in fld.MKTSTAT_DAILY_INDEX_MAP:
            mktstat_daily_t = self._table("MKTSTAT_DAILY_INDEX")
            field_col = mktstat_daily_t.c[fld.MKTSTAT_DAILY_INDEX_MAP[field]]
        elif field in fld.MKTSTAT_DAILY_MARKET_MAP:
            mktstat_daily_t = self._table("MKTSTAT_DAILY_MARKET")
            field_col = mktstat_daily_t.c[fld.MKTSTAT_DAILY_MARKET_MAP[field]]
        else:
            raise ValueError(
                f"{field} not in Data 1D field. Please check psims factor for more details."
            )

        j = self._join_sector_table(mktstat_daily_t)

        sql = (
            select(
                [
                    mktstat_daily_t.c.D_TRADE.label("trade_date"),
                    func.trim(sector_t.c.N_SECTOR).label("index"),
                    field_col.label(field),
                ]
            )
            .select_from(j)
            .order_by(func.DATE(mktstat_daily_t.c.D_TRADE))
        )

        vld.check_start_end_date(
            start_date=start_date,
            end_date=end_date,
            last_update_date=self.last_table_update(mktstat_daily_t.name),
        )
        sql = self._filter_stmt_by_symbol_and_date(
            stmt=sql,
            symbol_column=sector_t.c.N_SECTOR,
            date_column=mktstat_daily_t.c.D_TRADE,
            symbol_list=index_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = pd.read_sql_query(
            sql, self.__engine, index_col="trade_date", parse_dates="trade_date"
        )

        df = df.pivot(columns="index", values=field)
        df.columns.name = None
        df.index.name = None

        return df

    def get_data_sector_daily(
        self,
        field: str,
        market: str = fld.MARKET_SET,
        sector_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table DAILY_SECTOR_INFO. Filter only sector data.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'high', 'low', 'close'. More fields can be found in ezyquant.fields
        market : str
            I_MARKET e.g. 'SET', 'mai', by default 'SET'
        sector_list : Optional[List[str]]
            N_SECTOR in sector_list, case insensitive, by default None. More sector can be found in ezyquant.fields
        start_date : Optional[str]
            start of trade_date (D_TRADE), by default None
        end_date : Optional[str]
            end of trade_date (D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - sector: str as column
                - trade_date: date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_sector_daily(
        ...     field=fld.D_SECTOR_CLOSE,
        ...     sector_list=[fld.SECTOR_AGRI, fld.SECTOR_BANK],
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ... )
                      AGRI    BANK
        2022-01-04  296.13  421.31
        2022-01-05  297.66  423.08
        2022-01-06  299.85  417.30
        2022-01-07  300.12  421.00
        2022-01-10  306.93  423.81
        """
        return self._get_daily_sector_info(
            field=field,
            sector_list=sector_list,
            start_date=start_date,
            end_date=end_date,
            market=market,
            f_data="S",  # sector
        )

    def get_data_industry_daily(
        self,
        field: str,
        market: str = fld.MARKET_SET,
        industry_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table DAILY_SECTOR_INFO. Filter only industry data.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'high', 'low', 'close'. More fields can be found in ezyquant.fields
        market : str
            I_MARKET e.g. 'SET', 'mai', by default 'SET'
        industry_list : Optional[List[str]]
            N_SECTOR in industry_list, case insensitive, by default None. More industry can be found in ezyquant.fields
        start_date : Optional[str]
            start of trade_date (D_TRADE), by default None
        end_date : Optional[str]
            end of trade_date (D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - industry: str as column
                - trade_date: date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_data_industry_daily(
        ...     field=fld.D_INDUSTRY_CLOSE,
        ...     industry_list=[fld.INDUSTRY_AGRO, fld.INDUSTRY_CONSUMP],
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ... )
                      AGRO  CONSUMP
        2022-01-04  485.98    92.55
        2022-01-05  484.98    93.21
        2022-01-06  482.90    92.96
        2022-01-07  484.50    93.04
        2022-01-10  487.10    93.97
        """
        return self._get_daily_sector_info(
            field=field,
            sector_list=industry_list,
            start_date=start_date,
            end_date=end_date,
            market=market,
            f_data="I",  # industry
        )

    """
    Protected methods
    """

    def _table(self, name: str) -> Table:
        return Table(name, self.__metadata, autoload=True)

    def _filter_stmt_by_date(
        self,
        stmt: Select,
        column: Column,
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        vld.check_start_end_date(start_date, end_date)

        if start_date != None:
            stmt = stmt.where(func.DATE(column) >= func.DATE(start_date))
        if end_date != None:
            stmt = stmt.where(func.DATE(column) <= func.DATE(end_date))

        return stmt

    def _filter_str_in_list(
        self, stmt: Select, column: Column, values: Optional[List[str]]
    ):
        vld.check_duplicate(values)
        if values != None:
            values = [i.upper() for i in values]
            stmt = stmt.where(func.upper(func.trim(column)).in_(values))
        return stmt

    def _filter_stmt_by_symbol_and_date(
        self,
        stmt: Select,
        symbol_column: Column,
        date_column: Column,
        symbol_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        stmt = self._filter_str_in_list(
            stmt=stmt, column=symbol_column, values=symbol_list
        )
        stmt = self._filter_stmt_by_date(
            stmt=stmt, column=date_column, start_date=start_date, end_date=end_date
        )
        return stmt

    def _get_pivot_adjust_factor_df(
        self,
        min_date: str,
        max_date: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        ca_type_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        df = self.get_adjust_factor(
            symbol_list=symbol_list,
            start_date=start_date,
            ca_type_list=ca_type_list,
        )

        # pivot table
        df = df.pivot(index="effect_date", columns="symbol", values="adjust_factor")

        # reverse cumulate product adjust factor
        df = df.iloc[::-1].cumprod(skipna=True).iloc[::-1]

        # reindex trade date
        if not df.empty:
            max_date = max(max_date, utils.date_to_str(df.index.max()))
        df = df.reindex(
            index=pd.date_range(
                start=min_date,
                end=max_date,
                normalize=True,
                name="effect_date",
            ),  # type: ignore
            columns=symbol_list,  # type: ignore
        )

        # shift back 1 day
        df = df.shift(-1)

        # back fill and fill 1
        df = df.fillna(method="backfill").fillna(1)

        return df

    def _merge_adjust_factor(
        self,
        df: pd.DataFrame,
        is_multiply: bool = True,
        start_adjust_date: Optional[str] = None,
        adjusted_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Adjust dataframe by adjust_factor.

        Parameters
        ----------
        df : pd.DataFrame
            index must be trade_date and columns must be symbol
        is_multiply : bool, optional
            is multiply by adjust factor (adjust factor usually less than 1), by default True
        start_adjust_date : Optional[str], optional
            start of get adjust factor effect date, by default None
        adjusted_list : Optional[List[str]], optional
            n_ca_type list, by default None

        Returns
        -------
        pd.DataFrame
            index is trade_date and columns is symbol
        """
        if df.empty:
            return df

        if start_adjust_date == None:
            start_adjust_date = utils.date_to_str(df.index.min())

        symbol_list = df.columns.tolist()
        if len(symbol_list) > 100:
            symbol_list = None

        adjust_factor_df = self._get_pivot_adjust_factor_df(
            min_date=utils.date_to_str(df.index.min()),
            max_date=utils.date_to_str(df.index.max()),
            symbol_list=symbol_list,
            start_date=start_adjust_date,
            ca_type_list=adjusted_list,
        )

        # reindex adjust_factor_df to df
        adjust_factor_df = adjust_factor_df.reindex(df.index)  # type: ignore

        # multiply or divide
        if is_multiply:
            df = df * adjust_factor_df
        else:
            df = df / adjust_factor_df

        return df

    def _merge_adjust_factor_dividend(
        self,
        df: pd.DataFrame,
        start_adjust_date: Optional[str] = None,
        adjusted_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        if df.empty:
            return df

        if start_adjust_date == None:
            start_adjust_date = utils.date_to_str(df["ex_date"].min())

        symbol_list = df["symbol"].unique().tolist()
        if len(symbol_list) > 100:
            symbol_list = None

        adjust_factor_df = self._get_pivot_adjust_factor_df(
            min_date=utils.date_to_str(df["ex_date"].min()),
            max_date=utils.date_to_str(df["ex_date"].max()),
            symbol_list=symbol_list,
            start_date=start_adjust_date,
            ca_type_list=adjusted_list,
        )

        adjust_factor_df = (
            adjust_factor_df.stack().rename("adjust_factor").reset_index()  # type: ignore
        )

        df = df.merge(
            adjust_factor_df,
            how="left",
            left_on=["ex_date", "symbol"],
            right_on=["effect_date", "symbol"],
            validate="m:1",
        )
        df["adjust_factor"] = df["adjust_factor"].fillna(1)

        df["dps"] *= df["adjust_factor"]

        df = df.drop(columns=["effect_date", "adjust_factor"])

        return df

    def _get_fundamental_data(
        self,
        period: str,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fillna_value=None,
    ) -> pd.DataFrame:
        period = period.upper()
        field = field.lower()

        security_t = self._table("SECURITY")
        d_trade_subquery = self._d_trade_subquery()

        if field in fld.FINANCIAL_STAT_STD_MAP_COMPACT:
            stmt = self._get_financial_stat_std_stmt(field=field, period=period)
        elif field in fld.FINANCIAL_SCREEN_MAP and period in ("Q", "Y", "YTD"):
            stmt = self._get_financial_screen_stmt(field=field, period=period)
        else:
            raise ValueError(
                f"{field} is not supported for {period}. More field in ezyquant.field"
            )

        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=d_trade_subquery.c.D_TRADE,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = pd.read_sql_query(
            stmt, self.__engine, parse_dates="trade_date", dtype={"value": np.float64}  # type: ignore
        )

        # duplicate key mostly I_ACCT_FORM 6,7
        df = df.drop_duplicates(subset=["trade_date", "symbol"], keep="last")

        if fillna_value != None:
            df = df.fillna(fillna_value)

        # pivot dataframe
        df = df.pivot(index="trade_date", columns="symbol", values="value")

        df.index.name = None
        df.columns.name = None

        return df

    def _get_financial_screen_stmt(self, period: str, field: str) -> Select:
        PERIOD_DICT = {
            "Q": ("Q1", "Q2", "Q3", "Q4"),
            "Y": ("YE",),
            "YTD": ("Q1", "6M", "9M", "YE"),
        }

        financial_screen_t = self._table("FINANCIAL_SCREEN")
        security_t = self._table("SECURITY")
        d_trade_subquery = self._d_trade_subquery()

        value_column = financial_screen_t.c[fld.FINANCIAL_SCREEN_MAP[field]]

        stmt = (
            select(
                [
                    d_trade_subquery.c.D_TRADE.label("trade_date"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    value_column.label("value"),
                ]
            )
            .select_from(self._join_security_and_d_trade_subquery(financial_screen_t))
            .where(func.trim(financial_screen_t.c.I_PERIOD_TYPE) == "QY")
            .where(func.trim(financial_screen_t.c.I_PERIOD).in_(PERIOD_DICT[period]))
        )

        return stmt

    def _get_financial_stat_std_stmt(self, period: str, field: str) -> Select:
        financial_stat_std_t = self._table("FINANCIAL_STAT_STD")
        security_t = self._table("SECURITY")
        d_trade_subquery = self._d_trade_subquery()

        if period == "Q":
            value_column = financial_stat_std_t.c["M_ACCOUNT"]
        elif period == "Y":
            if field in fld.FINANCIAL_STAT_STD_MAP["B"]:
                value_column = financial_stat_std_t.c["M_ACCOUNT"]
            else:
                value_column = financial_stat_std_t.c["M_ACC_ACCOUNT_12M"]
        elif period == "YTD":
            value_column = financial_stat_std_t.c["M_ACC_ACCOUNT"]
        elif period == "AVG":
            value_column = financial_stat_std_t.c["M_ACCOUNT_AVG"]
        elif period == "TTM":
            value_column = financial_stat_std_t.c["M_ACC_ACCOUNT_12M"]
        else:
            raise ValueError(f"{period} is not a valid period")

        stmt = (
            select(
                [
                    d_trade_subquery.c.D_TRADE.label("trade_date"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    value_column.label("value"),
                ]
            )
            .select_from(self._join_security_and_d_trade_subquery(financial_stat_std_t))
            .where(
                func.trim(financial_stat_std_t.c.N_ACCOUNT)
                == fld.FINANCIAL_STAT_STD_MAP_COMPACT[field]
            )
        )

        if period == "Y":
            stmt = stmt.where(financial_stat_std_t.c.I_QUARTER == 9)

        return stmt

    @lru_cache
    def _d_trade_subquery(self):
        daily_stock_stat_t = self._table("DAILY_STOCK_STAT")
        return (
            select(
                [
                    daily_stock_stat_t.c.I_SECURITY,
                    daily_stock_stat_t.c.D_AS_OF,
                    func.min(func.DATE(daily_stock_stat_t.c.D_TRADE)).label("D_TRADE"),
                ]
            )
            .group_by(
                daily_stock_stat_t.c.I_SECURITY, func.DATE(daily_stock_stat_t.c.D_AS_OF)
            )
            .subquery()
        )

    def _join_security_and_d_trade_subquery(self, table: Table):
        security_t = self._table("SECURITY")
        d_trade_subquery = self._d_trade_subquery()
        return table.join(
            security_t, table.c.I_SECURITY == security_t.c.I_SECURITY
        ).join(
            d_trade_subquery,
            and_(
                table.c.I_SECURITY == d_trade_subquery.c.I_SECURITY,
                func.DATE(table.c.D_AS_OF) == func.DATE(d_trade_subquery.c.D_AS_OF),
            ),
        )

    def _join_sector_table(self, table: Table, isouter: bool = False):
        sector_t = self._table("SECTOR")
        return table.join(
            sector_t,
            and_(
                table.c.I_MARKET == sector_t.c.I_MARKET,
                table.c.I_INDUSTRY == sector_t.c.I_INDUSTRY,
                table.c.I_SECTOR == sector_t.c.I_SECTOR,
                table.c.I_SUBSECTOR == sector_t.c.I_SUBSECTOR,
            ),
            isouter=isouter,
        )

    def _get_daily_sector_info(
        self,
        field: str,
        sector_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        market: str,
        f_data: str,
    ) -> pd.DataFrame:
        market = market.upper()

        sector_t = self._table("SECTOR")
        daily_sector_info_t = self._table("DAILY_SECTOR_INFO")

        field = field.lower()

        j = self._join_sector_table(daily_sector_info_t)

        # N_SECTOR is the industry name in F_DATA = 'I'
        stmt = (
            select(
                [
                    daily_sector_info_t.c.D_TRADE.label("trade_date"),
                    func.trim(sector_t.c.N_SECTOR).label("sector"),
                    daily_sector_info_t.c[fld.DAILY_SECTOR_INFO_MAP[field]].label(
                        field
                    ),
                ]
            )
            .select_from(j)
            .where(sector_t.c.F_DATA == f_data)
            .where(sector_t.c.I_MARKET == fld.MARKET_MAP_UPPER[market])
            .where(sector_t.c.D_CANCEL == None)
            .order_by(func.DATE(daily_sector_info_t.c.D_TRADE))
        )

        vld.check_start_end_date(
            start_date=start_date,
            end_date=end_date,
            last_update_date=self.last_table_update(daily_sector_info_t.name),
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=sector_t.c.N_SECTOR,
            date_column=daily_sector_info_t.c.D_TRADE,
            symbol_list=sector_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = pd.read_sql_query(
            stmt, self.__engine, index_col="trade_date", parse_dates="trade_date"
        )

        df = df.pivot(columns="sector", values=field)

        df.columns.name = None
        df.index.name = None

        return df
