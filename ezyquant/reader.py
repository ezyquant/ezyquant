from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, and_, func, select

from . import fields as fc


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

        self.__engine = sa.create_engine(f"sqlite:///{self.__sqlite_path}")
        self.__metadata = MetaData(self.__engine)

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
        t = Table("CALENDAR", self.__metadata, autoload=True)

        stmt = select([t.c.D_TRADE])
        if start_date is not None:
            stmt = stmt.where(func.DATE(t.c.D_TRADE) >= start_date)
        if end_date is not None:
            stmt = stmt.where(func.DATE(t.c.D_TRADE) <= end_date)

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
            isouter=True
            # left outerjoin
        )
        stmt = select(
            [
                security.c.I_SECURITY.label("symbol_id"),
                func.trim(security.c.N_SECURITY).label("symbol"),
                security.c.I_MARKET.label("market"),
                func.trim(sect.c.N_INDUSTRY).label("industry"),
                func.trim(sect.c.N_SECTOR).label("sector"),
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

        map_market = {v: k for k, v in fc.MARKET_MAP.items()}
        res_df["market"] = res_df["market"].map(map_market)
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
                company.c.A_COMPANY_T.label("address_t"),
                company.c.A_COMPANY_E.label("address_e"),
                company.c.I_ZIP.label("zip"),
                company.c.E_TEL.label("tel"),
                company.c.E_FAX.label("fax"),
                company.c.E_EMAIL.label("email"),
                company.c.E_URL.label("url"),
                func.trim(company.c.D_ESTABLISH).label("establish"),
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
        >>> import datetime
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
        res_df = res_df.dropna()
        res_df = res_df[res_df["symbol_old"] != res_df["symbol_new"]]
        res_df = res_df.reset_index(drop=True)
        return res_df

    def get_dividend(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type_list: Optional[List[str]] = None,
        adjusted_list: List[str] = ["  ", "CR", "PC", "RC", "SD", "XR"],
    ) -> pd.DataFrame:
        """Data from table RIGHTS_BENEFIT. Include only Cash Dividend (CA) and
        Stock Dividend (SD). Not include Cancelled (F_CANCEL!='C') and dps more
        than 0 (Z_RIGHTS>0).

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
        >>> from ezyquant.reader import SETDataReader
        >>> import datetime
        >>> sdr = SETDataReader("ssetdi_db.db")
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
        >>> sdr.get_dividend(["M"],start_date=datetime.date(2020, 7, 28),end_date=datetime.date(2022, 5, 11))
            symbol     ex_date    pay_date ca_type  dps
        0        M  2020-08-24  2020-09-10      CD  0.5
        1        M  2021-05-10  2021-05-25      CD  0.5
        2        M  2022-05-10  2022-05-25      CD  0.8
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
            .where(func.trim(right.c.N_CA_TYPE).in_(["CD", "SD"]))
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
            stmt = stmt.where(right.c.N_CA_TYPE.in_(ca_type_list))
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
        >>> from ezyquant.reader import SETDataReader
        >>> import datetime
        >>> sdr = SETDataReader("ssetdi_db.db")
        >>> sdr.get_delisted(start_date=datstart, end_date=datend)
             symbol delisted_date
        0  CB14828A    2014-08-28
        1  CB14828B    2014-08-28
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
        >>> from ezyquant.reader import SETDataReader
        >>> import datetime
        >>> sdr = SETDataReader("ssetdi_db.db")
        >>> sdr.get_delisted(start_date=datetime.date(2014, 8, 27), end_date=datetime.date(2014, 8, 28))
             symbol delisted_date
        0  EGAT148B    2014-08-27
        1  DTAC148A    2014-08-27
        2    AA148A    2014-08-27
        3  TB14827A    2014-08-27
        """
        security = Table("SECURITY", self.__metadata, autoload=True)
        sign_post = Table("SIGN_POSTING", self.__metadata, autoload=True)
        j = sign_post.join(security, security.c.I_SECURITY == sign_post.c.I_SECURITY)
        stmt = select(
            [
                func.trim(security.c.N_SECURITY).label("symbol"),
                sign_post.c.D_HOLD.label("hold_date"),
                sign_post.c.N_SIGN.label("sign"),
            ]
        ).select_from(j)
        stmt = self._list_start_end_condition(
            query_object=stmt,
            list_condition=symbol_list,
            start_date=start_date,
            end_date=end_date,
            col_list=security.c.N_SECURITY,
            col_date=sign_post.c.D_HOLD,
        )
        if sign_list != None:
            stmt = stmt.where(func.trim(sign_post.c.N_SIGN).in_(sign_list))
        print(stmt)
        res_df = pd.read_sql(stmt, self.__engine)
        return res_df

    def get_symbols_by_index(
        self,
        index_list: Optional[List[str]] = None,
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
        >>> from ezyquant.reader import SETDataReader
        >>> import datetime
        >>> sdr = SETDataReader("ssetdi_db.db")
        >>> sdr.get_symbols_by_index(["COMM"],start_date=datetime.date(2022, 1, 1),end_date=datetime.date(2022, 4, 1))
           as_of_date  symbol index
        0  2022-01-04     BJC  COMM
        1  2022-01-04   HMPRO  COMM
        2  2022-01-04   CPALL  COMM
        3  2022-01-04  GLOBAL  COMM
        4  2022-01-04    MEGA  COMM
        """
        security = Table("SECURITY", self.__metadata, autoload=True)
        sector = Table("SECTOR", self.__metadata, autoload=True)
        security_index = Table("SECURITY_INDEX", self.__metadata, autoload=True)
        j = security_index.join(
            sector,
            and_(
                security.c.I_MARKET == sector.c.I_MARKET,
                security.c.I_INDUSTRY == sector.c.I_INDUSTRY,
                security.c.I_SECTOR == sector.c.I_SECTOR,
            ),
        ).join(
            security,
            security.c.I_SECURITY == security_index.c.I_SECURITY,
        )
        stmt = select(
            [
                security_index.c.D_AS_OF.label("as_of_date"),
                func.trim(security.c.N_SECURITY).label("symbol"),
                func.trim(sector.c.N_SECTOR).label("index"),
            ]
        ).select_from(j)

        stmt = self._list_start_end_condition(
            query_object=stmt,
            list_condition=index_list,
            start_date=start_date,
            end_date=end_date,
            col_list=sector.c.N_SECTOR,
            col_date=security_index.c.D_AS_OF,
        )

        res_df = pd.read_sql(stmt, self.__engine)
        return res_df

    def get_adjust_factor(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ca_type_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Data from table ADJUST_FACTOR. Filter only Auto Matching
        (I_TRADING_METHOD='A').

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
                - adjust_factor: float - R_ADJUST_FACTOR

        Examples
        --------
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("ssetdi_db.db")
        >>> print(sdr.get_adjust_factor(symbol_list=["ASW", "DITTO"], ca_type_list=["SD"]))
          symbol effect_date ca_type  adjust_factor
        0    ASW  2021-08-25      SD         0.8889
        1  DITTO  2022-03-15      SD         0.8333
        """
        security = Table("SECURITY", self.__metadata, autoload=True)
        adj_fac = Table("ADJUST_FACTOR", self.__metadata, autoload=True)
        j = adj_fac.join(security, security.c.I_SECURITY == adj_fac.c.I_SECURITY)
        stmt = select(
            [
                func.trim(security.c.N_SECURITY).label("symbol"),
                adj_fac.c.D_EFFECT.label("effect_date"),
                adj_fac.c.N_CA_TYPE.label("ca_type"),
                adj_fac.c.R_ADJUST_FACTOR.label("adjust_factor"),
            ]
        ).select_from(j)
        stmt = self._list_start_end_condition(
            query_object=stmt,
            list_condition=symbol_list,
            start_date=start_date,
            end_date=end_date,
            col_list=security.c.N_SECURITY,
            col_date=adj_fac.c.D_EFFECT,
        )
        if ca_type_list != None:
            stmt = stmt.where(func.trim(adj_fac.c.N_CA_TYPE).in_(ca_type_list))
        res_df = pd.read_sql(stmt, self.__engine)
        return res_df

    def _get_fundamental_data(
        self,
        period: str,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_to_dict: bool = True,
    ) -> pd.DataFrame:
        """fill nan with -np.inf if is_to_dict.

        period: str
            'Q' for Quarter, 'Y' for Quarter, 'YTD', 'TTM', 'AVG'
        """
        # split field_list for 2 tables
        screen_field_list = list()
        stat_field_list = list()
        df = pd.DataFrame
        field = field.lower()
        if field in fc.FINANCIAL_SCREEN_FACTOR:
            df = self._get_financial_screen(
                symbol_list=symbol_list,
                field=field,
                start_date=start_date,
                end_date=end_date,
                period=period,
            )
        elif field in fc.FINANCIAL_STAT_STD_FACTOR:
            df = self._get_financial_stat_std(
                symbol_list=symbol_list,
                field=field,
                start_date=start_date,
                end_date=end_date,
                period=period,
            )
        else:
            raise ValueError(
                f"{field} not in Data {period} field. Please check psims factor for more details."
            )
        return df

    def _get_financial_screen(
        self,
        period: str,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        period: str
            'Q' for Quarter, 'Y' for Year, 'YTD' for Year to date
        period_type: str
            'QY', 'QOQ', 'YOY'
        """
        PERIOD_DICT = {
            "Q": ("Q1", "Q2", "Q3", "Q4"),
            "Y": ("YE",),
            "YTD": ("Q1", "6M", "9M", "YE"),
        }

        financial_screen = Table("FINANCIAL_SCREEN", self.__metadata, autoload=True)
        security = Table("SECURITY", self.__metadata, autoload=True)

        j = financial_screen.join(
            security, financial_screen.c.I_SECURITY == security.c.I_SECURITY
        )

        sql = (
            select(
                [
                    financial_screen.c.D_AS_OF.label("trading_datetime"),
                    func.trim(security.c.N_SECURITY).label("symbol"),
                    financial_screen.c[fc.FINANCIAL_SCREEN_FACTOR[field.lower()]].label(
                        field.lower()
                    ),
                ]
            )
            .where(
                financial_screen.c.I_PERIOD.in_(
                    PERIOD_DICT.get(period.upper(), tuple())
                )
            )
            .select_from(j)
            .order_by(financial_screen.c.D_AS_OF)
            .order_by(financial_screen.c.I_YEAR.asc())
            .order_by(financial_screen.c.I_QUARTER.asc())
        )

        if symbol_list != None:
            sql = sql.where(
                security.c.N_SECURITY.in_(
                    ["{:<20}".format(s.upper()) for s in symbol_list]
                )
            )

        if not pd.isnull(start_date):
            sql = sql.where(financial_screen.c.D_AS_OF >= start_date)
        if not pd.isnull(end_date):
            sql = sql.where(financial_screen.c.D_AS_OF <= end_date)

        df = pd.read_sql(sql, self.__engine, parse_dates="trading_datetime")
        return df

    def _get_financial_stat_std(
        self,
        period: str,
        field: str,
        symbol_list: Optional[Iterable[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        period: str
            'Q' for Quarter, 'Y' for Year
        """
        PERIOD_DICT = {
            "Q": "M_ACCOUNT",
            "Y": "M_ACC_ACCOUNT_12M",
            "YTD": "M_ACC_ACCOUNT",
            "AVG": "M_ACCOUNT_AVG",
            "TTM": "M_ACC_ACCOUNT_12M",
        }

        period = period.upper()

        financial_stat_std = Table("FINANCIAL_STAT_STD", self.__metadata, autoload=True)
        daily_stock_stat = Table("DAILY_STOCK_STAT", self.__metadata, autoload=True)
        security = Table("SECURITY", self.__metadata, autoload=True)

        daily_stock_stat_subquery = (
            select(
                [
                    daily_stock_stat.c.I_SECURITY,
                    daily_stock_stat.c.D_AS_OF,
                    func.min(daily_stock_stat.c.D_TRADE).label("D_TRADE"),
                ]
            )
            .group_by(daily_stock_stat.c.I_SECURITY, daily_stock_stat.c.D_AS_OF)
            .subquery()  # type: ignore
        )

        selected_fields = [
            daily_stock_stat_subquery.c.D_TRADE.label("trading_datetime"),
            func.trim(security.c.N_SECURITY).label("symbol"),
            financial_stat_std.c.N_ACCOUNT.label("field"),
            financial_stat_std.c[PERIOD_DICT[period]].label("value"),
        ]

        if period == "Y":
            selected_fields.append(financial_stat_std.c.M_ACCOUNT)

        sql = (
            select(selected_fields)
            .select_from(financial_stat_std)
            .order_by(daily_stock_stat_subquery.c.D_TRADE.asc())
            .order_by(financial_stat_std.c.I_ACCT_FORM.asc())
        )

        if period == "Y":
            sql = sql.where(financial_stat_std.c.I_QUARTER == 9)

        if field_list is not None:
            field_list = [fc.FINANCIAL_STAT_STD_FACTOR[i.lower()] for i in field_list]
            sql = sql.where(financial_stat_std.c.N_ACCOUNT.in_(field_list))

        if symbol_list is not None:
            sql = sql.where(
                security.c.N_SECURITY.in_(
                    ["{:<20}".format(s.upper()) for s in symbol_list]
                )
            )

        if not pd.isnull(start_date):
            sql = sql.where(daily_stock_stat_subquery.c.D_TRADE >= start_date)
        if not pd.isnull(end_date):
            sql = sql.where(daily_stock_stat_subquery.c.D_TRADE <= end_date)

        sql = sql.join(
            daily_stock_stat_subquery,
            and_(
                financial_stat_std.c.D_AS_OF == daily_stock_stat_subquery.c.D_AS_OF,
                financial_stat_std.c.I_SECURITY
                == daily_stock_stat_subquery.c.I_SECURITY,
            ),
        ).join(security, financial_stat_std.c.I_SECURITY == security.c.I_SECURITY)

        # sql = self._compile_sql(sql)
        df = pd.read_sql(sql, self.__engine, parse_dates="trading_datetime")

        # duplicate key mostly I_ACCT_FORM 6,7
        df = df.drop_duplicates(
            subset=["trading_datetime", "symbol", "field"], keep="last"
        )
        df = df.set_index("trading_datetime")

        if period == "Y":
            """For Yearly fundamental "I_ACCT_TYPE".

            - B use "M_ACCOUNT"
            - I use "M_ACC_ACCOUNT_12M"
            - C use "M_ACC_ACCOUNT_12M"
            """
            df = df.fillna({"value": df["M_ACCOUNT"]}).drop(columns="M_ACCOUNT")

        # pivot dataframe
        df = df.reset_index()
        df = df.pivot(
            index=["trading_datetime", "symbol"], columns="field", values="value"
        )
        df = df.reset_index("symbol")

        # rename columns
        df = df.rename(columns={v: k for k, v in fc.FINANCIAL_STAT_STD_FACTOR.items()})

        return df

    def _merge_adjust_factor(
        self,
        df: pd.DataFrame,
        multiply_columns: Iterable[str] = {
            "open",
            "close",
            "low",
            "high",
            "average",
            "eps",
            "dps",
        },
        divide_columns: Iterable[str] = {"volume"},
        start_date: Optional[date] = None,
        adjust_list: List[str] = None,
    ) -> pd.DataFrame:
        """df index is trading_datetime and columns contain symbol."""
        if df.empty or (
            not set(df.columns) & (set(multiply_columns) | set(divide_columns))
        ):
            return df

        if pd.isnull(start_date):
            start_date = df.index.min().date()

        adj_factor = self.get_adjust_factor(
            symbol_list=df["symbol"].unique().tolist(),
            start_date=start_date,
            ca_type_list=adjust_list,
        )

        adj_factor.index = adj_factor.effect_date

        # print(adj_factor)
        end_adj = adj_factor.effect_date.max()

        if adj_factor.empty:
            return df

        # pivot table
        adj_factor = adj_factor.pivot(columns="symbol", values="adjust_factor")
        # print(adj_factor)
        # cumulate product of adjust factor
        adj_factor = adj_factor.iloc[::-1].cumprod().iloc[::-1]  # type: ignore
        # print(adj_factor)
        # reindex and shift back 1 day
        adj_factor = adj_factor.reindex(
            pd.date_range(
                start=df.index.min(),
                end=max(df.index.max(), end_adj),
                normalize=True,
            ),
        )
        # print(adj_factor)
        adj_factor = adj_factor.shift(-1)

        # back fill and fill 1
        adj_factor = adj_factor.fillna(method="backfill").fillna(1)
        # stack to series
        adj_factor = adj_factor.stack("symbol")

        # merge adjust factor to dataframe
        df = df.set_index("symbol", append=True)
        df["adj_factor"] = adj_factor
        df = df.fillna({"adj_factor": 1})
        df = df.reset_index("symbol")
        # print(df)
        mul_cols = [i for i in multiply_columns if i in df.columns]
        div_cols = [i for i in divide_columns if i in df.columns]

        for field in mul_cols:
            df[field] *= df["adj_factor"]
        for field in div_cols:
            df[field] /= df["adj_factor"]

        df = df.drop(columns=["adj_factor"]).dropna(
            subset=mul_cols + div_cols, how="all"
        )  # dropna from outer merge
        return df

    def get_data_symbol_daily(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjusted_list: List[str] = ["  ", "CR", "PC", "RC", "SD", "XR"],
    ) -> pd.DataFrame:
        """Data from table DAILY_STOCK_TRADE, DAILY_STOCK_STAT. Replace 0 with
        NaN in following field e.g. prior, open, high, low, close, average,
        last_bid, last_offer.

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
                - symbol(N_SECURITY): str as column
                - trade_date(D_TRADE): date as index

        Examples
        --------
        TODO: examples
        """
        adjusted_list = list(adjusted_list)  # copy to avoid modify original list
        daily_stock_trade = Table("DAILY_STOCK_TRADE", self.__metadata, autoload=True)
        daily_stock_stat = Table("DAILY_STOCK_STAT", self.__metadata, autoload=True)
        security = Table("SECURITY", self.__metadata, autoload=True)

        NULL_IF_FIELD = {
            "prior",
            "open",
            "high",
            "low",
            "close",
            "average",
            "last_bid",
            "last_offer",
        }

        selected_fields = list()

        if field is not None:
            # for i in field:   field have only 1
            field = field.lower()

            if field in fc.DAILY_STOCK_TRADE_FACTOR:
                selected_fields.append(
                    daily_stock_trade.c[fc.DAILY_STOCK_TRADE_FACTOR[field]].label(field)
                )
            elif field in fc.DAILY_STOCK_STAT_FACTOR:
                selected_fields.append(
                    daily_stock_stat.c[fc.DAILY_STOCK_STAT_FACTOR[field]].label(field)
                )
            else:
                raise ValueError(
                    f"{field} not in Data 1D field. Please check fields for more details."
                )
        else:
            selected_fields += [
                daily_stock_trade.c[v].label(k)
                for k, v in fc.DAILY_STOCK_TRADE_FACTOR.items()
            ]
            selected_fields += [
                daily_stock_stat.c[v].label(k)
                for k, v in fc.DAILY_STOCK_STAT_FACTOR.items()
            ]

        sql = (
            select(
                [
                    daily_stock_trade.c.D_TRADE.label("trading_datetime"),
                    func.trim(security.c.N_SECURITY).label("symbol"),
                ]
                + selected_fields
            )
            .select_from(daily_stock_trade)
            .where(daily_stock_trade.c.I_TRADING_METHOD == "A")  # Auto Matching
            .order_by(daily_stock_trade.c.D_TRADE.asc())
        )

        sql = self._list_start_end_condition(
            query_object=sql,
            list_condition=symbol_list,
            start_date=start_date,
            end_date=end_date,
            col_list=security.c.N_SECURITY,
            col_date=daily_stock_trade.c.D_TRADE,
        )

        sql = sql.join(
            security, daily_stock_trade.c.I_SECURITY == security.c.I_SECURITY
        ).join(
            daily_stock_stat,
            and_(
                daily_stock_trade.c.I_SECURITY == daily_stock_stat.c.I_SECURITY,
                daily_stock_trade.c.D_TRADE == daily_stock_stat.c.D_TRADE,
            ),
            isouter=True,
        )

        # sql = self._compile_sql(sql)
        df = pd.read_sql(
            sql,
            self.__engine,
            index_col="trading_datetime",
            parse_dates="trading_datetime",
        )
        # line 1430
        # adjust price
        # if is_adjusted:
        #    df = self._merge_adjust_factor(df)

        # replace 0 with nan
        df = df.replace({i: 0 for i in NULL_IF_FIELD if i in df.columns}, np.nan)
        self._merge_adjust_factor(df, adjust_list=adjusted_list)
        return df

    def get_data_symbol_quarterly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD. If field is
        duplicate in FINANCIAL_SCREEN and FINANCIAL_STAT_STD, the data from
        FINANCIAL_SCREEN will be used. Index date is trade
        date(DAILY_STOCK_STAT.D_TRADE). Data is showing at first
        DAILY_STOCK_STAT.D_TRADE which join on D_AS_OF. Null data in database
        will be filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date(DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date(DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        TODO: examples
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
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_SCREEN, FINANCIAL_STAT_STD. If field is
        duplicate in FINANCIAL_SCREEN and FINANCIAL_STAT_STD, the data from
        FINANCIAL_SCREEN will be used. Index date is trade
        date(DAILY_STOCK_STAT.D_TRADE). Data is showing at first
        DAILY_STOCK_STAT.D_TRADE which join on D_AS_OF. Null data in database
        will be filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date(DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date(DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

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
        FINANCIAL_SCREEN will be used. Index date is trade
        date(DAILY_STOCK_STAT.D_TRADE). Data is showing at first
        DAILY_STOCK_STAT.D_TRADE which join on D_AS_OF. Null data in database
        will be filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date(DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date(DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

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
        FINANCIAL_SCREEN will be used. Index date is trade
        date(DAILY_STOCK_STAT.D_TRADE). Data is showing at first
        DAILY_STOCK_STAT.D_TRADE which join on D_AS_OF. Null data in database
        will be filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date(DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date(DAILY_STOCK_STAT.D_TRADE), by default None

        Returns
        -------
        pd.DataFrame
            dataframe contain:
                - symbol(N_SECURITY): str as column
                - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

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
        list_condition,
        col_list,
        start_date,
        end_date,
        col_date,
    ):
        """helper function for make query.

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
            query_object = query_object.where(func.DATE(col_date) >= start_date)
        if end_date != None:
            query_object = query_object.where(func.DATE(col_date) <= end_date)
        return query_object
