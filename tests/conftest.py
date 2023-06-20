import pytest

from ezyquant import SETDataReader


@pytest.fixture
def sdr() -> SETDataReader:
    return SETDataReader()
