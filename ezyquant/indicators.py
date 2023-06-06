from typing import Callable, Tuple

import numpy as np
import pandas as pd
from pandas import isna
from ta.momentum import ROCIndicator, RSIIndicator, StochasticOscillator, rsi
from ta.trend import MACD, ADXIndicator, CCIIndicator, IchimokuIndicator, PSARIndicator
from ta.utils import _ema, _sma
from ta.volatility import (
    AverageTrueRange,
    BollingerBands,
    DonchianChannel,
    KeltnerChannel,
)

from .errors import InputError

nan = float("nan")


class TA:
    """Trend Indicators."""

    @staticmethod
    def sma(close: pd.DataFrame, window: int, fillna: bool = False) -> pd.DataFrame:
        """Simple Moving Average (SMA)

        Parameters
        ----------
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int
            n period.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Simple Moving Average (SMA)
        """
        df = _sma(close, periods=window, fillna=fillna)
        return df

    @staticmethod
    def ema(
        close: pd.DataFrame, window: int = 14, fillna: bool = False
    ) -> pd.DataFrame:
        """Exponential Moving Average (EMA)

        Parameters
        ----------
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 14
            n period.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Exponential Moving Average (EMA)
        """
        df = _ema(close, periods=window, fillna=fillna)
        return df

    @staticmethod
    def macd(
        close: pd.DataFrame,
        window_slow: int = 26,
        window_fast: int = 12,
        window_sign: int = 9,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Moving Average Convergence Divergence (MACD)

        Parameters
        ----------
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window_slow: int = 26
            n period short-term.
        window_fast: int = 12
            n period long-term.
        window_sign: int = 9
            n period to signal.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - MACD
                - MACD Signal
                - MACD Histogram
        """
        ind = close.apply(
            lambda x: MACD(
                close=x,
                window_slow=window_slow,
                window_fast=window_fast,
                window_sign=window_sign,
                fillna=fillna,
            )  # type: ignore
        )

        macd = _apply_t(ind, MACD.macd)
        macd_signal = _apply_t(ind, MACD.macd_signal)
        macd_diff = _apply_t(ind, MACD.macd_diff)

        return macd, macd_signal, macd_diff

    @staticmethod
    def adx(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 14,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Average Directional Movement Index (ADX)

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 14
            n period.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Average Directional Index (ADX)
                - Minus Directional Indicator (-DI)
                - Plus Directional Indicator (+DI)
        """
        ind = close.apply(
            lambda x: ADXIndicator(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )  # type: ignore
        )

        adx = _apply_t(ind, ADXIndicator.adx)
        adx_neg = _apply_t(ind, ADXIndicator.adx_neg)
        adx_pos = _apply_t(ind, ADXIndicator.adx_pos)

        return adx, adx_neg, adx_pos

    @staticmethod
    def cci(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        constant: float = 0.015,
        fillna: bool = False,
    ) -> pd.DataFrame:
        """Commodity Channel Index (CCI)

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 20
            n period.
        constant: float = 0.015
            constant.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Commodity Channel Index (CCI)
        """
        ind = close.apply(
            lambda x: CCIIndicator(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                constant=constant,
                fillna=fillna,
            )  # type: ignore
        )

        cci = _apply_t(ind, CCIIndicator.cci)

        return cci

    @staticmethod
    def ichimoku(
        high: pd.DataFrame,
        low: pd.DataFrame,
        window1: int = 9,
        window2: int = 26,
        window3: int = 52,
        visual: bool = False,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Ichimoku Kinko Hyo (Ichimoku)

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        window1: int = 9
            n period for Tenkan-sen.
        window2: int = 26
            n period for Kijun-sen.
        window3: int = 52
            n period for Senkou Span A.
        visual: bool = False
            if True, plot graph.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Tenkan-sen (Conversion Line)
                - Kijun-sen (Base Line)
                - Senkou Span A (Leading Span A)
                - Senkou Span B (Leading Span B)
        """
        ind = high.apply(
            lambda x: IchimokuIndicator(
                high=x,
                low=low[x.name],
                window1=window1,
                window2=window2,
                window3=window3,
                visual=visual,
                fillna=fillna,
            )  # type: ignore
        )

        conversion_line = _apply_t(ind, IchimokuIndicator.ichimoku_conversion_line)
        base_line = _apply_t(ind, IchimokuIndicator.ichimoku_base_line)
        a = _apply_t(ind, IchimokuIndicator.ichimoku_a)
        b = _apply_t(ind, IchimokuIndicator.ichimoku_b)

        return conversion_line, base_line, a, b

    @staticmethod
    def psar(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        step: float = 0.02,
        max_step: float = 0.20,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Parabolic SAR (Parabolic Stop and Reverse)

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        step: float = 0.02
            the Acceleration Factor used to compute the SAR.
        max_step: float = 0.20
            the maximum value allowed for the Acceleration Factor.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - PSAR value
                - PSAR down trend value
                - PSAR down trend value indicator
                - PSAR up trend value
                - PSAR up trend value indicator
        """
        ind = close.apply(
            lambda x: PSARIndicator(
                high=high[x.name],
                low=low[x.name],
                close=x,
                step=step,
                max_step=max_step,
                fillna=fillna,
            )  # type: ignore
        )

        psar = _apply_t(ind, PSARIndicator.psar)
        psar_down = _apply_t(ind, PSARIndicator.psar_down)
        psar_down_indicator = _apply_t(ind, PSARIndicator.psar_down_indicator)
        psar_up = _apply_t(ind, PSARIndicator.psar_up)
        psar_up_indicator = _apply_t(ind, PSARIndicator.psar_up_indicator)

        return psar, psar_down, psar_down_indicator, psar_up, psar_up_indicator

    """Momentum Indicators"""

    @staticmethod
    def rsi(
        close: pd.DataFrame, window: int = 14, fillna: bool = False
    ) -> pd.DataFrame:
        """Relative Strength Index (RSI)

        Parameters
        ----------
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 14
            n period.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Relative Strength Index (RSI)
        """
        ind = close.apply(
            lambda x: RSIIndicator(
                close=x,
                window=window,
                fillna=fillna,
            )  # type: ignore
        )

        rsi = _apply_t(ind, RSIIndicator.rsi)

        return rsi

    @staticmethod
    def rsi_divergence(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        rsi_period: int = 14,
        pivot_min_percent_change: float = 0.01,
    ) -> pd.DataFrame:
        """Relative Strength Index (RSI) Divergence.

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        rsi_period: int = 14
            n period for RSI.
        pivot_min_percent_change: float = 0.01
            minimum percent change for pivot.

        Returns
        -------
        pd.DataFrame
            Relative Strength Index (RSI) Divergence
        """
        return close.apply(
            lambda x: rsi_divergence(
                high=high[x.name],
                low=low[x.name],
                close=x,
                rsi_period=rsi_period,
                pivot_min_percent_change=pivot_min_percent_change,
                only_signal=True,
            )
        )

    @staticmethod
    def sto(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 14,
        smooth_window: int = 3,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Stochastic RSI (Stochastic Relative Strength Index)

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 14
            n period.
        smooth_window: int = 3
            sma period over stoch_k.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Stochastic Oscillator
                - Signal Stochastic Oscillator
        """
        ind = close.apply(
            lambda x: StochasticOscillator(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                smooth_window=smooth_window,
                fillna=fillna,
            )  # type: ignore
        )

        stoch = _apply_t(ind, StochasticOscillator.stoch)
        stoch_signal = _apply_t(ind, StochasticOscillator.stoch_signal)

        return stoch, stoch_signal

    @staticmethod
    def roc(
        close: pd.DataFrame,
        window: int = 12,
        fillna: bool = False,
    ) -> pd.DataFrame:
        """Rate of Change (ROC)

        Parameters
        ----------
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 12
            n period.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Rate of Change (ROC)
        """
        ind = close.apply(
            lambda x: ROCIndicator(
                close=x,
                window=window,
                fillna=fillna,
            )  # type: ignore
        )

        roc = _apply_t(ind, ROCIndicator.roc)

        return roc

    """Volatility Indicators"""

    @staticmethod
    def atr(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 14,
        fillna: bool = False,
    ) -> pd.DataFrame:
        """Average True Range (ATR)

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 14
            n period.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Average True Range (ATR)
        """
        ind = close.apply(
            lambda x: AverageTrueRange(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )  # type: ignore
        )

        average_true_range = _apply_t(ind, AverageTrueRange.average_true_range)

        return average_true_range

    @staticmethod
    def bb(
        close: pd.DataFrame, window: int = 20, window_dev: int = 2, fillna: bool = False
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
    ]:
        """Bollinger Bands.

        Parameters
        ----------
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 20
            n period.
        window_dev: int = 2
            n factor standard deviation.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Bollinger Channel High Band
                - Bollinger Channel Indicator Crossing High Band (binary).
                - Bollinger Channel Low Band
                - Bollinger Channel Indicator Crossing Low Band (binary).
                - Bollinger Channel Middle Band
                - Bollinger Channel Percentage Band
                - Bollinger Channel Band Width
        """
        ind = close.apply(
            lambda x: BollingerBands(
                close=x,
                window=window,
                window_dev=window_dev,
                fillna=fillna,
            )  # type: ignore
        )

        hband = _apply_t(ind, BollingerBands.bollinger_hband)
        hband_indicator = _apply_t(ind, BollingerBands.bollinger_hband_indicator)
        lband = _apply_t(ind, BollingerBands.bollinger_lband)
        lband_indicator = _apply_t(ind, BollingerBands.bollinger_lband_indicator)
        mavg = _apply_t(ind, BollingerBands.bollinger_mavg)
        pband = _apply_t(ind, BollingerBands.bollinger_pband)
        wband = _apply_t(ind, BollingerBands.bollinger_wband)

        return hband, hband_indicator, lband, lband_indicator, mavg, pband, wband

    @staticmethod
    def dc(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        offset: int = 0,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Donchian Channel.

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 20
            n period.
        offset: int = 0
            n period offset.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Donchian Channel High Band
                - Donchian Channel Low Band
                - Donchian Channel Middle Band
                - Donchian Channel Percentage Band
                - Donchian Channel Band Width
        """
        ind = close.apply(
            lambda x: DonchianChannel(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                offset=offset,
                fillna=fillna,
            )  # type: ignore
        )

        hband = _apply_t(ind, DonchianChannel.donchian_channel_hband)
        lband = _apply_t(ind, DonchianChannel.donchian_channel_lband)
        mband = _apply_t(ind, DonchianChannel.donchian_channel_mband)
        pband = _apply_t(ind, DonchianChannel.donchian_channel_pband)
        wband = _apply_t(ind, DonchianChannel.donchian_channel_wband)

        return hband, lband, mband, pband, wband

    @staticmethod
    def kc(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        window_atr: int = 10,
        multiplier: int = 2,
        original_version: bool = False,
        fillna: bool = False,
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
    ]:
        """Keltner Channel.

        Parameters
        ----------
        high: pd.DataFrame
            dataset 'High' dataframe.
        low: pd.DataFrame
            dataset 'Low' dataframe.
        close: pd.DataFrame
            dataset 'Close' dataframe.
        window: int = 20
            n period.
        window_atr: int = 10
            n atr period. Only valid if original_version param is False.
        multiplier: int = 2
            The multiplier has the most effect on the channel width.
        original_version: bool = False
            if True, use the original version.
        fillna: bool = False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Keltner Channel High Band
                - Keltner Channel Indicator Crossing High Band (binary)
                - Keltner Channel Low Band
                - Keltner Channel Indicator Crossing Low Band (binary)
                - Keltner Channel Middle Band
                - Keltner Channel Percentage Band
                - Keltner Channel Band Width
        """
        ind = close.apply(
            lambda x: KeltnerChannel(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
                multiplier=multiplier,
            )  # type: ignore
        )

        hband = _apply_t(ind, KeltnerChannel.keltner_channel_hband)
        hband_indicator = _apply_t(ind, KeltnerChannel.keltner_channel_hband_indicator)
        lband = _apply_t(ind, KeltnerChannel.keltner_channel_lband)
        lband_indicator = _apply_t(ind, KeltnerChannel.keltner_channel_lband_indicator)
        mband = _apply_t(ind, KeltnerChannel.keltner_channel_mband)
        pband = _apply_t(ind, KeltnerChannel.keltner_channel_pband)
        wband = _apply_t(ind, KeltnerChannel.keltner_channel_wband)

        return hband, hband_indicator, lband, lband_indicator, mband, pband, wband


def _apply_t(series: pd.Series, func: Callable) -> pd.DataFrame:
    df = series.apply(func).T
    if df.empty:
        raise InputError(f"{func.__name__} returned an empty dataframe")
    assert isinstance(df, pd.DataFrame)
    return df


"""
Pivot
"""


def pivot_points_high(high: pd.Series, left_bars: int, right_bars: int) -> pd.Series:
    """Pivot Points High.

    High is the highest high in a window between left_bars and
    right_bars. If multiple bars have the same high, the most right bar
    is used.
    """
    max_ = high.rolling(window=left_bars + 1).max()
    max_right = high.rolling(window=right_bars).max().shift(-right_bars)

    return high.where((max_ == high) & (max_ > max_right))


def pivot_points_low(low: pd.Series, left_bars: int, right_bars: int) -> pd.Series:
    """Pivot Points Low.

    Low is the lowest low in a window between left_bars and right_bars.
    If multiple bars have the same low, the most right bar is used.
    """
    min_ = low.rolling(window=left_bars + 1).min()
    min_right = low.rolling(window=right_bars).min().shift(-right_bars)

    return low.where((min_ == low) & (min_ < min_right))


def pivot_points_high_low(
    high: pd.Series,
    low: pd.Series,
    min_percent_change: float = 0.01,
) -> pd.Series:
    """Pivot Points High Low.

    1. Pivot points high and low are surrounded by each other.
    2. Pivot points high and low must change at least min percent change from the previous pivot point.
    """
    ph = pivot_points_high(high=high, left_bars=1, right_bars=1).dropna()
    pl = pivot_points_low(low=low, left_bars=1, right_bars=1).dropna()

    ph_m = ph.index.max()
    pl_m = pl.index.max()

    if isna(ph_m) and isna(pl_m):
        d = {}
    elif ph_m > pl_m or isna(pl_m):
        d = {ph_m: ph.loc[ph_m]}
    elif ph_m < pl_m or isna(ph_m):
        d = {pl_m: -pl.loc[pl_m]}  # negative value for low pivot
    else:
        d = {}

    pl_mul_change = pl * (1 + min_percent_change)
    ph_mul_change = ph * (1 - min_percent_change)

    while True:
        k = min(d, default=nan)
        v = d.get(k, nan)

        if v > 0:
            s = -pl[(pl.index < k) & (pl_mul_change < v)]
        else:
            s = ph[(ph.index < k) & (ph_mul_change > -v)]

        if len(s) == 0:
            break
        else:
            d[s.index[-1]] = s.iloc[-1]

    return pd.Series(d, index=high.index)


"""
RSI Divergence
"""


def rsi_bullish_divergence(
    low: pd.Series,
    close: pd.Series,
    rsi_period: int = 14,
    pivot_min_percent_change: float = 0.01,
) -> pd.Series:
    """Return RSI of the bullish divergence points.

    Otherwise, return NaN.
    """
    # Calculate RSI
    rsi_ = rsi(close, rsi_period)

    # Calculate RSI pivot points
    rsi_pp = pivot_points_high_low(
        rsi_, rsi_, min_percent_change=pivot_min_percent_change
    ).dropna()
    rsi_pl = rsi_pp[rsi_pp < 0]

    # Calculate price pivot points
    low_pl = low.loc[rsi_pl.index]
    return rsi_.where((rsi_pl > rsi_pl.shift(1)) & (low_pl < low_pl.shift(1)))


def rsi_bearish_divergence(
    high: pd.Series,
    close: pd.Series,
    rsi_period: int = 14,
    pivot_min_percent_change: float = 0.01,
) -> pd.Series:
    """Return RSI of the bearish divergence points.

    Otherwise, return NaN.
    """
    # Calculate RSI
    rsi_ = rsi(close, rsi_period)

    # Calculate RSI pivot points
    rsi_pp = pivot_points_high_low(
        rsi_, rsi_, min_percent_change=pivot_min_percent_change
    ).dropna()
    rsi_ph = rsi_pp[rsi_pp > 0]

    # Calculate price pivot points
    high_ph = high.loc[rsi_ph.index]
    return rsi_.where((rsi_ph < rsi_ph.shift(1)) & (high_ph > high_ph.shift(1)))


def rsi_divergence(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    rsi_period: int = 14,
    pivot_min_percent_change: float = 0.01,
    only_signal: bool = False,
) -> pd.Series:
    """Return Positive RSI of the bullish divergence points and Negative RSI of
    the bearish divergence points.

    Parameters
    ----------
    high : pd.Series
        Series of 'high' prices.
    low : pd.Series
        Series of 'low' prices.
    close : pd.Series
        Series of 'close' prices.
    rsi_period : int, optional
        RSI period, by default 14
    pivot_min_percent_change : int
        Minimum percent change for pivot points, by default 0.01
    only_signal : bool, optional
        If True, bullish divergence points are represented by 1 and bearish divergence points are represented by -1. Otherwise, return 0.
    """
    bullish = rsi_bullish_divergence(
        low=low,
        close=close,
        rsi_period=rsi_period,
        pivot_min_percent_change=pivot_min_percent_change,
    )
    bearish = rsi_bearish_divergence(
        high=high,
        close=close,
        rsi_period=rsi_period,
        pivot_min_percent_change=pivot_min_percent_change,
    )
    out = bullish.fillna(-bearish)
    if only_signal:
        out = pd.Series(np.sign(out)).fillna(0)
    return out
