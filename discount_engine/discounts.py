from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional
from .models import AppliedDiscount, DiscountContext

def round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

class Discount(ABC):
    stage: str = "percent"

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        pass

class PercentDiscount(Discount):
    stage = "percent"

    def __init__(self, name: str, percent: Decimal):
        super().__init__(name)
        self.percent = Decimal(percent)

    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        if ctx.itemsTotal <= 0:
            return None
        amount = round_money(ctx.itemsTotal * self.percent / Decimal("100"))
        if amount <= 0:
            return None
        ctx.itemsTotal -= amount
        d = AppliedDiscount(
            name=self.name,
            amount=amount,
            reason=f"Скидка {self.percent}% на сумму товаров",
        )
        ctx.add_discount(d)
        return d

class FixedDiscount(Discount):
    stage = "fixed"

    def __init__(self, name: str, value: Decimal, threshold: Decimal):
        super().__init__(name)
        self.value = Decimal(value)
        self.threshold = Decimal(threshold)

    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        if ctx.itemsTotal < self.threshold:
            return None
        amount = min(self.value, ctx.itemsTotal)
        amount = round_money(amount)
        if amount <= 0:
            return None
        ctx.itemsTotal -= amount
        d = AppliedDiscount(
            name=self.name,
            amount=amount,
            reason=f"Фиксированная скидка {self.value} при сумме от {self.threshold}",
        )
        ctx.add_discount(d)
        return d

class ThreeForTwoDiscount(Discount):
    stage = "threeForTwo"

    def __init__(self, name: str, category: str):
        super().__init__(name)
        self.category = category

    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        units = []
        for item in ctx.order.items:
            if item.product.category == self.category:
                units.extend([item.product.basePrice] * item.quantity)

        if len(units) < 3:
            return None

        units.sort()
        free_count = len(units) // 3
        free_units = units[:free_count]
        amount = round_money(sum(free_units))
        if amount <= 0:
            return None

        ctx.itemsTotal -= amount
        d = AppliedDiscount(
            name=self.name,
            amount=amount,
            reason=f"Категория {self.category}: {len(units)} единиц, {free_count} бесплатно",
        )
        ctx.add_discount(d)
        return d

class PromoCodeDiscount(Discount):
    def __init__(self, name: str, code: str, kind: str,
                 value: Decimal, expires: Optional[date] = None):
        super().__init__(name)
        self.code = code
        self.kind = kind
        self.value = Decimal(value)
        self.expires = expires
        self.stage = "percent" if kind == "percent" else "fixed"

    def is_valid(self, ctx: DiscountContext) -> bool:
        if ctx.promo_already_used(self.code):
            return False
        if self.code not in ctx.order.promoCodes:
            return False
        if self.expires is not None and ctx.order.createdAt > self.expires:
            return False
        return True

    def potential_amount(self, ctx: DiscountContext) -> Decimal:
        if self.kind == "percent":
            return round_money(ctx.itemsTotal * self.value / Decimal("100"))
        return round_money(min(self.value, ctx.itemsTotal))

    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        if not self.is_valid(ctx):
            return None
        amount = self.potential_amount(ctx)
        if amount <= 0:
            return None
        ctx.itemsTotal -= amount
        ctx.acceptedPromoCodes.append(self.code)
        d = AppliedDiscount(
            name=self.name,
            amount=amount,
            reason=f"Промокод {self.code}",
        )
        ctx.add_discount(d)
        return d

class LoyaltyDiscount(Discount):
    stage = "percent"

    def __init__(self, name: str, percent: Decimal, days: int):
        super().__init__(name)
        self.percent = Decimal(percent)
        self.days = days

    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        last = ctx.order.customer.lastPurchaseDate
        if last is None:
            return None
        if last > ctx.order.createdAt:
            return None
        delta = (ctx.order.createdAt - last).days
        if delta > self.days:
            return None
        amount = round_money(ctx.itemsTotal * self.percent / Decimal("100"))
        if amount <= 0:
            return None
        ctx.itemsTotal -= amount
        d = AppliedDiscount(
            name=self.name,
            amount=amount,
            reason=f"Последняя покупка была {delta} дней назад",
        )
        ctx.add_discount(d)
        return d

class FreeDeliveryDiscount(Discount):
    stage = "freeDelivery"

    def __init__(self, name: str, threshold: Decimal):
        super().__init__(name)
        self.threshold = Decimal(threshold)

    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        if ctx.itemsTotal <= self.threshold:
            return None
        if ctx.deliveryCost <= 0:
            return None
        amount = round_money(ctx.deliveryCost)
        ctx.deliveryCost = Decimal("0")
        d = AppliedDiscount(
            name=self.name,
            amount=amount,
            reason=f"Бесплатная доставка при сумме строго больше {self.threshold}",
        )
        ctx.add_discount(d)
        return d

class FirstOrderDiscount(Discount):
    stage = "percent"

    def __init__(self, name: str, percent: Decimal = Decimal("10")):
        super().__init__(name)
        self.percent = Decimal(percent)

    def apply(self, ctx: DiscountContext) -> Optional[AppliedDiscount]:
        if not ctx.order.customer.isFirstOrder:
            return None
        amount = round_money(ctx.itemsTotal * self.percent / Decimal("100"))
        if amount <= 0:
            return None
        ctx.itemsTotal -= amount
        d = AppliedDiscount(
            name=self.name,
            amount=amount,
            reason="Скидка за первый заказ",
        )
        ctx.add_discount(d)
        return d