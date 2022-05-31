from datetime import datetime

import pytest

from ezyquant.backtest.trade import Trade


class TestTrade:
    @pytest.mark.parametrize("timestamp", [datetime(2000, 1, 1)])
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
        timestamp: datetime,
        symbol: str,
        volume: float,
        price: float,
        pct_commission: float,
        expect_value_with_commission,
    ):
        t = Trade(
            timestamp=timestamp,
            symbol=symbol,
            volume=volume,
            price=price,
            pct_commission=pct_commission,
        )

        result = t.value_with_commission

        # Check
        assert result == expect_value_with_commission
