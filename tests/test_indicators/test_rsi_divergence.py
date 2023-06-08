from functools import lru_cache

import pandas as pd
import pytest
import yfinance as yf
from pandas.testing import assert_series_equal

from ezyquant.indicators.rsi_divergence import _divergence, rsi_divergence

nan = float("nan")
series_empty = pd.Series([], dtype=float)


@lru_cache
def make_aapl_df():
    df = yf.download("AAPL", start="2020-01-01", end="2020-12-31", progress=False)
    df["Close"] = df["Adj Close"]
    return df


def test_rsi_divergence():
    # Mock
    data = make_aapl_df()

    # Test
    actual = rsi_divergence(high=data["High"], low=data["Low"], close=data["Close"])

    # Check
    print(actual.dropna())


@pytest.mark.parametrize(
    "price_pivot, indicator, expected",
    [
        # No data
        (series_empty, series_empty, series_empty),
        # No divergence
        (
            pd.Series([1, 2, 3]),
            pd.Series([1, 2, 3]),
            pd.Series([nan, nan, nan]),
        ),
        (
            pd.Series([3, 2, 1]),
            pd.Series([3, 2, 1]),
            pd.Series([nan, nan, nan]),
        ),
        (
            pd.Series([1, 2]),
            pd.Series([2, 1]),
            pd.Series([nan, nan]),
        ),
        # Divergence
        (
            pd.Series([2, 1]),
            pd.Series([1, 2]),
            pd.Series([nan, 2]),
        ),
        # Divergence with skip price
        (
            pd.Series({0: 2, 2: 1}),
            pd.Series([1, 99, 2]),
            pd.Series([nan, nan, 2]),
        ),
    ],
)
def test_divergence(price_pivot: pd.Series, indicator: pd.Series, expected: pd.Series):
    # Test
    actual = _divergence(price_pivot=price_pivot, indicator=indicator, bullish=True)

    # Check
    assert_series_equal(actual, expected)
