from typing import List
from unittest.mock import ANY, Mock

import pandas as pd
import pytest
from numpy import inf, nan
from pandas.testing import assert_frame_equal, assert_series_equal

import ezyquant.fields as fld
from ezyquant import SETSignalCreator
from ezyquant import validators as vld
from ezyquant.errors import InputError
from tests import constant as const
from tests import utils

IDX_2020_01_02_TO_2020_01_15 = pd.DatetimeIndex(
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
    def test_symbol_list(self, symbol_list: List[str], expected: List[str]):
        # Mock
        ssc = SETSignalCreator(symbol_list=symbol_list)

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
                [fld.INDEX_SET50, fld.INDEX_SSET.upper()],
                "2022-01-04",
                "2022-01-04",
                const.SET50_2022_01_04 + const.SSET_2022_01_04,
            ),
            (
                [fld.INDEX_SET50, fld.INDEX_SSET.upper()],
                "2022-04-26",
                "2022-04-27",
                const.SET50_2022_01_04 + const.SSET_2022_01_04 + const.SET50_2022_04_27,
            ),
        ],
    )
    def test_dynamic_index_list(
        self,
        index_list: List[str],
        start_date: str,
        end_date: str,
        expected: List[str],
    ):
        # Mock
        ssc = SETSignalCreator(
            index_list=index_list,
            start_date=start_date,
            end_date=end_date,
        )

        # Test
        result = ssc._get_symbol_in_universe()

        # Check
        assert set(result) == set(expected)

    @pytest.mark.parametrize(
        ("index_list", "expected"),
        [
            ([fld.INDUSTRY_AGRO], const.ARGO_SET),
            ([fld.SECTOR_AGRI], const.AGRI_SET),
            ([fld.SECTOR_AGRI, fld.SECTOR_FOOD], const.ARGO_SET),
            ([fld.INDUSTRY_AGRO_MAI], const.ARGO_MAI),
        ],
    )
    def test_static_index_list(
        self,
        index_list: List[str],
        expected: List[str],
    ):
        # Mock
        ssc = SETSignalCreator(
            index_list=index_list,
            start_date="2022-11-01",
            end_date="2022-12-01",
        )

        # Test
        result = ssc._get_symbol_in_universe()

        # Check
        assert set(result) == set(expected)


