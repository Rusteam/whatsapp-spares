"""Process raw text into structured quote.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bot.log import setup_logger
from bot.scheme.parts import PartQuote
from bot.utils import parse

logger = setup_logger(__name__)


@dataclass
class TextQuoteParser(ABC):
    """Meta-class to convert raw text into structured quote"""

    @abstractmethod
    def run(self, text):
        pass


class TextQuoteParserRegex(TextQuoteParser):
    """Use regex to convert raw text into structured form."""

    def run(self, text: str) -> list[PartQuote]:
        msg_parts = parse.parse_input_message(text)
        res = [
            PartQuote(
                price=one.price,
                part_number=one.part_number if one.part_number else "<UNK>",
                lead_days=one.lead_days,
                vat=one.vat,
            )
            for one in msg_parts
        ]
        return res
