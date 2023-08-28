"""Utilities to extract text from images.
"""
from pathlib import Path

import cv2
import numpy as np
import pytesseract

# pylint: disable=no-member


def extract_image_text(img: np.ndarray) -> str:
    _, img_thresh = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)  # threshold image
    text = pytesseract.image_to_string(img_thresh)
    return text


def load_image_gray(image_path: str) -> np.ndarray:
    if not (p := Path(image_path)).exists():
        raise ValueError(f"{image_path=} does not exist.")
    if not p.is_file():
        raise ValueError(f"{image_path=} is not a file.")

    img = cv2.imread(image_path)
    return img


def run_ocr(image_src: str | np.ndarray) -> str:
    """Load an image from file or from numpy array and run pytesseract on it."""
    img = load_image_gray(image_src) if isinstance(image_src, str) else image_src
    extracted = extract_image_text(img)
    return extracted


if __name__ == "__main__":
    path = "../../tests/data/quotes/european_quote_screenshot.jpeg"
    text = run_ocr(path)
    print(text)
