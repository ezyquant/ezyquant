import copy
from datetime import datetime
from typing import Dict

import pandas as pd
import pytest

from ezyquant.backtesting import SETAccount, SETPosition, SETTrade

nan = float("nan")


@pytest.mark.parametrize(
    ("position_dict", "market_price_dict", "expect_result"),
    [
        ({}, {}, 0.0),
        ({}, {"A": 0.0}, 0.0),
        ({}, {"A": 1.0}, 0.0),
        # ({"A": SETPosition("A", 100.0)}, {}, 100.0),
        ({"A": SETPosition("A", 100.0)}, {"A": nan}, 0.0),
        ({"A": SETPosition("A", 100.0)}, {"A": 0.0}, 0.0),
        ({"A": SETPosition("A", 100.0)}, {"A": 1.0}, 100.0),
    ],
)
def test_total_market_value(
    position_dict: Dict[str, SETPosition],
    market_price_dict: Dict[str, float],
    expect_result: float,
):
    # Mock
    acct = SETAccount(cash=0.0, position_dict=position_dict)
    acct.set_position_close_price(market_price_dict)

    # Test
    result = acct.total_market_value

    # Check
    assert result == expect_result


class TestMatchOrderIfPossible:
    @pytest.mark.parametrize(
        ("cash", "pct_commission", "expect_trade_volume_list"),
        [
            (200.0, 0.0, [200.0]),
            (220.0, 0.1, [200.0]),
            (200.0, 0.1, [100.0]),
            (99.0, 0.0, []),
            (0.0, 0.0, []),
        ],
    )
    def test_buy_with_enough_cash(
        self, cash: float, pct_commission: float, expect_trade_volume_list: list
    ):
        self._test(
            cash=cash,
            pct_commission=pct_commission,
            volume=200.0,
            price=1.0,
        )

        assert self.acct.trade_list == [
            SETTrade(
                matched_at=datetime(2000, 1, 1),
                symbol="A",
                volume=i,
                price=1.0,
                pct_commission=pct_commission,
            )
            for i in expect_trade_volume_list
        ]

    @pytest.mark.parametrize(
        ("position_volume", "expect_trade_volume_list"),
        [
            (200.0, [-200.0]),
            (100.0, [-100]),
            (0.0, []),
        ],
    )
    def test_sell_with_enough_volume(
        self, position_volume: float, expect_trade_volume_list: list
    ):
        self._test(
            position_dict={"A": SETPosition("A", position_volume)}
            if position_volume
            else {},
            volume=-200.0,
        )

        assert self.acct.trade_list == [
            SETTrade(
                matched_at=datetime(2000, 1, 1),
                symbol="A",
                volume=i,
                price=1.0,
                pct_commission=0.0,
            )
            for i in expect_trade_volume_list
        ]

    @pytest.mark.parametrize(
        ("volume", "expect_trade_volume_list"),
        [
            (100.01, [100.0]),
            (100.0, [100.0]),
            (99.99, []),
            (1.0, []),
            (0.01, []),
            (-0.01, []),
            (-1.0, []),
            (-99.99, []),
            (-100.0, [-100.0]),
            (-100.01, [-100.0]),
        ],
    )
    def test_round_volume(self, volume: float, expect_trade_volume_list: list):
        self._test(volume=volume)

        assert self.acct.trade_list == [
            SETTrade(
                matched_at=datetime(2000, 1, 1),
                symbol="A",
                volume=i,
                price=1.0,
                pct_commission=0.0,
            )
            for i in expect_trade_volume_list
        ]

    @pytest.mark.parametrize("price", [-1.0, -0.01, 0.0, nan])
    def test_invalid_price(self, price: float):
        self._test(price=price)
        assert self.acct.trade_list == []

    def _test(
        self,
        cash: float = 1000.0,
        pct_commission: float = 0.0,
        position_dict: Dict[str, SETPosition] = {"A": SETPosition("A", 1000.0)},
        matched_at: datetime = datetime(2000, 1, 1),
        symbol: str = "A",
        volume: float = 0.0,
        price: float = 1.0,
    ):
        self.acct = SETAccount(
            cash=cash,
            pct_commission=pct_commission,
            position_dict=position_dict.copy(),
        )

        self.acct.match_order_if_possible(
            matched_at=matched_at,
            symbol=symbol,
            volume=volume,
            price=price,
        )


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
                {"A": SETPosition(symbol="A", volume=100.0, cost_price=1.0)},
            ),
            (
                {"A": SETPosition(symbol="A", volume=100.0, cost_price=2.0)},
                {"A": SETPosition(symbol="A", volume=200.0, cost_price=1.5)},
            ),
            (
                {"B": SETPosition(symbol="B", volume=200.0, cost_price=2.0)},
                {
                    "A": SETPosition(symbol="A", volume=100.0, cost_price=1.0),
                    "B": SETPosition(symbol="B", volume=200.0, cost_price=2.0),
                },
            ),
        ],
    )
    def test_success(
        self,
        cash: float,
        pct_commission: float,
        position_dict: Dict[str, SETPosition],
        expect_cash: float,
        expect_position_dict: Dict[str, SETPosition],
    ):
        symbol = "A"
        volume = 100.0
        price = 1.0
        matched_at = pd.Timestamp("2000-01-01")
        position_dict = copy.deepcopy(position_dict)

        # Mock
        expect_trade = SETTrade(
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
        result = acct.match_order(
            symbol=symbol,
            volume=volume,
            price=price,
            matched_at=matched_at,
        )

        # Check
        assert result == expect_trade
        assert acct.trade_list[0] == expect_trade
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
            acct.match_order(
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
        with pytest.raises(ValueError) as e:
            acct.match_order(
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
                {"A": SETPosition(symbol="A", volume=100.0, cost_price=1.0)},
                {},
            ),
            (
                {"A": SETPosition(symbol="A", volume=200.0, cost_price=1.5)},
                {"A": SETPosition(symbol="A", volume=100.0, cost_price=1.5)},
            ),
            (
                {
                    "A": SETPosition(symbol="A", volume=100.0, cost_price=1.0),
                    "B": SETPosition(symbol="B", volume=200.0, cost_price=2.0),
                },
                {"B": SETPosition(symbol="B", volume=200.0, cost_price=2.0)},
            ),
        ],
    )
    def test_success(
        self,
        cash: float,
        pct_commission: float,
        position_dict: Dict[str, SETPosition],
        expect_cash: float,
        expect_position_dict: Dict[str, SETPosition],
    ):
        symbol = "A"
        volume = -100.0
        price = 1.0
        matched_at = pd.Timestamp("2000-01-01")
        position_dict = copy.deepcopy(position_dict)

        # Mock
        expect_trade = SETTrade(
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
        result = acct.match_order(
            symbol=symbol,
            volume=volume,
            price=price,
            matched_at=matched_at,
        )

        # Check
        assert result == expect_trade
        assert acct.trade_list[0] == expect_trade
        assert acct.cash == expect_cash
        assert acct.position_dict == expect_position_dict

    @pytest.mark.parametrize(
        "position_dict",
        [
            {},
            {"A": SETPosition(symbol="A", volume=100.0, cost_price=1.0)},
            {"B": SETPosition(symbol="B", volume=200.0, cost_price=1.0)},
        ],
    )
    def test_error_insufficient_position(self, position_dict: Dict[str, SETPosition]):
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
            acct.match_order(
                symbol=symbol,
                volume=volume,
                price=price,
                matched_at=matched_at,
            )
        assert e.value.args[0] == "Insufficient volume"
