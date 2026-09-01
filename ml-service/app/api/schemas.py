from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ConfidenceFlags(BaseModel):
    needs_manual_review: bool
    low_confidence_fields: List[str]

class ComplianceReportResponse(BaseModel):
    product_id: Optional[str]
    status: str
    processed_at: str
    declarations: Dict[str, Any]
    font_analysis: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    overall_compliance_status: str
    confidence_flags: ConfidenceFlags

class ErrorResponse(BaseModel):
    status: str
    error_code: str
    message: str

class HealthResponse(BaseModel):
    status: str
    model_version: str