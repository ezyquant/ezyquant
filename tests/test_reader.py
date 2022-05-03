from datetime import date
from typing import List, Optional

import pandas as pd
import pytest
from pandas._testing import assert_frame_equal, assert_index_equal, assert_series_equal

import ezyquant.fields as fld
from ezyquant.errors import InputError
from ezyquant.reader import SETDataReader


class TestGetTradingDates:
    """source: https://www.bot.or.th/Thai/FinancialInstitutions/FIholiday/Pages/2022.aspx"""

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
            (date(2022, 12, 12), date(2022, 12, 9)),
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
        assert result == expect_dates

    @pytest.mark.parametrize(
        ("start_date", "end_date"),
        [
            (date(2022, 1, 1), date(2022, 1, 1)),
            (date(2022, 1, 3), date(2022, 1, 3)),
        ],
    )
    def test_empty(self, sdr: SETDataReader, start_date: date, end_date: date):
        # Test
        result = sdr.get_trading_dates(start_date=start_date, end_date=end_date)

        # Check
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.parametrize(
        ("start_date", "end_date"), [(date(2022, 1, 2), date(2022, 1, 1))]
    )
    def test_invalid_date(self, sdr: SETDataReader, start_date: date, end_date: date):
        # Test
        with pytest.raises(InputError):
            sdr.get_trading_dates(start_date=start_date, end_date=end_date)


