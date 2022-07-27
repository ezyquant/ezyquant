from datetime import datetime

import pytest

from ezyquant.backtesting import SETTrade


class TestSETTrade:
    @pytest.mark.parametrize("matched_at", [datetime(2000, 1, 1)])
    @pytest.mark.parametrize("symbol", ["A"])
    @pytest.mark.parametrize(
        ("volume", "price", "pct_commission", "expect_value_with_commission"),
        [
            (100, 1.0, 0.0, 100.0),
            (-100, 1.0, 0.0, -100.0),
            (100, 1.0, 0.01, 101.0),
            (-100, 1.0, 0.01, -99.0),
        ],
    )
    def test_value_with_commission(
        self,
        matched_at: datetime,
        symbol: str,
        volume: float,
        price: float,
        pct_commission: float,
        expect_value_with_commission,
    ):
        t = SETTrade(
            matched_at=matched_at,
            symbol=symbol,
            volume=volume,
            price=price,
            pct_commission=pct_commission,
        )

        result = t.value_with_commission

        # Check
        assert result == expect_value_with_commission
