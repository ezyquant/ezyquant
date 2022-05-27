from typing import Tuple

import pandas as pd
from ta.momentum import (
    awesome_oscillator,
    kama,
    ppo,
    ppo_hist,
    ppo_signal,
    pvo,
    pvo_hist,
    pvo_signal,
    roc,
    rsi,
    stoch,
    stoch_signal,
    stochrsi,
    stochrsi_d,
    stochrsi_k,
    tsi,
    ultimate_oscillator,
    williams_r,
)
from ta.trend import (
    PSARIndicator,
    adx,
    adx_neg,
    adx_pos,
    aroon_down,
    aroon_up,
    cci,
    dpo,
    ichimoku_a,
    ichimoku_b,
    ichimoku_base_line,
    ichimoku_conversion_line,
    kst,
    kst_sig,
    macd,
    macd_diff,
    macd_signal,
    mass_index,
    psar_down,
    psar_down_indicator,
    psar_up,
    psar_up_indicator,
    stc,
    trix,
    vortex_indicator_neg,
    vortex_indicator_pos,
    wma_indicator,
)
from ta.utils import _ema, _sma
from ta.volatility import (
    average_true_range,
    bollinger_hband,
    bollinger_hband_indicator,
    bollinger_lband,
    bollinger_lband_indicator,
    bollinger_mavg,
    bollinger_pband,
    bollinger_wband,
    donchian_channel_hband,
    donchian_channel_lband,
    donchian_channel_mband,
    donchian_channel_pband,
    donchian_channel_wband,
    keltner_channel_hband,
    keltner_channel_hband_indicator,
    keltner_channel_lband,
    keltner_channel_lband_indicator,
    keltner_channel_mband,
    keltner_channel_pband,
    keltner_channel_wband,
)


