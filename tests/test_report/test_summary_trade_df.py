from unittest.mock import PropertyMock, patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import ezyquant.fields as fld
from ezyquant.report import SETBacktestReport, position_columns
from tests import utils


@pytest.mark.parametrize(
    ("position_df", "trade_df", "expect_result"),
    [
        (
            pd.DataFrame(columns=["timestamp", "symbol", "cost_price"]),
            pd.DataFrame(columns=["matched_at", "symbol"]),
            pd.DataFrame(columns=["matched_at", "symbol", "cost_price"]),
        ),
        (
            pd.DataFrame(
                [["2022-01-04", "A", 1.0]],
                columns=["timestamp", "symbol", "cost_price"],
            ),
            pd.DataFrame([["2022-01-05", "A"]], columns=["matched_at", "symbol"]),
            pd.DataFrame(
                [["2022-01-05", "A", 1.0]],
                columns=["matched_at", "symbol", "cost_price"],
            ),
        ),
        (
            pd.DataFrame(
                [["2022-01-04", "A", 1.0]],
                columns=["timestamp", "symbol", "cost_price"],
            ),
            pd.DataFrame([["2022-01-05", "A"]], columns=["matched_at", "symbol"]),
            pd.DataFrame(
                [["2022-01-05", "A", 1.0]],
                columns=["matched_at", "symbol", "cost_price"],
            ),
        ),
        (
            pd.DataFrame(
                [["2022-01-07", "A", 1.0]],
                columns=["timestamp", "symbol", "cost_price"],
            ),
            pd.DataFrame([["2022-01-10", "A"]], columns=["matched_at", "symbol"]),
            pd.DataFrame(
                [["2022-01-10", "A", 1.0]],
                columns=["matched_at", "symbol", "cost_price"],
            ),
        ),
    ],
)
def test_summary_trade_cost_price(
    sbr: SETBacktestReport,
    position_df: pd.DataFrame,
    trade_df: pd.DataFrame,
    expect_result: pd.DataFrame,
):
    # Mock
    position_df["timestamp"] = pd.to_datetime(position_df["timestamp"])
    trade_df["matched_at"] = pd.to_datetime(trade_df["matched_at"])
    expect_result["matched_at"] = pd.to_datetime(expect_result["matched_at"])

    # Test
    with patch(
        "ezyquant.report.SETBacktestReport.position_df", new_callable=PropertyMock
    ) as mock_position_df:
        mock_position_df.return_value = position_df

        result = sbr._summary_trade_cost_price(trade_df=trade_df)

    # Check
    assert_frame_equal(result, expect_result)


@pytest.mark.parametrize(
    ("position_df", "expect_result"),
    [
        (
            pd.DataFrame(columns=position_columns),
            pd.DataFrame(
                columns=[
                    "matched_at",
                    "symbol",
                    "side",
                    "volume",
                    "price",
                    "commission",
                    "cost_price",
                ]
            ),
        ),
        (
            pd.DataFrame(
                [[pd.Timestamp("2000-01-02"), "A", 100.0, 1.0, 1.1, 110.0, 0.1]],
                columns=position_columns,
            ),
            pd.DataFrame(
                columns=[
                    "matched_at",
                    "symbol",
                    "side",
                    "volume",
                    "price",
                    "commission",
                    "cost_price",
                ]
            ),
        ),
        (
            pd.DataFrame(
                [[pd.Timestamp("2000-01-01"), "A", 100.0, 1.0, 1.1, 110.0, 0.1]],
                columns=position_columns,
            ),
            pd.DataFrame(
                [
                    [
                        pd.Timestamp("2000-01-01"),
                        "A",
                        fld.SIDE_SELL,
                        100.0,
                        1.1,
                        0.0,
                        1.0,
                    ]
                ],
                columns=[
                    "matched_at",
                    "symbol",
                    "side",
                    "volume",
                    "price",
                    "commission",
                    "cost_price",
                ],
            ),
        ),
    ],
)
def test_summary_trade_sell_all_position(
    sbr: SETBacktestReport, position_df: pd.DataFrame, expect_result: pd.DataFrame
):
    # Mock
    position_df["timestamp"] = pd.to_datetime(position_df["timestamp"])
    expect_result["matched_at"] = pd.to_datetime(expect_result["matched_at"])

    end_date = pd.Timestamp("2000-01-01")

    # Test
    with patch(
        "ezyquant.report.SETBacktestReport.end_date", new_callable=PropertyMock
    ) as mock_end_date, patch(
        "ezyquant.report.SETBacktestReport.position_df", new_callable=PropertyMock
    ) as mock_position_df:
        mock_end_date.return_value = end_date
        mock_position_df.return_value = position_df

        result = sbr._summary_trade_sell_all_position()

    # Check
    utils.assert_frame_equal_sort_index(result, expect_result, check_dtype=False)


@pytest.mark.parametrize(
    ("df", "expect_entry_at"),
    [
        (pd.DataFrame(columns=["matched_at", "symbol", "side"]), []),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-01"), "A", fld.SIDE_BUY],
                    [pd.Timestamp("2000-01-02"), "A", fld.SIDE_SELL],
                ],
                columns=["matched_at", "symbol", "side"],
            ),
            [pd.Timestamp("2000-01-01"), pd.Timestamp("2000-01-01")],
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-01"), "A", fld.SIDE_BUY],
                    [pd.Timestamp("2000-01-02"), "A", fld.SIDE_SELL],
                    [pd.Timestamp("2000-01-03"), "A", fld.SIDE_SELL],
                ],
                columns=["matched_at", "symbol", "side"],
            ),
            [
                pd.Timestamp("2000-01-01"),
                pd.Timestamp("2000-01-01"),
                pd.Timestamp("2000-01-01"),
            ],
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-01"), "A", fld.SIDE_BUY],
                    [pd.Timestamp("2000-01-02"), "A", fld.SIDE_SELL],
                    [pd.Timestamp("2000-01-03"), "A", fld.SIDE_BUY],
                    [pd.Timestamp("2000-01-04"), "A", fld.SIDE_SELL],
                ],
                columns=["matched_at", "symbol", "side"],
            ),
            [
                pd.Timestamp("2000-01-01"),
                pd.Timestamp("2000-01-01"),
                pd.Timestamp("2000-01-03"),
                pd.Timestamp("2000-01-03"),
            ],
        ),
        (
            pd.DataFrame(
                [
                    [pd.Timestamp("2000-01-01"), "A", fld.SIDE_BUY],
                    [pd.Timestamp("2000-01-02"), "B", fld.SIDE_BUY],
                    [pd.Timestamp("2000-01-03"), "A", fld.SIDE_SELL],
                    [pd.Timestamp("2000-01-03"), "B", fld.SIDE_SELL],
                ],
                columns=["matched_at", "symbol", "side"],
            ),
            [
                pd.Timestamp("2000-01-01"),
                pd.Timestamp("2000-01-02"),
                pd.Timestamp("2000-01-01"),
                pd.Timestamp("2000-01-02"),
            ],
        ),
    ],
)
def test_summary_trade_entry_at(df: pd.DataFrame, expect_entry_at: pd.Series):
    # Mock
    df["matched_at"] = pd.to_datetime(df["matched_at"])

    # Test
    result = SETBacktestReport._summary_trade_entry_at(df.copy())

    # Check
    df["entry_at"] = pd.to_datetime(expect_entry_at)
    assert_frame_equal(result, df)
