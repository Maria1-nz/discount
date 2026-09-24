from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional

@dataclass
class Product:
    id: str
    name: str
    basePrice: Decimal
    category: str

@dataclass
class CartItem:
    product: Product
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("quantity должна быть больше 0")
    @property
    def total(self) -> Decimal:
        return self.product.basePrice * self.quantity

@dataclass
class Customer:
    id: str
    lastPurchaseDate: Optional[date]
    isFirstOrder: bool

@dataclass
class Order:
    id: str
    customer: Customer
    items: List[CartItem]
    promoCodes: List[str] = field(default_factory=list)
    createdAt: date = field(default_factory=date.today)
    deliveryCost: Decimal = Decimal("0")

@dataclass
class AppliedDiscount:
    name: str
    amount: Decimal
    reason: str

@dataclass
class PricingResult:
    baseTotal: Decimal
    appliedDiscounts: List[AppliedDiscount]
    finalTotal: Decimal

@dataclass
class DiscountContext:
    order: Order
    itemsTotal: Decimal
    deliveryCost: Decimal
    appliedDiscounts: List[AppliedDiscount] = field(default_factory=list)
    acceptedPromoCodes: List[str] = field(default_factory=list)

    def add_discount(self, discount: AppliedDiscount):
        self.appliedDiscounts.append(discount)

    def promo_already_used(self, code: str) -> bool:
        return code in self.acceptedPromoCodes