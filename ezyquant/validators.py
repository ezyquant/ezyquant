from typing import List, Optional

import pandas as pd
from pandas.testing import assert_index_equal

from ezyquant import utils
from ezyquant.errors import InputError


def check_start_end_date(
    start_date: Optional[str],
    end_date: Optional[str],
    last_update_date: Optional[str] = None,
):
    s = utils.str_to_date(start_date) if start_date else None
    e = utils.str_to_date(end_date) if end_date else None
    l = utils.str_to_date(last_update_date) if last_update_date else None

    if s is not None and e is not None:
        if s > e:
            msg = f"Start date {s} is after end date {e}"
            raise InputError(msg)

    if l is not None:
        if s is not None and s > l:
            msg = f"Start date {s} is after last update date {l}"
            raise InputError(msg)
        if e is not None and e > l:
            msg = f"End date {e} is after last update date {l}"
            raise InputError(msg)


def check_duplicate(data_list: Optional[List[str]]):
    if data_list is None:
        return

    data_list = [x.upper() for x in data_list]

    if len(data_list) == len(set(data_list)):
        return

    msg = f"Input was duplicate ({data_list})"
    raise InputError(msg)


def check_cash(cash: float) -> None:
    if cash < 0:
        msg = "cash must be positive"
        raise InputError(msg)


def check_pct(pct: float) -> None:
    if pct < 0 or pct > 1:
        msg = "pct must be between 0 and 1"
        raise InputError(msg)


def check_df_symbol_daily(df):
    if not isinstance(df, pd.DataFrame):
        msg = "Input must be a DataFrame"
        raise TypeError(msg)
    check_df_index_daily(df)
    check_df_column_symbol(df)


def check_df_index_daily(df):
    index = df.index
    if not isinstance(index, pd.DatetimeIndex):
        msg = "Index must be a DatetimeIndex"
        raise TypeError(msg)
    if not index.is_monotonic_increasing:
        msg = "Index must be sorted in ascending order"
        raise ValueError(msg)
    if not index.is_unique:
        msg = "Duplicate dates found"
        raise ValueError(msg)
    assert_index_equal(index, index.normalize())


def check_df_column_symbol(df):
    column = df.columns
    if not column.is_unique:
        msg = "Duplicate symbols found"
        raise ValueError(msg)
    assert_index_equal(column, column.str.upper())