@pytest.mark.parametrize(
    ("check_date", "expected"),
    [
        (date(2022, 1, 1), False),
        (date(2022, 1, 2), False),
        (date(2022, 1, 3), False),
        (date(2022, 1, 4), True),
        (date(2022, 1, 5), True),
        (date(2022, 1, 6), True),
        (date(2022, 1, 7), True),
        (date(2022, 1, 8), False),
        (date(2022, 1, 9), False),
        (date(2022, 1, 10), True),
        (date(2022, 12, 9), True),
        (date(2022, 12, 12), False),
    ],
)
def test_is_trading_date(sdr: SETDataReader, check_date: date, expected: bool):
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
            .isin([fld.SECTOR_AGRI, fld.SECTOR_FOOD, fld.SECTOR_AGRO])
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
                    "",
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
    @pytest.mark.parametrize("start_date", [date(2021, 5, 12), None])
    @pytest.mark.parametrize("end_date", [date(2021, 5, 12), None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
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

        assert is_df_unique(result[["symbol_id", "effect_date"]])

        return result


class TestGetDividend:
    def test_all(self, sdr: SETDataReader):
        # Test
        result = sdr.get_dividend()

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize("symbol_list", [["PTC"], ["ptc"]])
    @pytest.mark.parametrize("start_date", [date(2022, 3, 15), None])
    @pytest.mark.parametrize("end_date", [date(2022, 3, 15), None])
    @pytest.mark.parametrize("ca_type_list", [["CD"], None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
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
            ["COM7"], ca_type_list=["CD"], start_date=date(2020, 1, 1)
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
    @pytest.mark.parametrize("start_date", [date(2020, 2, 20), None])
    @pytest.mark.parametrize("end_date", [date(2020, 2, 20), None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
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
    @pytest.mark.parametrize("start_date", [date(2022, 1, 5), None])
    @pytest.mark.parametrize("end_date", [date(2022, 1, 5), None])
    @pytest.mark.parametrize("sign_list", [["SP"], ["sp"], None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
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
                [["TAPAC", pd.Timestamp("2022-01-05"), "SP"]],
                columns=["symbol", "hold_date", "sign"],
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
            pd.Index(["symbol", "hold_date", "sign"]),
        )

        for i in result.columns:
            assert pd.notna(result[i]).all(), f"{i} is null"

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
    @pytest.mark.parametrize("start_date", [date(2012, 1, 3), date(2012, 1, 4)])
    @pytest.mark.parametrize("end_date", [date(2012, 1, 4), date(2012, 1, 5)])
    def test_filter(
        self,
        sdr: SETDataReader,
        index_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
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
                        "SCB",
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
                        "TRUE",
                        "DELTA",
                    ],
                    "seq": [i for i in range(1, 51)],
                },
                columns=["as_of_date", "index", "symbol", "seq"],
            ),
        )

    @pytest.mark.parametrize("index_list", [["sSET"], ["SSET"], ["sset"]])
    @pytest.mark.parametrize("start_date", [date(2022, 1, 3), date(2022, 1, 4)])
    @pytest.mark.parametrize("end_date", [date(2022, 1, 4), date(2022, 1, 5)])
    def test_sset(
        self,
        sdr: SETDataReader,
        index_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
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

        assert result["index"].isin(fld.INDEX_LIST).all()
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
    @pytest.mark.parametrize("start_date", [date(2022, 3, 11), None])
    @pytest.mark.parametrize("end_date", [date(2022, 3, 11), None])
    @pytest.mark.parametrize("ca_type_list", [["SD"], ["sd"], None])
    def test_one(
        self,
        sdr: SETDataReader,
        symbol_list: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
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

        assert is_df_unique(result[["symbol", "effect_date"]])
        assert result["ca_type"].isin(["  ", "CR", "PC", "RC", "SD", "XR"]).all()
        assert (result["adjust_factor"] > 0).all()

        return result


class TestGetDataSymbolDaily:
    """source: https://www.tradingview.com/chart/?symbol=SET:COM7"""

    @pytest.mark.parametrize(
        "field",
        [
            getattr(fld, i)
            for i in dir(fld)
            if i.startswith("D_")
            and not i.startswith(("D_INDEX", "D_SECTOR", "D_INDUSTRY"))
        ][::5],
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["COM7"]
        start_date = date(2022, 3, 10)
        end_date = date(2022, 3, 10)

        # Test
        result = sdr.get_data_symbol_daily(
            field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        assert not result.empty

    @pytest.mark.parametrize(
        ("field", "symbol", "start_date", "end_date", "is_adjust", "expected"),
        [
            (
                # adjust close 1 time
                "close",
                "COM7",
                date(2022, 3, 10),
                date(2022, 3, 14),
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
                date(2013, 4, 17),
                date(2013, 4, 19),
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
                date(2017, 5, 15),
                date(2017, 5, 17),
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
                date(2022, 3, 10),
                date(2022, 3, 14),
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
                date(2022, 3, 10),
                date(2022, 3, 14),
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
                date(2022, 3, 10),
                date(2022, 3, 14),
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
        ],
    )
    def test_with_expect(
        self,
        sdr: SETDataReader,
        field: str,
        symbol: str,
        start_date: date,
        end_date: date,
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
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        assert_frame_equal(result, expected)

    def test_empty(self, sdr: SETDataReader):
        # Test
        result = sdr.get_data_symbol_daily("close", symbol_list=[])

        # Check
        self._check(result)

        assert result.empty

    @pytest.mark.parametrize(
        ("symbol_list", "expect_columns"),
        [
            ([], []),
            (["COM7"], ["COM7"]),
            (["com7"], ["COM7"]),
            (["True"], ["TRUE"]),
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
            start_date=date(2017, 5, 15),
            end_date=date(2017, 5, 17),
        )
        print(result)

        # Check
        self._check(result)
        assert result.columns.to_list() == expect_columns

    @pytest.mark.parametrize(
        "symbol_list", [["AOT", "AOT"], ["AOT", "AOT", "AOT"], ["aot", "AOT"]]
    )
    def test_duplicate_symbol(self, sdr: SETDataReader, symbol_list: List[str]):
        with pytest.raises(InputError):
            sdr.get_data_symbol_daily("close", symbol_list)

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)

        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.is_monotonic_increasing
        assert result.index.is_unique
        assert (result.index == result.index.normalize()).all()  # type: ignore

        assert (result.columns == result.columns.str.upper()).all()

        return result


class TestGetDataSymbolQuarterly:
    _check = staticmethod(TestGetDataSymbolDaily._check)

    @pytest.mark.skip("Some field in FINANCIAL_STAT_STD is missing")
    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("Q_")][::10]
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = date(2021, 3, 1)
        end_date = date(2021, 11, 12)

        # Test
        result = sdr.get_data_symbol_quarterly(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

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
            (fld.Q_GROSS_PROFIT_MARGIN, [-float("inf")] * 4),
            # Balance Sheet
            (fld.Q_CASH, [233127550, 231865550, 185736074, 168533280]),
            # Income Statement
            (fld.Q_TOTAL_REVENUE, [22019850, 21069316, 19970220, 19727090]),
            (fld.Q_COS, [5073409, 4767026, 4651329, 4499566]),
            # Cashflow Statement
            (fld.Q_NET_CASH_FLOW, [3042325, -3732755, -2142246, -1378998]),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = date(2021, 3, 1)
        end_date = date(2021, 11, 12)

        # Test
        result = sdr.get_data_symbol_quarterly(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        expected = pd.DataFrame(
            {symbol: expected_list},
            index=pd.DatetimeIndex(
                ["2021-03-01", "2021-05-13", "2021-08-27", "2021-11-12"]
            ),
        )

        trade_dates = sdr.get_trading_dates(start_date, end_date)
        expected = expected.reindex(pd.DatetimeIndex(trade_dates))  # type: ignore

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("Q_")][::10]
    )
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_quarterly(field=field, symbol_list=[])

        # Check
        self._check(result)
        assert result.empty


class TestGetDataSymbolYearly:
    _check = staticmethod(TestGetDataSymbolDaily._check)

    @pytest.mark.skip("Some field in FINANCIAL_STAT_STD is missing")
    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("Q_")][::10]
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = date(2021, 3, 1)
        end_date = date(2021, 11, 12)

        # Test
        result = sdr.get_data_symbol_yearly(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected_list"],
        [
            # Financial Ratio
            (fld.Q_ROA, [1.6829434061191892]),
            (fld.Q_GROSS_PROFIT_MARGIN, [-float("inf")]),
            # Balance Sheet
            (fld.Q_CASH, [233127550.0]),
            # Income Statement
            (fld.Q_TOTAL_REVENUE, [89885610.0]),
            (fld.Q_COS, [23861086.0]),
            # Cashflow Statement
            (fld.Q_NET_CASH_FLOW, [-1889251.0]),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = date(2021, 3, 1)
        end_date = date(2021, 3, 1)

        # Test
        result = sdr.get_data_symbol_yearly(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        expected = pd.DataFrame(
            {symbol: expected_list}, index=pd.DatetimeIndex(["2021-03-01"])
        )

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("Q_")][::10]
    )
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_yearly(field=field, symbol_list=[])

        # Check
        self._check(result)

        assert result.empty


class TestGetDataSymbolTtm:
    _check = staticmethod(TestGetDataSymbolDaily._check)

    @pytest.mark.skip("Some field in FINANCIAL_STAT_STD is missing")
    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("Q_")][::10]
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = date(2021, 3, 1)
        end_date = date(2021, 11, 12)

        # Test
        result = sdr.get_data_symbol_ttm(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected_list"],
        [
            # Financial Ratio
            # Financial Ratio no TTM can be any result
            # (fld.Q_ROA, [-float("inf")] * 4),
            # (fld.Q_GROSS_PROFIT_MARGIN, [-float("inf")] * 4),
            # Balance Sheet
            # Balance Sheet no TTM can be any result
            # (fld.Q_CASH, [-float("inf")] * 4),
            # Income Statement
            (fld.Q_TOTAL_REVENUE, [89885610.0, 86495188.0, 84669125.0, 82786475.0]),
            (fld.Q_COS, [23861086.0, 21442714.0, 19895590.0, 18991330.0]),
            # Cashflow Statement
            (fld.Q_NET_CASH_FLOW, [-1889251.0, -2540135.0, -1985902.0, -4211674.0]),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = date(2021, 3, 1)
        end_date = date(2021, 11, 12)

        # Test
        result = sdr.get_data_symbol_ttm(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        expected = pd.DataFrame(
            {symbol: expected_list},
            index=pd.DatetimeIndex(
                ["2021-03-01", "2021-05-13", "2021-08-27", "2021-11-12"]
            ),
        )

        trade_dates = sdr.get_trading_dates(start_date, end_date)
        expected = expected.reindex(pd.DatetimeIndex(trade_dates))  # type: ignore

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize("field", [fld.Q_TOTAL_REVENUE, fld.Q_NET_CASH_FLOW])
    def test_empty(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_symbol_ttm(field=field, symbol_list=[])

        # Check
        self._check(result)
        assert result.empty


class TestGetDataSymbolYtd:
    _check = staticmethod(TestGetDataSymbolDaily._check)

    @pytest.mark.skip("Some field in FINANCIAL_STAT_STD is missing")
    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("Q_")][::10]
    )
    def test_field(self, sdr: SETDataReader, field: str):
        symbol_list = ["TTB"]
        start_date = date(2021, 3, 1)
        end_date = date(2021, 11, 12)

        # Test
        result = sdr.get_data_symbol_ytd(
            field=field,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected_list"],
        [
            # Financial Ratio
            # Financial Ratio no YTD can be any result
            # (
            #     fld.Q_ROA,
            #     [
            #         1.4697230952727913,
            #         1.3504085549573543,
            #         1.3672515432689933,
            #         1.46001638580354,
            #     ],
            # ),
            # (fld.Q_GROSS_PROFIT_MARGIN, [-float("inf")] * 4),
            # Balance Sheet
            # Balance Sheet no YTD can be any result
            # (fld.Q_CASH, [-float("inf")] * 4),
            # Income Statement
            (fld.Q_TOTAL_REVENUE, [89885610, 21069316, 41039535, 60766625]),
            (fld.Q_COS, [23861086, 4767026, 9418355, 13917921]),
            # Cashflow Statement
            (fld.Q_NET_CASH_FLOW, [-1889251, -3732755, -5875001, -7253999]),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, field: str, expected_list: List[float]
    ):
        symbol = "TTB"
        start_date = date(2021, 3, 1)
        end_date = date(2021, 11, 12)

        # Test
        result = sdr.get_data_symbol_ytd(
            field=field,
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Check
        self._check(result)
        assert_index_equal(
            result.index, pd.DatetimeIndex(sdr.get_trading_dates(start_date, end_date))
        )

        expected = pd.DataFrame(
            {symbol: expected_list},
            index=pd.DatetimeIndex(
                ["2021-03-01", "2021-05-13", "2021-08-27", "2021-11-12"]
            ),
        )

        trade_dates = sdr.get_trading_dates(start_date, end_date)
        expected = expected.reindex(pd.DatetimeIndex(trade_dates))  # type: ignore

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
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("D_INDEX")]
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
            (fld.INDEX_SET, fld.D_INDEX_HIGH, 1674.19),
            (fld.INDEX_SET, fld.D_INDEX_LOW, 1663.50),
            (fld.INDEX_SET, fld.D_INDEX_CLOSE, 1670.28),
            (fld.INDEX_SET, fld.D_INDEX_TOTAL_VOLUME, 28684980655),
            (fld.INDEX_SET, fld.D_INDEX_TOTAL_VALUE, 100014911411.57),
            (fld.INDEX_SET, fld.D_INDEX_MKT_PE, 20.96),
            (fld.INDEX_SET, fld.D_INDEX_MKT_PBV, 1.80),
            (fld.INDEX_SET, fld.D_INDEX_MKT_YIELD, 2.08),
            (fld.INDEX_SET, fld.D_INDEX_MKT_CAP, 19733996617934.5),
            (fld.INDEX_SSET, fld.D_INDEX_HIGH, 1156.83),
            (fld.INDEX_SSET, fld.D_INDEX_LOW, 1135.33),
            (fld.INDEX_SSET, fld.D_INDEX_CLOSE, 1156.83),
        ],
    )
    def test_field_with_expected(
        self, sdr: SETDataReader, index: str, field: str, expected: float
    ):
        """source: https://www.tradingview.com/chart/?symbol=SET:SET"""
        start_date = date(2022, 1, 4)
        end_date = date(2022, 1, 4)

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
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("D_INDEX")]
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
        assert (result.index == result.index.normalize()).all()  # type: ignore

        assert (result.columns.isin(fld.INDEX_LIST)).all()

        return result


class TestGetDataSectorDaily:
    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("D_SECTOR")][::5]
    )
    def test_field(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_sector_daily(field=field)

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected"],
        [
            (fld.D_SECTOR_INDEX_OPEN, 297.55),
            (fld.D_SECTOR_INDEX_HIGH, 299.36),
            (fld.D_SECTOR_INDEX_LOW, 293.34),
            (fld.D_SECTOR_INDEX_CLOSE, 296.13),
            (fld.D_SECTOR_VOLUME, 124063453),
            (fld.D_SECTOR_VALUE, 795051373.2),
            (fld.D_SECTOR_MKT_PE, 4.50),
            (fld.D_SECTOR_MKT_PBV, 1.29),
            (fld.D_SECTOR_MKT_YIELD, 4.30),
            (fld.D_SECTOR_MKT_CAP, 108032636545.26),
        ],
    )
    def test_field_with_expected(self, sdr: SETDataReader, field: str, expected: float):
        """source: https://www.tradingview.com/chart/?symbol=SET:AGRI"""
        start_date = date(2022, 1, 4)
        end_date = date(2022, 1, 4)

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

    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("D_SECTOR")]
    )
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
        assert (result.index == result.index.normalize()).all()  # type: ignore

        assert (result.columns.isin(fld.SECTOR_LIST)).all()

        return result


class TestGetDataIndustryDaily:
    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("D_INDUSTRY")][::5]
    )
    def test_field(self, sdr: SETDataReader, field: str):
        # Test
        result = sdr.get_data_industry_daily(field=field)

        # Check
        self._check(result)

        assert not result.empty

    @pytest.mark.parametrize(
        ["field", "expected"],
        [
            (fld.D_INDUSTRY_INDEX_OPEN, 481.75),
            (fld.D_INDUSTRY_INDEX_HIGH, 487.57),
            (fld.D_INDUSTRY_INDEX_LOW, 480.51),
            (fld.D_INDUSTRY_INDEX_CLOSE, 485.98),
            (fld.D_INDUSTRY_VOLUME, 511827513),
            (fld.D_INDUSTRY_VALUE, 8342552775.82),
            (fld.D_INDUSTRY_MKT_PE, 26.45),
            (fld.D_INDUSTRY_MKT_PBV, 2.05),
            (fld.D_INDUSTRY_MKT_YIELD, 2.55),
            (fld.D_INDUSTRY_MKT_CAP, 1297058662310.79),
        ],
    )
    def test_field_with_expected(self, sdr: SETDataReader, field: str, expected: float):
        """source: https://www.tradingview.com/chart/?symbol=SET:AGRO"""
        start_date = date(2022, 1, 4)
        end_date = date(2022, 1, 4)

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

    @pytest.mark.parametrize(
        "field", [getattr(fld, i) for i in dir(fld) if i.startswith("D_INDUSTRY")]
    )
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
        assert (result.index == result.index.normalize()).all()  # type: ignore

        assert (result.columns.isin(fld.INDUSTRY_LIST)).all()

        return result


@pytest.mark.parametrize(
    ("df", "expected"),
    [
        (pd.DataFrame(), True),
        (pd.DataFrame([1, 1]), False),
        (pd.DataFrame([1, 2]), True),
        (pd.DataFrame([1, 2, 3]), True),
        (pd.DataFrame([1, 1, 2]), False),
        (pd.DataFrame([1, 1, 2, 2]), False),
        (pd.DataFrame([[1, 2], [1, 2]]), False),
        (pd.DataFrame([[1, 1], [1, 2]]), True),
    ],
)
def test_is_df_unique(df: pd.DataFrame, expected: bool):
    assert is_df_unique(df) == expected


def is_df_unique(df):
    return (df.groupby([i for i in df.columns]).size() == 1).all()
