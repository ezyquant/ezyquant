import pytest

from ezyquant import SETDataReader, SETSignalCreator


@pytest.fixture(scope="session")
def sqlite_path() -> str:
    return "psims.db"


@pytest.fixture(scope="session")
def sdr(sqlite_path: str) -> SETDataReader:
    return SETDataReader(sqlite_path)


@pytest.fixture
def ssc(sqlite_path: str) -> SETSignalCreator:
    return SETSignalCreator(
        sqlite_path=sqlite_path,
        index_list=[],
        symbol_list=[],
    )
