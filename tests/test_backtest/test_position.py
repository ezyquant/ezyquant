import pytest

from ezyquant.backtesting import SETPosition


class TestCostPrice:
    @pytest.mark.parametrize(
        ("volume1", "price1", "volume2", "price2", "expect_cost_price"),
        [
            (0, 0.0, 100, 2.0, 2.0),
            (0, 1.0, 100, 2.0, 2.0),
            (100, 1.0, 100, 2.0, 1.5),
            (100, 1.0, 200, 2.0, 5 / 3),
        ],
    )
    def test_buy(
        self,
        volume1: float,
        price1: float,
        volume2: float,
        price2: float,
        expect_cost_price: float,
    ):
        p1 = SETPosition(symbol="A", volume=volume1, cost_price=price1)
        result1 = p1.match_order(volume=volume2, price=price2)

        p2 = SETPosition(symbol="A", volume=volume2, cost_price=price2)
        result2 = p2.match_order(volume=volume1, price=price1)

        assert result1 == result2 == volume1 + volume2
        assert p1.cost_price == p2.cost_price == expect_cost_price

    @pytest.mark.parametrize("volume1", [0.0, 100.0])
    @pytest.mark.parametrize("volume2", [100.0, 200.0])
    @pytest.mark.parametrize("price", [1.0, 2.0])
    def test_buy_same_price(
        self,
        volume1: float,
        volume2: float,
        price: float,
    ):
        p = SETPosition(symbol="A", volume=volume1, cost_price=price)

        result = p.match_order(volume=volume2, price=price)

        assert result == volume1 + volume2
        assert p.cost_price == price

    @pytest.mark.parametrize("volume1", [200.0, 300.0])
    @pytest.mark.parametrize("price1", [1.0, 2.0])
    @pytest.mark.parametrize("volume2", [-100.0, -200.0])
    @pytest.mark.parametrize("price2", [1.0, 2.0])
    def test_sell(
        self,
        volume1: float,
        price1: float,
        volume2: float,
        price2: float,
    ):
        p = SETPosition(symbol="A", volume=volume1, cost_price=price1)

        result = p.match_order(volume=volume2, price=price2)

        assert result == volume1 + volume2
        assert p.cost_price == price1
