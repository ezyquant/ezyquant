import inspect
import re
from datetime import date
from typing import List, Optional

from .errors import InputError


def check_start_end_date(start_date: Optional[date], end_date: Optional[date]):
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise InputError("end_date is after today")


def check_duplicate(data_list: Optional[List[str]]):
    if data_list == None:
        return

    data_list = [x.upper() for x in data_list]

    if len(data_list) == len(set(data_list)):
        return

    # get attribute name
    frame = inspect.getouterframes(inspect.currentframe())[1]
    code_str = inspect.getframeinfo(frame[0]).code_context[0].strip()  # type: ignore
    attr_name = re.search(r"\((.*)\)", code_str).group(1)  # type: ignore

    raise InputError(f"{attr_name} was duplicate")
