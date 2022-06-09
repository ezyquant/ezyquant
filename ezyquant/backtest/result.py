import pandas as pd

position_columns = [
    "timestamp",
    "symbol",
    "volume",
    "avg_cost_price",
    "close_price",
    "close_value",
]


def make_position_df(
    position_df: pd.DataFrame, close_price_df: pd.DataFrame
) -> pd.DataFrame:
    """Add close_price add close_value to position_df

    Parameters
    ----------
    position_df : pd.DataFrame
        dataframe of position. contains columns:
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
