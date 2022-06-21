from datetime import datetime
from functools import cached_property

import pandas as pd
from pandas.testing import assert_index_equal

from . import fields as fld
from . import utils
from .reader import _SETDataReaderCached

nan = float("nan")

summary_columns = [
    "timestamp",
    "port_value_with_dividend",
    "port_value",
    "total_market_value",
    "cash",
    "cashflow",
    "dividend",
    "cumulative_dividend",
    "commission",
]
position_columns = [
    "timestamp",
    "symbol",
    "volume",
    "avg_cost_price",
    "close_price",
    "close_value",
]
trade_columns = [
    "matched_at",
    "symbol",
    "side",
    "volume",
    "price",
    "commission",
]
dividend_columns = [
    "ex_date",
    "symbol",
    "dps",
    "volume",
    "amount",
    "before_ex_date",
    "pay_date",
]
summary_trade_columns = [
    "exit_at",
    "symbol",
    "avg_cost_price",
    "sell_price",
    "volume",
    "commission",
    "return",
    "pct_return",
    "entry_at",
    "hold_days",
]


def return_nan_on_failure(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ZeroDivisionError:
            return nan

    return wrapper


class SETBacktestReport:
    def __init__(
        self,
        initial_capital: float,
        pct_commission: float,
        pct_buy_slip: float,
        pct_sell_slip: float,
        cash_series: pd.Series,
        position_df: pd.DataFrame,
        trade_df: pd.DataFrame,
    ):
        """SETBacktestReport.

        Parameters
        ----------
        initial_capital : float
            initial capital.
        pct_commission : float
            percent commission.
        pct_buy_slip : float
            percent of buy price increase.
        pct_sell_slip : float
            percent of sell price decrease.
        cash_series : pd.Series
            series of cash.
        position_df : pd.DataFrame
            dataframe of position.
                - timestamp
                - symbol
                - volume
                - avg_cost_price
        trade_df : pd.DataFrame
            dataframe of trade.
                - matched_at
                - symbol
                - volume
                - price
                - pct_commission
        """
        self._initial_capital = initial_capital
        self._pct_commission = pct_commission
        self._pct_buy_slip = pct_buy_slip
        self._pct_sell_slip = pct_sell_slip

        self._cash_series = cash_series
        self._position_df = position_df
        self._trade_df = trade_df

        self._sdr = _SETDataReaderCached()

    @cached_property
    def summary_df(self) -> pd.DataFrame:
        """Summary DataFrame.

        Returns
        -------
        pd.DataFrame
            - timestamp
            - port_value_with_dividend
            - port_value
            - total_market_value
            - cash
            - cashflow
            - dividend
            - cumulative_dividend
            - commission
        """
        df = self._cash_series.to_frame("cash")

        df["cashflow"] = df["cash"].diff().fillna(0.0)

        df["commission"] = (
            self.trade_df.set_index("matched_at")["commission"].groupby(level=0).sum()
        )
        df["commission"] = df["commission"].fillna(0.0)

        df["total_market_value"] = (
            self.position_df.set_index("timestamp")["close_value"]
            .groupby(level=0)
            .sum()
        )
        df["total_market_value"] = df["total_market_value"].fillna(0.0)

        df["port_value"] = df["total_market_value"] + df["cash"]

        # pay_date can be non trade date.
        tds = pd.to_datetime(self._sdr.get_trading_dates())
        by = _searchsorted_value(tds, self.dividend_df["pay_date"])
        df["dividend"] = self.dividend_df["amount"].groupby(by).sum()
        df["dividend"] = df["dividend"].fillna(0.0)

        df["cumulative_dividend"] = df["dividend"].cumsum()

        df["port_value_with_dividend"] = df["port_value"] + df["cumulative_dividend"]

        df.index.name = "timestamp"
        df = df.reset_index()

        # sort column
        df = df[summary_columns]

        return df

    @cached_property
    def position_df(self) -> pd.DataFrame:
        """Position DataFrame.

        Returns
        -------
        pd.DataFrame
            - timestamp
            - symbol
            - volume
            - avg_cost_price
            - close_price
            - close_value
        """
        df = self._position_df.copy()

        if df.empty:
            df = pd.DataFrame(columns=position_columns)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df

        # close df
        symbol_list = df["symbol"].unique().tolist()
        start_date = utils.date_to_str(df["timestamp"].min())
        end_date = utils.date_to_str(df["timestamp"].max())
        close_price_df = self._sdr.get_data_symbol_daily(
            field=fld.D_CLOSE,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        close_price_df = close_price_df.stack()
        close_price_df.index.names = ["timestamp", "symbol"]
        close_price_df.name = "close_price"
        close_price_df = close_price_df.reset_index()

        # merge close_price_df and position_df
        df = df.merge(
            close_price_df, on=["timestamp", "symbol"], how="left", validate="1:1"
        )
        df["close_value"] = df["close_price"] * df["volume"]

        # sort column
        df = df[position_columns]

        return df

    @cached_property
    def trade_df(self) -> pd.DataFrame:
        """Trade DataFrame.

        Returns
        -------
        pd.DataFrame
            - matched_at
            - symbol
            - side
            - volume
            - price
            - commission
        """
        df = self._trade_df.copy()
        df["side"] = df["volume"].apply(
            lambda x: fld.SIDE_BUY if x > 0 else fld.SIDE_SELL
        )
        df["volume"] = df["volume"].abs()
        df["commission"] = df["price"] * df["volume"] * df["pct_commission"]
        df = df.drop(columns=["pct_commission"])

        # sort column
        df = df[trade_columns]

        return df

    @cached_property
    def dividend_df(self) -> pd.DataFrame:
        """Dividend DataFrame.

        Returns
        -------
        pd.DataFrame
            - ex_date
            - symbol
            - dps
            - volume
            - amount
            - before_ex_date
            - pay_date
        """
        position_df = self.position_df.copy()

        if position_df.empty:
            df = pd.DataFrame(columns=dividend_columns)
            df["ex_date"] = pd.to_datetime(df["ex_date"])
            df["before_ex_date"] = pd.to_datetime(df["before_ex_date"])
            df["pay_date"] = pd.to_datetime(df["pay_date"])
            return df

        # Get cash dividend dataframe
        symbol_list = position_df["symbol"].unique().tolist()
        start_date = utils.date_to_str(position_df["timestamp"].min())
        end_date = utils.date_to_str(position_df["timestamp"].max())
        cash_dvd_df = self._sdr.get_dividend(
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
            ca_type_list=["CD"],
        )

        cash_dvd_df["pay_date"] = cash_dvd_df["pay_date"].fillna(cash_dvd_df["ex_date"])

        cash_dvd_df["before_ex_date"] = cash_dvd_df["ex_date"] - self._sdr._custom_business_day(1)  # type: ignore

        position_df = position_df.rename(columns={"timestamp": "before_ex_date"})

        df = cash_dvd_df.merge(
            position_df, how="inner", on=["before_ex_date", "symbol"], sort=True
        )

        df["amount"] = df["dps"] * df["volume"]

        # sort column
        df = df[dividend_columns]

        return df

    @cached_property
    def stat_df(self) -> pd.DataFrame:
        """Stat DataFrame.

        Returns
        -------
        pd.DataFrame
            columns
                - port_value
                - port_value_with_dividend
            indexes
                - pct_net_profit
                - cagr
                - pct_maximum_drawdown
                - cagr_divided_maxdd
                - pct_win_per_trade
                - std
                - cagr_divided_std
                - pct_exposure
                - total_commission
                - initial_capital
                - ending_capital
                - net_profit
                - maximum_drawdown
                - all_trades
                - avg_profit_loss
                - pct_avg_profit_loss
                - avg_bar_held
                - win_trades
                - total_profit
                - avg_profit
                - pct_avg_profit
                - avg_win_bar_held
                - max_win_consecutive
                - loss_trades
                - total_loss
                - avg_loss
                - pct_avg_loss
                - avg_lose_bar_held
                - max_lose_consecutive
                - start_date
                - end_date
                - pct_commission
                - pct_buy_slip
                - pct_sell_slip
        """
        stat_dict = {
            # Highlight
            "pct_net_profit": self.pct_net_profit,
            "cagr": self.cagr,
            "pct_maximum_drawdown": self.pct_maximum_drawdown,
            "cagr_divided_maxdd": self.cagr_divided_maxdd,
            "pct_win_per_trade": self.pct_win_per_trade,
            "std": self.std,
            "cagr_divided_std": self.cagr_divided_std,
            "pct_exposure": self.pct_exposure,
            "total_commission": self.total_commission,
            # Stat
            "initial_capital": self.initial_capital,
            "ending_capital": self.ending_capital,
            "net_profit": self.net_profit,
            "maximum_drawdown": self.maximum_drawdown,
            "all_trades": self.all_trades,
            "avg_profit_loss": self.avg_profit_loss,
            "pct_avg_profit_loss": self.pct_avg_profit_loss,
            "avg_bar_held": self.avg_bar_held,
            "win_trades": self.win_trades,
            "total_profit": self.total_profit,
            "avg_profit": self.avg_profit,
            "pct_avg_profit": self.pct_avg_profit,
            "avg_win_bar_held": self.avg_win_bar_held,
            "max_win_consecutive": self.max_win_consecutive,
            "loss_trades": self.loss_trades,
            "total_loss": self.total_loss,
            "avg_loss": self.avg_loss,
            "pct_avg_loss": self.pct_avg_loss,
            "avg_lose_bar_held": self.avg_lose_bar_held,
            "max_lose_consecutive": self.max_lose_consecutive,
            # Setup
            "start_date": self.start_date,
            "end_date": self.end_date,
            "pct_commission": self.pct_commission,
            "pct_buy_slip": self.pct_buy_slip,
            "pct_sell_slip": self.pct_sell_slip,
        }

        df = pd.DataFrame(stat_dict).T

        # sort columns
        df = df[self._nav_df.columns]

        return df

    @cached_property
    def summary_trade_df(self) -> pd.DataFrame:
        """Summary Trade DataFrame. Each row is sell.

        Returns
        -------
        pd.DataFrame
            - exit_at
            - symbol
            - avg_cost_price
            - sell_price
            - volume
            - commission
            - return
            - pct_return
            - entry_at
            - hold_days
        """
        trade_df = self.trade_df.copy()

        # avg cost price
        trade_df = self._summary_trade_avg_cost_price(trade_df)

        # sell all in position
        df = self._summary_trade_sell_all_position()
        assert_index_equal(df.columns.sort_values(), trade_df.columns.sort_values())
        trade_df = pd.concat([trade_df, df], ignore_index=True)

        # datetime in
        trade_df = self._summary_trade_entry_at(trade_df)

        df = trade_df[trade_df["side"] == fld.SIDE_SELL]

        # sell price
        df = df.rename(columns={"price": "sell_price", "matched_at": "exit_at"})

        # commission from buy and sell
        df["commission"] = (
            (df["sell_price"] + df["avg_cost_price"])
            * df["volume"]
            * self.pct_commission
        ).abs()

        # return
        df["return"] = ((df["sell_price"] - df["avg_cost_price"]) * df["volume"]) - df[
            "commission"
        ]

        # pct_return
        df["pct_return"] = df["return"] / df["avg_cost_price"] / df["volume"]

        # hold days
        df["hold_days"] = (df["exit_at"] - df["entry_at"]).dt.days

        return df[summary_trade_columns]

    """
    Stat
    """

    @property
    @return_nan_on_failure
    def pct_net_profit(self) -> pd.Series:
        """Net profit divided by initial capital."""
        return self.net_profit / self.initial_capital

    @property
    @return_nan_on_failure
    def cagr(self) -> pd.Series:
        """Compound annual growth rate (CAGR)"""
        return (self.ending_capital / self.initial_capital) ** (1 / self._n_year) - 1

    @property
    @return_nan_on_failure
    def pct_maximum_drawdown(self) -> pd.Series:
        """Percent maximum drawdown."""
        nav = self._nav_df
        return (nav / nav.cummax() - 1).min()

    @property
    @return_nan_on_failure
    def cagr_divided_maxdd(self) -> pd.Series:
        """Compound Annual % Return divided by Max.

        system % drawdown.
        """
        return self.cagr / self.pct_maximum_drawdown.abs()

    @property
    @return_nan_on_failure
    def pct_win_per_trade(self) -> float:
        """Percent of win trades."""
        return self.win_trades / self.all_trades

    @property
    @return_nan_on_failure
    def std(self) -> pd.Series:
        """Standard deviation of profit/loss."""
        nav = self._nav_df
        return_per_day = nav / nav.shift(1) - 1
        trade_date_per_year = nav.shape[0] / self._n_year
        return return_per_day.std() * (trade_date_per_year**0.5)

    @property
    @return_nan_on_failure
    def cagr_divided_std(self) -> pd.Series:
        """Compound Annual % Return divided by Standard deviation."""
        return self.cagr / self.std

    @property
    @return_nan_on_failure
    def pct_exposure(self) -> pd.Series:
        """Percent of exposure."""
        df = self.summary_df
        df["port_value"] = df["total_market_value"] / df["port_value"]
        df["port_value_with_dividend"] = (
            df["total_market_value"] / df["port_value_with_dividend"]
        )
        return df[["port_value", "port_value_with_dividend"]].mean()

    @property
    @return_nan_on_failure
    def total_commission(self) -> float:
        """Total commission."""
        return self.summary_df["commission"].sum()

    @property
    @return_nan_on_failure
    def initial_capital(self) -> float:
        """Initial capital."""
        return self._initial_capital

    @property
    @return_nan_on_failure
    def ending_capital(self) -> pd.Series:
        """Ending capital."""
        return self._nav_df.iloc[-1]

    @property
    @return_nan_on_failure
    def net_profit(self) -> pd.Series:
        """Net profit."""
        return self.ending_capital - self.initial_capital

    @property
    @return_nan_on_failure
    def maximum_drawdown(self) -> pd.Series:
        """Maximum drawdown."""
        nav = self._nav_df
        return (nav - nav.cummax()).min()

    @property
    @return_nan_on_failure
    def all_trades(self) -> int:
        """Total number of trades."""
        df = self.summary_trade_df
        return df.shape[0]

    @property
    @return_nan_on_failure
    def avg_profit_loss(self) -> pd.Series:
        """Average profit/loss.

        also known as Expectancy ($) - (Profit of winners + Loss of losers)/(number of trades), represents expected dollar gain/loss per trade
        """
        return self.net_profit / self.all_trades

    @property
    @return_nan_on_failure
    def pct_avg_profit_loss(self) -> float:
        """Percent average profit/loss.

        also known as Expectancy (%) - '(% Profit of winners + % Loss of losers)/(number of trades), represents expected percent gain/loss per trade
        """
        return (
            (self.pct_avg_profit * self.win_trades)
            + (self.pct_avg_loss * self.loss_trades)
        ) / self.all_trades

    @property
    @return_nan_on_failure
    def avg_bar_held(self) -> float:
        """sum of bars in trades / number of trades."""
        df = self.summary_trade_df
        return df["hold_days"].mean()

    @property
    @return_nan_on_failure
    def win_trades(self) -> int:
        """Number of win trades."""
        return self._is_win_trade.sum()

    @property
    @return_nan_on_failure
    def total_profit(self) -> float:
        """Total profit."""
        df = self.summary_trade_df
        df = df[self._is_win_trade]
        return df["return"].sum()

    @property
    @return_nan_on_failure
    def avg_profit(self) -> float:
        """Average profit."""
        df = self.summary_trade_df
        df = df[self._is_win_trade]
        return df["return"].mean()

    @property
    @return_nan_on_failure
    def pct_avg_profit(self) -> float:
        """Percent average profit."""
        df = self.summary_trade_df
        df = df[self._is_win_trade]
        return df["pct_return"].mean()

    @property
    @return_nan_on_failure
    def avg_win_bar_held(self) -> float:
        """Average win bar held."""
        df = self.summary_trade_df
        df = df[self._is_win_trade]
        return df["hold_days"].mean()

    @property
    @return_nan_on_failure
    def max_win_consecutive(self) -> int:
        """Maximum win consecutive."""
        s = self._is_win_trade
        return (~s).cumsum()[s].value_counts().max()

    @property
    @return_nan_on_failure
    def loss_trades(self) -> int:
        """Number of loss trades."""
        return (~self._is_win_trade).sum()

    @property
    @return_nan_on_failure
    def total_loss(self) -> float:
        """Total loss."""
        df = self.summary_trade_df
        df = df[~self._is_win_trade]
        return df["return"].sum()

    @property
    @return_nan_on_failure
    def avg_loss(self) -> float:
        """Average loss."""
        df = self.summary_trade_df
        df = df[~self._is_win_trade]
        return df["return"].mean()

    @property
    @return_nan_on_failure
    def pct_avg_loss(self) -> float:
        """Percent average loss."""
        df = self.summary_trade_df
        df = df[~self._is_win_trade]
        return df["pct_return"].mean()

    @property
    @return_nan_on_failure
    def avg_lose_bar_held(self) -> float:
        """Average lose bar held."""
        df = self.summary_trade_df
        df = df[~self._is_win_trade]
        return df["hold_days"].mean()

    @property
    @return_nan_on_failure
    def max_lose_consecutive(self) -> int:
        """Maximum lose consecutive."""
        s = ~self._is_win_trade
        return (~s).cumsum()[s].value_counts().max()

    @property
    def start_date(self) -> datetime:
        """Start date."""
        out = self._nav_df.index[0]
        assert isinstance(out, datetime)
        return out

    @property
    def end_date(self) -> datetime:
        """End date."""
        out = self._nav_df.index[-1]
        assert isinstance(out, datetime)
        return out

    @property
    def pct_commission(self) -> float:
        """Percent commission."""
        return self._pct_commission

    @property
    def pct_buy_slip(self) -> float:
        """Percent buy slip."""
        return self._pct_buy_slip

    @property
    def pct_sell_slip(self) -> float:
        """Percent sell slip."""
        return self._pct_sell_slip

    @property
    def _n_year(self) -> float:
        """Number of years."""
        return (self.end_date - self.start_date).days / 365

    @property
    def _is_win_trade(self) -> pd.Series:
        """Is win trade."""
        return self.summary_trade_df["return"] > 0

    """
    Protected
    """

    @cached_property
    def _nav_df(self) -> pd.DataFrame:
        return self.summary_df.set_index("timestamp")[
            ["port_value", "port_value_with_dividend"]
        ]

    def _summary_trade_avg_cost_price(self, trade_df: pd.DataFrame) -> pd.DataFrame:
        """Add avg_cost_price to trade_df."""
        pos_df = self.position_df[["timestamp", "symbol", "avg_cost_price"]]
        pos_df = pos_df.rename(columns={"timestamp": "matched_at"})

        # get cost price from tomorrow position
        pos_df["matched_at"] += self._sdr._custom_business_day(1)  # type: ignore

        # set index for merge
        df = trade_df.merge(pos_df, on=["matched_at", "symbol"], validate="1:1")

        return df

    def _summary_trade_sell_all_position(self) -> pd.DataFrame:
        """Add trade if sell all position.

        No commission. Sell at close price.
        """
        df = self.position_df.copy()

        df = df[df["timestamp"] == self.end_date]
        df = df.rename(columns={"close_price": "price"})
        df["side"] = fld.SIDE_SELL
        df["commission"] = 0
        df = df.drop(columns=["close_value"])

        df = df.rename(columns={"timestamp": "matched_at"})

        return df

    def _summary_trade_entry_at(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add entry_at to trade_df.

        datetime in is nearest buy.
        """
        df["entry_at"] = df.loc[df["side"] == fld.SIDE_BUY, "matched_at"]

        tmp = df.groupby(["symbol"]).fillna(method="pad")  # type: ignore
        df["entry_at"] = tmp["entry_at"]

        return df


def _searchsorted_value(series: pd.DatetimeIndex, value: pd.Series) -> pd.Series:
    idx = series.searchsorted(value.to_list())
    return series[idx]