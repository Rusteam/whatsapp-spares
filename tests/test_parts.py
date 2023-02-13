from pathlib import Path

import pytest

from bot import ford, mercedes

TEST_DATA_DIR = Path(__file__).parent / "data" / "parts"


@pytest.mark.parametrize(
    "part_number, expected",
    [
        ("A1679063107", 0.919),
        ("A0259975047", 0.087),
    ],
)
def test_get_mercedes_weight(mocker, part_number, expected):
    mocker.patch("bot.mercedes._get_mercedes_entries")
    mocker.patch("bot.mercedes._extract_mercedes_linkpath", return_value=part_number)
    mocker.patch(
        "bot.mercedes._get_mercedes_product_page",
        return_value=_read_html_page(part_number),
    )

    weight = mercedes.get_mercedes_weight(part_number)
    pytest.approx(weight, expected)


@pytest.mark.parametrize(
    "part_number, expected",
    [
        ("FR3Z3079D", 3.6),
        ("GR3Z2C026C", 7.212),
    ],
)
def test_get_ford_weight(mocker, part_number, expected):
    mocker.patch(
        "bot.ford.get_product_page",
        return_value=_read_html_page(part_number),
    )

    weight = ford.get_weight(part_number)
    pytest.approx(weight, expected)


def _read_html_page(part_number: str) -> str:
    file = TEST_DATA_DIR / f"{part_number}.html"
    return file.read_text()
