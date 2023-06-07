import string
from functools import lru_cache

import numpy as np
import pandas as pd
import pytest
import yfinance as yf
from pandas.testing import assert_series_equal

from ezyquant import SETSignalCreator
from ezyquant import indicators as ind
from ezyquant import validators as vld
from ezyquant.errors import InputError

nan = float("nan")
series_empty = pd.Series([], dtype=float)


def make_random_df(n_row: int = 1, n_col: int = 1):
    df = pd.DataFrame(
        np.random.rand(n_row, n_col),
        columns=list(string.ascii_uppercase)[:n_col],
        index=pd.date_range(start="2000-01-01", periods=n_row),
    )
    df[df < 0.5] = np.nan
    return df


@lru_cache
def make_aapl_df():
    df = yf.download("AAPL", start="2020-01-01", end="2020-12-31", progress=False)
    df["Close"] = df["Adj Close"]
    return df


class TestTa:
    _check = staticmethod(vld.check_df_symbol_daily)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_sma(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.sma(df1, 10)

        # Check
        self._check(result)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_ema(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.ema(df1)

        # Check
        self._check(result)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_macd(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.macd(df1)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("n_row", [2, 20])
    @pytest.mark.parametrize("n_col", [2, 20])
    def test_adx(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)
        df3 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.adx(df1, df2, df3, window=n_row // 2)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_cci(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)
        df3 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.cci(df1, df2, df3)

        # Check
        self._check(result)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_ichimoku(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.ichimoku(df1, df2)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_psar(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)
        df3 = make_random_df(n_row=n_row, n_col=n_col)
        # Test
        result = SETSignalCreator.ta.psar(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_rsi(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.rsi(df1)

        # Check
        self._check(result)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_rsi_divergence(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.rsi_divergence(df1)

        # Check
        self._check(result)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_sto(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)
        df3 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.sto(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_roc(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.roc(df1)

        # Check
        self._check(result)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_atr(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)
        df3 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.atr(df1, df2, df3, window=n_row)

        # Check
        self._check(result)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_bb(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.bb(df1)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("n_row", [1, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_dc(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)
        df3 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.dc(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("n_row", [10, 20])
    @pytest.mark.parametrize("n_col", [1, 20])
    def test_kc(self, n_row: int, n_col: int):
        # Mock
        df1 = make_random_df(n_row=n_row, n_col=n_col)
        df2 = make_random_df(n_row=n_row, n_col=n_col)
        df3 = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.kc(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)


class TestTaEmpty:
    _check = staticmethod(vld.check_df_symbol_daily)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_sma(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.sma(df, 10)

        # Check
        self._check(result)
        assert result.empty

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_ema(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        result = SETSignalCreator.ta.ema(df)

        # Check
        self._check(result)
        assert result.empty

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_macd(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.macd(df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_adx(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.adx(df, df, df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_cci(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.cci(df, df, df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_ichimoku(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.ichimoku(df, df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_psar(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.psar(df, df, df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_rsi(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.rsi(df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_sto(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.sto(df, df, df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_roc(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.roc(df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_atr(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.atr(df, df, df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_bb(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.bb(df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_dc(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.dc(df, df, df)

    @pytest.mark.parametrize(("n_row", "n_col"), [(0, 0), (0, 1), (1, 0)])
    def test_kc(self, n_row: int, n_col: int):
        # Mock
        df = make_random_df(n_row=n_row, n_col=n_col)

        # Test
        with pytest.raises(InputError):
            SETSignalCreator.ta.kc(df, df, df)


@pytest.mark.parametrize(
    "data, expected",
    [
        # No data
        (series_empty, series_empty),
        # One data
        (pd.Series([1.0]), series_empty),
        # Data increasing
        (pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), series_empty),
        (pd.Series([1.0, 1.0, 2.0, 2.0, 3.0, 3.0]), series_empty),
        # Data decreasing
        (pd.Series([5.0, 4.0, 3.0, 2.0, 1.0]), series_empty),
        (pd.Series([3.0, 3.0, 2.0, 2.0, 1.0, 1.0]), series_empty),
        # Pivot edge
        (pd.Series([1.0, 2.0, 3.0, 4.0, 3.0]), series_empty),
        (pd.Series([3.0, 4.0, 3.0, 2.0, 1.0]), series_empty),
        # Data same
        (pd.Series([1.0, 1.0, 1.0, 1.0, 1.0]), series_empty),
        # Pivot low
        (pd.Series([3.0, 2.0, 1.0, 2.0, 3.0]), series_empty),
        # Pivot high
        (pd.Series([1.0, 2.0, 3.0, 2.0, 1.0]), pd.Series({2: 3.0})),
        # Two same pivots
        (pd.Series([1.0, 1.0, 2.0, 2.0, 1.0, 1.0]), pd.Series({3: 2.0})),
        (pd.Series([1.0, 1.0, 2.0, 1.0, 2.0, 1.0, 1.0]), pd.Series({4: 2.0})),
        # Two pivots high
        (
            pd.Series([1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0, 2.0, 1.0]),
            pd.Series({2: 3.0, 6: 3.0}),
        ),
    ],
)
def test_pivot_points_high(data, expected):
    # Test
    actual = ind.pivot_points_high(data, 2, 2)

    # Check
    assert_series_equal(actual.dropna(), expected)


def test_rsi_divergence():
    # Mock
    data = make_aapl_df()

    # Test
    actual = ind.rsi_divergence(close=data["Close"])

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
    actual = ind._divergence(price_pivot=price_pivot, indicator=indicator, bullish=True)

    # Check
    assert_series_equal(actual, expected)
