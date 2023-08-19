import ast
import os
from pprint import pprint

import openai

from bot.scheme.parts import PartQuote
from bot.workers.text import TextQuoteParser, logger

openai.api_key = os.getenv("OPENAI_API_KEY")

EXAMPLE = """
Input:
A118 885 38.00 BASIC CARRIER, BUMPER 125, 10 DAYS ORDER
A166 460 60.00/80. STEERING GEAR 9481 BACK ORDER
Output: [
{"part_number": "A118 885 38.00", "part_name": "BASIC CARRIER, BUMPER", "price": 125.0, "lead_time_days": 10},
{"part_number": "A166 460 60.00/80", "part_name": "STEERING GEAR", "price": 9481.0, "lead_time_days": -1},
]
"""


class TextQuoteParserGPT(TextQuoteParser):
    """Use the OpenAI GPT-3 API to parse a quotation for spare parts."""

    model_name: str = os.getenv("OPENAI_COMPLETION_MODEL", "text-davinci-003")
    temperature: float = 1.0
    max_tokens: int = 512

    @property
    def prompt(self) -> str:
        return """Auto spare part quote parser.
        
        Format:
        {response_format}
        
        Example:
        {example}
        
        Quote:
        {quote}
        
        The JSON representation of the quote above:
        """

    def create_prompt(self, quote: str) -> str:
        """Create a prompt for the API request."""
        return self.prompt.format(
            quote=quote,
            response_format=PartQuote.schema_json(indent=2),
            example=EXAMPLE,
        )

    def run(self, prompt: str) -> PartQuote:
        """Parse the quotation."""
        full_prompt = self.create_prompt(prompt)
        response = openai.Completion.create(
            engine=self.model_name,
            prompt=full_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            n=1,
            logprobs=0,
            echo=True,
            stream=False,
            best_of=1,
            logit_bias={},
        )
        resp_text = response.choices[0].text[len(full_prompt) :]
        data = self._parse_response(resp_text)
        return data

    @staticmethod
    def _parse_response(resp_text):
        try:
            data = ast.literal_eval(resp_text)
        except Exception as e:
            logger.error(f"Failed to parse response: {resp_text}, {e}")
            return []
        data = [PartQuote.parse_obj(d) for d in data]
        return data


if __name__ == "__main__":
    quote_gpt = TextQuoteParserGPT()
    quote = """‘A099 820 88 00 REFLECTING EMITTER. 35 10 DAYS ORDER
‘A118 885 38.00 BASIC CARRIER, BUMPER 125, 10 DAYS ORDER"""
    pprint(quote_gpt.run(quote))
