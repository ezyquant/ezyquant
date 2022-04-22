from datetime import date
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import Column, MetaData, Table, and_, case, func, select
from sqlalchemy.sql import Select

from . import fields as fld


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
        calendar_t = self._table("CALENDAR")

        stmt = select([calendar_t.c.D_TRADE])
        if start_date is not None:
            stmt = stmt.where(func.DATE(calendar_t.c.D_TRADE) >= start_date)
        if end_date is not None:
            stmt = stmt.where(func.DATE(calendar_t.c.D_TRADE) <= end_date)

        stmt = stmt.order_by(calendar_t.c.D_TRADE)

        res = self.__engine.execute(stmt).all()

        return [i[0].date() for i in res]

    def is_trading_date(self, check_date: date) -> bool:
        """Data from table CALENDAR.

        Parameters
        ----------
        check_date : date
            D_TRADE

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
        >>> from ezyquant import fields as fld
        >>> from ezyquant.reader import SETDataReader
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

        j = security_t.join(
            sector_t,
            and_(
                security_t.c.I_MARKET == sector_t.c.I_MARKET,
                security_t.c.I_INDUSTRY == sector_t.c.I_INDUSTRY,
                security_t.c.I_SECTOR == sector_t.c.I_SECTOR,
                security_t.c.I_SUBSECTOR == sector_t.c.I_SUBSECTOR,
            ),
            isouter=True,
        )
        stmt = select(
            [
                security_t.c.I_SECURITY.label("symbol_id"),
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                security_t.c.I_MARKET.label("market"),
                func.trim(sector_t.c.N_INDUSTRY).label("industry"),
                func.trim(sector_t.c.N_SECTOR).label("sector"),
                security_t.c.I_SEC_TYPE.label("sec_type"),
                security_t.c.I_NATIVE.label("native"),
            ]
        ).select_from(j)

        if market != None:
            stmt = stmt.where(security_t.c.I_MARKET == fld.MARKET_MAP[market])
        if symbol_list != None:
            stmt = stmt.where(
                func.trim(security_t.c.N_SECURITY).in_([s.upper() for s in symbol_list])
            )
        if industry != None:
            stmt = stmt.where(func.trim(sector_t.c.N_INDUSTRY) == industry)
        if sector != None:
            stmt = stmt.where(func.trim(sector_t.c.N_SECTOR) == sector)

        res_df = pd.read_sql(stmt, self.__engine)

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
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_company_info(symbol_list=["BBL", "PTT"])
           company_id symbol               company_name_t  ...  establish                                       dvd_policy_t                                       dvd_policy_e
        0           1    BBL  ธนาคารกรุงเทพ จำกัด (มหาชน)  ...  1/12/1944  เมื่อผลประกอบการของธนาคารมีกำไร (โดยมีเงื่อนไข...  Pays when company has profit (with additional ...
        1         646    PTT    บริษัท ปตท. จำกัด (มหาชน)  ...  1/10/2001  ไม่ต่ำกว่าร้อยละ 25 ของกำไรสุทธิที่เหลือหลังหั...  Not less than 25% of net income after deductio...
        """
        company_t = self._table("COMPANY")
        security_t = self._table("SECURITY")

        j = security_t.join(company_t, company_t.c.I_COMPANY == security_t.c.I_COMPANY)
        stmt = select(
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
        ).select_from(j)

        if symbol_list != None:
            symbol_list = [s.upper() for s in symbol_list]
            stmt = stmt.where(func.trim(security_t.c.N_SECURITY).in_(symbol_list))

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
        >>> from datetime import date
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_change_name(["SMG"])
           symbol_id symbol effect_date symbol_old symbol_new
        0        220    SMG  2006-07-31        SMG      SCSMG
        1        220    SMG  2014-08-28      SCSMG        SMG
        >>> sdr.get_change_name(start_date=date(2014, 8, 28), end_date=date(2014, 8, 29))
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
        )
        stmt = self._filter_symbol_start_end(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=change_name_t.c.D_EFFECT,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        res_df = pd.read_sql(stmt, self.__engine)
        res_df = res_df.drop_duplicates(ignore_index=True)
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
        than 0 (Z_RIGHTS>0). ex_date and pay_date can be null.

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
        >>> sdr.get_dividend(["M"],start_date=datetime.date(2020, 7, 28),end_date=datetime.date(2022, 5, 11))
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
        )

        stmt = self._filter_symbol_start_end(
            stmt=stmt,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            symbol_column=security_t.c.N_SECURITY,
            date_column=rights_benefit_t.c.D_SIGN,
        )
        if ca_type_list != None:
            stmt = stmt.where(rights_benefit_t.c.N_CA_TYPE.in_(ca_type_list))
        res_df = pd.read_sql(
            stmt,
            self.__engine,
            # index_col="ex_date",
            # parse_dates=["ex_date", "pay_date"],
        )
        res_df_copy = res_df.copy()
        res_df.index = res_df.ex_date
        if symbol_list == None:
            res_df = self._merge_adjust_factor(
                df=res_df,
                multiply_columns=["dps"],
                divide_columns=set(),
                adjust_list=adjusted_list,
                is_all_symbol=True,
            )
        else:
            res_df = self._merge_adjust_factor(
                df=res_df,
                multiply_columns=["dps"],
                divide_columns=set(),
                adjust_list=adjusted_list,
                is_all_symbol=False,
            )
        res_df = res_df.reset_index(drop=True)
        return res_df

    def get_delisted(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_DETAIL. Filter delisted by D_DELISTED !=
        None.

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
        >>> from datetime import date
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_delisted(start_date=date(2020, 2, 20), end_date=date(2020, 2, 20))
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
        )
        stmt = self._filter_symbol_start_end(
            stmt=stmt,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            symbol_column=security_t.c.N_SECURITY,
            date_column=security_detail_t.c.D_DELISTED,
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
        >>> from datetime import date
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_sign_posting(symbol_list=["THAI"], start_date=date(2020, 11, 12), end_date=date(2021, 2, 25))
          symbol  hold_date sign
        0   THAI 2020-11-12   SP
        1   THAI 2021-02-25   SP
        """
        security_t = self._table("SECURITY")
        sign_posting_t = self._table("SIGN_POSTING")

        j = sign_posting_t.join(
            security_t, security_t.c.I_SECURITY == sign_posting_t.c.I_SECURITY
        )
        stmt = select(
            [
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                sign_posting_t.c.D_HOLD.label("hold_date"),
                func.trim(sign_posting_t.c.N_SIGN).label("sign"),
            ]
        ).select_from(j)
        stmt = self._filter_symbol_start_end(
            stmt=stmt,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            symbol_column=security_t.c.N_SECURITY,
            date_column=sign_posting_t.c.D_HOLD,
        )
        if sign_list != None:
            sign_list = [i.upper() for i in sign_list]
            stmt = stmt.where(func.trim(sign_posting_t.c.N_SIGN).in_(sign_list))

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
        >>> from datetime import date
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> sdr.get_symbols_by_index(index_list=["SET50"], start_date=date(2022, 1, 4), end_date=date(2022, 1, 4))
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

        j = security_index_t.join(
            sector_t, security_index_t.c.I_SECTOR == sector_t.c.I_SECTOR
        ).join(security_t, security_t.c.I_SECURITY == security_index_t.c.I_SECURITY)
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
        )
        stmt = self._filter_symbol_start_end(
            stmt=stmt,
            symbol_list=index_list,
            start_date=start_date,
            end_date=end_date,
            symbol_column=sector_t.c.N_SECTOR,
            date_column=security_index_t.c.D_AS_OF,
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
                - adjust_factor: float - R_ADJUST_FACTOR

        Examples
        --------
        >>> from ezyquant.reader import SETDataReader
        >>> sdr = SETDataReader("psims.db")
        >>> print(sdr.get_adjust_factor(symbol_list=["ASW", "DITTO"], ca_type_list=["SD"]))
          symbol effect_date ca_type  adjust_factor
        0    ASW  2021-08-25      SD         0.8889
        1  DITTO  2022-03-15      SD         0.8333
        """
        security_t = self._table("SECURITY")
        adjust_factor_t = self._table("ADJUST_FACTOR")

        j = adjust_factor_t.join(
            security_t, security_t.c.I_SECURITY == adjust_factor_t.c.I_SECURITY
        )
        stmt = select(
            [
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                adjust_factor_t.c.D_EFFECT.label("effect_date"),
                adjust_factor_t.c.N_CA_TYPE.label("ca_type"),
                adjust_factor_t.c.R_ADJUST_FACTOR.label("adjust_factor"),
            ]
        ).select_from(j)
        stmt = self._filter_symbol_start_end(
            stmt=stmt,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            symbol_column=security_t.c.N_SECURITY,
            date_column=adjust_factor_t.c.D_EFFECT,
        )
        if ca_type_list != None:
            ca_type_list = [i.upper() for i in ca_type_list]
            stmt = stmt.where(func.trim(adjust_factor_t.c.N_CA_TYPE).in_(ca_type_list))
        res_df = pd.read_sql(stmt, self.__engine)

        return res_df

    def get_data_symbol_daily(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
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

        security_t = self._table("SECURITY")
        selected_fields = list()
        field = field.lower()
        from_table = ""
        if field in fld.DAILY_STOCK_TRADE_FACTOR:
            daily_stock_t = self._table("DAILY_STOCK_TRADE")
            selected_fields.append(
                daily_stock_t.c[fld.DAILY_STOCK_TRADE_FACTOR[field]].label(
                    field.upper()
                )
            )
            from_table = "DAILY_STOCK_TRADE"
        elif field in fld.DAILY_STOCK_STAT_FACTOR:
            daily_stock_t = self._table("DAILY_STOCK_STAT")
            selected_fields.append(
                daily_stock_t.c[fld.DAILY_STOCK_STAT_FACTOR[field]].label(field.upper())
            )
            from_table = "DAILY_STOCK_STAT"
        else:
            raise ValueError(
                f"{field} not in Data 1D field. Please check fields for more details."
            )
        j = daily_stock_t.join(
            security_t, daily_stock_t.c.I_SECURITY == security_t.c.I_SECURITY
        )

        stmt = select(
            [
                daily_stock_t.c.D_TRADE.label("TRADING_DATETIME"),
                func.trim(security_t.c.N_SECURITY).label("SYMBOL"),
            ]
            + selected_fields
        ).select_from(j)
        if from_table == "DAILY_STOCK_TRADE":
            stmt = stmt.where(
                func.trim(daily_stock_t.c.I_TRADING_METHOD) == "A"
            )  # Auto Matching
        stmt = self._filter_symbol_start_end(
            stmt=stmt,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            symbol_column=security_t.c.N_SECURITY,
            date_column=daily_stock_t.c.D_TRADE,
        )

        df = pd.read_sql(
            stmt,
            self.__engine,
            index_col="TRADING_DATETIME",
            parse_dates="TRADING_DATETIME",
        )
        # return df
        # replace 0 with nan
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
        df = df.replace({i: 0 for i in NULL_IF_FIELD if i in df.columns}, np.nan)
        # return df
        df = self._merge_adjust_factor(df, adjust_list=adjusted_list)
        df.index.name = None
        return df

    def get_data_symbol_quarterly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Data from tables FINANCIAL_STAT_STD and FINANCIAL_SCREEN. If field
        is in both table, the data from FINANCIAL_STAT_STD will be used.
        FINANCIAL_STAT_STD using data from column M_ACCOUNT. FINANCIAL_SCREEN
        filter by I_PERIOD_TYPE='QY' and I_PERIOD in ('Q1','Q2','Q3','Q4').
        Index date is trade date (DAILY_STOCK_STAT.D_TRADE). Data is showing at
        first trade date which join on D_AS_OF. Null data in database will be
        filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

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
        """Data from table FINANCIAL_STAT_STD and FINANCIAL_SCREEN. If field is
        in both table, the data from FINANCIAL_STAT_STD will be used.
        FINANCIAL_STAT_STD filter by "I_QUARTER"='9' and using data from column
        M_ACCOUNT. FINANCIAL_SCREEN filter by I_PERIOD_TYPE='QY' and
        I_PERIOD='YE'. Index date is trade date (DAILY_STOCK_STAT.D_TRADE).
        Data is showing at first trade date which join on D_AS_OF. Null data in
        database will be filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

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
        """Trailing 12 months (TTM) is a term used to describe the past 12
        consecutive months of a company's performance data. TTM can be
        calculate only Income Statement and Cashflow, but not Financial Ratio
        and Balance Sheet. Data from table FINANCIAL_STAT_STD,
        FINANCIAL_SCREEN. If field is in both table, the data from
        FINANCIAL_SCREEN will be used. FINANCIAL_STAT_STD filter by using data
        from column M_ACC_ACCOUNT_12M. FINANCIAL_SCREEN don't have TTM data.
        Index date is trade date (DAILY_STOCK_STAT.D_TRADE). Data is showing at
        first trade date which join on D_AS_OF. Null data in database will be
        filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

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
        """Year to date (YTD) refers to the period of time beginning the first
        day of the current calendar year or fiscal year up to the current date.
        YTD can be calculate only Income Statement and Cashflow, but not
        Financial Ratio and Balance Sheet. Data from table FINANCIAL_STAT_STD
        and FINANCIAL_SCREEN. If field is in both table, the data from
        FINANCIAL_STAT_STD will be used. FINANCIAL_STAT_STD using data from
        column M_ACC_ACCOUNT. FINANCIAL_SCREEN filter by I_PERIOD_TYPE='QY' and
        I_PERIOD in ('Q1','6M','9M','YE'). Index date is trade date
        (DAILY_STOCK_STAT.D_TRADE). Data is showing at first
        DAILY_STOCK_STAT.D_TRADE which join on D_AS_OF. Null data in database
        will be filled with -inf.

        Parameters
        ----------
        field : str
            Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, case insensitive, must be unique, by default None
        start_date : Optional[date]
            start of trade date (DAILY_STOCK_STAT.D_TRADE), by default None
        end_date : Optional[date]
            end of trade date (DAILY_STOCK_STAT.D_TRADE), by default None

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

    """
    Protected methods
    """

    def _table(self, name: str) -> Table:
        return Table(name, self.__metadata, autoload=True)

    def _filter_symbol_start_end(
        self,
        stmt: Select,
        symbol_column: Column,
        date_column: Column,
        symbol_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
    ):
        if symbol_list != None:
            symbol_list = [i.upper() for i in symbol_list]
            stmt = stmt.where(func.upper(func.trim(symbol_column)).in_(symbol_list))
        if start_date != None:
            stmt = stmt.where(func.DATE(date_column) >= start_date)
        if end_date != None:
            stmt = stmt.where(func.DATE(date_column) <= end_date)
        return stmt

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
        adjust_list: Optional[List[str]] = None,
        is_all_symbol: Optional[bool] = False,
    ) -> pd.DataFrame:
        """df index is trading_datetime and columns contain symbol."""
        if df.empty or (
            not set(df.columns) & (set(multiply_columns) | set(divide_columns))
        ):
            return df

        if pd.isnull(start_date):
            start_date = df.index.min().date()

        if is_all_symbol:
            adj_factor = self.get_adjust_factor(
                start_date=start_date,
                ca_type_list=adjust_list,
            )
        else:
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
        if field in fld.FINANCIAL_SCREEN_FACTOR:
            df = self._get_financial_screen(
                symbol_list=symbol_list,
                field=field,
                start_date=start_date,
                end_date=end_date,
                period=period,
            )
        elif field in fld.FINANCIAL_STAT_STD_FACTOR:
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

        financial_screen_t = self._table("FINANCIAL_SCREEN")
        security_t = self._table("SECURITY")

        j = financial_screen_t.join(
            security_t, financial_screen_t.c.I_SECURITY == security_t.c.I_SECURITY
        )

        sql = (
            select(
                [
                    financial_screen_t.c.D_AS_OF.label("trading_datetime"),
                    func.trim(security_t.c.N_SECURITY).label("symbol"),
                    financial_screen_t.c[
                        fld.FINANCIAL_SCREEN_FACTOR[field.lower()]
                    ].label(field.lower()),
                ]
            )
            .where(
                financial_screen_t.c.I_PERIOD.in_(
                    PERIOD_DICT.get(period.upper(), tuple())
                )
            )
            .select_from(j)
            .order_by(financial_screen_t.c.D_AS_OF)
            .order_by(financial_screen_t.c.I_YEAR.asc())
            .order_by(financial_screen_t.c.I_QUARTER.asc())
        )

        if symbol_list != None:
            sql = sql.where(
                security_t.c.N_SECURITY.in_(
                    ["{:<20}".format(s.upper()) for s in symbol_list]
                )
            )

        if not pd.isnull(start_date):
            sql = sql.where(financial_screen_t.c.D_AS_OF >= start_date)
        if not pd.isnull(end_date):
            sql = sql.where(financial_screen_t.c.D_AS_OF <= end_date)

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

        financial_stat_std_t = self._table("FINANCIAL_STAT_STD")
        daily_stock_stat_t = self._table("DAILY_STOCK_STAT")
        security_t = self._table("SECURITY")

        daily_stock_stat_subquery = (
            select(
                [
                    daily_stock_stat_t.c.I_SECURITY,
                    daily_stock_stat_t.c.D_AS_OF,
                    func.min(daily_stock_stat_t.c.D_TRADE).label("D_TRADE"),
                ]
            )
            .group_by(daily_stock_stat_t.c.I_SECURITY, daily_stock_stat_t.c.D_AS_OF)
            .subquery()  # type: ignore
        )

        selected_fields = [
            daily_stock_stat_subquery.c.D_TRADE.label("trading_datetime"),
            func.trim(security_t.c.N_SECURITY).label("symbol"),
            financial_stat_std_t.c.N_ACCOUNT.label("field"),
            financial_stat_std_t.c[PERIOD_DICT[period]].label("value"),
        ]

        if period == "Y":
            selected_fields.append(financial_stat_std_t.c.M_ACCOUNT)

        sql = (
            select(selected_fields)
            .select_from(financial_stat_std_t)
            .order_by(daily_stock_stat_subquery.c.D_TRADE.asc())
            .order_by(financial_stat_std_t.c.I_ACCT_FORM.asc())
        )

        if period == "Y":
            sql = sql.where(financial_stat_std_t.c.I_QUARTER == 9)

        sql = sql.where(
            financial_stat_std_t.c.N_ACCOUNT.in_(
                fld.FINANCIAL_STAT_STD_FACTOR[field.lower()]
            )
        )

        if symbol_list is not None:
            sql = sql.where(
                security_t.c.N_SECURITY.in_(
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
                financial_stat_std_t.c.D_AS_OF == daily_stock_stat_subquery.c.D_AS_OF,
                financial_stat_std_t.c.I_SECURITY
                == daily_stock_stat_subquery.c.I_SECURITY,
            ),
        ).join(security_t, financial_stat_std_t.c.I_SECURITY == security_t.c.I_SECURITY)

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
        df = df.rename(columns={v: k for k, v in fld.FINANCIAL_STAT_STD_FACTOR.items()})

        return df
