from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    volume: int = 0
    cost_price: float = 0.0
    market_price: float = 0.0

    def __post_init__(self) -> None:
        assert isinstance(self.symbol, str), "symbol must be a string"

    @property
    def market_value(self) -> float:
        return self.volume * self.market_price

    @property
    def cost_value(self) -> float:
        return self.volume * self.cost_price

    def buy(self, volume: int, price: float):
        self.cost_price = ((self.volume * self.cost_price) + (volume * price)) / (
            self.volume + volume
        )
        self.volume += volume
        self.market_price = price

    def sell(self, volume: int, price: float):
        if volume > self.volume:
            raise ValueError(
                f"Trying to sell {volume} shares of {self.symbol} but only have {self.volume} shares"
            )
        self.volume -= volume
        self.market_price = price
