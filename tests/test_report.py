from unittest.mock import Mock, PropertyMock

import pandas as pd
import pandas.api.types as ptypes
import pytest
import utils
from pandas.testing import assert_frame_equal, assert_index_equal

import ezyquant.fields as fld
from ezyquant.report import (
    BacktestReport,
    dividend_columns,
    position_columns,
    summary_columns,
    trade_columns,
)

position_in_columns = ["timestamp", "symbol", "volume", "avg_cost_price"]
trade_in_columns = ["timestamp", "symbol", "volume", "price", "pct_commission"]


class TestSummaryDf:
    def setup_method(self, _):
        self.position_df = BacktestReport.position_df
        self.trade_df = BacktestReport.trade_df
        self.dividend_df = BacktestReport.dividend_df

    def teardown_method(self, _):
        BacktestReport.position_df = self.position_df
        BacktestReport.trade_df = self.trade_df
        BacktestReport.dividend_df = self.dividend_df

    @pytest.mark.kwparametrize(
        # Empty
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["timestamp", "commission"]),
            "dividend_df": pd.DataFrame(columns=["pay_date", "amount"]),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Position
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]],
                columns=["timestamp", "close_value"],
            ),
            "trade_df": pd.DataFrame(columns=["timestamp", "commission"]),
            "dividend_df": pd.DataFrame(columns=["pay_date", "amount"]),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 2.0, 2.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Trade
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]], columns=["timestamp", "commission"]
            ),
            "dividend_df": pd.DataFrame(columns=["pay_date", "amount"]),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]],
                columns=summary_columns,
            ),
        },
        # Dividend
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["timestamp", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 2.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Dividend non trade date
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["timestamp", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-02"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 2.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Dividend after cash
        {
            "cash_series": pd.Series({pd.Timestamp("2000-01-03"): 1.0}),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["timestamp", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-04"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]],
                columns=summary_columns,
            ),
        },
        # Cumulative dividend
        {
            "cash_series": pd.Series(
                {pd.Timestamp("2000-01-03"): 1.0, pd.Timestamp("2000-01-04"): 1.0}
            ),
            "position_df": pd.DataFrame(columns=["timestamp", "close_value"]),
            "trade_df": pd.DataFrame(columns=["timestamp", "commission"]),
            "dividend_df": pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), 1.0]], columns=["pay_date", "amount"]
            ),
            "expect_result": pd.DataFrame(
                [
                    [
                        pd.Timestamp("2000-01-03"),
                        2.0,
                        1.0,
                        0.0,
                        1.0,
                        0.0,
                        1.0,
                        1.0,
                        0.0,
                    ],
                    [
                        pd.Timestamp("2000-01-04"),
                        2.0,
                        1.0,
                        0.0,
                        1.0,
                        0.0,
                        0.0,
                        1.0,
                        0.0,
                    ],
                ],
                columns=summary_columns,
            ),
        },
    )
    def test_summary_df(
        self,
        cash_series: pd.Series,
        position_df: pd.DataFrame,
        trade_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        # Mock
        br = BacktestReport(
            initial_capital=0.0,
            pct_commission=0.0,
            pct_buy_slip=0.0,
            pct_sell_slip=0.0,
            cash_series=cash_series,
            position_df=pd.DataFrame(),
            trade_df=pd.DataFrame(),
        )

        BacktestReport.position_df = PropertyMock(return_value=position_df)
        BacktestReport.trade_df = PropertyMock(return_value=trade_df)
        BacktestReport.dividend_df = PropertyMock(return_value=dividend_df)
        br._sdr.get_trading_dates = Mock(return_value=utils.make_bdate_range())

        # Test
        result = br.summary_df

        # Check
        _check_summary_df(result)
        assert_frame_equal(result, expect_result)


@pytest.mark.parametrize(
    "close_price_df",
    [
        utils.make_data_df(
            [[1.0, 4.0, 7.0], [2.0, 5.0, 8.0], [3.0, 6.0, 9.0]], n_col=3, n_row=3
        )
    ],
)
@pytest.mark.parametrize(
    ("position_df", "expect_result"),
    [
        (
            pd.DataFrame(columns=position_in_columns),
            pd.DataFrame(columns=position_columns),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1],
                ],
                columns=position_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0],
                ],
                columns=position_columns,
            ),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1],
                ],
                columns=position_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0],
                    [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1, 2.0, 200.0],
                ],
                columns=position_columns,
            ),
        ),
    ],
)
def test_position_df(
    position_df: pd.DataFrame, close_price_df: pd.DataFrame, expect_result: pd.DataFrame
):
    # Mock
    br = BacktestReport(
        initial_capital=0.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=pd.Series(),
        position_df=position_df,
        trade_df=pd.DataFrame(),
    )
    br._sdr.get_data_symbol_daily = Mock(return_value=close_price_df)

    # Test
    result = br.position_df

    # Check
    _check_position_df(result)
    assert_frame_equal(result, expect_result, check_dtype=False)  # type: ignore


