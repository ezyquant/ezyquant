from unittest.mock import Mock, PropertyMock, patch

import pandas as pd
import pandas.api.types as ptypes
import pytest
from pandas.testing import assert_frame_equal, assert_index_equal

from ezyquant.report import SETBacktestReport, dividend_columns
from tests import utils
from tests.test_report.conftest import _make_empty_backtest_report


class TestDividendDf:
    def setup_method(self, _):
        self.position_df = SETBacktestReport.position_df

    def teardown_method(self, _):
        SETBacktestReport.position_df = self.position_df

    def _test(
        self,
        position_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        # Mock
        sbr = _make_empty_backtest_report()
        sbr._sdr.get_dividend = Mock(return_value=dividend_df)
        sbr._sdr.get_trading_dates = Mock(return_value=utils.make_trading_dates())

        # Test
        with patch(
            "ezyquant.report.SETBacktestReport.position_df", new_callable=PropertyMock
        ) as mock_position_df:
            mock_position_df.return_value = position_df

            result = sbr.dividend_df

        # Check
        _check_dividend_df(result)
        assert_frame_equal(result, expect_result, check_dtype=False)

    @pytest.mark.parametrize(
        "dividend_df",
        [
            pd.DataFrame(
                [["AAA", pd.Timestamp("2000-01-04"), pd.Timestamp("2000-01-05"), 1.0]],
                columns=["symbol", "ex_date", "pay_date", "dps"],
            )
        ],
    )
    @pytest.mark.parametrize(
        ("position_df", "expect_result"),
        [
            (
                pd.DataFrame(columns=["timestamp", "symbol", "volume"]),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [[pd.Timestamp("2000-01-04"), "AAA", 100.0]],
                    columns=["timestamp", "symbol", "volume"],
                ),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [[pd.Timestamp("2000-01-03"), "AAB", 100.0]],
                    columns=["timestamp", "symbol", "volume"],
                ),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [[pd.Timestamp("2000-01-03"), "AAA", 100.0]],
                    columns=["timestamp", "symbol", "volume"],
                ),
                pd.DataFrame(
                    [
                        [
                            pd.Timestamp("2000-01-04"),
                            "AAA",
                            1.0,
                            100.0,
                            100.0,
                            pd.Timestamp("2000-01-03"),
                            pd.Timestamp("2000-01-05"),
                        ]
                    ],
                    columns=dividend_columns,
                ),
            ),
        ],
    )
    def test_position(
        self,
        position_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        self._test(position_df, dividend_df, expect_result)

    @pytest.mark.parametrize(
        "position_df",
        [
            pd.DataFrame(
                [[pd.Timestamp("2000-01-03"), "AAA", 100.0]],
                columns=["timestamp", "symbol", "volume"],
            )
        ],
    )
    @pytest.mark.parametrize(
        ("dividend_df", "expect_result"),
        [
            (
                pd.DataFrame(columns=["symbol", "ex_date", "pay_date", "dps"]),
                pd.DataFrame(columns=dividend_columns),
            ),
            (
                pd.DataFrame(
                    [
                        [
                            "AAA",
                            pd.Timestamp("2000-01-04"),
                            pd.NaT,
                            1.0,
                        ]
                    ],
                    columns=["symbol", "ex_date", "pay_date", "dps"],
                ),
                pd.DataFrame(
                    [
                        [
                            pd.Timestamp("2000-01-04"),
                            "AAA",
                            1.0,
                            100.0,
                            100.0,
                            pd.Timestamp("2000-01-03"),
                            pd.Timestamp("2000-01-04"),
                        ]
                    ],
                    columns=dividend_columns,
                ),
            ),
        ],
    )
    def test_dividend(
        self,
        position_df: pd.DataFrame,
        dividend_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        self._test(position_df, dividend_df, expect_result)


def _check_dividend_df(df):
    assert isinstance(df, pd.DataFrame)

    # Column
    assert_index_equal(df.columns, pd.Index(dividend_columns))

    # Data type
    if not df.empty:
        assert ptypes.is_datetime64_any_dtype(df["ex_date"])
        assert ptypes.is_datetime64_any_dtype(df["before_ex_date"])
        assert ptypes.is_datetime64_any_dtype(df["pay_date"])
        assert ptypes.is_string_dtype(df["symbol"])
        assert ptypes.is_float_dtype(df["dps"])
        assert ptypes.is_float_dtype(df["volume"])
        assert ptypes.is_float_dtype(df["amount"])

    # Value
    assert (df["dps"] > 0).all()
    assert (df["volume"] > 0).all()
    assert (df["amount"] > 0).all()
    assert (df["before_ex_date"] < df["ex_date"]).all()
    assert (df["ex_date"] <= df["pay_date"]).all()
