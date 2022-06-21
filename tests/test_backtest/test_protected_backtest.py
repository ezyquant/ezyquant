from typing import Callable, Optional

import pandas as pd
import pandas.api.types as ptypes
import pytest
import utils
from pandas.testing import assert_index_equal, assert_series_equal

from ezyquant.backtest._backtest import _backtest

nan = float("nan")

position_columns = ["timestamp", "symbol", "volume", "avg_cost_price"]
trade_columns = ["matched_at", "symbol", "volume", "price", "pct_commission"]


class TestProtectedBacktest:
    def _test(self):
        # TODO: TestProtectedBacktest
        pass


@pytest.mark.parametrize("pct_buy_slip", [0.0, 0.1])
@pytest.mark.parametrize("pct_sell_slip", [0.0, 0.1])
@pytest.mark.parametrize("pct_commission", [0.0, 0.1])
class TestNoTrade:
    @pytest.mark.parametrize(("initial_cash"), [0.0, 1.0])
    def test_no_cash(
        self,
        initial_cash: float,
        pct_buy_slip: float,
        pct_sell_slip: float,
        pct_commission: float,
    ):
        self._test(
            initial_cash=initial_cash,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

    @pytest.mark.parametrize(
        "signal_df", [utils.make_data_df(0), utils.make_data_df(nan)]
    )
    def test_no_signal(
        self,
        signal_df: pd.DataFrame,
        pct_buy_slip: float,
        pct_sell_slip: float,
        pct_commission: float,
    ):
        self._test(
            signal_df=signal_df,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

    @pytest.mark.parametrize(
        "price_match_df", [utils.make_data_df(0), utils.make_data_df(nan)]
    )
    @pytest.mark.parametrize(
        "apply_trade_volume",
        [lambda ts, sym, sig, price, acct: acct.target_pct_port(sig), lambda *args: 100.0],
    )
    def test_no_price(
        self,
        apply_trade_volume: Callable,
        price_match_df: pd.DataFrame,
        pct_buy_slip: float,
        pct_sell_slip: float,
        pct_commission: float,
    ):
        self._test(
            price_match_df=price_match_df,
            apply_trade_volume=apply_trade_volume,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

    @pytest.mark.parametrize("apply_trade_volume", [lambda *args: 0, lambda *args: nan])
    def test_apply_trade_volume(
        self,
        apply_trade_volume: Callable,
        pct_buy_slip: float,
        pct_sell_slip: float,
        pct_commission: float,
    ):
        self._test(
            apply_trade_volume=apply_trade_volume,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

    def _test(
        self,
        initial_cash: float = 1000.0,
        signal_df: pd.DataFrame = utils.make_signal_weight_df(),
        apply_trade_volume: Callable = lambda ts, sym, sig, price, acct: acct.target_pct_port(
            sig
        ),
        close_price_df: pd.DataFrame = utils.make_close_price_df(),
        price_match_df: pd.DataFrame = utils.make_price_df(),
        pct_buy_slip: float = 0.0,
        pct_sell_slip: float = 0.0,
        pct_commission: float = 0.0,
    ):
        # Test
        cash_series, position_df, trade_df = _backtest(
            initial_cash=initial_cash,
            signal_df=signal_df,
            apply_trade_volume=apply_trade_volume,
            close_price_df=close_price_df,
            price_match_df=price_match_df,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

        # Check
        # cash_series
        _check_cash_series(cash_series)
        assert_index_equal(price_match_df.index, cash_series.index)
        assert (cash_series == initial_cash).all()

        # position_df
        _check_position_df(position_df)
        assert position_df.empty

        # trade_df
        _check_trade_df(trade_df)
        assert trade_df.empty


@pytest.mark.parametrize("initial_cash", [1e3, 1e6])
@pytest.mark.parametrize(
    ("signal_df", "apply_trade_volume"),
    [
        (
            utils.make_signal_weight_df(n_row=1000, n_col=100),
            lambda ts, sym, sig, price, acct: acct.target_pct_port(sig),
        )
    ],
)
@pytest.mark.parametrize(
    "close_price_df", [utils.make_close_price_df(n_row=1000, n_col=100)]
)
@pytest.mark.parametrize("price_match_df", [utils.make_price_df(n_row=1000, n_col=100)])
@pytest.mark.parametrize("pct_buy_slip", [0.0, 0.1])
@pytest.mark.parametrize("pct_sell_slip", [0.0, 0.1])
@pytest.mark.parametrize("pct_commission", [0.0, 0.0025, 0.1])
def test_random_input(
    initial_cash: float,
    signal_df: pd.DataFrame,
    apply_trade_volume: Callable,
    close_price_df: pd.DataFrame,
    price_match_df: pd.DataFrame,
    pct_buy_slip: float,
    pct_sell_slip: float,
    pct_commission: float,
):
    # Test
    cash_series, position_df, trade_df = _backtest(
        initial_cash=initial_cash,
        signal_df=signal_df,
        apply_trade_volume=apply_trade_volume,
        close_price_df=close_price_df,
        price_match_df=price_match_df,
        pct_buy_slip=pct_buy_slip,
        pct_sell_slip=pct_sell_slip,
        pct_commission=pct_commission,
    )

    # Check
    # cash_series
    _check_cash_series(cash_series)
    assert_index_equal(price_match_df.index, cash_series.index)

    # position_df
    _check_position_df(position_df)

    # trade_df
    _check_trade_df(trade_df)


def _check_cash_series(series):
    assert isinstance(series, pd.Series)

    # Index
    utils.check_index_daily(series.index)

    # Data type
    assert ptypes.is_float_dtype(series)

    # Cash
    assert (series >= 0).all()

    assert not series.empty


def _check_position_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(position_columns))

    # Data type
    assert ptypes.is_datetime64_any_dtype(df["timestamp"])
    if not df.empty:
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["avg_cost_price"])


def _check_trade_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(trade_columns))

    # Data type
    assert ptypes.is_datetime64_any_dtype(df["matched_at"])
    if not df.empty:
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["price"])
        assert ptypes.is_float_dtype(df["pct_commission"])
