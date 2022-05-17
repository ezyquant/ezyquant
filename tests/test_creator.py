from unittest.mock import ANY, Mock

import pandas as pd
import pytest
from numpy import inf, nan
from pandas.testing import assert_frame_equal

import ezyquant.fields as fld
import tests.utils as utils
from ezyquant.creator import SETSignalCreator


class TestGetData:
    _check = staticmethod(utils.check_data_symbol_daily)

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
        ssc._reindex_trade_date = lambda df: df
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
            timeframe=fld.TIMEFRAME_QUARTERLY,
            fillna_value=inf,
        )
        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        ("field", "timeframe", "value_by"),
        [
            # symbol daily
            (fld.D_CLOSE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_STOCK),
            (fld.D_PE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_STOCK),
            # symbol quarterly
            (fld.Q_ROE, fld.TIMEFRAME_QUARTERLY, fld.VALUE_BY_STOCK),
            (fld.Q_TOTAL_ASSET, fld.TIMEFRAME_QUARTERLY, fld.VALUE_BY_STOCK),
            (fld.Q_EBITDA, fld.TIMEFRAME_QUARTERLY, fld.VALUE_BY_STOCK),
            (fld.Q_NET_FINANCING, fld.TIMEFRAME_QUARTERLY, fld.VALUE_BY_STOCK),
            # symbol yearly
            (fld.Q_ROE, fld.TIMEFRAME_YEARLY, fld.VALUE_BY_STOCK),
            (fld.Q_TOTAL_ASSET, fld.TIMEFRAME_YEARLY, fld.VALUE_BY_STOCK),
            (fld.Q_EBITDA, fld.TIMEFRAME_YEARLY, fld.VALUE_BY_STOCK),
            (fld.Q_NET_FINANCING, fld.TIMEFRAME_YEARLY, fld.VALUE_BY_STOCK),
            # symbol ttm
            (fld.Q_EBITDA, fld.TIMEFRAME_TTM, fld.VALUE_BY_STOCK),
            (fld.Q_NET_FINANCING, fld.TIMEFRAME_TTM, fld.VALUE_BY_STOCK),
            # symbol ytd
            (fld.Q_ROE, fld.TIMEFRAME_YTD, fld.VALUE_BY_STOCK),
            (fld.Q_TOTAL_ASSET, fld.TIMEFRAME_YTD, fld.VALUE_BY_STOCK),
            (fld.Q_EBITDA, fld.TIMEFRAME_YTD, fld.VALUE_BY_STOCK),
            (fld.Q_NET_FINANCING, fld.TIMEFRAME_YTD, fld.VALUE_BY_STOCK),
            # index daily
            (fld.D_INDEX_CLOSE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_INDEX),
            (fld.D_INDEX_MKT_PE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_INDEX),
            # sector daily
            (fld.D_SECTOR_CLOSE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_SECTOR),
            (fld.D_SECTOR_MKT_PE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_SECTOR),
            # industry daily
            (fld.D_SECTOR_CLOSE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_INDUSTRY),
            (fld.D_SECTOR_MKT_PE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_INDUSTRY),
        ],
    )
    @pytest.mark.parametrize("period", [1, 2, 1000])
    @pytest.mark.parametrize("shift", [0, 1, 2, 1000])
    @pytest.mark.parametrize(
        "method", [fld.METHOD_CONSTANT, fld.METHOD_SUM, fld.METHOD_MEAN]
    )
    def test_empty(
        self,
        ssc: SETSignalCreator,
        field: str,
        timeframe: str,
        value_by: str,
        method: str,
        period: int,
        shift: int,
    ):
        # Test
        result = ssc.get_data(
            field=field,
            timeframe=timeframe,
            value_by=value_by,
            method=method,
            period=period,
            shift=shift,
        )

        # Check
        self._check(result)

        assert result.empty
