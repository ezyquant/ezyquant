import operator

import pandas as pd
from ta.momentum import rsi

from ezyquant.indicators import zigzag


def rsi_divergence(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    rsi_period: int = 14,
    pivot_up_thresh: float = 0.05,
    pivot_down_thresh: float = -0.05,
) -> pd.Series:
    """Return Positive RSI of the bullish divergence points and Negative RSI of the
    bearish divergence points.

    Parameters
    ----------
    high : pd.Series
        Series of 'high' prices.
    low : pd.Series
        Series of 'low' prices.
    close : pd.Series
        Series of 'close' prices.
    rsi_period : int, optional
        RSI period, by default 14
    pivot_up_thresh : float
        Pivot up threshold, by default 0.05
    pivot_down_thresh : float
        Pivot down threshold, by default -0.05
    """
    # Calculate RSI
    rsi_ = rsi(close, window=rsi_period)

    # Calculate pivot points using zigzag
    zz_ = zigzag.peak_valley_pivots_candlestick(
        close=close,
        high=high,
        low=low,
        up_thresh=pivot_up_thresh,
        down_thresh=pivot_down_thresh,
    )
    close_pl = close[zz_ < 0]
    close_ph = close[zz_ > 0]

    # Calculate Divergence
    bullish = _divergence(close_pl, rsi_, bullish=True)
    bearish = _divergence(close_ph, rsi_, bullish=False)

    return bullish.fillna(-bearish)


def _divergence(
    price_pivot: pd.Series, indicator: pd.Series, bullish: bool = True
) -> pd.Series:
    """Divergence.

    Parameters
    ----------
    price_pivot : pd.Series
        Price pivot points. low for bullish divergence and high for bearish divergence.
    indicator : pd.Series
        indicator series.
    bullish : bool, optional
        bullish or bearish divergence, by default True

    Returns
    -------
    pd.Series
        Divergence series. Not NaN when divergence occurs.
    """
    indicator_pivot = indicator[price_pivot.index]

    op = operator.lt if bullish else operator.gt

    return indicator.where(
        op(price_pivot, price_pivot.shift(1))
        & op(indicator_pivot.shift(1), indicator_pivot)
    )
