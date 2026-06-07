"""Capacity-allocation scenario builder for CRICAT.

Assemble ``capacity_allocation_scenario`` documents (per the SD-MAC schema
registry) from a small set of analyst-supplied assumptions. The builder computes
the reserve margin and probability of stress from :mod:`cricat.grid_modeling`
and stamps a deterministic scenario id.

Inputs and outputs are non-proprietary. The bundled example scenarios under
``cricat/scenarios/fixtures/`` are synthetic illustrative data generated for
demonstration; they are NOT real agency data and NOT derived from any
proprietary or employer source. No network access is performed.
"""

from __future__ import annotations

import hashlib
from typing import Any

from cricat.grid_modeling.reserve import probability_of_stress, reserve_margin_pct

# Default data-provenance entry preserved as the required placeholder convention
# — we do not invent verified public URLs. Callers may pass real public
# provenance refs explicitly via ``data_provenance``.
_DEFAULT_PROVENANCE: list[str] = [
    "<JING_WEN_TO_FILL: verified public data-provenance URL(s) for this scenario>"
]


def _deterministic_scenario_id(scenario_label: str, regions: list[str]) -> str:
    """Build a stable scenario id from the label and regions.

    Deterministic (no RNG, no timestamp) so the same inputs always yield the
    same id — important for reproducible fixtures and round-trip tests. The hash
    is a short, content-derived suffix; the prefix keeps ids human-scannable.
    """
    key = f"{scenario_label}|{'|'.join(regions)}".encode()
    digest = hashlib.sha256(key).hexdigest()[:8]
    return f"CRICAT-SCN-{digest}"


def build_scenario(
    scenario_label: str,
    stress_drivers: list[str],
    regions: list[str],
    time_horizon_hours: int,
    assumed_demand_mw: float,
    assumed_available_capacity_mw: float,
    *,
    data_provenance: list[str] | None = None,
) -> dict[str, Any]:
    """Build a ``capacity_allocation_scenario`` document.

    Computes ``reserve_margin_pct`` and ``probability_of_stress`` from the
    assumed demand and capacity, and returns a dict conforming to the schema
    registry's ``capacity_allocation_scenario`` definition.

    Args:
        scenario_label: Human-readable scenario name
            (e.g. "summer_2027_extreme_heat_pjm").
        stress_drivers: Public stress drivers
            (e.g. ["heatwave", "outage"]).
        regions: ISO/RTO regions in scope (e.g. ["PJM"]).
        time_horizon_hours: Scenario horizon in hours (must be >= 1).
        assumed_demand_mw: Assumed peak demand in megawatts (must be > 0).
        assumed_available_capacity_mw: Assumed available capacity in megawatts.
        data_provenance: Optional list of public-data provenance URLs. If
            omitted, a ``<JING_WEN_TO_FILL: ...>`` placeholder is used — the
            builder never invents verified public URLs.

    Returns:
        A ``capacity_allocation_scenario`` dict.

    Raises:
        ValueError: If inputs are out of range (empty regions, non-positive
            demand, horizon < 1).
    """
    if not regions:
        raise ValueError("regions must be a non-empty list of ISO/RTO regions.")
    if time_horizon_hours < 1:
        raise ValueError(
            f"time_horizon_hours must be >= 1, got {time_horizon_hours!r}"
        )
    # reserve_margin_pct guards demand > 0; surface the same error early/clearly.
    margin = round(reserve_margin_pct(assumed_demand_mw, assumed_available_capacity_mw), 2)
    prob = round(probability_of_stress(margin), 3)

    provenance = list(data_provenance) if data_provenance else list(_DEFAULT_PROVENANCE)

    return {
        "scenario_id": _deterministic_scenario_id(scenario_label, list(regions)),
        "scenario_label": scenario_label,
        "stress_drivers": list(stress_drivers),
        "time_horizon_hours": int(time_horizon_hours),
        "regions": list(regions),
        "assumed_demand_mw": float(assumed_demand_mw),
        "assumed_available_capacity_mw": float(assumed_available_capacity_mw),
        "reserve_margin_pct": margin,
        "probability_of_stress": prob,
        "data_provenance": provenance,
    }
