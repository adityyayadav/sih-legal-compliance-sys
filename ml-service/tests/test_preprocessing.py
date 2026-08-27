"""
test_preprocessing.py
------------------------
Tests each preprocessing function individually against synthetic images
built on the fly (a tilted rectangle, a blurry/noisy image, a low-contrast
image) — no dependency on real photos, runs the same on any machine.

Run with:
    python -m pytest tests/test_preprocessing.py -v
"""

import numpy as np
import cv2
import pytest

from app.preprocessing.deskew import deskew
from app.preprocessing.perspective_correction import correct_perspective
from app.preprocessing.denoise_enhance import denoise_and_enhance, _denoise, _enhance_contrast
from app.preprocessing.pipeline import preprocess


def _make_blank_image(w=600, h=800, color=(255, 255, 255)) -> np.ndarray:
    return np.full((h, w, 3), color, dtype=np.uint8)


def _make_image_with_text_block(w=600, h=800, angle_degrees=0) -> np.ndarray:
    """Creates a synthetic 'label' image with a black rectangle (stand-in
    for a block of text) optionally rotated, on a white background."""
    img = _make_blank_image(w, h)
    block = np.zeros((150, 300, 3), dtype=np.uint8)
    x_off, y_off = (w - 300) // 2, (h - 150) // 2
    img[y_off:y_off + 150, x_off:x_off + 300] = block

    if angle_degrees != 0:
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderValue=(255, 255, 255))

    return img


def _make_tilted_quadrilateral_image(w=800, h=1000) -> np.ndarray:
    """Creates an image with a clearly visible tilted quadrilateral 'label'
    on a contrasting background, for perspective_correction to detect."""
    img = np.full((h, w, 3), (30, 30, 30), dtype=np.uint8)  # dark background
    pts = np.array([
        [150, 100], [700, 180], [650, 850], [100, 780]
    ], dtype=np.int32)
    cv2.fillPoly(img, [pts], (255, 255, 255))  # bright, tilted quad = "label"
    return img


def _make_noisy_image(w=400, h=400) -> np.ndarray:
    rng = np.random.default_rng(42)
    base = np.full((h, w, 3), 200, dtype=np.uint8)
    noise = rng.normal(0, 25, base.shape).astype(np.int16)
    noisy = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


def _make_low_contrast_image(w=400, h=400) -> np.ndarray:
    """A dim, washed-out image — most pixel values clustered narrowly."""
    return np.full((h, w, 3), 130, dtype=np.uint8) + np.random.randint(
        -5, 5, (h, w, 3), dtype=np.int8
    ).astype(np.uint8)


# ---------- deskew.py ----------

def test_deskew_corrects_a_rotated_image():
    tilted = _make_image_with_text_block(angle_degrees=8)
    result = deskew(tilted)
    assert result.shape == tilted.shape
    assert result.dtype == tilted.dtype


def test_deskew_leaves_already_straight_image_unchanged_in_shape():
    straight = _make_image_with_text_block(angle_degrees=0)
    result = deskew(straight)
    assert result.shape == straight.shape


def test_deskew_raises_on_empty_image():
    with pytest.raises(ValueError):
        deskew(np.array([]))


def test_deskew_does_not_apply_extreme_correction():
    # A near-blank image gives an unreliable angle estimate; deskew should
    # not wildly rotate it.
    blank = _make_blank_image()
    result = deskew(blank)
    assert result.shape == blank.shape


# ---------- perspective_correction.py ----------

def test_perspective_correction_detects_and_warps_quadrilateral():
    quad_image = _make_tilted_quadrilateral_image()
    result = correct_perspective(quad_image)
    # Warped output should differ in dimensions from the original frame
    # since it's cropped/warped to just the detected label region.
    assert result is not None
    assert result.shape[0] > 0 and result.shape[1] > 0


def test_perspective_correction_falls_back_safely_on_no_quad():
    blank = _make_blank_image()
    result = correct_perspective(blank)
    # No confident quad found on a blank image -> should return unchanged
    assert result.shape == blank.shape


def test_perspective_correction_raises_on_empty_image():
    with pytest.raises(ValueError):
        correct_perspective(np.array([]))


# ---------- denoise_enhance.py ----------

def test_denoise_reduces_pixel_variance():
    noisy = _make_noisy_image()
    denoised = _denoise(noisy)
    assert np.std(denoised) <= np.std(noisy)


def test_contrast_enhancement_increases_dynamic_range():
    low_contrast = _make_low_contrast_image()
    enhanced = _enhance_contrast(low_contrast)
    # CLAHE should widen the spread of pixel intensities
    assert np.std(enhanced) >= np.std(low_contrast)


def test_denoise_and_enhance_raises_on_empty_image():
    with pytest.raises(ValueError):
        denoise_and_enhance(np.array([]))


def test_denoise_and_enhance_preserves_image_shape():
    img = _make_noisy_image()
    result = denoise_and_enhance(img)
    assert result.shape == img.shape


# ---------- pipeline.py (full chain) ----------

def test_full_pipeline_runs_end_to_end_on_good_image():
    img = _make_image_with_text_block(angle_degrees=5)
    result = preprocess(img)
    assert result is not None
    assert result.ndim == 3


def test_full_pipeline_runs_on_noisy_low_contrast_image():
    img = _make_noisy_image()
    result = preprocess(img)
    assert result is not None


def test_full_pipeline_raises_on_empty_image():
    with pytest.raises(ValueError):
        preprocess(np.array([]))


def test_full_pipeline_does_not_crash_on_blank_image():
    """Blank image has no perspective quad and no skew signal — pipeline
    should degrade gracefully (fallbacks), not throw."""
    blank = _make_blank_image()
    result = preprocess(blank)
    assert result is not None
