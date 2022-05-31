from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    volume: float = 0.0
    cost_price: float = 0.0
    market_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.volume * self.market_price

    @property
    def cost_value(self) -> float:
        return self.volume * self.cost_price

    def place_order(self, volume: float, price: float) -> float:
        if volume > 0:
            self.cost_price = (self.cost_value + (volume * price)) / (
                self.volume + volume
            )

        self.volume += volume

        if self.volume < 0:
            raise ValueError("Insufficient volume")

        return self.volume
