from datetime import date
from decimal import Decimal
from .discounts import (
    PercentDiscount,
    FixedDiscount,
    ThreeForTwoDiscount,
    PromoCodeDiscount,
    LoyaltyDiscount,
    FreeDeliveryDiscount,
    FirstOrderDiscount,
)

class DiscountFactory:
    @staticmethod
    def create(config: dict):
        kind = config["type"]

        if kind == "percent":
            return PercentDiscount(
                name=config.get("name", "Процентная скидка"),
                percent=Decimal(str(config["value"])),
            )

        if kind == "fixed":
            return FixedDiscount(
                name=config.get("name", "Фиксированная скидка"),
                value=Decimal(str(config["value"])),
                threshold=Decimal(str(config["threshold"])),
            )

        if kind == "threeForTwo":
            return ThreeForTwoDiscount(
                name=config.get("name", "3 по цене 2"),
                category=config["category"],
            )

        if kind == "promoCode":
            expires = config.get("expires")
            if isinstance(expires, str):
                expires = date.fromisoformat(expires)
            return PromoCodeDiscount(
                name=config.get("name", "Промокод"),
                code=config["code"],
                kind=config["kind"],
                value=Decimal(str(config["value"])),
                expires=expires,
            )

        if kind == "loyalty":
            return LoyaltyDiscount(
                name=config.get("name", "Лояльность"),
                percent=Decimal(str(config["percent"])),
                days=int(config["days"]),
            )

        if kind == "freeDelivery":
            return FreeDeliveryDiscount(
                name=config.get("name", "Бесплатная доставка"),
                threshold=Decimal(str(config["threshold"])),
            )

        if kind == "firstOrder":
            return FirstOrderDiscount(
                name=config.get("name", "Первый заказ"),
                percent=Decimal(str(config.get("percent", 10))),
            )
        raise ValueError(f"Неизвестный тип скидки: {kind}")