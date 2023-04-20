import calendar
import copy
from datetime import date, datetime, timedelta
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

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
    return is_rebalance(
        trade_date_index=trade_date_index, rebalance_at=rebalance_at, freq="W"
    )


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
    return is_rebalance(
        trade_date_index=trade_date_index, rebalance_at=rebalance_at, freq="M"
    )


def is_rebalance(
    trade_date_index: pd.DatetimeIndex, rebalance_at: int, freq: str
) -> pd.Series:
    if not trade_date_index.is_monotonic_increasing or not trade_date_index.is_unique:
        raise InputError("trade_date_index must be monotonic and unique")

    tds = trade_date_index.to_series()

    if freq == "W":
        if not 1 <= rebalance_at <= 5:
            raise InputError("rebalance_at must be between 1 and 5")

        rule = f"W-{calendar.day_abbr[rebalance_at-2]}"
        by = pd.Grouper(freq=rule)

    elif freq == "M":
        if not 1 <= rebalance_at <= 31:
            raise InputError("rebalance_at must be between 1 and 31")

        tds = tds.mask(
            tds.dt.day < rebalance_at,
            tds - pd.DateOffset(months=1),  # type: ignore
        )
        by = [tds.dt.year, tds.dt.month]

    else:
        raise InputError("freq must be either W or M")

    return tds.groupby(by=by, group_keys=False).apply(lambda x: x == x[0])


def count_true_consecutive(s: pd.Series) -> pd.Series:
    return s * (s.groupby((s != s.shift()).cumsum()).cumcount() + 1)


def count_max_true_consecutive(s: pd.Series) -> int:
    """Count the number of consecutive True values in a series."""
    if s.empty:
        return 0
    return count_true_consecutive(s).max()


def union_datetime_index(indexes: List[pd.DatetimeIndex]) -> pd.DatetimeIndex:
    out = pd.DatetimeIndex([])
    for i in indexes:
        out = out.union(i)
    assert isinstance(out, pd.DatetimeIndex)
    return out


"""
Cache
"""


def cache_wrapper(
    func: Optional[Callable] = None, maxsize: int = 128, is_copy: bool = True
):
    """Cache the result of a function using lru_cache.

    Prase list arguments to sorted tuple and can return copy of result.
    """

    def _arg_handler(arg):
        if isinstance(arg, list):
            return tuple(sorted(arg))
        else:
            return arg

    def _outer_wrapper(fn: Callable):
        fn = lru_cache(maxsize=maxsize)(fn)

        @wraps(fn)
        def _inner_wrapper(*args, **kwargs):
            new_args = tuple(_arg_handler(i) for i in args)
            new_kwargs = {k: _arg_handler(v) for k, v in kwargs.items()}
            out = fn(*new_args, **new_kwargs)
            if is_copy:
                return copy.deepcopy(out)
            else:
                return out

        return _inner_wrapper

    if func:
        return _outer_wrapper(func)

    return _outer_wrapper


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
        method received keyword argument contain at least
            - symbol_list: Optional[List[str]] = None
            - start_date: Optional[str] = None
            - end_date: Optional[str] = None

        method must return dataframe with timestamp as index and symbol as column.
    """

    call_dict: Dict[Tuple[tuple], Dict[str, Any]] = {}

    def wrapped(
        *,
        symbol_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ):
        call_key = tuple(sorted(kwargs.items()))

        if call_key not in call_dict:
            c_symbol_list = symbol_list
            c_start_date = start_date
            c_end_date = end_date
        else:
            c_symbol_list = call_dict[call_key]["symbol_list"]
            c_start_date = call_dict[call_key]["start_date"]
            c_end_date = call_dict[call_key]["end_date"]

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
            symbol_list=c_symbol_list,
            start_date=c_start_date,
            end_date=c_end_date,
            **kwargs,
        )
        call_dict[call_key] = {
            "symbol_list": c_symbol_list,
            "start_date": c_start_date,
            "end_date": c_end_date,
        }

        if symbol_list is not None:
            df = df[[i for i in symbol_list if i in df.columns]]
        if start_date is not None:
            df = df[df.index >= start_date]
        if end_date is not None:
            df = df[df.index <= end_date]

        return df.copy()

    return wrapped


cached_property = lambda x: property(lru_cache(maxsize=1)(x))
