from unittest.mock import PropertyMock, patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from ezyquant.report import SETBacktestReport


@pytest.mark.parametrize(
    ("pct_return_list", "expect_result"),
    [
        (
            [],
            pd.DataFrame(
                index=pd.CategoricalIndex([], name="pct_return"),
                columns=["frequency"],
                dtype="int64",
            ),
        ),
        (
            [-0.05],
            pd.DataFrame(
                [1],
                index=pd.CategoricalIndex(
                    [pd.Interval(-0.1, -0.05)], name="pct_return"
                ),
                columns=["frequency"],
                dtype="int64",
            ),
        ),
        (
            [-0.01],
            pd.DataFrame(
                [1],
                index=pd.CategoricalIndex(
                    [pd.Interval(-0.05, 0.00)], name="pct_return"
                ),
                columns=["frequency"],
                dtype="int64",
            ),
        ),
        (
            [0.0],
            pd.DataFrame(
                [1],
                index=pd.CategoricalIndex(
                    [pd.Interval(-0.05, 0.00)], name="pct_return"
                ),
                columns=["frequency"],
                dtype="int64",
            ),
        ),
        (
            [0.01],
            pd.DataFrame(
                [1],
                index=pd.CategoricalIndex([pd.Interval(0.0, 0.05)], name="pct_return"),
                columns=["frequency"],
                dtype="int64",
            ),
        ),
        (
            [0.05],
            pd.DataFrame(
                [1],
                index=pd.CategoricalIndex([pd.Interval(0.0, 0.05)], name="pct_return"),
                columns=["frequency"],
                dtype="int64",
            ),
        ),
        (
            [-0.05, 0.05],
            pd.DataFrame(
                [1, 0, 1],
                index=pd.CategoricalIndex(
                    [
                        pd.Interval(-0.1, -0.05),
                        pd.Interval(-0.05, 0.0),
                        pd.Interval(0.0, 0.05),
                    ],
                    name="pct_return",
                ),
                columns=["frequency"],
                dtype="int64",
            ),
        ),
    ],
)
def test_price_distribution_df(
    sbr: SETBacktestReport, pct_return_list: list, expect_result: pd.DataFrame
):
    summary_trade_df = pd.DataFrame({"pct_return": pct_return_list})

    # Test
    with patch(
        "ezyquant.report.SETBacktestReport.summary_trade_df", new_callable=PropertyMock
    ) as mock_summary_trade_df:
        mock_summary_trade_df.return_value = summary_trade_df

        result = sbr.price_distribution_df

    # Check
    assert_frame_equal(result, expect_result, check_categorical=False)
