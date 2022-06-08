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
    trade_date_index: pd.DatetimeIndex, rebalance_day: int
) -> pd.Series:
    assert (
        rebalance_day >= 1 and rebalance_day <= 5
    ), f"Week rebalance day ({rebalance_day}) must between [1-5]"

    tds = trade_date_index.to_series()
    rule = f"W-{calendar.day_abbr[rebalance_day-2]}"
    rbs = tds.resample(rule=rule).first()

    return tds.isin(rbs)
