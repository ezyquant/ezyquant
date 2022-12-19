from dataclasses import dataclass
from typing import Any

import pandas as pd

nan = float("nan")


@dataclass
class Context:
    """
    Context class for backtest.
    """

    ts: pd.Timestamp
    """Current timestamp"""
    symbol: str = ""
    """Selected symbol"""
    signal: Any = nan
    """Signal"""
    close_price: float = nan
    """Close price"""
    volume: float = nan
    """Current Volume"""
    cost_price: float = nan
    """Cost price"""

    cash: float = nan
    """Available cash"""
    total_cost_value: float = nan
    """Sum of all stock market value in portfolio"""
    total_market_value: float = nan
    """Sum of all stock cost value in portfolio"""
    port_value: float = nan
    """Total portfolio value"""

    def buy_pct_port(self, pct_port: float) -> float:
        """Calculate buy volume from the percentage of the portfolio.

        Parameters
        ----------
        pct_port: float
            percentage of the portfolio

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return self.buy_value(self.port_value * pct_port)

    def buy_value(self, value: float) -> float:
        """Calculate buy volume from the given value.

        Parameters
        ----------
        value: float
            value

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return value / self.close_price

    def buy_pct_position(self, pct_position: float) -> float:
        """Calculate buy volume from the percentage of the current position.

        Parameters
        ----------
        pct_position: float
            percentage of position

        Returns
        -------
        float
            buy volume, always positive, not round 100
        """
        return pct_position * self.volume

    def sell_pct_port(self, pct_port: float) -> float:
        """Calculate sell volume from the percentage of the portfolio.
        Parameters
        ----------
        pct_port: float
            percentage of the portfolio

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return self.buy_pct_port(-pct_port)

    def sell_value(self, value: float) -> float:
        """Calculate sell volume from the given value.

        Parameters
        ----------
        value: float
            value

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return self.buy_value(-value)

    def sell_pct_position(self, pct_position: float) -> float:
        """Calculate sell volume from the percentage of the current position.

        Parameters
        ----------
        pct_position: float
            percentage of position

        Returns
        -------
        float
            sell volume, always negative, not round 100
        """
        return self.buy_pct_position(-pct_position)

    def target_pct_port(self, pct_port: float) -> float:
        """Calculate buy/sell volume to make the current position reach the target percentage of
        the portfolio.

        Parameters
        ----------
        pct_port: float
            percentage of the portfolio

        Returns
        -------
        float
            buy/sell volume, not round 100
        """
        return self.buy_pct_port(pct_port) - self.volume

    def target_value(self, value: float) -> float:
        """Calculate buy/sell volume to make the current position reach the target value.

        Parameters
        ----------
        value: float
            value

        Returns
        -------
        float
            buy/sell volume, not round 100
        """
        return self.buy_value(value) - self.volume
