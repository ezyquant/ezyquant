from datetime import datetime
from typing import Dict

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from ezyquant.backtest.portfolio import Portfolio
from ezyquant.backtest.position import Position


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
