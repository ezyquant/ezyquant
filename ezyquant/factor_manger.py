from datetime import date
from typing import Iterable


class _SETBaseFactorManager:
    def __init__(self, start_date: date, end_date: date) -> None:
        self._start_date = start_date
        self._end_date = end_date


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
