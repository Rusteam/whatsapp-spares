from dataclasses import dataclass

import cv2
import numpy as np
import pytesseract

# pylint: disable=no-member


def extract_image_text(img: np.ndarray) -> str:
    _, img_thresh = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)  # threshold image
    text = pytesseract.image_to_string(img_thresh)
    return text


def load_image_gray(path: str) -> np.ndarray:
    img = cv2.imread(path)
    return img


@dataclass
class OCR:
    def run(self, img: np.ndarray) -> str:
        return extract_image_text(img)


if __name__ == "__main__":

    img = load_image_gray("../tests/data/images/european_quote_screenshot.jpeg")
    ocr = OCR()
    text = ocr.run(img)
    print(text)
