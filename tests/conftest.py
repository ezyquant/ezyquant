import pytest

import ezyquant as ez
from ezyquant import SETDataReader, SETSignalCreator


@pytest.fixture(scope="session")
def sqlite_path() -> str:
    return "psims.db"


@pytest.fixture(scope="session")
def sdr(sqlite_path: str) -> SETDataReader:
    return SETDataReader(sqlite_path)


@pytest.fixture
def ssc(sqlite_path: str) -> SETSignalCreator:
    ez.connect_sqlite(sqlite_path)
    return SETSignalCreator(index_list=[], symbol_list=[])
