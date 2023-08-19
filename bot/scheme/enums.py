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
