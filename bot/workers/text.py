"""OpenAI GPT api requests.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bot.log import setup_logger
from bot.scheme.parts import PartQuote
from bot.utils import parse
from bot.utils.parse import process_message

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
        msg = parse.parse_input_message(text)
        return msg
