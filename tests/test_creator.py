from unittest.mock import ANY, Mock

import pandas as pd
import pytest
from numpy import inf, nan
from pandas.testing import assert_frame_equal

import ezyquant.fields as fld
from ezyquant.creator import SETSignalCreator


class TestGetData:
    @pytest.mark.parametrize(
        "df",
        [
            pd.DataFrame(
                {
                    "A": [11, 12, 13, 14, 15, 16, 17, 18, 19],
                    "B": [21, 22, nan, inf, nan, 26, inf, nan, 29],
                    "C": [nan] * 9,
                }
            )
        ],
    )
    @pytest.mark.parametrize(
        ("method", "period", "shift", "expected"),
        [
            (
                fld.METHOD_CONSTANT,
                None,
                0,
                pd.DataFrame(
                    {
                        "A": [11, 12, 13, 14, 15, 16, 17, 18, 19],
                        "B": [21, 22, 22, nan, nan, 26, nan, nan, 29],
                        "C": [nan] * 9,
                    }
                ),
            ),
            (
                fld.METHOD_CONSTANT,
                None,
                1,
                pd.DataFrame(
                    {
                        "A": [nan, 11, 12, 13, 14, 15, 16, 17, 18],
                        "B": [nan, 21, 21, 22, 22, nan, 26, 26, nan],
                        "C": [nan] * 9,
                    }
                ),
            ),
            (
                fld.METHOD_SUM,
                2,
                0,
                pd.DataFrame(
                    {
                        "A": [nan, 23, 25, 27, 29, 31, 33, 35, 37],
                        "B": [nan, 43, 43, nan, nan, nan, nan, nan, nan],
                        "C": [nan] * 9,
                    }
                ),
            ),
            (
                fld.METHOD_SUM,
                2,
                1,
                pd.DataFrame(
                    {
                        "A": [nan, nan, 23, 25, 27, 29, 31, 33, 35],
                        "B": [nan, nan, nan, 43, 43, nan, nan, nan, nan],
                        "C": [nan] * 9,
                    }
                ),
            ),
        ],
    )
    def test_fundamental_mock(
        self,
        ssc: SETSignalCreator,
        df: pd.DataFrame,
        method: str,
        period: int,
        shift: int,
        expected: pd.DataFrame,
    ):
        # Mock
        end = df.shape[0]
        ssc._reindex_trade_date = lambda df: df.reindex(pd.RangeIndex(end))  # type: ignore
        ssc._sdr._get_fundamental_data = Mock(return_value=df)

        # Test
        result = ssc.get_data(
            field=fld.Q_TOTAL_ASSET,
            timeframe=fld.TIMEFRAME_QUARTERLY,
            value_by=fld.VALUE_BY_STOCK,
            method=method,
            period=period,
            shift=shift,
        )

        # Check
        ssc._sdr._get_fundamental_data.assert_called_once_with(
            field=fld.Q_TOTAL_ASSET,
            symbol_list=ANY,
            start_date=ANY,
            end_date=ANY,
            period=fld.TIMEFRAME_QUARTERLY,
            fillna_value=inf,
        )
        assert_frame_equal(result, expected)
