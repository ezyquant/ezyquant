import dataclasses as dclass
from typing import Callable, Tuple
from unittest.mock import Mock, call

import pandas as pd
import pandas.api.types as ptypes
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal, assert_series_equal
from pandas.tseries.offsets import BusinessDay

from ezyquant import validators as vld
from ezyquant.backtesting import Context
from ezyquant.backtesting._backtesting import _backtest
from tests import utils

nan = float("nan")

position_columns = ["timestamp", "symbol", "volume", "cost_price", "close_price"]
trade_columns = ["matched_at", "symbol", "volume", "price", "pct_commission"]


@pytest.mark.parametrize("return_volume", [100.0, 100, 101, 101.0, 199, 199.0])
def test_backtest_algorithm(return_volume: float):
    # Mock
    index = pd.bdate_range("2000-01-01", periods=4)

    initial_cash = 1e6
    signal_df = pd.DataFrame(
        [[3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]],
        index=index,
        columns=["A", "B"],
    )
    m = Mock(return_value=return_volume)

    def backtest_algorithm(ctx):
        return m(dclass.replace(ctx))

    close_price_df = pd.DataFrame(
        [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]],  # type: ignore
        index=pd.bdate_range("2000-01-01", periods=5) - BusinessDay(),  # type: ignore
        columns=["A", "B"],
    )
    close_price_df.index.freq = index.freq  # type: ignore
    price_match_df = signal_df.copy()
    pct_buy_slip = 0.0
    pct_sell_slip = 0.0
    pct_commission = 0.0

    # Test
    cash_series, position_df, trade_df = _backtest_and_check(
        initial_cash=initial_cash,
        signal_df=signal_df,
        backtest_algorithm=backtest_algorithm,
        close_price_df=close_price_df,
        price_match_df=price_match_df,
        pct_buy_slip=pct_buy_slip,
        pct_sell_slip=pct_sell_slip,
        pct_commission=pct_commission,
    )

    # Check
    assert m.call_count == 8
    m.assert_has_calls(
        [
            call(
                Context(
                    ts=pd.Timestamp("2000-01-03 00:00:00", freq="B"),
                    symbol="A",
                    signal=3.0,
                    close_price=1.0,
                    volume=0.0,
                    cost_price=nan,
                    cash=1000000.0,
                    total_cost_value=0.0,
                    total_market_value=0.0,
                    port_value=1000000.0,
                )
            ),
            call(
                Context(
                    ts=pd.Timestamp("2000-01-03 00:00:00", freq="B"),
                    symbol="B",
                    signal=4.0,
                    close_price=2.0,
                    volume=0.0,
                    cost_price=nan,
                    cash=1000000.0,
                    total_cost_value=0.0,
                    total_market_value=0.0,
                    port_value=1000000.0,
                )
            ),
            call(
                Context(
                    ts=pd.Timestamp("2000-01-04 00:00:00", freq="B"),
                    symbol="A",
                    signal=5.0,
                    close_price=3.0,
                    volume=100.0,
                    cost_price=3.0,
                    cash=999300.0,
                    total_cost_value=700.0,
                    total_market_value=700.0,
                    port_value=1000000.0,
                )
            ),
            call(
                Context(
                    ts=pd.Timestamp("2000-01-04 00:00:00", freq="B"),
                    symbol="B",
                    signal=6.0,
                    close_price=4.0,
                    volume=100.0,
                    cost_price=4.0,
                    cash=999300.0,
                    total_cost_value=700.0,
                    total_market_value=700.0,
                    port_value=1000000.0,
                )
            ),
            call(
                Context(
                    ts=pd.Timestamp("2000-01-05 00:00:00", freq="B"),
                    symbol="A",
                    signal=7.0,
                    close_price=5.0,
                    volume=200.0,
                    cost_price=4.0,
                    cash=998200.0,
                    total_cost_value=1800.0,
                    total_market_value=2200.0,
                    port_value=1000400.0,
                )
            ),
            call(
                Context(
                    ts=pd.Timestamp("2000-01-05 00:00:00", freq="B"),
                    symbol="B",
                    signal=8.0,
                    close_price=6.0,
                    volume=200.0,
                    cost_price=5.0,
                    cash=998200.0,
                    total_cost_value=1800.0,
                    total_market_value=2200.0,
                    port_value=1000400.0,
                )
            ),
            call(
                Context(
                    ts=pd.Timestamp("2000-01-06 00:00:00", freq="B"),
                    symbol="A",
                    signal=9.0,
                    close_price=7.0,
                    volume=300.0,
                    cost_price=5.0,
                    cash=996700.0,
                    total_cost_value=3300.0,
                    total_market_value=4500.0,
                    port_value=1001200.0,
                )
            ),
            call(
                Context(
                    ts=pd.Timestamp("2000-01-06 00:00:00", freq="B"),
                    symbol="B",
                    signal=10.0,
                    close_price=8.0,
                    volume=300.0,
                    cost_price=6.0,
                    cash=996700.0,
                    total_cost_value=3300.0,
                    total_market_value=4500.0,
                    port_value=1001200.0,
                )
            ),
        ]
    )

    assert_series_equal(
        cash_series,
        pd.Series([999300.0, 998200.0, 996700.0, 994800.0], index=index),
    )
    assert_frame_equal(
        position_df,
        pd.DataFrame(
            [
                [pd.Timestamp("2000-01-03"), "A", 100.0, 3.0, 3.0],
                [pd.Timestamp("2000-01-03"), "B", 100.0, 4.0, 4.0],
                [pd.Timestamp("2000-01-04"), "A", 200.0, 4.0, 5.0],
                [pd.Timestamp("2000-01-04"), "B", 200.0, 5.0, 6.0],
                [pd.Timestamp("2000-01-05"), "A", 300.0, 5.0, 7.0],
                [pd.Timestamp("2000-01-05"), "B", 300.0, 6.0, 8.0],
                [pd.Timestamp("2000-01-06"), "A", 400.0, 6.0, 9.0],
                [pd.Timestamp("2000-01-06"), "B", 400.0, 7.0, 10.0],
            ],
            columns=position_columns,
        ),
    )
    assert_frame_equal(
        trade_df,
        pd.DataFrame(
            [
                [pd.Timestamp("2000-01-03"), "A", 100.0, 3.0, 0.0],
                [pd.Timestamp("2000-01-03"), "B", 100.0, 4.0, 0.0],
                [pd.Timestamp("2000-01-04"), "A", 100.0, 5.0, 0.0],
                [pd.Timestamp("2000-01-04"), "B", 100.0, 6.0, 0.0],
                [pd.Timestamp("2000-01-05"), "A", 100.0, 7.0, 0.0],
                [pd.Timestamp("2000-01-05"), "B", 100.0, 8.0, 0.0],
                [pd.Timestamp("2000-01-06"), "A", 100.0, 9.0, 0.0],
                [pd.Timestamp("2000-01-06"), "B", 100.0, 10.0, 0.0],
            ],
            columns=trade_columns,
        ),
    )


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
        "backtest_algorithm",
        [
            lambda ctx: ctx.target_pct_port(ctx.signal),
            lambda ctx: 100.0,
        ],
    )
    def test_no_price(
        self,
        backtest_algorithm: Callable,
        price_match_df: pd.DataFrame,
        pct_buy_slip: float,
        pct_sell_slip: float,
        pct_commission: float,
    ):
        self._test(
            price_match_df=price_match_df,
            backtest_algorithm=backtest_algorithm,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

    @pytest.mark.parametrize("backtest_algorithm", [lambda ctx: 0, lambda ctx: nan])
    def test_backtest_algorithm(
        self,
        backtest_algorithm: Callable,
        pct_buy_slip: float,
        pct_sell_slip: float,
        pct_commission: float,
    ):
        self._test(
            backtest_algorithm=backtest_algorithm,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

    def _test(
        self,
        initial_cash: float = 1000.0,
        signal_df: pd.DataFrame = utils.make_signal_weight_df(),
        backtest_algorithm: Callable = lambda ctx: ctx.target_pct_port(ctx.signal),
        close_price_df: pd.DataFrame = utils.make_close_price_df(),
        price_match_df: pd.DataFrame = utils.make_price_df(),
        pct_buy_slip: float = 0.0,
        pct_sell_slip: float = 0.0,
        pct_commission: float = 0.0,
    ):
        # Test
        cash_series, position_df, trade_df = _backtest_and_check(
            initial_cash=initial_cash,
            signal_df=signal_df,
            backtest_algorithm=backtest_algorithm,
            close_price_df=close_price_df,
            price_match_df=price_match_df,
            pct_buy_slip=pct_buy_slip,
            pct_sell_slip=pct_sell_slip,
            pct_commission=pct_commission,
        )

        # Check
        assert (cash_series == initial_cash).all()
        assert position_df.empty
        assert trade_df.empty


@pytest.mark.parametrize("initial_cash", [1e3, 1e6])
@pytest.mark.parametrize(
    ("signal_df", "backtest_algorithm"),
    [
        (
            utils.make_signal_weight_df(n_row=1000, n_col=100),
            lambda ctx: ctx.target_pct_port(ctx.signal),
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
    backtest_algorithm: Callable,
    close_price_df: pd.DataFrame,
    price_match_df: pd.DataFrame,
    pct_buy_slip: float,
    pct_sell_slip: float,
    pct_commission: float,
):
    _backtest_and_check(
        initial_cash=initial_cash,
        signal_df=signal_df,
        backtest_algorithm=backtest_algorithm,
        close_price_df=close_price_df,
        price_match_df=price_match_df,
        pct_buy_slip=pct_buy_slip,
        pct_sell_slip=pct_sell_slip,
        pct_commission=pct_commission,
    )


def _backtest_and_check(
    initial_cash: float,
    signal_df: pd.DataFrame,
    backtest_algorithm: Callable[[Context], float],
    close_price_df: pd.DataFrame,
    price_match_df: pd.DataFrame,
    pct_buy_slip: float,
    pct_sell_slip: float,
    pct_commission: float,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    # Test
    cash_series, position_df, trade_df = _backtest(
        initial_cash=initial_cash,
        signal_df=signal_df,
        backtest_algorithm=backtest_algorithm,
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

    return cash_series, position_df, trade_df


def _check_cash_series(series):
    assert isinstance(series, pd.Series)

    # Index
    vld.check_df_index_daily(series)

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
        assert ptypes.is_float_dtype(df["cost_price"])


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
