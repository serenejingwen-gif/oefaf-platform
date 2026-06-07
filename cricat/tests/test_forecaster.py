"""Tests for the CRICAT day-ahead load forecaster.

Covers held-out MAPE finiteness and sanity, ``load_forecast_record`` schema
conformance of emitted forecasts, prediction-interval ordering, determinism,
and rejection of regions without bundled fixtures.
"""

from __future__ import annotations

import math

import pytest
from shared.utilities.schema_loader import validate_record

from cricat.load_forecasting.forecaster import (
    _REGIONS_WITH_FIXTURES,
    LoadForecaster,
    predict_day_ahead,
    report_mape,
    train,
)

REGIONS = list(_REGIONS_WITH_FIXTURES)


@pytest.mark.parametrize("region", REGIONS)
def test_report_mape_finite_and_sane(region):
    # MAPE must be finite, non-negative, and well under 100% — a model that
    # cannot beat 100% error on this synthetic series would signal a real bug.
    mape = report_mape(region)
    assert math.isfinite(mape)
    assert mape >= 0.0
    assert mape < 100.0, f"{region} MAPE unexpectedly high: {mape}"


@pytest.mark.parametrize("region", REGIONS)
def test_train_returns_forecaster(region):
    fc = train(region)
    assert isinstance(fc, LoadForecaster)
    assert fc.region == region
    assert fc.n_train > 0 and fc.n_test > 0
    # Residual quantiles must be ordered (lower <= upper).
    assert fc.residual_low <= fc.residual_high


@pytest.mark.parametrize("region", REGIONS)
def test_predict_day_ahead_schema_conformance(region):
    records = predict_day_ahead(region, horizon_hours=24)
    assert len(records) == 24
    for rec in records:
        # Every emitted record must validate against the registry schema.
        assert validate_record(rec, "load_forecast_record") is True
        assert rec["iso_region"] == region
        assert rec["model_id"]
        assert isinstance(rec["input_data_sources"], list)
        assert len(rec["input_data_sources"]) >= 1


@pytest.mark.parametrize("region", REGIONS)
def test_prediction_interval_ordering(region):
    records = predict_day_ahead(region, horizon_hours=24)
    for rec in records:
        low = rec["prediction_interval_low_mw"]
        point = rec["predicted_load_mw"]
        high = rec["prediction_interval_high_mw"]
        # Interval must bracket the point forecast.
        assert low <= point <= high
        # Load is strictly positive in this synthetic regime.
        assert point > 0


def test_predict_day_ahead_is_deterministic():
    # Same inputs -> bit-for-bit identical records (seeded model, fixed epoch).
    a = predict_day_ahead("PJM", horizon_hours=12)
    b = predict_day_ahead("PJM", horizon_hours=12)
    assert a == b


def test_predict_day_ahead_reuses_forecaster():
    # Passing a pre-trained forecaster must match training on the fly.
    fc = train("PJM")
    from_fc = predict_day_ahead("PJM", forecaster=fc, horizon_hours=6)
    fresh = predict_day_ahead("PJM", horizon_hours=6)
    assert from_fc == fresh


def test_train_rejects_region_without_fixture():
    with pytest.raises(ValueError):
        train("NYISO")  # schema-valid region, but no bundled training fixture


def test_predict_rejects_mismatched_forecaster():
    fc_pjm = train("PJM")
    with pytest.raises(ValueError):
        predict_day_ahead("ERCOT", forecaster=fc_pjm)
