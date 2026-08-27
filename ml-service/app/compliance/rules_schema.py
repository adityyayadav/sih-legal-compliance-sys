"""
rules_schema.py
----------------
Defines the EXPECTED STRUCTURE of rules_config.json using Pydantic models.

Why this file exists:
Everyone downstream (field_extractor.py, font_measure.py, rule_engine.py in later
phases) will read rules_config.json and assume certain keys exist. If someone edits
the JSON by hand later (e.g. to add a new declaration or fix a rule number) and makes
a typo or drops a required key, you want that to fail LOUDLY at startup — not silently
break font-size checking three weeks from now during a demo.

This file belongs to Phase 1. It does not contain any rule content itself — only
the shape that rule content must conform to.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class FontSizeTier(BaseModel):
    max_net_qty_grams_or_ml: Optional[float] = None
    min_height_normal_mm: float
    min_height_blown_molded_mm: Optional[float] = None


class FontSizeTable(BaseModel):
    basis: str
    unit: str = "mm"
    tiers: Optional[List[FontSizeTier]] = None
    # allow alternate shapes (e.g. unit_sale_price's relative-to-MRP table)
    min_height_relative_to_mrp: Optional[float] = None
    description: Optional[str] = None
    note: Optional[str] = None


class SurroundingSpaceRule(BaseModel):
    rule_ref: str
    above_below_mm: str
    left_right_mm: str
    description: str


class DeclarationRule(BaseModel):
    field: str
    display_name: str
    rule_ref: str
    mandatory: bool
    applicability: str
    value_type: str
    format_regex: Optional[str] = None
    min_length_chars: Optional[int] = None
    required_keywords_any: Optional[List[str]] = None
    required_any_of: Optional[List[str]] = None
    must_contain_phrase_any: Optional[List[str]] = None
    disallowed_terms: Optional[List[str]] = None
    standard_units_only: Optional[bool] = None
    must_not_be_future_date: Optional[bool] = None
    letter_width_rule: Optional[str] = None
    surrounding_space_rule: Optional[SurroundingSpaceRule] = None
    font_size_table: Optional[FontSizeTable] = None
    notes: Optional[str] = None

    @field_validator("field")
    @classmethod
    def field_must_be_snake_case(cls, v: str) -> str:
        if not v.islower() or " " in v:
            raise ValueError(f"'field' must be snake_case, got: {v}")
        return v


class PrincipalDisplayPanel(BaseModel):
    rule_ref: str
    description: str
    area_calculation: Dict[str, str]
    excluded_from_area: List[str]
    small_package_exception: Dict[str, Any]


class SeverityLevels(BaseModel):
    CRITICAL: List[str]
    MAJOR: List[str]
    MINOR: List[str]
    description: str


class ProhibitedDeclarations(BaseModel):
    rule_ref: str
    disallowed_quantity_terms: List[str]
    description: str


class RulesConfigMeta(BaseModel):
    config_version: str
    source: str
    last_reviewed: str
    disclaimer: str
    notes: List[str]


class RulesConfig(BaseModel):
    meta: RulesConfigMeta
    principal_display_panel: PrincipalDisplayPanel
    declarations: List[DeclarationRule]
    prohibited_declarations: ProhibitedDeclarations
    severity_levels: SeverityLevels

    @field_validator("declarations")
    @classmethod
    def no_duplicate_fields(cls, v: List[DeclarationRule]) -> List[DeclarationRule]:
        names = [d.field for d in v]
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            raise ValueError(f"Duplicate 'field' entries in declarations: {dupes}")
        return v

    @field_validator("declarations")
    @classmethod
    def severity_lists_reference_real_fields(cls, v):
        # Note: cross-model validation (checking severity_levels against declarations)
        # is done in rules_loader.py after both are parsed, since Pydantic validates
        # field-by-field before the whole model exists.
        return v
