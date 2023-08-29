"""Workers to extract structured data from quotes.

A quote can be a text, a screenshot or an excel file.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bot.scheme.enums import ShippingType
from bot.scheme.messages import Constants
from bot.scheme.parts import PartQuote, PartQuoteExtended
from bot.services.gpt import TextQuoteParser, TextQuoteParserGPT
from bot.utils import ocr
from bot.utils.table import PandasMixin


@dataclass
class QuoteParser(ABC, PandasMixin):
    """Meta-class for different quote parsers."""

    src: str
    text_parser: TextQuoteParser

    def parse_text(self, text: str) -> list[PartQuote]:
        return self.text_parser.run(text)

    @abstractmethod
    def load_text(self):
        """Load text from input source."""
        pass

    def run(self, weight: bool = False):
        text = self.load_text()
        parts = self.parse_text(text)
        parts = [PartQuoteExtended.parse_obj(part) for part in parts]
        if weight:
            _ = [self.add_weight(part) for part in parts]
        _ = [self.add_shipping_cost(part) for part in parts]
        return parts

    @staticmethod
    def add_weight(part: PartQuoteExtended) -> float:
        """Get the weight of the part."""
        try:
            part.get_weight()
        except Exception as e:
            print(f"Unable to fetch weight for {part.part_number=}: {e}")

    @staticmethod
    def add_shipping_cost(part: PartQuoteExtended) -> float:
        """Calculate the shipping cost of the part."""
        try:
            part.calculate_shipping_cost()
        except Exception as e:
            print(f"Unable to calculate shipping cost for {part.part_number=}: {e}")
            pass


class QuoteParserText(QuoteParser):
    def load_text(self):
        return self.src


class QuoteParserScreenshot(QuoteParser):
    def load_text(self):
        return ocr.run_ocr(self.src)


if __name__ == "__main__":
    path = "../../tests/data/quotes/european_quote_screenshot.jpeg"
    parser = QuoteParserScreenshot(src=path, text_parser=TextQuoteParserGPT())
    res = parser.run(weight=True)
    print(parser.as_table(res))
