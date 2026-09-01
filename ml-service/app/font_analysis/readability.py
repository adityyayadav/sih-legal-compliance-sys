"""
readability.py
--------------
Luminance and contrast ratio analysis for text legibility under Rule 6 / Rule 7.
"""

from typing import Dict, Any
import cv2
import numpy as np


def calculate_contrast_ratio(crop: np.ndarray) -> float:
    """
    Calculates contrast ratio between text foreground and background in a crop.
    Contrast ratio = (L1 + 0.05) / (L2 + 0.05), where L1 >= L2 (WCAG formula).
    Returns ratio from 1.0 to 21.0.
    """
    if crop is None or crop.size == 0:
        return 1.0

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop.copy()

    # Binarize with Otsu's threshold to separate text from background
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Determine foreground and background masks based on darker vs lighter pixels
    mask_fg = thresh == 0
    mask_bg = thresh == 255

    # If crop is mostly uniform
    if np.sum(mask_fg) == 0 or np.sum(mask_bg) == 0:
        return 1.0

    mean_fg = np.mean(gray[mask_fg]) / 255.0
    mean_bg = np.mean(gray[mask_bg]) / 255.0

    l1 = max(mean_fg, mean_bg)
    l2 = min(mean_fg, mean_bg)

    contrast_ratio = (l1 + 0.05) / (l2 + 0.05)
    return float(round(contrast_ratio, 2))


def check_readability(crop: np.ndarray, min_contrast_ratio: float = 3.0) -> Dict[str, Any]:
    """
    Evaluates whether the given text region crop satisfies minimum readability criteria.
    """
    ratio = calculate_contrast_ratio(crop)
    return {
        "contrast_ratio": ratio,
        "is_readable": ratio >= min_contrast_ratio,
        "min_required_ratio": min_contrast_ratio
    }
