import string

import numpy as np
import pandas as pd
import pytest

from ezyquant import SETSignalCreator
from ezyquant import validators as vld
from ezyquant.errors import InputError


def make_random_df(n_row: int = 1, n_col: int = 1):
    df = pd.DataFrame(
        np.random.rand(n_row, n_col),
        columns=list(string.ascii_uppercase)[:n_col],
        index=pd.date_range(start="2000-01-01", periods=n_row),
    )
    df[df < 0.5] = np.nan
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
