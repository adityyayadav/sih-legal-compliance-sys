"""
rules_loader.py 
----------------
The ONLY place in the entire codebase that should ever open rules_config.json
directly with open()/json.load(). Every other module (field_extractor.py,
font_measure.py, rule_engine.py, the /api/v1/rules endpoint, etc.) imports and
calls `get_rules_config()` from here instead of touching the file directly.

Why centralize this:
  - Validates the JSON against rules_schema.py ONCE, at import time, so a broken
    config fails fast (at server startup) instead of crashing mid-request during
    a demo.
  - Caches the parsed config in memory so you're not re-reading/re-parsing the
    file on every single API call.
  - Gives you one place to add hot-reload later if you ever want to edit
    rules_config.json without restarting the service.

This file belongs to Phase 1 (it operationalizes the rule matrix) but is also
the first piece of Phase 9 infrastructure — later phases (6, 7, 8) will all
import from here.
"""

import json
from pathlib import Path
from functools import lru_cache

from pydantic import ValidationError

from app.compliance.rules_schema import RulesConfig

CONFIG_PATH = Path(__file__).parent / "rules_config.json"


class RulesConfigError(Exception):
    """Raised when rules_config.json is missing, malformed, or fails validation."""


@lru_cache(maxsize=1)
def get_rules_config() -> RulesConfig:
    """
    Load, validate, and return the parsed rules configuration.
    Cached after first call — restart the service to pick up file edits
    (or call get_rules_config.cache_clear() in a dev/hot-reload endpoint).
    """
    if not CONFIG_PATH.exists():
        raise RulesConfigError(f"rules_config.json not found at {CONFIG_PATH}")

    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RulesConfigError(f"rules_config.json is not valid JSON: {e}") from e

    try:
        config = RulesConfig(**raw)
    except ValidationError as e:
        raise RulesConfigError(
            f"rules_config.json failed schema validation:\n{e}"
        ) from e

    _cross_check_severity_levels(config)
    return config


def _cross_check_severity_levels(config: RulesConfig) -> None:
    """
    Extra validation Pydantic's per-field validators can't do alone: every field
    name listed under severity_levels (CRITICAL/MAJOR/MINOR) must actually exist
    in the declarations list, and every mandatory declaration should be assigned
    a severity somewhere (otherwise the compliance engine won't know how to
    weight it in Phase 8).
    """
    known_fields = {d.field for d in config.declarations}
    severity_fields = (
        set(config.severity_levels.CRITICAL)
        | set(config.severity_levels.MAJOR)
        | set(config.severity_levels.MINOR)
    )

    unknown = severity_fields - known_fields
    if unknown:
        raise RulesConfigError(
            f"severity_levels references fields not present in declarations: {unknown}"
        )

    mandatory_fields = {d.field for d in config.declarations if d.mandatory}
    unassigned = mandatory_fields - severity_fields
    if unassigned:
        raise RulesConfigError(
            f"Mandatory declarations missing a severity assignment: {unassigned}"
        )


def get_declaration_rule(field_name: str):
    """Convenience lookup used heavily in Phase 6/7/8."""
    config = get_rules_config()
    for d in config.declarations:
        if d.field == field_name:
            return d
    raise KeyError(f"No declaration rule found for field '{field_name}'")


if __name__ == "__main__":
    # Quick manual check: `python -m app.compliance.rules_loader`
    cfg = get_rules_config()
    print(f"Loaded rules_config.json — version {cfg.meta.config_version}")
    print(f"Declarations defined: {len(cfg.declarations)}")
    for d in cfg.declarations:
        print(f"  - {d.field:45s} mandatory={d.mandatory!s:5s} rule={d.rule_ref}")