"""
pipeline.py
------------
Composes the three preprocessing steps into a single function that Phase 4
(detection) and Phase 9 (the /analyze API route) call directly.

Order matters:
  1. correct_perspective — fix large angle/tilt (camera not facing label head-on)
  2. deskew              — fix small residual rotation
  3. denoise_and_enhance — clean up noise/contrast LAST, so it isn't undone by
                            the interpolation from steps 1-2

Each step is wrapped so that if one step fails on a particularly bad image,
the pipeline logs it and continues with the image as it was before that step,
rather than crashing the whole /analyze request over one preprocessing stage.
"""

import logging
import numpy as np

from app.preprocessing.perspective_correction import correct_perspective
from app.preprocessing.deskew import deskew
from app.preprocessing.denoise_enhance import denoise_and_enhance

logger = logging.getLogger(__name__)


def preprocess(image: np.ndarray) -> np.ndarray:
    """
    Runs the full preprocessing chain on a single image.
    Returns the cleaned-up image, ready for text detection (Phase 4).
    """
    if image is None or image.size == 0:
        raise ValueError("preprocess received an empty image")

    result = image

    result = _safe_step(correct_perspective, result, "correct_perspective")
    result = _safe_step(deskew, result, "deskew")
    result = _safe_step(denoise_and_enhance, result, "denoise_and_enhance")

    return result


def _safe_step(fn, image: np.ndarray, step_name: str) -> np.ndarray:
    """Runs one preprocessing step; on failure, logs and returns the
    input image unchanged so a single bad step doesn't break the whole
    request."""
    try:
        return fn(image)
    except Exception as e:
        logger.warning(f"Preprocessing step '{step_name}' failed, skipping it: {e}")
        return image
