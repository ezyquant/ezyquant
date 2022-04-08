from datetime import date
from typing import List

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
    def test_no_result(self, sdr: SETDataReader, start_date: date, end_date: date):
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
        assert result["market"].isin([fld.MARKET_SET, fld.MARKET_MAI]).all()
        assert result["industry"].isin(fld.INDUSTRY_LIST).all()
        assert result["sector"].isin(fld.SECTOR_LIST).all()

    def test_symbol_list(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(symbol_list=["TCCC", "PTTGC"])

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

    def test_market(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(market=fld.MARKET_MAI)

        # Check
        self._check(result)

        assert (result["market"] == fld.MARKET_SET).all()
        assert result["industry"].isin(fld.INDUSTRY_LIST).all()
        # MAI sector name same as industry name
        assert result["sector"].isin(fld.INDUSTRY_LIST).all()
        assert "STA" in result["symbol"]

    def test_industry(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(industry=fld.INDUSTRY_AGRO)

        # Check
        self._check(result)

        assert result["market"].isin([fld.MARKET_SET, fld.MARKET_MAI]).all()
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

    def test_symbol_list_and_sector(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(
            symbol_list=["TCCC", "PTTGC"], sector=fld.SECTOR_PETRO
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

    def test_no_result(self, sdr: SETDataReader):
        result = sdr.get_symbol_info(
            symbol_list=["TCCC", "PTTGC"], market=fld.MARKET_MAI
        )

        # Check
        self._check(result)

        assert result.empty

    @staticmethod
    def _check(result):
        assert isinstance(result, pd.DataFrame)
        assert result["symbol_id"].is_unique
        assert result["symbol"].is_unique

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

        assert_series_equal(result["symbol"], result["symbol"].str.upper())
        assert_series_equal(result["market"], result["market"].str.upper())
        assert_series_equal(result["industry"], result["industry"].str.upper())
        assert_series_equal(result["sector"], result["sector"].str.upper())

        return result
