from datetime import date
from typing import List


class SETDataReader:
    def __init__(self, sqlite_path: str) -> None:
        """
        The __init__ function is called when an instance of a class is created

        :param sqlite_path: The path to the SQLite database file
        :type sqlite_path: str
        """
        self.__sqlite_path = sqlite_path

    def get_trading_dates(self, start_date: date, end_date: date) -> List[date]:
        return []
