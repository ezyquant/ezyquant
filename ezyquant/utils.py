import calendar
from datetime import date, datetime, timedelta

import pandas as pd


def date_to_str(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def str_to_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def str_date_add_timedelta(value: str, delta: timedelta) -> str:
    return date_to_str((str_to_date(value) + delta))


def pivot_remove_index_name(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    df = df.pivot(*args, **kwargs)
    df.index.name = None
    df.columns.name = None
    return df


def round_df_100(df: pd.DataFrame) -> pd.DataFrame:
    return df // 100 * 100.0


def is_rebalance_weekly(
    trade_date_index: pd.DatetimeIndex, rebalance_at: int
) -> pd.Series:
    """Return a series of bool, True if the date is a rebalance date.
    Always rebalance on first day of index.

    Parameters
    ----------
    trade_date_index : pd.DatetimeIndex
        Trade date index.
    rebalance_at : int
        Day of week to rebalance. 1 is Monday, 5 is Friday.

    Returns
    -------
    pd.Series
        Series of bool, True if the date is a rebalance date.
    """
    if not trade_date_index.is_monotonic or not trade_date_index.is_unique:
        raise ValueError("trade_date_index must be monotonic and unique")
    if rebalance_at < 1 or rebalance_at > 5:
        raise ValueError("rebalance_at must be between 1 and 5")

    td_s = trade_date_index.to_series()

    rule = f"W-{calendar.day_abbr[rebalance_at-2]}"
    rbs = td_s.resample(rule=rule).first()
    return td_s.isin(rbs)


def is_rebalance_monthly(
    trade_date_index: pd.DatetimeIndex, rebalance_at: int
) -> pd.Series:
    """Return a series of bool, True if the date is a rebalance date.
    Always rebalance on first day of index.

    Parameters
    ----------
    trade_date_index : pd.DatetimeIndex
        Trade date index.
    rebalance_at : int
        Day of month to rebalance. Can be 1-31.

    Returns
    -------
    pd.Series
        Series of bool, True if the date is a rebalance date.
    """
    if not trade_date_index.is_monotonic or not trade_date_index.is_unique:
        raise ValueError("trade_date_index must be monotonic and unique")
    if rebalance_at < 1 or rebalance_at > 31:
        raise ValueError("rebalance_at must be between 1 and 31")

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

    return td_s.isin(td_s[idx])


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
