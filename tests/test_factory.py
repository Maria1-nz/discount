from decimal import Decimal
from datetime import date
import pytest
from discount_engine.factory import DiscountFactory
from discount_engine.discounts import (
    PercentDiscount,
    FixedDiscount,
    ThreeForTwoDiscount,
    PromoCodeDiscount,
    LoyaltyDiscount,
    FreeDeliveryDiscount,
    FirstOrderDiscount,
)

def test_create_percent():
    d = DiscountFactory.create({"type": "percent", "value": 10, "name": "Осень"})
    assert isinstance(d, PercentDiscount)
    assert d.name == "Осень"
    assert d.percent == Decimal("10")

def test_create_fixed():
    d = DiscountFactory.create({
        "type": "fixed", "value": 500, "threshold": 3000, "name": "500 от 3000",
    })
    assert isinstance(d, FixedDiscount)
    assert d.value == Decimal("500")
    assert d.threshold == Decimal("3000")

def test_create_three_for_two():
    d = DiscountFactory.create({
        "type": "threeForTwo", "category": "Книги", "name": "3 по цене 2",
    })
    assert isinstance(d, ThreeForTwoDiscount)
    assert d.category == "Книги"

def test_create_promo_code():
    d = DiscountFactory.create({
        "type": "promoCode", "code": "SALE10", "kind": "percent",
        "value": 10, "name": "Промокод",
    })
    assert isinstance(d, PromoCodeDiscount)
    assert d.code == "SALE10"
    assert d.stage == "percent"

def test_create_promo_code_with_expires():
    d = DiscountFactory.create({
        "type": "promoCode", "code": "SALE10", "kind": "percent",
        "value": 10, "name": "Промокод", "expires": "2025-12-31",
    })
    assert d.expires == date(2025, 12, 31)

def test_create_loyalty():
    d = DiscountFactory.create({
        "type": "loyalty", "percent": 5, "days": 30, "name": "Лояльность",
    })
    assert isinstance(d, LoyaltyDiscount)
    assert d.percent == Decimal("5")
    assert d.days == 30

def test_create_free_delivery():
    d = DiscountFactory.create({
        "type": "freeDelivery", "threshold": 5000, "name": "Бесплатная доставка",
    })
    assert isinstance(d, FreeDeliveryDiscount)
    assert d.threshold == Decimal("5000")

def test_create_first_order():
    d = DiscountFactory.create({"type": "firstOrder", "name": "Первый заказ"})
    assert isinstance(d, FirstOrderDiscount)
    assert d.percent == Decimal("10")

def test_unknown_type_raises():
    with pytest.raises(ValueError):
        DiscountFactory.create({"type": "unknown", "name": "X"})