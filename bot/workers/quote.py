"""Workers to extract structured data from quotes.

A quote can be a text, a screenshot or an excel file.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bot.scheme.parts import PartQuote
from bot.services.gpt import TextQuoteParser, TextQuoteParserGPT
from bot.utils import ocr


@dataclass
class QuoteParser(ABC):
    """Meta-class for different quote parsers."""

    src: str
    text_parser: TextQuoteParser

    def parse_text(self, text: str) -> list[PartQuote]:
        return self.text_parser.run(text)

    @abstractmethod
    def load_text(self):
        """Load text from input source."""
        pass

    def run(self):
        text = self.load_text()
        return self.parse_text(text)


class QuoteParserText(QuoteParser):
    def load_text(self):
        return self.src


class QuoteParserScreenshot(QuoteParser):
    def load_text(self):
        return ocr.run_ocr(self.src)
