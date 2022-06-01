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
    volume : float
        The volume of the trade, must be multiple of 100, positive is buy and negative is sell
    price : float
        The price of the trade
    pct_commission : float
        The percentage of commission, must be between 0 and 1
    """

    timestamp: datetime
    symbol: str
    volume: float
    price: float
    pct_commission: float

    def __post_init__(self):
        # TODO: remove assert after testing

        # timestamp
        assert isinstance(
            self.timestamp, datetime
        ), f"timestamp must be datetime, got {type(self.timestamp)}"

        # symbol
        assert isinstance(
            self.symbol, str
        ), f"symbol must be str, got {type(self.symbol)}"
        assert self.symbol != "", f"symbol must not be empty, got {self.symbol}"

        # volume
        assert self.volume != 0, f"volume must not be 0, got {self.volume}"
        assert (
            self.volume % 100 == 0
        ), f"volume must be multiple of 100, got {self.volume}"

        # price
        assert self.price > 0, f"price must be positive, got {self.price}"

        # pct_commission
        assert (
            0 <= self.pct_commission <= 1
        ), f"pct_commission must be between 0 and 1, got {self.pct_commission}"

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
