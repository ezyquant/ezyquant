from functools import lru_cache
from typing import List

import pandas as pd

from . import fields as fld
from .reader import SETDataReader


class SETSignalCreator:
    def __init__(
        self,
        index_list: List[str],
        symbol_list: List[str],
        start_date: str,
        end_date: str,
        sqlite_path: str,
    ):
        """Initialize SETSignalCreator.

        Parameters
        ----------
        index_list : List[str]
            List of index name.
        symbol_list : List[str]
            List of symbol name.
        start_date : str
            Start date of data.
        end_date : str
            End date of data.
        sqlite_path : str
            Path of sqlite file.
        """
        self._index_list = [i.upper() for i in index_list]
        self._symbol_list = [i.upper() for i in symbol_list]
        self._start_date = start_date
        self._end_date = end_date
        self._sqlite_path = sqlite_path

        self._sdr = SETDataReader(self._sqlite_path, ping=False)

    """ 
    Protected methods
    """

    @lru_cache
    def _get_symbol_in_universe(self) -> List[str]:
        out = set()
        if self._symbol_list:
            df = self._sdr.get_symbol_info(symbol_list=self._symbol_list)
            out.update(df["symbol"].tolist())
        if fld.MARKET_SET in self._index_list:
            df = self._sdr.get_symbol_info(market=fld.MARKET_SET)
            out.update(df["symbol"].tolist())
        if fld.MARKET_MAI.upper() in self._index_list:
            df = self._sdr.get_symbol_info(market=fld.MARKET_MAI)
            out.update(df["symbol"].tolist())
        if self._index_list:
            df = self._get_symbols_by_index()
            out.update(df["symbol"].tolist())
        return list(out)

    def _get_symbol_info(self):
        s = self._get_symbol_in_universe()
        return self._sdr.get_symbol_info(symbol_list=s)

    def _get_symbols_by_index(self):
        l = []
        for i in self._index_list:
            start_date = self._sdr._get_prior_as_of_date_symbol_index(
                index_name=i, current_date=self._start_date
            )

            df = self._sdr.get_symbols_by_index(
                index_list=[i],
                start_date=start_date,
                end_date=self._end_date,
            )

            l.append(df)

        return pd.concat(l)
