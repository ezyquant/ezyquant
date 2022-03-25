from datetime import date

from ezyquant.reader import SETDataReader


class TestGetTradeDates:
    def test_all(self, sdr: SETDataReader):
        result = sdr.get_trading_dates()

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(i, date) for i in result)
