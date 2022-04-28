from datetime import date
from typing import Any, List, Optional, Union

from .errors import InputError


def check_start_end_date(start_date: Optional[date], end_date: Optional[date]):
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise InputError("end_date is after today")


def check_duplicate(data_list: Optional[List[str]], attr_name: str):
    if data_list != None:
        data_list = [x.upper() for x in data_list]
        if len(data_list) != len(set(data_list)):
            raise InputError(f"{attr_name} was duplicate")
