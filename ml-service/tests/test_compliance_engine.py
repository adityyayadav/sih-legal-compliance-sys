# tests/test_compliance_engine.py
import pytest
from app.compliance.rule_engine import check_compliance

# You can load this directly from your actual JSON file in production tests
@pytest.fixture
def advanced_rules_config():
    """Mock subset of the provided advanced JSON for isolated testing."""
    return {
        "declarations": [
            {
                "field": "manufacturer_or_packer_or_importer_name_address",
                "rule_ref": "Rule 6(1)(a)",
                "mandatory": True,
                "required_keywords_any": ["Mfg", "Manufactured", "Packed"]
            },
            {
                "field": "mrp",
                "rule_ref": "Rule 6(1)(e)",
                "mandatory": True,
                "must_contain_phrase_any": ["incl. of all taxes", "inclusive of all taxes"]
            },
            {
                "field": "net_quantity",
                "rule_ref": "Rule 6(1)(c)",
                "mandatory": True
            }
        ],
        "prohibited_declarations": {
            "disallowed_quantity_terms": ["approx", "about"]
        },
        "severity_levels": {
            "CRITICAL": ["net_quantity", "mrp", "manufacturer_or_packer_or_importer_name_address"],
            "MAJOR": ["consumer_care_details"]
        }
    }

def test_missing_mandatory_flags_critical(advanced_rules_config):
    """Tests that a missing MRP correctly assigns a CRITICAL severity."""
    declarations = {
        "net_quantity": {"present": True, "value": "500g"},
        "mrp": {"present": False, "value": None}
    }
    
    violations = check_compliance(declarations, [], advanced_rules_config)
    
    assert len(violations) > 0
    mrp_violation = next(v for v in violations if v["field"] == "mrp")
    assert mrp_violation["severity"] == "CRITICAL"
    assert "missing" in mrp_violation["issue"].lower()

def test_prohibited_terms_violation(advanced_rules_config):
    """Tests that vague terms like 'approx' are flagged."""
    declarations = {
        "net_quantity": {"present": True, "value": "approx 500g"}
    }
    
    violations = check_compliance(declarations, [], advanced_rules_config)
    net_qty_violation = next((v for v in violations if v["field"] == "net_quantity"), None)
    
    assert net_qty_violation is not None
    assert "prohibited vague quantity terms" in net_qty_violation["issue"].lower()

def test_required_keywords_any(advanced_rules_config):
    """Tests that the manufacturer block requires specific keywords."""
    declarations = {
        "manufacturer_or_packer_or_importer_name_address": {
            "present": True,
            "value": "ABC Foods Ltd, Pune" # Missing 'Mfg' or 'Packed'
        }
    }
    
    violations = check_compliance(declarations, [], advanced_rules_config)
    mfg_violation = next((v for v in violations if v["field"] == "manufacturer_or_packer_or_importer_name_address"), None)
    
    assert mfg_violation is not None
    assert "keyword" in mfg_violation["issue"].lower()