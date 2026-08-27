"""
denoise_enhance.py
--------------------
Cleans up image noise (grainy low-light photos) and improves local contrast
(uneven lighting, glare, dim label text) — both of which hurt OCR accuracy
significantly if left uncorrected. Runs LAST in the pipeline, after geometry
(perspective + deskew) is already fixed, so denoising doesn't get undone by
a later rotation/warp interpolation.
"""

import cv2
import numpy as np


def _denoise(image: np.ndarray) -> np.ndarray:
    """Removes grain/noise while preserving edges (important — text edges
    must stay sharp for OCR, unlike a general photo-denoising use case)."""
    return cv2.fastNlMeansDenoisingColored(
        image,
        None,
        h=7,            # filter strength for luminance — higher = more smoothing
        hColor=7,        # filter strength for color channels
        templateWindowSize=7,
        searchWindowSize=21
    )


def _enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    CLAHE (Contrast Limited Adaptive Histogram Equalization) applied on the
    L channel only (LAB color space) — boosts local contrast (helps with
    uneven lighting / partial glare / dim print) without blowing out colors,
    which a naive global histogram equalization on BGR would do.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_channel)

    enhanced_lab = cv2.merge((l_enhanced, a_channel, b_channel))
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    return enhanced_bgr


def denoise_and_enhance(image: np.ndarray) -> np.ndarray:
    """Combined denoise + contrast enhancement step."""
    if image is None or image.size == 0:
        raise ValueError("denoise_and_enhance received an empty image")

    denoised = _denoise(image)
    enhanced = _enhance_contrast(denoised)
    return enhanced
