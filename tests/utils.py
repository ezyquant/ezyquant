import pandas as pd
from pandas.testing import assert_index_equal


def check_data_symbol_daily(result):
    assert isinstance(result, pd.DataFrame)

    # Index
    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.index.is_monotonic_increasing
    assert result.index.is_unique
    assert_index_equal(result.index, result.index.normalize())  # type: ignore

    # Column
    assert result.columns.is_unique
    assert_index_equal(result.columns, result.columns.str.upper())

    return result


def is_df_unique(df) -> bool:
    return (df.groupby([i for i in df.columns]).size() == 1).all()


def is_df_unique_cols(df) -> bool:
    if df.empty:
        return True
    a = df.to_numpy()
    return ((a[0] == a).all(0)).all()
