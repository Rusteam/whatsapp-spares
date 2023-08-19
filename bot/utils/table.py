import pandas as pd


class PandasMixin:
    @staticmethod
    def as_table(rows: list) -> pd.DataFrame:
        return pd.DataFrame([row.dict() for row in rows])

    @staticmethod
    def calculate_total(results: pd.DataFrame, vat: float = 0.0) -> float:
        """Multiple quantity by price and add vat."""
        total = results["quantity"] * results["price"]
        return total.sum().item() * (1 + vat)
