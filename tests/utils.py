import pandas as pd
from pandas.testing import assert_index_equal


def sort_values_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reindex(sorted(df.columns), axis=1)  #  type: ignore
    df = df.sort_values(by=df.columns)  #  type: ignore
    return df


def check_index_daily(result, is_unique=True):
    assert isinstance(result, pd.DatetimeIndex)
    assert result.is_monotonic_increasing
    if is_unique:
        assert result.is_unique
    assert_index_equal(result, result.normalize())  # type: ignore


def check_data_symbol_daily(result):
    assert isinstance(result, pd.DataFrame)

    # Index
    check_index_daily(result.index)

    # Column
    assert result.columns.is_unique
    assert_index_equal(result.columns, result.columns.str.upper())


def check_summary_df(df):
    assert isinstance(df, pd.DataFrame)

    # Index
    check_index_daily(df.index)

    # Column
    assert_index_equal(
        df.columns, pd.Index(["port_value", "cash", "total_market_value"])
    )

    assert not df.empty


def check_position_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(
        df.columns,
        pd.Index(["symbol", "volume", "cost_price", "market_price", "timestamp"]),
    )


def check_trade_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(
        df.columns,
        pd.Index(["timestamp", "symbol", "volume", "price", "pct_commission"]),
    )


def is_df_unique(df) -> bool:
    return (df.groupby([i for i in df.columns]).size() == 1).all()


def is_df_unique_cols(df) -> bool:
    if df.empty:
        return True
    a = df.to_numpy()
    return ((a[0] == a).all(0)).all()
