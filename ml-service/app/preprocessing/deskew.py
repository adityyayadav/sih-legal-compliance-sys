"""
deskew.py
----------
Corrects small rotational tilt in an image (photo taken slightly crooked).
This runs AFTER perspective_correction.py — perspective correction handles
large angle/tilt distortion (camera not facing the label head-on); deskew
handles the smaller residual rotation (label itself printed/warped slightly
off-axis, or the photo itself is a few degrees off level).
"""

import cv2
import numpy as np


def _estimate_skew_angle(image: np.ndarray) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Invert + threshold so text/foreground becomes white on black background,
    # which is what minAreaRect needs to find the enclosing rectangle angle.
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    if coords.shape[0] < 20:
        return 0.0  # not enough foreground pixels to estimate reliably

    angle = cv2.minAreaRect(coords)[-1]

    # cv2.minAreaRect angle convention varies by OpenCV version; normalize to
    # a value in the range [-45, 45] representing the rotation needed.
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    return angle


def deskew(image: np.ndarray, max_correction_degrees: float = 15.0) -> np.ndarray:
    """
    Detects and corrects small rotational skew.
    max_correction_degrees caps how much rotation we're willing to apply —
    protects against a bad angle estimate on a noisy/cluttered image causing
    a large, wrong rotation that makes things worse instead of better.
    """
    if image is None or image.size == 0:
        raise ValueError("deskew received an empty image")

    angle = _estimate_skew_angle(image)

    if abs(angle) < 0.3:
        return image  # negligible skew, not worth the interpolation cost/blur

    if abs(angle) > max_correction_degrees:
        # Angle estimate is likely wrong (background clutter, non-text image)
        # — skip correction rather than risk a bad rotation.
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated
