from typing import List, Optional

import pandas as pd
from pandas.testing import assert_index_equal

from . import utils
from .errors import InputError


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
            raise InputError(f"Start date {s} is after end date {e}")

    if l is not None:
        if s is not None and s > l:
            raise InputError(f"Start date {s} is after last update date {l}")
        if e is not None and e > l:
            raise InputError(f"End date {e} is after last update date {l}")


def check_duplicate(data_list: Optional[List[str]]):
    if data_list == None:
        return

    data_list = [x.upper() for x in data_list]

    if len(data_list) == len(set(data_list)):
        return

    raise InputError(f"Input was duplicate ({data_list})")


def check_cash(cash: float) -> None:
    if cash < 0:
        raise InputError("cash must be positive")


def check_pct(pct: float) -> None:
    if pct < 0 or pct > 1:
        raise InputError("pct must be between 0 and 1")


def check_df_symbol_daily(df):
    assert isinstance(df, pd.DataFrame)
    check_df_index_daily(df)
    check_df_column_symbol(df)


def check_df_index_daily(df):
    index = df.index
    assert isinstance(index, pd.DatetimeIndex)
    assert index.is_monotonic
    assert index.is_unique
    assert_index_equal(index, index.normalize())  # type: ignore


def check_df_column_symbol(df):
    column = df.columns
    assert column.is_unique
    assert_index_equal(column, column.str.upper())
