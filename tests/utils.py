import pandas as pd
from pandas.testing import assert_index_equal


def check_data_symbol_daily(result):
    assert isinstance(result, pd.DataFrame)

    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.index.is_monotonic_increasing
    assert result.index.is_unique
    assert_index_equal(result.index, result.index.normalize())  # type: ignore

    assert_index_equal(result.columns, result.columns.str.upper())
    return result
