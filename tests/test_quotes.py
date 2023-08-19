from pathlib import Path

import pytest

from bot.workers import quote, text

THIS_DIR = Path(__file__).parent


@pytest.mark.parametrize("file", ["./data/quotes/european_quote_screenshot.jpeg"])
def test_european_auto(file):
    parser = quote.QuoteParserScreenshot(
        src=file, text_parser=text.TextQuoteParserRegex()
    )
    res = parser.run()

    assert res
