from datetime import date
from typing import List, Optional

import pandas as pd
import pytest
from pandas._testing import assert_frame_equal, assert_index_equal, assert_series_equal

import ezyquant.fields as fld
from ezyquant.reader import SETDataReader


class TestGetTradingDates:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_trading_dates()

        # Check
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], date)

    @pytest.mark.parametrize(
        ("start_date", "expect_first_date"),
        [
            (date(2022, 1, 1), date(2022, 1, 4)),
            (date(2022, 1, 4), date(2022, 1, 4)),
            (date(2022, 1, 5), date(2022, 1, 5)),
        ],
    )
    def test_start_date(
        self, sdr: SETDataReader, start_date: date, expect_first_date: date
    ):
        # Test
        result = sdr.get_trading_dates(start_date=start_date)

        # Check
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], date)
        assert result[0] == expect_first_date

    @pytest.mark.parametrize(
        ("end_date", "expect_last_date"),
        [
            (date(2022, 1, 6), date(2022, 1, 6)),
            (date(2022, 1, 7), date(2022, 1, 7)),
            (date(2022, 1, 8), date(2022, 1, 7)),
            (date(2022, 1, 9), date(2022, 1, 7)),
        ],
    )
    def test_end_date(self, sdr: SETDataReader, end_date: date, expect_last_date: date):
        # Test
        result = sdr.get_trading_dates(end_date=end_date)

        # Check
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], date)
        assert result[-1] == expect_last_date

    @pytest.mark.parametrize(
        ("start_date", "end_date", "expect_dates"),
        [
            (date(2022, 1, 1), date(2022, 1, 4), [date(2022, 1, 4)]),
            (date(2022, 1, 3), date(2022, 1, 4), [date(2022, 1, 4)]),
            (date(2022, 1, 4), date(2022, 1, 4), [date(2022, 1, 4)]),
            (date(2022, 1, 1), date(2022, 1, 5), [date(2022, 1, 4), date(2022, 1, 5)]),
            (date(2022, 1, 3), date(2022, 1, 5), [date(2022, 1, 4), date(2022, 1, 5)]),
            (date(2022, 1, 4), date(2022, 1, 5), [date(2022, 1, 4), date(2022, 1, 5)]),
            (date(2022, 1, 1), date(2022, 1, 10), []),
        ],
    )
    def test_start_end_date(
        self,
        sdr: SETDataReader,
        start_date: date,
        end_date: date,
        expect_dates: List[date],
    ):
        # Test
        result = sdr.get_trading_dates(start_date=start_date, end_date=end_date)

        # Check
        print(result)
        assert result == expect_dates

    @pytest.mark.parametrize(
        ("start_date", "end_date"),
        [
            (date(2022, 1, 1), date(2022, 1, 1)),
            (date(2022, 1, 3), date(2022, 1, 3)),
            (date(2022, 1, 4), date(2022, 1, 3)),
            (date(2022, 1, 8), date(2022, 1, 7)),
        ],
    )
    def test_empty(self, sdr: SETDataReader, start_date: date, end_date: date):
        # Test
        result = sdr.get_trading_dates(start_date=start_date, end_date=end_date)

        # Check
        assert isinstance(result, list)
        assert len(result) == 0


