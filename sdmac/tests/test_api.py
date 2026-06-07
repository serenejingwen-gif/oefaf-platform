"""Tests for the SD-MAC public analytics API.

Coverage:
  * Every documented endpoint (7 record endpoints + /healthz) returns 200/201.
  * Returned payloads validate against the matching schema-registry schema via
    ``shared.utilities.schema_loader.validate_record``.
  * ``POST /v1/scenarios`` then ``GET /v1/scenarios/{id}`` round-trips.
  * Filters on ``/v1/events`` (commodity, region, since, min_severity) and on
    ``/v1/modules`` (platform_component, validation_status) work.

These tests exercise the FastAPI app in-process via ``TestClient`` (no live
server, no network). All records served are synthetic illustrative data
generated for demonstration; they are NOT real agency data and are NOT derived
from any proprietary or employer source.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from shared.utilities.schema_loader import validate_record

from sdmac.api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """A TestClient bound to the SD-MAC FastAPI app."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Operational endpoint
# ---------------------------------------------------------------------------


def test_healthz_returns_200_and_counts(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    # Seeded from bundled fixtures + manifests; all should be non-empty.
    assert body["events_loaded"] > 0
    assert body["forecasts_loaded"] > 0
    assert body["scenarios_loaded"] > 0
    assert body["modules_loaded"] > 0


# ---------------------------------------------------------------------------
# GEA — events
# ---------------------------------------------------------------------------


def test_list_events_200_and_summary_shape(client: TestClient) -> None:
    resp = client.get("/v1/events")
    assert resp.status_code == 200, resp.text
    events = resp.json()
    assert isinstance(events, list) and len(events) > 0
    # The list endpoint returns the compact projection, not the full record.
    expected_keys = {"event_id", "detected_at_utc", "severity_score", "public_evidence_refs"}
    for ev in events:
        assert set(ev.keys()) == expected_keys


def test_get_event_200_and_full_record_validates(client: TestClient) -> None:
    # Pick a known seeded event id from the list endpoint.
    first_id = client.get("/v1/events").json()[0]["event_id"]
    resp = client.get(f"/v1/events/{first_id}")
    assert resp.status_code == 200, resp.text
    record = resp.json()
    # Full record must validate against the registry schema.
    assert validate_record(record, "supply_disruption_event") is True


def test_get_event_unknown_id_404(client: TestClient) -> None:
    resp = client.get("/v1/events/GEA-EVT-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_events_filter_by_commodity(client: TestClient) -> None:
    resp = client.get("/v1/events", params={"commodity": "crude_oil"})
    assert resp.status_code == 200, resp.text
    ids = {e["event_id"] for e in resp.json()}
    # Cross-check each returned event's full record really is crude_oil.
    for eid in ids:
        full = client.get(f"/v1/events/{eid}").json()
        assert full["commodity"] == "crude_oil"
    # And the filter actually narrows the set (fixtures have other commodities).
    assert len(ids) < len(client.get("/v1/events").json())


def test_events_filter_by_region(client: TestClient) -> None:
    resp = client.get("/v1/events", params={"region": "SAU"})
    assert resp.status_code == 200, resp.text
    for e in resp.json():
        full = client.get(f"/v1/events/{e['event_id']}").json()
        assert full["region_iso"] == "SAU"


def test_events_filter_by_min_severity(client: TestClient) -> None:
    resp = client.get("/v1/events", params={"min_severity": 0.8})
    assert resp.status_code == 200, resp.text
    for e in resp.json():
        assert e["severity_score"] >= 0.8


def test_events_filter_by_since(client: TestClient) -> None:
    cutoff = "2026-01-20T00:00:00Z"
    resp = client.get("/v1/events", params={"since": cutoff})
    assert resp.status_code == 200, resp.text
    returned = resp.json()
    for e in returned:
        assert e["detected_at_utc"] >= cutoff
    # The cutoff should exclude at least one early-January fixture event.
    assert len(returned) < len(client.get("/v1/events").json())


# ---------------------------------------------------------------------------
# CRICAT — forecasts
# ---------------------------------------------------------------------------


def test_get_forecasts_200_and_records_validate(client: TestClient) -> None:
    resp = client.get("/v1/forecasts/PJM")
    assert resp.status_code == 200, resp.text
    records = resp.json()
    assert isinstance(records, list) and len(records) > 0
    for rec in records:
        assert rec["iso_region"] == "PJM"
        assert validate_record(rec, "load_forecast_record") is True


def test_get_forecasts_window_filter(client: TestClient) -> None:
    # Bound below all fixture windows -> still returns the PJM forecasts.
    resp = client.get(
        "/v1/forecasts/PJM",
        params={"target_window_start": "2026-01-01T00:00:00Z"},
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) > 0


def test_get_forecasts_invalid_region_422(client: TestClient) -> None:
    # Not a registry enum value -> FastAPI validation error.
    resp = client.get("/v1/forecasts/NOT_A_REGION")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# CRICAT — scenarios (POST then GET round-trip)
# ---------------------------------------------------------------------------


def test_create_scenario_then_get_roundtrip(client: TestClient) -> None:
    payload = {
        "scenario_label": "summer_2027_extreme_heat_pjm",
        "stress_drivers": ["heatwave", "outage"],
        "regions": ["PJM"],
        "time_horizon_hours": 24,
    }
    create = client.post("/v1/scenarios", json=payload)
    assert create.status_code == 201, create.text
    created = create.json()

    # Created record must validate against the registry schema.
    assert validate_record(created, "capacity_allocation_scenario") is True
    # Server-derived fields are present and within their declared domains.
    assert 0.0 <= created["probability_of_stress"] <= 1.0
    assert created["scenario_label"] == payload["scenario_label"]
    assert created["stress_drivers"] == payload["stress_drivers"]
    assert created["regions"] == payload["regions"]
    assert created["time_horizon_hours"] == payload["time_horizon_hours"]

    scenario_id = created["scenario_id"]
    # The round-trip: GET the just-created scenario returns the same record.
    fetched = client.get(f"/v1/scenarios/{scenario_id}")
    assert fetched.status_code == 200, fetched.text
    assert fetched.json() == created


def test_create_scenario_is_deterministic(client: TestClient) -> None:
    # Same request body -> identical server-derived magnitudes (seeded).
    payload = {
        "scenario_label": "determinism_probe",
        "stress_drivers": ["cold_snap"],
        "regions": ["ERCOT"],
        "time_horizon_hours": 48,
    }
    a = client.post("/v1/scenarios", json=payload).json()
    b = client.post("/v1/scenarios", json=payload).json()
    # Ids differ (monotonic), but the derived physics fields are identical.
    for field in (
        "assumed_demand_mw",
        "assumed_available_capacity_mw",
        "reserve_margin_pct",
        "probability_of_stress",
    ):
        assert a[field] == b[field]


def test_get_scenario_seeded_fixture_validates(client: TestClient) -> None:
    resp = client.get("/v1/scenarios/CRICAT-SCN-0000")
    assert resp.status_code == 200, resp.text
    assert validate_record(resp.json(), "capacity_allocation_scenario") is True


def test_get_scenario_unknown_id_404(client: TestClient) -> None:
    resp = client.get("/v1/scenarios/CRICAT-SCN-DOES-NOT-EXIST")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# SD-MAC — modules
# ---------------------------------------------------------------------------


def test_list_modules_200_and_validate(client: TestClient) -> None:
    resp = client.get("/v1/modules")
    assert resp.status_code == 200, resp.text
    modules = resp.json()
    assert isinstance(modules, list) and len(modules) > 0
    for mod in modules:
        assert validate_record(mod, "module_manifest") is True


def test_modules_filter_by_platform_component(client: TestClient) -> None:
    resp = client.get("/v1/modules", params={"platform_component": "cricat"})
    assert resp.status_code == 200, resp.text
    returned = resp.json()
    assert len(returned) > 0
    for mod in returned:
        assert mod["platform_component"] == "cricat"
    # Filter narrows the full set (manifests span gea/cricat/sdmac/shared).
    assert len(returned) < len(client.get("/v1/modules").json())


def test_modules_filter_by_validation_status(client: TestClient) -> None:
    resp = client.get("/v1/modules", params={"validation_status": "draft"})
    assert resp.status_code == 200, resp.text
    for mod in resp.json():
        assert mod["validation_status"] == "draft"


def test_get_module_200_and_validate(client: TestClient) -> None:
    first_id = client.get("/v1/modules").json()[0]["module_id"]
    resp = client.get(f"/v1/modules/{first_id}")
    assert resp.status_code == 200, resp.text
    assert validate_record(resp.json(), "module_manifest") is True


def test_get_module_unknown_id_404(client: TestClient) -> None:
    resp = client.get("/v1/modules/not-a-real-module")
    assert resp.status_code == 404
