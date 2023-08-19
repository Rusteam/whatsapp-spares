import cv2
import numpy as np
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


def download_image(url: str, **kwargs) -> np.ndarray:
    """Download an image from the url."""
    resp = requests.get(url, **kwargs)
    resp.raise_for_status()
    image_array = np.asarray(bytearray(resp.content), dtype="uint8")
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)  # pylint: disable=no-member


if __name__ == "__main__":
    a = download_image("https://i.imgur.com/4xysyQ7.jpeg")
    cv2.imwrite("test.jpg", a)
