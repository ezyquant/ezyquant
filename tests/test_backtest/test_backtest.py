import pandas as pd
import pytest
import utils
from pandas.testing import assert_index_equal, assert_series_equal

from ezyquant.backtest import _backtest_target_weight

nan = float("nan")

position_columns = ["timestamp", "symbol", "volume", "avg_cost_price"]
trade_columns = ["timestamp", "symbol", "volume", "price", "pct_commission"]


class TestBacktestTargetWeightNoTrade:
    @pytest.mark.parametrize("pct_commission", [0.0, 0.1])
    @pytest.mark.parametrize(
        ("initial_cash", "signal_weight_df", "price_df"),
        [
            # cash
            (0.0, utils.make_signal_weight_df(), utils.make_price_df()),
            (1.0, utils.make_signal_weight_df(), utils.make_price_df() * 100),
            # signal
            (1000.0, utils.make_data_df(0), utils.make_price_df()),
            (1000.0, utils.make_data_df(nan), utils.make_price_df()),
            (
                1000.0,
                utils.make_data_df([0, nan, 0, nan], n_row=4, n_col=1),
                utils.make_price_df(n_row=4, n_col=1),
            ),
            # price
            (1000.0, utils.make_signal_weight_df(), utils.make_data_df(0)),
            (1000.0, utils.make_signal_weight_df(), utils.make_data_df(nan)),
        ],
    )
    def test_no_trade(
        self,
        initial_cash: float,
        signal_weight_df: pd.DataFrame,
        price_df: pd.DataFrame,
        pct_commission: float,
    ):
        # Test
        cash_series, position_df, trade_df = _backtest_target_weight(
            initial_cash=initial_cash,
            signal_weight_df=signal_weight_df,
            buy_price_df=price_df,
            sell_price_df=price_df,
            pct_commission=pct_commission,
        )

        # Check
        # cash_series
        utils.check_cash_series(cash_series)
        assert_index_equal(price_df.index, cash_series.index)
        assert (cash_series == initial_cash).all()

        # position_df
        utils.check_position_df(position_df)
        assert position_df.empty

        # trade_df
        utils.check_trade_df(trade_df)
        assert trade_df.empty


