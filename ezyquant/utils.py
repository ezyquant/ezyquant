from datetime import date, datetime


def date_to_str(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def str_to_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
