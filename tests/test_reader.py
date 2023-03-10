from datetime import datetime
from typing import List, Optional

import pandas as pd
import pytest
from pandas._testing import assert_frame_equal, assert_index_equal, assert_series_equal

import ezyquant.fields as fld
from ezyquant import SETDataReader
from ezyquant import validators as vld
from ezyquant.errors import InputError
from tests import utils

INDEX_LIST = fld.INDEX_LIST + [fld.MARKET_SET, fld.MARKET_MAI]


def test_last_table_update(sdr: SETDataReader):
    # Test
    result = sdr.last_table_update("DAILY_STOCK_TRADE")

    assert isinstance(result, str)


def test_last_update(sdr: SETDataReader):
    # Test
    result = sdr.last_update()

    assert isinstance(result, str)


class TestGetTradingDates:
    """source: https://www.bot.or.th/Thai/FinancialInstitutions/FIholiday/Pages/2022.aspx"""

    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_trading_dates()

        # Check
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], str)

    @pytest.mark.parametrize(
        ("start_date", "expect_first_date"),
        [
            ("2022-01-01", "2022-01-04"),
            ("2022-01-04", "2022-01-04"),
            ("2022-01-05", "2022-01-05"),
        ],
    )
    def test_start_date(
        self, sdr: SETDataReader, start_date: str, expect_first_date: str
    ):
        # Test
        result = sdr.get_trading_dates(start_date=start_date)

        # Check
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], str)
        assert result[0] == expect_first_date

    @pytest.mark.parametrize(
        ("end_date", "expect_last_date"),
        [
            ("2022-01-06", "2022-01-06"),
            ("2022-01-07", "2022-01-07"),
            ("2022-01-08", "2022-01-07"),
            ("2022-01-09", "2022-01-07"),
            ("2022-12-12", "2022-12-09"),
        ],
    )
    def test_end_date(self, sdr: SETDataReader, end_date: str, expect_last_date: str):
        # Test
        result = sdr.get_trading_dates(end_date=end_date)

        # Check
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], str)
        assert result[-1] == expect_last_date

    @pytest.mark.parametrize(
        ("start_date", "end_date", "expect_dates"),
        [
            ("2022-01-01", "2022-01-04", ["2022-01-04"]),
            ("2022-01-03", "2022-01-04", ["2022-01-04"]),
            ("2022-01-04", "2022-01-04", ["2022-01-04"]),
            ("2022-01-01", "2022-01-05", ["2022-01-04", "2022-01-05"]),
            ("2022-01-03", "2022-01-05", ["2022-01-04", "2022-01-05"]),
            ("2022-01-04", "2022-01-05", ["2022-01-04", "2022-01-05"]),
        ],
    )
    def test_start_end_date(
        self,
        sdr: SETDataReader,
        start_date: str,
        end_date: str,
        expect_dates: List[str],
    ):
        # Test
        result = sdr.get_trading_dates(start_date=start_date, end_date=end_date)

        # Check
        assert result == expect_dates

    @pytest.mark.parametrize(
        ("start_date", "end_date"),
        [
            ("2022-01-01", "2022-01-01"),
            ("2022-01-03", "2022-01-03"),
        ],
    )
    def test_empty(self, sdr: SETDataReader, start_date: str, end_date: str):
        # Test
        result = sdr.get_trading_dates(start_date=start_date, end_date=end_date)

        # Check
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.parametrize(("start_date", "end_date"), [("2022-01-02", "2022-01-01")])
    def test_invalid_start_after_end(
        self, sdr: SETDataReader, start_date: str, end_date: str
    ):
        # Test
        with pytest.raises(InputError):
            sdr.get_trading_dates(start_date=start_date, end_date=end_date)


@pytest.mark.parametrize(
    ("check_date", "expected"),
    [
        ("2022-01-01", False),
        ("2022-01-02", False),
        ("2022-01-03", False),
        ("2022-01-04", True),
        ("2022-01-05", True),
        ("2022-01-06", True),
        ("2022-01-07", True),
        ("2022-01-08", False),
        ("2022-01-09", False),
        ("2022-01-10", True),
        ("2022-12-09", True),
        ("2022-12-12", False),
    ],
)
def test_is_trading_date(sdr: SETDataReader, check_date: str, expected: bool):
    # Test
    result = sdr.is_trading_date(check_date)

    assert result == expected


def test_is_today_trading_date(sdr: SETDataReader):
    # Test
    result = sdr.is_today_trading_date()

    assert isinstance(result, bool)


