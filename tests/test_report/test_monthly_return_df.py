from unittest.mock import Mock

import pandas as pd
import pytest

from ezyquant.report import SETBacktestReport


@pytest.mark.parametrize(("nav_df", "init_cap"), [])
def test_return_by_period_m(nav_df: pd.DataFrame, init_cap: float):
    result = SETBacktestReport._return_by_period(nav_df, init_cap, "M")

    print(result)
