import copy
from typing import Dict

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from ezyquant.backtest import Portfolio, Position, Trade


@pytest.mark.parametrize(
    ("cash", "position_dict", "expect_port_value"),
    [
        (0.0, {}, 0.0),
        (0.0, {"A": Position(symbol="A", volume=100, market_price=1.0)}, 100.0),
        (
            0.0,
            {
                "A": Position(symbol="A", volume=100, market_price=1.0),
                "B": Position(symbol="B", volume=200, market_price=2.0),
            },
            500.0,
        ),
        (100.0, {}, 100.0),
        (100.0, {"A": Position(symbol="A", volume=100, market_price=1.0)}, 200.0),
        (
            100.0,
            {
                "A": Position(symbol="A", volume=100, market_price=1.0),
                "B": Position(symbol="B", volume=200, market_price=2.0),
            },
            600.0,
        ),
    ],
)
def test_port_value(
    cash: float, position_dict: Dict[str, Position], expect_port_value: float
):
    # Mock
    pf = Portfolio(cash=cash, position_dict=position_dict)

    # Test
    result = pf.port_value

    # Check
    assert result == expect_port_value


class TestSetPositionMarketPrice:
    @pytest.mark.parametrize("price_series", [pd.Series({"A": 1.0, "B": 2.0})])
    @pytest.mark.parametrize(
        ("cash", "position_dict", "expect_port_value"),
        [
            (0.0, {}, 0.0),
            (0.0, {"A": Position(symbol="A", volume=100, market_price=0.0)}, 100.0),
            (
                0.0,
                {
                    "A": Position(symbol="A", volume=100, market_price=0.0),
                    "B": Position(symbol="B", volume=200, market_price=0.0),
                },
                500.0,
            ),
            (100.0, {}, 100.0),
            (100.0, {"A": Position(symbol="A", volume=100, market_price=0.0)}, 200.0),
            (
                100.0,
                {
                    "A": Position(symbol="A", volume=100, market_price=0.0),
                    "B": Position(symbol="B", volume=200, market_price=0.0),
                },
                600.0,
            ),
        ],
    )
    def test_success(
        self,
        price_series: pd.Series,
        cash: float,
        position_dict: Dict[str, Position],
        expect_port_value: float,
    ):
        # Mock
        pf = Portfolio(cash=cash, position_dict=position_dict)

        # Test
        pf.set_position_market_price(price_series)
        result = pf.port_value

        # Check
        assert result == expect_port_value

    @pytest.mark.parametrize(
        "price_series", [pd.Series(dtype="float64"), pd.Series({"B": 2.0})]
    )
    @pytest.mark.parametrize("cash", [0.0, 100.0])
    @pytest.mark.parametrize(
        "position_dict",
        [
            {"A": Position(symbol="A", volume=100, market_price=0.0)},
            {
                "A": Position(symbol="A", volume=100, market_price=0.0),
                "B": Position(symbol="B", volume=200, market_price=0.0),
            },
        ],
    )
    def test_error(
        self, price_series: pd.Series, cash: float, position_dict: Dict[str, Position]
    ):
        # Mock
        pf = Portfolio(cash=cash, position_dict=position_dict)

        # Test
        with pytest.raises(KeyError) as e:
            pf.set_position_market_price(price_series)
            assert e.value == "A"


@pytest.mark.parametrize(
    ("position_dict", "expected_volume_series"),
    [
        ({}, pd.Series(dtype="float64")),
        (
            {"A": Position(symbol="A", volume=100, market_price=1.0)},
            pd.Series({"A": 100.0}),
        ),
        (
            {
                "A": Position(symbol="A", volume=100, market_price=1.0),
                "B": Position(symbol="B", volume=200, market_price=2.0),
            },
            pd.Series({"A": 100.0, "B": 200.0}),
        ),
    ],
)
def test_volume_series(
    position_dict: Dict[str, Position], expected_volume_series: pd.Series
):
    # Mock
    pf = Portfolio(cash=0.0, position_dict=position_dict)

    # Test
    result = pf.volume_series

    # Check
    assert_series_equal(result, expected_volume_series)


class TestPlaceOrderBuy:
    @pytest.mark.parametrize(
        ("cash", "pct_commission", "expect_cash"),
        [(100.0, 0.0, 0.0), (200.0, 0.0, 100.0), (110.0, 0.1, 0.0)],
    )
    @pytest.mark.parametrize(
        ("position_dict", "expect_position_dict"),
        [
            (
                {},
                {"A": Position(symbol="A", volume=100.0, cost_price=1.0)},
            ),
            (
                {"A": Position(symbol="A", volume=100.0, cost_price=2.0)},
                {"A": Position(symbol="A", volume=200.0, cost_price=1.5)},
            ),
            (
                {"B": Position(symbol="B", volume=200.0, cost_price=2.0)},
                {
                    "A": Position(symbol="A", volume=100.0, cost_price=1.0),
                    "B": Position(symbol="B", volume=200.0, cost_price=2.0),
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
        timestamp = pd.Timestamp("2000-01-01")
        position_dict = copy.deepcopy(position_dict)

        # Mock
        expect_trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            volume=volume,
            price=price,
            pct_commission=pct_commission,
        )

        pf = Portfolio(
            cash=cash,
            pct_commission=pct_commission,
            position_dict=position_dict,
        )

        # Test
        result = pf.place_order(
            symbol=symbol,
            volume=volume,
            price=price,
            timestamp=timestamp,
        )

        # Check
        assert result == expect_trade
        assert pf.cash == expect_cash
        assert pf.position_dict == expect_position_dict

    @pytest.mark.parametrize(("cash", "pct_commission"), [(99.0, 0.0), (109.0, 0.1)])
    def test_error_insufficient_cash(self, cash: float, pct_commission: float):
        symbol = "A"
        volume = 100.0
        price = 1.0
        timestamp = pd.Timestamp("2000-01-01")

        # Mock
        pf = Portfolio(cash=cash, pct_commission=pct_commission)

        # Test
        with pytest.raises(ValueError) as e:
            pf.place_order(
                symbol=symbol,
                volume=volume,
                price=price,
                timestamp=timestamp,
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
        timestamp = pd.Timestamp("2000-01-01")

        # Mock
        pf = Portfolio(cash=1e6)

        # Test
        with pytest.raises(AssertionError) as e:
            pf.place_order(
                symbol=symbol,
                volume=volume,
                price=price,
                timestamp=timestamp,
            )
        assert "volume" in e.value.args[0]
