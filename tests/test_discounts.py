from datetime import date, timedelta
from decimal import Decimal
from discount_engine.models import (
    Product,
    CartItem,
    Customer,
    Order,
    DiscountContext,
)
from discount_engine.discounts import (
    PercentDiscount,
    FixedDiscount,
    ThreeForTwoDiscount,
    LoyaltyDiscount,
    FreeDeliveryDiscount,
    FirstOrderDiscount,
    PromoCodeDiscount,
)

def make_ctx(items_sum="1000", delivery="100", is_first=False,
             last_days_ago=None, promos=None):
    p = Product("1", "X", Decimal("100"), "Кат")
    last = None
    if last_days_ago is not None:
        last = date.today() - timedelta(days=last_days_ago)
    cust = Customer("c1", last, is_first)
    order = Order(
        id="o1",
        customer=cust,
        items=[CartItem(p, 1)],
        promoCodes=promos or [],
        createdAt=date.today(),
        deliveryCost=Decimal(delivery),
    )
    return DiscountContext(
        order=order,
        itemsTotal=Decimal(items_sum),
        deliveryCost=Decimal(delivery),
    )

def test_percent_applies():
    ctx = make_ctx(items_sum="1000")
    d = PercentDiscount("10%", Decimal("10"))
    res = d.apply(ctx)
    assert res is not None
    assert res.amount == Decimal("100.00")
    assert ctx.itemsTotal == Decimal("900")

def test_percent_not_applied_on_zero():
    ctx = make_ctx(items_sum="0")
    d = PercentDiscount("10%", Decimal("10"))
    assert d.apply(ctx) is None

def test_fixed_below_threshold_not_applied():
    ctx = make_ctx(items_sum="2000")
    d = FixedDiscount("500", Decimal("500"), Decimal("3000"))
    assert d.apply(ctx) is None

def test_fixed_caps_at_items_total():
    ctx = make_ctx(items_sum="100")
    d = FixedDiscount("500", Decimal("500"), Decimal("50"))
    res = d.apply(ctx)
    assert res.amount == Decimal("100.00")
    assert ctx.itemsTotal == Decimal("0")

def test_three_for_two_two_units_no_discount():
    p = Product("1", "Книга", Decimal("100"), "Книги")
    cust = Customer("c1", None, False)
    order = Order("o1", cust, [CartItem(p, 2)], createdAt=date.today(),
                  deliveryCost=Decimal("0"))
    ctx = DiscountContext(order=order, itemsTotal=Decimal("200"),
                          deliveryCost=Decimal("0"))
    d = ThreeForTwoDiscount("3x2", "Книги")
    assert d.apply(ctx) is None

def test_three_for_two_free_cheapest():
    p1 = Product("1", "Дешёвая", Decimal("100"), "Книги")
    p2 = Product("2", "Дорогая", Decimal("500"), "Книги")
    cust = Customer("c1", None, False)
    order = Order("o1", cust, [CartItem(p1, 2), CartItem(p2, 1)],
                  createdAt=date.today(), deliveryCost=Decimal("0"))
    ctx = DiscountContext(order=order, itemsTotal=Decimal("700"),
                          deliveryCost=Decimal("0"))
    d = ThreeForTwoDiscount("3x2", "Книги")
    res = d.apply(ctx)
    assert res.amount == Decimal("100.00")

def test_loyalty_exactly_30_days():
    ctx = make_ctx(items_sum="1000", last_days_ago=30)
    d = LoyaltyDiscount("Лояльность", Decimal("5"), 30)
    res = d.apply(ctx)
    assert res is not None
    assert res.amount == Decimal("50.00")

def test_loyalty_31_days_no_discount():
    ctx = make_ctx(items_sum="1000", last_days_ago=31)
    d = LoyaltyDiscount("Лояльность", Decimal("5"), 30)
    assert d.apply(ctx) is None

def test_loyalty_future_date_no_discount():
    p = Product("1", "X", Decimal("100"), "К")
    cust = Customer("c1", date.today() + timedelta(days=5), False)
    order = Order("o1", cust, [CartItem(p, 10)], createdAt=date.today(),
                  deliveryCost=Decimal("0"))
    ctx = DiscountContext(order=order, itemsTotal=Decimal("1000"),
                          deliveryCost=Decimal("0"))
    d = LoyaltyDiscount("Л", Decimal("5"), 30)
    assert d.apply(ctx) is None

def test_free_delivery_strictly_greater():
    ctx = make_ctx(items_sum="5000", delivery="200")
    d = FreeDeliveryDiscount("Доставка", Decimal("5000"))
    assert d.apply(ctx) is None

def test_free_delivery_applies():
    ctx = make_ctx(items_sum="5001", delivery="200")
    d = FreeDeliveryDiscount("Доставка", Decimal("5000"))
    res = d.apply(ctx)
    assert res.amount == Decimal("200.00")
    assert ctx.deliveryCost == Decimal("0")

def test_first_order_applies():
    ctx = make_ctx(items_sum="1000", is_first=True)
    d = FirstOrderDiscount("Первый", Decimal("10"))
    res = d.apply(ctx)
    assert res.amount == Decimal("100.00")

def test_first_order_not_applied():
    ctx = make_ctx(items_sum="1000", is_first=False)
    d = FirstOrderDiscount("Первый", Decimal("10"))
    assert d.apply(ctx) is None

def test_promo_unknown_code_not_applied():
    ctx = make_ctx(items_sum="1000", promos=["OTHER"])
    d = PromoCodeDiscount("P", "SALE10", "percent", Decimal("10"))
    assert d.apply(ctx) is None

def test_promo_expired_not_applied():
    p = Product("1", "X", Decimal("100"), "К")
    cust = Customer("c1", None, False)
    order = Order("o1", cust, [CartItem(p, 10)], createdAt=date.today(),
                  promoCodes=["SALE10"], deliveryCost=Decimal("0"))
    ctx = DiscountContext(order=order, itemsTotal=Decimal("1000"),
                          deliveryCost=Decimal("0"))
    yesterday = date.today() - timedelta(days=1)
    d = PromoCodeDiscount("P", "SALE10", "percent", Decimal("10"),
                          expires=yesterday)
    assert d.apply(ctx) is None

def test_promo_applies_on_expiry_date():
    p = Product("1", "X", Decimal("100"), "К")
    cust = Customer("c1", None, False)
    order = Order("o1", cust, [CartItem(p, 10)], createdAt=date.today(),
                  promoCodes=["SALE10"], deliveryCost=Decimal("0"))
    ctx = DiscountContext(order=order, itemsTotal=Decimal("1000"),
                          deliveryCost=Decimal("0"))
    d = PromoCodeDiscount("P", "SALE10", "percent", Decimal("10"),
                          expires=date.today())
    assert d.apply(ctx) is not None