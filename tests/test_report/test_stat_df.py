from typing import List
from unittest.mock import PropertyMock, patch

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from ezyquant.report import SETBacktestReport
from tests import utils


@pytest.mark.parametrize(
    ("nav_list", "expected_result"),
    [
        ([100.0], 0.0),
        ([100.0, 200.0], 0.0),
        ([100.0, 200.0, 300.0], 0.0),
        ([100.0, 50.0], -0.5),
        ([100.0, 50.0, 10.0], -0.9),
        ([100.0, 200.0, 100.0], -0.5),
        ([100.0, 200.0, 100.0, 400.0, 100.0], -0.75),
    ],
)
def test_pct_maximum_drawdown(
    sbr: SETBacktestReport, nav_list: List[float], expected_result: float
):
    # Mock
    sbr._initial_capital = nav_list[0]
    summary_df = pd.DataFrame(
        {
            "timestamp": utils.make_bdate_range(len(nav_list)),
            "port_value": nav_list,
            "port_value_with_dividend": nav_list,
        }
    )

    # Test
    with patch(
        "ezyquant.report.SETBacktestReport.summary_df", new_callable=PropertyMock
    ) as mock_summary_df:
        mock_summary_df.return_value = summary_df

        result = sbr.pct_maximum_drawdown

    # Check
    assert_series_equal(
        result,
        pd.Series(
            {"portfolio": expected_result, "portfolio_with_dividend": expected_result}
        ),
    )


@pytest.mark.parametrize(
    ("nav_list", "expected_result"),
    [
        ([100.0], 0.0),
        ([100.0, 200.0], 0.0),
        ([100.0, 200.0, 300.0], 0.0),
        ([100.0, 50.0], -50.0),
        ([100.0, 50.0, 10.0], -90.0),
        ([100.0, 200.0, 100.0], -100.0),
        ([100.0, 200.0, 100.0, 400.0, 100.0], -300.0),
    ],
)
def test_maximum_drawdown(
    sbr: SETBacktestReport, nav_list: List[float], expected_result: float
):
    # Mock
    summary_df = pd.DataFrame(
        {
            "timestamp": utils.make_bdate_range(len(nav_list)),
            "port_value": nav_list,
            "port_value_with_dividend": nav_list,
        }
    )

    # Test
    with patch(
        "ezyquant.report.SETBacktestReport.summary_df", new_callable=PropertyMock
    ) as mock_summary_df:
        mock_summary_df.return_value = summary_df

        result = sbr.maximum_drawdown

    # Check
    assert_series_equal(
        result,
        pd.Series(
            {"portfolio": expected_result, "portfolio_with_dividend": expected_result}
        ),
    )


@pytest.mark.parametrize(
    ("nav_list", "mkt_value_list", "expected_result"),
    [
        ([100.0], [0.0], 0.0),
        ([100.0], [100.0], 1.0),
        ([100.0, 100.0], [0.0, 0.0], 0.0),
        ([100.0, 100.0], [0.0, 100.0], 0.5),
        ([100.0, 100.0], [100.0, 0.0], 0.5),
        ([100.0, 100.0], [100.0, 100.0], 1.0),
    ],
)
def test_pct_exposure(
    sbr: SETBacktestReport,
    nav_list: List[float],
    mkt_value_list: List[float],
    expected_result: float,
):
    # Mock
    summary_df = pd.DataFrame(
        {
            "port_value": nav_list,
            "port_value_with_dividend": nav_list,
            "total_market_value": mkt_value_list,
        }
    )

    # Test
    with patch(
        "ezyquant.report.SETBacktestReport.summary_df", new_callable=PropertyMock
    ) as mock_summary_df:
        mock_summary_df.return_value = summary_df

        result = sbr.pct_exposure

    # Check
    assert_series_equal(
        result,
        pd.Series(
            {"portfolio": expected_result, "portfolio_with_dividend": expected_result}
        ),
    )