@pytest.mark.parametrize(
    ("trade_df", "expect_result"),
    [
        (
            pd.DataFrame(columns=trade_in_columns),
            pd.DataFrame(columns=trade_columns),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 0.01],
                ],
                columns=trade_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", fld.SIDE_BUY, 100.0, 0.1, 0.1],
                ],
                columns=trade_columns,
            ),
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 0.01],
                    [pd.Timestamp("2000-01-04"), "AAA", -100.0, 0.1, 0.01],
                ],
                columns=trade_in_columns,
            ),
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", fld.SIDE_BUY, 100.0, 0.1, 0.1],
                    [pd.Timestamp("2000-01-04"), "AAA", fld.SIDE_SELL, 100.0, 0.1, 0.1],
                ],
                columns=trade_columns,
            ),
        ),
    ],
)
def test_trade_df(trade_df: pd.DataFrame, expect_result: pd.DataFrame):
    # Mock
    br = BacktestReport(
        initial_capital=0.0,
        pct_commission=0.0,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        cash_series=pd.Series(),
        position_df=pd.DataFrame(),
        trade_df=trade_df,
    )

    # Test
    result = br.trade_df

    # Check
    _check_trade_df(result)
    assert_frame_equal(result, expect_result, check_dtype=False)  # type: ignore


