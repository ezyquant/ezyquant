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
        if not isinstance(self.symbol, str):
            msg = f"symbol must be str, got {type(self.symbol)}"
            raise TypeError(msg)

        # volume
        if not self.volume >= 0:
            msg = f"volume must be positive, got {self.volume}"
            raise ValueError(msg)
        if not (self.volume % 100 == 0):
            msg = f"volume must be multiple of 100, got {self.volume}"
            raise ValueError(msg)

        # price
        if not (self.cost_price >= 0):
            msg = f"cost_price must be positive, got {self.cost_price}"
            raise ValueError(msg)

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
            msg = "Insufficient volume"
            raise ValueError(msg)

        return self.volume
