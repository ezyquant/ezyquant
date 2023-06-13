from dataclasses import dataclass
from datetime import datetime

from ezyquant.utils import cached_property


@dataclass(frozen=True)
class SETTrade:
    """SETTrade.

    Parameters
    ----------
    matched_at: datetime
        The time when the trade was executed.
    symbol: str
        The symbol of the trade.
    volume: float
        The volume of the trade positive is buy and negative is sell (must be multiple of 100).
    price: float
        The price of the trade.
    pct_commission: float
        The percentage of commission (must be between 0 and 1).
    """

    matched_at: datetime
    symbol: str
    volume: float
    price: float
    pct_commission: float

    def __post_init__(self):
        # matched_at
        if not isinstance(self.matched_at, datetime):
            msg = f"matched_at must be datetime, got {type(self.matched_at)}"
            raise TypeError(msg)

        # symbol
        if not isinstance(self.symbol, str):
            msg = f"symbol must be str, got {type(self.symbol)}"
            raise TypeError(msg)
        if not self.symbol:
            msg = "symbol must not be empty"
            raise ValueError(msg)

        # volume
        if self.volume == 0:
            msg = "volume must not be zero"
            raise ValueError(msg)

        if self.volume % 100 != 0:
            msg = "volume must be multiple of 100"
            raise ValueError(msg)

        # price
        if not self.price > 0:
            msg = "price must be positive"
            raise ValueError(msg)

        # pct_commission
        if not (0 <= self.pct_commission <= 1):
            msg = "pct_commission must be between 0 and 1"
            raise ValueError(msg)

    @cached_property
    def value(self) -> float:
        """Positive is Buy, Negative is Sell."""
        return self.price * self.volume

    @cached_property
    def commission(self) -> float:
        """Always positive."""
        return abs(self.value * self.pct_commission)

    @cached_property
    def value_with_commission(self) -> float:
        """Amount of cash reduced by this trade.

        Positive is Buy, Negative is Sell
        """
        return self.value + self.commission
