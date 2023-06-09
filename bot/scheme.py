import os
from typing import Optional

import pydantic

# pylint: disable=no-member


class InputMessage(pydantic.BaseModel):
    """A raw message from a supplier."""

    price: float
    part_number: Optional[str] = None
    lead_days: int = 1
    vat: bool = True
    currency: str = "AED"


class OutputMessage(pydantic.BaseModel):
    """A message to be sent to a customer."""

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


class Constants(pydantic.BaseModel):
    """Constants for the calculations."""

    vat: float = float(os.getenv("AED_VAT", "0.05"))
    shipping_days: int = int(os.getenv("RU_SHIPPING_DAYS", "14"))
    profit_margin: float = float(os.getenv("PROFIT_MARGIN", "0.2"))
    currency_conversion_charge: float = float(
        os.getenv("CURRENCY_CONVERSION_CHARGE", "0.1")
    )
    back_order_lead_days: int = int(os.getenv("BACK_ORDER_LEAD_DAYS", "90"))
    shipping_rate: float = float(os.getenv("SHIPPING_RATE_AED", "40"))


class PartQuote(pydantic.BaseModel):
    part_number: str = pydantic.Field(
        ...,
        description="Long part number including spaces and other non-alphanumeric characters.",
    )
    part_name: str = pydantic.Field(None, description="Short part description.")
    price: float = pydantic.Field(0.0, description="Price in the original currency.")
    lead_time_days: int = pydantic.Field(
        -1, description="Lead time in days, -1 for back order"
    )

    # pylint: disable=no-self-argument
    @pydantic.validator("part_number")
    def keep_alphanumberic(cls, v):
        return "".join([c for c in v if c.isalnum()])

    @pydantic.validator("part_name")
    def capitalize(cls, v):
        return v.lower().capitalize()
