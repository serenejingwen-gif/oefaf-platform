"""Guard against model_id drift between the forecaster and its fixture.

The bundled ``load_forecast_record`` fixture records carry a ``model_id`` that
names the model which produced them. That identifier must match the model
identifier the shipped forecaster actually stamps on every record it emits
(:data:`cricat.load_forecasting.forecaster.MODEL_ID`); otherwise the fixture
mislabels which model generated the forecast.

All inputs are synthetic illustrative data generated for demonstration; no real
agency data and no proprietary or employer source.
"""

from __future__ import annotations

from shared.utilities.io import read_json, repo_root

from cricat.load_forecasting.forecaster import MODEL_ID


def _fixture_path():
    return (
        repo_root()
        / "shared"
        / "data_sources"
        / "fixtures"
        / "cricat"
        / "load_forecast_records.json"
    )


def test_fixture_model_id_matches_forecaster() -> None:
    """Every fixture forecast record's model_id equals the forecaster MODEL_ID."""
    records = read_json(_fixture_path())
    assert records, "load_forecast_records.json fixture is empty"
    for rec in records:
        assert rec["model_id"] == MODEL_ID, (
            f"fixture model_id {rec['model_id']!r} != forecaster MODEL_ID "
            f"{MODEL_ID!r} (drift between fixture and shipped model)"
        )
