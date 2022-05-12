import pytest

from ezyquant.reader import SETDataReader


@pytest.fixture
def sqlite_path() -> str:
    return "psims.db"


@pytest.fixture
def sdr(sqlite_path: str) -> SETDataReader:
    return SETDataReader(sqlite_path, ping=False)
