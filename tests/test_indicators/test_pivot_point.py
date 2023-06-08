import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from ezyquant.indicators.pivot_point import pivot_points_high

nan = float("nan")
series_empty = pd.Series([], dtype=float)


@pytest.mark.parametrize(
    "data, expected",
    [
        # No data
        (series_empty, series_empty),
        # One data
        (pd.Series([1.0]), series_empty),
        # Data increasing
        (pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), series_empty),
        (pd.Series([1.0, 1.0, 2.0, 2.0, 3.0, 3.0]), series_empty),
        # Data decreasing
        (pd.Series([5.0, 4.0, 3.0, 2.0, 1.0]), series_empty),
        (pd.Series([3.0, 3.0, 2.0, 2.0, 1.0, 1.0]), series_empty),
        # Pivot edge
        (pd.Series([1.0, 2.0, 3.0, 4.0, 3.0]), series_empty),
        (pd.Series([3.0, 4.0, 3.0, 2.0, 1.0]), series_empty),
        # Data same
        (pd.Series([1.0, 1.0, 1.0, 1.0, 1.0]), series_empty),
        # Pivot low
        (pd.Series([3.0, 2.0, 1.0, 2.0, 3.0]), series_empty),
        # Pivot high
        (pd.Series([1.0, 2.0, 3.0, 2.0, 1.0]), pd.Series({2: 3.0})),
        # Two same pivots
        (pd.Series([1.0, 1.0, 2.0, 2.0, 1.0, 1.0]), pd.Series({3: 2.0})),
        (pd.Series([1.0, 1.0, 2.0, 1.0, 2.0, 1.0, 1.0]), pd.Series({4: 2.0})),
        # Two pivots high
        (
            pd.Series([1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0, 2.0, 1.0]),
            pd.Series({2: 3.0, 6: 3.0}),
        ),
    ],
)
def test_pivot_points_high(data, expected):
    # Test
    actual = pivot_points_high(data, 2, 2)

    # Check
    assert_series_equal(actual.dropna(), expected)
