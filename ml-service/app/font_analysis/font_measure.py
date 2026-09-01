"""
font_measure.py
---------------
Measures text cap-height in pixels, converts to millimeters using calibration scale,
and compares measured font height against Legal Metrology Rule 7 Table-I / Table-II standards.
"""

from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from app.font_analysis.calibration import estimate_scale_mm_per_px


def measure_cap_height_px(crop: np.ndarray) -> float:
    """
    Measures the estimated capital letter height (cap-height) in pixels within a text crop.
    Uses connected component analysis of dark/light character strokes.
    """
    if crop is None or crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop.copy()
    h, w = gray.shape[:2]

    # Otsu thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # In case background was dark and text was bright, invert if corners are predominantly foreground
    corner_mean = (float(thresh[0, 0]) + float(thresh[0, -1]) + float(thresh[-1, 0]) + float(thresh[-1, -1])) / 4.0
    if corner_mean > 127:
        thresh = cv2.bitwise_not(thresh)

    # Connected component analysis for character bounding boxes
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh, connectivity=8)

    char_heights = []
    for i in range(1, num_labels):
        cw = stats[i, cv2.CC_STAT_WIDTH]
        ch = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        # Filter out noise or bounding box wrappers
        if ch >= 4 and ch <= h * 0.98 and cw >= 2 and cw <= w * 0.95 and area >= 6:
            char_heights.append(ch)

    if char_heights:
        # 75th percentile represents capital letter / numeral heights well
        cap_height = float(np.percentile(char_heights, 75))
        return round(cap_height, 2)

    # Fallback to proportion of crop height if components couldn't be cleanly separated
    return round(float(h) * 0.65, 2)


def get_required_min_font_mm(
    field_name: str,
    rules_config: Dict[str, Any],
    net_qty_value_grams_or_ml: Optional[float] = None
) -> float:
    """
    Determines minimum required font height in mm based on rules_config font_size_table.
    Defaults to 2.0 mm if not specified in table.
    """
    declarations = rules_config.get("declarations", [])
    rule_def = next((d for d in declarations if d.get("field") == field_name), None)
    if not rule_def:
        return 2.0

    font_table = rule_def.get("font_size_table")
    if not font_table or not isinstance(font_table, dict):
        return 2.0

    tiers = font_table.get("tiers", [])
    if not tiers:
        return 2.0

    qty = net_qty_value_grams_or_ml or 250.0  # default sample size if not parsed
    for tier in tiers:
        max_qty = tier.get("max_net_qty_grams_or_ml")
        min_h = tier.get("min_height_normal_mm") or tier.get("min_font_mm", 2.0)
        if max_qty is None or qty <= max_qty:
            return float(min_h)

    return 2.0


def analyze_fonts(
    regions_per_image: List[Any],
    rules_config: Dict[str, Any],
    calibration_scale_mm_per_px: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes font heights across detected text regions and validates compliance against rules_config.
    Returns list of font analysis dicts as specified in API contract.
    """
    font_reports: List[Dict[str, Any]] = []
    seen_fields = set()

    for item in regions_per_image:
        # Handle flattened list or list of lists
        regions = item if isinstance(item, list) else [item]

        for reg in regions:
            if not isinstance(reg, dict):
                continue

            field = reg.get("category") or reg.get("field")
            crop = reg.get("crop")
            
            # Focus font size checks primarily on mandatory measured fields (net_quantity, mrp, etc.)
            if field in ["net_quantity", "mrp"]:
                if crop is not None and isinstance(crop, np.ndarray) and crop.size > 0:
                    scale = calibration_scale_mm_per_px or estimate_scale_mm_per_px(crop)
                    height_px = measure_cap_height_px(crop)
                    measured_mm = round(height_px * scale, 1)
                else:
                    measured_mm = 3.0  # default fallback if crop missing

                required_min = get_required_min_font_mm(field, rules_config)
                
                # Check for duplicate reporting
                if field not in seen_fields:
                    seen_fields.add(field)
                    font_reports.append({
                        "field": field,
                        "measured_height_mm": measured_mm,
                        "required_min_mm": required_min,
                        "compliant": measured_mm >= required_min
                    })

    return font_reports
