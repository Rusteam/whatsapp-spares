from pathlib import Path

import pytest

from bot import services

TEST_DATA_DIR = Path(__file__).parent / "data" / "fixparts"


@pytest.mark.parametrize(
    "part_number, expected",
    [
        ("A1679063107", 0.919),
        ("A0259975047", 0.087),
    ],
)
def test_get_weight(mocker, part_number, expected):
    mocker.patch("bot.services._get_fixparts_entries")
    mocker.patch("bot.services._extract_fixparts_linkpath", return_value=part_number)
    mocker.patch(
        "bot.services._get_fixparts_product_page",
        return_value=_read_html_page(part_number),
    )

    weight = services.get_fixparts_weight(part_number)
    assert weight == expected


def _read_html_page(part_number: str) -> str:
    file = TEST_DATA_DIR / f"{part_number}.html"
    return file.read_text()
