"""Deterministic synthetic-fixture generators for the oefaf-platform codebase.

Every generator here is seeded (``seed=42``) so repeated runs produce identical
fixtures, and every fixture directory is stamped with the required
synthetic-data disclaimer. No network access is performed; all values are drawn
from local NumPy RNGs.

IMPORTANT (legal/integrity):
    All data produced by this module is synthetic illustrative data generated
    for demonstration. It is NOT real agency data and is NOT derived from any
    proprietary or employer source. The provider/source *names* embedded in the
    fixtures (e.g. "ais", "satellite", "noaa_ncep") are public-source category
    *labels* only — no real records, parameters, or proprietary content are
    used. Any URLs are illustrative ``example.org`` placeholders, not real
    agency endpoints.

Run as a script to materialize everything:

    python -m shared.utilities.synthetic_data
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from shared.utilities.io import (
    SYNTHETIC_DISCLAIMER,
    ensure_dir,
    repo_root,
    write_csv,
    write_json,
    write_readme,
)

SEED = 42

# Day-ahead model identifier stamped on the generated CRICAT load_forecast_record
# fixture rows. This MUST stay equal to
# cricat.load_forecasting.forecaster.MODEL_ID (the GradientBoosting day-ahead
# model that actually emits these records), or the fixture would mislabel which
# model produced the forecast. It is hardcoded rather than imported because
# ``shared.utilities`` is imported during ``cricat.load_forecasting.forecaster``
# initialization (forecaster -> shared.utilities.io -> shared.utilities.__init__
# -> synthetic_data), so importing MODEL_ID here would be a circular import.
# cricat/tests/test_fixture_model_id.py asserts the two stay in sync.
_FORECASTER_MODEL_ID = "cricat-gbr-dayahead-v0.1"

# Fixed anchor timestamp so every generated record is reproducible. This is a
# synthetic reference epoch for the demonstration data, not a claim about any
# real event time.
_ANCHOR = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


# --------------------------------------------------------------------------- #
# Schema-registry bootstrap (idempotent)
# --------------------------------------------------------------------------- #
# The four schemas are the authoritative schema-registry contract.
# We write them only if absent so this fixture generator is runnable standalone
# (it needs them to validate sample records) without clobbering an existing copy
# authored by the packaging track. Field names/types/enums match the registry
# exactly.
_SCHEMA_YAML: dict[str, str] = {
    "supply_disruption_event": """# schema: supply_disruption_event
# Version: 0.1 draft
# Purpose: GEA event record describing a detected supply-disruption signal from public sources
schema: supply_disruption_event
version: 0.1
fields:
  - name: event_id
    type: string
    description: Stable unique identifier for the disruption event
  - name: detected_at_utc
    type: timestamp
    units: ISO-8601 UTC
    description: Time the event was first detected from public sources
  - name: commodity
    type: enum
    values: [crude_oil, natural_gas, refined_products, electricity, lng, coal, agricultural]
    description: Affected commodity category
  - name: region_iso
    type: string
    description: ISO 3166-1 alpha-3 country code or recognized region code (e.g., "USA", "EUR")
  - name: source_categories
    type: array<string>
    description: Public source categories supporting detection (e.g., "ais", "satellite", "sanctions", "weather")
  - name: severity_score
    type: float
    units: 0.0_to_1.0
    description: Calibrated supply-disruption severity score
  - name: confidence
    type: float
    units: 0.0_to_1.0
    description: Calibration-based confidence score
  - name: public_evidence_refs
    type: array<url>
    description: Public source URLs supporting the event
""",
    "load_forecast_record": """# schema: load_forecast_record
# Version: 0.1 draft
# Purpose: CRICAT short-horizon power-load forecast record for a public ISO/RTO region
schema: load_forecast_record
version: 0.1
fields:
  - name: forecast_id
    type: string
    description: Unique identifier for this forecast issuance
  - name: iso_region
    type: enum
    values: [PJM, ERCOT, MISO, NYISO, ISO_NE, CAISO, SPP]
    description: Public ISO/RTO region
  - name: forecast_issued_at_utc
    type: timestamp
    units: ISO-8601 UTC
  - name: target_window_start_utc
    type: timestamp
    units: ISO-8601 UTC
  - name: target_window_end_utc
    type: timestamp
    units: ISO-8601 UTC
  - name: predicted_load_mw
    type: float
    units: megawatts
  - name: prediction_interval_low_mw
    type: float
    units: megawatts
  - name: prediction_interval_high_mw
    type: float
    units: megawatts
  - name: model_id
    type: string
    description: Identifier of the open-source model that produced the forecast
  - name: input_data_sources
    type: array<string>
    description: Public-data source identifiers used as features
