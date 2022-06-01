import pandas as pd
import pytest
import utils

from ezyquant.backtest import backtest


class TestBacktest:
    def test_success(
        self,
        signal_weight_df: pd.DataFrame,
        close_price_df: pd.DataFrame,
        match_price_df: pd.DataFrame,
        is_rebalance_df: pd.DataFrame,
    ):
        # Mock
        initial_cash = 1000

        # Test
        summary_df, position_df, trade_df = backtest(
            initial_cash=initial_cash,
            signal_weight_df=signal_weight_df,
            close_price_df=close_price_df,
            match_price_df=match_price_df,
            is_rebalance_df=is_rebalance_df,
        )

        # Assert
        utils.check_summary_df(summary_df)
        utils.check_position_df(position_df)
        utils.check_trade_df(trade_df)