class TA:
    """Trend Indicators."""

    @staticmethod
    def sma(close: pd.DataFrame, window: int, fillna: bool = False) -> pd.DataFrame:
        """Simple Moving Average (SMA)

        Parameters
        ----------
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int
            n period.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Simple Moving Average (SMA)
        """
        sma_df = _sma(close, periods=window, fillna=fillna)

        assert isinstance(sma_df, pd.DataFrame)

        return sma_df

    @staticmethod
    def ema(
        close: pd.DataFrame, window: int = 14, fillna: bool = False
    ) -> pd.DataFrame:
        """Exponential Moving Average (EMA)

        Parameters
        ----------
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 14
            n period.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Exponential Moving Average (EMA)
        """
        ema_df = _ema(close, periods=window, fillna=fillna)

        assert isinstance(ema_df, pd.DataFrame)

        return ema_df

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
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window_slow : int, default 26
            n period short-term.
        window_fast : int, default 12
            n period long-term.
        window_sign : int, default 9
            n period to signal.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - MACD
                - MACD Signal
                - MACD Signal
        """
        macd_df = close.apply(
            lambda x: macd(
                close=x,
                window_slow=window_slow,
                window_fast=window_fast,
                fillna=fillna,
            )
        )
        macd_signal_df = close.apply(
            lambda x: macd_signal(
                close=x,
                window_slow=window_slow,
                window_fast=window_fast,
                window_sign=window_sign,
                fillna=fillna,
            )
        )
        macd_diff_df = close.apply(
            lambda x: macd_diff(
                close=x,
                window_slow=window_slow,
                window_fast=window_fast,
                window_sign=window_sign,
                fillna=fillna,
            )
        )

        assert isinstance(macd_df, pd.DataFrame)
        assert isinstance(macd_signal_df, pd.DataFrame)
        assert isinstance(macd_diff_df, pd.DataFrame)

        return macd_df, macd_signal_df, macd_diff_df

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
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 14
            n period.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        Tuple[pd.DataFrame]
            Contains:
                - Average Directional Index (ADX)
                - Minus Directional Indicator (-DI)
                - Plus Directional Indicator (+DI)
        """
        adx_df = close.apply(
            lambda x: adx(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )
        adx_neg_df = close.apply(
            lambda x: adx_neg(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )
        adx_pos_df = close.apply(
            lambda x: adx_pos(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )

        assert isinstance(adx_df, pd.DataFrame)
        assert isinstance(adx_neg_df, pd.DataFrame)
        assert isinstance(adx_pos_df, pd.DataFrame)

        return adx_df, adx_neg_df, adx_pos_df

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
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 20
            n period.
        constant : float, default 0.015
            constant.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Commodity Channel Index (CCI)
        """
        cci_df = close.apply(
            lambda x: cci(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                constant=constant,
                fillna=fillna,
            )
        )

        assert isinstance(cci_df, pd.DataFrame)

        return cci_df

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
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        window1 : int, default 9
            n period for Tenkan-sen.
        window2 : int, default 26
            n period for Kijun-sen.
        window3 : int, default 52
            n period for Senkou Span A.
        visual : bool, default False
            if True, plot graph.
        fillna : bool, default False
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
        conversion_line_df = high.apply(
            lambda x: ichimoku_conversion_line(
                high=x,
                low=low[x.name],
                window1=window1,
                window2=window2,
                visual=visual,
                fillna=fillna,
            )
        )
        base_line_df = high.apply(
            lambda x: ichimoku_base_line(
                high=x,
                low=low[x.name],
                window1=window1,
                window2=window2,
                visual=visual,
                fillna=fillna,
            )
        )
        a_df = high.apply(
            lambda x: ichimoku_a(
                high=x,
                low=low[x.name],
                window1=window1,
                window2=window2,
                visual=visual,
                fillna=fillna,
            )
        )
        b_df = high.apply(
            lambda x: ichimoku_b(
                high=x,
                low=low[x.name],
                window2=window2,
                window3=window3,
                visual=visual,
                fillna=fillna,
            )
        )

        assert isinstance(conversion_line_df, pd.DataFrame)
        assert isinstance(base_line_df, pd.DataFrame)
        assert isinstance(a_df, pd.DataFrame)
        assert isinstance(b_df, pd.DataFrame)

        return conversion_line_df, base_line_df, a_df, b_df

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
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 14
            n period.
        fillna : bool, default False
            if True, fill nan values.

        Returns
        -------
        pd.DataFrame
            Average True Range (ATR)
        """
        average_true_range_df = close.apply(
            lambda x: average_true_range(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )

        assert isinstance(average_true_range_df, pd.DataFrame)

        return average_true_range_df

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
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 20
            n period.
        window_dev : int, default 2
            n factor standard deviation.
        fillna : bool, default False
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
        hband_df = close.apply(
            lambda x: bollinger_hband(
                close=x, window=window, window_dev=window_dev, fillna=fillna
            )
        )
        hband_indicator_df = close.apply(
            lambda x: bollinger_hband_indicator(
                close=x, window=window, window_dev=window_dev, fillna=fillna
            )
        )
        lband_df = close.apply(
            lambda x: bollinger_lband(
                close=x, window=window, window_dev=window_dev, fillna=fillna
            )
        )
        lband_indicator_df = close.apply(
            lambda x: bollinger_lband_indicator(
                close=x, window=window, window_dev=window_dev, fillna=fillna
            )
        )
        mavg_df = close.apply(
            lambda x: bollinger_mavg(close=x, window=window, fillna=fillna)
        )
        pband_df = close.apply(
            lambda x: bollinger_pband(
                close=x, window=window, window_dev=window_dev, fillna=fillna
            )
        )
        wband_df = close.apply(
            lambda x: bollinger_wband(
                close=x, window=window, window_dev=window_dev, fillna=fillna
            )
        )

        assert isinstance(hband_df, pd.DataFrame)
        assert isinstance(hband_indicator_df, pd.DataFrame)
        assert isinstance(lband_df, pd.DataFrame)
        assert isinstance(lband_indicator_df, pd.DataFrame)
        assert isinstance(mavg_df, pd.DataFrame)
        assert isinstance(pband_df, pd.DataFrame)
        assert isinstance(wband_df, pd.DataFrame)

        return (
            hband_df,
            hband_indicator_df,
            lband_df,
            lband_indicator_df,
            mavg_df,
            pband_df,
            wband_df,
        )

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
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 20
            n period.
        offset : int, default 0
            n period offset.
        fillna : bool, default False
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
        hband_df = close.apply(
            lambda x: donchian_channel_hband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                offset=offset,
                fillna=fillna,
            )
        )
        lband_df = close.apply(
            lambda x: donchian_channel_lband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                offset=offset,
                fillna=fillna,
            )
        )
        mband_df = close.apply(
            lambda x: donchian_channel_mband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                offset=offset,
                fillna=fillna,
            )
        )
        pband_df = close.apply(
            lambda x: donchian_channel_pband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                offset=offset,
                fillna=fillna,
            )
        )
        wband_df = close.apply(
            lambda x: donchian_channel_wband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                offset=offset,
                fillna=fillna,
            )
        )

        assert isinstance(hband_df, pd.DataFrame)
        assert isinstance(lband_df, pd.DataFrame)
        assert isinstance(mband_df, pd.DataFrame)
        assert isinstance(pband_df, pd.DataFrame)
        assert isinstance(wband_df, pd.DataFrame)

        return hband_df, lband_df, mband_df, pband_df, wband_df

    @staticmethod
    def kc(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        window_atr: int = 10,
        fillna: bool = False,
        original_version: bool = True,
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
        high : pd.DataFrame
            dataset 'High' dataframe.
        low : pd.DataFrame
            dataset 'Low' dataframe.
        close : pd.DataFrame
            dataset 'Close' dataframe.
        window : int, default 20
            n period.
        window_atr : int, default 10
            n atr period. Only valid if original_version param is False.
        fillna : bool, default False
            if True, fill nan values.
        original_version : bool, default True
            if True, use the original version.

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
        hband = close.apply(
            lambda x: keltner_channel_hband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
            )
        )
        hband_indicator = close.apply(
            lambda x: keltner_channel_hband_indicator(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
            )
        )
        lband = close.apply(
            lambda x: keltner_channel_lband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
            )
        )
        lband_indicator = close.apply(
            lambda x: keltner_channel_lband_indicator(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
            )
        )
        mband = close.apply(
            lambda x: keltner_channel_mband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
            )
        )
        pband = close.apply(
            lambda x: keltner_channel_pband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
            )
        )
        wband = close.apply(
            lambda x: keltner_channel_wband(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
            )
        )

        assert isinstance(hband, pd.DataFrame)
        assert isinstance(hband_indicator, pd.DataFrame)
        assert isinstance(lband, pd.DataFrame)
        assert isinstance(lband_indicator, pd.DataFrame)
        assert isinstance(mband, pd.DataFrame)
        assert isinstance(pband, pd.DataFrame)
        assert isinstance(wband, pd.DataFrame)

        return hband, hband_indicator, lband, lband_indicator, mband, pband, wband
