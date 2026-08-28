"""
text_detector.py
------------------
Detects text regions in a preprocessed image and returns their bounding
boxes + cropped sub-images, ready for Phase 5 (OCR).

TWO BACKENDS — read this before you deploy:

  1. "paddleocr" (recommended for production/demo accuracy)
     Wraps PaddleOCR's DB text detector. Requires the `paddleocr` +
     `paddlepaddle` packages, AND an internet connection the first time it
     runs (PaddleOCR downloads its pretrained detection model on first use).
     This is what you should actually use for your real demo/deployment.

  2. "contour" (offline fallback, zero downloads, zero GPU)
     A classical OpenCV MSER/Otsu + morphological-merge detector. Lower
     accuracy than PaddleOCR on real cluttered photos, but works completely
     offline. This exists so that:
       - This module's tests run identically on any machine (including CI
         environments with no internet access), without needing to fake or
         skip the detection step.
       - You have a working fallback if PaddleOCR fails to install on
         someone's machine (a real, common problem — paddlepaddle is a large,
         sometimes finicky dependency).

  backend="auto" (the default) tries PaddleOCR first and transparently
  falls back to the contour method if PaddleOCR isn't installed/available.
  This is what app/main.py should use in Phase 9.

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
_paddle_available = None  # None = not checked yet, True/False = checked


def _try_load_paddleocr() -> bool:
    """Lazily imports and initializes PaddleOCR exactly once. Cached after
    the first call (successful or not) so we don't retry a slow/failing
    import on every single request."""
    global _paddle_detector, _paddle_available
    if _paddle_available is not None:
        return _paddle_available

    try:
        from paddleocr import PaddleOCR
        _paddle_detector = PaddleOCR(use_angle_cls=False, lang="en", det=True, rec=False, show_log=False)
        _paddle_available = True
        logger.info("PaddleOCR detector loaded successfully.")
    except Exception as e:
        logger.warning(f"PaddleOCR not available ({e}); falling back to contour-based detector.")
        _paddle_available = False

    return _paddle_available


def _detect_with_paddleocr(image: np.ndarray) -> List[Dict]:
    result = _paddle_detector.ocr(image, det=True, rec=False, cls=False)
    regions = []
    if not result or not result[0]:
        return regions

    for box in result[0]:
        pts = np.array(box, dtype=np.int32)  # 4 (x, y) corner points, possibly rotated
        x, y, w, h = cv2.boundingRect(pts)
        crop = image[y:y + h, x:x + w]
        if crop.size == 0:
            continue
        regions.append({"bbox": [int(x), int(y), int(w), int(h)], "crop": crop})

    return regions


def _detect_with_contours(image: np.ndarray, min_area: int = 150, max_area_ratio: float = 0.5) -> List[Dict]:
    """
    Offline fallback detector:
      1. Otsu threshold to separate ink (text) from background.
      2. Horizontal dilation to merge individual characters/words into
         text-line-sized blobs (text detection cares about lines/phrases,
         not individual letters).
      3. Contour extraction on the merged blobs -> bounding boxes.

    Tuned for printed label text on a roughly uniform background. Will
    under-perform PaddleOCR on cluttered/textured real product photos —
    that's expected and fine, this is the safety-net backend, not the
    primary one.
    """
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

    # Stable reading order: top-to-bottom, then left-to-right.
    regions.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))
    return regions


def detect_text_regions(image: np.ndarray, backend: str = "auto") -> List[Dict]:
    """
    Detects text regions in `image`.

    backend:
      "auto"       -> try PaddleOCR, fall back to contour-based if unavailable (default, use this in production)
      "paddleocr"  -> force PaddleOCR; raises RuntimeError if not installed/available
      "contour"    -> force the offline fallback (used by this module's own tests)
    """
    if image is None or image.size == 0:
        raise ValueError("detect_text_regions received an empty image")

    if backend == "contour":
        return _detect_with_contours(image)

    if backend == "paddleocr":
        if not _try_load_paddleocr():
            raise RuntimeError(
                "PaddleOCR backend was explicitly requested but is not available. "
                "Install with: pip install paddleocr paddlepaddle"
            )
        return _detect_with_paddleocr(image)

    # backend == "auto"
    if _try_load_paddleocr():
        try:
            return _detect_with_paddleocr(image)
        except Exception as e:
            logger.warning(f"PaddleOCR detection failed at runtime ({e}); falling back to contour-based detector.")
            return _detect_with_contours(image)

    return _detect_with_contours(image)
