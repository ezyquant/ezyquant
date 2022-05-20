from typing import List

import constant as const
import pytest

import ezyquant.fields as fld
from ezyquant import SETSignalCreator


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
