import pandas as pd
import pytest

from tests import utils


@pytest.mark.parametrize(
    ("df", "expected"),
    [
        (pd.DataFrame(), True),
        (pd.DataFrame([1, 1]), False),
        (pd.DataFrame([1, 2]), True),
        (pd.DataFrame([1, 2, 3]), True),
        (pd.DataFrame([1, 1, 2]), False),
        (pd.DataFrame([1, 1, 2, 2]), False),
        (pd.DataFrame([[1, 2], [1, 2]]), False),
        (pd.DataFrame([[1, 1], [1, 2]]), True),
    ],
)
def test_is_df_unique(df: pd.DataFrame, expected: bool):
    assert utils.is_df_unique(df) == expected


@pytest.mark.parametrize(
    ("df", "expected"),
    [
        (pd.DataFrame(), True),
        (pd.DataFrame({"A": [1, 1, 1]}), True),
        (pd.DataFrame({"A": [1, 1, 1], "B": [1, 1, 1]}), True),
        (pd.DataFrame({"A": [1, 1, 2]}), False),
        (pd.DataFrame({"A": [1, 2, 3]}), False),
        (pd.DataFrame({"A": [1, 1, 2], "B": [1, 1, 1]}), False),
    ],
)
def test_is_df_unique_cols(df: pd.DataFrame, expected: bool):
    assert utils.is_df_unique_cols(df) == expected
