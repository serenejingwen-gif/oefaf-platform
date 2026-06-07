"""Tests for the CRICAT capacity-allocation scenario builder.

Covers ``capacity_allocation_scenario`` schema conformance, that the reserve
margin and probability of stress are computed consistently with the
grid-modeling math, determinism of the scenario id, the placeholder-preserving
provenance default, conformance of the bundled fixtures, and input guards.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from shared.utilities.io import repo_root
from shared.utilities.schema_loader import validate_record

from cricat.grid_modeling.reserve import probability_of_stress, reserve_margin_pct
from cricat.scenarios.builder import build_scenario


def _example_scenario(**overrides):
    spec = dict(
        scenario_label="summer_2027_extreme_heat_pjm",
        stress_drivers=["heatwave", "forced_outage"],
        regions=["PJM"],
        time_horizon_hours=24,
        assumed_demand_mw=151000.0,
        assumed_available_capacity_mw=148500.0,
    )
    spec.update(overrides)
    return build_scenario(**spec)


def test_build_scenario_schema_conformance():
    scenario = _example_scenario()
    assert validate_record(scenario, "capacity_allocation_scenario") is True


def test_build_scenario_reserve_and_probability_consistent():
    demand, capacity = 151000.0, 148500.0
    scenario = _example_scenario(
        assumed_demand_mw=demand, assumed_available_capacity_mw=capacity
    )
    expected_margin = round(reserve_margin_pct(demand, capacity), 2)
    expected_prob = round(probability_of_stress(expected_margin), 3)
    assert scenario["reserve_margin_pct"] == pytest.approx(expected_margin)
    assert scenario["probability_of_stress"] == pytest.approx(expected_prob)
    # Probability stays bounded in [0, 1].
    assert 0.0 <= scenario["probability_of_stress"] <= 1.0


def test_shortfall_raises_stress_probability_above_surplus():
    # A capacity shortfall must yield a higher stress probability than surplus.
    shortfall = _example_scenario(
        assumed_demand_mw=100000.0, assumed_available_capacity_mw=95000.0
    )
    surplus = _example_scenario(
        assumed_demand_mw=100000.0, assumed_available_capacity_mw=120000.0
    )
    assert shortfall["probability_of_stress"] > surplus["probability_of_stress"]


def test_scenario_id_is_deterministic():
    a = _example_scenario()
    b = _example_scenario()
    assert a["scenario_id"] == b["scenario_id"]
    # Different label -> different id.
    c = _example_scenario(scenario_label="winter_2027_cold_snap_ercot", regions=["ERCOT"])
    assert c["scenario_id"] != a["scenario_id"]


def test_provenance_default_is_placeholder():
    scenario = _example_scenario()
    prov = scenario["data_provenance"]
    assert isinstance(prov, list) and len(prov) == 1
    # No invented URLs: the default must be the JING_WEN_TO_FILL placeholder.
    assert prov[0].startswith("<JING_WEN_TO_FILL:")


def test_provenance_override_is_used():
    refs = ["https://example.org/public-provenance/demo/0"]
    scenario = _example_scenario(data_provenance=refs)
    assert scenario["data_provenance"] == refs


def test_build_scenario_input_guards():
    with pytest.raises(ValueError):
        _example_scenario(regions=[])
    with pytest.raises(ValueError):
        _example_scenario(time_horizon_hours=0)
    with pytest.raises(ValueError):
        _example_scenario(assumed_demand_mw=0.0)


def test_bundled_scenario_fixtures_conform():
    fixtures_dir = repo_root() / "cricat" / "scenarios" / "fixtures"
    json_files = sorted(fixtures_dir.glob("*.json"))
    assert json_files, "expected at least one bundled scenario fixture"
    for path in json_files:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        assert validate_record(record, "capacity_allocation_scenario") is True
