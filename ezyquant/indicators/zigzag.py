# https://stackoverflow.com/questions/65800877/python-zig-zag-algorithm-function-not-returning-expected-results

# TODO: use pandas_ta instead when it's released

import numpy as np

PEAK, VALLEY = 1, -1


def _identify_initial_pivot(X, up_thresh, down_thresh):  # noqa: N803
    """Quickly identify the X[0] as a peak or valley."""
    x_0 = X[0]
    max_x = x_0
    max_t = 0
    min_x = x_0
    min_t = 0
    up_thresh += 1
    down_thresh += 1

    for t in range(1, len(X)):
        x_t = X[t]

        if x_t / min_x >= up_thresh:
            return VALLEY if min_t == 0 else PEAK

        if x_t / max_x <= down_thresh:
            return PEAK if max_t == 0 else VALLEY

        if x_t > max_x:
            max_x = x_t
            max_t = t

        if x_t < min_x:
            min_x = x_t
            min_t = t

    t_n = len(X) - 1
    return VALLEY if x_0 < X[t_n] else PEAK


def peak_valley_pivots_candlestick(close, high, low, up_thresh, down_thresh):
    """
    Finds the peaks and valleys of a series of HLC (open is not necessary).
    TR: This is modified peak_valley_pivots function in order to find peaks and valleys for OHLC.
    Parameters
    ----------
    close : This is series with closes prices.
    high : This is series with highs  prices.
    low : This is series with lows prices.
    up_thresh : The minimum relative change necessary to define a peak.
    down_thesh : The minimum relative change necessary to define a valley.
    Returns
    -------
    an array with 0 indicating no pivot and -1 and 1 indicating valley and peak
    respectively
    Using Pandas
    ------------
    For the most part, close, high and low may be a pandas series. However, the index must
    either be [0,n) or a DateTimeIndex. Why? This function does X[t] to access
    each element where t is in [0,n).
    The First and Last Elements
    ---------------------------
    The first and last elements are guaranteed to be annotated as peak or
    valley even if the segments formed do not have the necessary relative
    changes. This is a tradeoff between technical correctness and the
    propensity to make mistakes in data analysis. The possible mistake is
    ignoring data outside the fully realized segments, which may bias analysis.
    """
    if down_thresh > 0:
        msg = "The down_thresh must be negative."
        raise ValueError(msg)

    initial_pivot = _identify_initial_pivot(close, up_thresh, down_thresh)

    t_n = len(close)
    pivots = np.zeros(t_n, dtype="i1")
    pivots[0] = initial_pivot

    # Adding one to the relative change thresholds saves operations. Instead
    # of computing relative change at each point as x_j / x_i - 1, it is
    # computed as x_j / x_1. Then, this value is compared to the threshold + 1.
    # This saves (t_n - 1) subtractions.
    up_thresh += 1
    down_thresh += 1

    trend = -initial_pivot
    last_pivot_t = 0
    last_pivot_x = close[0]
    for t in range(1, len(close)):
        if trend == -1:
            x = low[t]
            r = x / last_pivot_x
            if r >= up_thresh:
                pivots[last_pivot_t] = trend  #
                trend = 1
                # last_pivot_x = x
                last_pivot_x = high[t]
                last_pivot_t = t
            elif x < last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t
        else:
            x = high[t]
            r = x / last_pivot_x
            if r <= down_thresh:
                pivots[last_pivot_t] = trend
                trend = -1
                # last_pivot_x = x
                last_pivot_x = low[t]
                last_pivot_t = t
            elif x > last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t

    if last_pivot_t == t_n - 1:
        pivots[last_pivot_t] = trend
    elif pivots[t_n - 1] == 0:
        pivots[t_n - 1] = trend

    return pivots
