from urllib.parse import urljoin

from bs4 import BeautifulSoup

from bot.utils import make_request


def _get_mercedes_entries(part_number: str) -> list[dict]:
    """Get the entries from the API."""
    base_url = "https://www.fixparts-online.com/en/Catalogs/"
    # send form data
    params = {"s": part_number}
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    resp = make_request(base_url, params, json=False, headers=headers)
    return resp


def _extract_mercedes_linkpath(html: str, part_number: str) -> str:
    """Extract the links from the HTML."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="mobile__table")
    for one in cards:
        link = one.find("a", class_="text-orange")
        if link.text.strip().lower() == part_number.lower():
            return link["href"].strip()
    return None


def _get_mercedes_product_page(linkpath: str) -> str:
    """Get the product from the API."""
    base_url = "https://www.fixparts-online.com"
    url = urljoin(base_url, linkpath)
    headers = {
        "referral": "https://www.fixparts-online.com/en/Catalogs/",
    }
    resp = make_request(url, None, json=False, headers=headers)
    return resp


def _extract_mercedes_product_weight(html: str) -> float:
    """Extract the weight from the HTML."""
    soup = BeautifulSoup(html, "html.parser")
    weight_row = soup.find("div", class_="name", string="Weight")
    if weight_row is None:
        return 0.0
    weight_value = weight_row.find_next_sibling("div", class_="type")
    if weight_value is None:
        return 0.0
    weight = weight_value.text.rstrip("kg").strip()
    return float(weight)


def get_mercedes_weight(part_number: str) -> float:
    """Get the weight of the part from the API."""
    entries = _get_mercedes_entries(part_number)
    linkpath = _extract_mercedes_linkpath(entries, part_number)
    if linkpath is None:
        return 0.0
    product = _get_mercedes_product_page(linkpath)
    weight = _extract_mercedes_product_weight(product)
    return weight


if __name__ == "__main__":
    w = get_mercedes_weight("A0259975047")
    print(f"Weight: {w}")
