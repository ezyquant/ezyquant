import pytest

import ezyquant as ez
from ezyquant import SETDataReader, SETSignalCreator


@pytest.fixture(scope="session")
def sqlite_path() -> str:
    return "ezyquant.db"


@pytest.fixture(scope="session")
def connect_sqlite(sqlite_path: str):
    ez.connect_sqlite(sqlite_path)


@pytest.fixture(scope="session")
def connect_postgres():
    ez.connect_postgres(
        host="localhost",
        username="postgres",
        password="1234",
        port="5432",
        database="psims",
    )


@pytest.fixture
def sdr() -> SETDataReader:
    return SETDataReader()


@pytest.fixture
def ssc() -> SETSignalCreator:
    return SETSignalCreator(index_list=[], symbol_list=[])