class TestGetData:
    _check = staticmethod(vld.check_df_symbol_daily)

    def test_sector_daily(self):
        # Mock
        ssc = SETSignalCreator(
            index_list=[fld.MARKET_SET, fld.MARKET_MAI],
            start_date="2021-05-18",
            end_date="2021-05-31",
        )

        # Test
        result = ssc.get_data(
            field=fld.D_SECTOR_CLOSE,
            timeframe=fld.TIMEFRAME_DAILY,
            value_by=fld.VALUE_BY_SECTOR,
            method=fld.METHOD_CONSTANT,
            period=1,
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
            "SCBB",
            "TCAP",
            "TISCO",
            "TTB",
        ]:
            assert_series_equal(
                result[i], const.BANK_D_CLOSE_2021_05_18, check_names=False
            )

    def test_industry_daily(self):
        # Mock
        ssc = SETSignalCreator(
            index_list=[fld.MARKET_SET, fld.MARKET_MAI],
            start_date="2021-05-18",
            end_date="2021-05-31",
        )

        # Test
        result = ssc.get_data(
            field=fld.D_SECTOR_CLOSE,
            timeframe=fld.TIMEFRAME_DAILY,
            value_by=fld.VALUE_BY_INDUSTRY,
            method=fld.METHOD_CONSTANT,
            period=1,
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
    def test_stock_daily_fill_prior(self, field: str):
        """THAI no trade after 2021-05-18, close at 2021-05-17 is 3.32"""
        # Mock
        ssc = SETSignalCreator(
            symbol_list=["THAI"],
            start_date="2021-05-18",
            end_date="2021-05-31",
        )

        # Test
        result = ssc.get_data(
            field=field,
            timeframe=fld.TIMEFRAME_DAILY,
            value_by=fld.VALUE_BY_STOCK,
            method=fld.METHOD_CONSTANT,
            period=1,
            shift=0,
        )

        # Check
        expect = pd.DataFrame(
            {"THAI": 3.32},
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
                    "A": [11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0],
                    "B": [21.0, 22.0, nan, inf, nan, 26.0, inf, nan, 29.0],
                    "C": [nan] * 9,
                },
                index=IDX_2020_01_02_TO_2020_01_15[:9],
            )
        ],
    )
    @pytest.mark.parametrize(
        ("method", "period", "shift", "expected"),
        [
            (
                fld.METHOD_CONSTANT,
                1,
                0,
                pd.DataFrame(
                    {
                        "A": [11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0],
                        "B": [21.0, 22.0, 22.0, nan, nan, 26.0, nan, nan, 29.0],
                        "C": [nan] * 9,
                    },
                    index=IDX_2020_01_02_TO_2020_01_15[:9],
                ),
            ),
            (
                fld.METHOD_CONSTANT,
                1,
                1,
                pd.DataFrame(
                    {
                        "A": [nan, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0],
                        "B": [nan, 21.0, 21.0, 22.0, 22.0, nan, 26.0, 26.0, nan],
                        "C": [nan] * 9,
                    },
                    index=IDX_2020_01_02_TO_2020_01_15[:9],
                ),
            ),
            (
                fld.METHOD_SUM,
                2,
                0,
                pd.DataFrame(
                    {
                        "A": [nan, 23.0, 25.0, 27.0, 29.0, 31.0, 33.0, 35.0, 37.0],
                        "B": [nan, 43.0, 43.0, nan, nan, nan, nan, nan, nan],
                        "C": [nan] * 9,
                    },
                    index=IDX_2020_01_02_TO_2020_01_15[:9],
                ),
            ),
            (
                fld.METHOD_SUM,
                2,
                1,
                pd.DataFrame(
                    {
                        "A": [nan, nan, 23.0, 25.0, 27.0, 29.0, 31.0, 33.0, 35.0],
                        "B": [nan, nan, nan, 43.0, 43.0, nan, nan, nan, nan],
                        "C": [nan] * 9,
                    },
                    index=IDX_2020_01_02_TO_2020_01_15[:9],
                ),
            ),
        ],
    )
    def test_fundamental_mock(
        self,
        data: pd.DataFrame,
        method: str,
        period: int,
        shift: int,
        expected: pd.DataFrame,
    ):
        # Mock
        symbols = ["A", "B", "C"]
        ssc = SETSignalCreator()
        ssc._get_symbol_in_universe = Mock(return_value=symbols)
        ssc._reindex_trade_date = lambda df, **kwargs: df  # type: ignore
        ssc._sdr._get_fundamental_data = Mock(return_value=data)
        ssc.is_banned = Mock(
            return_value=pd.DataFrame(
                False,
                columns=data.columns,
                index=data.index,
            )
        )

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
            symbol_list=symbols,
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
            (fld.METHOD_CONSTANT, 1),
            (fld.METHOD_MEAN, 1),
            (fld.METHOD_MEAN, 2),
            (fld.METHOD_MEAN, 999),
        ],
    )
    def test_empty(
        self,
        field: str,
        timeframe: str,
        value_by: str,
        method: str,
        period: int,
        shift: int,
    ):
        ssc = SETSignalCreator()

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


IDX_2022_04_01_TO_2022_04_29 = pd.DatetimeIndex(
    [
        "2022-04-01",
        "2022-04-04",
        "2022-04-05",
        "2022-04-07",
        "2022-04-08",
        "2022-04-11",
        "2022-04-12",
        "2022-04-18",
        "2022-04-19",
        "2022-04-20",
        "2022-04-21",
        "2022-04-22",
        "2022-04-25",
        "2022-04-26",
        "2022-04-27",
        "2022-04-28",
        "2022-04-29",
    ],
    freq=None,
)


