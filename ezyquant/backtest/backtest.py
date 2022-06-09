from dataclasses import fields
from typing import List, Tuple

import pandas as pd

from .. import fields as fld
from .. import utils
from ..creator import SETSignalCreator
from ..reader import SETDataReader
from .portfolio import Portfolio
from .position import Position
from .trade import Trade


def backtest_target_weight(
    sqlite_path: str,
    signal_df: pd.DataFrame,
    rebalance_freq: str,
    rebalance_at: int,
    # common param
    start_date: str,
    end_date: str,
    initial_cash: float,
    pct_commission: float = 0.0,
    pct_buy_slip: float = 0.0,
    pct_sell_slip: float = 0.0,
    trigger_buy_price_mode: str = "close",
    trigger_buy_price_delay_bar: int = 0,
    trigger_sell_price_mode: str = "close",
    trigger_sell_price_delay_bar: int = 0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    symbol_list = signal_df.columns.tolist()
    ssc = SETSignalCreator(
        sqlite_path=sqlite_path,
        start_date=start_date,
        end_date=end_date,
        symbol_list=symbol_list,
    )

    # TODO: initial_position_dict

    # Baned symbol
    # TODO: Sell only banned symbol, not rebalance
    is_banned = ssc.is_banned()
    signal_df = signal_df.mask(is_banned, 0)

    # Rebalance
    # TODO: Rebalance by frequency
    is_signal_change = (signal_df != signal_df.shift(1)).any(axis=1)

    signal_df = signal_df[is_signal_change]

    # Price df
    _validate_price_mode(trigger_buy_price_mode)
    _validate_price_mode(trigger_sell_price_mode)

    sdr = SETDataReader(sqlite_path)
    symbol_list = signal_df.columns.tolist()

    buy_price_df = sdr.get_data_symbol_daily(
        field=trigger_buy_price_mode,
        symbol_list=symbol_list,
        start_date=start_date,
        end_date=end_date,
    )
    sell_price_df = sdr.get_data_symbol_daily(
        field=trigger_sell_price_mode,
        symbol_list=symbol_list,
        start_date=start_date,
        end_date=end_date,
    )

    # Slip
    buy_price_df *= 1 + pct_buy_slip
    sell_price_df *= 1 - pct_sell_slip

    # Delay
    # TODO: load more data for delay bar
    # buy_price_df = buy_price_df.shift(trigger_buy_price_delay_bar)
    # sell_price_df = sell_price_df.shift(trigger_sell_price_delay_bar)

    # Backtest
    cash_series, position_df, trade_df = _backtest_target_weight(
        initial_cash=initial_cash,
        signal_weight_df=signal_df,
        buy_price_df=buy_price_df,
        sell_price_df=sell_price_df,
        pct_commission=pct_commission,
    )

    # Dividend df
    dividend_df = pd.DataFrame()

    # Stat df
    stat_df = pd.DataFrame()

    # Summary df
    summary_df = pd.DataFrame()

    return summary_df, position_df, trade_df, dividend_df, stat_df


def _backtest_target_weight(
    initial_cash: float,
    signal_weight_df: pd.DataFrame,
    buy_price_df: pd.DataFrame,
    sell_price_df: pd.DataFrame,
    pct_commission: float = 0.0,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Backtest Target Weight.

    Parameters
    ----------
    initial_cash : float
        cash at the beginning of the backtest
    signal_weight_df : pd.DataFrame
        dataframe of signal weight.
        index is trade date, columns are symbol, values are weight.
        values must be positive and sum must not more than 1 each day.
        missing index or nan row is not rebalance.
    buy_price_df : pd.DataFrame
        dataframe of buy price.
        index is trade date, columns are symbol, values are weight.
        index and columns must be same as or more than signal_weight_df.
    sell_price_df : pd.DataFrame
        dataframe of sell price.
        index is trade date, columns are symbol, values are weight.
        index and columns must be same as or more than signal_weight_df.
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
                - timestamp
                - symbol
                - volume
                - price
                - pct_commission
    """
    _validate_initial_cash(initial_cash)
    _validate_pct_commission(pct_commission)
    _validate_price_df(buy_price_df, sell_price_df)
    _validate_signal_df(
        signal_weight_df,
        trade_date_list=buy_price_df.index.to_list(),
        symbol_list=buy_price_df.columns.to_list(),
    )

    # Select only symbol in signal
    buy_price_df = buy_price_df[signal_weight_df.columns]
    sell_price_df = sell_price_df[signal_weight_df.columns]

    group_price = pd.concat([buy_price_df, sell_price_df]).groupby(level=0)
    min_price_df = group_price.min() * (1.0 - pct_commission)
    max_price_df = group_price.max() * (1.0 + pct_commission)

    pf = Portfolio(
        cash=initial_cash,
        pct_commission=pct_commission,
        position_dict={},  # TODO: initial position
        trade_list=[],  # TODO: initial trade
    )

    sig_by_price_df = signal_weight_df / max_price_df

    position_df_list: List[pd.DataFrame] = [
        # First dataframe for sort columns
        pd.DataFrame(
            columns=["timestamp"] + [i.name for i in fields(Position)], dtype="float64"
        )
    ]

    def on_interval(buy_price_s: pd.Series) -> float:
        ts = buy_price_s.name

        trade_value = pf.cash + (pf.volume_series * min_price_df.loc[ts]).sum()  # type: ignore
        target_volume_s = trade_value * sig_by_price_df.loc[ts]  # type: ignore
        trade_volume_s = target_volume_s - pf.volume_series.reindex(
            target_volume_s.index, fill_value=0
        )
        trade_volume_s = utils.round_df_100(trade_volume_s)

        # Sell
        sell_price_s = sell_price_df.loc[ts]  # type: ignore
        for k, v in trade_volume_s[trade_volume_s < 0].items():
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
                price=sell_price_s[k],
                timestamp=ts,  # type: ignore
            )

        # Buy
        for k, v in trade_volume_s[trade_volume_s > 0].items():
            pf.place_order(
                symbol=k,  # type: ignore
                volume=v,  # type: ignore
                price=buy_price_s[k],  # type: ignore
                timestamp=ts,  # type: ignore
            )

        pos_df = pf.get_position_df()
        pos_df["timestamp"] = ts
        position_df_list.append(pos_df)

        return pf.cash

    cash_s = buy_price_df.apply(on_interval, axis=1)
    assert isinstance(cash_s, pd.Series)

    position_df = pd.concat(position_df_list, ignore_index=True)
    trade_df = pd.DataFrame(pf.trade_list, columns=[i.name for i in fields(Trade)])

    return cash_s, position_df, trade_df


""" 
Validation
"""


def _validate_price_mode(price_mode: str) -> None:
    if price_mode not in [fld.D_OPEN, fld.D_HIGH, fld.D_LOW, fld.D_CLOSE]:
        raise ValueError(f"Invalid price mode: {price_mode}")


def _validate_initial_cash(initial_cash: float) -> None:
    if initial_cash < 0:
        raise ValueError("initial_cash must be positive")


def _validate_pct_commission(pct_commission: float) -> None:
    if pct_commission < 0 or pct_commission > 1:
        raise ValueError("pct_commission must be between 0 and 1")


def _validate_price_df(buy_price_df: pd.DataFrame, sell_price_df: pd.DataFrame):
    idx = buy_price_df.index

    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("buy_price_df index must be DatetimeIndex")
    if not idx.is_monotonic:
        raise ValueError("buy_price_df index must be monotonic increasing")
    if not idx.is_unique:
        raise ValueError("buy_price_df index must be unique")
    if not idx.equals(sell_price_df.index):
        raise ValueError("buy_price_df and sell_price_df index must be same")
    if not buy_price_df.columns.equals(sell_price_df.columns):
        raise ValueError("buy_price_df and sell_price_df columns must be same")

    if buy_price_df.empty:
        raise ValueError("buy_price_df must not be empty")
    if sell_price_df.empty:
        raise ValueError("sell_price_df must not be empty")


def _validate_signal_df(
    signal_df: pd.DataFrame,
    trade_date_list: List,
    symbol_list: List[str],
    is_allow_nan_row: bool = True,
):
    idx = signal_df.index

    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("signal_df index must be DatetimeIndex")
    if not idx.is_monotonic:
        raise ValueError("signal_df index must be monotonic increasing")
    if not idx.is_unique:
        raise ValueError("signal_df index must be unique")
    if not idx.isin(trade_date_list).all():
        raise ValueError("signal_df index must be in buy_price_df index")
    if not signal_df.columns.isin(symbol_list).all():
        raise ValueError("signal_df columns must be in buy_price_df columns")

    if signal_df.empty:
        raise ValueError("signal_df must not be empty")

    if is_allow_nan_row:
        signal_df = signal_df.dropna(how="all")

    if signal_df.isnull().values.any():
        raise ValueError("signal_df must not contain NaN")
    if (signal_df < 0).values.any():
        raise ValueError("signal_df must be positive")
    if not signal_df.sum(axis=1).between(0, 1).all():
        raise ValueError(
            "signal_df must be positive and sum must not more than 1 each day"
        )
