from dataclasses import dataclass

import pandas as pd


@dataclass
class SETPosition:
    symbol: str
    volume: float = 0.0
    cost_price: float = 0.0
    close_price: float = float("nan")

    def __post_init__(self):
        # symbol
        assert isinstance(
            self.symbol, str
        ), f"symbol must be str, got {type(self.symbol)}"

        # volume
        assert self.volume >= 0, f"volume must be positive, got {self.volume}"
        assert (
            self.volume % 100 == 0
        ), f"volume must be multiple of 100, got {self.volume}"

        # price
        assert (
            self.cost_price >= 0
        ), f"cost_price must be positive, got {self.cost_price}"

    @property
    def cost_value(self) -> float:
        return self.volume * self.cost_price

    @property
    def close_value(self) -> float:
        if pd.notna(self.close_price):
            return self.volume * self.close_price
        else:
            return 0.0

    def match_order(self, volume: float, price: float) -> float:
        if volume > 0:
            self.cost_price = (self.cost_value + (volume * price)) / (
                self.volume + volume
            )

        self.volume += volume

        if self.volume < 0:
            raise ValueError("Insufficient volume")

        return self.volume
