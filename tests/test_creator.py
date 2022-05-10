import pandas as pd
import pytest
from numpy import inf, nan
from pandas.testing import assert_frame_equal

import ezyquant.fields as fld
from ezyquant.creator import SETSignalCreator


class TestManipulateDf:
    @pytest.mark.parametrize(
        ("df", "expected"),
        [
            (
                pd.DataFrame(
                    {
                        "a": [11, 12, 13, 14, 15, 16, 17, 18, 19],
                        "b": [21, 22, nan, inf, nan, 26, inf, nan, 29],
                        "c": [nan] * 9,
                    }
                ),
                pd.DataFrame(
                    {
                        "a": [11, 12, 13, 14, 15, 16, 17, 18, 19],
                        "b": [21, 22, 22, nan, nan, 26, nan, nan, 29],
                        "c": [nan] * 9,
                    }
                ),
            )
        ],
    )
    def test_constant(
        self, ssc: SETSignalCreator, df: pd.DataFrame, expected: pd.DataFrame
    ):
        # Test
        result = ssc._manipulate_df(
            df=df, method=fld.METHOD_CONSTANT, period=0, shift=0
        )

        # Check
        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        ("df", "expected"),
        [
            (
                pd.DataFrame(
                    {
                        "a": [11, 12, 13, 14, 15, 16, 17, 18, 19],
                        "b": [21, 22, nan, inf, nan, 26, inf, nan, 29],
                        "c": [nan] * 9,
                    }
                ),
                pd.DataFrame(
                    {
                        "a": [nan, 23, 25, 27, 29, 31, 33, 35, 37],
                        "b": [nan, 43, 43, nan, nan, nan, nan, nan, nan],
                        "c": [nan] * 9,
                    }
                ),
            )
        ],
    )
    def test_sum(self, ssc: SETSignalCreator, df: pd.DataFrame, expected: pd.DataFrame):
        # Test
        result = ssc._manipulate_df(df=df, method=fld.METHOD_SUM, period=2, shift=0)

        # Check
        assert_frame_equal(result, expected)
