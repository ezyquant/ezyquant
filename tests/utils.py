import string
from itertools import product
from typing import List

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from pandas.tseries.offsets import BusinessDay


def sort_index_column(df: pd.DataFrame) -> pd.DataFrame:
    if not df.empty:
        assert df.index.is_integer()
    df = df.sort_index(axis=1)
    df = df.sort_values(by=df.columns.to_list()).reset_index(drop=True)
    return df


def assert_frame_equal_sort_index(
    df1: pd.DataFrame, df2: pd.DataFrame, check_dtype: bool = True
):
    df1 = sort_index_column(df1)
    df2 = sort_index_column(df2)
    assert_frame_equal(df1, df2, check_dtype=check_dtype)


def is_df_unique(df) -> bool:
    return (df.groupby(list(df.columns)).size() == 1).all()


def is_df_unique_cols(df) -> bool:
    if df.empty:
        return True
    a = df.to_numpy()
    return ((a[0] == a).all(0)).all()


"""
Backtest
"""

N_ROW = 10
N_COL = 4


def make_str_list(n: int = N_COL) -> List[str]:
    p = product(string.ascii_uppercase, repeat=3)
    return ["".join(next(p)) for _ in range(n)]


def make_bdate_range(n: int = N_ROW) -> pd.DatetimeIndex:
    return pd.bdate_range(start="2000-01-01", periods=n)


def make_trading_dates(n: int = N_ROW) -> List[str]:
    return make_bdate_range(n).strftime("%Y-%m-%d").to_list()


def make_data_df(data, n_row: int = N_ROW, n_col: int = N_COL) -> pd.DataFrame:
    return pd.DataFrame(
        data, columns=make_str_list(n_col), index=make_bdate_range(n_row)
    )


def make_signal_weight_df(n_row: int = N_ROW, n_col: int = N_COL) -> pd.DataFrame:
    """Equal weight top 10 and monthly rebalance."""
    df = make_data_df(np.random.rand(n_row, n_col), n_row, n_col)

    # Top 10
    df = (df.rank(axis=1) <= 10).astype(bool) / 10

    # Rebalance monthly
    idx_ym = df.index.strftime("%Y%m")  # type: ignore
    df = df[~idx_ym.duplicated()]
    assert isinstance(df, pd.DataFrame)

    return df


def make_price_df(n_row: int = N_ROW, n_col: int = N_COL) -> pd.DataFrame:
    """Make random price from a normal (Gaussian) distribution."""
    df = make_data_df(np.random.normal(1, 0.1, size=(n_row, n_col)), n_row, n_col)
    df = df.cumprod()
    return df


def make_close_price_df(n_row: int = N_ROW, n_col: int = N_COL) -> pd.DataFrame:
    """Make random price from a normal (Gaussian) distribution."""
    df = make_price_df(n_row=n_row + 1, n_col=n_col)
    df.index -= BusinessDay(1)
    return df
