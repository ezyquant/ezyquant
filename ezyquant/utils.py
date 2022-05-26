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
