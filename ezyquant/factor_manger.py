from datetime import date
from typing import Iterable
import pandas as pd


class _SETBaseFactorManager:
    def __init__(self, start_date: date, end_date: date) -> None:
        self._start_date = start_date
        self._end_date = end_date

    def get_factor(
        self,
        factor: str,
        timeframe: str,
        period: int = 1,
        shift: int = 0,
        by: str = "stock",
        method: str = "constant",
        row_trading_date: bool = True,
    ) -> pd.DataFrame:
        """
        by: stock, sector, industry
        method: constant, sum, mean, median, ...
        period: integer must be greater than 0 (period >= 1)
        shift: integer must be less that 1 (shift <= 0)
        """
        return pd.DataFrame()

    def is_index(self, index: str) -> pd.DataFrame:
        return pd.DataFrame()

    def is_sector(self, sector: str) -> pd.DataFrame:
        return pd.DataFrame()

    def is_industry(self, industry: str) -> pd.DataFrame:
        return pd.DataFrame()

    def is_banned(self):
        return pd.DataFrame()


class SETUniverseFactorManager(_SETBaseFactorManager):
    def __init__(
        self,
        max_universe: str,
        start_date: date,
        end_date: date,
    ) -> None:
        super().__init__(start_date, end_date)


class SETSymbolFactorManager(_SETBaseFactorManager):
    def __init__(
        self,
        symbols: Iterable[str],
        start_date: date,
        end_date: date,
    ) -> None:
        super().__init__(start_date, end_date)