class TestDividendDf:
    def setup_method(self, _):
        self.position_df = BacktestReport.position_df

    def teardown_method(self, _):
        BacktestReport.position_df = self.position_df

    def _test(
        self,
        position_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        # Mock
        br = BacktestReport(
            initial_capital=0.0,
            pct_commission=0.0,
            pct_buy_slip=0.0,
            pct_sell_slip=0.0,
            cash_series=pd.Series(),
            position_df=pd.DataFrame(),
            trade_df=pd.DataFrame(),
        )
        BacktestReport.position_df = PropertyMock(return_value=position_df)
        br._sdr.get_dividend = Mock(return_value=dividend_df)
        br._sdr.get_trading_dates = Mock(return_value=utils.make_bdate_range())

        # Test
        result = br.dividend_df

        # Check
        _check_dividend_df(result)
        assert_frame_equal(result, expect_result, check_dtype=False)  # type: ignore

    @pytest.mark.parametrize(
        "dividend_df",
        [
            pd.DataFrame(
                [["AAA", pd.Timestamp("2000-01-04"), pd.Timestamp("2000-01-05"), 1.0]],
                columns=["symbol", "ex_date", "pay_date", "dps"],
            )
        ],
    )
    @pytest.mark.parametrize(
        ("position_df", "expect_result"),
        [
            (
                pd.DataFrame(columns=["timestamp", "symbol", "volume"]),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [[pd.Timestamp("2000-01-04"), "AAA", 100.0]],
                    columns=["timestamp", "symbol", "volume"],
                ),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [[pd.Timestamp("2000-01-03"), "AAB", 100.0]],
                    columns=["timestamp", "symbol", "volume"],
                ),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [[pd.Timestamp("2000-01-03"), "AAA", 100.0]],
                    columns=["timestamp", "symbol", "volume"],
                ),
                pd.DataFrame(
                    [
                        [
                            pd.Timestamp("2000-01-04"),
                            "AAA",
                            1.0,
                            100.0,
                            100.0,
                            pd.Timestamp("2000-01-03"),
                            pd.Timestamp("2000-01-05"),
                        ]
                    ],
                    columns=dividend_columns,
                ),
            ),
        ],
    )
    def test_position(
        self,
        position_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        self._test(position_df, dividend_df, expect_result)

    @pytest.mark.parametrize(
        "position_df",
        [
            pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), "AAA", 100.0]],
                columns=["timestamp", "symbol", "volume"],
            )
        ],
    )
    @pytest.mark.parametrize(
        ("dividend_df", "expect_result"),
        [
            (
                pd.DataFrame(columns=["symbol", "ex_date", "pay_date", "dps"]),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [
                        [
                            "AAA",
                            pd.Timestamp("2000-01-04"),
                            pd.NaT,
                            1.0,
                        ]
                    ],
                    columns=["symbol", "ex_date", "pay_date", "dps"],
                ),
                pd.DataFrame(
                    [
                        [
                            pd.Timestamp("2000-01-04"),
                            "AAA",
                            1.0,
                            100.0,
                            100.0,
                            pd.Timestamp("2000-01-03"),
                            pd.Timestamp("2000-01-04"),
                        ]
                    ],
                    columns=dividend_columns,
                ),
            ),
        ],
    )
    def test_dividend(
        self,
        position_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        self._test(position_df, dividend_df, expect_result)


def test_stat_df():
    # TODO: test_stat_df
    pass


def test_summary_trade_df():
    # TODO: test_summary_trade_df
    pass


def _check_summary_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(summary_columns))

    # Data type
    assert ptypes.is_datetime64_any_dtype(df["timestamp"])
    assert ptypes.is_float_dtype(df["port_value_with_dividend"])
    assert ptypes.is_float_dtype(df["port_value"])
    assert ptypes.is_float_dtype(df["total_market_value"])
    assert ptypes.is_float_dtype(df["cash"])
    assert ptypes.is_float_dtype(df["cashflow"])
    assert ptypes.is_float_dtype(df["dividend"])
    assert ptypes.is_float_dtype(df["cumulative_dividend"])
    assert ptypes.is_float_dtype(df["commission"])

    # Value
    assert (df["port_value_with_dividend"] >= 0).all()
    assert (df["port_value"] >= 0).all()
    assert (df["total_market_value"] >= 0).all()
    assert (df["cash"] >= 0).all()
    assert (df["dividend"] >= 0).all()
    assert (df["cumulative_dividend"] >= 0).all()
    assert (df["commission"] >= 0).all()

    assert df["cumulative_dividend"].is_monotonic

    assert not df.empty


def _check_position_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(position_columns))

    # Data type
    if not df.empty:
        assert ptypes.is_datetime64_any_dtype(df["timestamp"])
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["avg_cost_price"])
        assert ptypes.is_float_dtype(df["close_price"])
        assert ptypes.is_float_dtype(df["close_value"])

    # Value
    assert (df["volume"] > 0).all()
    assert (df["avg_cost_price"] > 0).all()
    assert (df["close_price"] > 0).all()
    assert (df["close_value"] > 0).all()


def _check_trade_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(trade_columns))

    # Data type
    if not df.empty:
        assert ptypes.is_datetime64_any_dtype(df["timestamp"])
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_string_dtype(df["side"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["price"])
        assert ptypes.is_float_dtype(df["commission"])

    # Value
    assert (df["volume"] > 0).all()
    assert (df["price"] > 0).all()
    assert (df["commission"] >= 0).all()


def _check_dividend_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(dividend_columns))

    # Data type
    if not df.empty:
        assert ptypes.is_datetime64_any_dtype(df["ex_date"])
        assert ptypes.is_datetime64_any_dtype(df["before_ex_date"])
        assert ptypes.is_datetime64_any_dtype(df["pay_date"])
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_float_dtype(df["dps"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["amount"])

    # Value
    assert (df["dps"] > 0).all()
    assert (df["volume"] > 0).all()
    assert (df["amount"] > 0).all()
    assert (df["before_ex_date"] < df["ex_date"]).all()
    assert (df["ex_date"] <= df["pay_date"]).all()
