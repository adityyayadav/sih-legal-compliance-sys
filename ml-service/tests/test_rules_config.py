"""
test_rules_config.py
---------------------
Phase 1 is only "done" when these tests pass. Run with:
    pytest tests/test_rules_config.py -v

These tests don't test any ML/OCR — they only test that your rule matrix
(rules_config.json) is well-formed, internally consistent, and safe for the
later phases to build on top of.
"""

import pytest
from app.compliance.rules_loader import get_rules_config, get_declaration_rule, RulesConfigError


def test_config_loads_without_error():
    config = get_rules_config()
    assert config is not None


def test_all_critical_fields_present():
    """The three highest-stakes fields must exist and be mandatory."""
    config = get_rules_config()
    fields = {d.field: d for d in config.declarations}
    for critical_field in ["net_quantity", "mrp", "manufacturer_or_packer_or_importer_name_address"]:
        assert critical_field in fields, f"Missing critical field: {critical_field}"
        assert fields[critical_field].mandatory is True


def test_net_quantity_has_font_table_with_three_tiers():
    rule = get_declaration_rule("net_quantity")
    assert rule.font_size_table is not None
    assert len(rule.font_size_table.tiers) == 3


def test_mrp_requires_tax_inclusive_phrase():
    rule = get_declaration_rule("mrp")
    assert rule.must_contain_phrase_any is not None
    assert any("tax" in p.lower() for p in rule.must_contain_phrase_any)


def test_no_duplicate_field_names():
    config = get_rules_config()
    names = [d.field for d in config.declarations]
    assert len(names) == len(set(names)), "Duplicate field names found in rules_config.json"


def test_every_mandatory_field_has_a_severity():
    config = get_rules_config()
    all_severity_fields = (
        set(config.severity_levels.CRITICAL)
        | set(config.severity_levels.MAJOR)
        | set(config.severity_levels.MINOR)
    )
    for d in config.declarations:
        if d.mandatory:
            assert d.field in all_severity_fields, f"{d.field} has no severity level assigned"


def test_unknown_field_lookup_raises_keyerror():
    with pytest.raises(KeyError):
        get_declaration_rule("this_field_does_not_exist")


def test_regex_patterns_actually_compile():
    """A malformed regex in the JSON should be caught here, not at runtime in Phase 6."""
    import re
    config = get_rules_config()
    for d in config.declarations:
        if d.format_regex:
            try:
                re.compile(d.format_regex)
            except re.error as e:
                pytest.fail(f"Invalid regex for field '{d.field}': {e}")
