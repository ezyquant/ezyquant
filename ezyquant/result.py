from functools import cached_property

import pandas as pd

from . import fields as fld
from . import utils
from .reader import SETDataReader

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


class SETResult:
    def __init__(
        self, cash_series: pd.Series, position_df: pd.DataFrame, trade_df: pd.DataFrame
    ):
        """SETResult.

        Parameters
        ----------
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
        df["side"] = df["volume"].apply(lambda x: "buy" if x > 0 else "sell")
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

        cash_dvd_df["before_ex_date"] = self._sub_one_trade_date(cash_dvd_df["ex_date"])

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
        """
        # TODO: [EZ-76] stat_df
        return pd.DataFrame()

    """
    Protected
    """

    def _sub_one_trade_date(self, series: pd.Series) -> pd.Series:
        td_list = self._sdr.get_trading_dates()

        td_df = pd.DataFrame({"trade_date": pd.to_datetime(td_list)})
        td_df["sub_trade_date"] = td_df["trade_date"].shift(1)

        df = series.to_frame("trade_date").merge(
            td_df, how="left", on="trade_date", validate="m:1"
        )

        return df["sub_trade_date"]


def _searchsorted_value(series: pd.DatetimeIndex, value: pd.Series) -> pd.Series:
    idx = series.searchsorted(value.to_list())
    return series[idx]  # type: ignore