class TestIsUniverse:
    @pytest.mark.parametrize(
        "universe",
        [
            fld.MARKET_SET,
            fld.MARKET_MAI,
            fld.INDUSTRY_FINCIAL,
            fld.INDUSTRY_AGRO,
            fld.SECTOR_BANK,
            fld.SECTOR_INSUR,
            fld.SECTOR_AGRI,
            "AOT",
        ],
    )
    def test_static(self, universe: str):
        # Mock
        ssc = SETSignalCreator(
            index_list=[fld.MARKET_SET, fld.MARKET_MAI],
            start_date="2022-04-01",
            end_date="2022-05-01",
        )

        # Test
        result = ssc.is_universe([universe])

        # Check
        self._check(result)
        assert utils.is_df_unique_cols(result)

    @pytest.mark.parametrize(
        ("universe", "expected_true"),
        [
            (fld.INDUSTRY_AGRO, const.ARGO_SET),
            (fld.SECTOR_AGRI, const.AGRI_SET),
            (fld.INDUSTRY_AGRO_MAI, const.ARGO_MAI),
        ],
    )
    def test_static_with_expect(self, universe: str, expected_true: List[str]):
        # Mock
        ssc = SETSignalCreator(
            index_list=[fld.MARKET_SET, fld.MARKET_MAI],
            start_date="2022-11-01",
            end_date="2022-12-01",
        )

        # Test
        result = ssc.is_universe([universe])

        # Check
        self._check(result)
        assert utils.is_df_unique_cols(result)
        assert set(result.columns[result.iloc[0]]) == set(expected_true)

    @pytest.mark.parametrize(
        "universe",
        [
            fld.INDEX_SETWB,
            fld.INDEX_SETTHSI,
            fld.INDEX_SETCLMV,
            fld.INDEX_SETHD,
            fld.INDEX_SSET,
            fld.INDEX_SET100,
            fld.INDEX_SET50,
        ],
    )
    def test_dynamic(self, universe: str):
        # Mock
        ssc = SETSignalCreator(
            index_list=[fld.MARKET_SET, fld.MARKET_MAI],
            start_date="2022-04-01",
            end_date="2022-05-01",
        )

        # Test
        result = ssc.is_universe([universe])

        # Check
        self._check(result)

    @pytest.mark.parametrize("universe", [fld.INDEX_SSET])
    def test_dynamic_universe_not_launch(self, universe: str):
        """sSET launch 2017-01-01"""
        # Mock
        ssc = SETSignalCreator(
            index_list=[fld.MARKET_SET, fld.MARKET_MAI],
            start_date="2010-01-01",
            end_date="2010-02-01",
        )

        # Test
        result = ssc.is_universe([universe])

        # Check
        self._check(result)
        assert (result == False).all().all()

    def test_multi_universe(self):
        # Mock
        ssc = SETSignalCreator(index_list=[fld.MARKET_SET, fld.MARKET_MAI])

        # Test
        result = ssc.is_universe(["AOT", "BBL"])

        # Check
        self._check(result)
        assert result["AOT"].all()
        assert result["BBL"].all()
        assert (result["CPF"] == False).all()

    def test_no_universe(self):
        # Mock
        ssc = SETSignalCreator(index_list=[fld.MARKET_SET, fld.MARKET_MAI])

        # Test
        result = ssc.is_universe([])

        # Check
        self._check(result)
        assert (result == False).all().all()

    @pytest.mark.parametrize(
        ("index_list", "symbol_list"),
        [
            ([], ["SCB", "SCBB"]),
            ([], ["SCBB", "SCB", "AU"]),
            ([fld.INDEX_SET50], []),
            ([fld.INDEX_SET100], []),
            ([fld.MARKET_SET, fld.MARKET_MAI], []),
            ([fld.INDEX_SET50], ["SCB", "SCBB"]),
            ([fld.INDEX_SET50], ["AU"]),
            ([fld.MARKET_MAI], ["SCB", "SCBB"]),
        ],
    )
    @pytest.mark.parametrize(
        ("universe", "expect"),
        [
            (
                fld.MARKET_SET,
                pd.DataFrame(
                    {"SCB": True, "SCBB": True},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.MARKET_MAI,
                pd.DataFrame(
                    {"SCB": False, "SCBB": False},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.INDUSTRY_FINCIAL,
                pd.DataFrame(
                    {"SCB": True, "SCBB": True},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.INDUSTRY_AGRO,
                pd.DataFrame(
                    {"SCB": False, "SCBB": False},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.SECTOR_BANK,
                pd.DataFrame(
                    {"SCB": True, "SCBB": True},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.SECTOR_INSUR,
                pd.DataFrame(
                    {"SCB": False, "SCBB": False},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.SECTOR_AGRI,
                pd.DataFrame(
                    {"SCB": False, "SCBB": False},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.INDEX_SET100,
                pd.DataFrame(
                    {
                        "SCB": [False] * 14 + [True] * 3,
                        "SCBB": [True] * 14 + [False] * 3,
                    },
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.INDEX_SET50,
                pd.DataFrame(
                    {
                        "SCB": [False] * 14 + [True] * 3,
                        "SCBB": [True] * 14 + [False] * 3,
                    },
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
            (
                fld.INDEX_SSET.upper(),
                pd.DataFrame(
                    {"SCB": False, "SCBB": False},
                    index=IDX_2022_04_01_TO_2022_04_29,
                ),
            ),
        ],
    )
    def test_with_expect(
        self,
        index_list: List[str],
        symbol_list: List[str],
        universe: str,
        expect: pd.DataFrame,
    ):
        # Mock
        ssc = SETSignalCreator(
            index_list=index_list,
            symbol_list=symbol_list,
            start_date="2022-04-01",
            end_date="2022-05-01",
        )

        # Test
        result = ssc.is_universe([universe])

        # Check
        self._check(result)
        assert_frame_equal(result[["SCB", "SCBB"]], expect)

    @pytest.mark.parametrize("universe", ["", "invalid"])
    def test_invalid_universe(self, universe: str):
        ssc = SETSignalCreator()
        with pytest.raises(InputError):
            ssc.is_universe([universe])

    @staticmethod
    def _check(result):
        vld.check_df_symbol_daily(result)

        assert (result.dtypes == bool).all()
        assert result.notna().all().all()


class TestIsBanned:
    _check = staticmethod(TestIsUniverse._check)

    @pytest.mark.parametrize(
        ("start_date", "end_date"),
        [
            ("2010-01-01", "2022-01-01"),
            ("2021-01-01", "2021-02-01"),
            ("2021-02-24", "2021-02-24"),
            ("2021-02-25", "2021-02-25"),
        ],
    )
    def test_all(self, start_date: str, end_date: str):
        # Mock
        ssc = SETSignalCreator(
            index_list=[fld.MARKET_SET, fld.MARKET_MAI],
            start_date=start_date,
            end_date=end_date,
        )

        # Test
        result = ssc.is_banned()

        # Check
        self._check(result)

    @pytest.mark.parametrize("symbol_list", [["JTS"], ["JTS", "THAI"]])
    def test_one_day_sp(self, symbol_list: List[str]):
        """https://portal.settrade.com/NewsEngineTXTDisplay.jsp?newsId=16529175763321&t=H&fp=/simsImg/news/histri/202205/22065589.t22&tk=ee62bd2018156b05378402dcd9cb4828&q=Y"""
        # Mock
        ssc = SETSignalCreator(
            symbol_list=symbol_list,
            start_date="2022-04-01",
            end_date="2022-05-01",
        )

        # Test
        result = ssc.is_banned()

        # Check
        self._check(result)

        assert_frame_equal(
            result[["JTS"]],
            pd.DataFrame(
                {
                    "JTS": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        True,
                        False,
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                    ]
                },
                index=IDX_2022_04_01_TO_2022_04_29,
            ),
        )

    @pytest.mark.parametrize(
        ("symbol", "start_date", "end_date", "expect"),
        [
            ("THAI", "2021-01-01", "2021-02-01", False),
            ("THAI", "2021-02-24", "2021-02-24", False),
            ("THAI", "2021-02-25", "2021-02-25", True),
            ("THAI", "2022-01-01", "2022-02-01", True),
            ("SCBB", "2022-01-01", "2022-02-01", False),
            ("SCBB", "2022-04-26", "2022-04-26", False),
            ("AOT", "2010-01-01", "2020-01-01", False),
        ],
    )
    def test_one_symbol(
        self, symbol: str, start_date: str, end_date: str, expect: bool
    ):
        # Mock
        ssc = SETSignalCreator(
            symbol_list=[symbol],
            start_date=start_date,
            end_date=end_date,
        )

        # Test
        result = ssc.is_banned()

        # Check
        self._check(result)

        assert (result[symbol] == expect).all()

    def test_scbb_delist(self):
        """SCBB delist on 2022-04-27 (2022-04-26 can trade)."""
        # Mock
        ssc = SETSignalCreator(
            symbol_list=["SCBB"],
            start_date="2022-04-26",
            end_date="2022-04-27",
        )

        # Test
        result = ssc.is_banned()

        # Check
        self._check(result)

        assert_frame_equal(
            result,
            pd.DataFrame(
                {"SCBB": [False, True]},
                index=pd.DatetimeIndex(["2022-04-26", "2022-04-27"]),
            ),
        )


class TestRank:
    @pytest.mark.parametrize(
        ("factor_df", "expect"),
        [
            (pd.DataFrame(), pd.DataFrame()),
            (pd.DataFrame([[11.0, 12.0, 13.0]]), pd.DataFrame([[1.0, 2.0, 3.0]])),
            (
                pd.DataFrame(
                    [
                        [11.0, 12.0, 13.0],
                        [21.0, nan, 23.0],
                        [31.0, 31.0, 31.0],
                    ]
                ),
                pd.DataFrame(
                    [
                        [1.0, 2.0, 3.0],
                        [1.0, nan, 2.0],
                        [1.0, 1.0, 1.0],
                    ]
                ),
            ),
        ],
    )
    def test_no_quantity_ascending(self, factor_df: pd.DataFrame, expect: pd.DataFrame):
        result = SETSignalCreator.rank(factor_df, method="min")

        assert_frame_equal(result, expect)

    @pytest.mark.parametrize(
        ("factor_df", "expect"),
        [
            (pd.DataFrame(), pd.DataFrame()),
            (pd.DataFrame([[11.0, 12.0, 13.0]]), pd.DataFrame([[1.0, 2.0, nan]])),
            (
                pd.DataFrame(
                    [
                        [11.0, 12.0, 13.0],
                        [21.0, nan, 23.0],
                        [31.0, 31.0, 31.0],
                    ]
                ),
                pd.DataFrame(
                    [
                        [1.0, 2.0, nan],
                        [1.0, nan, 2.0],
                        [1.0, 1.0, 1.0],
                    ]
                ),
            ),
        ],
    )
    def test_quantity(self, factor_df: pd.DataFrame, expect: pd.DataFrame):
        result = SETSignalCreator.rank(factor_df, quantity=2, method="min")

        assert_frame_equal(result, expect)

    @pytest.mark.parametrize(
        ("factor_df", "expect"),
        [
            (pd.DataFrame(), pd.DataFrame()),
            (pd.DataFrame([[11.0, 12.0, 13.0]]), pd.DataFrame([[1 / 3, nan, nan]])),
            (
                pd.DataFrame(
                    [
                        [11.0, 12.0, 13.0],
                        [21.0, nan, 23.0],
                        [31.0, 31.0, 31.0],
                    ]
                ),
                pd.DataFrame(
                    [
                        [1 / 3, nan, nan],
                        [1 / 2, nan, nan],
                        [1 / 3, nan, nan],
                    ]
                ),
            ),
        ],
    )
    def test_pct(self, factor_df: pd.DataFrame, expect: pd.DataFrame):
        result = SETSignalCreator.rank(factor_df, pct=True, quantity=0.5)

        assert_frame_equal(result, expect)


class TestScreenUniverse:
    @pytest.mark.parametrize(
        ("index_list", "symbol_list"),
        [
            ([], ["AOT"]),
            ([], ["AOT", "BBL"]),
            (["SET"], []),
            (["SET", "SET50"], []),
            (["SET"], ["AOT"]),
        ],
    )
    def test_no_screen(self, index_list: List[str], symbol_list: List[str]):
        # Mock
        ssc = SETSignalCreator(
            index_list=index_list,
            symbol_list=symbol_list,
        )

        df = pd.DataFrame(
            [[1.0], [2.0], [3.0]],
            columns=["AOT"],
            index=pd.bdate_range(start="2022-01-04", periods=3),
        )

        # Test
        result = ssc.screen_universe(df)

        # Check
        assert_frame_equal(result, df)

    def test_banned(self):
        """THAI no trade after 2021-05-18, close at 2021-05-17 is 3.32"""
        # Mock
        ssc = SETSignalCreator(
            index_list=[],
            symbol_list=["THAI"],
        )

        df = pd.DataFrame(
            [[1.0], [2.0], [3.0]],
            columns=["THAI"],
            index=pd.bdate_range(start="2021-05-17", periods=3),
        )

        # Test
        result = ssc.screen_universe(df)

        # Check
        expect = pd.DataFrame(
            [[1.0], [nan], [nan]],
            columns=["THAI"],
            index=pd.bdate_range(start="2021-05-17", periods=3),
        )
        assert_frame_equal(expect, result)

    def test_universe(self):
        """
        BANPU added to SET50 on 2022
        https://thestandard.co/set50-set100-2565/
        """
        # Mock
        ssc = SETSignalCreator(
            index_list=["SET50"],
            symbol_list=[],
        )
        df = pd.DataFrame(
            [[1.0], [2.0], [3.0]],
            columns=["BANPU"],
            index=pd.DatetimeIndex(["2021-12-30", "2022-01-04", "2022-01-05"]),
        )

        # Test
        result = ssc.screen_universe(df)

        # Check
        expect = pd.DataFrame(
            [[nan], [2.0], [3.0]],
            columns=["BANPU"],
            index=pd.DatetimeIndex(["2021-12-30", "2022-01-04", "2022-01-05"]),
        )
        assert_frame_equal(expect, result)


class TestGetSymbolsByTradingSign:
    def test_success_default(self):
        # Mock
        ssc = SETSignalCreator(symbol_list=["BTS"])

        # Test
        result = ssc.get_symbols_by_trading_sign()

        # Check
        assert result == ["BTS"]

    def test_success_specific(self):
        # Mock
        ssc = SETSignalCreator(symbol_list=["BTS"])

        # Test
        result = ssc.get_symbols_by_trading_sign(
            start_date="2022-02-07",
            end_date="2022-02-07",
            sign_list=["CD"],
        )

        # Check
        assert result == ["BTS"]

    def test_empty(self):
        # Mock
        ssc = SETSignalCreator(symbol_list=["BTS"])

        # Test
        result = ssc.get_symbols_by_trading_sign(
            start_date="2022-02-08",
            end_date="2022-02-08",
            sign_list=["CD"],
        )

        # Check
        assert result == []
