from pathlib import Path

import pytest

from bot.scheme.parts import PartQuoteExtended
from bot.services import ford, mercedes

TEST_DATA_DIR = Path(__file__).parent / "data" / "parts"


@pytest.mark.parametrize(
    "part_number, expected",
    [
        ("A1679063107", 0.919),
        ("A0259975047", 0.087),
    ],
)
def test_get_mercedes_weight(mocker, part_number, expected):
    mocker.patch("bot.services.mercedes._get_mercedes_entries")
    mocker.patch(
        "bot.services.mercedes._extract_mercedes_linkpath", return_value=part_number
    )
    mocker.patch(
        "bot.services.mercedes._get_mercedes_product_page",
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
        "bot.services.ford.get_product_page",
        return_value=_read_html_page(part_number),
    )

    weight = ford.get_weight(part_number)
    pytest.approx(weight, expected)


@pytest.mark.parametrize(
    "part_number,price,weight,expected_air,expected_container",
    [
        ("A123", 100, 0, 25, 25 / (40 / 14.68)),
        ("A123", 1000, 10, 40 * 10, 14.68 * 10),
    ],
)
def test_shipping_calculation(
    part_number, price, weight, expected_air, expected_container
):
    part = PartQuoteExtended(part_number=part_number, price=price, weight=weight)
    part.calculate_shipping_cost()

    assert part.shipping_air == expected_air
    assert part.shipping_container == expected_container


def _read_html_page(part_number: str) -> str:
    file = TEST_DATA_DIR / f"{part_number}.html"
    return file.read_text()
