from typing import List, Optional

from . import utils
from .errors import InputError


def check_start_end_date(
    start_date: Optional[str],
    end_date: Optional[str],
    last_update_date: Optional[str] = None,
):
    s = utils.str_to_date(start_date) if start_date else None
    e = utils.str_to_date(end_date) if end_date else None
    l = utils.str_to_date(last_update_date) if last_update_date else None

    if s is not None and e is not None:
        if s > e:
            raise InputError(
                f"Start date {start_date} is greater than end date {end_date}"
            )

    if l is not None:
        if s is not None and s > l:
            raise InputError(
                f"Start date {start_date} is greater than last update date {last_update_date}"
            )
        if e is not None and e > l:
            raise InputError(
                f"End date {end_date} is greater than last update date {last_update_date}"
            )


def check_duplicate(data_list: Optional[List[str]]):
    if data_list == None:
        return

    data_list = [x.upper() for x in data_list]

    if len(data_list) == len(set(data_list)):
        return

    raise InputError(f"Input was duplicate ({data_list})")
