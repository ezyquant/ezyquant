import pandas as pd


def pivot_points_high(high: pd.Series, left_bars: int, right_bars: int) -> pd.Series:
    """Pivot Points High.

    High is the highest high in a window between left_bars and right_bars. If multiple
    bars have the same high, the most right bar is used.
    """
    max_ = high.rolling(window=left_bars + 1).max()
    max_right = high.rolling(window=right_bars).max().shift(-right_bars)

    return high.where((max_ == high) & (max_ > max_right))


def pivot_points_low(low: pd.Series, left_bars: int, right_bars: int) -> pd.Series:
    """Pivot Points Low.

    Low is the lowest low in a window between left_bars and right_bars. If multiple bars
    have the same low, the most right bar is used.
    """
    min_ = low.rolling(window=left_bars + 1).min()
    min_right = low.rolling(window=right_bars).min().shift(-right_bars)

    return low.where((min_ == low) & (min_ < min_right))
