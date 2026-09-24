from datetime import date, timedelta
from decimal import Decimal
from discount_engine.models import Product, CartItem, Customer, Order
from discount_engine.factory import DiscountFactory
from discount_engine.engine import PricingEngine

def make_order(items, customer=None, promos=None, delivery="0"):
    if customer is None:
        customer = Customer("c1", None, False)
    return Order(
        id="o1",
        customer=customer,
        items=items,
        promoCodes=promos or [],
        createdAt=date.today(),
        deliveryCost=Decimal(delivery),
    )

def test_three_for_two_then_percent():
    p = Product("1", "Книга", Decimal("100"), "Книги")
    order = make_order([CartItem(p, 3)])
    strategies = [
        DiscountFactory.create({"type": "threeForTwo", "category": "Книги",
                                "name": "3x2"}),
        DiscountFactory.create({"type": "percent", "value": 10,
                                "name": "10%"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.baseTotal == Decimal("300.00")
    assert result.finalTotal == Decimal("180.00")
    assert [d.name for d in result.appliedDiscounts] == ["3x2", "10%"]

def test_fixed_does_not_go_below_zero():
    p = Product("1", "X", Decimal("100"), "К")
    order = make_order([CartItem(p, 1)])
    strategies = [
        DiscountFactory.create({"type": "fixed", "value": 500,
                                "threshold": 50, "name": "500"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.finalTotal == Decimal("0.00")

def test_promo_percent_vs_ordinary_percent_picks_bigger():
    p = Product("1", "X", Decimal("1000"), "К")
    order = make_order([CartItem(p, 1)], promos=["BIG"])
    strategies = [
        DiscountFactory.create({"type": "percent", "value": 5,
                                "name": "Обычная"}),
        DiscountFactory.create({"type": "promoCode", "code": "BIG",
                                "kind": "percent", "value": 20,
                                "name": "Промокод"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.finalTotal == Decimal("800.00")
    assert result.appliedDiscounts[0].name == "Промокод"

def test_promo_percent_vs_ordinary_percent_tie_goes_to_promo():
    p = Product("1", "X", Decimal("1000"), "К")
    order = make_order([CartItem(p, 1)], promos=["SALE"])
    strategies = [
        DiscountFactory.create({"type": "percent", "value": 10,
                                "name": "Обычная"}),
        DiscountFactory.create({"type": "promoCode", "code": "SALE",
                                "kind": "percent", "value": 10,
                                "name": "Промокод"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.finalTotal == Decimal("900.00")
    assert result.appliedDiscounts[0].name == "Промокод"

def test_loyalty_combines_with_promo_percent():
    p = Product("1", "X", Decimal("1000"), "К")
    cust = Customer("c1", date.today() - timedelta(days=10), False)
    order = make_order([CartItem(p, 1)], customer=cust, promos=["SALE"])
    strategies = [
        DiscountFactory.create({"type": "promoCode", "code": "SALE",
                                "kind": "percent", "value": 10,
                                "name": "Промокод"}),
        DiscountFactory.create({"type": "loyalty", "percent": 5,
                                "days": 30, "name": "Лояльность"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.finalTotal == Decimal("855.00")
    assert len(result.appliedDiscounts) == 2


def test_free_delivery_after_discounts():
    p = Product("1", "X", Decimal("1000"), "К")
    order = make_order([CartItem(p, 5)], delivery="300")
    strategies = [
        DiscountFactory.create({"type": "percent", "value": 10,
                                "name": "10%"}),
        DiscountFactory.create({"type": "freeDelivery", "threshold": 4000,
                                "name": "Доставка"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.finalTotal == Decimal("4500.00")
    assert any(d.name == "Доставка" for d in result.appliedDiscounts)

def test_empty_cart():
    order = make_order([])
    strategies = [
        DiscountFactory.create({"type": "percent", "value": 10,
                                "name": "10%"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.baseTotal == Decimal("0.00")
    assert result.finalTotal == Decimal("0.00")
    assert result.appliedDiscounts == []

def test_round_half_to_even():
    p = Product("1", "X", Decimal("0.05"), "К")
    order = make_order([CartItem(p, 1)])
    strategies = [
        DiscountFactory.create({"type": "percent", "value": 10,
                                "name": "10%"}),
    ]
    result = PricingEngine(strategies).calculate(order)

    assert result.finalTotal == Decimal("0.05")
    assert result.appliedDiscounts == []

def test_three_for_two_multiple_prices_in_category():
    p1 = Product("1", "Дешёвая", Decimal("100"), "Книги")
    p2 = Product("2", "Дорогая", Decimal("500"), "Книги")
    order = make_order([CartItem(p1, 2), CartItem(p2, 2)])
    strategies = [
        DiscountFactory.create({"type": "threeForTwo", "category": "Книги",
                                "name": "3x2"}),
    ]
    result = PricingEngine(strategies).calculate(order)
    assert result.finalTotal == Decimal("1100.00")
    assert result.appliedDiscounts[0].amount == Decimal("100.00")