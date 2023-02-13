from urllib.parse import urljoin

from bs4 import BeautifulSoup

from bot.utils import make_request


def get_product_page(part_number: str) -> str:
    """Get the link to the Ford part."""
    base_url = "https://www.fordpartsgiant.com"
    path = f"{base_url}/parts/{part_number}.html"
    content = make_request(urljoin(base_url, path), None, json=False)
    return content


def _extract_weight(page: str) -> float:
    """Get the weight of the Ford part."""
    soup = BeautifulSoup(page, "html.parser")
    row = soup.find("td", string="Item Weight")
    if row is None:
        return 0.0
    pounds = float(row.find_next_sibling("td").text.lower().strip("pounds").strip())
    return pounds * 0.45359237


def get_weight(part_number: str) -> float:
    """Get the weight of the Ford part."""
    page = get_product_page(part_number)
    return _extract_weight(page)


if __name__ == "__main__":
    w = get_weight("GR3Z2C026C")
    print(f"weight is {w:.3f}kg")
