# app/compliance/rule_engine.py
from typing import Any, Dict, List, Optional
import re

def _get_severity(field_name: str, severity_config: Dict[str, List[str]]) -> str:
    """Determines the severity level of a violation based on the rules_config."""
    for level, fields in severity_config.items():
        if isinstance(fields, list) and field_name in fields:
            return level
    return "MINOR"  # Default fallback

def _check_mandatory(
    field_name: str, 
    field_data: Dict[str, Any], 
    rule_def: Dict[str, Any],
    severity: str
) -> Optional[Dict[str, str]]:
    """Checks if a mandatory field is missing."""
    # Note: Advanced applicability (e.g., 'imported_goods_only') can be evaluated here 
    # if product context is passed. For now, we rely on the strict 'mandatory' boolean.
    is_mandatory = rule_def.get("mandatory", False)
    is_present = field_data.get("present", False)
    value = field_data.get("value")

    if is_mandatory and (not is_present or value is None or str(value).strip() == ""):
        return {
            "rule_ref": rule_def.get("rule_ref", "Unknown Rule"),
            "field": field_name,
            "issue": f"Mandatory declaration '{rule_def.get('display_name', field_name)}' is missing",
            "severity": severity
        }
    return None

def _check_phrases_and_keywords(
    field_name: str, 
    field_data: Dict[str, Any], 
    rule_def: Dict[str, Any],
    severity: str
) -> Optional[Dict[str, str]]:
    """Checks for required phrases (like taxes) or keywords (like 'Mfg')."""
    if not field_data.get("present", False) or not field_data.get("value"):
        return None

    raw_value = str(field_data.get("value", "")).lower()
    
    # Check 'must_contain_phrase_any' (e.g., for MRP)
    phrases = rule_def.get("must_contain_phrase_any", [])
    if phrases and not any(p.lower() in raw_value for p in phrases):
        return {
            "rule_ref": str(rule_def.get("rule_ref", "PCR Rule")),
            "field": field_name,
            "issue": f"Missing mandatory phrase. Must contain one of: {phrases}",
            "severity": severity
        }

    # Check 'required_keywords_any' (e.g., for Manufacturer)
    keywords = rule_def.get("required_keywords_any", [])
    if keywords and not any(k.lower() in raw_value for k in keywords):
        return {
            "rule_ref": str(rule_def.get("rule_ref", "PCR Rule")),
            "field": field_name,
            "issue": f"Missing required keyword. Must contain one of: {keywords}",
            "severity": severity
        }
        
    return None

def _check_format_regex(
    field_name: str, 
    field_data: Dict[str, Any], 
    rule_def: Dict[str, Any],
    severity: str
) -> Optional[Dict[str, str]]:
    """Validates the extracted value against the specified format_regex."""
    pattern = rule_def.get("format_regex")
    if not pattern or not field_data.get("present", False) or not field_data.get("value"):
        return None

    if not re.search(pattern, str(field_data.get("value", "")), re.IGNORECASE):
        return {
            "rule_ref": str(rule_def.get("rule_ref", "PCR Rule")),
            "field": field_name,
            "issue": "Format does not match legal metrology standard patterns",
            "severity": severity
        }
    return None

def _check_prohibited_terms(
    field_name: str, 
    field_data: Dict[str, Any], 
    prohibited_config: Dict[str, Any]
) -> Optional[Dict[str, str]]:
    """Flags prohibited vague quantity terms if they appear in the net_quantity field."""
    if field_name != "net_quantity" or not field_data.get("present"):
        return None

    raw_value = str(field_data.get("value", "")).lower()
    disallowed_terms = prohibited_config.get("disallowed_quantity_terms", [])
    
    found_terms = [term for term in disallowed_terms if term.lower() in raw_value]
    if found_terms:
        return {
            "rule_ref": prohibited_config.get("rule_ref", "Numeration Rules"),
            "field": field_name,
            "issue": f"Contains prohibited vague quantity terms: {found_terms}",
            "severity": "MAJOR"
        }
    return None

def check_compliance(
    declarations: Dict[str, Any],
    font_analysis: List[Dict[str, Any]],
    rules_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Applies the comprehensive rules_config to extracted declarations.
    """
    violations = []
    rule_list = rules_config.get("declarations", [])
    severity_config = rules_config.get("severity_levels", {})
    prohibited_config = rules_config.get("prohibited_declarations", {})
    
    # Map rules by field name for O(1) lookup
    rule_map = {r["field"]: r for r in rule_list}

    # 1. Text Declaration Checks
    for field_name, rule_def in rule_map.items():
        field_data = declarations.get(field_name, {"present": False, "value": None})
        severity = _get_severity(field_name, severity_config)

        # Missing Mandatory Data
        missing_violation = _check_mandatory(field_name, field_data, rule_def, severity)
        if missing_violation:
            violations.append(missing_violation)
            continue # Skip regex checks if missing

        # Missing Phrases / Keywords
        phrase_violation = _check_phrases_and_keywords(field_name, field_data, rule_def, severity)
        if phrase_violation:
            violations.append(phrase_violation)

        # Regex Format violations
        regex_violation = _check_format_regex(field_name, field_data, rule_def, severity)
        if regex_violation:
            violations.append(regex_violation)

        # Prohibited terms (specifically for net_quantity)
        prohibited_violation = _check_prohibited_terms(field_name, field_data, prohibited_config)
        if prohibited_violation:
            violations.append(prohibited_violation)

    # 2. Font Size Violations (Phase 7 input integration)
    for font_item in font_analysis:
        if font_item.get("compliant") is False:
            field = font_item.get("field", "unknown")
            severity = _get_severity(field, severity_config)
            violations.append({
                "rule_ref": "Rule 7",
                "field": field,
                "issue": f"Font height {font_item.get('measured_height_mm')}mm is below required {font_item.get('required_min_mm')}mm",
                "severity": severity
            })

    return violations