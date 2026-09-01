from typing import List, Dict, Any
from app.extraction.regex_patterns import evaluate_structured_field
from app.extraction.ner_model import AddressNERModel

def create_empty_declaration() -> Dict[str, Any]:
    """Creates the default empty state for a declaration field."""
    return {
        "present": False,
        "value": None,
        "confidence": 0.0,
        "bbox": None,
        "source_image_index": None
    }

def extract_fields(ocr_results: List[Dict], rules_config: Dict) -> Dict[str, Any]:
    """
    Matches OCR'd text against rules_config regexes and structures the output.
    Returns the 'declarations' section of the API response.
    """
    declarations = {}
    config_rules = rules_config.get("declarations", [])
    ner_engine = AddressNERModel()
    
    # Initialize all fields defined in the rules matrix to empty
    for rule in config_rules:
        field_name = rule["field"]
        declarations[field_name] = create_empty_declaration()

    for rule in config_rules:
        field_name = rule["field"]
        
        # 1. Handle Unstructured Fields via NER
        if field_name == "manufacturer_name_address":
            ner_result = ner_engine.extract_manufacturer_info(ocr_results)
            if ner_result:
                declarations[field_name] = {
                    "present": True,
                    "value": ner_result.get("text"),
                    "confidence": ner_result.get("confidence", 0.0),
                    "bbox": ner_result.get("bbox"),
                    "source_image_index": ner_result.get("source_image_index", 0)
                }
            continue
            
        # 2. Handle Structured Fields via dynamic Regex
        best_match = None
        for ocr_block in ocr_results:
            text = ocr_block.get("text", "")
            matched_value = evaluate_structured_field(text, rule)
            
            if matched_value:
                # If multiple matches exist, keep the one with the highest confidence
                current_conf = ocr_block.get("confidence", 0.0)
                if not best_match or current_conf > best_match.get("confidence", 0.0):
                    best_match = {
                        "present": True,
                        "value": matched_value,
                        "confidence": current_conf,
                        "bbox": ocr_block.get("bbox"),
                        "source_image_index": ocr_block.get("source_image_index", 0)
                    }
        
        if best_match:
            declarations[field_name] = best_match

    return declarations