from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .position import Position
from .trade import Trade


@dataclass
class Portfolio:
    cash: float
    pct_commission: float = 0.0
    position_dict: Dict[str, Position] = field(default_factory=dict)
    trade_list: List[Trade] = field(default_factory=list)
    market_price_series: pd.Series = field(default_factory=pd.Series)
    selected_symbol: Optional[str] = None  #  select symbol for buy/sell method

    def __post_init__(self) -> None:
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
    def port_value(self) -> float:
        return self.total_market_value + self.cash

    @property
    def total_market_value(self) -> float:
        return (self.volume_series * self.market_price_series).sum()

    @property
    def total_cost_value(self) -> float:
        return sum(i.cost_value for i in self.position_dict.values())

    @property
    def volume_series(self) -> pd.Series:
        return pd.Series(
            {k: v.volume for k, v in self.position_dict.items()}, dtype="float64"
        )

    @property
    def position_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.position_dict.values())  # type: ignore

    """
    Buy/Sell
    """

    def has_position(self, symbol: str) -> bool:
        return symbol in self.position_dict

    @property
    def price(self) -> float:
        """Get last close price of selected symbol"""
        assert self.selected_symbol is not None, "symbol must be selected"
        return self.market_price_series[self.selected_symbol]

    @property
    def volume(self) -> float:
        """Get volume of selected symbol"""
        assert self.selected_symbol is not None, "symbol must be selected"
        if self.has_position(self.selected_symbol):
            return self.position_dict[self.selected_symbol].volume
        else:
            return 0.0

    def buy_pct_port(self, pct_port: float) -> float:
        """Calculate buy volume from percentage of portfolio.
        Using last close price.

        Parameters
        ----------
        pct_port : float
            percentage of portfolio

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return self.buy_value(self.port_value * pct_port)

    def buy_value(self, value: float) -> float:
        """Calculate buy volume from value.
        Using last close price.

        Parameters
        ----------
        value : float
            value

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return value / self.price

    def buy_pct_position(self, pct_position: float) -> float:
        """Calculate buy volume from percentage of current position.

        Parameters
        ----------
        pct_position : float
            percentage of position

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return pct_position * self.volume

    def sell_pct_port(self, pct_port: float) -> float:
        """Calculate sell volume from percentage of portfolio.
        Using last close price.

        Parameters
        ----------
        pct_port : float
            percentage of portfolio

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return -self.buy_pct_port(pct_port)

    def sell_value(self, value: float) -> float:
        """Calculate sell volume from value.
        Using last close price.

        Parameters
        ----------
        value : float
            value

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return -self.buy_value(value)

    def sell_pct_position(self, pct_position: float) -> float:
        """Calculate sell volume from percentage of current position.

        Parameters
        ----------
        pct_position : float
            percentage of position

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return -self.buy_pct_position(pct_position)

    def target_pct_port(self, pct_port: float) -> float:
        """Calculate buy/sell volume to make position reach percentage of portfolio.
        Using last close price.

        Parameters
        ----------
        pct_port : float
            percentage of portfolio

        Returns
        -------
        float
            buy/sell volume, not round 100
        """
        return self.buy_pct_port(pct_port) - self.volume

    def target_value(self, value: float) -> float:
        """Calculate buy/sell volume to make position reach value.
        Parameters
        ----------
        value : float
            value

        Returns
        -------
        float
            buy/sell volume, not round 100
        """
        return self.buy_value(value) - self.volume

    def _match_order(
        self,
        matched_at: datetime,
        symbol: str,
        volume: float,
        price: float,
    ):
        # Create trade
        trade = Trade(
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

        # Add/Remove Position
        if symbol not in self.position_dict:
            self.position_dict[symbol] = Position(symbol=symbol)
        self.position_dict[symbol]._match_order(volume=volume, price=price)
        if self.position_dict[symbol].volume == 0:
            del self.position_dict[symbol]

        return trade
