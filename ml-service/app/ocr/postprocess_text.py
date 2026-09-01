"""
postprocess_text.py
----------------------
Cleans up raw OCR output before it's handed to Phase 4's region_classifier.py
(for re-classification if needed) and Phase 6's field_extractor.py (for
structured value extraction). Pure string logic — no ML, deterministic,
fully unit-testable without any OCR engine installed.

Three cleanup steps, applied in THIS ORDER by postprocess() — order matters,
see the note above fix_digit_confusions below:
  1. strip_noise_characters
  2. fix_digit_confusions
  3. normalize_units
  4. collapse_whitespace
"""

import re

# Unit spelling variants -> canonical form. Each pattern matches the unit
# word ONLY when it directly follows a digit (with optional whitespace in
# between) — e.g. "500gm" or "500 GM" — which is how units actually appear
# on labels. This intentionally does NOT touch a bare unit word floating
# with no adjacent number (there's nothing meaningful to normalize there).
_UNIT_VARIANTS = [
    (r"gms?|grams?", "g"),
    (r"kgs?|kilograms?", "kg"),
    (r"mls?|milliliters?|millilitres?", "ml"),
    (r"ltrs?|liters?|litres?", "l"),
]

# Characters allowed to survive strip_noise_characters. Deliberately
# generous — covers currency symbols, standard punctuation used on labels,
# and alphanumerics — while dropping control characters and stray OCR
# artifact glyphs (e.g. "\ufffd", box-drawing characters from misread barcodes).
_ALLOWED_CHARS_PATTERN = re.compile(
    r"[^A-Za-z0-9\u0900-\u097F"   # ASCII alnum + Devanagari (Hindi labels)
    r"\s"                          # whitespace
    r"\u20b9.,:/\-%&()+#@'\"]"
)

_ALNUM_TOKEN = re.compile(r"\b[\dA-Za-z]+\b")


def strip_noise_characters(text: str) -> str:
    if not text:
        return text
    return _ALLOWED_CHARS_PATTERN.sub("", text)


def _fix_token_digit_confusions(token: str) -> str:
    # Only fix a token if it ALREADY contains at least one real digit —
    # i.e. it's very likely a misread number, not an actual English word
    # that happens to contain the letters O/o/l/I (e.g. "Consumer",
    # "Country", "Origin" must be left untouched — this was caught by
    # test_fix_digit_confusions_does_not_corrupt_real_words).
    if not any(c.isdigit() for c in token):
        return token
    fixed = token.replace("O", "0").replace("o", "0")
    fixed = fixed.replace("I", "1").replace("l", "1")
    return fixed


def fix_digit_confusions(text: str) -> str:
    """
    OCR frequently confuses visually similar glyphs in NUMBERS specifically
    (O/o <-> 0, l/I <-> 1). Applied per whole alphanumeric token (not just
    runs of digit-like characters) so that a token like "5OOg" -- digits,
    a confusable letter, AND a real trailing unit letter all stuck together
    with no spaces, exactly as OCR often emits it -- gets its confusable
    characters fixed as one unit ("500g"), which is required before
    normalize_units can recognize "g" as an attached unit.
    """
    if not text:
        return text
    return _ALNUM_TOKEN.sub(lambda m: _fix_token_digit_confusions(m.group(0)), text)


def normalize_units(text: str) -> str:
    if not text:
        return text
    result = text
    for unit_pattern, canonical in _UNIT_VARIANTS:
        # (digit)(optional whitespace)(unit word) -> digit + same whitespace + canonical unit.
        # Preserves whether the original had "500gm" (no space) or "500 GM" (space).
        pattern = re.compile(r"(\d)(\s*)(" + unit_pattern + r")\b", flags=re.IGNORECASE)
        result = pattern.sub(lambda m: m.group(1) + m.group(2) + canonical, result)
    return result


def collapse_whitespace(text: str) -> str:
    if not text:
        return text
    return re.sub(r"\s+", " ", text).strip()


def postprocess(text: str) -> str:
    """
    Full cleanup pipeline. ORDER MATTERS: fix_digit_confusions must run
    BEFORE normalize_units, not after -- a token like "5OO gm" only becomes
    recognizable as a number+unit once "5OO" is fixed to "500" first;
    normalize_units's digit-anchor regex can't match a unit following "O"
    characters. This ordering was caught and fixed via
    test_postprocess_full_pipeline_on_realistic_noisy_ocr_output -- don't
    reorder these steps without re-running that test.

    Safe to call on empty/None input (returns "" unchanged).
    """
    if not text:
        return text or ""

    result = strip_noise_characters(text)
    result = fix_digit_confusions(result)
    result = normalize_units(result)
    result = collapse_whitespace(result)
    return result
