from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"


def _make_request(url, params, json: bool = True, **kwargs) -> dict | str:
    """Make a request to the API.
    """
    resp = requests.get(url, params=params, **kwargs)
    resp.raise_for_status()
    return resp.json() if json else resp.content.decode()


def get_exchange_rate(from_currency: str, to_currency: str, date_str: str) -> float:
    """Get the exchange rate from the API.
    """
    base_url = "https://api.exchangerate.host/timeseries"
    params = {
        "base": from_currency,
        "symbols": to_currency,
        "start_date": date_str,
        "end_date": date_str,
    }
    resp = _make_request(base_url, params)
    return resp["rates"][date_str][to_currency]


def _get_fixparts_entries(part_number: str) -> list[dict]:
    """Get the entries from the API.
    """
    base_url = "https://www.fixparts-online.com/en/Catalogs/"
    # send form data
    params = {"s": part_number}
    headers = {
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
    resp = _make_request(base_url, params, headers=headers, json=False)
    return resp


def _extract_fixparts_linkpath(html: str, part_number: str) -> str:
    """Extract the links from the HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="mobile__table")
    for one in cards:
        link = one.find("a", class_="text-orange")
        if link.text.strip().lower() == part_number.lower():
            return link["href"].strip()
    return None


def _get_fixparts_product_page(linkpath: str) -> str:
    """Get the product from the API.
    """
    base_url = "https://www.fixparts-online.com"
    url = urljoin(base_url, linkpath)
    headers = {
        "User-Agent": USER_AGENT,
        "referral": "https://www.fixparts-online.com/en/Catalogs/"
    }
    resp = _make_request(url, None, headers=headers, json=False)
    return resp


def _extract_fixparts_product_weight(html: str) -> float:
    """Extract the weight from the HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    weight_row = soup.find("div", class_="name", text="Weight")
    if weight_row is None:
        return None
    weight_value = weight_row.find_next_sibling("div", class_="type")
    if weight_value is None:
        return None
    weight = weight_value.text.rstrip("kg").strip()
    return float(weight)


def get_fixparts_weight(part_number: str) -> float:
    """Get the weight of the part from the API.
    """
    entries = _get_fixparts_entries(part_number)
    linkpath = _extract_fixparts_linkpath(entries, part_number)
    if linkpath is None:
        return None
    product = _get_fixparts_product_page(linkpath)
    weight = _extract_fixparts_product_weight(product)
    return weight


if __name__ == '__main__':
    w = get_fixparts_weight("A0259975047")
    print(f"Weight: {w}")
