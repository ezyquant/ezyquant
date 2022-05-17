import pytest

from ezyquant.creator import SETSignalCreator
from ezyquant.reader import SETDataReader


@pytest.fixture(scope="session")
def sqlite_path() -> str:
    return "psims.db"


@pytest.fixture(scope="session")
def sdr(sqlite_path: str) -> SETDataReader:
    return SETDataReader(sqlite_path, ping=False)


@pytest.fixture(scope="session")
def ssc(sqlite_path: str) -> SETSignalCreator:
    return SETSignalCreator(
        index_list=[],
        symbol_list=[],
        sector_list=[],
        industry_list=[],
        start_date="2010-01-01",
        end_date="2020-01-01",
        sqlite_path=sqlite_path,
    )
