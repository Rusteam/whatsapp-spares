from datetime import datetime as dt
from typing import Optional

from bot.services import ford, mercedes
from bot.utils.io import make_request


def get_exchange_rate(
    from_currency: str, to_currency: str, date_str: Optional[str] = None
) -> float:
    """Get the exchange rate from the API."""
    if not date_str:
        date_str = get_today()
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


def get_today() -> str:
    return dt.today().strftime("%Y-%m-%d")


if __name__ == "__main__":
    today = get_today()
    rate = get_exchange_rate("AED", "RUB", today)
    print(f"{today=} {rate=:.1f} from AED to RUB")
