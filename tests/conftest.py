import pytest

from ezyquant.reader import SETDataReader


@pytest.fixture
def sqlite_path():
    return "ssetdi_db.db"


@pytest.fixture
def sdr():
    return SETDataReader(path)
