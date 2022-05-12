from datetime import date
from typing import List, Optional

from .errors import InputError


def check_start_end(start, end, last_update=None):
    if start is not None and end is not None:
        if start > end:
            raise InputError(f"start {start} is after end {end}")

    if last_update is not None:
        if start is not None and start > last_update:
            raise InputError(f"start {start} is after last update {last_update}")
        if end is not None and end > last_update:
            raise InputError(f"end {end} is after last update {last_update}")


def check_duplicate(data_list: Optional[List[str]]):
    if data_list == None:
        return

    data_list = [x.upper() for x in data_list]

    if len(data_list) == len(set(data_list)):
        return

    raise InputError(f"Input was duplicate ({data_list})")
