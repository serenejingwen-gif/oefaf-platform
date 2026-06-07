"""Schema-conformance tests for emitted GEA ``supply_disruption_event`` records.

Each emitted record must validate against the ``supply_disruption_event`` schema
in the SD-MAC schema registry via
:func:`shared.utilities.schema_loader.validate_record`.

All inputs are synthetic illustrative data generated for demonstration; no real
agency data and no proprietary or employer source.
"""

from __future__ import annotations

import jsonschema
import pytest
from shared.utilities.schema_loader import load_schema, validate_record

from gea.ingestion.loaders import COMMODITY_ENUM, SOURCE_CATEGORIES
from gea.scoring.scorer import build_events

_SCHEMA_NAME = "supply_disruption_event"

# The exact field set the schema registry declares for supply_disruption_event.
_EXPECTED_FIELDS = {
    "event_id",
    "detected_at_utc",
    "commodity",
    "region_iso",
    "source_categories",
    "severity_score",
    "confidence",
    "public_evidence_refs",
}


def test_registry_has_expected_fields():
    """The on-disk schema declares exactly the expected field set."""
    registry = load_schema(_SCHEMA_NAME)
    declared = {f["name"] for f in registry["fields"]}
    assert declared == _EXPECTED_FIELDS


def test_emitted_records_validate_against_schema():
    """Every emitted supply_disruption_event validates against the registry schema."""
    events = build_events()
    assert events, "build_events() produced no records to validate"
    for rec in events:
        # validate_record raises on failure; True on success.
        assert validate_record(rec, _SCHEMA_NAME) is True


def test_emitted_records_have_exact_field_set():
    """Emitted records carry every declared field and no missing ones."""
    for rec in build_events():
        assert set(rec) == _EXPECTED_FIELDS


def test_emitted_commodity_within_enum():
    """commodity values stay within the schema's commodity enum."""
    for rec in build_events():
        assert rec["commodity"] in COMMODITY_ENUM


def test_emitted_source_categories_are_public_labels():
    """source_categories are drawn only from the public source-category labels."""
    for rec in build_events():
        assert rec["source_categories"], "expected at least one source category"
        for label in rec["source_categories"]:
            assert label in SOURCE_CATEGORIES


def test_emitted_evidence_refs_are_illustrative_example_org():
    """Evidence refs are illustrative example.org placeholders, not real URLs."""
    for rec in build_events():
        assert rec["public_evidence_refs"], "expected at least one evidence ref"
        for url in rec["public_evidence_refs"]:
            assert url.startswith("https://example.org/synthetic-evidence/")


def test_invalid_record_is_rejected():
    """A record with an out-of-range severity must fail validation.

    Confirms the schema's [0, 1] bound on severity_score is actually enforced,
    so a passing conformance test is meaningful (negative control).
    """
    events = build_events()
    bad = dict(events[0])
    bad["severity_score"] = 1.5  # outside [0, 1]
    with pytest.raises(jsonschema.ValidationError):
        validate_record(bad, _SCHEMA_NAME)


def test_invalid_commodity_is_rejected():
    """A record with an out-of-enum commodity must fail validation (negative control)."""
    events = build_events()
    bad = dict(events[0])
    bad["commodity"] = "uranium"  # not in the schema enum
    with pytest.raises(jsonschema.ValidationError):
        validate_record(bad, _SCHEMA_NAME)