""",
    "capacity_allocation_scenario": """# schema: capacity_allocation_scenario
# Version: 0.1 draft
# Purpose: CRICAT scenario for grid stress and capacity-allocation analysis
schema: capacity_allocation_scenario
version: 0.1
fields:
  - name: scenario_id
    type: string
  - name: scenario_label
    type: string
    description: Human-readable scenario name (e.g., "summer_2027_extreme_heat_pjm")
  - name: stress_drivers
    type: array<string>
    description: Public stress drivers (e.g., "heatwave", "cold_snap", "outage", "fuel_constraint")
  - name: time_horizon_hours
    type: integer
    units: hours
  - name: regions
    type: array<string>
    description: ISO/RTO regions in scope
  - name: assumed_demand_mw
    type: float
    units: megawatts
  - name: assumed_available_capacity_mw
    type: float
    units: megawatts
  - name: reserve_margin_pct
    type: float
    units: percent
  - name: probability_of_stress
    type: float
    units: 0.0_to_1.0
  - name: data_provenance
    type: array<url>
    description: Public-data provenance references
""",
    "module_manifest": """# schema: module_manifest
# Version: 0.1 draft
# Purpose: SD-MAC manifest describing a deployable module
schema: module_manifest
version: 0.1
fields:
  - name: module_id
    type: string
  - name: module_name
    type: string
  - name: platform_component
    type: enum
    values: [gea, cricat, sdmac, shared]
  - name: license
    type: string
    description: Open-source license identifier (e.g., "MIT")
  - name: maintainers
    type: array<string>
    description: Maintainer handles or institutional affiliations
  - name: public_dependencies
    type: array<string>
    description: Open-source dependencies with version constraints
  - name: data_inputs
    type: array<string>
    description: Public/licensed data inputs consumed
  - name: outputs
    type: array<string>
    description: Schema-registered output record types
  - name: validation_status
    type: enum
    values: [draft, internal_validated, public_validated]
  - name: documentation_url
    type: url
