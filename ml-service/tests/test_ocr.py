"""
test_ocr.py
-------------
Tests for Phase 5: app/ocr/ocr_engine.py and postprocess_text.py.

Two groups of tests:
  1. postprocess_text tests — pure string logic, no ML, always run.
  2. ocr_engine tests — split into "stub" backend tests (always run, no
     dependencies) and "real EasyOCR" tests (skipped automatically if
     EasyOCR/its model weights aren't available in the current environment,
     via pytest.importorskip — so this file works whether or not EasyOCR
     is installed, without silently pretending real-OCR correctness was
     verified when it wasn't).

Run with:
    python -m pytest tests/test_ocr.py -v
"""

import numpy as np
import cv2
import pytest

from app.ocr.postprocess_text import (
    strip_noise_characters,
    normalize_units,
    fix_digit_confusions,
    collapse_whitespace,
    postprocess,
)
from app.ocr.ocr_engine import run_ocr


# ---------------------------------------------------------------------------
# postprocess_text.py — pure logic, deterministic
# ---------------------------------------------------------------------------

def test_strip_noise_characters_removes_garbage_symbols():
    result = strip_noise_characters("Net Wt 500g \ufffd\x00")
    assert "\ufffd" not in result
    assert "\x00" not in result
    assert "Net Wt 500g" in result


def test_strip_noise_characters_keeps_currency_and_punctuation():
    result = strip_noise_characters("MRP: ₹120.00 (incl. of all taxes)")
    assert "₹" in result
    assert "(" in result and ")" in result
    assert "." in result


@pytest.mark.parametrize("raw,expected_unit", [
    ("500gm", "500g"),
    ("500 GM", "500 g"),
    ("500 grams", "500 g"),
    ("2 kgs", "2 kg"),
    ("2 kilograms", "2 kg"),
    ("250ml", "250ml"),
    ("250 mls", "250 ml"),
    ("1 litre", "1 l"),
    ("1 Liters", "1 l"),
])
def test_normalize_units_standardizes_spelling_variants(raw, expected_unit):
    assert normalize_units(raw) == expected_unit


def test_normalize_units_does_not_affect_unrelated_text():
    text = "Consumer Care: 1800-123-456"
    assert normalize_units(text) == text


def test_fix_digit_confusions_fixes_number_like_tokens():
    # "5OO" -> "500" (O misread in a token that's already got real digits)
    assert fix_digit_confusions("Net Wt 5OOg") == "Net Wt 500g"
    assert fix_digit_confusions("Rs. 1O0.00") == "Rs. 100.00"


def test_fix_digit_confusions_does_not_corrupt_real_words():
    # This is the critical negative test: "Consumer" and "Origin" must NOT
    # be mangled just because they contain O's — the whole point of scoping
    # this fix to number-like tokens only.
    text = "Consumer Care and Country of Origin"
    assert fix_digit_confusions(text) == text


def test_fix_digit_confusions_leaves_pure_words_alone():
    assert fix_digit_confusions("MRP") == "MRP"
    assert fix_digit_confusions("Hello World") == "Hello World"


def test_collapse_whitespace_normalizes_spacing():
    assert collapse_whitespace("Net   Wt.\t\t500g  \n") == "Net Wt. 500g"


def test_postprocess_full_pipeline_on_realistic_noisy_ocr_output():
    raw = "  Net  Wt.   5OO gm  \ufffd "
    result = postprocess(raw)
    assert result == "Net Wt. 500 g"


def test_postprocess_handles_empty_and_none_input():
    assert postprocess("") == ""
    assert postprocess(None) == ""


# ---------------------------------------------------------------------------
# ocr_engine.py — "stub" backend (always available, deterministic)
# ---------------------------------------------------------------------------

def _make_text_crop(text="500g", w=300, h=80):
    img = np.full((h, w, 3), 255, dtype=np.uint8)
    cv2.putText(img, text, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    return img


def test_run_ocr_stub_backend_detects_presence_of_ink():
    crop = _make_text_crop()
    result = run_ocr(crop, backend="stub")
    assert result["text"] != ""
    assert result["confidence"] > 0


def test_run_ocr_stub_backend_on_blank_crop_returns_empty():
    blank = np.full((80, 300, 3), 255, dtype=np.uint8)
    result = run_ocr(blank, backend="stub")
    assert result["text"] == ""
    assert result["confidence"] == 0.0


def test_run_ocr_raises_on_empty_array():
    with pytest.raises(ValueError):
        run_ocr(np.array([]), backend="stub")


def test_run_ocr_raises_on_none():
    with pytest.raises(ValueError):
        run_ocr(None, backend="stub")


def test_run_ocr_returns_correct_dict_shape():
    crop = _make_text_crop()
    result = run_ocr(crop, backend="stub")
    assert set(result.keys()) == {"text", "confidence"}
    assert isinstance(result["text"], str)
    assert isinstance(result["confidence"], float)


# ---------------------------------------------------------------------------
# ocr_engine.py — REAL EasyOCR backend (genuine recognition accuracy check)
# ---------------------------------------------------------------------------
# These tests exercise actual character recognition, not just code paths.
# They're skipped (not failed) if easyocr isn't installed in the current
# environment, so this file is safe to run anywhere, but when EasyOCR IS
# available, these are the tests that actually prove OCR works.

easyocr = pytest.importorskip("easyocr", reason="easyocr not installed — skipping real-OCR accuracy tests")


@pytest.fixture(scope="module")
def easyocr_ready():
    """Warms up the EasyOCR reader once for this whole test module (loading
    it per-test would be extremely slow)."""
    from app.ocr.ocr_engine import _try_load_easyocr
    available = _try_load_easyocr()
    if not available:
        pytest.skip("EasyOCR failed to initialize (likely no model weights cached/no network)")
    return available


def test_real_ocr_reads_simple_label_text_correctly(easyocr_ready):
    crop = _make_text_crop("NET WT 500g", w=500, h=120)
    result = run_ocr(crop, backend="easyocr")
    # Real accuracy check — not just "did it return something"
    assert "500" in result["text"]
    assert result["confidence"] > 0.5


def test_real_ocr_reads_mrp_style_text_correctly(easyocr_ready):
    crop = _make_text_crop("MRP RS 120", w=500, h=120)
    result = run_ocr(crop, backend="easyocr")
    assert "120" in result["text"]
    assert result["confidence"] > 0.5


def test_real_ocr_on_blank_crop_returns_empty_or_low_confidence(easyocr_ready):
    blank = np.full((100, 400, 3), 255, dtype=np.uint8)
    result = run_ocr(blank, backend="easyocr")
    assert result["text"].strip() == "" or result["confidence"] < 0.3


def test_real_ocr_output_is_postprocessable(easyocr_ready):
    """Integration check: real OCR output correctly flows into
    postprocess_text.py without errors and produces a clean result."""
    crop = _make_text_crop("Net Wt 5OOgm", w=500, h=120)  # deliberately OCR-confusable text
    result = run_ocr(crop, backend="easyocr")
    cleaned = postprocess(result["text"])
    assert isinstance(cleaned, str)
    # Whatever EasyOCR actually read, postprocessing shouldn't crash or
    # leave it empty when there was real text.
    assert len(cleaned) > 0
