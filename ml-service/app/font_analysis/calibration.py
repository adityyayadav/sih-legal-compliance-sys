"""
calibration.py
--------------
Pixel-to-millimeter conversion logic.
1. Barcode detector: Searches for 1D standard EAN-13 / UPC barcodes (standard width = 37.29 mm).
2. Fallback: Uses default physical scale (e.g. 0.264 mm/px based on standard capture constraints).
"""

from typing import Optional, Tuple
import cv2
import numpy as np

# Standard physical dimensions in millimeters
STANDARD_EAN13_WIDTH_MM = 37.29
DEFAULT_MM_PER_PIXEL = 0.264  # ~96 DPI standard baseline


def detect_barcode_bbox(image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """
    Detects standard 1D barcode region using OpenCV's barcode detector or gradient morphology.
    Returns (x, y, w, h) if detected, else None.
    """
    if image is None or image.size == 0:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

    # Try OpenCV Barcode detector if available
    try:
        if hasattr(cv2, "barcode") and hasattr(cv2.barcode, "BarcodeDetector"):
            detector = cv2.barcode.BarcodeDetector()
            if hasattr(detector, "detectAndDecodeWithType"):
                ok, decoded_info, decoded_type, corners = detector.detectAndDecodeWithType(gray)
            else:
                ok, corners = detector.detect(gray)
            if ok and corners is not None and len(corners) > 0:
                pts = corners[0].astype(int)
                x_min, y_min = np.min(pts, axis=0)
                x_max, y_max = np.max(pts, axis=0)
                w, h = max(1, x_max - x_min), max(1, y_max - y_min)
                return int(x_min), int(y_min), int(w), int(h)
    except Exception:
        pass

    # Morphological fallback for 1D vertical bar patterns
    try:
        gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
        gradient = cv2.subtract(gradX, gradY)
        gradient = cv2.convertScaleAbs(gradient)

        blurred = cv2.blur(gradient, (9, 9))
        _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        closed = cv2.erode(closed, None, iterations=4)
        closed = cv2.dilate(closed, None, iterations=4)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = w / float(h) if h > 0 else 0
            if 1.2 <= aspect_ratio <= 3.5 and w > 60 and h > 25:
                return x, y, w, h
    except Exception:
        pass

    return None


def estimate_scale_mm_per_px(
    image: np.ndarray,
    reference_barcode_mm: float = STANDARD_EAN13_WIDTH_MM,
    fallback_mm_per_px: float = DEFAULT_MM_PER_PIXEL
) -> float:
    """
    Computes scale factor in millimeters per pixel.
    If a barcode is detected, scale = reference_barcode_mm / barcode_width_px.
    Otherwise, returns fallback_mm_per_px.
    """
    if image is None or image.size == 0:
        return fallback_mm_per_px

    barcode_box = detect_barcode_bbox(image)
    if barcode_box:
        _, _, w, _ = barcode_box
        if w > 10:
            scale = reference_barcode_mm / float(w)
            # Bound scale between reasonable photo limits (0.02 mm/px to 1.5 mm/px)
            if 0.02 <= scale <= 1.5:
                return float(scale)

    return fallback_mm_per_px
