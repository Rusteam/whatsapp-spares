from bot import ford, mercedes
from bot.utils import make_request


def get_exchange_rate(from_currency: str, to_currency: str, date_str: str) -> float:
    """Get the exchange rate from the API."""
    base_url = "https://api.exchangerate.host/timeseries"
    params = {
        "base": from_currency,
        "symbols": to_currency,
        "start_date": date_str,
        "end_date": date_str,
    }
    resp = make_request(base_url, params)
    return resp["rates"][date_str][to_currency]


def get_part_weight(part_number: str) -> float:
    if part_number.startswith("A"):
        weight = mercedes.get_mercedes_weight(part_number)
    elif part_number.startswith(("FR", "GR")):
        weight = ford.get_weight(part_number)
    else:
        raise NotImplementedError(f"Unknown part number: {part_number}")
    return weight
