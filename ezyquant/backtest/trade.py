import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Trade:
    """Trade

    Parameters
    -------
    timestamp : datetime
        The timestamp of the trade
    symbol : str
        The symbol of the trade
    volume : int
        The volume of the trade, must be multiple of 100, positive is buy and negative is sell
    price : float
        The price of the trade
    pct_commission : float
        The percentage of commission, must be between 0 and 1
    """

    timestamp: datetime
    symbol: str
    volume: int
    price: float
    pct_commission: float

    def __post_init__(self):
        # TODO: remove assert after testing
        # timestamp
        assert isinstance(self.timestamp, datetime), "timestamp must be datetime"

        # symbol
        assert isinstance(self.symbol, str), "symbol must be str"
        assert self.symbol != "", "symbol must not be empty"

        # volume
        assert not math.isnan(self.volume), "volume must be a number"
        assert self.volume != 0, "volume must be non-zero"
        assert self.volume % 100 == 0, "volume must be multiple of 100"

        # price
        assert isinstance(self.price, float), "price must be float"
        assert not math.isnan(self.price), "price must be a number"
        assert self.price > 0, "price must be positive"

        # pct_commission
        assert isinstance(self.pct_commission, float), "pct_commission must be float"
        assert not math.isnan(self.pct_commission), "pct_commission must be a number"
        assert 0 <= self.pct_commission <= 1, "pct_commission must be between 0 and 1"

    @property
    def value(self) -> float:
        """Positive is Buy, Negative is Sell"""
        return self.price * self.volume

    @property
    def commission(self) -> float:
        """Always positive"""
        return abs(self.value * self.pct_commission)

    @property
    def value_with_commission(self) -> float:
        """Amount of cash reduced by this trade. Positive is Buy, Negative is Sell"""
        return self.value + self.commission
