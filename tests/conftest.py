import pytest

from ezyquant.creator import SETSignalCreator
from ezyquant.reader import SETDataReader


@pytest.fixture(scope="session")
def sqlite_path() -> str:
    return "psims.db"


@pytest.fixture(scope="session")
def sdr(sqlite_path: str) -> SETDataReader:
    return SETDataReader(sqlite_path, ping=False)


@pytest.fixture
def ssc() -> SETSignalCreator:
    return SETSignalCreator()
