import pytest

from bot import parse, services
from bot.scheme import InputMessage


@pytest.mark.parametrize(
    "message, expected",
    [
        (
            "1250 + vat  1 day order",
            {
                "part_number": None,
                "price": 1250.0,
                "vat": True,
                "lead_days": 1,
                "currency": "AED",
            },
        ),
        (
            "75 + vat 3 week order",
            {
                "part_number": None,
                "price": 75.0,
                "vat": True,
                "lead_days": 21,
                "currency": "AED",
            },
        ),
        (
            "1000 + vat 1 month order",
            {
                "part_number": None,
                "price": 1000.0,
                "vat": True,
                "lead_days": 30,
                "currency": "AED",
            },
        ),
        (
            "2054 + VAT  10 days order",
            {
                "part_number": None,
                "price": 2054.0,
                "vat": True,
                "lead_days": 10,
                "currency": "AED",
            },
        ),
        (
            "A2143520500 - 999 + vat  1 day order",
            {
                "part_number": "A2143520500",
                "price": 999.0,
                "vat": True,
                "lead_days": 1,
                "currency": "AED",
            },
        ),
        (
            "3343 + vat  availability will update soon",
            {
                "part_number": None,
                "price": 3343.0,
                "vat": True,
                "lead_days": 0,
                "currency": "AED",
            },
        ),
        (
            " A1678802808 - 410 + vat  7-10 days",
            {
                "part_number": "A1678802808",
                "price": 410.0,
                "vat": True,
                "lead_days": 10,
                "currency": "AED",
            },
        ),
        (
            "810 + VAT  BACK ORDER NO ETA",
            {
                "part_number": None,
                "price": 810.0,
                "vat": True,
                "lead_days": 90,
                "currency": "AED",
            },
        ),
    ],
)
def test_parse_line(message, expected):
    parsed = parse.parse_input_line(message)
    assert parsed.dict() == expected


@pytest.mark.parametrize(
    "message, expected",
    [
        (
            """A2143520500 - 99 + vat  1 day order
A2233521601 - 115 + vat  1 day order""",
            [
                {
                    "part_number": "A2143520500",
                    "price": 99.0,
                    "vat": True,
                    "lead_days": 1,
                    "currency": "AED",
                },
                {
                    "part_number": "A2233521601",
                    "price": 115.0,
                    "vat": True,
                    "lead_days": 1,
                    "currency": "AED",
                },
            ],
        )
    ],
)
def test_parse_multiline(message, expected):
    output = parse.parse_input_message(message)
    assert output == expected


def test_get_exchange_rate(mocker):
    mock_resp = mocker.patch(
        "bot.services._make_request",
        return_value={"rates": {"2021-01-01": {"RUB": 20.0}}},
    )
    rate = services.get_exchange_rate("AED", "RUB", "2021-01-01")
    assert rate == 20.0
    assert mock_resp.call_count == 1


@pytest.mark.parametrize(
    "price, ex_rate, weight, expected",
    [
        (100.0, 20.0, 1, 3610.0),
        (1000.0, 20.0, 10, 36100.0),
        (50, 19, 0, 1296.75),
    ],
)
def test_calc_selling_price(price, ex_rate, weight, expected):
    out = parse.calc_selling_price(price, weight=weight, ex_rate=ex_rate)
    assert out == expected


@pytest.mark.parametrize(
    "message, expected",
    [
        (
            {"price": 100.0, "vat": True, "lead_days": 1, "currency": "AED"},
            {
                "price": 2730.0,
                "lead_days": 15,
                "currency": "RUB",
                "part_number": None,
                "weight": 0.0,
            },
        ),
        (
            {
                "price": 100.0,
                "vat": True,
                "lead_days": 1,
                "currency": "AED",
                "part_number": "A1678853300",
            },
            {
                "price": 11530.0,
                "lead_days": 15,
                "currency": "RUB",
                "part_number": "A1678853300",
                "weight": 10.0,
            },
        ),
    ],
)
def test_prepare_output(mocker, message, expected):
    inp = InputMessage.parse_obj(message)
    ex_rate_mock = mocker.patch("bot.parse.get_exchange_rate", return_value=20.0)
    mocker.patch("bot.parse.get_fixparts_weight", return_value=10)
    out = parse.prepare_output(inp)
    assert out.dict() == expected
    assert ex_rate_mock.call_count == 1


@pytest.mark.parametrize(
    "message, expected",
    [
        (
            "1000 + vat 1 month order",
            [
                {
                    "price": 27300.0,
                    "lead_days": 44,
                    "currency": "RUB",
                    "part_number": None,
                    "weight": 0.0,
                }
            ],
        ),
        (
            """A1678853300 - 900 + vat  7-10 days 
 A1678802808 - 540 + vat  17-21 days""",
            [
                {
                    "price": 25450.0,
                    "lead_days": 24,
                    "currency": "RUB",
                    "part_number": "A1678853300",
                    "weight": 1.0,
                },
                {
                    "price": 15622.0,
                    "lead_days": 35,
                    "currency": "RUB",
                    "part_number": "A1678802808",
                    "weight": 1.0,
                },
            ],
        ),
    ],
)
def test_process_message(mocker, message, expected):
    mocker.patch("bot.parse.get_exchange_rate", return_value=20.0)
    mocker.patch("bot.parse._get_today", return_value="2021-01-01")
    mocker.patch("bot.parse.get_fixparts_weight", return_value=1)
    output = parse.process_message(message)

    assert len(output) == len(expected)
    for out, exp in zip(output, expected):
        assert out == exp
