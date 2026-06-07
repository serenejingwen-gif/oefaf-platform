"""Pydantic v2 models mirroring the SD-MAC schema registry field-for-field.

Each model corresponds to one record type defined in
``sdmac/schema_registry/*.yaml``. Field names, types,
enum value sets, and the closed ``[0, 1]`` ranges on calibrated scores are kept
identical to the registry so that:

  * the FastAPI response/request shapes match the documented schema exactly, and
  * every payload the API returns also validates against the registry JSON
    Schema via :func:`shared.utilities.schema_loader.validate_record`.

All record instances served by the API are synthetic illustrative data
generated for demonstration. They are NOT real agency data and are NOT derived
from any proprietary or employer source.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enumerations (mirror the registry ``enum`` value sets exactly).
# ---------------------------------------------------------------------------


class Commodity(StrEnum):
    """``supply_disruption_event.commodity`` enum (GEA)."""

    crude_oil = "crude_oil"
    natural_gas = "natural_gas"
    refined_products = "refined_products"
    electricity = "electricity"
    lng = "lng"
    coal = "coal"
    agricultural = "agricultural"


class IsoRegion(StrEnum):
    """``load_forecast_record.iso_region`` enum (CRICAT)."""

    PJM = "PJM"
    ERCOT = "ERCOT"
    MISO = "MISO"
    NYISO = "NYISO"
    ISO_NE = "ISO_NE"
    CAISO = "CAISO"
    SPP = "SPP"


class PlatformComponent(StrEnum):
    """``module_manifest.platform_component`` enum (SD-MAC)."""

    gea = "gea"
    cricat = "cricat"
    sdmac = "sdmac"
    shared = "shared"


class ValidationStatus(StrEnum):
    """``module_manifest.validation_status`` enum (SD-MAC)."""

    draft = "draft"
    internal_validated = "internal_validated"
    public_validated = "public_validated"


# ---------------------------------------------------------------------------
# Full record models (one per schema-registry record type).
# ---------------------------------------------------------------------------


class SupplyDisruptionEvent(BaseModel):
    """Full ``supply_disruption_event`` record (GEA).

    Mirrors ``sdmac/schema_registry/supply_disruption_event.yaml`` v0.1.
    """

    event_id: str = Field(..., description="Stable unique identifier for the disruption event")
    detected_at_utc: str = Field(..., description="Detection time (ISO-8601 UTC)")
    commodity: Commodity = Field(..., description="Affected commodity category")
    region_iso: str = Field(..., description="ISO 3166-1 alpha-3 country/region code")
    source_categories: list[str] = Field(
        ..., description="Public source categories supporting detection"
    )
    # severity_score / confidence are calibrated to the closed interval [0, 1]
    # to match the registry "0.0_to_1.0" unit marker.
    severity_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated severity score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibration-based confidence")
    public_evidence_refs: list[str] = Field(
        ..., description="Public source URLs supporting the event"
    )


class EventSummary(BaseModel):
    """Compact ``supply_disruption_event`` projection for ``GET /v1/events``.

    The list-endpoint contract specifies it returns only
    ``event_id``, ``detected_at_utc``, ``severity_score``, and
    ``public_evidence_refs[]`` (not the full record).
    """

    event_id: str
    detected_at_utc: str
    severity_score: float = Field(..., ge=0.0, le=1.0)
    public_evidence_refs: list[str]


class LoadForecastRecord(BaseModel):
    """Full ``load_forecast_record`` (CRICAT).

    Mirrors ``sdmac/schema_registry/load_forecast_record.yaml`` v0.1.
    """

    forecast_id: str = Field(..., description="Unique identifier for this forecast issuance")
    iso_region: IsoRegion = Field(..., description="Public ISO/RTO region")
    forecast_issued_at_utc: str = Field(..., description="Issuance time (ISO-8601 UTC)")
    target_window_start_utc: str = Field(..., description="Target window start (ISO-8601 UTC)")
    target_window_end_utc: str = Field(..., description="Target window end (ISO-8601 UTC)")
    predicted_load_mw: float = Field(..., description="Point load forecast (MW)")
    prediction_interval_low_mw: float = Field(..., description="Lower prediction-interval bound (MW)")
    prediction_interval_high_mw: float = Field(..., description="Upper prediction-interval bound (MW)")
    model_id: str = Field(..., description="Identifier of the open-source model used")
    input_data_sources: list[str] = Field(..., description="Public-data source identifiers used")


class CapacityAllocationScenario(BaseModel):
    """Full ``capacity_allocation_scenario`` (CRICAT).

    Mirrors ``sdmac/schema_registry/capacity_allocation_scenario.yaml`` v0.1.
    """

    scenario_id: str = Field(..., description="Stable unique identifier for the scenario")
    scenario_label: str = Field(..., description="Human-readable scenario name")
    stress_drivers: list[str] = Field(..., description="Public stress drivers")
    time_horizon_hours: int = Field(..., description="Scenario time horizon (hours)")
    regions: list[str] = Field(..., description="ISO/RTO regions in scope")
    assumed_demand_mw: float = Field(..., description="Assumed peak demand (MW)")
    assumed_available_capacity_mw: float = Field(..., description="Assumed available capacity (MW)")
    reserve_margin_pct: float = Field(..., description="Reserve margin as percent of demand")
    probability_of_stress: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated probability of grid stress"
    )
    data_provenance: list[str] = Field(..., description="Public-data provenance references")


class ScenarioCreateRequest(BaseModel):
    """Request body for ``POST /v1/scenarios`` (CRICAT).

    Per the endpoint contract the caller supplies only ``scenario_label``,
    ``stress_drivers[]``, ``regions[]``, and ``time_horizon_hours``. The server
    deterministically derives the demand/capacity assumptions, reserve margin,
    and probability of stress (transparent grid-modeling logic, seeded) and
    assigns the ``scenario_id``.
    """

    scenario_label: str = Field(..., description="Human-readable scenario name")
    stress_drivers: list[str] = Field(..., description="Public stress drivers in scope")
    regions: list[str] = Field(..., description="ISO/RTO regions in scope")
    time_horizon_hours: int = Field(..., gt=0, description="Scenario time horizon (hours)")


class ModuleManifest(BaseModel):
    """Full ``module_manifest`` record (SD-MAC).

    Mirrors ``sdmac/schema_registry/module_manifest.yaml`` v0.1.
    """

    module_id: str = Field(..., description="Stable module identifier")
    module_name: str = Field(..., description="Human-readable module name")
    platform_component: PlatformComponent = Field(..., description="Owning platform component")
    license: str = Field(..., description="Open-source license identifier (e.g. MIT)")
    maintainers: list[str] = Field(..., description="Maintainer handles or affiliations")
    public_dependencies: list[str] = Field(..., description="Open-source dependencies")
    data_inputs: list[str] = Field(..., description="Public/licensed data inputs consumed")
    outputs: list[str] = Field(..., description="Schema-registered output record types")
    validation_status: ValidationStatus = Field(..., description="Module validation status")
    documentation_url: str = Field(..., description="Documentation URL")


class HealthResponse(BaseModel):
    """Operational health payload for ``GET /healthz`` (not a record type)."""

    status: str = Field(..., description="Liveness indicator; 'ok' when the app is serving")
    events_loaded: int = Field(..., description="Count of seeded supply_disruption_event records")
    forecasts_loaded: int = Field(..., description="Count of seeded load_forecast_record records")
    scenarios_loaded: int = Field(..., description="Count of capacity_allocation_scenario records")
    modules_loaded: int = Field(..., description="Count of module_manifest records")
