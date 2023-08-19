import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
import pdfplumber
import pydantic

from bot.scheme.enums import Currency
from bot.scheme.parts import PartOrder

TABLE_TYPE = list[PartOrder]


@dataclass
class PdfOrderProcessor(ABC):
    """
    Base class to extract data from pdf files and format into our data format.
    """

    file: str
    checksum: Optional[float] = None

    @property
    @abstractmethod
    def supplier_name(self) -> str:
        pass

    @property
    @abstractmethod
    def currency(self) -> Currency:
        pass

    @property
    @abstractmethod
    def vat(self) -> float:
        pass

    def _read_pdf(self):
        pdf = pdfplumber.open(self.file)
        return pdf

    def _process_page_table(self, page) -> pd.DataFrame | None:
        table = page.extract_table(
            table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "text",
                "min_words_horizontal": 2,
            }
        )
        if not table:
            return None
        rows = self.parse_table(table)
        df = pd.DataFrame([row.dict() for row in rows])
        return df

    def run(self):
        pdf = self._read_pdf()
        results = []
        for page in pdf.pages:
            if (t := self._process_page_table(page)) is not None:
                results.append(t)

        results = pd.concat(results)
        if self.checksum:
            if (res := round(self.calculate_total(results), 2)) - self.checksum > 1e-3:
                raise ValueError(f"Parsing has failed: {self.checksum=} and {res=}")
        return results

    @staticmethod
    def concat_rows(prev_row: list, new_row: list) -> None:
        for i in range(len(new_row)):
            if new_row[i]:
                prev_row[i] += " " + new_row[i]

    @abstractmethod
    def parse_table(self, table) -> TABLE_TYPE:
        """From pdfplumbers extract_table output to a list of rows and
        a list of column names."""
        pass

    def calculate_total(self, results: pd.DataFrame) -> float:
        """Multiple quantity by price and add vat."""
        total = results["quantity"] * results["price"]
        return total.sum().item() * (1 + self.vat)

    @staticmethod
    def fix_number(value: str) -> str:
        value = re.sub(",", "", value)
        value = re.sub("\.00$", "", value)
        return value


class PdfOrderEuropeanAutospares(PdfOrderProcessor):
    @property
    def supplier_name(self):
        return "European Autospares"

    @property
    def vat(self):
        return 0.05

    @property
    def currency(self):
        return Currency.aed

    def _process_row(self, row: list) -> list:
        # Strip manufacturer letter and remove non-word chars
        part_num = row[1]
        if m := re.match("(\w\s)(.+(\s\w+)?)", part_num):
            row[1] = re.sub("\W", "", m.group(2))
        # create a representation
        try:
            part_order = PartOrder(
                part_number=row[1],
                part_name=row[2],
                price=self.fix_number(row[5]),
                quantity=self.fix_number(row[4]),
                currency=self.currency,
                discount=row[6],
            )
        except pydantic.ValidationError as e:
            print(f"{row=}")
            raise e
        return part_order

    def parse_table(self, rows: list[Any]) -> TABLE_TYPE:
        """Only keep meaningful rows and extract column names"""
        rows = rows[1:]
        rows_filtered = list(filter(lambda x: any(x), rows))
        i = 1
        while i < len(rows_filtered):
            row = rows_filtered[i]
            if row[0] == "":
                # second line printing
                prev_row = rows_filtered[i - 1]
                self.concat_rows(prev_row, rows_filtered.pop(i))
            elif row[0] is None:
                # table subtotals
                rows_filtered.pop(i)
            else:
                i += 1
        # strip a manufacturer name
        rows_filtered = list(map(lambda x: self._process_row(x), rows_filtered))
        return rows_filtered


class PdfOrderHND(PdfOrderProcessor):
    @property
    def supplier_name(self):
        return "HND"

    @property
    def vat(self):
        return 0.05

    @property
    def currency(self):
        return Currency.aed

    def _process_row(self, row: list) -> list:
        try:
            part_order = PartOrder(
                part_number=row[1],
                part_name=row[2],
                price=self.fix_number(row[5]),
                quantity=self.fix_number(row[4]),
                currency=self.currency,
                discount=row[6],
            )
        except pydantic.ValidationError as e:
            print(f"{row=}")
            raise e
        return part_order

    def parse_table(self, rows: list[Any]) -> TABLE_TYPE:
        """Only keep meaningful rows and extract column names"""
        rows_filtered = list(filter(lambda x: any(x), rows[1:]))
        rows_filtered = list(map(lambda x: self._process_row(x), rows_filtered))
        return rows_filtered


class PdfOrderHumaidAli(PdfOrderProcessor):
    # TODO fix failing table extraction
    @property
    def supplier_name(self):
        return "Humaid Ali Trading"

    @property
    def vat(self):
        return 0.05

    @property
    def currency(self):
        return Currency.aed

    def _process_row(self, row: list) -> list:
        try:
            part_order = PartOrder(
                part_number=row[0],
                part_name=row[1],
                price=self.fix_number(row[3]),
                quantity=self.fix_number(row[2]),
                currency=self.currency,
            )
        except pydantic.ValidationError as e:
            print(f"{row=}")
            raise e
        return part_order

    def parse_table(self, rows: list[Any]) -> TABLE_TYPE:
        """Only keep meaningful rows and extract column names"""
        rows = rows[2:]
        rows_filtered = list(filter(lambda x: any(x), rows))
        rows_filtered = list(map(lambda x: self._process_row(x), rows_filtered))
        return rows_filtered
