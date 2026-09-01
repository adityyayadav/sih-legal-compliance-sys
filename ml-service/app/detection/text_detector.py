"""
text_detector.py
------------------
Detects text regions in a preprocessed image and returns their bounding
boxes + cropped sub-images, ready for Phase 5 (OCR).

BACKENDS:
  1. "paddleocr" / "craft" (Deep Learning Text Detectors: PaddleOCR DB or EasyOCR CRAFT)
  2. "contour" (Offline classical morphological fallback)
  3. "auto" (Tries DL detector first, falls back gracefully)

Usage:
    from app.detection.text_detector import detect_text_regions
    regions = detect_text_regions(image)   # image: preprocessed np.ndarray (BGR)
    # regions: [{"bbox": [x, y, w, h], "crop": np.ndarray}, ...]
"""

import logging
from typing import List, Dict

import numpy as np
import cv2

logger = logging.getLogger(__name__)

_paddle_detector = None
_paddle_available = None
_easyocr_detector = None
_craft_available = None


def _try_load_paddleocr() -> bool:
    global _paddle_detector, _paddle_available
    if _paddle_available is not None:
        return _paddle_available

    try:
        from paddleocr import PaddleOCR
        try:
            _paddle_detector = PaddleOCR(lang="en")
        except Exception:
            _paddle_detector = PaddleOCR(use_angle_cls=False, lang="en", det=True, rec=False)
        _paddle_available = True
        logger.info("PaddleOCR detector loaded successfully.")
    except Exception as e:
        logger.warning(f"PaddleOCR not available ({e}); checking CRAFT/EasyOCR detector.")
        _paddle_available = False

    return _paddle_available


def _try_load_craft() -> bool:
    global _easyocr_detector, _craft_available
    if _craft_available is not None:
        return _craft_available

    try:
        import easyocr
        _easyocr_detector = easyocr.Reader(['en'], gpu=False)
        _craft_available = True
        logger.info("CRAFT (EasyOCR) detector loaded successfully.")
    except Exception as e:
        logger.warning(f"CRAFT detector not available ({e}).")
        _craft_available = False

    return _craft_available


def _detect_with_paddleocr(image: np.ndarray) -> List[Dict]:
    result = _paddle_detector.ocr(image)
    regions = []
    if not result:
        return regions

    # PaddleOCR 3.x returns generator/list of dicts or list of boxes
    boxes = []
    if isinstance(result, list):
        if len(result) > 0 and isinstance(result[0], dict) and "dt_polys" in result[0]:
            boxes = result[0]["dt_polys"]
        elif len(result) > 0 and isinstance(result[0], list):
            boxes = result[0]

    for box in boxes:
        if isinstance(box, list) and len(box) >= 4 and isinstance(box[0], (list, tuple, np.ndarray)):
            pts = np.array(box, dtype=np.int32)
            x, y, w, h = cv2.boundingRect(pts)
        elif isinstance(box, (list, tuple, np.ndarray)) and len(box) == 4:
            x, y, w, h = int(box[0]), int(box[1]), int(box[2]), int(box[3])
        else:
            continue

        crop = image[y:y + h, x:x + w]
        if crop.size == 0:
            continue
        regions.append({"bbox": [int(x), int(y), int(w), int(h)], "crop": crop})

    regions.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))
    return regions


def _detect_with_craft(image: np.ndarray) -> List[Dict]:
    """Runs PyTorch-based CRAFT detector via EasyOCR detection API."""
    horizontal_list, free_list = _easyocr_detector.detect(image)
    regions = []
    boxes = horizontal_list[0] if (horizontal_list and len(horizontal_list) > 0) else []
    for box in boxes:
        # box: [x_min, x_max, y_min, y_max]
        x_min, x_max, y_min, y_max = box
        x, y = int(x_min), int(y_min)
        w, h = int(x_max - x_min), int(y_max - y_min)
        if w <= 0 or h <= 0:
            continue
        crop = image[y:y + h, x:x + w]
        if crop.size == 0:
            continue
        regions.append({"bbox": [int(x), int(y), int(w), int(h)], "crop": crop})

    # Sort in reading order
    regions.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))
    return regions


def _detect_with_contours(image: np.ndarray, min_area: int = 150, max_area_ratio: float = 0.5) -> List[Dict]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 9))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    image_area = image.shape[0] * image.shape[1]
    regions = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area < min_area or area > max_area_ratio * image_area:
            continue
        if w < 10 or h < 8:
            continue
        crop = image[y:y + h, x:x + w]
        if crop.size == 0:
            continue
        regions.append({"bbox": [int(x), int(y), int(w), int(h)], "crop": crop})

    regions.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))
    return regions


def detect_text_regions(image: np.ndarray, backend: str = "auto") -> List[Dict]:
    if image is None or image.size == 0:
        raise ValueError("detect_text_regions received an empty image")

    if backend == "contour":
        return _detect_with_contours(image)

    if backend == "craft":
        if not _try_load_craft():
            raise RuntimeError("CRAFT backend requested but unavailable.")
        return _detect_with_craft(image)

    if backend == "paddleocr":
        if not _try_load_paddleocr():
            raise RuntimeError("PaddleOCR backend requested but unavailable.")
        return _detect_with_paddleocr(image)

    # backend == "auto": Try CRAFT / PaddleOCR, fall back to contours
    if _try_load_craft():
        try:
            return _detect_with_craft(image)
        except Exception as e:
            logger.warning(f"CRAFT detection failed ({e}); falling back to contour detector.")

    if _try_load_paddleocr():
        try:
            return _detect_with_paddleocr(image)
        except Exception as e:
            logger.warning(f"PaddleOCR detection failed ({e}); falling back to contour detector.")

    return _detect_with_contours(image)
