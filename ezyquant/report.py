import math
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import quantstats as qs
from pandas.testing import assert_index_equal
from quantstats import stats as qs_stats
from quantstats import utils as qs_utils

from ezyquant import fields as fld
from ezyquant import utils
from ezyquant.reader import _SETDataReaderCached
from ezyquant.utils import cached_property

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
    "cost_price",
    "close_price",
    "close_value",
    "pct_profit",
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
    "cost_price",
    "sell_price",
    "volume",
    "commission",
    "return",
    "pct_return",
    "entry_at",
    "hold_days",
]

DEFAULT_PERIOD_PER_YEAR = 252


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
        initial_capital: float
            initial capital.
        pct_commission: float
            percent commission.
        pct_buy_slip: float
            percent of buy price increase.
        pct_sell_slip: float
            percent of sell price decrease.
        cash_series: pd.Series
            series of cash.
        position_df: pd.DataFrame
            dataframe of position.
                - timestamp
                - symbol
                - volume
                - cost_price
        trade_df: pd.DataFrame
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

        df["cashflow"] = df["cash"] - df["cash"].shift(
            1, fill_value=self.initial_capital
        )

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
        dividend_df = self.dividend_df.copy()
        dividend_df["pay_date"] += self._sdr._SETBusinessDay(0)
        df["dividend"] = (
            dividend_df.set_index("pay_date")["amount"].groupby(level=0).sum()
        )
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
        """SETPosition DataFrame.

        Returns
        -------
        pd.DataFrame
            - timestamp
            - symbol
            - volume
            - cost_price
            - close_price
            - close_value
            - pct_profit
        """
        df = self._position_df.copy()

        if df.empty:
            df = pd.DataFrame(columns=position_columns)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df

        df["close_value"] = df["close_price"] * df["volume"]
        df["pct_profit"] = (df["close_price"] / df["cost_price"]) - 1.0

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

        cash_dvd_df["before_ex_date"] = cash_dvd_df["ex_date"] - self._sdr._SETBusinessDay(1)  # type: ignore

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

                - nav names

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
        if not isinstance(df, pd.DataFrame):
            msg = "df must be pd.DataFrame"
            raise TypeError(msg)

        return df

    @cached_property
    def summary_trade_df(self) -> pd.DataFrame:
        """Summary Trade DataFrame. Each row is sell.

        Returns
        -------
        pd.DataFrame
            - exit_at
            - symbol
            - cost_price
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
        trade_df = self._summary_trade_cost_price(trade_df)

        # sell all in position
        df = self._summary_trade_sell_all_position()
        assert_index_equal(df.columns.sort_values(), trade_df.columns.sort_values())
        trade_df = pd.concat([trade_df, df], ignore_index=True)

        # datetime in
        trade_df = self._summary_trade_entry_at(trade_df)

        df = trade_df[trade_df["side"] == fld.SIDE_SELL]
        df = df.reset_index(drop=True)

        # sell price
        df = df.rename(columns={"price": "sell_price", "matched_at": "exit_at"})

        # commission from buy and sell
        df["commission"] = (
            (df["sell_price"] + df["cost_price"]) * df["volume"] * self._pct_commission
        ).abs()

        # return
        df["return"] = ((df["sell_price"] - df["cost_price"]) * df["volume"]) - df[
            "commission"
        ]

        # pct_return
        df["pct_return"] = df["return"] / df["cost_price"] / df["volume"]

        # hold days
        df["hold_days"] = (df["exit_at"] - df["entry_at"]).dt.days

        return df[summary_trade_columns]

    @cached_property
    def cumulative_return_df(self) -> pd.DataFrame:
        """Cumulative Return DataFrame.

        Returns
        -------
        pd.DataFrame
            index is trade date, columns is nav names
        """
        return self._nav_df / self.initial_capital

    @cached_property
    def monthly_return_df(self) -> pd.DataFrame:
        """Monthly Return DataFrame.

        Returns
        -------
        pd.DataFrame
        """
        return pd.concat(
            [qs_stats.monthly_returns(self._nav_df[i]) for i in self._nav_df.columns],
            keys=list(self._nav_df.columns),
            names=["name", "year"],
        )

    @cached_property
    def price_distribution_df(self) -> pd.DataFrame:
        """Price Distribution DataFrame.

        Returns
        -------
        pd.DataFrame

        Examples
        --------
        >>>                     frequency
        ... pct_return
        ... (-0.25, -0.2]             153
        ... (-0.2, -0.15]             352
        ... (-0.15, -0.1]             459
        ... (-0.1, -0.05]             698
        ... (-0.05, -0.0]            1268
        ... (-0.0, 0.05]             1256
        ... (0.05, 0.1]               571
        ... (0.1, 0.15]               374
        ... (0.15, 0.2]               181
        """
        pct_return = self.summary_trade_df["pct_return"]

        # bins
        step = 0.05

        min_r = pct_return.min()
        max_r = pct_return.max()

        if np.isnan(min_r) and np.isnan(max_r):
            min_r, max_r = 0, 0
        else:
            if min_r % step == 0:
                min_r -= step
            else:
                min_r = math.ceil(min_r / step - 1) * step
            max_r += step

        bins = np.arange(min_r, max_r, step)

        # histogram
        price_dis = pct_return.groupby(pd.cut(pct_return, bins)).count()  # type: ignore

        return price_dis.to_frame("frequency")

    @cached_property
    def drawdown_percent_df(self) -> pd.DataFrame:
        """Drawdown Percent DataFrame.

        Returns
        -------
        pd.DataFrame
            index is trade date, columns is nav names
        """
        return qs_stats.to_drawdown_series(self._nav_df)

    def to_excel(self, path: str):
        """Export to Excel.

        Parameters
        ----------
        path: str
            Path to Excel file.
        """
        with pd.ExcelWriter(
            path,
            engine="xlsxwriter",
            datetime_format="YYYY-MM-DD",
        ) as writer:
            self.summary_df.to_excel(writer, sheet_name="summary", index=False)
            self.position_df.to_excel(writer, sheet_name="position", index=False)
            self.trade_df.to_excel(writer, sheet_name="trade", index=False)
            self.stat_df.to_excel(writer, sheet_name="stat")
            self.summary_trade_df.to_excel(
                writer, sheet_name="summary_trade", index=False
            )
            self.cumulative_return_df.to_excel(writer, sheet_name="cumulative_return")
            self.monthly_return_df.to_excel(writer, sheet_name="monthly_return")
            self.dividend_df.to_excel(writer, sheet_name="dividend", index=False)
            self.price_distribution_df.to_excel(writer, sheet_name="price_distribution")
            self.drawdown_percent_df.to_excel(writer, sheet_name="drawdown_percent")

    def to_snapshot(
        self,
        with_dividend=True,
        grayscale=False,
        figsize=(10, 8),
        title="Portfolio Summary",
        fontname="Arial",
        lw=1.5,
        mode="comp",
        subtitle=True,
        savefig=None,
        show=True,
        log_scale=False,
    ):
        """Generates a snapshot plot of portfolio performance. including Cumulative
        Return, Drawdown and Daily Return.

        Parameters
        ----------
        with_dividend : bool, optional
            Include dividend values in the portfolio values, by default True.
        grayscale : bool, optional
            Generate grayscale visualizations, by default False.
        figsize : tuple, optional
            Size of the figure for visualizations, by default (10, 8).
        title : str, optional
            Title of the plot, by default "Portfolio Summary".
        fontname : str, optional
            Font name for the plot, by default "Arial".
        lw : float, optional
            Line width for the plot, by default 1.5
        mode : str, optional
            Mode of returns calculation. 'comp' for compounded returns, 'sum' for simple returns, by default "comp"
        subtitle : bool, optional
            Display the subtitle "start date to end date" and "sharp ratio", by default True
        savefig : None, optional
            Saving the plot image, by default None
        show : bool, optional
            Display the plot if not return a Figure instead object instead, by default True
        log_scale : bool, optional
            Use a logarithmic scale for the y-axis, by default False

        Returns
        -------
        None
            Plot the portfolio performance that is base on "show" arguments.
        """
        return qs.plots.snapshot(
            returns=self._get_nav_series(with_dividend=with_dividend),
            grayscale=grayscale,
            figsize=figsize,
            title=title,
            fontname=fontname,
            lw=lw,
            mode=mode,
            subtitle=subtitle,
            savefig=savefig,
            show=show,
            log_scale=log_scale,
        )

    def to_html(
        self,
        with_dividend=True,
        benchmark: Optional[pd.DataFrame] = None,
        rf=0.0,
        grayscale=False,
        title="Strategy Tearsheet",
        output=None,
        compounded=True,
        periods_per_year=DEFAULT_PERIOD_PER_YEAR,
        download_filename="quantstats-tearsheet.html",
        figfmt="svg",
        template_path=None,
        match_dates=False,
        **kwargs,
    ):
        """Generates an HTML tearsheet for strategy performance analysis.

        Parameters
        ----------
        with_dividend : bool, optional
            Include dividend values in the portfolio values, by default True.
        benchmark : Optional[pd.DataFrame], optional
            Time-series of benchmark returns, by default is None.
        rf : float, optional
            Risk-free rate of return, by default is 0.
        grayscale : bool, optional
            Generate grayscale visualizations, by default False.
        title : str, optional
            Title of the tearsheet, by default "Strategy Tearsheet".
        output : None, optional
            Output file name for saving the HTML tearsheet If set to None,
            the tearsheet will be opened in the File Explorer instead of saving to a file., by default None.
        compounded : bool, optional
            Calculate compounded returns for performance metrics, by default True.
        periods_per_year : int, optional
            Number of periods per year for calculating annualized metrics, by default 252.
        download_filename : str, optional
            Output the file name HTML tearsheet, by default "quantstats-tearsheet.html"
        figfmt : str, optional
            Format of the saved figure file, by default "svg".
        template_path : None, optional
            Path to the custom template file for the HTML tearsheet, by default None
        match_dates : bool, optional
            Match the dates of strategy and benchmark returns, by default False.

        Returns
        -------
        None
            If output is None (HTML tearsheet is displayed in the browser).
        """
        return qs.reports.html(
            returns=self._get_nav_series(with_dividend=with_dividend),
            benchmark=benchmark,
            rf=rf,
            grayscale=grayscale,
            title=title,
            output=output,
            compounded=compounded,
            periods_per_year=periods_per_year,
            download_filename=download_filename,
            figfmt=figfmt,
            template_path=template_path,
            match_dates=match_dates,
            **kwargs,
        )

    def to_basic(
        self,
        with_dividend=True,
        benchmark: Optional[pd.DataFrame] = None,
        rf=0.0,
        grayscale=False,
        figsize=(8, 5),
        display=True,
        compounded=True,
        periods_per_year=DEFAULT_PERIOD_PER_YEAR,
        match_dates=False,
    ):
        """Calculate performance metrics and generate visualizations for a given
        strategy.

        Parameters
        ----------
        with_dividend : bool, optional
            Include dividend values in the portfolio values, by default True.
        benchmark : Optional[pd.DataFrame], optional
            Time-series of benchmark returns, by default is None.
        rf : float, optional
            Risk-free rate of return, by default is 0.
        grayscale : bool, optional
            Generate grayscale visualizations, by default False.
        figsize : tuple, optional
            Size of the figure for visualizations, by default (8, 5)
        display : bool, optional
            Display the performance metrics, by default True.
        compounded : bool, optional
            Calculate compounded returns for performance metrics, by default True
        periods_per_year : int, optional
            Number of periods per year for calculating annualized metrics, by default 252.
        match_dates : bool, optional
            Match the dates of strategy and benchmark returns, by default False.

        Returns
        -------
        None
            The function generates performance metrics and visualizations based on the provided parameters.
        """
        return qs.reports.basic(
            returns=self._get_nav_series(with_dividend=with_dividend),
            benchmark=benchmark,
            rf=rf,
            grayscale=grayscale,
            figsize=figsize,
            display=display,
            compounded=compounded,
            periods_per_year=periods_per_year,
            match_dates=match_dates,
        )

    def to_full(
        self,
        with_dividend=True,
        benchmark: Optional[pd.DataFrame] = None,
        rf=0.0,
        grayscale=False,
        figsize=(8, 5),
        display=True,
        compounded=True,
        periods_per_year=DEFAULT_PERIOD_PER_YEAR,
        match_dates=False,
    ):
        """Calculate performance metrics and generate visualizations for a given
        strategy.

        Parameters
        ----------
        with_dividend : bool, optional
            Include dividend values in the portfolio values, by default True.
        benchmark : Optional[pd.DataFrame], optional
            Time-series of benchmark returns, by default is None.
        rf : float, optional
            Risk-free rate of return, by default is 0.
        grayscale : bool, optional
            Generate grayscale visualizations, by default False.
        figsize : tuple, optional
            Size of the figure for visualizations, by default (8, 5).
        display : bool, optional
            Display the performance metrics, by default True.
        compounded : bool, optional
            Calculate compounded returns for performance metrics, by default True.
        periods_per_year : int, optional
            Number of periods per year for calculating annualized metrics, by default 252.
        match_dates : bool, optional
            Match the dates of strategy and benchmark returns, by default False.

        Returns
        -------
        None
            The function generates performance metrics and visualizations based on the provided parameters.
        """

        return qs.reports.full(
            returns=self._get_nav_series(with_dividend=with_dividend),
            benchmark=benchmark,
            rf=rf,
            grayscale=grayscale,
            figsize=figsize,
            display=display,
            compounded=compounded,
            periods_per_year=periods_per_year,
            match_dates=match_dates,
        )

    """
    Pipeline To Quantstats Reports
    """

    def _get_nav_series(self, with_dividend: bool = True) -> pd.Series:
        """Selects and returns a pandas Series containing the portfolio values. Before
        implementing it with the QuanStats libraries.

        Parameters
        ----------
        with_dividend : bool, optional
            Flag indicating whether to include dividend values in the portfolio values, by default True.

        Returns
        -------
        pd.Series
            Pandas Series containing the portfolio values based on the specified criteria.
        """
        return self._nav_df["portfolio_with_dividend" if with_dividend else "portfolio"]

    """
    Stat
    """

    @property
    @return_nan_on_failure
    def pct_net_profit(self) -> pd.Series:
        """Net profit divided by initial capital."""
        return self.net_profit / self.initial_capital

    @property
    def cagr(self) -> pd.Series:
        """Calculates the communicative annualized growth return (CAGR%) of access
        returns."""
        return qs_stats.cagr(self._nav_df)

    @property
    def pct_maximum_drawdown(self) -> pd.Series:
        """Calculates the maximum drawdown."""
        return qs_stats.max_drawdown(self._nav_df)

    @property
    def cagr_divided_maxdd(self) -> pd.Series:
        """Calculates the calmar ratio (CAGR% / MaxDD%)"""
        return qs_stats.calmar(self._nav_df)

    @property
    @return_nan_on_failure
    def pct_win_per_trade(self) -> float:
        """Percent of win trades."""
        return self.win_trades / self.all_trades

    @property
    def std(self) -> pd.Series:
        """Calculates the volatility of returns for a period."""
        return qs_stats.volatility(self._nav_df, periods=DEFAULT_PERIOD_PER_YEAR)

    @property
    @return_nan_on_failure
    def cagr_divided_std(self) -> pd.Series:
        """Compound Annual % Return divided by Standard deviation."""
        return self.cagr / self.std

    @property
    @return_nan_on_failure
    def pct_exposure(self) -> pd.Series:
        """Percent of exposure."""
        df = self.summary_df.copy()
        df["portfolio"] = df["total_market_value"] / df["port_value"]
        df["portfolio_with_dividend"] = (
            df["total_market_value"] / df["port_value_with_dividend"]
        )
        return df[["portfolio", "portfolio_with_dividend"]].mean()

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
        """Sum of bars in trades / number of trades."""
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
        return utils.count_max_true_consecutive(s)

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
        return utils.count_max_true_consecutive(s)

    @cached_property
    def start_date(self) -> datetime:
        """Start date."""
        out = self._nav_df.index[0]
        if not isinstance(out, datetime):
            msg = "start_date must be datetime"
            raise TypeError(msg)
        return out

    @cached_property
    def end_date(self) -> datetime:
        """End date."""
        out = self._nav_df.index[-1]
        if not isinstance(out, datetime):
            msg = "end_date must be datetime"
            raise TypeError(msg)
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
    def _is_win_trade(self) -> pd.Series:
        """Is win trade."""
        return self.summary_trade_df["return"] > 0

    """
    Protected
    """

    @cached_property
    def _nav_df(self) -> pd.DataFrame:
        df: pd.DataFrame = self.summary_df.set_index("timestamp")[
            ["port_value", "port_value_with_dividend"]
        ].rename(
            columns={
                "port_value": "portfolio",
                "port_value_with_dividend": "portfolio_with_dividend",
            }
        )
        df.loc[df.index[0] - timedelta(days=1)] = self._initial_capital  # type: ignore
        df = df.sort_index()
        return df

    def _summary_trade_cost_price(self, trade_df: pd.DataFrame) -> pd.DataFrame:
        """Add cost_price to trade_df."""
        pos_df = self.position_df[["timestamp", "symbol", "cost_price"]]
        pos_df = pos_df.rename(columns={"timestamp": "matched_at"})

        # get cost price from tomorrow position
        pos_df["matched_at"] += self._sdr._SETBusinessDay(1)

        # set index for merge
        df = trade_df.merge(
            pos_df, how="left", on=["matched_at", "symbol"], validate="1:1"
        )

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
        df = df.drop(columns=["close_value", "pct_profit"])

        df = df.rename(columns={"timestamp": "matched_at"})

        df = df.reset_index(drop=True)

        return df

    @staticmethod
    def _summary_trade_entry_at(df: pd.DataFrame) -> pd.DataFrame:
        """Add entry_at to trade_df.

        datetime in is nearest buy.
        """
        df["entry_at"] = df.loc[df["side"] == fld.SIDE_BUY, "matched_at"]

        tmp = df.groupby(["symbol"]).fillna(method="pad")  # type: ignore
        df["entry_at"] = tmp["entry_at"]

        return df


# Change default periods to 365
def cagr(returns, rf=0.0, compounded=True, periods=365):
    """Calculates the communicative annualized growth return (CAGR%) of access returns.

    If rf is non-zero, you must specify periods. In this case, rf is assumed to be
    expressed in yearly (annualized) terms
    """
    total = qs_utils._prepare_returns(returns, rf)
    if compounded:
        total = qs_stats.comp(total)
    else:
        total = np.sum(total)

    years = (returns.index[-1] - returns.index[0]).days / periods

    res = abs(total + 1.0) ** (1.0 / years) - 1  #   type: ignore

    if isinstance(returns, pd.DataFrame):
        res = pd.Series(res)
        res.index = returns.columns

    return res


qs_stats.cagr = cagr
