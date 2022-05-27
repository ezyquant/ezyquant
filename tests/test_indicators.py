import string

import numpy as np
import pandas as pd
import pytest
import utils

from ezyquant import SETSignalCreator


def make_random_df(n_row=100, n_col=4):
    df = pd.DataFrame(
        np.random.rand(n_row, n_col),
        columns=list(string.ascii_uppercase[:n_col]),
        index=pd.date_range(start="2000-01-01", periods=n_row),
    )
    df[df < 0.5] = np.nan
    return df


class TestTA:
    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_sma(self, df_func):
        # Mock
        df1 = df_func()

        # Test
        result = SETSignalCreator.ta.sma(df1, 10)

        # Check
        self._check(result)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_ema(self, df_func):
        # Mock
        df1 = df_func()

        # Test
        result = SETSignalCreator.ta.ema(df1)

        # Check
        self._check(result)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_macd(self, df_func):
        # Mock
        df1 = df_func()

        # Test
        result = SETSignalCreator.ta.macd(df1)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_adx(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()

        # Test
        result = SETSignalCreator.ta.adx(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_cci(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()

        # Test
        result = SETSignalCreator.ta.cci(df1, df2, df3)

        # Check
        self._check(result)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_ichimoku(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()

        # Test
        result = SETSignalCreator.ta.ichimoku(df1, df2)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_psar(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()
        # Test
        result = SETSignalCreator.ta.psar(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_rsi(self, df_func):
        # Mock
        df1 = df_func()

        # Test
        result = SETSignalCreator.ta.rsi(df1)

        # Check
        self._check(result)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_sto(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()

        # Test
        result = SETSignalCreator.ta.sto(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_roc(self, df_func):
        # Mock
        df1 = df_func()

        # Test
        result = SETSignalCreator.ta.roc(df1)

        # Check
        self._check(result)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_atr(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()

        # Test
        result = SETSignalCreator.ta.atr(df1, df2, df3)

        # Check
        self._check(result)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_bb(self, df_func):
        # Mock
        df1 = df_func()

        # Test
        result = SETSignalCreator.ta.bb(df1)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_dc(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()

        # Test
        result = SETSignalCreator.ta.dc(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @pytest.mark.parametrize("df_func", [make_random_df])
    def test_kc(self, df_func):
        # Mock
        df1 = df_func()
        df2 = df_func()
        df3 = df_func()

        # Test
        result = SETSignalCreator.ta.kc(df1, df2, df3)

        # Check
        for i in result:
            self._check(i)

    @staticmethod
    def _check(result: pd.DataFrame):
        utils.check_data_symbol_daily(result)
