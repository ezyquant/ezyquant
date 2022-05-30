from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    volume: int = 0
    cost_price: float = 0.0
    market_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.volume * self.market_price

    @property
    def cost_value(self) -> float:
        return self.volume * self.cost_price

    def transact(self, volume: int, price: float):
        if volume > 0:
            self.cost_price = ((self.volume * self.cost_price) + (volume * price)) / (
                self.volume + volume
            )

        self.volume += volume

        if self.volume < 0:
            raise ValueError("Insufficient volume")

        self.market_price = price
