import copy
from typing import Dict

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from ezyquant.backtest import Position, SETAccount, Trade

nan = float("nan")


@pytest.mark.parametrize(
    ("position_dict", "market_price_dict", "expect_result"),
    [
        ({}, {}, 0.0),
        ({}, {"A": 0.0}, 0.0),
        ({}, {"A": 1.0}, 0.0),
        ({"A": Position("A", 100.0)}, {"A": 0.0}, 0.0),
        ({"A": Position("A", 100.0)}, {"A": 1.0}, 100.0),
    ],
)
def test_total_market_value(
    position_dict: Dict[str, Position],
    market_price_dict: Dict[str, float],
    expect_result: float,
):
    # Mock
    acct = SETAccount(
        cash=0.0, position_dict=position_dict, market_price_dict=market_price_dict
    )

    # Test
    result = acct.total_market_value

    # Check
    assert result == expect_result


class TestMatchOrderBuy:
    @pytest.mark.parametrize(
        ("cash", "pct_commission", "expect_cash"),
        [(100.0, 0.0, 0.0), (200.0, 0.0, 100.0), (110.0, 0.1, 0.0)],
    )
    @pytest.mark.parametrize(
        ("position_dict", "expect_position_dict"),
        [
            (
                {},
                {"A": Position(symbol="A", volume=100.0, avg_cost_price=1.0)},
            ),
            (
                {"A": Position(symbol="A", volume=100.0, avg_cost_price=2.0)},
                {"A": Position(symbol="A", volume=200.0, avg_cost_price=1.5)},
            ),
            (
                {"B": Position(symbol="B", volume=200.0, avg_cost_price=2.0)},
                {
                    "A": Position(symbol="A", volume=100.0, avg_cost_price=1.0),
                    "B": Position(symbol="B", volume=200.0, avg_cost_price=2.0),
                },
            ),
        ],
    )
    def test_success(
        self,
        cash: float,
        pct_commission: float,
        position_dict: Dict[str, Position],
        expect_cash: float,
        expect_position_dict: Dict[str, Position],
    ):
        symbol = "A"
        volume = 100.0
        price = 1.0
        matched_at = pd.Timestamp("2000-01-01")
        position_dict = copy.deepcopy(position_dict)

        # Mock
        expect_trade = Trade(
            matched_at=matched_at,
            symbol=symbol,
            volume=volume,
            price=price,
            pct_commission=pct_commission,
        )

        acct = SETAccount(
            cash=cash,
            pct_commission=pct_commission,
            position_dict=position_dict,
        )

        # Test
        result = acct._match_order(
            symbol=symbol,
            volume=volume,
            price=price,
            matched_at=matched_at,
        )

        # Check
        assert result == expect_trade
        assert acct.cash == expect_cash
        assert acct.position_dict == expect_position_dict

    @pytest.mark.parametrize(("cash", "pct_commission"), [(99.0, 0.0), (109.0, 0.1)])
    def test_error_insufficient_cash(self, cash: float, pct_commission: float):
        symbol = "A"
        volume = 100.0
        price = 1.0
        matched_at = pd.Timestamp("2000-01-01")

        # Mock
        acct = SETAccount(cash=cash, pct_commission=pct_commission)

        # Test
        with pytest.raises(ValueError) as e:
            acct._match_order(
                symbol=symbol,
                volume=volume,
                price=price,
                matched_at=matched_at,
            )
        assert e.value.args[0] == "Insufficient cash"

    @pytest.mark.parametrize(
        "volume",
        [
            0.0,
            0.1,
            -0.1,
            1.0,
            -1.0,
            99.0,
            -99.0,
            101.0,
            -101.0,
            float("nan"),
            float("inf"),
            -float("inf"),
        ],
    )
    def test_error_volume(self, volume: float):
        symbol = "A"
        price = 1.0
        matched_at = pd.Timestamp("2000-01-01")

        # Mock
        acct = SETAccount(cash=1e6)

        # Test
        with pytest.raises(AssertionError) as e:
            acct._match_order(
                symbol=symbol,
                volume=volume,
                price=price,
                matched_at=matched_at,
            )
        assert "volume" in e.value.args[0]


class TestMatchOrderSell:
    @pytest.mark.parametrize(
        ("cash", "pct_commission", "expect_cash"),
        [(0.0, 0.0, 100.0), (100.0, 0.0, 200.0), (0.0, 0.1, 90.0)],
    )
    @pytest.mark.parametrize(
        ("position_dict", "expect_position_dict"),
        [
            (
                {"A": Position(symbol="A", volume=100.0, avg_cost_price=1.0)},
                {},
            ),
            (
                {"A": Position(symbol="A", volume=200.0, avg_cost_price=1.5)},
                {"A": Position(symbol="A", volume=100.0, avg_cost_price=1.5)},
            ),
            (
                {
                    "A": Position(symbol="A", volume=100.0, avg_cost_price=1.0),
                    "B": Position(symbol="B", volume=200.0, avg_cost_price=2.0),
                },
                {"B": Position(symbol="B", volume=200.0, avg_cost_price=2.0)},
            ),
        ],
    )
    def test_success(
        self,
        cash: float,
        pct_commission: float,
        position_dict: Dict[str, Position],
        expect_cash: float,
        expect_position_dict: Dict[str, Position],
    ):
        symbol = "A"
        volume = -100.0
        price = 1.0
        matched_at = pd.Timestamp("2000-01-01")
        position_dict = copy.deepcopy(position_dict)

        # Mock
        expect_trade = Trade(
            matched_at=matched_at,
            symbol=symbol,
            volume=volume,
            price=price,
            pct_commission=pct_commission,
        )

        acct = SETAccount(
            cash=cash,
            pct_commission=pct_commission,
            position_dict=position_dict,
        )

        # Test
        result = acct._match_order(
            symbol=symbol,
            volume=volume,
            price=price,
            matched_at=matched_at,
        )

        # Check
        assert result == expect_trade
        assert acct.cash == expect_cash
        assert acct.position_dict == expect_position_dict

    @pytest.mark.parametrize(
        "position_dict",
        [
            {},
            {"A": Position(symbol="A", volume=100.0, avg_cost_price=1.0)},
            {"B": Position(symbol="B", volume=200.0, avg_cost_price=1.0)},
        ],
    )
    def test_error_insufficient_position(self, position_dict: Dict[str, Position]):
        symbol = "A"
        volume = -200.0
        price = 1.0
        matched_at = pd.Timestamp("2000-01-01")

        # Mock
        acct = SETAccount(
            cash=0.0,
            pct_commission=0.0,
            position_dict=position_dict,
        )

        # Test
        with pytest.raises(ValueError) as e:
            acct._match_order(
                symbol=symbol,
                volume=volume,
                price=price,
                matched_at=matched_at,
            )
        assert e.value.args[0] == "Insufficient volume"
