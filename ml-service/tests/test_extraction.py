import pytest
from app.extraction.field_extractor import extract_fields

@pytest.fixture
def mock_rules_config():
    """Mocks the rules_config.json structure from Phase 1."""
    return {
        "declarations": [
            {
                "field": "net_quantity",
                "rule_ref": "Rule 6/7",
                "mandatory": True,
                "format_regex": r"\d+(\.\d+)?\s?(g|kg|ml|l|gm|GM|ML)"
            },
            {
                "field": "mrp",
                "rule_ref": "Rule 6(1)(e)",
                "mandatory": True,
                "format_regex": r"(Rs\.?|INR)\s?\d+(\.\d{2})?",
                "must_contain_phrase": ["incl. of all taxes", "inclusive of all taxes"]
            },
            {
                "field": "manufacturer_name_address",
                "rule_ref": "Rule 6(1)(a)",
                "mandatory": True
            }
        ]
    }

@pytest.fixture
def mock_ocr_results():
    """Mocks the output format from Phase 5 (OCR Engine)."""
    return [
        {
            "text": "Net Wt: 500 g",
            "confidence": 0.92,
            "bbox": [10, 20, 30, 40],
            "source_image_index": 0
        },
        {
            "text": "MRP Rs 120.00 (incl. of all taxes)",
            "confidence": 0.95,
            "bbox": [50, 60, 70, 80],
            "source_image_index": 0
        },
        {
            "text": "Manufactured by ABC Foods Pvt Ltd, Pune",
            "confidence": 0.88,
            "bbox": [100, 110, 120, 130],
            "source_image_index": 1
        },
        {
            "text": "Random packaging text",
            "confidence": 0.99,
            "bbox": [0, 0, 10, 10],
            "source_image_index": 0
        }
    ]

def test_extract_fields_success(mock_ocr_results, mock_rules_config):
    declarations = extract_fields(mock_ocr_results, mock_rules_config)
    
    # Assert Net Quantity
    assert declarations["net_quantity"]["present"] is True
    assert declarations["net_quantity"]["value"] == "500 g"
    assert declarations["net_quantity"]["confidence"] == 0.92
    
    # Assert MRP (Checking regex and must_contain_phrase)
    assert declarations["mrp"]["present"] is True
    assert declarations["mrp"]["value"] == "Rs 120.00"
    
    # Assert NER/Manufacturer
    assert declarations["manufacturer_name_address"]["present"] is True
    assert "ABC Foods Pvt Ltd" in declarations["manufacturer_name_address"]["value"]
    assert declarations["manufacturer_name_address"]["source_image_index"] == 1

def test_extract_fields_missing_data(mock_rules_config):
    empty_ocr = []
    declarations = extract_fields(empty_ocr, mock_rules_config)
    
    assert declarations["net_quantity"]["present"] is False
    assert declarations["net_quantity"]["value"] is None
    assert declarations["mrp"]["present"] is False

def test_mrp_missing_required_phrase(mock_rules_config):
    ocr_results = [
        {
            "text": "MRP Rs 120.00", # Missing "incl. of all taxes"
            "confidence": 0.95,
            "bbox": [50, 60, 70, 80],
            "source_image_index": 0
        }
    ]
    declarations = extract_fields(ocr_results, mock_rules_config)
    assert declarations["mrp"]["present"] is False