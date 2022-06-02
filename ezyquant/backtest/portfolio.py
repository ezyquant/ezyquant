from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import pandas as pd

from .position import Position
from .trade import Trade


@dataclass
class Portfolio:
    cash: float
    pct_commission: float = 0.0
    position_dict: Dict[str, Position] = field(default_factory=dict)
    trade_list: List[Trade] = field(default_factory=list)

    def __post_init__(self) -> None:
        # TODO: remove assert after testing

        # cash
        assert self.cash >= 0, "cash must be positive"

        # pct_commission
        assert 0 <= self.pct_commission <= 1, "pct_commission must be between 0 and 1"

        # position_dict
        for k, v in self.position_dict.items():
            assert isinstance(v, Position), "position_dict must be a dict of Position"
            assert v.symbol == k, "position_dict must be a dict of Position"

        # trade_list
        for i in self.trade_list:
            assert isinstance(i, Trade), "trade_list must be a list of Trade"

    @property
    def volume_series(self) -> pd.Series:
        return pd.Series(
            {k: v.volume for k, v in self.position_dict.items()}, dtype="float64"
        )

    def get_position_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.position_dict.values())  # type: ignore

    def place_order(
        self,
        symbol: str,
        volume: float,
        price: float,
        timestamp: datetime,
    ):
        # Create trade
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            volume=volume,
            price=price,
            pct_commission=self.pct_commission,
        )
        self.trade_list.append(trade)

        # Add/Reduce cash
        self.cash -= trade.value_with_commission
        if self.cash < 0:
            raise ValueError("Insufficient cash")

        # Add/Remove Position
        if symbol not in self.position_dict:
            self.position_dict[symbol] = Position(symbol=symbol)
        self.position_dict[symbol].place_order(volume=volume, price=price)
        if self.position_dict[symbol].volume == 0:
            del self.position_dict[symbol]

        return trade
