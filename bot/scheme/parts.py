import logging

import pydantic

from bot import CONSTANTS
from bot.scheme.enums import Currency, PartCondition, PartManufacturerType
from bot.services.utils import get_part_weight

# pylint: disable=no-member


class PartBase(pydantic.BaseModel):
    part_number: str = pydantic.Field(
        ...,
        description="Long part number including spaces and other non-alphanumeric characters.",
    )
    part_name: str = pydantic.Field(None, description="Short part description.")
    quantity: int = pydantic.Field(1, description="How many items.")
    currency: str = pydantic.Field(Currency.aed, description="3-letter curency code.")
    price: float = pydantic.Field(0.0, description="Price in the original currency.")

    # pylint: disable=no-self-argument
    @pydantic.validator("part_number")
    def keep_alphanumberic(cls, v):
        return "".join([c for c in v if c.isalnum()])

    @pydantic.validator("part_name")
    def capitalize(cls, v):
        return v.lower().capitalize()

    def fetch_weight(self):
        try:
            self.weight = get_part_weight(self.part_number)
        except NotImplementedError as e:
            logging.error(f"Unable to fetch weight for {self.part_number=}", exc_info=e)


class PartQuote(PartBase):
    lead_time_days: int = pydantic.Field(
        -1, description="Lead time in days, -1 for back order"
    )


class PartQuoteExtended(PartQuote):
    weight: float = pydantic.Field(-1, description="Part weight in kilograms.")
    manufacturer: str = pydantic.Field(
        None, description="The original producer of the part."
    )
    manufacturer_type: PartManufacturerType = pydantic.Field(
        None, description="Part manufacturer and condition"
    )
    condition: PartCondition = pydantic.Field(
        PartCondition.new, description="Whether new or used."
    )
    shipping_air: float = pydantic.Field(
        0.0, description="Shipping cost by air in the original currency."
    )
    shipping_container: float = pydantic.Field(
        0.0, description="Shipping cost by container in the original currency."
    )

    def get_weight(self) -> None:
        """Get the weight of the part."""
        self.weight = get_part_weight(self.part_number)

    def calculate_shipping_cost(self) -> None:
        """Calculate the shipping cost of the part."""
        if self.weight <= 0.0:
            air_to_container = (
                CONSTANTS.shipping_rate / CONSTANTS.shipping_rate_container
            )
            self.shipping_air = self.price * CONSTANTS.shipping_default_cost
            self.shipping_container = self.shipping_air / air_to_container
        else:
            self.shipping_air = self.weight * CONSTANTS.shipping_rate
            self.shipping_container = self.weight * CONSTANTS.shipping_rate_container


class PartOrder(PartBase):
    discount: float = pydantic.Field(0.0, description="discount on the items.")
