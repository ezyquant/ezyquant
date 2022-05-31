from dataclasses import dataclass, field


@dataclass
class Position:
    symbol: str
    volume: int = field(default=0, init=False)
    cost_price: float = field(default=0.0, init=False)
    market_price: float = field(default=0.0)

    @property
    def market_value(self) -> float:
        return self.volume * self.market_price

    @property
    def cost_value(self) -> float:
        return self.volume * self.cost_price

    def place_order(self, volume: int, price: float):
        if volume > 0:
            self.cost_price = ((self.volume * self.cost_price) + (volume * price)) / (
                self.volume + volume
            )

        self.volume += volume

        if self.volume < 0:
            raise ValueError("Insufficient volume")
