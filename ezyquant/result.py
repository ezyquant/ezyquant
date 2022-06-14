from datetime import datetime
from functools import cached_property

import pandas as pd

from . import fields as fld
from . import utils
from .reader import SETDataReader

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
    "timestamp",
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
    # timestamp
    "symbol",
    "avg_cost_price",
    "sell_price",
    "volume",
    "commission",
    "return",
    "pct_return",
    "datetime_in",
    "hold_days",
]


def return_nan_on_failure(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ZeroDivisionError:
            return nan

    return wrapper


class SETResult:
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
        """SETResult.

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
                - timestamp
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

        self._sdr = SETDataReader()

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
            self.trade_df.set_index("timestamp")["commission"].groupby(level=0).sum()
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
        position_df = self._position_df.copy()

        if position_df.empty:
            return pd.DataFrame(columns=position_columns)

        # close df
        symbol_list = position_df["symbol"].unique().tolist()
        start_date = utils.date_to_str(position_df["timestamp"].min())
        end_date = utils.date_to_str(position_df["timestamp"].max())
        close_price_df = self._sdr.get_data_symbol_daily(
            field=fld.D_CLOSE,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )

        close_price_df = close_price_df.stack()  # type: ignore
        close_price_df.index.names = ["timestamp", "symbol"]
        close_price_df.name = "close_price"
        close_price_df = close_price_df.reset_index()

        # merge close_price_df and position_df
        df = position_df.merge(
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
            - timestamp
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
            return pd.DataFrame(columns=dividend_columns)

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

        cash_dvd_df["before_ex_date"] = self._shift_trade_date(
            cash_dvd_df["ex_date"], periods=1
        )

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
        nav = self._nav_df
        return (nav / nav.cummax() - 1).min()

    @property
    @return_nan_on_failure
    def cagr_divided_maxdd(self) -> pd.Series:
        return self.cagr / -self.pct_maximum_drawdown  # type: ignore

    @property
    @return_nan_on_failure
    def pct_win_per_trade(self) -> float:
        return self.win_trades / self.all_trades

    @property
    @return_nan_on_failure
    def std(self) -> pd.Series:
        nav = self._nav_df
        return_per_day = nav / nav.shift(1) - 1
        td_per_year = nav.shape[0] / self._n_year
        return return_per_day.std() * (td_per_year**0.5)

    @property
    @return_nan_on_failure
    def cagr_divided_std(self) -> pd.Series:
        return self.cagr / self.std

    @property
    @return_nan_on_failure
    def pct_exposure(self) -> pd.Series:
        """Stock hold divided by total_market_value."""
        df = self.summary_df
        df["port_value"] = df["total_market_value"] / df["port_value"]
        df["port_value_with_dividend"] = (
            df["total_market_value"] / df["port_value_with_dividend"]
        )
        return df[["port_value", "port_value_with_dividend"]].mean()

    @property
    @return_nan_on_failure
    def total_commission(self) -> float:
        return self.summary_df["commission"].sum()

    @property
    @return_nan_on_failure
    def initial_capital(self) -> float:
        return self._initial_capital

    @property
    @return_nan_on_failure
    def ending_capital(self) -> pd.Series:
        return self._nav_df.iloc[-1]

    @property
    @return_nan_on_failure
    def net_profit(self) -> pd.Series:
        return self.ending_capital - self.initial_capital

    @property
    @return_nan_on_failure
    def maximum_drawdown(self) -> pd.Series:
        nav = self._nav_df
        maxcum = nav.cummax()
        drawdown = nav - maxcum
        return drawdown.min()

    @property
    @return_nan_on_failure
    def all_trades(self) -> int:
        df = self._summary_trade_df
        return df.shape[0]

    @property
    @return_nan_on_failure
    def avg_profit_loss(self) -> pd.Series:  # TODO: change name to expectancy
        return self.net_profit / self.all_trades

    @property
    @return_nan_on_failure
    def pct_avg_profit_loss(self) -> float:  # TODO: change name to pct_expectancy
        return (
            (self.pct_avg_profit * self.win_trades)
            + (self.pct_avg_loss * self.loss_trades)
        ) / self.all_trades

    @property
    @return_nan_on_failure
    def avg_bar_held(self) -> float:
        df = self._summary_trade_df
        out = df["hold_days"].mean()
        assert isinstance(out, float)
        return out

    @property
    @return_nan_on_failure
    def win_trades(self) -> int:
        df = self._summary_trade_df
        df = df[df["pct_return"] >= 0]
        return df.shape[0]

    @property
    @return_nan_on_failure
    def total_profit(self) -> float:
        df = self._summary_trade_df
        df = df[df["return"] > 0]
        return df["return"].sum()

    @property
    @return_nan_on_failure
    def avg_profit(self) -> float:
        df = self._summary_trade_df
        df = df[df["pct_return"] > 0]
        out = df["return"].mean()
        assert isinstance(out, float)
        return out

    @property
    @return_nan_on_failure
    def pct_avg_profit(self) -> float:
        df = self._summary_trade_df
        df = df[df["pct_return"] > 0]
        out = df["pct_return"].mean()
        assert isinstance(out, float)
        return out

    @property
    @return_nan_on_failure
    def avg_win_bar_held(self) -> float:
        df = self._summary_trade_df
        df = df[df["pct_return"] > 0]
        out = df["hold_days"].mean()
        assert isinstance(out, float)
        return out

    @property
    @return_nan_on_failure
    def max_win_consecutive(self) -> int:
        df = self._summary_trade_df
        is_win = df["pct_return"] > 0
        cum_win = is_win.cumsum()
        return cum_win.max()

    @property
    @return_nan_on_failure
    def loss_trades(self) -> int:
        df = self._summary_trade_df
        df = df[df["pct_return"] < 0]
        return df.shape[0]

    @property
    @return_nan_on_failure
    def total_loss(self) -> float:
        df = self._summary_trade_df
        df = df[df["return"] <= 0]
        return df["return"].sum()

    @property
    @return_nan_on_failure
    def avg_loss(self) -> float:
        df = self._summary_trade_df
        df = df[df["pct_return"] <= 0]
        out = df["return"].mean()
        assert isinstance(out, float)
        return out

    @property
    @return_nan_on_failure
    def pct_avg_loss(self) -> float:
        df = self._summary_trade_df
        df = df[df["pct_return"] <= 0]
        out = df["pct_return"].mean()
        assert isinstance(out, float)
        return out

    @property
    @return_nan_on_failure
    def avg_lose_bar_held(self) -> float:
        df = self._summary_trade_df
        df = df[df["pct_return"] <= 0]
        out = df["hold_days"].mean()
        assert isinstance(out, float)
        return out

    @property
    @return_nan_on_failure
    def max_lose_consecutive(self) -> int:
        df = self._summary_trade_df
        is_lose = df["pct_return"] <= 0
        cum_lose = is_lose.cumsum()
        return cum_lose.max()

    @property
    def start_date(self) -> datetime:
        out = self._nav_df.index[0]
        assert isinstance(out, datetime)
        return out

    @property
    def end_date(self) -> datetime:
        out = self._nav_df.index[-1]
        assert isinstance(out, datetime)
        return out

    @property
    def pct_commission(self) -> float:
        return self._pct_commission

    @property
    def pct_buy_slip(self) -> float:
        return self._pct_buy_slip

    @property
    def pct_sell_slip(self) -> float:
        return self._pct_sell_slip

    @property
    def _n_year(self) -> float:
        """Number of year."""
        return (self.end_date - self.start_date).days / 365

    """
    Protected
    """

    @cached_property
    def _nav_df(self) -> pd.DataFrame:
        return self.summary_df.set_index("timestamp")[
            ["port_value", "port_value_with_dividend"]
        ]

    @cached_property
    def _summary_trade_df(self) -> pd.DataFrame:
        """Each row is sell.

        Datetime in is nearest buy. Sell all in position.
        """
        trade_df = self.trade_df.copy()
        position_df = self.position_df.copy()

        trade_df = self._summary_trade_cost_price(trade_df, position_df)

        # sell all in position
        trade_df = self._summary_trade_sell_all_position(trade_df, position_df)

        # datetime in
        trade_df = self._summary_trade_datetime_in(trade_df)

        df = trade_df[trade_df["side"] == fld.SIDE_SELL]

        # sell price
        df = df.rename(columns={"price": "sell_price"})

        # commission
        df["commission"] = (
            (df["sell_price"] + df["avg_cost_price"])
            * df["volume"]
            * self.pct_commission
        )

        # return
        df["return"] = ((df["sell_price"] - df["avg_cost_price"]) * df["volume"]) - df[
            "commission"
        ]

        # pct_return
        df["pct_return"] = df["return"] / df["avg_cost_price"] / df["volume"]

        # hold days
        df["hold_days"] = (df["timestamp"] - df["datetime_in"]).dt.days

        df = df.set_index("timestamp")

        return df[summary_trade_columns]

    def _summary_trade_cost_price(
        self, trade_df: pd.DataFrame, pos_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Add avg_cost_price to trade_df."""
        pos_df = pos_df[["timestamp", "symbol", "avg_cost_price"]]

        # get cost price from tomorrow position
        pos_df["timestamp"] = self._shift_trade_date(pos_df["timestamp"], periods=-1)

        # set index for merge
        df = trade_df.merge(pos_df, on=["timestamp", "symbol"], validate="1:1")

        return df

    def _summary_trade_sell_all_position(
        self, trade_df: pd.DataFrame, position_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Add trade if sell all position."""
        pos_df = position_df.copy()

        df = pos_df[pos_df["timestamp"] == self.end_date]
        df = df.rename(columns={"close_price": "price"})  # type: ignore
        df["side"] = fld.SIDE_SELL
        df["commission"] = 0
        df = df.drop(columns=["close_value"])

        assert trade_df.columns.sort_values().equals(df.columns.sort_values())

        df = pd.concat([trade_df, df])
        return df

    @staticmethod
    def _summary_trade_datetime_in(df: pd.DataFrame) -> pd.DataFrame:
        """Add datetime_in to trade_df."""
        df["datetime_in"] = df["timestamp"]
        df.loc[df["side"] == fld.SIDE_SELL, "datetime_in"] = nan

        if not df.empty:
            df["datetime_in"] = df.groupby(["symbol"]).fillna(method="pad")[  # type: ignore
                "datetime_in"
            ]

        return df

    def _shift_trade_date(self, series: pd.Series, periods: int) -> pd.Series:
        """Add/sub series trade date by periods.

        Parameters
        ----------
        series : pd.Series
            Series to shift.
        periods : int
            periods to shift. 1 is yesterday, -1 is tomorrow.

        Returns
        -------
        pd.Series
            Shifted series.
        """
        tds = self._sdr.get_trading_dates()

        td_df = pd.DataFrame({"trade_date": pd.to_datetime(tds)})
        td_df["sub_trade_date"] = td_df["trade_date"].shift(periods)

        df = series.to_frame("trade_date").merge(
            td_df, how="left", on="trade_date", validate="m:1"
        )

        return df["sub_trade_date"]


def _searchsorted_value(series: pd.DatetimeIndex, value: pd.Series) -> pd.Series:
    idx = series.searchsorted(value.to_list())
    return series[idx]  # type: ignore
