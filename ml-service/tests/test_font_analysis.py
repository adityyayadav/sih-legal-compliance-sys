import cv2
import numpy as np
import pytest

from app.font_analysis.calibration import estimate_scale_mm_per_px, detect_barcode_bbox
from app.font_analysis.readability import calculate_contrast_ratio, check_readability
from app.font_analysis.font_measure import (
    measure_cap_height_px,
    get_required_min_font_mm,
    analyze_fonts
)


@pytest.fixture
def mock_rules_config():
    return {
        "declarations": [
            {
                "field": "net_quantity",
                "font_size_table": {
                    "tiers": [
                        {"max_net_qty_grams_or_ml": 200, "min_height_normal_mm": 2.0},
                        {"max_net_qty_grams_or_ml": 500, "min_height_normal_mm": 4.0},
                        {"max_net_qty_grams_or_ml": None, "min_height_normal_mm": 6.0}
                    ]
                }
            },
            {
                "field": "mrp",
                "font_size_table": {
                    "tiers": [
                        {"max_net_qty_grams_or_ml": None, "min_height_normal_mm": 2.0}
                    ]
                }
            }
        ]
    }


def create_synthetic_text_crop(text="500 g", font_scale=1.5, thickness=2, bg_val=255, fg_val=0):
    img = np.ones((60, 200, 3), dtype=np.uint8) * bg_val
    cv2.putText(img, text, (15, 45), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (fg_val, fg_val, fg_val), thickness)
    return img


def test_measure_cap_height_positive():
    crop = create_synthetic_text_crop("500 g", font_scale=1.2, thickness=2)
    h_px = measure_cap_height_px(crop)
    assert h_px > 10
    assert h_px <= 60


def test_measure_cap_height_empty_crop():
    empty = np.array([], dtype=np.uint8)
    assert measure_cap_height_px(empty) == 0.0


def test_calibration_fallback():
    dummy = np.ones((100, 100, 3), dtype=np.uint8) * 255
    scale = estimate_scale_mm_per_px(dummy)
    assert scale > 0
    assert 0.02 <= scale <= 1.5


def test_contrast_ratio_high_contrast():
    high_contrast = create_synthetic_text_crop("TEST", bg_val=255, fg_val=0)
    ratio = calculate_contrast_ratio(high_contrast)
    assert ratio > 4.5  # High contrast


def test_contrast_ratio_low_contrast():
    low_contrast = create_synthetic_text_crop("TEST", bg_val=130, fg_val=125)
    readability = check_readability(low_contrast)
    assert readability["is_readable"] is False


def test_get_required_min_font_mm(mock_rules_config):
    # Tier 1: <= 200g -> 2.0mm
    req1 = get_required_min_font_mm("net_quantity", mock_rules_config, net_qty_value_grams_or_ml=150)
    assert req1 == 2.0

    # Tier 2: <= 500g -> 4.0mm
    req2 = get_required_min_font_mm("net_quantity", mock_rules_config, net_qty_value_grams_or_ml=450)
    assert req2 == 4.0

    # Tier 3: > 500g -> 6.0mm
    req3 = get_required_min_font_mm("net_quantity", mock_rules_config, net_qty_value_grams_or_ml=1000)
    assert req3 == 6.0


def test_analyze_fonts_integration(mock_rules_config):
    crop = create_synthetic_text_crop("Net Wt. 500g", font_scale=1.5, thickness=2)
    regions = [
        {"category": "net_quantity", "crop": crop, "bbox": [10, 10, 200, 60]},
        {"category": "mrp", "crop": crop, "bbox": [10, 80, 200, 60]}
    ]

    report = analyze_fonts([regions], mock_rules_config, calibration_scale_mm_per_px=0.2)
    assert len(report) == 2
    fields = [r["field"] for r in report]
    assert "net_quantity" in fields
    assert "mrp" in fields
    assert all("measured_height_mm" in r and "required_min_mm" in r and "compliant" in r for r in report)
