from datetime import date, timedelta
from decimal import Decimal
from discount_engine.models import Product, CartItem, Customer, Order
from discount_engine.factory import DiscountFactory
from discount_engine.engine import PricingEngine

def main():
    book = Product("1", "Война и мир", Decimal("1000"), "Книги")
    pen = Product("2", "Ручка", Decimal("100"), "Канцелярия")

    customer = Customer(
        id="c1",
        lastPurchaseDate=date.today() - timedelta(days=10),
        isFirstOrder=False,
    )

    order = Order(
        id="o1",
        customer=customer,
        items=[
            CartItem(book, 3),
            CartItem(pen, 5),
        ],
        promoCodes=["SALE10"],
        createdAt=date.today(),
        deliveryCost=Decimal("300"),
    )

    configs = [
        {"type": "threeForTwo", "category": "Книги", "name": "3 по цене 2"},
        {"type": "percent", "value": 10, "name": "Осенняя распродажа"},
        {"type": "loyalty", "percent": 5, "days": 30, "name": "Лояльность"},
        {"type": "promoCode", "code": "SALE10", "kind": "percent",
         "value": 10, "name": "Промокод SALE10"},
        {"type": "freeDelivery", "threshold": 3000, "name": "Бесплатная доставка"},
    ]

    strategies = [DiscountFactory.create(cfg) for cfg in configs]
    engine = PricingEngine(strategies)
    result = engine.calculate(order)

    print(f"baseTotal: {result.baseTotal}")
    for d in result.appliedDiscounts:
        print(f"  - {d.name}: {d.amount} ({d.reason})")
    print(f"finalTotal: {result.finalTotal}")

if __name__ == "__main__":
    main()