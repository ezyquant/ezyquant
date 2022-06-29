import pytest

import ezyquant as ez
from ezyquant import SETDataReader, SETSignalCreator


@pytest.fixture(scope="session")
def sqlite_path() -> str:
    return "psims.db"


@pytest.fixture(autouse=True)
def connect_sqlite(sqlite_path: str):
    ez.connect_sqlite(sqlite_path)


@pytest.fixture
def sdr() -> SETDataReader:
    return SETDataReader()


@pytest.fixture
def ssc() -> SETSignalCreator:
    return SETSignalCreator(index_list=[], symbol_list=[])
