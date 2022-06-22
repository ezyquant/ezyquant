from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import Dict, List, Optional

import pandas as pd

from .. import utils
from .position import Position
from .trade import Trade


@dataclass
class SETAccount:
    cash: float
    pct_commission: float = 0.0
    position_dict: Dict[str, Position] = field(default_factory=dict)
    trade_list: List[Trade] = field(default_factory=list)
    market_price_dict: Dict[str, float] = field(default_factory=dict, repr=False)
    selected_symbol: Optional[str] = None  # select symbol for buy/sell method

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

        self.ratio_commission = 1.0 + self.pct_commission

    @property
    def port_value(self) -> float:
        return self.total_market_value + self.cash

    @cached_property
    def total_market_value(self) -> float:
        return float(
            sum(
                v.volume * self.market_price_dict[v.symbol]
                for v in self.position_dict.values()
                if pd.notna(self.market_price_dict[v.symbol])
            )
        )

    @property
    def total_cost_value(self) -> float:
        return sum(i.cost_value for i in self.position_dict.values())

    @property
    def position_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.position_dict.values())  # type: ignore

    """
    Buy/Sell
    """

    def has_position(self, symbol: str) -> bool:
        return symbol in self.position_dict

    @property
    def _price(self) -> float:
        """Get last close price of selected symbol."""
        assert self.selected_symbol is not None, "symbol must be selected"
        return self.market_price_dict[self.selected_symbol]

    @property
    def _volume(self) -> float:
        """Get volume of selected symbol."""
        assert self.selected_symbol is not None, "symbol must be selected"
        if self.selected_symbol in self.position_dict:
            return self.position_dict[self.selected_symbol].volume
        else:
            return 0.0

    def buy_pct_port(self, pct_port: float) -> float:
        """Calculate buy volume from percentage of SETAccount. Using last close
        price. Symbol must be selected.

        Parameters
        ----------
        pct_port : float
            percentage of SETAccount

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return self.buy_value(self.port_value * pct_port)

    def buy_value(self, value: float) -> float:
        """Calculate buy volume from value. Using last close price. Symbol must
        be selected.

        Parameters
        ----------
        value : float
            value

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return value / self._price

    def buy_pct_position(self, pct_position: float) -> float:
        """Calculate buy volume from percentage of current position. Symbol
        must be selected.

        Parameters
        ----------
        pct_position : float
            percentage of position

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return pct_position * self._volume

    def sell_pct_port(self, pct_port: float) -> float:
        """Calculate sell volume from percentage of SETAccount. Using last
        close price. Symbol must be selected.

        Parameters
        ----------
        pct_port : float
            percentage of SETAccount

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return self.buy_pct_port(-pct_port)

    def sell_value(self, value: float) -> float:
        """Calculate sell volume from value. Using last close price. Symbol
        must be selected.

        Parameters
        ----------
        value : float
            value

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return self.buy_value(-value)

    def sell_pct_position(self, pct_position: float) -> float:
        """Calculate sell volume from percentage of current position. Symbol
        must be selected.

        Parameters
        ----------
        pct_position : float
            percentage of position

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return self.buy_pct_position(-pct_position)

    def target_pct_port(self, pct_port: float) -> float:
        """Calculate buy/sell volume to make position reach percentage of
        SETAccount. Using last close price. Symbol must be selected.

        Parameters
        ----------
        pct_port : float
            percentage of SETAccount

        Returns
        -------
        float
            buy/sell volume, not round 100
        """
        return self.buy_pct_port(pct_port) - self._volume

    def target_value(self, value: float) -> float:
        """Calculate buy/sell volume to make position reach value. Symbol must
        be selected.

        Parameters
        ----------
        value : float
            value

        Returns
        -------
        float
            buy/sell volume, not round 100
        """
        return self.buy_value(value) - self._volume

    """
    Protected methods
    """

    def _set_market_price_dict(self, market_price_dict: Dict[str, float]) -> None:
        """Set market price dict.

        Parameters
        ----------
        market_price_dict : dict
            dict of symbol and last close price
        """
        self._cache_clear()
        self.market_price_dict = market_price_dict

    def _match_order_if_possible(
        self,
        matched_at: datetime,
        symbol: str,
        volume: float,
        price: float,
    ):
        """Buy/Sell with enough cash/position. skip if price is invalid (<=0,
        NaN). Volume don't need to round 100.

        Parameters
        ----------
        matched_at : datetime
            matched datetime
        symbol : str
            symbol
        volume : float
            volume, don't need round 100, positive for buy, negative for sell
        price : float
            price
        """
        # return if 0, negative, nan
        if not price > 0:
            return

        if volume > 0:
            # buy with enough cash
            can_buy_volume = (
                self.cash / price / self.ratio_commission + 1e-10
            )  # fix for floating point error
            volume = min(volume, can_buy_volume)
        elif volume < 0:
            # sell with enough volume
            if symbol in self.position_dict:
                volume = max(volume, -self.position_dict[symbol].volume)
            else:
                return

        volume = utils.round_100(volume)

        if volume == 0.0:
            return

        return self._match_order(
            matched_at=matched_at,
            symbol=symbol,
            volume=volume,
            price=price,
        )

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

    def _cache_clear(self):
        if "total_market_value" in self.__dict__:
            del self.__dict__["total_market_value"]
