# app/compliance/report_builder.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


def build_report(
    product_id: Optional[str],
    declarations: Dict[str, Any],
    font_analysis: List[Dict[str, Any]],
    violations: List[Dict[str, Any]],
    confidence_threshold: float = 0.85
) -> Dict[str, Any]:
    """
    Assembles the final API CONTRACT response JSON.
    Computes overall status, confidence flags, and ISO 8601 timestamp.
    """
    # 1. Ensure product_id exists
    resolved_product_id = product_id if product_id and str(product_id).strip() else str(uuid.uuid4())

    # 2. Identify low confidence fields
    low_confidence_fields: List[str] = []
    for field_name, field_data in declarations.items():
        if isinstance(field_data, dict) and field_data.get("present", False):
            conf = field_data.get("confidence", 0.0)
            if conf < confidence_threshold:
                low_confidence_fields.append(field_name)

    # 3. Determine compliance and review triggers
    is_compliant = len(violations) == 0
    overall_status = "COMPLIANT" if is_compliant else "NON COMPLIANT"
    needs_manual_review = (len(low_confidence_fields) > 0) or (not is_compliant)

    # 4. Assemble response following Section 2 API contract
    return {
        "product_id": resolved_product_id,
        "status": "SUCCESS",
        "processed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "declarations": declarations,
        "font_analysis": font_analysis,
        "violations": violations,
        "overall_compliance_status": overall_status,
        "confidence_flags": {
            "needs_manual_review": needs_manual_review,
            "low_confidence_fields": low_confidence_fields
        }
    }