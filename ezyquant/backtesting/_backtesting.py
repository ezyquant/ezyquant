from dataclasses import fields
from typing import Callable, Dict, List, Tuple

import pandas as pd
from pandas.testing import assert_index_equal

from .. import validators as vld
from .account import SETAccount
from .context import Context
from .position import SETPosition
from .trade import SETTrade

position_df_columns = ["timestamp"] + [i.name for i in fields(SETPosition)]
trade_df_columns = [i.name for i in fields(SETTrade)]


def _backtest(
    initial_cash: float,
    signal_df: pd.DataFrame,
    backtest_algorithm: Callable[[Context], float],
    close_price_df: pd.DataFrame,
    price_match_df: pd.DataFrame,
    pct_buy_slip: float,
    pct_sell_slip: float,
    pct_commission: float,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Backtest function without load any data.

    Parameters
    ----------
    initial_cash: float
        Initial cash.
    signal_df: pd.DataFrame
        Dataframe of signal.
        Index is the trading date, columns are symbol, values are signal.
        Missing signal in the trading date will be filled with nan.
    backtest_algorithm: Callable[[Context], float]
        Function for calculate trade volume.
        Parameters:
            - context: Context
                context for backtest
        Return:
            - trade_volume: float
                positive for buy, negative for sell, 0 or nan for no trade
    close_price_df: pd.DataFrame
        Dataframe of close price.
        Index is trade date, columns are symbol, values are weight.
        First row will be used as initial close price.
    price_match_df: pd.DataFrame
        Dataframe of match price. No trade will be made if price is nan.
        Index is trade date, columns are symbol, values are weight.
        Index and columns must be same as or more than close_price_df.
    pct_buy_slip: float
        Percentage of buy slip, higher value means higher buy price (ex. 0.01 means 1% increase).
    pct_sell_slip: float
        Percentage of sell slip, higher value means lower sell price (ex. 0.01 means 1% decrease).
    pct_commission: float
        Percentage of commission fee (ex. 0.01 means 1% fee).

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
                - cost_price
                - close_price
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
    )
    acct.set_position_close_price(close_price_df.iloc[0].to_dict())  # type: ignore

    # remove first close row
    close_price_df = close_price_df.iloc[1:]

    # reindex signal
    signal_df = signal_df.reindex(close_price_df.index)
    signal_df = signal_df.sort_index(axis=1)

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
        signal_d = signal_dict[ts]

        buy_volume_d = dict()
        sell_volume_d = dict()

        ctx = Context(
            ts=ts,
            cash=acct.cash,
            total_cost_value=acct.total_cost_value,
            total_market_value=acct.total_market_value,
            port_value=acct.port_value,
        )

        for k, v in signal_d.items():
            # Setup ctx
            ctx.symbol = k
            ctx.signal = v
            ctx.close_price = acct.close_price_dict[k]
            if k in acct.position_dict:
                pos = acct.position_dict[k]
                ctx.volume = pos.volume
                ctx.cost_price = pos.cost_price
            else:
                ctx.volume = 0.0
                ctx.cost_price = 0.0

            trade_volume = backtest_algorithm(ctx)

            if trade_volume > 0:
                buy_volume_d[k] = trade_volume
            elif trade_volume < 0:
                sell_volume_d[k] = trade_volume

        return buy_volume_d, sell_volume_d

    def on_interval(ts: pd.Timestamp, close_price_dict: Dict[str, float]) -> float:
        buy_volume_d, sell_volume_d = calculate_trade_volume(ts)

        # Trade
        for k, v in sell_volume_d.items():
            price = price_match_dict[ts][k] * ratio_sell_slip
            acct.match_order_if_possible(ts, symbol=k, volume=v, price=price)
        for k, v in buy_volume_d.items():
            price = price_match_dict[ts][k] * ratio_buy_slip
            acct.match_order_if_possible(ts, symbol=k, volume=v, price=price)

        # Snap
        acct.set_position_close_price(close_price_dict)
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

    assert_index_equal(close_price_df.index, signal_df.index)
    assert_index_equal(close_price_df.columns, signal_df.columns)
