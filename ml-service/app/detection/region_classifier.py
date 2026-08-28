"""
region_classifier.py
----------------------
Classifies each detected+OCR'd text region into one of the mandatory
declaration types from rules_config.json (Phase 1), using fast keyword +
regex matching against the region's recognized text.

IMPORTANT — pipeline ordering: this module classifies based on TEXT
CONTENT, so it must run AFTER Phase 5's OCR step has produced a `text`
string for each region, not directly on raw image crops. The full pipeline
order (see app/main.py in Phase 9) is:

    regions = detect_text_regions(image)          # Phase 4, text_detector.py
    for r in regions:
        r["text"] = run_ocr(r["crop"])["text"]     # Phase 5, ocr_engine.py
    classified = classify_regions(regions)         # Phase 4, this file

Classification strategy (fast, no training data required):
  1. Regex match — does the text match the field's `format_regex` from
     rules_config.json? (net_quantity: "500g", mrp: "Rs. 120", etc.)
  2. Keyword boost — does the text contain any keyword associated with that
     field ("MRP", "Net Wt", "Mfg Date", "Best Before", ...)?
  3. Required-phrase boost — fields like MRP that require a specific phrase
     ("inclusive of all taxes") get bonus score when it's present.
  4. Penalty — if the text contains a disallowed/vague term for that field
     (e.g. "approx" near a quantity), its score for that field is reduced.
  5. Highest-scoring field wins. Below MIN_SCORE_TO_CLASSIFY, the region is
     labeled "other_non_mandatory_text" instead of being forced into a
     wrong category.

This is intentionally simple and fast — Phase 4's plan explicitly notes a
fine-tuned layout model (LayoutLMv3) as a stretch upgrade "only if time
permits." Keep this regex/keyword version working first: it's what makes
the Week-2 "rough end-to-end pipeline" checkpoint achievable without
needing a trained model yet.

KNOWN LIMITATION: `common_or_generic_name` has no reliable regex or
keyword pattern (it's just "whatever the product is called"), so this
classifier will rarely confidently tag it. In practice it's usually the
largest/most prominent text on the front panel — if time permits, add a
simple heuristic in classify_regions() that also considers bbox height
(pick the largest un-classified text block as a common_or_generic_name
candidate). Documented here rather than silently guessed at.
"""

import re
from typing import List, Dict

from app.compliance.rules_loader import get_rules_config

# Extra keyword hints per field, layered on top of rules_config.json's
# format_regex / required_keywords_any / must_contain_phrase_any. Not every
# field has a reliable regex (e.g. manufacturer address, dates in free text),
# so keywords carry more weight there.
FIELD_KEYWORDS = {
    "manufacturer_or_packer_or_importer_name_address": [
        # NOTE: deliberately NOT using bare "mfg" here — it's a substring of
        # "Mfg Date", which caused a real misclassification bug caught by
        # test_classify_region_text_matches_expected_field (see git history /
        # PHASE4_WALKTHROUGH.md). Multi-word phrases below are specific
        # enough to avoid that collision.
        "manufactured by", "mfg by", "mfg. by", "packed by", "marketed by",
        "mktd by", "imported by", "pvt ltd", "ltd", "llp"
    ],
    "common_or_generic_name": [],  # see KNOWN LIMITATION above
    "net_quantity": ["net wt", "net weight", "net qty", "net quantity", "net vol", "net content"],
    "mrp": ["mrp", "maximum retail price", "m.r.p"],
    "unit_sale_price": ["unit sale price", "usp", "per kg", "per litre", "per unit"],
    "mfg_or_pack_or_import_date": ["mfg date", "mfd", "pkd", "packed on", "date of mfg", "manufacture date"],
    "best_before_or_use_by_date": ["best before", "use by", "expiry", "exp date", "bb date"],
    "consumer_care_details": ["consumer care", "customer care", "helpline", "toll free", "email", "contact us"],
    "country_of_origin": ["country of origin", "made in", "manufactured in"],
    "dimensions_or_number_of_contents": ["contains", "pieces", "pcs", "nos", "dimensions"],
}

OTHER_CLASS = "other_non_mandatory_text"
MIN_SCORE_TO_CLASSIFY = 1


def _score_text_against_field(text: str, field_rule) -> int:
    """
    NOTE on weighting: explicit keyword/phrase matches are weighted HIGHER
    than generic format_regex matches on purpose. A phrase like "Best
    Before" is an unambiguous, human-written label of intent. A generic
    date regex (e.g. "MM/YYYY") is a much weaker signal on its own, because
    several date-shaped fields (mfg date, best-before date) can all match
    the same generic pattern — the keyword is what actually disambiguates
    them. Getting this weighting backwards was caught by
    test_classify_region_text_matches_expected_field in tests/test_detection.py
    (a "Best Before 12 2026" string was mis-scored toward mfg_date until
    this weighting was fixed) — don't revert it without re-running that test.
    """
    score = 0
    text_lower = text.lower()

    if field_rule.format_regex:
        try:
            if re.search(field_rule.format_regex, text, flags=re.IGNORECASE):
                score += 2
        except re.error:
            pass  # regex validity is already guaranteed by Phase 1's test suite

    for kw in FIELD_KEYWORDS.get(field_rule.field, []):
        if kw in text_lower:
            score += 3

    # NOTE: required_keywords_any comes from rules_config.json (Phase 1),
    # where it was designed as a coarse PRESENCE check (e.g. bare "Mfg"),
    # not for fine-grained disambiguation between fields. Weighted lower
    # than FIELD_KEYWORDS above for that reason — bare "Mfg" alone
    # shouldn't outscore a more specific competing match (e.g. "Mfg Date").
    required_keywords = getattr(field_rule, "required_keywords_any", None)
    if required_keywords and any(kw.lower() in text_lower for kw in required_keywords):
        score += 1

    must_contain = getattr(field_rule, "must_contain_phrase_any", None)
    if must_contain and any(p.lower() in text_lower for p in must_contain):
        score += 3

    disallowed = getattr(field_rule, "disallowed_terms", None)
    if disallowed and any(term.lower() in text_lower for term in disallowed):
        score -= 2  # penalize vague/prohibited terms near an otherwise-matching field

    return score


def classify_region_text(text: str) -> Dict[str, object]:
    """
    Classifies a single OCR'd text string into the best-matching declaration
    field.

    Returns:
        {"category": <field_name or 'other_non_mandatory_text'>,
         "score": int,
         "all_scores": {field_name: score, ...}}
    """
    if not text or not text.strip():
        return {"category": OTHER_CLASS, "score": 0, "all_scores": {}}

    config = get_rules_config()
    scores = {rule.field: _score_text_against_field(text, rule) for rule in config.declarations}

    best_field = max(scores, key=scores.get)
    best_score = scores[best_field]

    if best_score < MIN_SCORE_TO_CLASSIFY:
        return {"category": OTHER_CLASS, "score": best_score, "all_scores": scores}

    return {"category": best_field, "score": best_score, "all_scores": scores}


def classify_regions(regions: List[Dict]) -> List[Dict]:
    """
    Takes a list of regions (each already carrying an OCR'd "text" key —
    see module docstring for the expected pipeline order) and adds a
    "category" + "classification_score" key to each IN PLACE. Also returns
    the same list for convenience/chaining.
    """
    for region in regions:
        text = region.get("text", "")
        result = classify_region_text(text)
        region["category"] = result["category"]
        region["classification_score"] = result["score"]
    return regions
