import inspect
import re
from datetime import date
from typing import List, Optional

from .errors import InputError


def check_start_end_date(
    start_date: Optional[date],
    end_date: Optional[date],
    last_update_date: Optional[date] = None,
):
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise InputError("end_date is after today")

    if last_update_date is not None:
        if start_date is not None and start_date > last_update_date:
            raise InputError("start_date is after last_update_date")
        if end_date is not None and end_date > last_update_date:
            raise InputError("end_date is after last_update_date")


def check_duplicate(data_list: Optional[List[str]]):
    if data_list == None:
        return

    data_list = [x.upper() for x in data_list]

    if len(data_list) == len(set(data_list)):
        return

    raise InputError(f"Input was duplicate ({data_list})")
