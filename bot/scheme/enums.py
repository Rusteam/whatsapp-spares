from enum import Enum


class Currency(str, Enum):
    aed = "AED"
    rub = "RUB"
    usd = "USD"
    eur = "EUR"


class PartManufacturerType(str, Enum):
    genuine = "genuine"
    aftermarket = "aftermarket"


class PartCondition(str, Enum):
    new = "new"
    used = "used"


class ShippingType(str, Enum):
    air = "air"
    container = "container"
    pickup = "pickup"
    urgent = "urgent"
