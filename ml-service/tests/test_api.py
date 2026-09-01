import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_rules():
    return {"declarations": [{"field": "net_quantity", "mandatory": True}]}

@pytest.fixture
def mock_report():
    return {
        "product_id": "test-123",
        "status": "SUCCESS",
        "processed_at": "2026-08-26T10:00:00Z",
        "declarations": {"net_quantity": {"present": True, "value": "500 g"}},
        "font_analysis": [],
        "violations": [],
        "overall_compliance_status": "COMPLIANT",
        "confidence_flags": {"needs_manual_review": False, "low_confidence_fields": []}
    }

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_version": "v1.2"}

@patch("app.api.routes.load_rules_config")
def test_rules_endpoint(mock_load_rules, mock_rules):
    mock_load_rules.return_value = mock_rules
    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    assert response.json() == mock_rules

@patch("app.api.routes.load_rules_config")
@patch("app.api.routes.load_image")
@patch("app.api.routes.preprocess")
@patch("app.api.routes.detect_text_regions")
@patch("app.api.routes.run_ocr")
@patch("app.api.routes.extract_fields")
@patch("app.api.routes.analyze_fonts")
@patch("app.api.routes.check_compliance")
@patch("app.api.routes.build_report")
def test_analyze_endpoint_success(
    mock_build_report, mock_check_compliance, mock_analyze_fonts, 
    mock_extract_fields, mock_run_ocr, mock_detect, mock_preprocess, 
    mock_load_image, mock_load_rules, mock_rules, mock_report
):
    # Setup Mocks
    mock_load_rules.return_value = mock_rules
    mock_build_report.return_value = mock_report
    mock_detect.return_value = [{"bbox": [0,0,10,10], "crop": "mock_array"}] # Mocking 1 region

    # Create dummy image file for upload
    file_data = {"images": ("test_image.jpg", b"dummy_image_bytes", "image/jpeg")}
    form_data = {"product_id": "test-123"}

    response = client.post("/api/v1/analyze", files=file_data, data=form_data)

    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert response.json()["product_id"] == "test-123"
    
    # Verify the pipeline chain was called
    mock_preprocess.assert_called()
    mock_detect.assert_called()
    mock_extract_fields.assert_called()
    mock_build_report.assert_called()

def test_analyze_endpoint_invalid_file_type():
    # Provide a text file instead of an image
    file_data = {"images": ("test.txt", b"not an image", "text/plain")}
    response = client.post("/api/v1/analyze", files=file_data)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "INVALID_IMAGE"