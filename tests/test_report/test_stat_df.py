import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

import ezyquant.fields as fld
from ezyquant.report import SETBacktestReport, position_columns
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
    sbr: SETBacktestReport, nav_list: pd.DataFrame, expected_result: float
):
    # Mock
    summary_df = pd.DataFrame(
        {
            "timestamp": utils.make_bdate_range(len(nav_list)),
            "port_value": nav_list,
            "port_value_with_dividend": nav_list,
        }
    )
    sbr.__dict__["summary_df"] = summary_df

    # Test
    result = sbr.pct_maximum_drawdown

    # Check
    assert_series_equal(
        result,
        pd.Series(
            {"port_value": expected_result, "port_value_with_dividend": expected_result}
        ),
    )
