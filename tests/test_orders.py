from pathlib import Path

import pydantic
import pytest

from bot import pdf

THIS_DIR = Path(__file__).parent


# pylint: disable=no-member
class CheckItem(pydantic.BaseModel):
    index: int
    part_number: str
    quantity: int
    price: float


@pytest.mark.parametrize(
    "file,checksum,check_items",
    [
        (
            "./data/orders/SOW.11833.pdf",
            19808.25,
            [
                CheckItem(
                    index=9, part_number="A44768025069051", quantity=1, price=422
                ),
                CheckItem(
                    index=10, part_number="A44768026069051", quantity=1, price=422
                ),
                CheckItem(
                    index=18, part_number="A000989700613ABDW", quantity=4, price=127
                ),
            ],
        ),
        (
            "./data/orders/SOW.11544.pdf",
            9839.55,
            [
                CheckItem(index=2, part_number="A222524260064", quantity=1, price=449),
                CheckItem(
                    index=9, part_number="A22390540009999", quantity=1, price=360
                ),
                CheckItem(index=16, part_number="A2137506600", quantity=1, price=3237),
            ],
        ),
    ],
)
def test_european_autospares(file, checksum, check_items):
    proc = pdf.PdfOrderEuropeanAutospares(file=str(THIS_DIR / file), checksum=checksum)
    res = proc.run()
    _check_items(res, check_items)


@pytest.mark.parametrize(
    "file,checksum,check_items",
    [
        (
            "./data/orders/Humaid_Ali_1.pdf",
            289.0,
            [
                CheckItem(
                    index=1,
                    part_number="86531AA000",
                    quantity=1,
                    price=165.24,
                ),
                CheckItem(
                    index=2,
                    part_number="86564AA010",
                    quantity=1,
                    price=110,
                ),
            ],
        ),
        (
            "./data/orders/Humaid_Ali_2.pdf",
            945,
            [
                CheckItem(index=1, part_number="28218BV100", quantity=10, price=90),
            ],
        ),
    ],
)
def test_humaid_ali(file, checksum, check_items):
    proc = pdf.PdfOrderHumaidAli(file=str(THIS_DIR / file), checksum=checksum)
    res = proc.run()
    _check_items(res, check_items)


@pytest.mark.parametrize(
    "file,checksum,check_items",
    [
        (
            "./data/orders/HND_invoice.pdf",
            1436.40,
            [
                CheckItem(index=1, part_number="BMW83215A7EDB2", quantity=36, price=38),
            ],
        ),
    ],
)
def test_hnd(file, checksum, check_items):
    proc = pdf.PdfOrderHND(file=str(THIS_DIR / file), checksum=checksum)
    res = proc.run()
    _check_items(res, check_items)


def _check_items(res, check_items):
    if check_items:
        for expected in check_items:
            actual = res.iloc[expected.index - 1].to_dict()
            actual = CheckItem(index=expected.index, **actual)
            assert actual == expected
