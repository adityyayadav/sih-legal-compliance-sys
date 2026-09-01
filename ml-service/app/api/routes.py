import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.api.schemas import ComplianceReportResponse, HealthResponse

# Dynamic imports from your previously implemented phases
from app.utils.image_io import load_image  # Utility to convert UploadFile to np.ndarray
from app.preprocessing.pipeline import preprocess
from app.detection.text_detector import detect_text_regions
from app.ocr.ocr_engine import run_ocr
from app.extraction.field_extractor import extract_fields
# Assuming Phase 7 implemented a main analysis function:
from app.font_analysis.font_measure import analyze_fonts 
from app.compliance.rule_engine import check_compliance
from app.compliance.report_builder import build_report

router = APIRouter()

def load_rules_config() -> dict:
    """Loads the Phase 1 rule matrix."""
    try:
        with open("app/compliance/rules_config.json", "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Rules configuration missing or invalid.")

@router.post("/analyze", response_model=ComplianceReportResponse)
async def analyze(
    images: List[UploadFile] = File(...), 
    product_id: Optional[str] = Form(None)
):
    """
    Main POST endpoint for the AI module as defined in Section 2.
    """
    try:
        # 1. Load Rules Config (Phase 1)
        rules_config = load_rules_config()
        
        # 2. Assign or echo product_id
        current_product_id = product_id if product_id else str(uuid.uuid4())

        # 3. Load & Preprocess Images (Phase 3)
        processed_images = []
        for img in images:
            # Check content type or filename extension to fulfill API contract error
            content_type = getattr(img, "content_type", "") or ""
            filename = (getattr(img, "filename", "") or "").lower()
            valid_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")
            
            if not content_type.startswith("image/") and not filename.endswith(valid_extensions):
                raise HTTPException(status_code=400, detail="INVALID_IMAGE")
            
            raw_img_array = await load_image(img) 
            processed_images.append(preprocess(raw_img_array))

        # 4. Text Detection (Phase 4)
        regions_per_image = [detect_text_regions(img) for img in processed_images]

        # 5. OCR Recognition (Phase 5)
        # Flatten regions into a single list of OCR results
        ocr_results = [run_ocr(r) for region_set in regions_per_image for r in region_set]

        # 6. Extraction (Phase 6)
        declarations = extract_fields(ocr_results, rules_config)

        # 7. Font Analysis (Phase 7)
        font_analysis = analyze_fonts(regions_per_image, rules_config)

        # 8. Compliance Engine (Phase 8)
        violations = check_compliance(declarations, font_analysis, rules_config)

        # 9. Build Report (Phase 8/9)
        final_report = build_report(current_product_id, declarations, font_analysis, violations)
        
        return final_report

    except HTTPException as he:
        # Re-raise known HTTP exceptions (like INVALID_IMAGE)
        raise he
    except Exception as e:
        # Return 5xx as defined in the API contract for processing failures
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint from API Contract."""
    return {"status": "ok", "model_version": "v1.2"}

@router.get("/rules")
async def get_rules():
    """Returns the current rules_config.json to the dashboard."""
    return load_rules_config()