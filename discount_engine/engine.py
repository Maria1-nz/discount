from decimal import Decimal
from typing import List
from .models import DiscountContext, PricingResult
from .discounts import Discount, PromoCodeDiscount, PercentDiscount, round_money

class PricingEngine:
    def __init__(self, strategies: List[Discount]):
        self.strategies = strategies

    def _apply_stage(self, ctx: DiscountContext, stage: str):
        for s in self.strategies:
            if s.stage == stage:
                s.apply(ctx)

    def _resolve_percent_conflict(self, ctx: DiscountContext):
        ordinary = [
            s for s in self.strategies
            if s.stage == "percent" and isinstance(s, PercentDiscount)
        ]
        promo = [
            s for s in self.strategies
            if s.stage == "percent" and isinstance(s, PromoCodeDiscount)
        ]

        if not (ordinary and promo):
            return None

        best_amount = Decimal("-1")
        winner = None
        for s in ordinary:
            amt = round_money(ctx.itemsTotal * s.percent / Decimal("100"))
            if amt > best_amount:
                best_amount, winner = amt, s
        for s in promo:
            if s.is_valid(ctx):
                amt = s.potential_amount(ctx)
                if amt >= best_amount:
                    best_amount, winner = amt, s
        return winner

    def calculate(self, order) -> PricingResult:
        items_sum = sum((item.total for item in order.items), Decimal("0"))
        base_total = round_money(items_sum + order.deliveryCost)

        ctx = DiscountContext(
            order=order,
            itemsTotal=items_sum,
            deliveryCost=order.deliveryCost,
        )

        conflict_winner = self._resolve_percent_conflict(ctx)

        self._apply_stage(ctx, "threeForTwo")

        for s in self.strategies:
            if s.stage != "percent":
                continue
            if conflict_winner is None:
                s.apply(ctx)
            elif s is conflict_winner:
                s.apply(ctx)

        self._apply_stage(ctx, "fixed")
        self._apply_stage(ctx, "freeDelivery")
        final_total = round_money(ctx.itemsTotal + ctx.deliveryCost)

        return PricingResult(
            baseTotal=base_total,
            appliedDiscounts=ctx.appliedDiscounts,
            finalTotal=final_total,
        )