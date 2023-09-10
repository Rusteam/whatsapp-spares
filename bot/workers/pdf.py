import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
import pdfplumber
import pydantic

from bot.scheme.enums import Currency
from bot.scheme.parts import PartOrder
from bot.utils.parse import format_date
from bot.utils.table import PandasMixin

TABLE_TYPE = list[PartOrder]


class CropConfig(pydantic.BaseModel):  # pylint: disable=no-member
    start_after: str = pydantic.Field(..., description="Start after this text")
    end_before: str = pydantic.Field(..., description="End before this text")


class ColumnConfig(pydantic.BaseModel):  # pylint: disable=no-member
    name: str = pydantic.Field(..., description="Text value that defines a column")
    side: str = pydantic.Field("x0", description="Attribute that described the border")


@dataclass
class PdfOrderProcessor(ABC, PandasMixin):
    """
    Base class to extract data from pdf files and format into our data format.
    """

    file: str
    checksum: Optional[float] = None

    @property
    def table_settings(self) -> dict:
        return {
            "vertical_strategy": "lines",
            "horizontal_strategy": "text",
            "min_words_horizontal": 2,
        }

    @property
    def crop_settings(self) -> CropConfig:
        return None

    @property
    def column_names(self) -> list[ColumnConfig]:
        return []

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
        page = self.crop_page(page)
        table = page.extract_table(
            table_settings=self.update_table_settings(page, self.table_settings),
        )
        if not table:
            return None
        rows = self.parse_table(table)
        return self.as_table(rows)

    @abstractmethod
    def extract_invoice_date(self, pdf: pdfplumber.PDF) -> str:
        pass

    def run(self):
        pdf = self._read_pdf()
        results = []
        for page in pdf.pages:
            if (t := self._process_page_table(page)) is not None:
                results.append(t)

        results = pd.concat(results)
        if self.checksum:
            if (
                res := round(self.calculate_unit_total(results, vat=self.vat).sum(), 2)
            ) - self.checksum > 1e-3:
                raise ValueError(f"Parsing has failed: {self.checksum=} and {res=}")

        results["invoice_date"] = self.extract_invoice_date(pdf)
        results["supplier_name"] = self.supplier_name
        results["amount"] = results["price"] * results["quantity"] * (1 + self.vat)
        return results

    def crop_page(self, page):
        """Crops a page if crop_settings are defined."""
        if self.crop_settings:
            start, *_ = page.search(self.crop_settings.start_after)
            end, *_ = page.search(self.crop_settings.end_before)
            crop = page.crop(
                [0, start["bottom"] + 1, page.width, end["top"] - 1], strict=False
            )
            return crop
        else:
            return page

    def update_table_settings(
        self, page: pdfplumber.pdf.Page, table_settings: dict
    ) -> dict:
        """If table column names are provided, then define columns based on test search"""
        if not self.column_names:
            return table_settings
        else:
            vert_lines = []
            for col in self.column_names:
                res, *_ = page.search(col.name)
                vert_lines.append(res[col.side])
            table_settings.update(
                dict(vertical_strategy="explicit", explicit_vertical_lines=vert_lines)
            )
            return table_settings

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

    def extract_invoice_date(self, pdf: pdfplumber.PDF) -> str:
        page = pdf.pages[0]
        tables = page.extract_tables()
        [key], [val] = tables[2]
        if key == "Invoice Date":
            return format_date(val, from_format="%m/%d/%Y")
        else:
            raise ValueError(f"Table contains {key}={val} in place of invoice date.")


class PdfOrderHND(PdfOrderProcessor):
    @property
    def table_settings(self):
        return dict(
            horizontal_strategy="lines",
            vertical_strategy="text",
        )

    @property
    def crop_settings(self):
        return CropConfig(start_after="Delivery Date", end_before="Order Subtotal")

    @property
    def column_names(self) -> list[str]:
        return [
            ColumnConfig(name="Sr. No."),
            ColumnConfig(name="Item Code"),
            ColumnConfig(name="Description"),
            ColumnConfig(name="Quantity"),
            ColumnConfig(name="UoM"),
            ColumnConfig(name="Loc"),
            ColumnConfig(name="Loc", side="x1"),
            ColumnConfig(name="Price", side="x1"),
            ColumnConfig(name="Tax 5%", side="x1"),
            ColumnConfig(name="Total", side="x1"),
        ]

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
                price=self.fix_number(row[6]),
                quantity=self.fix_number(row[3]),
                currency=self.currency,
                discount=0,
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

    def extract_invoice_date(self, pdf: pdfplumber.PDF) -> str:
        page = pdf.pages[0]
        match, *_ = page.search("Document Date")
        crop = page.crop(
            [match["x0"], match["bottom"] + 1, match["x1"], match["bottom"] + 10]
        )
        date = crop.extract_text_simple()
        return format_date(date, "%d/%m/%y")


class PdfOrderHumaidAli(PdfOrderProcessor):
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

    def extract_invoice_date(self, pdf: pdfplumber.PDF) -> str:
        page = pdf.pages[0]
        text = page.extract_text_simple()
        match = re.search("DATE : (\d{2}/\d{2}/\d{4})", text, re.I)
        if match:
            return format_date(match.group(1), "%d/%m/%Y")
        else:
            raise ValueError(f"Date not found in:\n\n{text}")