class TestGetSymbolInfo:
    def test_get_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_symbol_info()

        # Check
        self._check(result)

        assert not result.empty

    def test_market(self, sdr: SETDataReader):
        # Test
        result = sdr.get_symbol_info(market=fld.MARKET_MAI)

        # Check
        self._check(result)

        assert (result["market"] == fld.MARKET_MAI).all()
        assert "AU" in result["symbol"].tolist()

    def test_industry(self, sdr: SETDataReader):
        # Test
        result = sdr.get_symbol_info(industry=fld.INDUSTRY_AGRO)

        # Check
        self._check(result)

        assert (result["industry"] == fld.INDUSTRY_AGRO).all()
        assert (
            result["sector"]
            .isin([fld.SECTOR_AGRI, fld.SECTOR_FOOD, fld.INDUSTRY_AGRO])
            .all()
        )
        assert "STA" in result["symbol"].tolist()

    def test_sector(self, sdr: SETDataReader):
        # Test
        result = sdr.get_symbol_info(sector=fld.SECTOR_AGRI)

        # Check
        self._check(result)

        # MAI sector name same as industry name
        assert (result["market"] == fld.MARKET_SET).all()
        assert (result["industry"] == fld.INDUSTRY_AGRO).all()
        assert (result["sector"] == fld.SECTOR_AGRI).all()
        assert "STA" in result["symbol"].tolist()

    @pytest.mark.parametrize(
        ("start", "expected"),
        [("2022-04-26", ["SCBB", "SCB"]), ("2022-04-27", ["SCB"])],
    )
    def test_start_has_price_date(
        self, sdr: SETDataReader, start: str, expected: List[str]
    ):
        """
        SCBB last trade date is 2022-04-26
        SCB first trade date is 2022-04-27
        """

        # Test
        result = sdr.get_symbol_info(
            symbol_list=["SCBB", "SCB"], start_has_price_date=start
        )

        # Check
        self._check(result)

        assert result["symbol"].tolist() == expected

    @pytest.mark.parametrize(
        ("end", "expected"),
        [("2022-04-26", ["SCBB"]), ("2022-04-27", ["SCBB", "SCB"])],
    )
    def test_end_has_price_date(
        self, sdr: SETDataReader, end: str, expected: List[str]
    ):
        """
        SCBB last trade date is 2022-04-26
        SCB first trade date is 2022-04-27
        """

        # Test
        result = sdr.get_symbol_info(
            symbol_list=["SCBB", "SCB"], end_has_price_date=end
        )

        # Check
        self._check(result)

        assert result["symbol"].tolist() == expected

    @pytest.mark.parametrize("symbol_list", [["TCCC", "PTTGC"]])
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
        # Test
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

    @pytest.mark.parametrize("symbol_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, symbol_list: List[str]):
        # Test
        result = sdr.get_symbol_info(symbol_list)

        # Check
        self._check(result)

        assert result.empty

    @pytest.mark.parametrize(
        "symbol_list", [["AOT", "AOT"], ["AOT", "AOT", "AOT"], ["aot", "AOT"]]
    )
    def test_duplicate_symbol(self, sdr: SETDataReader, symbol_list: List[str]):
        with pytest.raises(InputError):
            sdr.get_symbol_info(symbol_list)

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

        assert pd.notna(result["symbol_id"]).all()
        assert pd.notna(result["symbol"]).all()
        assert pd.notna(result["market"]).all()
        # assert pd.notna(result["industry"]).all()
        # assert pd.notna(result["sector"]).all()
        assert pd.notna(result["sec_type"]).all()
        # assert pd.notna(result["native"]).all()

        assert_series_equal(result["symbol"], result["symbol"].str.upper())

        # assert result["market"].isin([fld.MARKET_SET, fld.MARKET_MAI]).all()

        assert result["symbol_id"].is_unique
        assert result["symbol"].is_unique

        return result


class TestGetCompanyInfo:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_company_info()

        # Check
        self._check(result)

        assert not result.empty

    def test_one(self, sdr: SETDataReader):
        # Test
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

    @pytest.mark.parametrize("symbol_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, symbol_list: List[str]):
        # Test
        result = sdr.get_company_info(symbol_list)

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
        # Test
        result = sdr.get_change_name()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["TTB"], ["ttb"]])
    @pytest.mark.parametrize("start_date", ["2021-05-12", None])
    @pytest.mark.parametrize("end_date", ["2021-05-12", None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        # Test
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

    @pytest.mark.parametrize("symbol_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, symbol_list: List[str]):
        # Test
        result = sdr.get_change_name(symbol_list)

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

        assert utils.is_df_unique(result[["symbol_id", "effect_date"]])

        return result


class TestGetDividend:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_dividend()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["PTC"], ["ptc"]])
    @pytest.mark.parametrize("start_date", ["2022-03-15", None])
    @pytest.mark.parametrize("end_date", ["2022-03-15"])
    @pytest.mark.parametrize("ca_type_list", [["CD"], None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        ca_type_list: Optional[List[str]],
    ):
        # Test
        result = sdr.get_dividend(
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            ca_type_list=ca_type_list,
            adjusted_list=[],
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

    def test_adjust(self, sdr: SETDataReader):
        """source: https://www.tradingview.com/chart/?symbol=SET:COM7"""
        # Test
        result = sdr.get_dividend(
            ["COM7"], ca_type_list=["CD"], start_date="2020-01-01"
        )

        # Check
        self._check(result)

        # COM7 split 2:1 2022-03-11
        assert_frame_equal(
            result,
            pd.DataFrame(
                [
                    [
                        "COM7",
                        pd.Timestamp("2020-05-08"),
                        pd.Timestamp("2020-05-26"),
                        "CD",
                        0.4,
                    ],
                    [
                        "COM7",
                        pd.Timestamp("2021-04-29"),
                        None,  # D_BEG_PAID is null in database
                        "CD",
                        0.5,
                    ],
                    [
                        "COM7",
                        pd.Timestamp("2022-03-11"),
                        pd.Timestamp("2022-05-06"),
                        "CD",
                        1.0,
                    ],
                    [
                        "COM7",
                        pd.Timestamp("2023-03-08"),
                        None,  # D_BEG_PAID is null in database
                        "CD",
                        0.75,
                    ],
                ],
                columns=["symbol", "ex_date", "pay_date", "ca_type", "dps"],
            ),
        )

    def test_cancel(self, sdr: SETDataReader):
        # Test
        result = sdr.get_dividend(["CRC"], adjusted_list=[])

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
                    [
                        "CRC",
                        pd.Timestamp("2023-05-08"),
                        pd.Timestamp("2023-05-26"),
                        "CD",
                        0.48,
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

    @pytest.mark.parametrize("symbol_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, symbol_list: List[str]):
        # Test
        result = sdr.get_dividend(symbol_list)

        # Check
        self._check(result)

        assert result.empty

    @pytest.mark.parametrize(
        "symbol_list", [["AOT", "AOT"], ["AOT", "AOT", "AOT"], ["aot", "AOT"]]
    )
    def test_duplicate_symbol(self, sdr: SETDataReader, symbol_list: List[str]):
        with pytest.raises(InputError):
            sdr.get_dividend(symbol_list)

    @pytest.mark.parametrize(
        "ca_type_list", [["CD", "CD"], ["CD", "CD", "CD"], ["cd", "CD"]]
    )
    def test_duplicate_ca_type(self, sdr: SETDataReader, ca_type_list: List[str]):
        with pytest.raises(InputError):
            sdr.get_dividend(ca_type_list=ca_type_list)

    @pytest.mark.parametrize(
        "adjusted_list", [["SD", "SD"], ["SD", "SD", "SD"], ["sd", "SD"]]
    )
    def test_duplicate_adjusted(self, sdr: SETDataReader, adjusted_list: List[str]):
        with pytest.raises(InputError):
            sdr.get_dividend(adjusted_list=adjusted_list)

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

        # ex_date and pay_date can null in database
        assert pd.notna(result["symbol"]).all()
        assert pd.notna(result["ca_type"]).all()
        assert pd.notna(result["dps"]).all()

        assert result["ca_type"].isin(["CD", "SD"]).all()
        assert (result["dps"] > 0).all()

        return result


class TestGetDelisted:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_delisted()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["ROBINS"], ["robins"]])
    @pytest.mark.parametrize("start_date", ["2020-02-20", None])
    @pytest.mark.parametrize("end_date", ["2020-02-20", None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        # Test
        result = sdr.get_delisted(
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [["ROBINS", pd.Timestamp("2020-02-20")]],
                columns=["symbol", "delisted_date"],
            ),
        )

    @pytest.mark.parametrize("symbol_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, symbol_list: Optional[List[str]]):
        # Test
        result = sdr.get_delisted(symbol_list)

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert_index_equal(
            result.columns,
            pd.Index(
                ["symbol", "delisted_date"],
            ),
        )

        for i in result.columns:
            assert pd.notna(result[i]).all(), f"{i} is null"

        assert result["symbol"].is_unique

        return result


class TestGetSignPosting:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_sign_posting()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["TAPAC"], ["tapac"]])
    @pytest.mark.parametrize("start_date", ["2022-01-05", None])
    @pytest.mark.parametrize("end_date", ["2022-01-05"])
    @pytest.mark.parametrize("sign_list", [["SP"], ["sp"], None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        sign_list: Optional[List[str]],
    ):
        # Test
        result = sdr.get_sign_posting(
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            sign_list=sign_list,
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [
                    [
                        "TAPAC",
                        pd.Timestamp("2022-01-05"),
                        pd.Timestamp("2022-01-06"),
                        "SP",
                    ]
                ],
                columns=["symbol", "hold_date", "release_date", "sign"],
            ),
        )

    @pytest.mark.parametrize("symbol_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, symbol_list: Optional[List[str]]):
        # Test
        result = sdr.get_sign_posting(symbol_list=symbol_list)

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert_index_equal(
            result.columns,
            pd.Index(["symbol", "hold_date", "release_date", "sign"]),
        )

        assert pd.notna(result["symbol"]).all(), f"symbol is null"
        assert pd.notna(result["hold_date"]).all(), f"hold_date is null"
        assert pd.notna(result["sign"]).all(), f"sign is null"

        assert result["sign"].isin(["C", "CM", "DS", "H", "NC", "NP", "SP", "ST"]).all()

        return result


class TestGetSymbolsByIndex:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_symbols_by_index()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        "index",
        [
            fld.INDEX_SETWB,
            fld.INDEX_SETTHSI,
            fld.INDEX_SETCLMV,
            fld.INDEX_SETHD,
            fld.INDEX_SSET,
            fld.INDEX_SET100,
            fld.INDEX_SET50,
        ],
    )
    def test_index(self, sdr: SETDataReader, index: str):
        # Test
        result = sdr.get_symbols_by_index([index])

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("index_list", [["SET50"], ["set50"]])
    @pytest.mark.parametrize("start_date", ["2012-01-03", "2012-01-04"])
    @pytest.mark.parametrize("end_date", ["2012-01-04", "2012-01-05"])
    def test_filter(
        self,
        sdr: SETDataReader,
        index_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        # Test
        result = sdr.get_symbols_by_index(
            index_list=index_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                {
                    "as_of_date": pd.Timestamp("2012-01-04"),
                    "index": "SET50",
                    "symbol": [
                        "STA",
                        "CPF",
                        "MINT",
                        "TU",
                        "BAY",
                        "BBL",
                        "KBANK",
                        "KTB",
                        "SCBB",
                        "TCAP",
                        "TISCO",
                        "TTB",
                        "BLA",
                        "IVL",
                        "PTTGC",
                        "TPC",
                        "DCC",
                        "SCC",
                        "SCCC",
                        "TPIPL",
                        "CPN",
                        "LH",
                        "PS",
                        "SPALI",
                        "BANPU",
                        "BCP",
                        "EGCO",
                        "ESSO",
                        "GLOW",
                        "IRPC",
                        "PTT",
                        "PTTEP",
                        "RATCH",
                        "TOP",
                        "BIGC",
                        "BJC",
                        "CPALL",
                        "HMPRO",
                        "MAKRO",
                        "ROBINS",
                        "BEC",
                        "BDMS",
                        "BH",
                        "AOT",
                        "BTS",
                        "THAI",
                        "ADVANC",
                        "DTAC",
                        "TRUEE",
                        "DELTA",
                    ],
                    "seq": [i for i in range(1, 51)],
                },
                columns=["as_of_date", "index", "symbol", "seq"],
            ),
        )

    @pytest.mark.parametrize("index_list", [["sSET"], ["SSET"], ["sset"]])
    @pytest.mark.parametrize("start_date", ["2022-01-03", "2022-01-04"])
    @pytest.mark.parametrize("end_date", ["2022-01-04", "2022-01-05"])
    def test_sset(
        self,
        sdr: SETDataReader,
        index_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        """sSET is not upper"""
        # Test
        result = sdr.get_symbols_by_index(
            index_list=index_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert_series_equal(
            result["seq"], pd.Series([i for i in range(1, 139)], name="seq")
        )
        assert (result["as_of_date"] == pd.Timestamp("2022-01-04")).all()
        assert (result["index"] == fld.INDEX_SSET).all()

    @pytest.mark.parametrize("index_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, index_list: Optional[List[str]]):
        # Test
        result = sdr.get_symbols_by_index(index_list=index_list)

        # Check
        self._check(result)

        assert result.empty

    @pytest.mark.parametrize(
        "index_list",
        [["SET50", "SET50"], ["SET50", "SET50", "SET50"], ["SET50", "set50"]],
    )
    def test_duplicate_index(self, sdr: SETDataReader, index_list: List[str]):
        with pytest.raises(ValueError):
            sdr.get_symbols_by_index(index_list)

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert_index_equal(
            result.columns,
            pd.Index(["as_of_date", "index", "symbol", "seq"]),
        )

        for i in result.columns:
            assert pd.notna(result[i]).all(), f"{i} is null"

        assert result["index"].isin(INDEX_LIST).all()
        assert (result["symbol"] == result["symbol"].str.upper()).all()

        return result


class TestGetAdjustFactor:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_adjust_factor()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["COM7"], ["com7"]])
    @pytest.mark.parametrize("start_date", ["2022-03-11", None])
    @pytest.mark.parametrize("end_date", ["2022-03-11", None])
    @pytest.mark.parametrize("ca_type_list", [["SD"], ["sd"], None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        ca_type_list: Optional[List[str]],
    ):
        # Test
        result = sdr.get_adjust_factor(
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
                [["COM7", pd.Timestamp("2022-03-11"), "SD", 0.5]],
                columns=["symbol", "effect_date", "ca_type", "adjust_factor"],
            ),
        )

    @pytest.mark.parametrize("symbol_list", [["ABCD"], []])
    def test_empty(self, sdr: SETDataReader, symbol_list: Optional[List[str]]):
        # Test
        result = sdr.get_adjust_factor(symbol_list)

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
                    "effect_date",
                    "ca_type",
                    "adjust_factor",
                ]
            ),
        )

        for i in result.columns:
            assert pd.notna(result[i]).all(), f"{i} is null"

        assert utils.is_df_unique(result[["symbol", "effect_date"]])
        assert result["ca_type"].isin(["  ", "CR", "PC", "RC", "SD", "XR"]).all()
        assert (result["adjust_factor"] > 0).all()

        return result


class TestGetDataSymbolDaily:
    """source: https://www.tradingview.com/chart/?symbol=SET:COM7"""

    _check = staticmethod(vld.check_df_symbol_daily)

    @pytest.mark.parametrize(
        "field",
        [fld.D_AVERAGE, fld.D_VALUE, fld.D_TURNOVER, fld.D_12M_DVD_YIELD, "has_trade"],
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["COM7"]
        start_date = "2022-03-10"
        end_date = "2022-03-10"

        # Test
        result = sdr.get_data_symbol_daily(
            field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ("field", "symbol", "start_date", "end_date", "is_adjust", "expected"),
        [
            (
                # adjust close 1 time
                "close",
                "COM7",
                "2022-03-10",
                "2022-03-14",
                True,
                pd.DataFrame(
                    {"COM7": [41.75, 42.25, 40.75]},
                    index=[
                        pd.Timestamp("2022-03-10"),
                        pd.Timestamp("2022-03-11"),
                        pd.Timestamp("2022-03-14"),
                    ],
                ),
            ),
            (
                # adjust close 2 time (first)
                "close",
                "MALEE",
                "2013-04-17",
                "2013-04-19",
                True,
                pd.DataFrame(
                    {"MALEE": [36.75, 37.125, 36.875]},
                    index=[
                        pd.Timestamp("2013-04-17"),
                        pd.Timestamp("2013-04-18"),
                        pd.Timestamp("2013-04-19"),
                    ],
                ),
            ),
            (
                # adjust close 2 time (last)
                "close",
                "MALEE",
                "2017-05-15",
                "2017-05-17",
                True,
                pd.DataFrame(
                    {"MALEE": [50.75, 53.25, 54.0]},
                    index=[
                        pd.Timestamp("2017-05-15"),
                        pd.Timestamp("2017-05-16"),
                        pd.Timestamp("2017-05-17"),
                    ],
                ),
            ),
            (
                # not adjust close
                "close",
                "COM7",
                "2022-03-10",
                "2022-03-14",
                False,
                pd.DataFrame(
                    {"COM7": [83.50, 42.25, 40.75]},
                    index=[
                        pd.Timestamp("2022-03-10"),
                        pd.Timestamp("2022-03-11"),
                        pd.Timestamp("2022-03-14"),
                    ],
                ),
            ),
            (
                # adjust volume 1 time
                "volume",
                "COM7",
                "2022-03-10",
                "2022-03-14",
                True,
                pd.DataFrame(
                    {"COM7": [41811200.0, 35821300.0, 23099500.0]},
                    index=[
                        pd.Timestamp("2022-03-10"),
                        pd.Timestamp("2022-03-11"),
                        pd.Timestamp("2022-03-14"),
                    ],
                ),
            ),
            (
                # not adjust volume
                "volume",
                "COM7",
                "2022-03-10",
                "2022-03-14",
                False,
                pd.DataFrame(
                    {"COM7": [20905600.0, 35821300.0, 23099500.0]},
                    index=[
                        pd.Timestamp("2022-03-10"),
                        pd.Timestamp("2022-03-11"),
                        pd.Timestamp("2022-03-14"),
                    ],
                ),
            ),
            # THAI no trade after 2021-05-18, close at 2021-05-17 is 3.32
            (
                "has_trade",
                "THAI",
                "2021-05-17",
                "2021-05-18",
                True,
                pd.DataFrame(
                    {"THAI": [1.0, 0.0]},
                    index=[
                        pd.Timestamp("2021-05-17"),
                        pd.Timestamp("2021-05-18"),
                    ],
                ),
            ),
        ],
    )
    def test_with_expect(
        self,
        sdr: SETDataReader,
        field: str,
        symbol: str,
        start_date: str,
        end_date: str,
        is_adjust: bool,
        expected: pd.DataFrame,
    ):
        # Test
        if is_adjust:
            result = sdr.get_data_symbol_daily(
                field=field,
                symbol_list=[symbol],
                start_date=start_date,
                end_date=end_date,
            )
        else:
            result = sdr.get_data_symbol_daily(
                field=field,
                symbol_list=[symbol],
                start_date=start_date,
                end_date=end_date,
                adjusted_list=[],
            )

        # Check
        self._check(result)

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        "field",
        [fld.D_AVERAGE, fld.D_VALUE, fld.D_TURNOVER, fld.D_12M_DVD_YIELD, "has_trade"],
    )
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_daily(field, symbol_list=[])

        # Check
        self._check(result)

        assert result.empty

    @pytest.mark.parametrize(
        ("symbol_list", "expect_columns"),
        [
            ([], []),
            (["COM7"], ["COM7"]),
            (["com7"], ["COM7"]),
            (["Truee"], ["TRUEE"]),
            (["COM7", "MALEE"], ["COM7", "MALEE"]),
            (["MALEE", "COM7"], ["MALEE", "COM7"]),
            # INVALID
            (["INVALID"], []),
            (["INVALID", "COM7", "MALEE"], ["COM7", "MALEE"]),
            (["COM7", "INVALID", "MALEE"], ["COM7", "MALEE"]),
            (["COM7", "MALEE", "INVALID"], ["COM7", "MALEE"]),
            # New Symbol
            (["OR"], []),
            (["OR", "COM7", "MALEE"], ["COM7", "MALEE"]),
            (["COM7", "OR", "MALEE"], ["COM7", "MALEE"]),
            (["COM7", "MALEE", "OR"], ["COM7", "MALEE"]),
        ],
    )
    def test_symbol_column(
        self, sdr: SETDataReader, symbol_list: List[str], expect_columns: List[str]
    ):
        # Test
        result = sdr.get_data_symbol_daily(
            "close",
            symbol_list=symbol_list,
            start_date="2017-05-15",
            end_date="2017-05-17",
        )

        # Check
        self._check(result)
        assert result.columns.to_list() == expect_columns

    @pytest.mark.parametrize(
        "symbol_list", [["AOT", "AOT"], ["AOT", "AOT", "AOT"], ["aot", "AOT"]]
    )
    def test_duplicate_symbol(self, sdr: SETDataReader, symbol_list: List[str]):
        with pytest.raises(InputError):
            sdr.get_data_symbol_daily("close", symbol_list)


class TestGetDataSymbolQuarterly:
    _check = staticmethod(vld.check_df_symbol_daily)

    @pytest.mark.parametrize(
        "field",
        [
            fld.Q_ROE,  # Financial Ratio
            fld.Q_TOTAL_ASSET,  # Balance Sheet
            fld.Q_EBITDA,  # Income Statement
            fld.Q_NET_FINANCING,  # Cashflow Statement
        ],
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = "2021-03-01"
        end_date = "2021-11-12"

        # Test
        result = sdr.get_data_symbol_quarterly(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected_list"],
        [
            # Financial Ratio
            (
                fld.Q_ROA,
                [
                    1.6829434061191892,
                    1.4697230952727913,
                    1.3504085549573543,
                    1.3672515432689933,
                ],
            ),
            (fld.Q_GROSS_PROFIT_MARGIN, [-float("nan")] * 4),
            # Balance Sheet
            (
                fld.Q_CASH,
                [233127550000.0, 231865550000.0, 185736074000.0, 168533280000.0],
            ),
            # Income Statement
            (
                fld.Q_TOTAL_REVENUE,
                [22019850000.0, 21069316000.0, 19970220000.0, 19727090000.0],
            ),
            (fld.Q_COS, [5073409000.0, 4767026000.0, 4651329000.0, 4499566000.0]),
            # Cashflow Statement
            (
                fld.Q_NET_CASH_FLOW,
                [3042325000.0, -3732755000.0, -2142246000.0, -1378998000.0],
            ),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = "2021-03-01"
        end_date = "2021-11-12"

        # Test
        result = sdr.get_data_symbol_quarterly(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        expected = pd.DataFrame(
            {symbol: expected_list},
            index=pd.DatetimeIndex(
                ["2021-03-01", "2021-05-13", "2021-08-27", "2021-11-12"]
            ),
        )

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        "field",
        [
            fld.Q_ROE,  # Financial Ratio
            fld.Q_TOTAL_ASSET,  # Balance Sheet
            fld.Q_EBITDA,  # Income Statement
            fld.Q_NET_FINANCING,  # Cashflow Statement
        ],
    )
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_quarterly(field=field, symbol_list=[])

        # Check
        self._check(result)
        assert result.empty


class TestGetDataSymbolYearly:
    _check = staticmethod(vld.check_df_symbol_daily)

    @pytest.mark.parametrize(
        "field",
        [
            fld.Q_ROE,  # Financial Ratio
            fld.Q_TOTAL_ASSET,  # Balance Sheet
            fld.Q_EBITDA,  # Income Statement
            fld.Q_NET_FINANCING,  # Cashflow Statement
        ],
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = "2021-03-01"
        end_date = "2021-11-12"

        # Test
        result = sdr.get_data_symbol_yearly(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected_list"],
        [
            # Financial Ratio
            (fld.Q_ROA, [1.6829434061191892]),
            (fld.Q_GROSS_PROFIT_MARGIN, [-float("nan")]),
            # Balance Sheet
            (fld.Q_CASH, [233127550000.0]),
            # Income Statement
            (fld.Q_TOTAL_REVENUE, [89885610000.0]),
            (fld.Q_COS, [23861086000.0]),
            # Cashflow Statement
            (fld.Q_NET_CASH_FLOW, [-1889251000.0]),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = "2021-03-01"
        end_date = "2021-03-01"

        # Test
        result = sdr.get_data_symbol_yearly(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        expected = pd.DataFrame(
            {symbol: expected_list}, index=pd.DatetimeIndex(["2021-03-01"])
        )

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        "field",
        [
            fld.Q_ROE,  # Financial Ratio
            fld.Q_TOTAL_ASSET,  # Balance Sheet
            fld.Q_EBITDA,  # Income Statement
            fld.Q_NET_FINANCING,  # Cashflow Statement
        ],
    )
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_yearly(field=field, symbol_list=[])

        # Check
        self._check(result)

        assert result.empty


class TestGetDataSymbolTtm:
    _check = staticmethod(vld.check_df_symbol_daily)

    @pytest.mark.parametrize(
        "field",
        [
            # fld.Q_TOTAL_ASSET,  # Balance Sheet
            fld.Q_EBITDA,  # Income Statement
            fld.Q_NET_FINANCING,  # Cashflow Statement
        ],
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = "2021-03-01"
        end_date = "2021-11-12"

        # Test
        result = sdr.get_data_symbol_ttm(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected_list"],
        [
            # Income Statement
            (
                fld.Q_TOTAL_REVENUE,
                [89885610000.0, 86495188000.0, 84669125000.0, 82786475000.0],
            ),
            (fld.Q_COS, [23861086000.0, 21442714000.0, 19895590000.0, 18991330000.0]),
            # Cashflow Statement
            (
                fld.Q_NET_CASH_FLOW,
                [-1889251000.0, -2540135000.0, -1985902000.0, -4211674000.0],
            ),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = "2021-03-01"
        end_date = "2021-11-12"

        # Test
        result = sdr.get_data_symbol_ttm(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        expected = pd.DataFrame(
            {symbol: expected_list},
            index=pd.DatetimeIndex(
                ["2021-03-01", "2021-05-13", "2021-08-27", "2021-11-12"]
            ),
        )

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize("field", [fld.Q_TOTAL_REVENUE, fld.Q_NET_CASH_FLOW])
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_ttm(field=field, symbol_list=[])

        # Check
        self._check(result)
        assert result.empty


class TestGetDataSymbolYtd:
    _check = staticmethod(vld.check_df_symbol_daily)

    @pytest.mark.parametrize(
        "field",
        [
            # fld.Q_ROE,  # Financial Ratio
            # fld.Q_TOTAL_ASSET,  # Balance Sheet
            fld.Q_EBITDA,  # Income Statement
            fld.Q_NET_FINANCING,  # Cashflow Statement
        ],
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = "2021-03-01"
        end_date = "2021-11-12"

        # Test
        result = sdr.get_data_symbol_ytd(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected_list"],
        [
            # Income Statement
            (
                fld.Q_TOTAL_REVENUE,
                [89885610000.0, 21069316000.0, 41039535000.0, 60766625000.0],
            ),
            (fld.Q_COS, [23861086000.0, 4767026000.0, 9418355000.0, 13917921000.0]),
            # Cashflow Statement
            (
                fld.Q_NET_CASH_FLOW,
                [-1889251000.0, -3732755000.0, -5875001000.0, -7253999000.0],
            ),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = "2021-03-01"
        end_date = "2021-11-12"

        # Test
        result = sdr.get_data_symbol_ytd(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        expected = pd.DataFrame(
            {symbol: expected_list},
            index=pd.DatetimeIndex(
                ["2021-03-01", "2021-05-13", "2021-08-27", "2021-11-12"]
            ),
        )

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize("field", [fld.Q_TOTAL_REVENUE, fld.Q_NET_CASH_FLOW])
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_ytd(field=field, symbol_list=[])

        # Check
        self._check(result)
        assert result.empty


class TestGetDataIndexDaily:
    @pytest.mark.parametrize(
        "field",
        [fld.D_INDEX_CLOSE, fld.D_INDEX_BETA],
    )
    def test_field(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_index_daily(field=field)

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["index", "field", "expected"],
        [
            (fld.MARKET_SET, fld.D_INDEX_HIGH, 1674.19),
            (fld.MARKET_SET, fld.D_INDEX_LOW, 1663.50),
            (fld.MARKET_SET, fld.D_INDEX_CLOSE, 1670.28),
            (fld.MARKET_SET, fld.D_INDEX_VOLUME, 28684980655.0),
            (fld.MARKET_SET, fld.D_INDEX_VALUE, 100014911411.57),
            (fld.MARKET_SET, fld.D_INDEX_MKT_PE, 20.96),
            (fld.MARKET_SET, fld.D_INDEX_MKT_PBV, 1.80),
            (fld.MARKET_SET, fld.D_INDEX_MKT_YIELD, 2.08),
            (fld.MARKET_SET, fld.D_INDEX_MKT_CAP, 19733996617934.5),
            (fld.INDEX_SSET, fld.D_INDEX_HIGH, 1156.83),
            (fld.INDEX_SSET, fld.D_INDEX_LOW, 1135.33),
            (fld.INDEX_SSET, fld.D_INDEX_CLOSE, 1156.83),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, index: str, field: str, expected: float
    ):
        """source: https://www.tradingview.com/chart/?symbol=SET:SET"""
        start_date = "2022-01-04"
        end_date = "2022-01-04"

        # Test
        result = sdr.get_data_index_daily(
            field=field,
            index_list=[index],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [[expected]],
                columns=[index],
                index=pd.DatetimeIndex(["2022-01-04"]),
            ),
        )

    @pytest.mark.parametrize(
        "field",
        [fld.D_INDEX_CLOSE, fld.D_INDEX_12M_DVD_YIELD],
    )
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_index_daily(field=field, index_list=[])

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.is_monotonic_increasing
        assert result.index.is_unique
        assert (result.index == result.index.normalize()).all()

        assert (result.columns.isin(INDEX_LIST)).all()

        return result


class TestGetDataSectorDaily:
    @pytest.mark.parametrize("field", [fld.D_SECTOR_BETA, fld.D_SECTOR_12M_DVD_YIELD])
    def test_field(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_sector_daily(field=field)

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected"],
        [
            (fld.D_SECTOR_OPEN, 297.55),
            (fld.D_SECTOR_HIGH, 299.36),
            (fld.D_SECTOR_LOW, 293.34),
            (fld.D_SECTOR_CLOSE, 296.13),
            (fld.D_SECTOR_VOLUME, 124063453.0),
            (fld.D_SECTOR_VALUE, 795051373.2),
            (fld.D_SECTOR_MKT_PE, 4.50),
            (fld.D_SECTOR_MKT_PBV, 1.29),
            (fld.D_SECTOR_MKT_YIELD, 4.30),
            (fld.D_SECTOR_MKT_CAP, 108032636545.26),
        ],
    )
    def test_field_with_expected(self, sdr: SETDataReader, field: str, expected: float):
        """source: https://www.tradingview.com/chart/?symbol=SET:AGRI"""
        start_date = "2022-01-04"
        end_date = "2022-01-04"

        # Test
        result = sdr.get_data_sector_daily(
            field=field,
            sector_list=[fld.SECTOR_AGRI],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [[expected]],
                columns=[fld.SECTOR_AGRI],
                index=pd.DatetimeIndex(["2022-01-04"]),
            ),
        )

    @pytest.mark.parametrize("field", [fld.D_SECTOR_BETA, fld.D_SECTOR_12M_DVD_YIELD])
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_sector_daily(field=field, sector_list=[])

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.is_monotonic_increasing
        assert result.index.is_unique
        assert (result.index == result.index.normalize()).all()

        assert (result.columns.isin(fld.SECTOR_LIST)).all()

        return result


class TestGetDataIndustryDaily:
    @pytest.mark.parametrize("field", [fld.D_SECTOR_BETA, fld.D_SECTOR_12M_DVD_YIELD])
    def test_field(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_industry_daily(field=field)

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected"],
        [
            (fld.D_INDUSTRY_OPEN, 481.75),
            (fld.D_INDUSTRY_HIGH, 487.57),
            (fld.D_INDUSTRY_LOW, 480.51),
            (fld.D_INDUSTRY_CLOSE, 485.98),
            (fld.D_INDUSTRY_VOLUME, 511827513.0),
            (fld.D_INDUSTRY_VALUE, 8342552775.82),
            (fld.D_INDUSTRY_MKT_PE, 26.45),
            (fld.D_INDUSTRY_MKT_PBV, 2.05),
            (fld.D_INDUSTRY_MKT_YIELD, 2.55),
            (fld.D_INDUSTRY_MKT_CAP, 1297058662310.79),
        ],
    )
    def test_field_with_expected(self, sdr: SETDataReader, field: str, expected: float):
        """source: https://www.tradingview.com/chart/?symbol=SET:AGRO"""
        start_date = "2022-01-04"
        end_date = "2022-01-04"

        # Test
        result = sdr.get_data_industry_daily(
            field=field,
            industry_list=[fld.INDUSTRY_AGRO],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                [[expected]],
                columns=[fld.INDUSTRY_AGRO],
                index=pd.DatetimeIndex(["2022-01-04"]),
            ),
        )

    @pytest.mark.parametrize("field", [fld.D_SECTOR_BETA, fld.D_SECTOR_12M_DVD_YIELD])
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_industry_daily(field=field, industry_list=[])

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.is_monotonic_increasing
        assert result.index.is_unique
        assert (result.index == result.index.normalize()).all()

        assert (result.columns.isin(fld.INDUSTRY_LIST)).all()

        return result


class TestGetLastAsOfDateInSecurityIndex:
    def test_none(self, sdr: SETDataReader):
        # Test
        result = sdr._get_last_as_of_date_in_security_index()

        # Check
        self._check(result)

    @pytest.mark.parametrize(
        ("current_date", "expected"),
        [
            (
                "2022-01-04",
                {
                    "SET100": "2022-01-04",
                    "SET50": "2022-01-04",
                    "SETCLMV": "2022-01-04",
                    "SETHD": "2022-01-04",
                    "SETTHSI": "2022-01-04",
                    "SETWB": "2022-01-04",
                    "sSET": "2022-01-04",
                },
            ),
            (
                "2022-04-27",
                {
                    "SET100": "2022-04-27",
                    "SET50": "2022-04-27",
                    "SETCLMV": "2022-04-27",
                    "SETHD": "2022-04-01",
                    "SETTHSI": "2022-04-27",
                    "SETWB": "2022-04-01",
                    "sSET": "2022-01-04",
                },
            ),
        ],
    )
    def test_with_expect(self, sdr: SETDataReader, current_date: str, expected: str):
        # Test
        result = sdr._get_last_as_of_date_in_security_index(current_date)

        # Check
        self._check(result)
        assert result == expected

    @staticmethod
    def _check(result):
        for k, v in result.items():
            assert isinstance(k, str)
            datetime.strptime(v, "%Y-%m-%d")


class TestSETBusinessDay:
    @pytest.mark.parametrize(
        ("inp", "n", "expected"),
        [
            (pd.Timestamp("2022-01-05"), -2, pd.Timestamp("2021-12-30")),
            (pd.Timestamp("2022-01-05"), -1, pd.Timestamp("2022-01-04")),
            (pd.Timestamp("2022-01-05"), 0, pd.Timestamp("2022-01-05")),
            (pd.Timestamp("2022-01-05"), 1, pd.Timestamp("2022-01-06")),
            (pd.Timestamp("2022-01-05"), 2, pd.Timestamp("2022-01-07")),
            (pd.Timestamp("2022-01-05"), 3, pd.Timestamp("2022-01-10")),
            (pd.Timestamp("2022-01-01"), 0, pd.Timestamp("2022-01-04")),
        ],
    )
    def test_timestamp(self, sdr: SETDataReader, inp, n: int, expected):
        # Test
        result = inp + sdr._SETBusinessDay(n)

        # Check
        assert result == expected

    @pytest.mark.parametrize(
        ("inp", "n", "expected"),
        [
            (
                pd.date_range("2022-01-01", "2022-01-07"),
                1,
                pd.DatetimeIndex(
                    [
                        "2022-01-04",
                        "2022-01-04",
                        "2022-01-04",
                        "2022-01-05",
                        "2022-01-06",
                        "2022-01-07",
                        "2022-01-10",
                    ]
                ),
            ),
        ],
    )
    def test_datetime_index(self, sdr: SETDataReader, inp, n: int, expected):
        # Test
        result = inp + sdr._SETBusinessDay(n)

        # Check
        assert_index_equal(result, expected)

    @pytest.mark.parametrize("n", [-1, 0, 1])
    def test_nat(self, sdr: SETDataReader, n: int):
        # Test
        result = pd.NaT + sdr._SETBusinessDay(n)  # type: ignore

        # Check
        assert pd.isnull(result)
