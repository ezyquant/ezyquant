import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import ezyquant.fields as fld
from ezyquant.report import SETBacktestReport, position_columns
from tests import utils


@pytest.mark.parametrize(("summary_df", "expected_result"), [])
def test_pct_maximum_drawdown(
    sbr: SETBacktestReport, summary_df: pd.DataFrame, expected_result: float
):
    # Mock
    sbr.__dict__["summary_df"] = summary_df

    # Test
    result = sbr.pct_maximum_drawdown()

    # Check
    assert result == expected_result
