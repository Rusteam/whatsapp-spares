import logging

import pydantic

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


class PartBaseExtended(PartBase):
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


class PartQuote(PartBase):
    lead_time_days: int = pydantic.Field(
        -1, description="Lead time in days, -1 for back order"
    )


class PartOrder(PartBase):
    discount: float = pydantic.Field(0.0, description="discount on the items.")
