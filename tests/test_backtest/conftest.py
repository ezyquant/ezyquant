import string
from itertools import product
from typing import List

import numpy as np
import pandas as pd
import pytest

N_SYMBOL = 4
N_DATE = 10

FLOOR_RATIO = 0.9
CEIL_RATIO = 1.1


@pytest.fixture(scope="session")
def symbol_list() -> List[str]:
    p = product(string.ascii_uppercase, repeat=3)
    return ["".join(next(p)) for _ in range(N_SYMBOL)]


@pytest.fixture(scope="session")
def datetime_index() -> pd.DatetimeIndex:
    return pd.bdate_range(start="2000-01-01", periods=N_DATE)


@pytest.fixture
def signal_weight_df(
    symbol_list: List[str], datetime_index: pd.DatetimeIndex
) -> pd.DataFrame:
    df = pd.DataFrame(
        np.random.rand(N_DATE, N_SYMBOL),
        columns=symbol_list,
        index=datetime_index,
    )
    df = (df.rank(axis=1) <= 10).astype(bool) / 10
    return df


@pytest.fixture
def close_price_df(
    symbol_list: List[str], datetime_index: pd.DatetimeIndex
) -> pd.DataFrame:
    return pd.DataFrame(
        np.random.uniform(FLOOR_RATIO, CEIL_RATIO, (N_DATE, N_SYMBOL)),
        columns=symbol_list,
        index=datetime_index,
    ).cumprod()


@pytest.fixture
def match_price_df(close_price_df: pd.DataFrame) -> pd.DataFrame:
    return close_price_df.shift(1, fill_value=1) * np.random.uniform(
        FLOOR_RATIO, CEIL_RATIO, close_price_df.shape
    )


@pytest.fixture
def is_rebalance_df(
    symbol_list: List[str], datetime_index: pd.DatetimeIndex
) -> pd.DataFrame:
    df = pd.DataFrame(
        True,  # type: ignore
        columns=symbol_list,
        index=datetime_index,
    )
    return df
