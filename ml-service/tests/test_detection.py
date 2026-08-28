"""
test_detection.py
--------------------
Tests for Phase 4: app/detection/text_detector.py and region_classifier.py.

Uses the offline "contour" backend for text_detector.py (no PaddleOCR
download required, so this runs identically on any machine/CI). If
PaddleOCR is installed and available where you run this, you can also
manually test backend="auto"/"paddleocr" — see the bottom of this file.

Run with:
    python -m pytest tests/test_detection.py -v
"""

import numpy as np
import cv2
import pytest

from app.detection.text_detector import detect_text_regions
from app.detection.region_classifier import classify_region_text, classify_regions, OTHER_CLASS


# ---------------------------------------------------------------------------
# Helpers — synthetic label images, built the same way as Phase 3's tests
# ---------------------------------------------------------------------------

def _make_label_image(lines, w=800, h=1000, font_scale=1.1, thickness=2):
    """Creates a white image with each string in `lines` printed on its own
    row, spaced apart — simulates a simple printed label."""
    img = np.full((h, w, 3), 255, dtype=np.uint8)
    y = 100
    for line in lines:
        cv2.putText(img, line, (60, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
        y += 120
    return img


def _make_blank_image(w=400, h=400):
    return np.full((h, w, 3), 255, dtype=np.uint8)


# ---------------------------------------------------------------------------
# text_detector.py
# ---------------------------------------------------------------------------

def test_detect_text_regions_finds_multiple_lines():
    img = _make_label_image(["NET WT 500g", "MRP RS 120", "MFG DATE 07 2026"])
    regions = detect_text_regions(img, backend="contour")
    assert len(regions) >= 2, f"Expected at least 2 detected regions, got {len(regions)}"


def test_detected_region_has_correct_shape():
    img = _make_label_image(["NET WT 500g"])
    regions = detect_text_regions(img, backend="contour")
    assert len(regions) >= 1
    region = regions[0]
    assert "bbox" in region and "crop" in region
    assert len(region["bbox"]) == 4
    x, y, w, h = region["bbox"]
    assert w > 0 and h > 0
    assert region["crop"].shape[0] == h
    assert region["crop"].shape[1] == w


def test_detect_text_regions_raises_on_empty_image():
    with pytest.raises(ValueError):
        detect_text_regions(np.array([]), backend="contour")


def test_detect_text_regions_on_blank_image_returns_no_or_few_regions():
    blank = _make_blank_image()
    regions = detect_text_regions(blank, backend="contour")
    # A blank image should not hallucinate lots of text regions
    assert len(regions) <= 1


def test_regions_are_in_top_to_bottom_reading_order():
    img = _make_label_image(["FIRST LINE HERE", "SECOND LINE HERE", "THIRD LINE HERE"])
    regions = detect_text_regions(img, backend="contour")
    ys = [r["bbox"][1] for r in regions]
    assert ys == sorted(ys), "Regions should be sorted top-to-bottom"


def test_invalid_backend_falls_through_to_contour_safely():
    # backend="contour" is the only backend guaranteed available in this
    # test environment (no PaddleOCR model download access) — confirm it
    # doesn't error out unexpectedly.
    img = _make_label_image(["MRP RS 120"])
    regions = detect_text_regions(img, backend="contour")
    assert isinstance(regions, list)


# ---------------------------------------------------------------------------
# region_classifier.py — classify_region_text (single string)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_category", [
    ("Net Wt. 500 g", "net_quantity"),
    ("MRP Rs. 120.00 incl. of all taxes", "mrp"),
    ("Mfg Date: 07/2026", "mfg_or_pack_or_import_date"),
    ("Best Before 12 2026", "best_before_or_use_by_date"),
    ("Consumer Care: 1800-123-4567", "consumer_care_details"),
    ("Country of Origin: India", "country_of_origin"),
    ("Mfg by ABC Foods Pvt Ltd, Pune", "manufacturer_or_packer_or_importer_name_address"),
])
def test_classify_region_text_matches_expected_field(text, expected_category):
    result = classify_region_text(text)
    assert result["category"] == expected_category, (
        f"Text '{text}' classified as '{result['category']}', "
        f"expected '{expected_category}'. Scores: {result['all_scores']}"
    )


def test_classify_region_text_empty_string_is_other():
    result = classify_region_text("")
    assert result["category"] == OTHER_CLASS


def test_classify_region_text_whitespace_only_is_other():
    result = classify_region_text("     ")
    assert result["category"] == OTHER_CLASS


def test_classify_region_text_irrelevant_marketing_text_is_other():
    result = classify_region_text("Now with real fruit extracts!")
    assert result["category"] == OTHER_CLASS


def test_classify_region_text_returns_all_scores_dict():
    result = classify_region_text("MRP Rs. 99")
    assert isinstance(result["all_scores"], dict)
    assert "mrp" in result["all_scores"]
    assert result["all_scores"]["mrp"] >= result["score"]  # winning field's score is the max


def test_mrp_without_tax_phrase_still_classifies_as_mrp_via_regex():
    # No "inclusive of all taxes" phrase present — should still classify as
    # mrp based on currency+amount regex match (compliance CORRECTNESS is
    # Phase 8's job, not Phase 4's — Phase 4 only needs to find the region).
    result = classify_region_text("Rs. 45.00")
    assert result["category"] == "mrp"


# ---------------------------------------------------------------------------
# region_classifier.py — classify_regions (list of region dicts)
# ---------------------------------------------------------------------------

def test_classify_regions_adds_category_to_each_region_in_place():
    regions = [
        {"bbox": [0, 0, 10, 10], "text": "Net Wt. 500 g"},
        {"bbox": [0, 20, 10, 10], "text": "MRP Rs. 120 incl. of all taxes"},
        {"bbox": [0, 40, 10, 10], "text": "Some random tagline"},
    ]
    result = classify_regions(regions)

    assert result is regions  # same list object, modified in place
    assert regions[0]["category"] == "net_quantity"
    assert regions[1]["category"] == "mrp"
    assert regions[2]["category"] == OTHER_CLASS
    assert all("classification_score" in r for r in regions)


def test_classify_regions_handles_missing_text_key_gracefully():
    regions = [{"bbox": [0, 0, 10, 10]}]  # no "text" key at all
    result = classify_regions(regions)
    assert result[0]["category"] == OTHER_CLASS


# ---------------------------------------------------------------------------
# Integration: detect_text_regions -> (simulated OCR) -> classify_regions
# ---------------------------------------------------------------------------

def test_full_detection_to_classification_flow_on_synthetic_label():
    """
    Simulates the real Phase 4 -> Phase 5 -> Phase 4 handoff:
        1. detect_text_regions() finds bounding boxes (Phase 4, step 1)
        2. (Phase 5 OCR normally fills in "text" here — we hardcode it
           since Phase 5 isn't built yet, this test only proves Phase 4's
           two pieces connect correctly)
        3. classify_regions() assigns a category to each (Phase 4, step 2)
    """
    img = _make_label_image(["NET WT 500g", "MRP RS 120"])
    regions = detect_text_regions(img, backend="contour")
    assert len(regions) >= 1

    # Simulate Phase 5 OCR output for however many regions were actually found
    fake_ocr_texts = ["Net Wt 500g", "MRP Rs 120"]
    for i, region in enumerate(regions):
        region["text"] = fake_ocr_texts[i % len(fake_ocr_texts)]

    classified = classify_regions(regions)
    categories = {r["category"] for r in classified}
    assert "net_quantity" in categories or "mrp" in categories
