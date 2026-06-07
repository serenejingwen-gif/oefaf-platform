"""Tests for GEA scoring: bounds, determinism, and monotonic sanity.

All inputs here are synthetic illustrative data generated for demonstration;
no real agency data and no proprietary or employer source.
"""

from __future__ import annotations

import pandas as pd
import pytest

from gea.ingestion.loaders import assemble_event_features
from gea.scoring.scorer import FEATURE_WEIGHTS, build_events, score_event

# A spread of hand-built feature dicts covering corners and interior points.
_FEATURE_CASES: list[dict[str, float]] = [
    {"sanctions_intensity": 0.0, "ais_disruption": 0.0, "weather_stress": 0.0, "n_sources": 0},
    {"sanctions_intensity": 1.0, "ais_disruption": 1.0, "weather_stress": 1.0, "n_sources": 5},
    {"sanctions_intensity": 0.5, "ais_disruption": 0.2, "weather_stress": 0.9, "n_sources": 3},
    {"sanctions_intensity": 0.3, "ais_disruption": 0.7, "weather_stress": 0.1, "n_sources": 2},
    {"sanctions_intensity": 0.85, "ais_disruption": 0.05, "weather_stress": 0.4, "n_sources": 1},
]


def test_feature_weights_sum_to_one():
    """Severity weights must sum to 1.0 so the weighted sum stays in [0, 1]."""
    assert sum(FEATURE_WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("features", _FEATURE_CASES)
def test_score_event_bounds(features):
    """severity_score and confidence must both lie in the closed interval [0, 1]."""
    result = score_event(features)
    assert set(result) == {"severity_score", "confidence"}
    for key in ("severity_score", "confidence"):
        assert 0.0 <= result[key] <= 1.0, f"{key}={result[key]} out of [0, 1]"


@pytest.mark.parametrize("features", _FEATURE_CASES)
def test_score_event_deterministic(features):
    """Same input -> same output, across repeated independent calls."""
    first = score_event(features)
    for _ in range(5):
        assert score_event(dict(features)) == first


def test_score_event_zero_features_minimal_severity():
    """All-zero features yield zero severity and a sub-0.5 (low) confidence."""
    result = score_event(
        {"sanctions_intensity": 0.0, "ais_disruption": 0.0, "weather_stress": 0.0, "n_sources": 0}
    )
    assert result["severity_score"] == 0.0
    assert result["confidence"] < 0.5


def test_score_event_saturated_features_high_severity():
    """All-saturated features yield severity == 1.0 (weights sum to 1)."""
    result = score_event(
        {"sanctions_intensity": 1.0, "ais_disruption": 1.0, "weather_stress": 1.0, "n_sources": 5}
    )
    assert result["severity_score"] == pytest.approx(1.0)


def test_score_event_monotonic_in_each_feature():
    """Increasing any single feature must not decrease the severity score."""
    base = {"sanctions_intensity": 0.2, "ais_disruption": 0.2, "weather_stress": 0.2, "n_sources": 3}
    base_sev = score_event(base)["severity_score"]
    for feat in ("sanctions_intensity", "ais_disruption", "weather_stress"):
        bumped = dict(base)
        bumped[feat] = 0.9
        assert score_event(bumped)["severity_score"] >= base_sev


def test_score_event_confidence_rises_with_more_sources():
    """More corroborating source categories -> higher confidence (monotone)."""
    common = {"sanctions_intensity": 0.5, "ais_disruption": 0.5, "weather_stress": 0.5}
    c1 = score_event({**common, "n_sources": 1})["confidence"]
    c3 = score_event({**common, "n_sources": 3})["confidence"]
    c5 = score_event({**common, "n_sources": 5})["confidence"]
    assert c1 < c3 < c5


def test_score_event_handles_missing_and_nan_features():
    """Missing keys and NaN values are treated as 0.0 without raising."""
    result = score_event({"sanctions_intensity": float("nan"), "n_sources": 1})
    assert 0.0 <= result["severity_score"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0


def test_score_event_clips_out_of_range_inputs():
    """Feature values outside [0, 1] are clipped, not propagated."""
    over = score_event(
        {"sanctions_intensity": 5.0, "ais_disruption": -2.0, "weather_stress": 0.5, "n_sources": 3}
    )
    # sanctions clipped to 1, ais clipped to 0 -> 0.40*1 + 0.35*0 + 0.25*0.5 = 0.525
    assert over["severity_score"] == pytest.approx(0.525, abs=1e-6)


# --------------------------------------------------------------------------- #
# Ingestion + end-to-end determinism
# --------------------------------------------------------------------------- #
def test_assemble_event_features_nonempty_and_bounded():
    """The assembled feature frame is non-empty with bounded normalized signals."""
    features = assemble_event_features()
    assert isinstance(features, pd.DataFrame)
    assert not features.empty
    for col in ("sanctions_intensity", "ais_disruption", "weather_stress"):
        assert (features[col] >= 0.0).all()
        assert (features[col] <= 1.0).all()
    # Every candidate event carries at least one contributing source category.
    assert (features["n_sources"] >= 1).all()


def test_assemble_event_features_deterministic():
    """Re-assembling from the seeded fixtures yields identical frames."""
    a = assemble_event_features()
    b = assemble_event_features()
    pd.testing.assert_frame_equal(a, b)


def test_build_events_nonempty_and_deterministic():
    """build_events emits a non-empty, reproducible list of records."""
    first = build_events()
    assert isinstance(first, list)
    assert len(first) > 0
    second = build_events()
    assert first == second


def test_build_events_score_bounds():
    """Every emitted record's severity and confidence lie in [0, 1]."""
    for rec in build_events():
        assert 0.0 <= rec["severity_score"] <= 1.0
        assert 0.0 <= rec["confidence"] <= 1.0
