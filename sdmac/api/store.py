"""In-memory record store for the SD-MAC API, seeded from bundled fixtures.

This store decouples the API from the GEA and CRICAT Python packages: instead of
importing those modules directly (which would couple boot to their build state),
it serves from the bundled synthetic fixture JSON and the schema-registry
manifest YAMLs:

  * ``supply_disruption_event`` records   <- shared/.../gea/supply_disruption_events.json
  * ``load_forecast_record`` records      <- shared/.../cricat/load_forecast_records.json
  * ``capacity_allocation_scenario``      <- shared/.../cricat/capacity_allocation_scenarios.json
  * ``module_manifest`` records           <- sdmac/manifests/*.yaml

If any fixture file is missing, the store falls back to a minimal inline
synthetic sample so the API remains self-sufficient and bootable.

``POST /v1/scenarios`` creates a new ``capacity_allocation_scenario`` and
persists it in this store so a subsequent ``GET /v1/scenarios/{id}`` returns it.
Scenario derivation is deterministic (seeded, ``SEED = 42``) and uses transparent
grid-modeling math (reserve margin and a monotone probability-of-stress map), so
the same request always yields the same scenario.

All records held by this store are synthetic illustrative data generated for
demonstration. They are NOT real agency data and are NOT derived from any
proprietary or employer source.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from shared.utilities.io import read_json, repo_root

# Deterministic seed mandated by the build contract. Used to make synthetic
# scenario derivation reproducible without any global RNG state.
SEED = 42

# Default demand / capacity assumptions (MW) for POST-created scenarios. These
# are synthetic illustrative magnitudes only; they are not tied to any real or
# proprietary grid data. Per-region jitter is derived deterministically from the
# request so identical requests produce identical scenarios.
_BASE_DEMAND_MW = 80_000.0
_BASE_CAPACITY_MW = 88_000.0

# A stress driver present in a request nudges assumed demand up and assumed
# capacity down (transparent, illustrative weights in MW).
_DRIVER_DEMAND_DELTA_MW = 6_500.0
_DRIVER_CAPACITY_DELTA_MW = 4_000.0


def _fixtures_dir() -> Path:
    """Absolute path to the bundled synthetic fixtures directory."""
    return repo_root() / "shared" / "data_sources" / "fixtures"


def _manifests_dir() -> Path:
    """Absolute path to the schema-registry module manifests directory."""
    return repo_root() / "sdmac" / "manifests"


def _stable_unit_float(*parts: str) -> float:
    """Deterministically map string parts to a float in [0, 1).

    Uses a SHA-256 digest of the seed-prefixed, joined parts so the result is
    stable across processes and Python hash randomization (unlike ``hash()``).
    """
    key = f"{SEED}:" + "|".join(parts)
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    # Take 8 bytes -> integer -> normalize into [0, 1).
    value = int.from_bytes(digest[:8], "big")
    return value / float(1 << 64)


def _reserve_margin_pct(demand_mw: float, capacity_mw: float) -> float:
    """Reserve margin as a percent of demand: (capacity - demand) / demand * 100.

    Mirrors the transparent CRICAT grid-modeling definition. Returns 0.0 when
    demand is non-positive (degenerate input) rather than dividing by zero.
    """
    if demand_mw <= 0:
        return 0.0
    return (capacity_mw - demand_mw) / demand_mw * 100.0


# Logistic parameters for the probability-of-stress map.
# Mirrors cricat.grid_modeling.reserve.probability_of_stress (midpoint, steepness
# kept in sync). The canonical definition lives in that module; the API stays
# decoupled from the cricat package, so the constants are copied here verbatim
# rather than imported. P(margin=0) = 0.5 exactly.
_STRESS_LOGISTIC_MIDPOINT_PCT = 0.0
_STRESS_LOGISTIC_STEEPNESS = 0.15


def _probability_of_stress(reserve_margin_pct: float) -> float:
    """Monotone-decreasing map from reserve margin (%) to P(stress) in [0, 1].

    A logistic squashing centered at a zero reserve margin: as the reserve margin
    falls (tighter grid), stress probability rises toward 1; as it grows,
    probability falls toward 0; at a zero reserve margin it is exactly 0.5.
    Deterministic and clipped to [0, 1].

    Mirrors cricat.grid_modeling.reserve.probability_of_stress (midpoint,
    steepness kept in sync) so the API and the CRICAT package agree.
    """
    import math

    z = _STRESS_LOGISTIC_STEEPNESS * (reserve_margin_pct - _STRESS_LOGISTIC_MIDPOINT_PCT)
    # 1 / (1 + exp(+z)) is decreasing in z, hence decreasing in the margin.
    # Guard against overflow for extreme margins so we never raise on inf.
    if z > 700:  # exp(700) is near the float64 ceiling
        prob = 0.0
    elif z < -700:
        prob = 1.0
    else:
        prob = 1.0 / (1.0 + math.exp(z))
    return max(0.0, min(1.0, prob))


# Minimal inline synthetic fallbacks (used only if a fixture file is missing),
# so the API can still boot and serve schema-conformant records.
_FALLBACK_EVENTS: list[dict[str, Any]] = [
    {
        "event_id": "GEA-EVT-FALLBACK-0",
        "detected_at_utc": "2026-01-01T00:00:00Z",
        "commodity": "crude_oil",
        "region_iso": "USA",
        "source_categories": ["weather"],
        "severity_score": 0.5,
        "confidence": 0.5,
        "public_evidence_refs": ["https://example.org/public-evidence/fallback/0"],
    }
]

_FALLBACK_FORECASTS: list[dict[str, Any]] = [
    {
        "forecast_id": "CRICAT-FC-FALLBACK-0",
        "iso_region": "PJM",
        "forecast_issued_at_utc": "2026-03-12T00:00:00Z",
        "target_window_start_utc": "2026-03-13T00:00:00Z",
        "target_window_end_utc": "2026-03-14T00:00:00Z",
        "predicted_load_mw": 70000.0,
        "prediction_interval_low_mw": 67000.0,
        "prediction_interval_high_mw": 73000.0,
        # Must match cricat.load_forecasting.forecaster.MODEL_ID. The API stays
        # decoupled from the cricat package, so the value is mirrored here rather
        # than imported.
        "model_id": "cricat-gbr-dayahead-v0.1",
        "input_data_sources": ["synthetic_load_history", "synthetic_weather", "calendar_features"],
    }
]

_FALLBACK_SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario_id": "CRICAT-SCN-FALLBACK-0",
        "scenario_label": "fallback_summer_heat_pjm",
        "stress_drivers": ["heatwave"],
        "time_horizon_hours": 24,
        "regions": ["PJM"],
        "assumed_demand_mw": 90000.0,
        "assumed_available_capacity_mw": 88000.0,
        "reserve_margin_pct": -2.22,
        # Consistent with the unified probability-of-stress map (midpoint=0,
        # steepness=0.15) at a -2.22% reserve margin.
        "probability_of_stress": 0.582,
        "data_provenance": ["https://example.org/public-provenance/fallback/0"],
    }
]

_FALLBACK_MANIFEST: dict[str, Any] = {
    "module_id": "sdmac-api",
    "module_name": "SD-MAC Public Analytics API",
    "platform_component": "sdmac",
    "license": "MIT",
    "maintainers": ["<JING_WEN_TO_FILL: maintainer handle or institutional affiliation>"],
    "public_dependencies": ["fastapi==0.128.0", "pydantic==2.12.5"],
    "data_inputs": ["supply_disruption_event"],
    "outputs": ["supply_disruption_event"],
    "validation_status": "draft",
    "documentation_url": "<JING_WEN_TO_FILL: documentation URL>",
}


class RecordStore:
    """Mutable in-memory store of platform records, seeded from fixtures.

    Read-side collections (events, forecasts, manifests) are seeded once at
    construction. Scenarios are seeded from a fixture and then grown by
    ``POST /v1/scenarios`` for the lifetime of the process.
    """

    def __init__(self) -> None:
        self.events: dict[str, dict[str, Any]] = {}
        self.forecasts: list[dict[str, Any]] = []
        self.scenarios: dict[str, dict[str, Any]] = {}
        self.modules: dict[str, dict[str, Any]] = {}
        # Monotonic counter used to mint deterministic ids for new scenarios.
        self._scenario_seq: int = 0
        self._seed_from_fixtures()

    # -- seeding ----------------------------------------------------------

    def _seed_from_fixtures(self) -> None:
        """Load events, forecasts, scenarios, and manifests into the store."""
        self._seed_events()
        self._seed_forecasts()
        self._seed_scenarios()
        self._seed_modules()

    def _seed_events(self) -> None:
        path = _fixtures_dir() / "gea" / "supply_disruption_events.json"
        records = read_json(path) if path.is_file() else list(_FALLBACK_EVENTS)
        for rec in records:
            self.events[rec["event_id"]] = rec

    def _seed_forecasts(self) -> None:
        path = _fixtures_dir() / "cricat" / "load_forecast_records.json"
        self.forecasts = read_json(path) if path.is_file() else list(_FALLBACK_FORECASTS)

    def _seed_scenarios(self) -> None:
        path = _fixtures_dir() / "cricat" / "capacity_allocation_scenarios.json"
        records = read_json(path) if path.is_file() else list(_FALLBACK_SCENARIOS)
        for rec in records:
            self.scenarios[rec["scenario_id"]] = rec
        # Continue the seed sequence past the highest fixture index so minted
        # ids never collide with seeded ids.
        self._scenario_seq = len(self.scenarios)

    def _seed_modules(self) -> None:
        manifest_dir = _manifests_dir()
        loaded = False
        if manifest_dir.is_dir():
            for yaml_path in sorted(manifest_dir.glob("*.yaml")):
                with yaml_path.open("r", encoding="utf-8") as fh:
                    rec = yaml.safe_load(fh)
                if isinstance(rec, dict) and rec.get("module_id"):
                    self.modules[rec["module_id"]] = rec
                    loaded = True
        if not loaded:
            self.modules[_FALLBACK_MANIFEST["module_id"]] = dict(_FALLBACK_MANIFEST)

    # -- read access ------------------------------------------------------

    def list_events(self) -> list[dict[str, Any]]:
        """All events in stable insertion order."""
        return list(self.events.values())

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        return self.events.get(event_id)

    def list_forecasts(self) -> list[dict[str, Any]]:
        return list(self.forecasts)

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        return self.scenarios.get(scenario_id)

    def list_modules(self) -> list[dict[str, Any]]:
        return list(self.modules.values())

    def get_module(self, module_id: str) -> dict[str, Any] | None:
        return self.modules.get(module_id)

    # -- write access -----------------------------------------------------

    def create_scenario(
        self,
        scenario_label: str,
        stress_drivers: list[str],
        regions: list[str],
        time_horizon_hours: int,
    ) -> dict[str, Any]:
        """Create, persist, and return a deterministic scenario record.

        The demand/capacity assumptions, reserve margin, and probability of
        stress are derived from the request via transparent grid-modeling math.
        A small per-request jitter (deterministic, in [0, 1)) makes distinct
        labels produce distinct magnitudes while keeping identical requests
        identical. The minted ``scenario_id`` uses a monotonic sequence index.
        """
        n_drivers = len(stress_drivers)

        # Deterministic jitter in [-1, 1) MW-scale factor derived from the label
        # and regions. No RNG state; reproducible across processes.
        jitter = _stable_unit_float(scenario_label, *sorted(regions)) * 2.0 - 1.0
        demand = _BASE_DEMAND_MW + n_drivers * _DRIVER_DEMAND_DELTA_MW + jitter * 1_500.0
        capacity = _BASE_CAPACITY_MW - n_drivers * _DRIVER_CAPACITY_DELTA_MW + jitter * 800.0

        reserve = _reserve_margin_pct(demand, capacity)
        prob = _probability_of_stress(reserve)

        scenario_id = f"CRICAT-SCN-{self._scenario_seq:04d}"
        self._scenario_seq += 1

        record: dict[str, Any] = {
            "scenario_id": scenario_id,
            "scenario_label": scenario_label,
            "stress_drivers": list(stress_drivers),
            "time_horizon_hours": int(time_horizon_hours),
            "regions": list(regions),
            "assumed_demand_mw": round(demand, 1),
            "assumed_available_capacity_mw": round(capacity, 1),
            "reserve_margin_pct": round(reserve, 2),
            "probability_of_stress": round(prob, 3),
            "data_provenance": [
                f"https://example.org/public-provenance/{scenario_label}/0",
                f"https://example.org/public-provenance/{scenario_label}/1",
            ],
        }
        self.scenarios[scenario_id] = record
        return record
