from typing import List
from unittest.mock import ANY, Mock

import constant as const
import pandas as pd
import pytest
import utils
from numpy import inf, nan
from pandas.testing import assert_frame_equal, assert_series_equal

import ezyquant.fields as fld
from ezyquant import SETSignalCreator

dt_idx = pd.DatetimeIndex(
    [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
        "2020-01-09",
        "2020-01-10",
        "2020-01-13",
        "2020-01-14",
        "2020-01-15",
    ],
    freq=None,
)


class TestGetSymbolInUniverse:
    @pytest.mark.parametrize(
        ("symbol_list", "expected"),
        [
            ([], []),
            (["XXX"], []),
            (["COM7"], ["COM7"]),
            (["com7"], ["COM7"]),
            (["COM7", "MALEE"], ["COM7", "MALEE"]),
        ],
    )
    def test_symbol_list(
        self, ssc: SETSignalCreator, symbol_list: List[str], expected: List[str]
    ):
        # Mock
        ssc._symbol_list = symbol_list

        # Test
        result = ssc._get_symbol_in_universe()

        # Check
        assert set(result) == set(expected)

    @pytest.mark.parametrize(
        ("index_list", "start_date", "end_date", "expected"),
        [
            ([fld.INDEX_SET50], "2022-01-04", "2022-01-04", const.SET50_2022_01_04),
            ([fld.INDEX_SET50], "2022-01-05", "2022-01-05", const.SET50_2022_01_04),
            ([fld.INDEX_SET50], "2022-01-04", "2022-01-05", const.SET50_2022_01_04),
            ([fld.INDEX_SET50], "2022-04-26", "2022-04-26", const.SET50_2022_01_04),
            (
                [fld.INDEX_SET50],
                "2022-04-26",
                "2022-04-27",
                const.SET50_2022_01_04 + const.SET50_2022_04_27,
            ),
            (
                [fld.INDEX_SET50, fld.INDEX_SSET],
                "2022-01-04",
                "2022-01-04",
                const.SET50_2022_01_04 + const.SSET_2022_01_04,
            ),
            (
                [fld.INDEX_SET50, fld.INDEX_SSET],
                "2022-04-26",
                "2022-04-27",
                const.SET50_2022_01_04 + const.SSET_2022_01_04 + const.SET50_2022_04_27,
            ),
        ],
    )
    def test_index_list(
        self,
        ssc: SETSignalCreator,
        index_list: List[str],
        start_date: str,
        end_date: str,
        expected: List[str],
    ):
        # Mock
        ssc._index_list = index_list
        ssc._start_date = start_date
        ssc._end_date = end_date

        # Test
        result = ssc._get_symbol_in_universe()

        # Check
        assert set(result) == set(expected)


