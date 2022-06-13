from functools import cached_property

import pandas as pd

from . import fields as fld
from .reader import SETDataReader

summary_df_columns = [
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
    "price",
    "volume",
    "commission",
]


class SETResult:
    def __init__(
        self, cash_series: pd.Series, position_df: pd.DataFrame, trade_df: pd.DataFrame
    ):
        """SETResult

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
        df = self._cash_series.to_frame("cash")

        df["cashflow"] = df["cash"].diff().fillna(0)

        df["commission"] = (
            self.trade_df.set_index("timestamp")["commission"].groupby(level=0).sum()
        )
        df["commission"] = df["commission"].fillna(0)

        df["total_market_value"] = (
            self.position_df.set_index("timestamp")["close_value"]
            .groupby(level=0)
            .sum()
        )
        df["total_market_value"] = df["total_market_value"].fillna(0)

        df["port_value"] = df["total_market_value"] + df["cash"]

        df["dividend"] = (
            self.dividend_df.set_index("timestamp")["amount"].groupby(level=0).sum()
        )
        df["dividend"] = df["dividend"].fillna(0)

        df["cumulative_dividend"] = df["dividend"].cumsum()

        df["port_value_with_dividend"] = df["port_value"] + df["cumulative_dividend"]

        df.index.name = "timestamp"
        df = df.reset_index()

        # sort column
        df = df[summary_df_columns]

        return df

    @cached_property
    def position_df(self) -> pd.DataFrame:
        # close df
        close_price_df = self._sdr.get_data_symbol_daily(
            field=fld.D_CLOSE,
            symbol_list=self._position_df["symbol"].unique().tolist(),
            start_date=self._position_df["timestamp"].min(),
            end_date=self._position_df["timestamp"].max(),
        )
        close_price_df = close_price_df.stack()  # type: ignore
        close_price_df.index.names = ["timestamp", "symbol"]
        close_price_df.name = "close_price"
        close_price_df = close_price_df.reset_index()

        # merge close_price_df and position_df
        df = self._position_df.merge(
            close_price_df, on=["timestamp", "symbol"], how="left", validate="1:1"
        )
        df["close_value"] = df["close_price"] * df["volume"]

        # sort column
        df = df[position_columns]

        return df

    @cached_property
    def trade_df(self) -> pd.DataFrame:
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
        # TODO: [EZ-77] dividend_df
        return pd.DataFrame(columns=["timestamp", "amount"])

    @cached_property
    def stat_df(self) -> pd.DataFrame:
        # TODO: [EZ-76] stat_df
        return pd.DataFrame()
