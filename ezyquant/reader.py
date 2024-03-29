import warnings
from datetime import date
from functools import lru_cache
from typing import Dict, List, Optional

import pandas as pd
from pandas.errors import PerformanceWarning
from pandas.tseries.offsets import CustomBusinessDay
from sqlalchemy import (
    ColumnElement,
    MetaData,
    Subquery,
    Table,
    and_,
    case,
    exists,
    func,
    or_,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import aliased
from sqlalchemy.sql import FromClause, Join, Select

from ezyquant import fields as fld
from ezyquant import utils
from ezyquant import validators as vld
from ezyquant.errors import InputError

warnings.filterwarnings(
    "ignore",
    message="Non-vectorized DateOffset being applied to Series or DatetimeIndex.",
    category=PerformanceWarning,
)

TRADE_DATE = "trade_date"
NAME = "name"
VALUE = "value"

set50_number = 50
set100_number = 100
sethd_number = 30

sqlite_max_variable_number = 100

fourth_quarter_number = 9

TIMEFRAME_MAP = {
    fld.TIMEFRAME_QUARTERLY: ("Q1", "Q2", "Q3", "Q4"),
    fld.TIMEFRAME_YEARLY: ("YE",),
}


class SETDataReader:
    _engine: Optional[Engine] = None

    def __init__(self):
        """SETDataReader read PSIMS data."""
        if self._engine is None:
            msg = "You need to connect sqlite using ezyquant.connect_sqlite."
            raise InputError(msg)

        self._metadata = MetaData()

        # ping database
        try:
            self._table("SECURITY")
        except DatabaseError as e:
            raise InputError(e) from e

    # TODO: Clear cache
    @lru_cache
    def last_table_update(self, table_name: str) -> str:
        """Last D_TRADE in table.

        Parameters
        ----------
        table_name: str
            name of table:

            - DAILY_STOCK_TRADE
            - DAILY_STOCK_STAT
            - DAILY_SECTOR_INFO

            or any table that have D_TRADE column.

        Returns
        -------
        str
            string with format YYYY-MM-DD.
        """
        t = self._table(table_name)
        stmt = select(func.max(t.c.D_TRADE).label(TRADE_DATE))
        df = self._read_sql_query(stmt)
        res = df[TRADE_DATE].dt.strftime("%Y-%m-%d").iloc[0]
        return res

    def last_update(self) -> str:
        """Last database update, checking from last D_TRADE in the following
        tables:

        - DAILY_STOCK_TRADE
        - DAILY_STOCK_STAT
        - DAILY_SECTOR_INFO

        Returns
        -------
        str
            string with format YYYY-MM-DD.
        """
        d1 = self.last_table_update("DAILY_STOCK_TRADE")
        d2 = self.last_table_update("DAILY_STOCK_STAT")
        d3 = self.last_table_update("DAILY_SECTOR_INFO")
        if d1 != d2 or d1 != d3:
            warnings.warn(
                "Last update is not the same for all tables. "
                "Please check your database.",
                stacklevel=2,
            )
        return d1

    def get_trading_dates(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[str]:
        """Data from table CALENDAR.

        Parameters
        ----------
        start_date: Optional[str] = None
            start of D_TRADE.
        end_date: Optional[str] = None
            end of D_TRADE.

        Returns
        -------
        List[str]
            list of string with format YYYY-MM-DD.
        """
        calendar_t = self._table("CALENDAR")

        stmt = select(calendar_t.c.D_TRADE.label(TRADE_DATE)).order_by(
            calendar_t.c.D_TRADE
        )

        stmt = self._filter_stmt_by_date(
            stmt=stmt,
            column=calendar_t.c.D_TRADE,
            start_date=start_date,
            end_date=end_date,
        )

        df = self._read_sql_query(stmt)

        res = df[TRADE_DATE].dt.strftime("%Y-%m-%d").tolist()

        return res

    def is_trading_date(self, check_date: str) -> bool:
        """Data from table CALENDAR.

        Parameters
        ----------
        check_date: str
            string with format YYYY-MM-DD.

        Returns
        -------
        bool
            True if the trading date is exist.
        """
        calendar_t = self._table("CALENDAR")

        stmt = select(
            exists().where(self._func_date(calendar_t.c.D_TRADE) == check_date)
        )

        df = self._read_sql_query(stmt)

        res = bool(df.iloc[0, 0])

        return res

    def is_today_trading_date(self) -> bool:
        """Data from table CALENDAR.

        Returns
        -------
        bool
            True if today is the trading date.
        """
        return self.is_trading_date(utils.date_to_str(date.today()))

    def get_symbol_info(
        self,
        symbol_list: Optional[List[str]] = None,
        market: Optional[str] = None,
        industry: Optional[str] = None,
        sector: Optional[str] = None,
        sec_type: Optional[str] = None,
        native: Optional[str] = None,
        start_has_price_date: Optional[str] = None,
        end_has_price_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY. Symbol must exist in table DAILY_STOCK_TRADE.

        Parameters
        ----------
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        market: Optional[str] = None
            I_MARKET e.g. 'SET', 'mai'
        industry: Optional[str] = None
            SECTOR.N_SYMBOL_FEED
        sector: Optional[str] = None
            SECTOR.N_SYMBOL_FEED
        sec_type: Optional[str] = None
            Security type
                - S: Common
                - F: Common Foreign
                - P: Preferred
                - Q: Preferred Foreign
                - U: Unit Trusts
                - T: Unit Trusts Foreign
                - W: Warrant
                - X: Depository Receipts
                - Y: Depository Receipts Foreign
                - L: ETFs
                - O: Index Options
                - D: Debenture
                - C: Convertible Debenture
                - I: Index Warrant
                - V: Derivatives Warrant
                - R: Transferable Subscription Right
                - G: Government Bond
                - J: Convertible Preferred
        native: Optional[str] = None
            I_NATIVE
                - L: Local
                - F: Foreign
                - U: Thai Trust Fund
                - R: NVDR
        start_has_price_date: Optional[str] = None
            start of D_TRADE in DAILY_STOCK_TRADE.
        end_has_price_date: Optional[str] = None
            end of D_TRADE in DAILY_STOCK_TRADE.

        Returns
        -------
        pd.DataFrame
            symbol info dataframe contain columns:
                - symbol_id: int - I_SECURITY
                - symbol: str - N_SECURITY
                - market: str - I_MARKET
                - industry: str - SECTOR.N_SYMBOL_FEED
                - sector: str - SECTOR.N_SYMBOL_FEED
                - sec_type: str - I_SEC_TYPE
                - native: str - I_NATIVE

        Examples
        --------
        >>> from ezyquant import fields as fld
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader()
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
        daily_stock_t = self._table("DAILY_STOCK_TRADE")

        sector_industry_t = aliased(sector_t)
        sector_sector_t = aliased(sector_t)

        from_clause = self._join_sector_table(
            security_t,
            isouter=True,
            sector_t=sector_industry_t,
            is_join_sector=False,
        )
        from_clause = self._join_sector_table(
            from_clause,
            isouter=True,
            sector_t=sector_sector_t,
            is_join_sector=True,
        )
        stmt = (
            select(
                security_t.c.I_SECURITY.label("symbol_id"),
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                security_t.c.I_MARKET.label("market"),
                func.trim(sector_industry_t.c.N_SYMBOL_FEED).label("industry"),
                func.trim(sector_sector_t.c.N_SYMBOL_FEED).label("sector"),
                security_t.c.I_SEC_TYPE.label("sec_type"),
                security_t.c.I_NATIVE.label("native"),
            )
            .select_from(from_clause)
            .order_by(security_t.c.I_SECURITY)
        )

        stmt = self._filter_str_in_list(
            stmt=stmt, column=security_t.c.N_SECURITY, values=symbol_list
        )
        if market is not None:
            market = market.upper()
            stmt = stmt.where(security_t.c.I_MARKET == fld.MARKET_MAP_UPPER[market])
        if industry is not None:
            industry = industry.upper()
            stmt = stmt.where(
                func.upper(func.trim(sector_industry_t.c.N_SYMBOL_FEED)) == industry
            )
        if sector is not None:
            sector = sector.upper()
            stmt = stmt.where(
                func.upper(func.trim(sector_sector_t.c.N_SYMBOL_FEED)) == sector
            )
        if sec_type is not None:
            sec_type = sec_type.upper()
            stmt = stmt.where(security_t.c.I_SEC_TYPE == sec_type)
        if native is not None:
            native = native.upper()
            stmt = stmt.where(security_t.c.I_NATIVE == native)

        # No if because symbol must exist in DAILY_STOCK_TRADE
        subq = select(daily_stock_t.c.I_SECURITY).distinct()
        subq = self._filter_stmt_by_date(
            stmt=subq,
            column=daily_stock_t.c.D_TRADE,
            start_date=start_has_price_date,
            end_date=end_has_price_date,
        )
        stmt = stmt.where(security_t.c.I_SECURITY.in_(subq))

        df = self._read_sql_query(stmt)

        map_market = {v: k for k, v in fld.MARKET_MAP.items()}
        df["market"] = df["market"].replace(map_market)

        return df

    def get_company_info(self, symbol_list: Optional[List[str]] = None) -> pd.DataFrame:
        """Data from table COMPANY.

        Parameters
        ----------
        symbol_list: Optional[List[str]] = None
            SECURITY.N_SECURITY in symbol_list (must be unique).

        Returns
        -------
        pd.DataFrame
            company info dataframe contain columns:
                - company_id: int - I_COMPANY
                - symbol: str - SECURITY.N_SECURITY
                - company_name_t: str - N_COMPANY_T
                - company_name_e: str - N_COMPANY_E

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader()
        >>> sdr.get_company_info(symbol_list=["BBL", "PTT"])
           company_id symbol               company_name_t                       company_name_e
        0           1    BBL    ธนาคารกรุงเทพ จำกัด (มหาชน)  BANGKOK BANK PUBLIC COMPANY LIMITED
        1         646    PTT     บริษัท ปตท. จำกัด (มหาชน)           PTT PUBLIC COMPANY LIMITED
        """
        warnings.warn(
            "This function will be deprecated in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        company_t = self._table("COMPANY")
        security_t = self._table("SECURITY")

        from_clause = security_t.join(
            company_t, company_t.c.I_COMPANY == security_t.c.I_COMPANY
        )
        stmt = (
            select(
                company_t.c.I_COMPANY.label("company_id"),
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                company_t.c.N_COMPANY_T.label("company_name_t"),
                company_t.c.N_COMPANY_E.label("company_name_e"),
            )
            .select_from(from_clause)
            .order_by(company_t.c.I_COMPANY)
        )

        stmt = self._filter_str_in_list(
            stmt=stmt, column=security_t.c.N_SECURITY, values=symbol_list
        )

        df = self._read_sql_query(stmt)
        return df

    def get_change_name(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table CHANGE_NAME_SECURITY.

        Parameters
        ----------
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        start_date: Optional[str] = None
            start of effect_date (D_EFFECT).
        end_date: Optional[str] = None
            end of effect_date (D_EFFECT).

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
        >>> sdr = SETDataReader()
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
        warnings.warn(
            "This function will be deprecated in the future.",
            DeprecationWarning,
            stacklevel=2,
        )
        security_t = self._table("SECURITY")
        change_name_t = self._table("CHANGE_NAME_SECURITY")

        from_clause = change_name_t.join(
            security_t, security_t.c.I_SECURITY == change_name_t.c.I_SECURITY
        )
        stmt = (
            select(
                change_name_t.c.I_SECURITY.label("symbol_id"),
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                change_name_t.c.D_EFFECT.label("effect_date"),
                func.trim(change_name_t.c.N_SECURITY_OLD).label("symbol_old"),
                func.trim(change_name_t.c.N_SECURITY_NEW).label("symbol_new"),
            )
            .select_from(from_clause)
            .where(change_name_t.c.D_EFFECT != None)
            .where(
                func.trim(change_name_t.c.N_SECURITY_OLD)
                != func.trim(change_name_t.c.N_SECURITY_NEW)
            )
            .order_by(change_name_t.c.D_EFFECT)
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=change_name_t.c.D_EFFECT,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = self._read_sql_query(stmt)
        df = df.drop_duplicates(ignore_index=True)
        return df

    def get_dividend(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ca_type_list: Optional[List[str]] = None,
        adjusted_list: List[str] = ["", "CR", "PC", "RC", "SD", "XR"],  # noqa: B006
    ) -> pd.DataFrame:
        """Data from table RIGHTS_BENEFIT. Include only Cash Dividend (CD) and Stock
        Dividend (SD). Not include Cancelled (F_CANCEL!='C') and dps more than 0
        (Z_RIGHTS>0). ex_date and pay_date can be null.

        Parameters
        ----------
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        start_date: Optional[str] = None
            start of ex_date (D_SIGN).
        end_date: Optional[str] = None
            end of ex_date (D_SIGN).
        ca_type_list: Optional[List[str]] = None
            Corporate action type (N_CA_TYPE).
                - CD - cash dividend
                - SD - stock dividend
        adjusted_list: List[str] = ["", "CR", "PC", "RC", "SD", "XR"]
            Adjust data by ca_type (empty list for no adjustment).

        Returns
        -------
        pd.DataFrame
            dividend dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - ex_date: date - D_SIGN
                - pay_date: date - D_BEG_PAID
                - ca_type: str - N_CA_TYPE
                - dps: int - Z_RIGHTS

        Notes
        -----
        - ex_date and pay_date can be null.
        - pay_date can be non trade date.

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader()
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
        if ca_type_list is None:
            ca_type_list = ["CD", "SD"]

        df = self.get_rights_benefit(
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            ca_type_list=ca_type_list,
        )

        df = df.rename(columns={"sign_date": "ex_date"})

        # filter dps > 0
        df = df[df["dps"] > 0]

        df = self._merge_adjust_factor_dividend(df, adjusted_list=adjusted_list)

        return df

    def get_rights_benefit(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ca_type_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Data from table RIGHTS_BENEFIT. Not include Cancelled (F_CANCEL!='C')
        sign_date and pay_date can be null.

        Parameters
        ----------
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        start_date: Optional[str] = None
            start of sign_date (D_SIGN).
        end_date: Optional[str] = None
            end of sign_date (D_SIGN).
        ca_type_list: Optional[List[str]] = None
            Corporate action type (N_CA_TYPE).
                - CD - Cash dividend
                - SD - Stock dividend
                - XR - Excluding Right
                - XM - Excluding Meetings
                - XI - Excluding Interest
                - XE - Excluding Exercise
                - ND - No dividend
                - XC - Exclude Conversion
                - CR - Capital Reduction
                - PP - Private Placement
                - PO - Public Offering
                - CA - Capital Announce
                - XN - Excluding Capital Return
                - XB - Excluding Other Benefit

        Returns
        -------
        pd.DataFrame
            dividend dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - sign_date: date - D_SIGN
                - pay_date: date - D_BEG_PAID
                - ca_type: str - N_CA_TYPE
                - dps: int - Z_RIGHTS

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader()
        >>> sdr.get_rights_benefit(["M"])
           symbol  sign_date   pay_date ca_type  dps
        0       M        NaT        NaT      CA  NaN
        1       M        NaT        NaT      CR  NaN
        2       M 2014-03-13        NaT      XM  NaN
        3       M 2014-05-06 2014-05-21      CD  1.6
        4       M 2014-08-20 2014-09-04      CD  0.8
        5       M 2015-03-10        NaT      XM  NaN
        6       M 2015-04-30 2015-05-21      CD  1.0
        7       M 2015-08-24 2015-09-08      CD  0.9
        8       M 2016-03-08        NaT      XM  NaN
        9       M 2016-04-28 2016-05-19      CD  1.0
        10      M 2016-08-23 2016-09-08      CD  1.0
        11      M 2017-03-08        NaT      XM  NaN
        12      M 2017-05-04 2017-05-23      CD  1.1
        13      M 2017-08-22 2017-09-08      CD  1.1
        14      M 2018-03-09        NaT      XM  NaN
        15      M 2018-05-07 2018-05-23      CD  1.2
        16      M 2018-08-22 2018-09-07      CD  1.2
        17      M 2019-03-11        NaT      XM  NaN
        18      M 2019-05-07 2019-05-23      CD  1.3
        19      M 2019-08-26 2019-09-11      CD  1.3
        20      M 2020-04-22 2020-05-08      CD  1.3
        21      M 2020-06-22        NaT      XM  NaN
        22      M 2020-08-24 2020-09-10      CD  0.5
        23      M 2021-03-09        NaT      XM  NaN
        24      M 2021-05-10 2021-05-25      CD  0.5
        25      M 2022-03-09        NaT      XM  NaN
        26      M 2022-05-10 2022-05-25      CD  0.8
        27      M 2022-08-23 2022-09-08      CD  0.5
        >>> sdr.get_rights_benefit(["M"], start_date="2020-07-28", end_date="2022-05-11")
          symbol  sign_date   pay_date ca_type  dps
        0      M 2020-08-24 2020-09-10      CD  0.5
        1      M 2021-03-09        NaT      XM  NaN
        2      M 2021-05-10 2021-05-25      CD  0.5
        3      M 2022-03-09        NaT      XM  NaN
        4      M 2022-05-10 2022-05-25      CD  0.8
        """
        security_t = self._table("SECURITY")
        rights_benefit_t = self._table("RIGHTS_BENEFIT")

        from_clause = rights_benefit_t.join(
            security_t, security_t.c.I_SECURITY == rights_benefit_t.c.I_SECURITY
        )
        stmt = (
            select(
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                rights_benefit_t.c.D_SIGN.label("sign_date"),
                rights_benefit_t.c.D_BEG_PAID.label("pay_date"),
                func.trim(rights_benefit_t.c.N_CA_TYPE).label("ca_type"),
                rights_benefit_t.c.Z_RIGHTS.label("dps"),
            )
            .select_from(from_clause)
            .where(func.trim(rights_benefit_t.c.F_CANCEL) != "C")
            .order_by(rights_benefit_t.c.D_SIGN)
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

        df = self._read_sql_query(stmt)

        return df

    def get_delisted(
        self,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_DETAIL. Filter delisted by D_DELISTED != None.

        Parameters
        ----------
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        start_date: Optional[str] = None
            start of delisted_date (D_DELISTED).
        end_date: Optional[str] = None
            end of delisted_date (D_DELISTED).

        Returns
        -------
        pd.DataFrame
            delisted dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - delisted_date: date - D_DELISTED

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader()
        >>> sdr.get_delisted(start_date="2020-02-20", end_date="2020-02-20")
             symbol delisted_date
        0    ROBINS    2020-02-20
        1    KK202A    2020-02-20
        2  CB20220A    2020-02-20
        3  CB20220B    2020-02-20
        """
        warnings.warn(
            "This function will be deprecated in the future.",
            DeprecationWarning,
            stacklevel=2,
        )

        security_t = self._table("SECURITY")
        security_detail_t = self._table("SECURITY_DETAIL")

        from_clause = security_detail_t.join(
            security_t, security_t.c.I_SECURITY == security_detail_t.c.I_SECURITY
        )
        stmt = (
            select(
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                security_detail_t.c.D_DELISTED.label("delisted_date"),
            )
            .select_from(from_clause)
            .where(security_detail_t.c.D_DELISTED != None)
            .order_by(security_detail_t.c.D_DELISTED)
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=security_detail_t.c.D_DELISTED,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = self._read_sql_query(stmt)
        return df

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
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        start_date: Optional[str] = None
            start of hold_date (D_HOLD).
        end_date: Optional[str] = None
            end of hold_date (D_HOLD).
        sign_list: Optional[List[str]] = None,
            N_SIGN in sign_list.
                - C - Caution Flag
                - CM - Call Market
                - DS - Designated
                - H - Halt
                - NC - Non Compliance
                - NP - Notice Pending
                - SP - Suspension
                - ST - Stabilization

        Returns
        -------
        pd.DataFrame
            sp dataframe contain columns:
                - symbol: str - SECURITY.N_SECURITY
                - hold_date: date - D_HOLD
                - release_date: date - D_RELEASE
                - sign: str - N_SIGN

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> sdr = SETDataReader()
        >>> sdr.get_sign_posting(symbol_list=["THAI"], start_date="2020-11-12", end_date="2021-02-25")
          symbol  hold_date release_date sign
        0   THAI 2020-11-12   2020-11-13   SP
        1   THAI 2021-02-25          NaT   SP
        """
        security_t = self._table("SECURITY")
        sign_posting_t = self._table("SIGN_POSTING")

        from_clause = sign_posting_t.join(
            security_t, security_t.c.I_SECURITY == sign_posting_t.c.I_SECURITY
        )
        stmt = (
            select(
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                sign_posting_t.c.D_HOLD.label("hold_date"),
                sign_posting_t.c.D_RELEASE.label("release_date"),
                func.trim(sign_posting_t.c.N_SIGN).label("sign"),
            )
            .select_from(from_clause)
            .order_by(sign_posting_t.c.D_HOLD)
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

        df = self._read_sql_query(stmt)
        return df

    def get_symbols_by_index(
        self,
        index_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table SECURITY_INDEX.

        Parameters
        ----------
        index_list: Optional[List[str]] = None
            index (SECTOR.N_SYMBOL_FEED)
                - SETWB
                - SETTHSI
                - SETCLMV
                - SETHD
                - sSET
                - SET100
                - SET50
        start_date: Optional[str] = None
            start of as_of_date (D_AS_OF).
        end_date: Optional[str] = None
            end of as_of_date (D_AS_OF).

        Returns
        -------
        pd.DataFrame
            - as_of_date: date - D_AS_OF
            - index: str - SECTOR.N_SYMBOL_FEED
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
        >>> sdr = SETDataReader()
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
        46 2022-01-04  SET50   TRUEE   47
        47 2022-01-04  SET50  ADVANC   48
        48 2022-01-04  SET50  INTUCH   49
        49 2022-01-04  SET50     KCE   50
        """
        security_t = self._table("SECURITY")
        sector_t = self._table("SECTOR")
        security_index_t = self._table("SECURITY_INDEX")

        from_clause = self._join_sector_table(security_index_t).join(
            security_t, security_t.c.I_SECURITY == security_index_t.c.I_SECURITY
        )
        stmt = (
            select(
                security_index_t.c.D_AS_OF.label("as_of_date"),
                func.trim(sector_t.c.N_SYMBOL_FEED).label("index"),
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                security_index_t.c.S_SEQ.label("seq"),
            )
            .select_from(from_clause)
            .where(
                case(
                    (
                        func.trim(sector_t.c.N_SYMBOL_FEED) == fld.INDEX_SET50,
                        security_index_t.c.S_SEQ <= set50_number,
                    ),
                    (
                        func.trim(sector_t.c.N_SYMBOL_FEED) == fld.INDEX_SET100,
                        security_index_t.c.S_SEQ <= set100_number,
                    ),
                    (
                        func.trim(sector_t.c.N_SYMBOL_FEED) == fld.INDEX_SETHD,
                        security_index_t.c.S_SEQ <= sethd_number,
                    ),
                    else_=True,
                )
            )
            .order_by(
                security_index_t.c.D_AS_OF,
                sector_t.c.N_SYMBOL_FEED,
                security_index_t.c.S_SEQ,
            )
        )
        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=sector_t.c.N_SYMBOL_FEED,
            date_column=security_index_t.c.D_AS_OF,
            symbol_list=index_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = self._read_sql_query(stmt)

        return df

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
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        start_date: Optional[str] = None
            start of effect_date (D_EFFECT).
        end_date: Optional[str] = None
            end of effect_date (D_EFFECT).
        ca_type_list: Optional[List[str]] = None
            Corporate action type (N_CA_TYPE).
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
        >>> sdr = SETDataReader()
        >>> sdr.get_adjust_factor(symbol_list=["RAM"])
          symbol effect_date ca_type  adjust_factor
        0    RAM  2019-06-17      PC           0.05
        1    RAM  2021-11-09      PC           0.20
        """
        security_t = self._table("SECURITY")
        adjust_factor_t = self._table("ADJUST_FACTOR")

        from_clause = adjust_factor_t.join(
            security_t, security_t.c.I_SECURITY == adjust_factor_t.c.I_SECURITY
        )
        stmt = (
            select(
                func.trim(security_t.c.N_SECURITY).label("symbol"),
                adjust_factor_t.c.D_EFFECT.label("effect_date"),
                adjust_factor_t.c.N_CA_TYPE.label("ca_type"),
                adjust_factor_t.c.R_ADJUST_FACTOR.label("adjust_factor"),
            )
            .select_from(from_clause)
            .order_by(adjust_factor_t.c.D_EFFECT)
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

        df = self._read_sql_query(stmt)

        return df

    def get_data_symbol_daily(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjusted_list: List[str] = ["", "CR", "PC", "RC", "SD", "XR"],  # noqa: B006
    ) -> pd.DataFrame:
        """Data from table DAILY_STOCK_TRADE, DAILY_STOCK_STAT.

        Filter only Auto Matching (I_TRADING_METHOD='A').

        Parameters
        ----------
        field: str
            - prior
            - open
            - high
            - low
            - close
            - average
            - last_bid
            - last_offer
            - trans
            - volume
            - value
            - pe
            - pb
            - par
            - dps
            - dvd_yield
            - mkt_cap
            - eps
            - book_value
            - quarter_fin
            - month_dvd
            - as_of
            - dividend
            - status
            - benefit
            - share_listed
            - turnover
            - share_index
            - npg
            - total_volume
            - total_value
            - beta
            - roi
            - acc_dps
            - dvd_payment
            - dvd_payout
            - earning
            - iv
            - delta
            - notice
            - non_compliance
            - stabilization
            - call_market
            - caution
            - 12m_dvd_yield
            - peg
            - has_trade (if close > 0 or last_bid > 0 or last_offer > 0 return 1.0 else 0.0/nan)
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list (must be unique).
        start_date: Optional[str] = None
            start of trade_date (D_TRADE), by default None
        end_date: Optional[str] = None
            end of trade_date (D_TRADE), by default None
        adjusted_list: List[str] = ["", "CR", "PC", "RC", "SD", "XR"]
            Adjust data by ca_type (empty list for no adjustment).

        Returns
        -------
        pd.DataFrame
            - symbol(N_SECURITY): str as column
            - trade_date(D_TRADE): date as index

        Warning
        -------
        - OHLCV is 0 if no trade.

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
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
            symbol_list = [i.strip().upper() for i in symbol_list]

        security_t = self._table("SECURITY")

        if field in fld.DAILY_STOCK_TRADE_MAP:
            daily_stock_t = self._table("DAILY_STOCK_TRADE")
            value_col = daily_stock_t.c[fld.DAILY_STOCK_TRADE_MAP[field]]
        elif field in fld.DAILY_STOCK_STAT_MAP:
            daily_stock_t = self._table("DAILY_STOCK_STAT")
            value_col = daily_stock_t.c[fld.DAILY_STOCK_STAT_MAP[field]]
        elif field == "has_trade":
            daily_stock_t = self._table("DAILY_STOCK_TRADE")
            value_col = or_(
                daily_stock_t.c.Z_CLOSE > 0,
                daily_stock_t.c.Z_LAST_BID > 0,
                daily_stock_t.c.Z_LAST_OFFER > 0,
            )
        else:
            msg = (
                f"{field} is invalid field. Please read document to check valid field."
            )
            raise InputError(msg)

        from_clause = daily_stock_t.join(
            security_t, daily_stock_t.c.I_SECURITY == security_t.c.I_SECURITY
        )

        stmt = (
            select(
                daily_stock_t.c.D_TRADE.label(TRADE_DATE),
                func.trim(security_t.c.N_SECURITY).label(NAME),
                value_col.label(VALUE),
            )
            .select_from(from_clause)
            .order_by(daily_stock_t.c.D_TRADE)
        )
        if "I_TRADING_METHOD" in daily_stock_t.c:
            stmt = stmt.where(
                func.trim(daily_stock_t.c.I_TRADING_METHOD) == "A"
            )  # Auto Matching

        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=security_t.c.N_SECURITY,
            date_column=daily_stock_t.c.D_TRADE,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = self._read_sql_query(stmt, index_col=TRADE_DATE)

        df = self._pivot_name_value(df)

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

        if symbol_list is not None:
            df = df.reindex(columns=[i for i in symbol_list if i in df.columns])

        return df

    def get_data_symbol_quarterly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from tables FINANCIAL_STAT_STD and FINANCIAL_SCREEN.If field is in both
        table, the data from FINANCIAL_STAT_STD will be used.

        FINANCIAL_STAT_STD using data from column M_ACCOUNT multiply 1000.
        FINANCIAL_SCREEN filter by I_PERIOD_TYPE='QY' and I_PERIOD in ('Q1','Q2','Q3','Q4').

        Index date is the trading date (DAILY_STOCK_STAT.D_TRADE). Data is showing at first trade date which join on D_AS_OF.

        Parameters
        ----------
        field: str
            - account_payable
            - account_receivable
            - accrued_int_receive
            - accumulate
            - allowance
            - ap_turnover
            - ar_turnover
            - as_of
            - asset_turnover
            - bad_debt
            - broker_fee
            - cap_paidin
            - cap_paidup
            - cash
            - cash_cycle
            - change_ppe
            - common_share
            - cos
            - current_asset
            - current_liability
            - current_ratio
            - de
            - deposit
            - dividend
            - dp
            - dscr
            - earning_asset
            - ebit
            - ebitda
            - ebt
            - eps
            - fix_asset_turnover
            - gross_profit_margin
            - ibde
            - int_bearing_debt
            - int_dvd_income
            - interest_coverage
            - interest_expense
            - interest_income
            - inventory
            - inventory_turnover
            - invest_asset
            - invest_sec_rev
            - invest_security
            - investment
            - loan
            - loan_deposit_revenue
            - loan_from_relatedparty
            - loan_revenue
            - loan_to_relatedparty
            - longterm_liability_currentportion
            - longterm_liability_net_currentportion
            - minority_interest
            - net_cash_flow
            - net_cashflow
            - net_financing
            - net_investing
            - net_operating
            - net_premium
            - net_profit
            - net_profit_incl_minority
            - net_profit_margin
            - net_profit_ordinary
            - operating_expense
            - operating_revenue
            - period
            - period_type
            - pl_other_activities
            - ppe
            - preferred_share
            - quarter
            - quick_ratio
            - retain_earning
            - retain_earning_unappropriate
            - roa
            - roe
            - sale
            - selling_admin
            - selling_admin_exc_renumuration
            - shld_equity
            - short_invest
            - total_asset
            - total_equity
            - total_expense
            - total_liability
            - total_revenue
            - year
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list, must be unique.
        start_date: Optional[str] = None
            start of trade date (DAILY_STOCK_STAT.D_TRADE).
        end_date: Optional[str] = None
            end of trade date (DAILY_STOCK_STAT.D_TRADE).

        Returns
        -------
        pd.DataFrame
            - symbol(N_SECURITY): str as column
            - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
        >>> sdr.get_data_symbol_quarterly(
        ...     field=fld.Q_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7      MALEE
        2022-03-01          NaN  953995.79
        2022-03-04  17573710.66        NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            timeframe=fld.TIMEFRAME_QUARTERLY,
        )

    def get_data_symbol_yearly(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table FINANCIAL_STAT_STD and FINANCIAL_SCREEN. If field is in both
        table, the data from FINANCIAL_STAT_STD will be used.

        FINANCIAL_STAT_STD filter by "I_QUARTER"='9' and using data from column M_ACCOUNT multiply 1000.
        FINANCIAL_SCREEN filter by I_PERIOD_TYPE='QY' and I_PERIOD='YE'.

        Index date is trade date (DAILY_STOCK_STAT.D_TRADE). Data is showing at first trade date which join on D_AS_OF.

        Parameters
        ----------
        field: str
            - account_payable
            - account_receivable
            - accrued_int_receive
            - accumulate
            - allowance
            - ap_turnover
            - ar_turnover
            - as_of
            - asset_turnover
            - bad_debt
            - broker_fee
            - cap_paidin
            - cap_paidup
            - cash
            - cash_cycle
            - change_ppe
            - common_share
            - cos
            - current_asset
            - current_liability
            - current_ratio
            - de
            - deposit
            - dividend
            - dp
            - dscr
            - earning_asset
            - ebit
            - ebitda
            - ebt
            - eps
            - fix_asset_turnover
            - gross_profit_margin
            - ibde
            - int_bearing_debt
            - int_dvd_income
            - interest_coverage
            - interest_expense
            - interest_income
            - inventory
            - inventory_turnover
            - invest_asset
            - invest_sec_rev
            - invest_security
            - investment
            - loan
            - loan_deposit_revenue
            - loan_from_relatedparty
            - loan_revenue
            - loan_to_relatedparty
            - longterm_liability_currentportion
            - longterm_liability_net_currentportion
            - minority_interest
            - net_cash_flow
            - net_cashflow
            - net_financing
            - net_investing
            - net_operating
            - net_premium
            - net_profit
            - net_profit_incl_minority
            - net_profit_margin
            - net_profit_ordinary
            - operating_expense
            - operating_revenue
            - period
            - period_type
            - pl_other_activities
            - ppe
            - preferred_share
            - quarter
            - quick_ratio
            - retain_earning
            - retain_earning_unappropriate
            - roa
            - roe
            - sale
            - selling_admin
            - selling_admin_exc_renumuration
            - shld_equity
            - short_invest
            - total_asset
            - total_equity
            - total_expense
            - total_liability
            - total_revenue
            - year
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list, must be unique.
        start_date: Optional[str] = None
            start of trade date (DAILY_STOCK_STAT.D_TRADE).
        end_date: Optional[str] = None
            end of trade date (DAILY_STOCK_STAT.D_TRADE).

        Returns
        -------
        pd.DataFrame
            - symbol(N_SECURITY): str as column
            - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
        >>> sdr.get_data_symbol_yearly(
        ...     field=fld.Y_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7       MALEE
        2022-03-01          NaN  3488690.79
        2022-03-04  51154660.73         NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            timeframe=fld.TIMEFRAME_YEARLY,
        )

    def get_data_symbol_ttm(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Trailing 12 months (TTM) is a term used to describe the past 12 consecutive
        months of a company's performance data.

        TTM can be calculate only Income Statement and Cashflow, but not Financial Ratio and Balance Sheet.

        Data from table FINANCIAL_STAT_STD.

        FINANCIAL_STAT_STD filter by using data from column M_ACC_ACCOUNT_12M multiply 1000.

        Index date is trade date (DAILY_STOCK_STAT.D_TRADE). Data is showing at first trade date which join on D_AS_OF.

        Parameters
        ----------
        field : str
            - bad_debt
            - broker_fee
            - change_ppe
            - cos
            - dividend
            - dp
            - ebit
            - ebitda
            - ebt
            - eps
            - int_dvd_income
            - interest_expense
            - interest_income
            - invest_sec_rev
            - loan_deposit_revenue
            - net_cash_flow
            - net_financing
            - net_investing
            - net_operating
            - net_premium
            - net_profit
            - net_profit_incl_minority
            - net_profit_ordinary
            - operating_expense
            - operating_revenue
            - pl_other_activities
            - sale
            - selling_admin
            - selling_admin_exc_renumuration
            - total_expense
            - total_revenue
        symbol_list : Optional[List[str]]
            N_SECURITY in symbol_list, must be unique.
        start_date : Optional[str]
            start of trade date (DAILY_STOCK_STAT.D_TRADE).
        end_date : Optional[str]
            end of trade date (DAILY_STOCK_STAT.D_TRADE).

        Returns
        -------
        pd.DataFrame
            - symbol(N_SECURITY): str as column
            - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
        >>> sdr.get_data_symbol_ttm(
        ...     field=fld.Q_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7       MALEE
        2022-03-01          NaN  3488690.79
        2022-03-04  51154660.73         NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            timeframe=fld.TIMEFRAME_TTM,
        )

    def get_data_symbol_ytd(
        self,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Year to date (YTD) refers to the period of time beginning the first day of
        the current calendar year or fiscal year up to the current date.

        Data from table FINANCIAL_STAT_STD and FINANCIAL_SCREEN. If field is in both table, the data from FINANCIAL_STAT_STD will be used.

        FINANCIAL_STAT_STD using data from column M_ACC_ACCOUNT multiply 1000.
        FINANCIAL_SCREEN filter by I_PERIOD_TYPE='QY' and I_PERIOD in ('Q1','6M','9M','YE').

        Index date is trade date (DAILY_STOCK_STAT.D_TRADE). Data is showing at first DAILY_STOCK_STAT.D_TRADE which join on D_AS_OF.

        Parameters
        ----------
        field: str
            - bad_debt
            - broker_fee
            - change_ppe
            - cos
            - dividend
            - dp
            - ebit
            - ebitda
            - ebt
            - eps
            - int_dvd_income
            - interest_expense
            - interest_income
            - invest_sec_rev
            - loan_deposit_revenue
            - net_cash_flow
            - net_financing
            - net_investing
            - net_operating
            - net_premium
            - net_profit
            - net_profit_incl_minority
            - net_profit_ordinary
            - operating_expense
            - operating_revenue
            - pl_other_activities
            - sale
            - selling_admin
            - selling_admin_exc_renumuration
            - total_expense
            - total_revenue
        symbol_list: Optional[List[str]] = None
            N_SECURITY in symbol_list, must be unique.
        start_date: Optional[str] = None
            start of trade date (DAILY_STOCK_STAT.D_TRADE).
        end_date: Optional[str] = None
            end of trade date (DAILY_STOCK_STAT.D_TRADE).

        Returns
        -------
        pd.DataFrame
            - symbol(N_SECURITY): str as column
            - trade date(DAILY_STOCK_STAT.D_TRADE): date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
        >>> sdr.get_data_symbol_ytd(
        ...     field=fld.Q_TOTAL_REVENUE,
        ...     symbol_list=["COM7", "MALEE"],
        ...     start_date="2022-02-01",
        ...     end_date=None,
        ... )
                           COM7       MALEE
        2022-03-01          NaN  3488690.79
        2022-03-04  51154660.73         NaN
        """
        return self._get_fundamental_data(
            symbol_list=symbol_list,
            field=field,
            start_date=start_date,
            end_date=end_date,
            timeframe=fld.TIMEFRAME_YTD,
        )

    def get_data_index_daily(
        self,
        field: str,
        index_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table DAILY_SECTOR_INFO. Filter only market data.

        Parameters
        ----------
        field: str
            - prior
            - open
            - high
            - low
            - close
            - trans
            - volume
            - value
            - mkt_pe
            - mkt_pbv
            - mkt_yield
            - mkt_cap
            - turnover
            - share_listed_avg
            - beta
            - turnover_volume
            - 12m_dvd_yield
        index_list: Optional[List[str]] = None
            N_SYMBOL_FEED in index_list. More index can be found in ezyquant.fields
        start_date: Optional[str] = None
            start of trade_date (D_TRADE).
        end_date: Optional[str] = None
            end of trade_date (D_TRADE).

        Returns
        -------
        pd.DataFrame
            - index: str as column
            - trade_date: date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
        >>> sdr.get_data_index_daily(
        ...     field=fld.D_INDEX_CLOSE,
        ...     index_list=[fld.MARKET_SET, fld.INDEX_SET100],
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
        return self._get_daily_sector_info(
            field=field,
            symbol_list=index_list,
            start_date=start_date,
            end_date=end_date,
            f_data="M",
        )

    def get_data_sector_daily(
        self,
        field: str,
        sector_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table DAILY_SECTOR_INFO. Filter only sector data.

        Parameters
        ----------
        field: str
            - prior
            - open
            - high
            - low
            - close
            - trans
            - volume
            - value
            - mkt_pe
            - mkt_pbv
            - mkt_yield
            - mkt_cap
            - turnover
            - share_listed_avg
            - beta
            - turnover_volume
            - 12m_dvd_yield
        sector_list: Optional[List[str]] = None
            N_SYMBOL_FEED in sector_list. More sector can be found in ezyquant.fields
        start_date: Optional[str] = None
            start of trade_date (D_TRADE).
        end_date: Optional[str] = None
            end of trade_date (D_TRADE).

        Returns
        -------
        pd.DataFrame
            - sector: str as column
            - trade_date: date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
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
            symbol_list=sector_list,
            start_date=start_date,
            end_date=end_date,
            f_data="S",
        )

    def get_data_industry_daily(
        self,
        field: str,
        industry_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Data from table DAILY_SECTOR_INFO. Filter only industry data.

        Parameters
        ----------
        field: str
            - prior
            - open
            - high
            - low
            - close
            - trans
            - volume
            - value
            - mkt_pe
            - mkt_pbv
            - mkt_yield
            - mkt_cap
            - turnover
            - share_listed_avg
            - beta
            - turnover_volume
            - 12m_dvd_yield
        industry_list: Optional[List[str]] = None
            N_SYMBOL_FEED in industry_list. More industry can be found in ezyquant.fields
        start_date: Optional[str] = None
            start of trade_date (D_TRADE).
        end_date: Optional[str] = None
            end of trade_date (D_TRADE).

        Returns
        -------
        pd.DataFrame
            - industry: str as column
            - trade_date: date as index

        Examples
        --------
        >>> from ezyquant import SETDataReader
        >>> from ezyquant import fields as fld
        >>> sdr = SETDataReader()
        >>> sdr.get_data_industry_daily(
        ...     field=fld.D_INDUSTRY_CLOSE,
        ...     industry_list=[fld.INDUSTRY_AGRO, fld.INDUSTRY_FINCIAL],
        ...     start_date="2022-01-01",
        ...     end_date="2022-01-10",
        ... )
                      AGRO  FINCIAL
        2022-01-04  485.98   182.10
        2022-01-05  484.98   183.50
        2022-01-06  482.90   181.39
        2022-01-07  484.50   182.81
        2022-01-10  487.10   182.79
        """
        return self._get_daily_sector_info(
            field=field,
            symbol_list=industry_list,
            start_date=start_date,
            end_date=end_date,
            f_data="I",
        )

    """
    Protected methods
    """

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            msg = "engine is not set"
            raise ValueError(msg)
        return self._engine

    def _func_date(self, column: ColumnElement):
        """Convert date column to date type for sqlite engine.

        Usually use in where clause. Select clause will be converted automatically by
        pandas.read_sql_query
        """
        if self.engine.name == "sqlite":
            return func.DATE(column)
        return column

    def _table(self, name: str) -> Table:
        return Table(name, self._metadata, autoload_with=self._engine)

    def _read_sql_query(
        self, stmt: Select, index_col: Optional[str] = None
    ) -> pd.DataFrame:
        col_name_list = [i.name for i in stmt.selected_columns if hasattr(i, "name")]

        parse_dates = [i for i in col_name_list if i.endswith("_date")]

        with self.engine.connect() as conn:
            df = pd.read_sql_query(
                stmt, con=conn, index_col=index_col, parse_dates=parse_dates
            )

        if VALUE in col_name_list:
            try:
                df = df.astype({VALUE: "float64"})
            except ValueError:
                pass

        return df

    def _filter_stmt_by_date(
        self,
        stmt: Select,
        column: ColumnElement,
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        if isinstance(column.table, Table) and "D_TRADE" in column.table.columns:
            last_update_date = self.last_table_update(column.table)
        else:
            last_update_date = None

        vld.check_start_end_date(
            start_date=start_date,
            end_date=end_date,
            last_update_date=last_update_date,
        )

        if start_date is not None and end_date is not None:
            stmt = stmt.where(self._func_date(column).between(start_date, end_date))
        elif start_date is not None:
            stmt = stmt.where(self._func_date(column) >= start_date)
        elif end_date is not None:
            stmt = stmt.where(self._func_date(column) <= end_date)

        return stmt

    def _filter_str_in_list(
        self, stmt: Select, column: ColumnElement, values: Optional[List[str]]
    ):
        vld.check_duplicate(values)
        if values is not None:
            values = [i.strip().upper() for i in values]
            stmt = stmt.where(func.upper(func.trim(column)).in_(values))
        return stmt

    def _filter_stmt_by_symbol_and_date(
        self,
        stmt: Select,
        symbol_column: ColumnElement,
        date_column: ColumnElement,
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

    def _d_trade_subquery(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Subquery:
        daily_stock_stat_t = self._table("DAILY_STOCK_STAT")
        stmt = select(
            daily_stock_stat_t.c.I_SECURITY,
            daily_stock_stat_t.c.D_AS_OF,
            func.min(daily_stock_stat_t.c.D_TRADE).label("D_TRADE"),
        )
        stmt = self._filter_stmt_by_date(
            stmt=stmt,
            column=daily_stock_stat_t.c.D_TRADE,
            start_date=start_date,
            end_date=end_date,
        )
        stmt = stmt.group_by(
            daily_stock_stat_t.c.I_SECURITY, daily_stock_stat_t.c.D_AS_OF
        )
        return stmt.subquery()

    def _join_security_and_d_trade_subquery(
        self, table: Table, d_trade_subquery: Subquery
    ) -> Join:
        security_t = self._table("SECURITY")
        return d_trade_subquery.join(
            table,
            and_(
                table.c.I_SECURITY == d_trade_subquery.c.I_SECURITY,
                table.c.D_AS_OF == d_trade_subquery.c.D_AS_OF,
            ),
        ).join(security_t, security_t.c.I_SECURITY == d_trade_subquery.c.I_SECURITY)

    def _join_sector_table(
        self,
        table: FromClause,
        isouter: bool = False,
        sector_t: Optional[FromClause] = None,
        is_join_sector: bool = True,
    ):
        if sector_t is None:
            sector_t = self._table("SECTOR")

        prefix = ""
        if isinstance(table, Join):
            if not isinstance(table.left, Table):
                msg = "table must be a Table or Join of Table"
                raise ValueError(msg)
            prefix = table.left.name + "_"

        return table.join(
            sector_t,
            onclause=and_(
                sector_t.c.I_MARKET == table.c[f"{prefix}I_MARKET"],
                sector_t.c.I_INDUSTRY == table.c[f"{prefix}I_INDUSTRY"],
                sector_t.c.I_SECTOR
                == (table.c[f"{prefix}I_SECTOR"] if is_join_sector else 0),
            ),
            isouter=isouter,
        )

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
        df: pd.DataFrame
            index must be trade_date and columns must be symbol.
        is_multiply: bool = True
            is multiply by adjust factor (adjust factor usually less than 1).
        start_adjust_date: Optional[str] = None
            start of get adjust factor effect date.
        adjusted_list: Optional[List[str]] = None
            n_ca_type list.

        Returns
        -------
        pd.DataFrame
            index is trade_date and columns is symbol
        """
        if df.empty:
            return df

        if start_adjust_date is None:
            start_adjust_date = utils.date_to_str(df.index.min())

        symbol_list = df.columns.tolist()

        adjust_factor_df = self._get_pivot_adjust_factor_df(
            min_date=utils.date_to_str(df.index.min()),
            max_date=utils.date_to_str(df.index.max()),
            symbol_list=symbol_list,
            start_date=start_adjust_date,
            ca_type_list=adjusted_list,
        )

        # reindex adjust_factor_df to df
        adjust_factor_df = adjust_factor_df.reindex(df.index)

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

        if start_adjust_date is None:
            start_adjust_date = utils.date_to_str(df["ex_date"].min())

        symbol_list = df["symbol"].unique().tolist()

        adjust_factor_df = self._get_pivot_adjust_factor_df(
            min_date=utils.date_to_str(df["ex_date"].min()),
            max_date=utils.date_to_str(df["ex_date"].max()),
            symbol_list=symbol_list,
            start_date=start_adjust_date,
            ca_type_list=adjusted_list,
        )

        adjust_factor_df = adjust_factor_df.stack().rename("adjust_factor").reset_index()  # type: ignore

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

    def _get_pivot_adjust_factor_df(
        self,
        min_date: str,
        max_date: str,
        symbol_list: Optional[List[str]],
        start_date: Optional[str] = None,
        ca_type_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        should_symbol_list_none = (
            symbol_list is None or len(symbol_list) > sqlite_max_variable_number
        )

        df = self.get_adjust_factor(
            symbol_list=None if should_symbol_list_none else symbol_list,
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
            ),
            columns=symbol_list,
        )

        # shift back 1 day
        df = df.shift(-1)

        # back fill and fill 1
        df = df.fillna(method="backfill").fillna(1)

        return df

    def _get_financial_screen_stmt(
        self, timeframe: str, field: str, d_trade_subquery: Subquery
    ) -> Select:
        financial_screen_t = self._table("FINANCIAL_SCREEN")
        security_t = self._table("SECURITY")

        value_column = financial_screen_t.c[fld.FINANCIAL_SCREEN_MAP[field]]

        stmt = (
            select(
                d_trade_subquery.c.D_TRADE.label(TRADE_DATE),
                func.trim(security_t.c.N_SECURITY).label(NAME),
                value_column.label(VALUE),
            )
            .select_from(
                self._join_security_and_d_trade_subquery(
                    financial_screen_t, d_trade_subquery=d_trade_subquery
                )
            )
            .where(func.trim(financial_screen_t.c.I_PERIOD_TYPE) == "QY")
            .where(
                func.trim(financial_screen_t.c.I_PERIOD).in_(TIMEFRAME_MAP[timeframe])
            )
        )

        return stmt

    def _get_financial_stat_std_stmt(
        self, timeframe: str, field: str, d_trade_subquery: Subquery
    ) -> Select:
        financial_stat_std_t = self._table("FINANCIAL_STAT_STD")
        security_t = self._table("SECURITY")

        field_type = ""
        for i in fld.FINANCIAL_STAT_STD_MAP:
            if field in fld.FINANCIAL_STAT_STD_MAP[i]:
                field_type = i
                break

        if timeframe == fld.TIMEFRAME_QUARTERLY:
            value_column = financial_stat_std_t.c["M_ACCOUNT"]
        elif timeframe == fld.TIMEFRAME_YEARLY and field_type == "B":
            value_column = financial_stat_std_t.c["M_ACCOUNT"]
        elif timeframe == fld.TIMEFRAME_YEARLY:
            value_column = financial_stat_std_t.c["M_ACC_ACCOUNT_12M"]
        elif timeframe == fld.TIMEFRAME_YTD and field_type != "B":
            value_column = financial_stat_std_t.c["M_ACC_ACCOUNT"]
        elif timeframe == fld.TIMEFRAME_TTM and field_type != "B":
            value_column = financial_stat_std_t.c["M_ACC_ACCOUNT_12M"]
        else:
            msg = f"Invalid timeframe {timeframe}"
            raise ValueError(msg)

        db_field = fld.FINANCIAL_STAT_STD_MAP[field_type][field]

        if db_field.startswith("m_"):
            value_column *= 1000  # Database stores in thousands bath

        stmt = (
            select(
                d_trade_subquery.c.D_TRADE.label(TRADE_DATE),
                func.trim(security_t.c.N_SECURITY).label(NAME),
                value_column.label(VALUE),
            )
            .select_from(
                self._join_security_and_d_trade_subquery(
                    financial_stat_std_t, d_trade_subquery=d_trade_subquery
                )
            )
            .where(func.trim(financial_stat_std_t.c.N_ACCOUNT) == db_field)
        )

        if timeframe == fld.TIMEFRAME_YEARLY:
            stmt = stmt.where(financial_stat_std_t.c.I_QUARTER == fourth_quarter_number)

        return stmt

    def _get_fundamental_data(
        self,
        timeframe: str,
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fillna_value=None,
    ) -> pd.DataFrame:
        timeframe = timeframe.lower()
        field = field.lower()

        d_trade_subquery = self._d_trade_subquery(
            start_date=start_date, end_date=end_date
        )

        if field in fld.FINANCIAL_STAT_STD_MAP_COMPACT:
            stmt = self._get_financial_stat_std_stmt(
                field=field, timeframe=timeframe, d_trade_subquery=d_trade_subquery
            )
        elif field in fld.FINANCIAL_SCREEN_MAP and timeframe in (
            fld.TIMEFRAME_QUARTERLY,
            fld.TIMEFRAME_YEARLY,
        ):
            stmt = self._get_financial_screen_stmt(
                field=field, timeframe=timeframe, d_trade_subquery=d_trade_subquery
            )
        else:
            msg = (
                f"{field} is invalid field. Please read document to check valid field."
            )
            raise InputError(msg)

        security_t = self._table("SECURITY")
        stmt = self._filter_str_in_list(
            stmt=stmt, column=security_t.c.N_SECURITY, values=symbol_list
        )

        df = self._read_sql_query(stmt)

        # duplicate key mostly I_ACCT_FORM 6,7
        df = df.drop_duplicates(subset=[TRADE_DATE, NAME], keep="last")
        df = df.set_index(TRADE_DATE)

        if fillna_value is not None:
            df = df.fillna(fillna_value)

        df = self._pivot_name_value(df)

        return df

    def _get_daily_sector_info(
        self,
        field: str,
        symbol_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        f_data: str,
        is_stock_column: bool = False,
    ) -> pd.DataFrame:
        field = field.lower()
        f_data = f_data.upper()

        if f_data not in ("I", "S", "M"):
            msg = "f_data must be one of I, S, M"
            raise ValueError(msg)

        security_t = self._table("SECURITY")
        sector_t = self._table("SECTOR")
        daily_sector_info_t = self._table("DAILY_SECTOR_INFO")

        from_clause = self._join_sector_table(daily_sector_info_t)

        if is_stock_column:
            from_clause = from_clause.join(
                security_t,
                onclause=and_(
                    sector_t.c.I_MARKET == security_t.c.I_MARKET,
                    sector_t.c.I_INDUSTRY == security_t.c.I_INDUSTRY,
                    sector_t.c.I_SECTOR
                    == (security_t.c.I_SECTOR if f_data == "S" else 0),
                ),
            )
            symbol_column = security_t.c.N_SECURITY
        else:
            symbol_column = sector_t.c.N_SYMBOL_FEED

        try:
            field_col = daily_sector_info_t.c[fld.DAILY_SECTOR_INFO_MAP[field]]
        except KeyError as e:
            msg = (
                f"{field} is invalid field. Please read document to check valid field."
            )
            raise InputError(msg) from e

        stmt = (
            select(
                daily_sector_info_t.c.D_TRADE.label(TRADE_DATE),
                func.trim(symbol_column).label(NAME),
                field_col.label(VALUE),
            )
            .select_from(from_clause)
            .where(sector_t.c.F_DATA == f_data)
            .where(sector_t.c.D_CANCEL == None)
            .order_by(daily_sector_info_t.c.D_TRADE)
        )

        stmt = self._filter_stmt_by_symbol_and_date(
            stmt=stmt,
            symbol_column=symbol_column,
            date_column=daily_sector_info_t.c.D_TRADE,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        df = self._read_sql_query(stmt, index_col=TRADE_DATE)

        df = self._pivot_name_value(df)

        return df

    def _get_last_as_of_date_in_security_index(
        self, current_date: Optional[str] = None
    ) -> Dict[str, str]:
        sector_t = self._table("SECTOR")
        security_index_t = self._table("SECURITY_INDEX")

        from_clause = self._join_sector_table(security_index_t)
        stmt = (
            select(
                func.trim(sector_t.c.N_SYMBOL_FEED).label("sector"),
                func.max(security_index_t.c.D_AS_OF).label("as_of_date"),
            )
            .select_from(from_clause)
            .group_by(sector_t.c.N_SYMBOL_FEED)
        )
        stmt = self._filter_stmt_by_date(
            stmt=stmt,
            column=security_index_t.c.D_AS_OF,
            start_date=None,
            end_date=current_date,
        )

        df = self._read_sql_query(stmt)

        res = df.set_index("sector")["as_of_date"].dt.strftime("%Y-%m-%d").to_dict()
        return res

    """
    Custom business day functions
    """

    @lru_cache(maxsize=1)
    def _get_holidays(self) -> List[str]:
        tds = self.get_trading_dates()
        bds = pd.bdate_range(tds[0], tds[-1]).strftime("%Y-%m-%d")
        return list(set(bds) - set(tds))

    def _SETBusinessDay(self, n: int = 1) -> CustomBusinessDay:
        holidays = self._get_holidays()
        return CustomBusinessDay(n, normalize=True, holidays=holidays)

    """
    Static methods
    """

    @staticmethod
    def _pivot_name_value(df: pd.DataFrame) -> pd.DataFrame:
        df = utils.pivot_remove_index_name(df=df, columns=NAME, values=VALUE)
        return df


@lru_cache(maxsize=1)
def _SETDataReaderCached() -> SETDataReader:
    out: SETDataReader = utils.wrap_cache_class(SETDataReader)()  # type: ignore

    out.get_data_symbol_daily = utils.cache_dataframe_wrapper(out.get_data_symbol_daily)  # type: ignore
    out._get_fundamental_data = utils.cache_dataframe_wrapper(
        utils.cache_wrapper(out._get_fundamental_data, maxsize=1024)
    )  # type: ignore
    out._get_daily_sector_info = utils.cache_dataframe_wrapper(
        utils.cache_wrapper(out._get_daily_sector_info)
    )  # type: ignore

    return out


def SETBusinessDay(n: int = 1) -> CustomBusinessDay:
    return _SETDataReaderCached()._SETBusinessDay(n)
