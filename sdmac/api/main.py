"""SD-MAC public analytics API (FastAPI).

Exposes exactly the seven documented record endpoints, plus an operational
``/healthz`` liveness probe (not a record endpoint; documented as such):

    GET  /v1/events                  (GEA)    list event summaries, filterable
    GET  /v1/events/{event_id}       (GEA)    full supply_disruption_event
    GET  /v1/forecasts/{iso_region}  (CRICAT) array of load_forecast_record
    POST /v1/scenarios               (CRICAT) create capacity_allocation_scenario
    GET  /v1/scenarios/{scenario_id} (CRICAT) full capacity_allocation_scenario
    GET  /v1/modules                 (SD-MAC) array of module_manifest, filterable
    GET  /v1/modules/{module_id}     (SD-MAC) full module_manifest
    GET  /healthz                    (ops)    liveness + seeded record counts

The application serves entirely from bundled synthetic fixtures and the schema
registry manifests (see ``sdmac.api.store``). It performs no network access and
reads no proprietary or employer-internal data.

All records returned by this API are synthetic illustrative data generated for
demonstration. They are NOT real agency data and are NOT derived from any
proprietary or employer source.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from sdmac.api.models import (
    CapacityAllocationScenario,
    Commodity,
    EventSummary,
    HealthResponse,
    IsoRegion,
    LoadForecastRecord,
    ModuleManifest,
    PlatformComponent,
    ScenarioCreateRequest,
    SupplyDisruptionEvent,
    ValidationStatus,
)
from sdmac.api.store import RecordStore

API_DESCRIPTION = (
    "SD-MAC (Sector-Wide Deployable Modular Analytics Commons) public analytics "
    "API for the Integrated Commodity Risk Analytics Platform (GEA, CRICAT, "
    "SD-MAC), governed under the planned Open Energy Finance Analytics Foundation "
    "(OEFAF, in formation as a Section 501(c)(3) public charity). "
    "All data served by this API is synthetic illustrative data generated for "
    "demonstration. It is NOT real agency data and is NOT derived from any "
    "proprietary or employer source."
)

app = FastAPI(
    title="SD-MAC Public Analytics API",
    version="0.1.0",
    description=API_DESCRIPTION,
)

# Single process-lifetime store, seeded from fixtures + manifests at import.
# POST /v1/scenarios mutates this store so later GETs observe created scenarios.
store = RecordStore()


# ---------------------------------------------------------------------------
# GEA endpoints
# ---------------------------------------------------------------------------


@app.get("/v1/events", response_model=list[EventSummary], tags=["GEA"])
def list_events(
    commodity: Commodity | None = Query(  # noqa: B008 -- FastAPI dependency-injection default
        default=None, description="Filter by affected commodity category"
    ),
    region: str | None = Query(
        default=None, description="Filter by region_iso (exact match, e.g. 'USA')"
    ),
    since: str | None = Query(
        default=None,
        description="Return events with detected_at_utc >= this ISO-8601 UTC timestamp",
    ),
    min_severity: float | None = Query(
        default=None, ge=0.0, le=1.0, description="Return events with severity_score >= this value"
    ),
) -> list[EventSummary]:
    """List supply-disruption event summaries (GEA), with optional filters.

    Returns the compact projection: ``event_id``,
    ``detected_at_utc``, ``severity_score``, and ``public_evidence_refs[]``.
    Filters are conjunctive (an event must satisfy all supplied filters).
    """
    results: list[EventSummary] = []
    for rec in store.list_events():
        if commodity is not None and rec.get("commodity") != commodity.value:
            continue
        if region is not None and rec.get("region_iso") != region:
            continue
        # since is an ISO-8601 UTC string; lexical comparison is correct for the
        # fixed "YYYY-MM-DDTHH:MM:SSZ" Zulu format used by the fixtures.
        if since is not None and str(rec.get("detected_at_utc", "")) < since:
            continue
        if min_severity is not None and float(rec.get("severity_score", 0.0)) < min_severity:
            continue
        results.append(
            EventSummary(
                event_id=rec["event_id"],
                detected_at_utc=rec["detected_at_utc"],
                severity_score=rec["severity_score"],
                public_evidence_refs=rec["public_evidence_refs"],
            )
        )
    return results


@app.get("/v1/events/{event_id}", response_model=SupplyDisruptionEvent, tags=["GEA"])
def get_event(event_id: str) -> SupplyDisruptionEvent:
    """Return the full ``supply_disruption_event`` for ``event_id`` (GEA)."""
    rec = store.get_event(event_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"event '{event_id}' not found")
    return SupplyDisruptionEvent(**rec)


# ---------------------------------------------------------------------------
# CRICAT endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/v1/forecasts/{iso_region}", response_model=list[LoadForecastRecord], tags=["CRICAT"]
)
def get_forecasts(
    iso_region: IsoRegion,
    target_window_start: str | None = Query(
        default=None,
        description="Return forecasts with target_window_start_utc >= this ISO-8601 UTC timestamp",
    ),
    target_window_end: str | None = Query(
        default=None,
        description="Return forecasts with target_window_end_utc <= this ISO-8601 UTC timestamp",
    ),
) -> list[LoadForecastRecord]:
    """Return ``load_forecast_record`` array for an ISO/RTO region (CRICAT).

    Optionally bound by the target forecast window. The ``iso_region`` path is
    validated against the registry enum by FastAPI before this handler runs.
    """
    results: list[LoadForecastRecord] = []
    for rec in store.list_forecasts():
        if rec.get("iso_region") != iso_region.value:
            continue
        if (
            target_window_start is not None
            and str(rec.get("target_window_start_utc", "")) < target_window_start
        ):
            continue
        if (
            target_window_end is not None
            and str(rec.get("target_window_end_utc", "")) > target_window_end
        ):
            continue
        results.append(LoadForecastRecord(**rec))
    return results


@app.post("/v1/scenarios", response_model=CapacityAllocationScenario, status_code=201, tags=["CRICAT"])
def create_scenario(payload: ScenarioCreateRequest) -> CapacityAllocationScenario:
    """Create and persist a ``capacity_allocation_scenario`` (CRICAT).

    The server derives demand/capacity assumptions, reserve margin, and
    probability of stress deterministically (seeded) from the request, assigns a
    ``scenario_id``, and stores the record so a subsequent
    ``GET /v1/scenarios/{scenario_id}`` returns it.
    """
    rec = store.create_scenario(
        scenario_label=payload.scenario_label,
        stress_drivers=payload.stress_drivers,
        regions=payload.regions,
        time_horizon_hours=payload.time_horizon_hours,
    )
    return CapacityAllocationScenario(**rec)


@app.get(
    "/v1/scenarios/{scenario_id}",
    response_model=CapacityAllocationScenario,
    tags=["CRICAT"],
)
def get_scenario(scenario_id: str) -> CapacityAllocationScenario:
    """Return the full ``capacity_allocation_scenario`` for ``scenario_id`` (CRICAT)."""
    rec = store.get_scenario(scenario_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"scenario '{scenario_id}' not found")
    return CapacityAllocationScenario(**rec)


# ---------------------------------------------------------------------------
# SD-MAC endpoints
# ---------------------------------------------------------------------------


@app.get("/v1/modules", response_model=list[ModuleManifest], tags=["SD-MAC"])
def list_modules(
    platform_component: PlatformComponent | None = Query(  # noqa: B008 -- FastAPI DI default
        default=None, description="Filter by owning platform component"
    ),
    validation_status: ValidationStatus | None = Query(  # noqa: B008 -- FastAPI DI default
        default=None, description="Filter by module validation status"
    ),
) -> list[ModuleManifest]:
    """List ``module_manifest`` records (SD-MAC), with optional filters."""
    results: list[ModuleManifest] = []
    for rec in store.list_modules():
        if (
            platform_component is not None
            and rec.get("platform_component") != platform_component.value
        ):
            continue
        if (
            validation_status is not None
            and rec.get("validation_status") != validation_status.value
        ):
            continue
        results.append(ModuleManifest(**rec))
    return results


@app.get("/v1/modules/{module_id}", response_model=ModuleManifest, tags=["SD-MAC"])
def get_module(module_id: str) -> ModuleManifest:
    """Return the full ``module_manifest`` for ``module_id`` (SD-MAC)."""
    rec = store.get_module(module_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"module '{module_id}' not found")
    return ModuleManifest(**rec)


# ---------------------------------------------------------------------------
# Operational endpoint (NOT a record type; documented as operational)
# ---------------------------------------------------------------------------


@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
def healthz() -> HealthResponse:
    """Operational liveness probe with seeded record counts.

    This endpoint is operational only and is intentionally outside the
    versioned ``/v1`` record API surface.
    """
    return HealthResponse(
        status="ok",
        events_loaded=len(store.events),
        forecasts_loaded=len(store.forecasts),
        scenarios_loaded=len(store.scenarios),
        modules_loaded=len(store.modules),
    )
