from dataclasses import fields
from typing import Callable, Dict, List, Tuple

import pandas as pd
from pandas.testing import assert_index_equal

from .. import validators as vld
from .account import SETAccount
from .position import Position
from .trade import Trade

position_df_columns = ["timestamp"] + [i.name for i in fields(Position)]
trade_df_columns = [i.name for i in fields(Trade)]


def _backtest(
    initial_cash: float,
    signal_df: pd.DataFrame,
    apply_trade_volume: Callable[[pd.Timestamp, float, Position, SETAccount], float],
    close_price_df: pd.DataFrame,
    price_match_df: pd.DataFrame,
    pct_buy_slip: float,
    pct_sell_slip: float,
    pct_commission: float,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Backtest function without load any data. apply_trade_volume will be
    called depend on signal_df.

    Parameters
    ----------
    initial_cash : float
        cash at the beginning of the backtest
    signal_df : pd.DataFrame
        dataframe of signal.
        index is trade date, columns are symbol, values are signal.
    apply_trade_volume: Callable[[pd.Timestamp, float, Position, SETAccount], float],
        function for calculate trade volume.
        Parameters:
            - timestamp: pd.Timestamp
                timestamp of bar.
            - signal: float
                signal from signal_df
            - position: Position
                - symbol: str
                    symbol of position
                - volume: float
                    volume of position
                - close_price: float
                    close price of position
                - avg_cost_price: float
                    average cost price of position
            - account: SETAccount
                account object
        Return:
            - trade_volume: float
                positive for buy, negative for sell, 0 or nan for no trade
    close_price_df : pd.DataFrame
        dataframe of buy price.
        index is trade date, columns are symbol, values are weight.
        index and columns must be same as or more than signal_df.
        first row will be used as initial price.
    price_match_df : pd.DataFrame
        dataframe of sell price.
        index is trade date, columns are symbol, values are weight.
        index and columns must be same as or more than signal_df.
    pct_buy_slip : float, default 0.0
        percentage of buy slip, higher value means higher buy price
    pct_sell_slip : float, default 0.0
        percentage of sell slip, higher value means lower sell price
    pct_commission : float, default 0.0
        percentage of commission fee

    Returns
    -------
    Tuple[pd.Series, pd.DataFrame, pd.DataFrame]
        Return snapshot at end of day:
            - cash_series
                - timestamp (index)
                - cash
            - position_df
                - timestamp
                - symbol
                - volume
                - avg_cost_price
            - trade_df
                - matched_at
                - symbol
                - volume
                - price
                - pct_commission
    """
    vld.check_cash(initial_cash)
    vld.check_pct(pct_buy_slip)
    vld.check_pct(pct_sell_slip)
    vld.check_pct(pct_commission)

    # Ratio
    ratio_buy_slip = 1.0 + pct_buy_slip
    ratio_sell_slip = 1.0 - pct_sell_slip

    # Account
    acct = SETAccount(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: [EZ-79] initial position dict
        trade_list=[],  # TODO: initial trade
        market_price_dict=close_price_df.iloc[0].to_dict(),
    )

    # remove first close row
    close_price_df = close_price_df.iloc[1:]  # type: ignore

    # Check after remove first close row
    _check_df_input(signal_df, close_price_df, price_match_df)

    # Dict
    signal_dict: Dict[pd.Timestamp, Dict[str, float]] = signal_df.to_dict("index")  # type: ignore
    close_price_dict: Dict[pd.Timestamp, Dict[str, float]] = close_price_df.to_dict(
        "index"
    )  # type: ignore
    price_match_dict: Dict[pd.Timestamp, Dict[str, float]] = price_match_df.to_dict(
        "index"
    )  # type: ignore

    position_df_list: List[pd.DataFrame] = [
        # First dataframe for sort columns
        pd.DataFrame(columns=position_df_columns, dtype="float64"),
    ]

    def calculate_trade_volume(
        ts: pd.Timestamp,
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        signal_d = signal_dict.get(ts, dict())

        buy_volume_d = dict()
        sell_volume_d = dict()

        for k, v in signal_d.items():
            acct.selected_symbol = k
            trade_volume = apply_trade_volume(ts, v, acct._position, acct)

            if trade_volume > 0:
                buy_volume_d[k] = trade_volume
            elif trade_volume < 0:
                sell_volume_d[k] = trade_volume

            # teardown
            acct.selected_symbol = None

        return buy_volume_d, sell_volume_d

    def on_interval(ts: pd.Timestamp, close_price_dict: Dict[str, float]) -> float:
        buy_volume_d, sell_volume_d = calculate_trade_volume(ts)

        # Trade
        for k, v in sell_volume_d.items():
            price = price_match_dict[ts][k] * ratio_sell_slip
            acct._match_order_if_possible(ts, symbol=k, volume=v, price=price)
        for k, v in buy_volume_d.items():
            price = price_match_dict[ts][k] * ratio_buy_slip
            acct._match_order_if_possible(ts, symbol=k, volume=v, price=price)

        # Snap
        acct._set_market_price_dict(close_price_dict)
        pos_df = acct.position_df
        pos_df["timestamp"] = ts
        position_df_list.append(pos_df)

        return acct.cash

    cash_s = pd.Series(
        [on_interval(k, v) for k, v in close_price_dict.items()],
        index=close_price_df.index,
    )
    assert isinstance(cash_s, pd.Series)

    position_df = pd.concat(position_df_list, ignore_index=True)
    position_df["timestamp"] = pd.to_datetime(position_df["timestamp"])

    trade_df = pd.DataFrame(acct.trade_list, columns=trade_df_columns)
    trade_df["matched_at"] = pd.to_datetime(trade_df["matched_at"])

    return cash_s, position_df, trade_df


def _check_df_input(
    signal_df: pd.DataFrame,
    close_price_df: pd.DataFrame,
    price_match_df: pd.DataFrame,
):
    vld.check_df_symbol_daily(signal_df)
    vld.check_df_symbol_daily(close_price_df)
    vld.check_df_symbol_daily(price_match_df)

    assert_index_equal(close_price_df.index, price_match_df.index)
    assert_index_equal(close_price_df.columns, price_match_df.columns)

    assert signal_df.index.isin(close_price_df.index).all()
    assert signal_df.columns.isin(close_price_df.columns).all()