class TestGetData:
    _check = staticmethod(utils.check_data_symbol_daily)

    def test_sector_daily(self, ssc: SETSignalCreator):
        # Mock
        ssc._start_date = "2021-05-18"
        ssc._end_date = "2021-05-31"
        ssc._index_list = ["SET", "mai"]

        # Test
        result = ssc.get_data(
            field=fld.D_SECTOR_CLOSE,
            timeframe=fld.TIMEFRAME_DAILY,
            value_by=fld.VALUE_BY_SECTOR,
            method=fld.METHOD_CONSTANT,
            period=0,
            shift=0,
        )

        # Check
        self._check(result)

        for i in [
            "BAY",
            "BBL",
            "CIMBT",
            "KBANK",
            "KKP",
            "KTB",
            "LHFG",
            "SCB",
            "TCAP",
            "TISCO",
            "TTB",
        ]:
            assert_series_equal(
                result[i], const.BANK_D_CLOSE_2021_05_18, check_names=False
            )

    def test_industry_daily(self, ssc: SETSignalCreator):
        # Mock
        ssc._start_date = "2021-05-18"
        ssc._end_date = "2021-05-31"
        ssc._index_list = ["SET", "mai"]

        # Test
        result = ssc.get_data(
            field=fld.D_SECTOR_CLOSE,
            timeframe=fld.TIMEFRAME_DAILY,
            value_by=fld.VALUE_BY_INDUSTRY,
            method=fld.METHOD_CONSTANT,
            period=0,
            shift=0,
        )

        # Check
        self._check(result)

        for i in [
            "BAY",  # BANK
            "AEONTS",  # FIN
            "AYUD",  # INSUR
        ]:
            assert_series_equal(
                result[i], const.FINCIAL_D_CLOSE_2021_05_18, check_names=False
            )

    @pytest.mark.parametrize(
        "field",
        [
            fld.D_OPEN,
            fld.D_HIGH,
            fld.D_LOW,
            fld.D_CLOSE,
            fld.D_AVERAGE,
            fld.D_LAST_BID,
            fld.D_LAST_OFFER,
        ],
    )
    def test_stock_daily_fill_prior(self, ssc: SETSignalCreator, field: str):
        """THAI no trade after 2021-05-18, close at 2021-05-17 is 3.32"""
        # Mock
        ssc._start_date = "2021-05-18"
        ssc._end_date = "2021-05-31"
        ssc._symbol_list = ["THAI"]

        # Test
        result = ssc.get_data(
            field=field,
            timeframe=fld.TIMEFRAME_DAILY,
            value_by=fld.VALUE_BY_STOCK,
            method=fld.METHOD_CONSTANT,
            period=0,
            shift=0,
        )

        # Check
        expect = pd.DataFrame(
            {"THAI": [3.32] * 9},
            index=pd.DatetimeIndex(
                [
                    "2021-05-18",
                    "2021-05-19",
                    "2021-05-20",
                    "2021-05-21",
                    "2021-05-24",
                    "2021-05-25",
                    "2021-05-27",
                    "2021-05-28",
                    "2021-05-31",
                ]
            ),
        )

        assert_frame_equal(result, expect)

    @pytest.mark.parametrize(
        "data",
        [
            pd.DataFrame(
                {
                    "A": [11, 12, 13, 14, 15, 16, 17, 18, 19],
                    "B": [21, 22, nan, inf, nan, 26, inf, nan, 29],
                    "C": [nan] * 9,
                },
                index=dt_idx[:9],
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
                    },
                    index=dt_idx[:9],
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
                    },
                    index=dt_idx[:9],
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
                    },
                    index=dt_idx[:9],
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
                    },
                    index=dt_idx[:9],
                ),
            ),
        ],
    )
    def test_fundamental_mock(
        self,
        ssc: SETSignalCreator,
        data: pd.DataFrame,
        method: str,
        period: int,
        shift: int,
        expected: pd.DataFrame,
    ):
        # Mock
        ssc._reindex_trade_date = lambda df: df
        ssc._sdr._get_fundamental_data = Mock(return_value=data)

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

        self._check(result)

        assert_frame_equal(result, expected)

    @pytest.mark.parametrize(
        ("field", "timeframe", "value_by"),
        [
            (fld.D_CLOSE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_STOCK),
            (fld.D_PE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_STOCK),
            (fld.Q_EBITDA, fld.TIMEFRAME_QUARTERLY, fld.VALUE_BY_STOCK),
            (fld.D_SECTOR_CLOSE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_SECTOR),
            (fld.D_INDUSTRY_CLOSE, fld.TIMEFRAME_DAILY, fld.VALUE_BY_INDUSTRY),
        ],
    )
    @pytest.mark.parametrize("shift", [0, 1, 999])
    @pytest.mark.parametrize(
        ("method", "period"),
        [
            (fld.METHOD_CONSTANT, 0),
            (fld.METHOD_MEAN, 1),
            (fld.METHOD_MEAN, 2),
            (fld.METHOD_MEAN, 999),
        ],
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
