import os
from typing import Optional

from pydantic import BaseModel


class InputMessage(BaseModel):
    """A raw message from a supplier.
    """
    price: float
    part_number: Optional[str] = None
    lead_days: int = 1
    vat: bool = True
    currency: str = "AED"


class OutputMessage(BaseModel):
    """A message to be sent to a customer.
    """
    price: float
    lead_days: int
    part_number: Optional[str] = None
    currency: str = "RUB"
    weight: float = 0.0

    def format(self) -> str:
        values = []
        if self.part_number:
            values.append(self.part_number)
        values.append(f"Цена: {self.price:.0f} руб.")
        values.append(f"Срок поставки: {self.lead_days} дн.")
        values.append(f"Вес: {self.weight:.3f} кг.")
        return "\n".join(values)


class Constants(BaseModel):
    """Constants for the calculations.
    """
    vat: float = float(os.getenv("AED_VAT", "0.05"))
    shipping_days: int = int(os.getenv("RU_SHIPPING_DAYS", "14"))
    profit_margin: float = float(os.getenv("PROFIT_MARGIN", "0.2"))
    currency_conversion_charge: float = float(os.getenv("CURRENCY_CONVERSION_CHARGE", "0.1"))
    back_order_lead_days: int = int(os.getenv("BACK_ORDER_LEAD_DAYS", "90"))
    shipping_rate: float = float(os.getenv("SHIPPING_RATE_AED", "40"))
