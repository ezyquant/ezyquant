from datetime import date
from typing import List

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest

from ezyquant.reader import SETDataReader


path = r"C:\Users\User\Desktop\fintech\ezyquant\ssetdi_db.db"
sdr = SETDataReader(path)


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
