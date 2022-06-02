import pandas as pd
import pytest
import utils
from pandas.testing import assert_index_equal

from ezyquant.backtest import backtest


class TestBacktest:
    @pytest.mark.parametrize("pct_commission", [0.0, 0.1])
    @pytest.mark.parametrize("pct_buy_match_price", [0.0, 0.1])
    @pytest.mark.parametrize("pct_sell_match_price", [0.0, 0.1])
    @pytest.mark.parametrize(
        ("initial_cash", "signal_weight_df", "match_price_df"),
        [
            # cash
            (0, utils.make_signal_weight_df(), utils.make_price_df()),
            # signal
            (1000, utils.make_data_df(0), utils.make_price_df()),
            (1000, utils.make_data_df(float("nan")), utils.make_price_df()),
            (1000, utils.make_data_df(0, n_row=0), utils.make_price_df()),
            (1000, utils.make_data_df(0, n_col=0), utils.make_price_df()),
            (1000, utils.make_data_df(0, n_row=0, n_col=0), utils.make_price_df()),
            # price
            (1000, utils.make_signal_weight_df(), utils.make_data_df(0)),
            (1000, utils.make_signal_weight_df(), utils.make_data_df(float("nan"))),
        ],
    )
    def test_no_trade(
        self,
        initial_cash: float,
        signal_weight_df: pd.DataFrame,
        match_price_df: pd.DataFrame,
        pct_commission: float,
        pct_buy_match_price: float,
        pct_sell_match_price: float,
    ):
        # Test
        cash_df, position_df, trade_df = backtest(
            initial_cash=initial_cash,
            signal_weight_df=signal_weight_df,
            match_price_df=match_price_df,
            pct_commission=pct_commission,
            pct_buy_match_price=pct_buy_match_price,
            pct_sell_match_price=pct_sell_match_price,
        )

        # Check
        # cash_df
        utils.check_cash_df(cash_df)
        assert_index_equal(match_price_df.index, cash_df.index)
        assert (cash_df == initial_cash).all().all()

        # position_df
        utils.check_position_df(position_df)
        assert position_df.empty

        # trade_df
        utils.check_trade_df(trade_df)
        assert trade_df.empty
