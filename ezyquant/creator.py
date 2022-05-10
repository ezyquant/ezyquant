import numpy as np
import pandas as pd

from . import fields as fld
from .reader import SETDataReader


class SETSignalCreator:
    def __init__(self):
        pass

    @staticmethod
    def _manipulate_df(df: pd.DataFrame, method: str, period: int, shift: int):
        if method != fld.METHOD_CONSTANT:
            df = df.apply(
                lambda x: SETSignalCreator._rolling_skip_na_keep_inf(
                    x, method=method, period=period, shift=shift
                ),
                axis=0,
            )
        df = df.fillna(method="ffill")
        df = df.replace(np.inf, np.nan)
        return df

    @staticmethod
    def _rolling_skip_na_keep_inf(
        series: pd.Series, method: str, period: int, shift: int
    ) -> pd.Series:
        series = series.dropna().shift(shift)

        roll = series.rolling(period)

        if method == fld.METHOD_SUM:
            out = roll.sum()
        elif method == fld.METHOD_MEAN:
            out = roll.mean()
        else:
            raise ValueError(f"Unknown method: {method}")

        out = out.mask(np.isinf(series), np.inf)
        out = out.fillna(method="ffill")

        assert isinstance(out, pd.Series)
        return out
