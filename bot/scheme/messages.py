import os
from typing import Optional

import pydantic

from bot.scheme.enums import Currency

# pylint: disable=no-member


class InputMessage(pydantic.BaseModel):
    """A raw message from a supplier."""

    price: float
    part_number: Optional[str] = None
    lead_days: int = 1
    vat: bool = True
    currency: str = Currency.aed


class OutputMessage(pydantic.BaseModel):
    """A message to be sent to a customer."""

    price: float
    lead_days: int
    part_number: Optional[str] = None
    currency: str = Currency.rub
    weight: float = 0.0

    def format(self) -> str:
        values = []
        if self.part_number:
            values.append(self.part_number)
        values.append(f"Цена: {self.price:.0f} руб.")
        values.append(f"Срок поставки: {self.lead_days} дн.")
        values.append(f"Вес: {self.weight:.3f} кг.")
        return "\n".join(values)


class Constants(pydantic.BaseModel):
    """Constants for the calculations."""

    vat: float = float(os.getenv("AED_VAT", "0.05"))
    profit_margin: float = float(os.getenv("PROFIT_MARGIN", "0.2"))
    currency_conversion_charge: float = float(
        os.getenv("CURRENCY_CONVERSION_CHARGE", "0.04")
    )
    back_order_lead_days: int = int(os.getenv("BACK_ORDER_LEAD_DAYS", "90"))
    shipping_rate: float = float(os.getenv("SHIPPING_RATE_AED", "40"))
    shipping_days: int = int(os.getenv("RU_SHIPPING_DAYS", "14"))
    shipping_rate_container: float = float(
        os.getenv("SHIPPING_RATE_AED_CONTAINER", "14.68")
    )
    shipping_default_cost: float = float(os.getenv("SHIPPING_DEFAULT_COST", "0.25"))
