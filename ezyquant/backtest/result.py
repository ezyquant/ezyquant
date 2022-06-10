import pandas as pd

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


def make_position_df(
    position_df: pd.DataFrame, close_price_df: pd.DataFrame
) -> pd.DataFrame:
    """Make position dataframe from backtest logic to backtest result.

    Parameters
    ----------
    position_df : pd.DataFrame
        dataframe of position.
            - timestamp
            - symbol
            - volume
            - avg_cost_price
    close_price_df : pd.DataFrame
        dataframe of close price.
        index is trade date, columns are symbol, values are close price.

    Returns
    -------
    pd.DataFrame
        position df
            - timestamp
            - symbol
            - volume
            - avg_cost_price
            - close_price
            - close_value
    """
    # close df
    close_price_df = close_price_df.stack()  # type: ignore
    close_price_df.index.names = ["timestamp", "symbol"]
    close_price_df.name = "close_price"
    close_price_df = close_price_df.reset_index()

    # merge close_price_df and position_df
    position_df = position_df.merge(
        close_price_df, on=["timestamp", "symbol"], how="left", validate="1:1"
    )
    position_df["close_value"] = position_df["close_price"] * position_df["volume"]

    # sort column
    position_df = position_df[position_columns]

    return position_df


def make_trade_df(trade_df: pd.DataFrame) -> pd.DataFrame:
    """Make trade dataframe from backtest logic to backtest result.

    Parameters
    ----------
    trade_df : pd.DataFrame
        dataframe of trade.
            - timestamp
            - symbol
            - volume
            - price
            - pct_commission

    Returns
    -------
    pd.DataFrame
        trade df
            - timestamp
            - symbol
            - side
            - volume
            - price
            - commission
    """
    trade_df["side"] = trade_df["volume"].apply(lambda x: "buy" if x > 0 else "sell")
    trade_df["volume"] = trade_df["volume"].abs()
    trade_df["commission"] = (
        trade_df["price"] * trade_df["volume"] * trade_df["pct_commission"]
    )
    trade_df = trade_df.drop(columns=["pct_commission"])

    trade_df = trade_df[trade_columns]

    return trade_df


def make_summary_df(
    cash_series: pd.Series,
    trade_df: pd.DataFrame,
    position_df: pd.DataFrame,
    dividend_df: pd.DataFrame,
) -> pd.DataFrame:
    """Make summary dataframe from backtest logic to backtest result.

    Parameters
    ----------
    cash_series : pd.Series
        cash series. timestamp as index, cash as value.
    trade_df : pd.DataFrame
        contain columns at least timestamp, commission.
    position_df : pd.DataFrame
        contain columns at least timestamp, close_value.
    dividend_df : pd.DataFrame
        contain columns at least timestamp, amount.

    Returns
    -------
    pd.DataFrame
        summary df
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
    df = cash_series.to_frame("cash")

    df["cashflow"] = df["cash"].diff().fillna(0)

    df["commission"] = (
        trade_df.set_index("timestamp")["commission"].groupby(level=0).sum()
    )
    df["commission"] = df["commission"].fillna(0)

    df["total_market_value"] = (
        position_df.set_index("timestamp")["close_value"].groupby(level=0).sum()
    )
    df["total_market_value"] = df["total_market_value"].fillna(0)

    df["port_value"] = df["total_market_value"] + df["cash"]

    df["dividend"] = dividend_df.set_index("timestamp")["amount"].groupby(level=0).sum()
    df["dividend"] = df["dividend"].fillna(0)

    df["cumulative_dividend"] = df["dividend"].cumsum()

    df["port_value_with_dividend"] = df["port_value"] + df["cumulative_dividend"]

    df.index.name = "timestamp"
    df = df.reset_index()

    # sort column
    df = df[summary_df_columns]

    return df
