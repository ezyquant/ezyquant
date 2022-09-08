import calendar
import copy
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from .errors import InputError


def date_to_str(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def str_to_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def str_to_date(value: str) -> date:
    return str_to_datetime(value).date()


def str_date_add_timedelta(value: str, delta: timedelta) -> str:
    return date_to_str((str_to_date(value) + delta))


def pivot_remove_index_name(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    df = df.pivot(*args, **kwargs)
    df.index.name = None
    df.columns.name = None
    return df


def round_down(value, base=100.0):
    return int(value / base) * base


def is_rebalance_weekly(
    trade_date_index: pd.DatetimeIndex, rebalance_at: int
) -> pd.Series:
    """Return a series of bool, True if the date is a rebalance date. Always
    rebalance on first day of index.

    Parameters
    ----------
    trade_date_index: pd.DatetimeIndex
        Trade date index.
    rebalance_at: int
        Day of week to rebalance (e.g. 1 is Monday or 5 is Friday).

    Returns
    -------
    pd.Series
        Series of bool. True if the date is a rebalance date.
    """
    if not trade_date_index.is_monotonic or not trade_date_index.is_unique:
        raise InputError("trade_date_index must be monotonic and unique")
    if rebalance_at < 1 or rebalance_at > 5:
        raise InputError("rebalance_at must be between 1 and 5")

    td_s = trade_date_index.to_series()

    rule = f"W-{calendar.day_abbr[rebalance_at-2]}"
    rbs = td_s.resample(rule=rule).first()
    return td_s.isin(rbs)


def is_rebalance_monthly(
    trade_date_index: pd.DatetimeIndex, rebalance_at: int
) -> pd.Series:
    """Return a series of bool, True if the date is a rebalance date. Always
    rebalance on first day of index.

    Parameters
    ----------
    trade_date_index: pd.DatetimeIndex
        Trade date index.
    rebalance_at: int
        Day of month to rebalance (available from 1-31).

    Returns
    -------
    pd.Series
        Series of bool, True if the date is a rebalance date.
    """
    if not trade_date_index.is_monotonic or not trade_date_index.is_unique:
        raise InputError("trade_date_index must be monotonic and unique")
    if rebalance_at < 1 or rebalance_at > 31:
        raise InputError("rebalance_at must be between 1 and 31")

    td_s = trade_date_index.to_series()

    # TODO: improve is_rebalance_monthly
    v = _date_range(
        start_month=td_s[0].month,
        start_year=td_s[0].year,
        end_month=td_s[-1].month,
        end_year=td_s[-1].year,
        day_of_month=rebalance_at,
    )

    idx = td_s.searchsorted(v, side="left")
    idx = idx[idx != td_s.size]

    return td_s.isin(td_s[idx])  # type: ignore


def _date_range(
    start_month: int,
    start_year: int,
    end_month: int,
    end_year: int,
    day_of_month: int,
):
    out = []

    ym_start = 12 * start_year + start_month - 2
    ym_end = 12 * end_year + end_month + 1

    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        try:
            out.append(date(y, m + 1, day_of_month))
        except ValueError:
            assert day_of_month > 28
            out.append(date(y, m + 2, 1))

    assert len(out) >= 3

    out = pd.to_datetime(out)
    return out


def count_true_consecutive(s: pd.Series) -> pd.Series:
    return s * (s.groupby((s != s.shift()).cumsum()).cumcount() + 1)


def count_max_true_consecutive(s: pd.Series) -> int:
    """Count the number of consecutive True values in a series."""
    if s.empty:
        return 0
    return count_true_consecutive(s).max()


"""
Cache
"""


def cache_wrapper(method):
    """Cache the result of a method using lru_cache.

    Prase list arguments to sorted tuple and return copy of result.
    """
    method = lru_cache(maxsize=128)(method)

    def _arg_handler(arg):
        if isinstance(arg, list):
            return tuple(sorted(arg))
        else:
            return arg

    def wrapped(*args, **kwargs):
        new_args = tuple(_arg_handler(i) for i in args)
        new_kwargs = {k: _arg_handler(v) for k, v in kwargs.items()}
        out = method(*new_args, **new_kwargs)
        return copy.deepcopy(out)

    return wrapped


class CacheMetaClass(type):
    """Meta class for cache_wrapper."""

    def __new__(cls, clsname, bases, attrs):
        new_attrs = {
            k: cache_wrapper(v) if not k.startswith("_") and callable(v) else v
            for k, v in attrs.items()
        }
        return type.__new__(cls, clsname, bases, new_attrs)


def wrap_cache_class(cls):
    return CacheMetaClass(cls.__name__, cls.__bases__, cls.__dict__)


def cache_dataframe_wrapper(method: Callable):
    """Wrap a method to cache the result of the method.

    Parameters
    ----------
    method: Callable
        method parameter must be
            - field: str
            - symbol_list: Optional[List[str]] = None
            - start_date: Optional[str] = None
            - end_date: Optional[str] = None

        method must return dataframe with timestamp as index and symbol as column.
    """

    call_dict: Dict[str, Dict[str, Any]] = {}

    def wrapped(
        field: str,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        if symbol_list != None:
            symbol_list = [i.upper() for i in symbol_list]

        if field not in call_dict:
            c_symbol_list = symbol_list
            c_start_date = start_date
            c_end_date = end_date
        else:
            c_symbol_list = call_dict[field]["symbol_list"]
            c_start_date = call_dict[field]["start_date"]
            c_end_date = call_dict[field]["end_date"]

            if c_symbol_list == None or symbol_list == None:
                c_symbol_list = None
            elif set(symbol_list) - set(c_symbol_list):
                c_symbol_list = c_symbol_list + list(
                    set(symbol_list) - set(c_symbol_list)
                )

            if c_start_date == None or start_date == None:
                c_start_date = None
            elif c_start_date > start_date:
                c_start_date = start_date

            if c_end_date == None or end_date == None:
                c_end_date = None
            elif c_end_date < end_date:
                c_end_date = end_date

        df = method(
            field=field,
            symbol_list=c_symbol_list,
            start_date=c_start_date,
            end_date=c_end_date,
        )
        call_dict[field] = {
            "symbol_list": c_symbol_list,
            "start_date": c_start_date,
            "end_date": c_end_date,
        }

        if symbol_list != None:
            df = df[[i for i in symbol_list if i in df.columns]]
        if start_date != None:
            df = df[df.index >= start_date]
        if end_date != None:
            df = df[df.index <= end_date]

        return df.copy()

    return wrapped


cached_property = lambda x: property(lru_cache(maxsize=1)(x))
