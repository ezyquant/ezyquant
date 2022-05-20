from datetime import date, datetime, timedelta


def date_to_str(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def str_to_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def str_date_add_timedelta(value: str, delta: timedelta) -> str:
    return date_to_str((str_to_date(value) + delta))
