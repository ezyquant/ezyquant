import numpy as np
import pandas as pd


def combine_signal_weight_df_and_is_rebalance_df(
    signal_weight_df: pd.DataFrame, is_rebalance_df: pd.DataFrame
) -> pd.DataFrame:
    cash_signal_s = 1 - signal_weight_df.sum(axis=1)
    signal_weight_df = signal_weight_df.where(is_rebalance_df, np.nan)
    signal_weight_df = signal_weight_df.div(
        signal_weight_df.sum(axis=1) + cash_signal_s, axis=0
    )
    return signal_weight_df