""",
}


def ensure_schema_registry() -> list[Path]:
    """Write the four registry YAML files if they do not already exist.

    Returns the list of files that this call created (empty if all four were
    already present). Existing files are never overwritten — the packaging track
    owns the canonical copies; this only bootstraps a standalone run.
    """
    registry_dir = ensure_dir(repo_root() / "sdmac" / "schema_registry")
    created: list[Path] = []
    for name, body in _SCHEMA_YAML.items():
        path = registry_dir / f"{name}.yaml"
        if not path.exists():
            path.write_text(body, encoding="utf-8")
            created.append(path)
    return created


# --------------------------------------------------------------------------- #
# Disclaimer helpers
# --------------------------------------------------------------------------- #
def _iso(dt: datetime) -> str:
    """Render a UTC datetime as an ISO-8601 string with a trailing 'Z'."""
    # Normalize to 'Z' suffix so timestamps are valid JSON Schema date-time.
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _disclaimer_comment() -> str:
    """Return the disclaimer as a leading CSV/text comment line."""
    return f"# {SYNTHETIC_DISCLAIMER}"


# --------------------------------------------------------------------------- #
# GEA fixtures
# --------------------------------------------------------------------------- #
def make_gea_fixtures() -> dict[str, list[Path]]:
    """Generate synthetic GEA fixtures.

    Produces (under ``shared/data_sources/fixtures/gea/``):
      - ``sanctions_events.csv`` — synthetic public-style sanctions entries
      - ``ais_vessel_positions.csv`` — synthetic AIS vessel positions
      - ``weather_observations.csv`` — synthetic weather observations
      - ``supply_disruption_events.json`` — sample ``supply_disruption_event``
        records the GEA API can serve.

    Deterministic via a seeded ``numpy`` RNG. The commodity/source labels are
    public *category* names only; no real or proprietary records are used.
    """
    rng = np.random.default_rng(SEED)
    out_dir = ensure_dir(repo_root() / "shared" / "data_sources" / "fixtures" / "gea")
    written: list[Path] = []

    commodities = [
        "crude_oil",
        "natural_gas",
        "refined_products",
        "electricity",
        "lng",
        "coal",
        "agricultural",
    ]
    regions = ["USA", "EUR", "RUS", "SAU", "CHN", "NGA", "AUS"]
    source_categories = ["ais", "satellite", "sanctions", "weather", "regulatory"]

    # --- sanctions_events.csv ---------------------------------------------
    n_sanctions = 24
    sanctions = pd.DataFrame(
        {
            "record_id": [f"SAN-{i:04d}" for i in range(n_sanctions)],
            "listed_at_utc": [
                _iso(_ANCHOR + timedelta(hours=int(h)))
                for h in rng.integers(0, 24 * 30, size=n_sanctions)
            ],
            # Synthetic entity labels — generic, not tied to any real list entry.
            "entity_label": [f"synthetic_entity_{i:03d}" for i in range(n_sanctions)],
            "program": rng.choice(
                ["energy", "shipping", "financial", "trade"], size=n_sanctions
            ),
            "region_iso": rng.choice(regions, size=n_sanctions),
        }
    )
    written.append(write_csv(sanctions, out_dir / "sanctions_events.csv"))

    # --- ais_vessel_positions.csv -----------------------------------------
    n_ais = 60
    ais = pd.DataFrame(
        {
            "synthetic_mmsi": [f"SYN{800000000 + i}" for i in range(n_ais)],
            "observed_at_utc": [
                _iso(_ANCHOR + timedelta(minutes=int(m)))
                for m in rng.integers(0, 60 * 24 * 10, size=n_ais)
            ],
            # Plausible but synthetic lat/lon over open ranges.
            "latitude": np.round(rng.uniform(-60.0, 70.0, size=n_ais), 4),
            "longitude": np.round(rng.uniform(-180.0, 180.0, size=n_ais), 4),
            "speed_knots": np.round(rng.uniform(0.0, 22.0, size=n_ais), 1),
            "cargo_category": rng.choice(
                ["crude_oil", "lng", "refined_products", "coal", "agricultural"],
                size=n_ais,
            ),
        }
    )
    written.append(write_csv(ais, out_dir / "ais_vessel_positions.csv"))

    # --- weather_observations.csv -----------------------------------------
    n_wx = 72
    wx = pd.DataFrame(
        {
            "station_id": [f"SYNWX{i % 12:02d}" for i in range(n_wx)],
            "observed_at_utc": [
                _iso(_ANCHOR + timedelta(hours=int(h))) for h in range(n_wx)
            ],
            "region_iso": rng.choice(regions, size=n_wx),
            "temp_c": np.round(rng.normal(12.0, 10.0, size=n_wx), 1),
            "wind_mps": np.round(np.abs(rng.normal(6.0, 3.0, size=n_wx)), 1),
            "precip_mm": np.round(np.abs(rng.normal(1.5, 2.0, size=n_wx)), 2),
        }
    )
    written.append(write_csv(wx, out_dir / "weather_observations.csv"))

    # --- supply_disruption_events.json (API-servable records) -------------
    n_events = 12
    events: list[dict[str, Any]] = []
    for i in range(n_events):
        commodity = commodities[i % len(commodities)]
        region = str(rng.choice(regions))
        n_src = int(rng.integers(1, 4))
        srcs = sorted(
            set(rng.choice(source_categories, size=n_src, replace=True).tolist())
        )
        severity = float(np.round(rng.uniform(0.05, 0.98), 3))
        confidence = float(np.round(rng.uniform(0.40, 0.99), 3))
        events.append(
            {
                "event_id": f"GEA-EVT-{i:04d}",
                "detected_at_utc": _iso(
                    _ANCHOR + timedelta(hours=int(rng.integers(0, 24 * 30)))
                ),
                "commodity": commodity,
                "region_iso": region,
                "source_categories": srcs,
                "severity_score": severity,
                "confidence": confidence,
                # Illustrative placeholder evidence URLs (example.org), not real
                # agency endpoints. Valid URIs so they satisfy the schema.
                "public_evidence_refs": [
                    f"https://example.org/public-evidence/{commodity}/{i:04d}/{k}"
                    for k in range(int(rng.integers(1, 3)) + 1)
                ],
            }
        )
    written.append(
        write_json(events, out_dir / "supply_disruption_events.json")
    )

    write_readme(
        out_dir,
        "GEA (Geopolitical-Event Analytics) synthetic fixtures: sanctions-style "
        "events, AIS vessel positions, weather observations, and sample "
        "`supply_disruption_event` records served by the GEA API. Source-category "
        "labels (ais, satellite, sanctions, weather) are public category names "
        "only; URLs are illustrative `example.org` placeholders.",
    )
    return {"gea": written}


# --------------------------------------------------------------------------- #
# CRICAT fixtures
# --------------------------------------------------------------------------- #
def _make_load_series(rng: np.random.Generator, region: str, n_days: int) -> pd.DataFrame:
    """Build a synthetic hourly load + weather series for one ISO region.

    The load is a transparent deterministic function of calendar features
    (hour-of-day double peak, weekday/weekend, seasonal sinusoid) plus a
    temperature-driven term and bounded noise — enough signal to train a
    day-ahead model. Region only sets the base magnitude. No real grid data.
    """
    n_hours = n_days * 24
    base = {"PJM": 95000.0, "ERCOT": 55000.0}.get(region, 60000.0)
    rows: list[dict[str, Any]] = []
    for h in range(n_hours):
        ts = _ANCHOR + timedelta(hours=h)
        hour = ts.hour
        dow = ts.weekday()  # 0=Mon
        doy = ts.timetuple().tm_yday
        # Morning + evening peak shape (two cosine humps).
        daily = 0.5 * np.cos((hour - 8) / 24 * 2 * np.pi) + 0.5 * np.cos(
            (hour - 19) / 24 * 2 * np.pi
        )
        weekend = -0.06 if dow >= 5 else 0.0
        seasonal = 0.12 * np.sin(2 * np.pi * doy / 365.25)
        # Synthetic temperature: seasonal mean + diurnal swing + noise.
        temp_c = (
            12.0
            + 10.0 * np.sin(2 * np.pi * (doy - 80) / 365.25)
            + 4.0 * np.sin(2 * np.pi * (hour - 15) / 24)
            + float(rng.normal(0, 1.5))
        )
        # Cooling/heating load both raise demand away from a ~18C comfort point.
        temp_effect = 0.004 * (abs(temp_c - 18.0))
        load = base * (1.0 + 0.18 * daily + seasonal + weekend + temp_effect)
        load += float(rng.normal(0, base * 0.01))  # bounded measurement noise
        rows.append(
            {
                "iso_region": region,
                "timestamp_utc": _iso(ts),
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_weekend": int(dow >= 5),
                "day_of_year": doy,
                "temp_c": round(temp_c, 2),
                "load_mw": round(float(load), 1),
            }
        )
    return pd.DataFrame(rows)


def make_cricat_fixtures(n_days: int = 75) -> dict[str, list[Path]]:
    """Generate synthetic CRICAT fixtures.

    Produces (under ``shared/data_sources/fixtures/cricat/``):
      - ``pjm_load_weather_hourly.csv`` — ~75 days of hourly synthetic load+weather
      - ``ercot_load_weather_hourly.csv`` — same for ERCOT
      - ``load_forecast_records.json`` — sample ``load_forecast_record`` rows
      - ``capacity_allocation_scenarios.json`` — sample scenarios

    Deterministic via a seeded RNG. ~75 days hourly (1800 rows/region) is enough
    to train/test a day-ahead model. No real ISO/RTO data is used.
    """
    rng = np.random.default_rng(SEED)
    out_dir = ensure_dir(
        repo_root() / "shared" / "data_sources" / "fixtures" / "cricat"
    )
    written: list[Path] = []

    pjm = _make_load_series(rng, "PJM", n_days)
    ercot = _make_load_series(rng, "ERCOT", n_days)
    written.append(write_csv(pjm, out_dir / "pjm_load_weather_hourly.csv"))
    written.append(write_csv(ercot, out_dir / "ercot_load_weather_hourly.csv"))

    # --- sample load_forecast_record rows ---------------------------------
    forecasts: list[dict[str, Any]] = []
    for i, region in enumerate(["PJM", "ERCOT", "PJM", "MISO"]):
        issued = _ANCHOR + timedelta(days=70, hours=i)
        start = issued + timedelta(hours=24)
        end = start + timedelta(hours=24)
        predicted = float(np.round(rng.uniform(50000, 100000), 1))
        spread = float(np.round(predicted * 0.04, 1))
        forecasts.append(
            {
                "forecast_id": f"CRICAT-FC-{i:04d}",
                "iso_region": region,
                "forecast_issued_at_utc": _iso(issued),
                "target_window_start_utc": _iso(start),
                "target_window_end_utc": _iso(end),
                "predicted_load_mw": predicted,
                "prediction_interval_low_mw": round(predicted - spread, 1),
                "prediction_interval_high_mw": round(predicted + spread, 1),
                # Must match cricat.load_forecasting.forecaster.MODEL_ID (the
                # GradientBoosting day-ahead model that actually emits these).
                "model_id": _FORECASTER_MODEL_ID,
                "input_data_sources": [
                    "synthetic_load_history",
                    "synthetic_weather",
                    "calendar_features",
                ],
            }
        )
    written.append(write_json(forecasts, out_dir / "load_forecast_records.json"))

    # --- sample capacity_allocation_scenario rows -------------------------
    scenario_specs = [
        ("summer_extreme_heat_pjm", ["heatwave", "outage"], ["PJM"], 24),
        ("winter_cold_snap_ercot", ["cold_snap", "fuel_constraint"], ["ERCOT"], 48),
        ("multi_region_demand_surge", ["heatwave"], ["PJM", "MISO"], 72),
    ]
    scenarios: list[dict[str, Any]] = []
    for i, (label, drivers, regions, horizon) in enumerate(scenario_specs):
        demand = float(np.round(rng.uniform(60000, 110000), 1))
        # Available capacity drawn near demand so reserve margins are realistic.
        capacity = float(np.round(demand * rng.uniform(0.95, 1.20), 1))
        reserve_margin_pct = round((capacity - demand) / demand * 100.0, 2)
        # Monotone decreasing in reserve margin, clipped to [0, 1].
        prob = float(np.clip(0.5 - 0.03 * reserve_margin_pct, 0.0, 1.0))
        scenarios.append(
            {
                "scenario_id": f"CRICAT-SCN-{i:04d}",
                "scenario_label": label,
                "stress_drivers": drivers,
                "time_horizon_hours": horizon,
                "regions": regions,
                "assumed_demand_mw": demand,
                "assumed_available_capacity_mw": capacity,
                "reserve_margin_pct": reserve_margin_pct,
                "probability_of_stress": round(prob, 3),
                "data_provenance": [
                    f"https://example.org/public-provenance/{label}/{k}"
                    for k in range(2)
                ],
            }
        )
    written.append(
        write_json(scenarios, out_dir / "capacity_allocation_scenarios.json")
    )

    write_readme(
        out_dir,
        "CRICAT (Climate-Risk Integrated Capacity-Allocation Toolkit) synthetic "
        "fixtures: ~75 days of hourly synthetic load+weather time series for PJM "
        "and ERCOT (enough to train/test a day-ahead model), plus sample "
        "`load_forecast_record` and `capacity_allocation_scenario` records. "
        "Load values are generated from calendar + synthetic-temperature features; "
        "no real ISO/RTO market data is used. URLs are illustrative placeholders.",
    )
    return {"cricat": written}


# --------------------------------------------------------------------------- #
# SD-MAC fixtures
# --------------------------------------------------------------------------- #
def make_sdmac_fixtures() -> dict[str, list[Path]]:
    """Generate synthetic SD-MAC fixtures for the schema-validation demo.

    Produces (under ``shared/data_sources/fixtures/sdmac/``):
      - ``module_manifests.json`` — sample ``module_manifest`` records
        (validation_status: draft) for the demo and the /v1/modules endpoint.

    Maintainer handles and documentation URLs are preserved as the required
    placeholder convention (``<JING_WEN_TO_FILL: ...>``) — we do not invent real
    handles or URLs.
    """
    out_dir = ensure_dir(
        repo_root() / "shared" / "data_sources" / "fixtures" / "sdmac"
    )
    written: list[Path] = []

    module_specs = [
        ("gea-scoring", "GEA Event Scoring", "gea", ["supply_disruption_event"]),
        (
            "cricat-load-forecasting",
            "CRICAT Day-Ahead Load Forecasting",
            "cricat",
            ["load_forecast_record"],
        ),
        (
            "cricat-grid-modeling",
            "CRICAT Grid Modeling & Scenarios",
            "cricat",
            ["capacity_allocation_scenario"],
        ),
        ("sdmac-api", "SD-MAC Public API", "sdmac", ["module_manifest"]),
    ]
    manifests: list[dict[str, Any]] = []
    for mod_id, name, component, outputs in module_specs:
        manifests.append(
            {
                "module_id": mod_id,
                "module_name": name,
                "platform_component": component,
                "license": "MIT",
                # Placeholder convention preserved — no invented handles.
                "maintainers": [
                    "<JING_WEN_TO_FILL: maintainer handle/affiliation>"
                ],
                "public_dependencies": [
                    "pandas>=2.2",
                    "numpy>=1.26",
                    "scikit-learn>=1.5",
                    "fastapi>=0.128",
                    "pydantic>=2.12",
                ],
                "data_inputs": ["synthetic_public_fixtures"],
                "outputs": outputs,
                "validation_status": "draft",
                # Placeholder convention preserved — no invented docs URL.
                "documentation_url": "<JING_WEN_TO_FILL: docs URL>",
            }
        )
    written.append(write_json(manifests, out_dir / "module_manifests.json"))

    write_readme(
        out_dir,
        "SD-MAC (Sector-Wide Deployable Modular Analytics Commons) synthetic "
        "fixtures: sample `module_manifest` records (validation_status: draft) "
        "used by the schema-validation demo and the SD-MAC /v1/modules endpoint. "
        "Maintainer handles and documentation URLs are intentionally preserved as "
        "`<JING_WEN_TO_FILL: ...>` placeholders.",
    )
    return {"sdmac": written}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _write_fixtures_root_readme() -> Path:
    """Write the top-level README covering the whole fixtures tree."""
    fixtures_root = ensure_dir(
        repo_root() / "shared" / "data_sources" / "fixtures"
    )
    body = (
        "This directory and all of its subdirectories contain synthetic fixtures "
        "used to make the oefaf-platform codebase runnable offline for "
        "demonstration. Subtrees: `gea/`, `cricat/`, `sdmac/`.\n\n"
        "- The data was generated deterministically (seed=42) by "
        "`shared/utilities/synthetic_data.py`.\n"
        "- Provider/source names appearing in fixtures are public-source category "
        "labels only.\n"
        "- All URLs are illustrative `example.org` placeholders or "
        "`<JING_WEN_TO_FILL: ...>` placeholders — they are not real endpoints.\n"
        "- No proprietary or employer content of any kind is present."
    )
    return write_readme(fixtures_root, body)


def generate_all() -> dict[str, Any]:
    """Materialize the schema registry (if needed) and all synthetic fixtures.

    Returns a summary dict mapping each group to the list of files written,
    including the fixtures-tree README and any registry files bootstrapped.
    """
    summary: dict[str, Any] = {}
    summary["schema_registry_created"] = [str(p) for p in ensure_schema_registry()]
    summary["fixtures_readme"] = str(_write_fixtures_root_readme())
    summary.update(make_gea_fixtures())
    summary.update(make_cricat_fixtures())
    summary.update(make_sdmac_fixtures())
    return summary


if __name__ == "__main__":
    import json as _json

    result = generate_all()
    # Print a stable, machine-readable summary of what was written.
    print(_json.dumps(result, indent=2, default=str))
