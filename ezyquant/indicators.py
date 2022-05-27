from typing import Tuple

import pandas as pd
from ta.volatility import (
    AverageTrueRange,
    BollingerBands,
    DonchianChannel,
    KeltnerChannel,
)


class TA:
    """Volatility Indicators."""

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
        ind_df = close.apply(
            lambda x: AverageTrueRange(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )
        out = ind_df.apply(lambda x: x.average_true_range()).T
        return out  # type: ignore

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
        ind_df = close.apply(
            lambda x: BollingerBands(
                close=x,
                window=window,
                window_dev=window_dev,
                fillna=fillna,
            )
        )
        out = (
            ind_df.apply(lambda x: x.bollinger_hband()).T,
            ind_df.apply(lambda x: x.bollinger_hband_indicator()).T,
            ind_df.apply(lambda x: x.bollinger_lband()).T,
            ind_df.apply(lambda x: x.bollinger_lband_indicator()).T,
            ind_df.apply(lambda x: x.bollinger_mavg()).T,
            ind_df.apply(lambda x: x.bollinger_pband()).T,
            ind_df.apply(lambda x: x.bollinger_wband()).T,
        )
        return out  # type: ignore

    @staticmethod
    def dc(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        fillna: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
        ind_df = close.apply(
            lambda x: DonchianChannel(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                fillna=fillna,
            )
        )
        out = (
            ind_df.apply(lambda x: x.donchian_channel_hband()).T,
            ind_df.apply(lambda x: x.donchian_channel_lband()).T,
            ind_df.apply(lambda x: x.donchian_channel_mband()).T,
            ind_df.apply(lambda x: x.donchian_channel_pband()).T,
            ind_df.apply(lambda x: x.donchian_channel_wband()).T,
        )
        return out  # type: ignore

    @staticmethod
    def kc(
        high: pd.DataFrame,
        low: pd.DataFrame,
        close: pd.DataFrame,
        window: int = 20,
        window_atr: int = 10,
        fillna: bool = False,
        original_version: bool = True,
        multiplier: int = 2,
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
        multiplier : int, default 2
            The multiplier has the most effect on the channel width.

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
        ind_df = close.apply(
            lambda x: KeltnerChannel(
                high=high[x.name],
                low=low[x.name],
                close=x,
                window=window,
                window_atr=window_atr,
                fillna=fillna,
                original_version=original_version,
                multiplier=multiplier,
            )
        )
        out = (
            ind_df.apply(lambda x: x.keltner_channel_hband()).T,
            ind_df.apply(lambda x: x.keltner_channel_hband_indicator()).T,
            ind_df.apply(lambda x: x.keltner_channel_lband()).T,
            ind_df.apply(lambda x: x.keltner_channel_lband_indicator()).T,
            ind_df.apply(lambda x: x.keltner_channel_mband()).T,
            ind_df.apply(lambda x: x.keltner_channel_pband()).T,
            ind_df.apply(lambda x: x.keltner_channel_wband()).T,
        )
        return out  # type: ignore
