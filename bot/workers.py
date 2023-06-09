"""Define chained processors.
"""
from pprint import pprint

from bot.gpt import QuoteParserGPT
from bot.ocr import OCR, load_image_gray


class ScreenshotQuoteParser:
    def __init__(self):
        self.processors = [
            OCR(),
            QuoteParserGPT(),
        ]

    def execute(self, input_data):
        for processor in self.processors:
            input_data = processor.run(input_data)
        return input_data


if __name__ == "__main__":
    # Load screenshot and preprocess image
    img = load_image_gray("../tests/data/images/european_quote_screenshot_6column.jpeg")
    parser = ScreenshotQuoteParser()
    res = parser.execute(img)
    pprint(res)
