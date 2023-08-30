from typing import Optional

import pandas as pd

from bot import CONSTANTS
from bot.services.utils import get_exchange_rate


class PandasMixin:
    @staticmethod
    def as_table(rows: list) -> pd.DataFrame:
        return pd.DataFrame([row.dict() for row in rows])

    @staticmethod
    def calculate_unit_total(
        results: pd.DataFrame, vat: float = 0.0, shipping: Optional[str] = None
    ) -> float:
        """Multiple quantity by price and add vat."""
        total = results["quantity"] * results["price"]
        direct_cost = total * (1 + vat)
        if shipping:
            direct_cost += results[shipping] * results["quantity"]
        return direct_cost

    @staticmethod
    def convert_currency(
        results: pd.DataFrame, from_currency: str, to_currency: str
    ) -> float:
        """Convert currency."""
        ex_rate = get_exchange_rate(from_currency, to_currency)
        ex_rate *= 1 + CONSTANTS.currency_conversion_charge
        return results["total"] * ex_rate
