import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ezyquant.reader import SETDataReader
import datetime
import pytest

path = r"C:\Users\User\Desktop\fintech\ezyquant\ssetdi_db.db"
sdr = SETDataReader(path)


def test_get_trading_date():
    datstart = datetime.date(2030, 12, 25)
    datend = datetime.date(2030, 12, 30)
    # case not have input
    assert len(sdr.get_trading_dates()) >= len(sdr.get_trading_dates(end_date=datend))

    # case have only end_date
    assert sdr.get_trading_dates(end_date=datend)[0] <= datend

    # case have only start_date
    assert sdr.get_trading_dates(start_date=datstart)[0] >= datstart

    # case have both start_date and end_date
    assert sdr.get_trading_dates(start_date=datstart, end_date=datend)[0] >= datstart
    assert sdr.get_trading_dates(start_date=datstart, end_date=datend)[0] <= datend