@pytest.mark.parametrize("initial_cash", [10000.0])
@pytest.mark.parametrize(
    "price_df",
    [
        utils.make_data_df(
            [
                [1.1, 2.1],
                [1.2, 2.2],
                [1.3, 2.3],
            ],
            n_row=3,
            n_col=2,
        ),
        utils.make_data_df(
            [
                [1.1, 2.1, 0.0],
                [1.2, 2.2, 0.0],
                [1.3, 2.3, 0.0],
            ],
            n_row=3,
            n_col=3,
        ),
    ],
)
class TestBacktestTargetWeight:
    @pytest.mark.kwparametrize(
        # Buy and hold
        dict(
            signal_weight_df=utils.make_data_df([0.1, 0.1, 0.1], n_row=3, n_col=1),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [9010.0, 9130.0, 9260.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 800.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 700.0, 1.1],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1, 0.0],
                    [pd.Timestamp("2000-01-04"), "AAA", -100.0, 1.2, 0.0],
                    [pd.Timestamp("2000-01-05"), "AAA", -100.0, 1.3, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
        # Buy and hold full port
        dict(
            signal_weight_df=utils.make_data_df(
                [[1.0], [1.0], [1.0]], n_row=3, n_col=1
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [100.0, 100.0, 100.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 9000.0, 1.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 9000.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 9000.0, 1.1],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 9000.0, 1.1, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
        # Buy and Sell
        dict(
            signal_weight_df=utils.make_data_df(
                [[0.1], [0.0], [0.1]], n_row=3, n_col=1
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [9010.00, 10090.00, 9180.00],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 700.0, 1.3],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1, 0.0],
                    [pd.Timestamp("2000-01-04"), "AAA", -900.0, 1.2, 0.0],
                    [pd.Timestamp("2000-01-05"), "AAA", 700.0, 1.3, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
        # Buy and Sell full port
        dict(
            signal_weight_df=utils.make_data_df(
                [[1.0], [0.0], [1.0]], n_row=3, n_col=1
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [100.0, 10900.0, 110.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 9000.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 8300.0, 1.3],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 9000.0, 1.1, 0.0],
                    [pd.Timestamp("2000-01-04"), "AAA", -9000.0, 1.2, 0.0],
                    [pd.Timestamp("2000-01-05"), "AAA", 8300.0, 1.3, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
        # Buy and Sell full port with commission
        dict(
            signal_weight_df=utils.make_data_df(
                [[1.0], [0.0], [1.0]], n_row=3, n_col=1
            ),
            pct_commission=0.1,
            expect_cash_series=pd.Series(
                [78.0, 8934.0, 68.00],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 8200.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 6200.0, 1.3],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 8200.0, 1.1, 0.1],
                    [pd.Timestamp("2000-01-04"), "AAA", -8200.0, 1.2, 0.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 6200.0, 1.3, 0.1],
                ],
                columns=trade_columns,
            ),
        ),
    )
    def test_one_symbol(
        self,
        initial_cash: float,
        signal_weight_df: pd.DataFrame,
        price_df: pd.DataFrame,
        pct_commission: float,
        expect_cash_series: pd.Series,
        expect_position_df: pd.DataFrame,
        expect_trade_df: pd.DataFrame,
    ):
        # Test
        cash_series, position_df, trade_df = _backtest_target_weight(
            initial_cash=initial_cash,
            signal_weight_df=signal_weight_df,
            buy_price_df=price_df,
            sell_price_df=price_df,
            pct_commission=pct_commission,
        )

        # Check
        # cash_series
        utils.check_cash_series(cash_series)
        assert_index_equal(price_df.index, cash_series.index)
        assert_series_equal(cash_series, expect_cash_series)

        # position_df
        utils.check_position_df(position_df)
        utils.assert_frame_equal_sort_index(
            position_df, expect_position_df, check_dtype=False
        )

        # trade_df
        utils.check_trade_df(trade_df)
        utils.assert_frame_equal_sort_index(
            trade_df, expect_trade_df, check_dtype=False
        )

    @pytest.mark.kwparametrize(
        # Buy and hold
        dict(
            signal_weight_df=utils.make_data_df(
                [[0.1], [nan], [0.1]], n_row=3, n_col=1
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [9010.0, 9010.0, 9270.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 900.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 700.0, 1.1],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1, 0.0],
                    [pd.Timestamp("2000-01-05"), "AAA", -200.0, 1.3, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
        # Buy and hold full port
        dict(
            signal_weight_df=utils.make_data_df(
                [[1.0], [nan], [1.0]], n_row=3, n_col=1
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [100.0, 100.0, 100.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 9000.0, 1.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 9000.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 9000.0, 1.1],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 9000.0, 1.1, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
        # Start with not rebalance then buy
        dict(
            signal_weight_df=utils.make_data_df(
                [[nan], [0.1], [0.1]], n_row=3, n_col=1
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [10000.0, 9040.0, 9170.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-04"), "AAA", 800.0, 1.2],
                    [pd.Timestamp("2000-01-05"), "AAA", 700.0, 1.2],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-04"), "AAA", 800.0, 1.2, 0.0],
                    [pd.Timestamp("2000-01-05"), "AAA", -100.0, 1.3, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
    )
    def test_nan_signal(
        self,
        initial_cash: float,
        signal_weight_df: pd.DataFrame,
        price_df: pd.DataFrame,
        pct_commission: float,
        expect_cash_series: pd.Series,
        expect_position_df: pd.DataFrame,
        expect_trade_df: pd.DataFrame,
    ):
        self.test_one_symbol(
            initial_cash=initial_cash,
            signal_weight_df=signal_weight_df,
            price_df=price_df,
            pct_commission=pct_commission,
            expect_cash_series=expect_cash_series,
            expect_position_df=expect_position_df,
            expect_trade_df=expect_trade_df,
        )

    @pytest.mark.kwparametrize(
        dict(
            signal_weight_df=utils.make_data_df(
                [
                    [0.1, 0.1],
                    [0.1, 0.1],
                    [0.1, 0.1],
                ],
                n_row=3,
                n_col=2,
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [8170.0, 8290.0, 8420.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1],
                    [pd.Timestamp("2000-01-03"), "AAB", 400.0, 2.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 800.0, 1.1],
                    [pd.Timestamp("2000-01-04"), "AAB", 400.0, 2.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 700.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAB", 400.0, 2.1],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 900.0, 1.1, 0.0],
                    [pd.Timestamp("2000-01-03"), "AAB", 400.0, 2.1, 0.0],
                    [pd.Timestamp("2000-01-04"), "AAA", -100.0, 1.2, 0.0],
                    [pd.Timestamp("2000-01-05"), "AAA", -100.0, 1.3, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
    )
    def test_two_symbol(
        self,
        initial_cash: float,
        signal_weight_df: pd.DataFrame,
        price_df: pd.DataFrame,
        pct_commission: float,
        expect_cash_series: pd.Series,
        expect_position_df: pd.DataFrame,
        expect_trade_df: pd.DataFrame,
    ):
        self.test_one_symbol(
            initial_cash=initial_cash,
            signal_weight_df=signal_weight_df,
            price_df=price_df,
            pct_commission=pct_commission,
            expect_cash_series=expect_cash_series,
            expect_position_df=expect_position_df,
            expect_trade_df=expect_trade_df,
        )

    @pytest.mark.kwparametrize(
        dict(
            signal_weight_df=utils.make_data_df([0.1, 0.1, 0.1], n_row=3, n_col=1),
            sell_price_df=utils.make_data_df(
                [[1.15], [1.25], [1.35]], n_row=3, n_col=1
            ),
            pct_commission=0.0,
            expect_cash_series=pd.Series(
                [9120.0, 9120.0, 9255.0],
                index=utils.make_bdate_range(3),
            ),
            expect_position_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 800.0, 1.1],
                    [pd.Timestamp("2000-01-04"), "AAA", 800.0, 1.1],
                    [pd.Timestamp("2000-01-05"), "AAA", 700.0, 1.1],
                ],
                columns=position_columns,
            ),
            expect_trade_df=pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-03"), "AAA", 800.0, 1.1, 0.0],
                    [pd.Timestamp("2000-01-05"), "AAA", -100.0, 1.35, 0.0],
                ],
                columns=trade_columns,
            ),
        ),
    )
    def test_buy_sell_price(
        self,
        initial_cash: float,
        signal_weight_df: pd.DataFrame,
        price_df: pd.DataFrame,
        sell_price_df: pd.DataFrame,
        pct_commission: float,
        expect_cash_series: pd.Series,
        expect_position_df: pd.DataFrame,
        expect_trade_df: pd.DataFrame,
    ):
        price_df = price_df[sell_price_df.columns]

        # Test
        cash_series, position_df, trade_df = _backtest_target_weight(
            initial_cash=initial_cash,
            signal_weight_df=signal_weight_df,
            buy_price_df=price_df,
            sell_price_df=sell_price_df,
            pct_commission=pct_commission,
        )

        # Check
        # cash_series
        utils.check_cash_series(cash_series)
        assert_index_equal(price_df.index, cash_series.index)
        assert_series_equal(cash_series, expect_cash_series)

        # position_df
        utils.check_position_df(position_df)
        utils.assert_frame_equal_sort_index(
            position_df, expect_position_df, check_dtype=False
        )

        # trade_df
        utils.check_trade_df(trade_df)
        utils.assert_frame_equal_sort_index(
            trade_df, expect_trade_df, check_dtype=False
        )


@pytest.mark.parametrize("initial_cash", [1e2, 1e6])
@pytest.mark.parametrize("pct_commission", [0.0, 0.0025, 0.1])
@pytest.mark.parametrize(
    "signal_weight_df", [utils.make_signal_weight_df(n_row=2000, n_col=800)]
)
@pytest.mark.parametrize("buy_price_df", [utils.make_price_df(n_row=2000, n_col=800)])
@pytest.mark.parametrize("sell_price_df", [utils.make_price_df(n_row=2000, n_col=800)])
def test_random_input(
    initial_cash: float,
    signal_weight_df: pd.DataFrame,
    buy_price_df: pd.DataFrame,
    sell_price_df: pd.DataFrame,
    pct_commission: float,
):
    cash_series, position_df, trade_df = _backtest_target_weight(
        initial_cash=initial_cash,
        signal_weight_df=signal_weight_df,
        buy_price_df=buy_price_df,
        sell_price_df=sell_price_df,
        pct_commission=pct_commission,
    )

    # Check
    # cash_series
    utils.check_cash_series(cash_series)
    assert_index_equal(buy_price_df.index, cash_series.index)

    # position_df
    utils.check_position_df(position_df)

    # trade_df
    utils.check_trade_df(trade_df)
