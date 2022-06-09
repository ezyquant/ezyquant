import pandas as pd
import pytest
import utils
from pandas.testing import assert_frame_equal

from ezyquant.backtest import result as res

position_in_columns = ["timestamp", "symbol", "volume", "avg_cost_price"]
position_columns = [
    "timestamp",
    "symbol",
    "volume",
    "avg_cost_price",
    "close_price",
    "close_value",
]


class TestMakePositionDf:
    @pytest.mark.parametrize(
        "close_price_df",
        [
            utils.make_data_df(
                [[1.0, 4.0, 7.0], [2.0, 5.0, 8.0], [3.0, 6.0, 9.0]], n_col=3, n_row=3
            )
        ],
    )
    @pytest.mark.parametrize(
        ("position_df", "expect_result"),
        [
            (
                pd.DataFrame(columns=position_in_columns),
                pd.DataFrame(columns=position_columns),
            ),
            (
                pd.DataFrame(
                    [
                        [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1],
                    ],
                    columns=position_in_columns,
                ),
                pd.DataFrame(
                    [
                        [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0],
                    ],
                    columns=position_columns,
                ),
            ),
            (
                pd.DataFrame(
                    [
                        [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1],
                        [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1],
                    ],
                    columns=position_in_columns,
                ),
                pd.DataFrame(
                    [
                        [pd.Timestamp("2000-01-03"), "AAA", 100.0, 0.1, 1.0, 100.0],
                        [pd.Timestamp("2000-01-04"), "AAA", 100.0, 0.1, 2.0, 200.0],
                    ],
                    columns=position_columns,
                ),
            ),
        ],
    )
    def test_make_position_df(
        self,
        position_df: pd.DataFrame,
        close_price_df: pd.DataFrame,
        expect_result: pd.DataFrame,
    ):
        result = res.make_position_df(position_df, close_price_df)

        assert_frame_equal(result, expect_result, check_dtype=False)  # type: ignore
