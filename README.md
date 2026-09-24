# Discount Engine

Движок расчёта скидок для маркетплейса.

## Запуск
```
pip install -r requirements.txt
python demo.py
pytest tests/ -v
```
## Классы

- **Discount** (ABC) — контракт: `apply(ctx)` возвращает `AppliedDiscount` или `None`.
- **PercentDiscount** — N% от суммы товаров.
- **FixedDiscount** — N рублей при сумме ≥ порога.
- **ThreeForTwoDiscount** — 3 по цене 2 в категории.
- **PromoCodeDiscount** — промокод (процентный или фиксированный), одноразовый в заказе.
- **LoyaltyDiscount** — 5% при последней покупке ≤ 30 дней.
- **FreeDeliveryDiscount** — доставка 0 при сумме строго выше порога.
- **FirstOrderDiscount** — 10% при первом заказе.
- **DiscountFactory** — создаёт стратегию по конфигу.
- **DiscountRegistry**, **ConfigProvider** — Singleton.
- **PricingEngine** — применяет стратегии. Работает только с абстракцией `Discount`, без проверок типа.

## Округление

Банковское (`ROUND_HALF_EVEN`) до копеек. Округляется каждый промежуточный результат.

**Студентка:** Кудиярова Мария · **Группа:** 09.07.13р