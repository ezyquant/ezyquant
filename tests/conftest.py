import pytest

from ezyquant.reader import SETDataReader


@pytest.fixture
def sqlite_path() -> str:
    return "psims.sqlite3"


@pytest.fixture
def sdr(sqlite_path: str) -> SETDataReader:
    return SETDataReader(sqlite_path)