class TestSymbolInfo:
    def test_get_all(self, sdr: SETDataReader):
        result = sdr.get_symbol_info()

        # Check
        self._check(result)

        assert not result.empty

    def test_market(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(market=fld.MARKET_MAI)

        # Check
        self._check(result)

        assert (result["market"] == fld.MARKET_SET).all()
        # MAI sector name same as industry name
        assert result["sector"].isin(fld.INDUSTRY_LIST).all()
        assert "STA" in result["symbol"]

    def test_industry(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(industry=fld.INDUSTRY_AGRO)

        # Check
        self._check(result)

        assert (result["industry"] == fld.INDUSTRY_AGRO).all()
        assert (
            result["sector"]
            .isin([fld.SECTOR_AGRI, fld.SECTOR_FOOD, fld.SECTOR_AGRO])
            .all()
        )
        assert "STA" in result["symbol"]

    def test_sector(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(sector=fld.SECTOR_AGRI)

        # Check
        self._check(result)

        # MAI sector name same as industry name
        assert (result["market"] == fld.MARKET_SET).all()
        assert (result["industry"] == fld.INDUSTRY_AGRO).all()
        assert (result["sector"] == fld.SECTOR_AGRI).all()
        assert "STA" in result["symbol"]

    @pytest.mark.parametrize("symbol_list", ["TCCC", "PTTGC"])
    @pytest.mark.parametrize("market", [fld.MARKET_SET, None])
    @pytest.mark.parametrize("industry", [fld.INDUSTRY_INDUS, None])
    @pytest.mark.parametrize("sector", [fld.SECTOR_PETRO, None])
    def test_many_parameter(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        market: Optional[str],
        industry: Optional[str],
        sector: Optional[str],
    ):
        result = sdr.get_symbol_info(
            symbol_list=symbol_list, market=market, industry=industry, sector=sector
        )

        # Check
        self._check(result)

        expect = pd.DataFrame(
            [
                [
                    741,
                    "TCCC",
                    fld.MARKET_SET,
                    fld.INDUSTRY_INDUS,
                    fld.SECTOR_PETRO,
                    "S",
                    "L",
                ],
                [
                    15382,
                    "PTTGC",
                    fld.MARKET_SET,
                    fld.INDUSTRY_INDUS,
                    fld.SECTOR_PETRO,
                    "S",
                    "L",
                ],
            ],
            columns=[
                "symbol_id",
                "symbol",
                "market",
                "industry",
                "sector",
                "sec_type",
                "native",
            ],
        )
        assert_frame_equal(result, expect)

    def test_empty(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(
            symbol_list=["TCCC", "PTTGC"], market=fld.MARKET_MAI
        )

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert_index_equal(
            result.columns,
            pd.Index(
                [
                    "symbol_id",
                    "symbol",
                    "market",
                    "industry",
                    "sector",
                    "sec_type",
                    "native",
                ]
            ),
        )

        for i in result.columns:
            assert pd.notna(result[i]).all(), f"{i} is null"

        assert_series_equal(result["symbol"], result["symbol"].str.upper())

        assert result["market"].isin([fld.MARKET_SET, fld.MARKET_MAI]).all()
        assert result["industry"].isin(fld.INDUSTRY_LIST).all()
        assert result["sector"].isin(fld.SECTOR_LIST).all()

        assert result["symbol_id"].is_unique
        assert result["symbol"].is_unique

        return result


class TestGetCompanyInfo:
    def test_all(self, sdr: SETDataReader):
        result = sdr.get_company_info()

        # Check
        self._check(result)

        assert not result.empty

    def test_one(self, sdr: SETDataReader):
        result = sdr.get_company_info(["PTT"])

        # Check
        self._check(result)

        expect = pd.DataFrame(
            [
                [
                    646,
                    "PTT",
                    "บริษัท ปตท. จำกัด (มหาชน)",
                    "PTT PUBLIC COMPANY LIMITED",
                    "555 ถนนวิภาวดีรังสิต แขวงจตุจักร เขตจตุจักร กทม.",
                    "555 VIBHAVADI RANGSIT ROAD, CHATUCHAK Bangkok",
                    "10900",
                    "0-2537-2000",
                    "0-2537-3498-9",
                    None,
                    "http://www.pttplc.com",
                    "1/10/2001",
                    "ไม่ต่ำกว่าร้อยละ 25 ของกำไรสุทธิที่เหลือหลังหักเงินสำรองต่างๆ ทุกประเภทที่กฎหมายและบริษัทได้กำหนดไว้ (โดยมีเงื่อนไขเพิ่มเติม)",
                    "Not less than 25% of net income after deduction of all specified reserves (with additional conditions)",
                ]
            ],
            columns=[
                "company_id",
                "symbol",
                "company_name_t",
                "company_name_e",
                "address_t",
                "address_e",
                "zip",
                "tel",
                "fax",
                "email",
                "url",
                "establish",
                "dvd_policy_t",
                "dvd_policy_e",
            ],
        )
        assert_frame_equal(result, expect)

    def test_empty(self, sdr: SETDataReader):
        result = sdr.get_company_info(["ABCD"])

        # Check
        self._check(result)
        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert_index_equal(
            result.columns,
            pd.Index(
                [
                    "company_id",
                    "symbol",
                    "company_name_t",
                    "company_name_e",
                    "address_t",
                    "address_e",
                    "zip",
                    "tel",
                    "fax",
                    "email",
                    "url",
                    "establish",
                    "dvd_policy_t",
                    "dvd_policy_e",
                ]
            ),
        )

        assert pd.notna(result["company_id"]).all()
        assert pd.notna(result["symbol"]).all()

        assert result["symbol"].is_unique

        return result


class TestGetChangeName:
    def test_all(self, sdr: SETDataReader):
        result = sdr.get_change_name()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["TTB"], ["ttb"]])
    @pytest.mark.parametrize("start_date", [date(2021, 5, 12), None])
    @pytest.mark.parametrize("end_date", [date(2021, 5, 12), None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
    ):
        result = sdr.get_change_name(
            symbol_list=symbol_list, start_date=start_date, end_date=end_date
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [[181, "TTB", pd.Timestamp("2021-05-12"), "TMB", "TTB"]],
                columns=[
                    "symbol_id",
                    "symbol",
                    "effect_date",
                    "symbol_old",
                    "symbol_new",
                ],
            ),
        )

    def test_empty(self, sdr: SETDataReader):
        result = sdr.get_change_name(["ABCD"])

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert_index_equal(
            result.columns,
            pd.Index(
                [
                    "symbol_id",
                    "symbol",
                    "effect_date",
                    "symbol_old",
                    "symbol_new",
                ]
            ),
        )

        for i in result.columns:
            assert pd.notna(result[i]).all(), f"{i} is null"

        assert (result["symbol_old"] != result["symbol_new"]).all()

        assert is_df_unique(result[["symbol_id", "effect_date"]])

        return result


class TestGetDividend:
    def test_all(self, sdr: SETDataReader):
        result = sdr.get_dividend()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["PTC"], ["ptc"]])
    @pytest.mark.parametrize("start_date", [date(2022, 3, 15), None])
    @pytest.mark.parametrize("end_date", [date(2022, 3, 15), None])
    @pytest.mark.parametrize("ca_type_list", ["CD", None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
        ca_type_list: Optional[List[str]],
    ):
        result = sdr.get_dividend(
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            ca_type_list=ca_type_list,
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [
                    [
                        "PTC",
                        pd.Timestamp("2022-03-15"),
                        pd.Timestamp("2022-05-24"),
                        "CD",
                        0.1,
                    ]
                ],
                columns=["symbol", "ex_date", "pay_date", "ca_type", "dps"],
            ),
        )

    def test_cancel(self, sdr: SETDataReader):
        result = sdr.get_dividend(["CRC"])

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [
                    [
                        "CRC",
                        pd.Timestamp("2021-04-29"),
                        pd.Timestamp("2021-05-21"),
                        "CD",
                        0.40,
                    ],
                    [
                        "CRC",
                        pd.Timestamp("2022-05-09"),
                        pd.Timestamp("2022-05-27"),
                        "CD",
                        0.30,
                    ],
                ],
                columns=[
                    "symbol",
                    "ex_date",
                    "pay_date",
                    "ca_type",
                    "dps",
                ],
            ),
        )

    def test_empty(self, sdr: SETDataReader):
        result = sdr.get_dividend(["ABCD"])

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert_index_equal(
            result.columns,
            pd.Index(
                [
                    "symbol",
                    "ex_date",
                    "pay_date",
                    "ca_type",
                    "dps",
                ]
            ),
        )

        for i in result.columns:
            assert pd.notna(result[i]).all(), f"{i} is null"

        assert (result["pay_date"] >= result["ex_date"]).all()
        assert result["ca_type"].isin(["CD", "SD"]).all()
        assert (result["dps"] > 0).all()

        return result


@pytest.mark.parametrize(
    ("df", "expected"),
    [
        (pd.DataFrame(), True),
        (pd.DataFrame([1, 1]), False),
        (pd.DataFrame([1, 2]), True),
        (pd.DataFrame([[1, 2], [1, 2]]), False),
        (pd.DataFrame([[1, 1], [1, 2]]), True),
    ],
)
def test_is_df_unique(df: pd.DataFrame, expected: bool):
    assert is_df_unique(df) == expected


def is_df_unique(df):
    return (df.groupby([i for i in df.columns]).size() == 1).all()
