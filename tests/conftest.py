import pytest

from ezyquant import SETDataReader, SETSignalCreator


@pytest.fixture(scope="session")
def sqlite_path() -> str:
    return "psims.db"


@pytest.fixture(scope="session")
def sdr(sqlite_path: str) -> SETDataReader:
    return SETDataReader(sqlite_path, ping=False)


@pytest.fixture
def ssc(sqlite_path: str) -> SETSignalCreator:
    return SETSignalCreator(
        index_list=[],
        symbol_list=[],
        start_date="2020-01-01",
        end_date="2021-12-31",
        sqlite_path=sqlite_path,
    )
