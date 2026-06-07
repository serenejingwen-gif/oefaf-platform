"""CRICAT day-ahead load-forecasting subpackage.

Exposes the deterministic scikit-learn forecaster that produces
``load_forecast_record`` documents (with prediction intervals) for public
ISO/RTO regions, trained on bundled synthetic load+weather fixtures.
"""

from __future__ import annotations

from cricat.load_forecasting.forecaster import (
    LoadForecaster,
    predict_day_ahead,
    report_mape,
    train,
)

__all__ = [
    "LoadForecaster",
    "train",
    "predict_day_ahead",
    "report_mape",
]
