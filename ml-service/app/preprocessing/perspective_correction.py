"""
perspective_correction.py
---------------------------
Finds the packaging/label boundary in a photo and warps it to a flat,
front-on rectangle. Handles photos taken at an angle (not straight-on) or
of curved/bottle labels where the visible label region is a quadrilateral
rather than a perfect rectangle in the raw photo.

If no reliable quadrilateral is found (e.g. background is cluttered, label
fills the whole frame already), the original image is returned unchanged
rather than risking a bad warp that destroys the image.
"""

import cv2
import numpy as np


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Orders 4 points as top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]        # top-left has smallest sum
    rect[2] = pts[np.argmax(s)]        # bottom-right has largest sum
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]     # top-right has smallest difference
    rect[3] = pts[np.argmax(diff)]     # bottom-left has largest difference
    return rect


def _find_largest_quadrilateral(image: np.ndarray):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    image_area = image.shape[0] * image.shape[1]

    for c in contours[:5]:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(c) > 0.2 * image_area:
            return approx.reshape(4, 2)

    return None


def correct_perspective(image: np.ndarray) -> np.ndarray:
    """
    Detects the label/package boundary and warps it to a flat rectangle.
    Falls back to returning the original image unchanged if no confident
    quadrilateral boundary is found.
    """
    if image is None or image.size == 0:
        raise ValueError("correct_perspective received an empty image")

    quad = _find_largest_quadrilateral(image)
    if quad is None:
        return image  # safe fallback — no confident boundary found

    rect = _order_points(quad.astype("float32"))
    (tl, tr, br, bl) = rect

    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = max(int(width_a), int(width_b))

    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = max(int(height_a), int(height_b))

    if max_width < 20 or max_height < 20:
        # degenerate quad, not worth warping
        return image

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    return warped
