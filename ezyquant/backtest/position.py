from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    volume: float = 0.0
    avg_cost_price: float = 0.0

    def __post_init__(self):
        # TODO: remove assert after testing

        # symbol
        assert isinstance(
            self.symbol, str
        ), f"symbol must be str, got {type(self.symbol)}"
        assert self.symbol != "", f"symbol must not be empty, got {self.symbol}"

        # volume
        assert self.volume >= 0, f"volume must be positive, got {self.volume}"

        # price
        assert (
            self.avg_cost_price >= 0
        ), f"avg_cost_price must be positive, got {self.avg_cost_price}"

    @property
    def cost_value(self) -> float:
        return self.volume * self.avg_cost_price

    def place_order(self, volume: float, price: float) -> float:
        if volume > 0:
            self.avg_cost_price = (self.cost_value + (volume * price)) / (
                self.volume + volume
            )

        self.volume += volume

        if self.volume < 0:
            raise ValueError("Insufficient volume")

        return self.volume