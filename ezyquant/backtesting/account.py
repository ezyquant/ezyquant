from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

import pandas as pd

from .. import utils
from .position import SETPosition
from .trade import SETTrade


@dataclass
class SETAccount:
    cash: float
    pct_commission: float = 0.0
    position_dict: Dict[str, SETPosition] = field(default_factory=dict)
    trade_list: List[SETTrade] = field(default_factory=list)
    close_price_dict: Dict[str, float] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self):
        # cash
        assert self.cash >= 0, "cash must be positive"

        # pct_commission
        assert 0 <= self.pct_commission <= 1, "pct_commission must be between 0 and 1"

        # position_dict
        for k, v in self.position_dict.items():
            assert isinstance(
                v, SETPosition
            ), "position_dict must be a dict of SETPosition"
            assert v.symbol == k, "position_dict must be a dict of SETPosition"

        # trade_list
        for i in self.trade_list:
            assert isinstance(i, SETTrade), "trade_list must be a list of SETTrade"

        self.ratio_commission = 1.0 + self.pct_commission

    @property
    def port_value(self) -> float:
        return self.total_market_value + self.cash

    @property
    def total_market_value(self) -> float:
        return float(sum(v.close_value for v in self.position_dict.values()))

    @property
    def total_cost_value(self) -> float:
        return float(sum(i.cost_value for i in self.position_dict.values()))

    @property
    def position_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.position_dict.values())  # type: ignore

    def set_position_close_price(self, close_price_dict: Dict[str, float]):
        """Set position close price.

        Parameters
        ----------
        close_price_dict : dict
            dict of symbol and close price
        """
        self.close_price_dict = close_price_dict
        for k, v in self.position_dict.items():
            v.close_price = close_price_dict[k]

    def match_order_if_possible(
        self,
        matched_at: datetime,
        symbol: str,
        volume: float,
        price: float,
    ):
        """Buy/Sell with enough cash/position. skip if price is invalid (<=0,
        NaN). Volume don't need to be rounded to 100.

        Parameters
        ----------
        matched_at: datetime
            matched datetime
        symbol: str
            symbol
        volume: float
            Volume positive for buy and negative for sell (Volume don't need to be rounded to 100).
        price: float
            price
        """
        # return if 0, negative, nan
        if not price > 0:
            return

        if volume > 0:
            # buy with enough cash
            can_buy_volume = float(
                Decimal(str(self.cash))
                / Decimal(str(price))
                / Decimal(str(self.ratio_commission))
            )  # fix for floating point error
            volume = min(volume, can_buy_volume)
        elif volume < 0:
            # sell with enough volume
            if symbol in self.position_dict:
                volume = max(volume, -self.position_dict[symbol].volume)
            else:
                return

        volume = utils.round_down(volume, base=100.0)

        if volume == 0.0:
            return

        return self.match_order(
            matched_at=matched_at,
            symbol=symbol,
            volume=volume,
            price=price,
        )

    def match_order(
        self,
        matched_at: datetime,
        symbol: str,
        volume: float,
        price: float,
    ):
        # Create trade
        trade = SETTrade(
            matched_at=matched_at,
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

        # Add/Remove SETPosition
        if symbol not in self.position_dict:
            self.position_dict[symbol] = SETPosition(symbol=symbol)
        self.position_dict[symbol].match_order(volume=volume, price=price)
        if self.position_dict[symbol].volume == 0:
            del self.position_dict[symbol]

        return trade
