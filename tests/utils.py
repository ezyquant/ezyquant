import string
from itertools import product
from typing import List

import numpy as np
import pandas as pd
import pandas.api.types as ptypes
from pandas.testing import assert_frame_equal, assert_index_equal, assert_series_equal


def sort_index_column(df: pd.DataFrame) -> pd.DataFrame:
    assert isinstance(df.index, pd.RangeIndex), "Index must be RangeIndex"
    df = df.sort_index(axis=1)
    df = df.sort_values(by=df.columns.to_list()).reset_index(drop=True)
    return df


def assert_frame_equal_sort_index(
    df1: pd.DataFrame, df2: pd.DataFrame, check_dtype: bool = True
):
    df1 = sort_index_column(df1)
    df2 = sort_index_column(df2)
    assert_frame_equal(df1, df2, check_dtype=check_dtype)  # type: ignore


def check_index_daily(result, is_unique=True):
    assert isinstance(result, pd.DatetimeIndex)
    assert result.is_monotonic_increasing
    if is_unique:
        assert result.is_unique
    assert_index_equal(result, result.normalize())  # type: ignore


def check_data_symbol_daily(result):
    assert isinstance(result, pd.DataFrame)

    # Index
    check_index_daily(result.index)

    # Column
    assert result.columns.is_unique
    assert_index_equal(result.columns, result.columns.str.upper())


def check_cash_series(series):
    assert isinstance(series, pd.Series)

    # Index
    check_index_daily(series.index)

    # Data type
    assert ptypes.is_float_dtype(series)

    # Cash
    assert (series >= 0).all()

    assert not series.empty


def check_position_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(
        df.columns, pd.Index(["timestamp", "symbol", "volume", "avg_cost_price"])
    )

    # Data type
    # assert ptypes.is_datetime64_any_dtype(df["timestamp"])
    # assert ptypes.is_string_dtype(df["symbol"])
    assert ptypes.is_float_dtype(df["volume"])
    assert ptypes.is_float_dtype(df["avg_cost_price"])


def check_trade_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(
        df.columns,
        pd.Index(["timestamp", "symbol", "volume", "price", "pct_commission"]),
    )

    # Data type
    # assert ptypes.is_datetime64_any_dtype(df["timestamp"])
    # assert ptypes.is_string_dtype(df["symbol"])
    assert ptypes.is_float_dtype(df["volume"])
    assert ptypes.is_float_dtype(df["price"])
    assert ptypes.is_float_dtype(df["pct_commission"])


def is_df_unique(df) -> bool:
    return (df.groupby([i for i in df.columns]).size() == 1).all()


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


def make_data_df(data, n_row: int = N_ROW, n_col: int = N_COL):
    return pd.DataFrame(
        data, columns=make_str_list(n_col), index=make_bdate_range(n_row)
    )


def make_signal_weight_df(n_row: int = N_ROW, n_col: int = N_COL):
    """Equal weight top 10 symbol"""
    df = make_data_df(np.random.rand(n_row, n_col), n_row, n_col)
    df = (df.rank(axis=1) <= 10).astype(bool) / 10
    return df


def make_price_df(n_row: int = N_ROW, n_col: int = N_COL):
    """Make random price from a normal (Gaussian) distribution."""
    df = make_data_df(np.random.normal(1, 0.1, size=(n_row, n_col)), n_row, n_col)
    df = df.cumprod()
    return df
