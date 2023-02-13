import requests


def make_request(url, params, json: bool = True, **kwargs) -> dict | str:
    """Make a request to the API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))
    resp = requests.get(url, params=params, headers=headers, **kwargs)
    resp.raise_for_status()
    return resp.json() if json else resp.content.decode()
