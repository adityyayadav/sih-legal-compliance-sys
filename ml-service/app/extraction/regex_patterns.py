import re
from typing import List, Optional, Dict, Any

def match_regex_pattern(text: str, pattern: str) -> Optional[str]:
    """Matches a dynamic regex pattern from the rules config against text."""
    if not pattern:
        return None
    try:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else None
    except re.error:
        return None

def contains_required_phrases(text: str, phrases: List[str]) -> bool:
    """Checks if the text contains at least one of the required phrases (e.g., for MRP)."""
    if not phrases:
        return True
    
    text_lower = text.lower()
    return any(phrase.lower() in text_lower for phrase in phrases)

def evaluate_structured_field(ocr_text: str, rule: Dict[str, Any]) -> Optional[str]:
    """Evaluates OCR text against regex and phrase rules for a specific field."""
    regex_pattern = rule.get("format_regex")
    required_phrases = rule.get("must_contain_phrase", [])
    
    matched_value = match_regex_pattern(ocr_text, regex_pattern)
    
    if matched_value:
        if contains_required_phrases(ocr_text, required_phrases):
            return matched_value
    return None