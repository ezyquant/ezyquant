import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from ezyquant.report import SETBacktestReport

nan = float("nan")
month_abbr = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@pytest.mark.parametrize("init_cap", [1.0, 1])
@pytest.mark.parametrize(
    ("nav_df", "expect_result_data"),
    [
        (
            pd.DataFrame(
                [1.0], index=pd.DatetimeIndex(["2000-01-01"]), columns=["port_value"]
            ),
            [[0.0, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]],
        ),
        (
            pd.DataFrame(
                [1.0], index=pd.DatetimeIndex(["2000-02-01"]), columns=["port_value"]
            ),
            [[nan, 0.0, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]],
        ),
        (
            pd.DataFrame(
                [2.0, 1.0],
                index=pd.DatetimeIndex(["2000-01-01", "2000-01-02"]),
                columns=["port_value"],
            ),
            [[0.0, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]],
        ),
        (
            pd.DataFrame(
                [2.0, 1.0, 2.0, 1.0],
                index=pd.DatetimeIndex(
                    ["2000-01-01", "2000-01-02", "2000-02-01", "2000-02-02"]
                ),
                columns=["port_value"],
            ),
            [[0.0, 0.0, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]],
        ),
        (
            pd.DataFrame(
                [1.0, 1.0, 1.0],
                index=pd.DatetimeIndex(["2000-01-01", "2000-02-01", "2000-03-01"]),
                columns=["port_value"],
            ),
            [[0.0, 0.0, 0.0, nan, nan, nan, nan, nan, nan, nan, nan, nan]],
        ),
        (
            pd.DataFrame(
                [1.0, 2.0, 3.0],
                index=pd.DatetimeIndex(["2000-01-01", "2000-02-01", "2000-03-01"]),
                columns=["port_value"],
            ),
            [[0.0, 1.0, 0.5, nan, nan, nan, nan, nan, nan, nan, nan, nan]],
        ),
        (
            pd.DataFrame(
                [1.0, 1.0],
                index=pd.DatetimeIndex(["2000-12-01", "2001-01-01"]),
                columns=["port_value"],
            ),
            [
                [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 0.0],
                [0.0, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan],
            ],
        ),
        (
            pd.DataFrame(
                [1.0, 2.0, 3.0],
                index=pd.DatetimeIndex(["2000-12-01", "2001-01-01", "2001-02-01"]),
                columns=["port_value"],
            ),
            [
                [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 0.0],
                [1.0, 0.5, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan],
            ],
        ),
    ],
)
def test_return_by_period_m(
    nav_df: pd.DataFrame, init_cap: float, expect_result_data: list
):
    # Test
    result = SETBacktestReport._return_by_period(nav_df, init_cap, "M")

    # Check
    expect_result = pd.DataFrame(
        expect_result_data,
        index=pd.MultiIndex.from_tuples(
            [("port_value", 2000 + i) for i in range(len(expect_result_data))],
            names=["name", "year"],
        ),
        columns=pd.Index(month_abbr, name="month"),
    )
    assert_frame_equal(result, expect_result)


@pytest.mark.parametrize("init_cap", [1.0, 1])
@pytest.mark.parametrize(
    ("nav_df", "expect_result_data"),
    [
        (
            pd.DataFrame(
                [1.0], index=pd.DatetimeIndex(["2000-01-01"]), columns=["port_value"]
            ),
            [0.0],
        ),
        (
            pd.DataFrame(
                [1.0], index=pd.DatetimeIndex(["2000-02-01"]), columns=["port_value"]
            ),
            [0.0],
        ),
        (
            pd.DataFrame(
                [2.0, 1.0],
                index=pd.DatetimeIndex(["2000-01-01", "2000-01-02"]),
                columns=["port_value"],
            ),
            [0.0],
        ),
        (
            pd.DataFrame(
                [2.0, 1.0, 2.0, 1.0],
                index=pd.DatetimeIndex(
                    ["2000-01-01", "2000-01-02", "2000-02-01", "2000-02-02"]
                ),
                columns=["port_value"],
            ),
            [0.0],
        ),
        (
            pd.DataFrame(
                [1.0, 1.0, 1.0],
                index=pd.DatetimeIndex(["2000-01-01", "2000-02-01", "2000-03-01"]),
                columns=["port_value"],
            ),
            [0.0],
        ),
        (
            pd.DataFrame(
                [1.0, 2.0, 3.0],
                index=pd.DatetimeIndex(["2000-01-01", "2000-02-01", "2000-03-01"]),
                columns=["port_value"],
            ),
            [2.0],
        ),
        (
            pd.DataFrame(
                [1.0, 1.0],
                index=pd.DatetimeIndex(["2000-12-01", "2001-01-01"]),
                columns=["port_value"],
            ),
            [0.0, 0.0],
        ),
        (
            pd.DataFrame(
                [1.0, 2.0, 3.0],
                index=pd.DatetimeIndex(["2000-12-01", "2001-01-01", "2001-02-01"]),
                columns=["port_value"],
            ),
            [0.0, 2.0],
        ),
    ],
)
def test_return_by_period_y(
    nav_df: pd.DataFrame, init_cap: float, expect_result_data: list
):
    # Test
    result = SETBacktestReport._return_by_period(nav_df, init_cap, "Y")

    # Check
    expect_result = pd.DataFrame(
        expect_result_data,
        index=pd.MultiIndex.from_tuples(
            [("port_value", 2000 + i) for i in range(len(expect_result_data))],
            names=["name", "year"],
        ),
        columns=pd.Index(["YTD"], name="month"),
    )
    assert_frame_equal(result, expect_result)
