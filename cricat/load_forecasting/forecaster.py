"""Deterministic day-ahead power-load forecaster for CRICAT.

This module trains an open-source scikit-learn regressor to predict day-ahead
hourly power load for a public ISO/RTO region from calendar features
(hour-of-day, day-of-week, month, weekend flag, cyclical encodings) plus a
synthetic weather feature (temperature). It produces ``load_forecast_record``
documents that conform to the SD-MAC schema registry, including prediction
intervals derived from held-out residual quantiles.

Data
----
Training data is the bundled synthetic fixture
``shared/data_sources/fixtures/cricat/<region>_load_weather_hourly.csv``.

    Synthetic illustrative data generated for demonstration. NOT real agency
    data and NOT derived from any proprietary or employer source.

The fixtures are generated deterministically by
``shared/utilities/synthetic_data.py``. No real ISO/RTO market data is used and
no network access is performed.

Method
------
- Features: ``hour_of_day``, ``day_of_week``, ``month``, ``is_weekend``,
  cyclical (sin/cos) encodings of hour and day-of-year, and ``temp_c``.
- Model: :class:`sklearn.ensemble.GradientBoostingRegressor` (deterministic via
  ``random_state=42``).
- Split: a deterministic chronological train/test split (the last fraction of
  the series is held out) so MAPE reflects genuine out-of-sample performance and
  there is no look-ahead leakage.
- Prediction intervals: symmetric-by-quantile intervals built from the
  empirical quantiles of the held-out residuals (default central 80% interval),
  added to each point forecast.

All randomness is seeded; repeated runs are bit-for-bit identical.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from shared.utilities.io import read_csv, repo_root
from sklearn.ensemble import GradientBoostingRegressor

SEED = 42

# Public ISO/RTO regions that ship with synthetic training fixtures. Other
# schema-valid regions (MISO, NYISO, ...) have no bundled series, so training
# for them raises a clear error rather than silently failing.
_REGIONS_WITH_FIXTURES: tuple[str, ...] = ("PJM", "ERCOT")

# Model identifier embedded in every emitted ``load_forecast_record``. Names the
# open-source model that produced the forecast, per the schema's intent.
MODEL_ID: str = "cricat-gbr-dayahead-v0.1"

# Public-data source identifiers (synthetic fixture labels) recorded on every
# forecast. These are category labels for the demonstration fixtures — not real
# feeds and not proprietary identifiers.
INPUT_DATA_SOURCES: list[str] = [
    "synthetic_load_history",
    "synthetic_weather",
    "calendar_features",
]

# Feature columns the model consumes, in a fixed order so training and inference
# always align.
_FEATURE_COLUMNS: list[str] = [
    "hour_of_day",
    "day_of_week",
    "month",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "doy_sin",
    "doy_cos",
    "temp_c",
]


def _fixture_path(region: str) -> Any:
    """Absolute path to the bundled synthetic load+weather CSV for ``region``."""
    return (
        repo_root()
        / "shared"
        / "data_sources"
        / "fixtures"
        / "cricat"
        / f"{region.lower()}_load_weather_hourly.csv"
    )


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the model feature matrix from a raw load+weather frame.

    The raw fixture already carries ``hour_of_day``, ``day_of_week``,
    ``is_weekend``, ``day_of_year`` and ``temp_c``. Here we add ``month`` and
    cyclical (sin/cos) encodings so the tree model can exploit the periodicity
    of hour-of-day and day-of-year without treating them as unbounded integers.

    Returns a new DataFrame containing exactly :data:`_FEATURE_COLUMNS`.
    """
    out = pd.DataFrame(index=df.index)
    out["hour_of_day"] = df["hour_of_day"].astype(int)
    out["day_of_week"] = df["day_of_week"].astype(int)
    # Derive month from the ISO timestamp string (UTC).
    out["month"] = pd.to_datetime(df["timestamp_utc"], utc=True).dt.month.astype(int)
    out["is_weekend"] = df["is_weekend"].astype(int)
    # Cyclical encodings: hour over a 24h cycle, day-of-year over a ~365d cycle.
    hour = df["hour_of_day"].astype(float).to_numpy()
    doy = df["day_of_year"].astype(float).to_numpy()
    out["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    out["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    out["temp_c"] = df["temp_c"].astype(float)
    return out[_FEATURE_COLUMNS]


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean absolute percentage error in percent.

    Guards against division by zero by masking out any zero actuals (load is
    strictly positive in the synthetic fixtures, so the mask is a safety net,
    not an expected code path).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    nonzero = y_true != 0
    if not np.any(nonzero):
        raise ValueError("Cannot compute MAPE: all actual values are zero.")
    return float(
        np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100.0
    )


@dataclass
class LoadForecaster:
    """A trained day-ahead load forecaster for one ISO/RTO region.

    Hold the fitted scikit-learn model plus the metadata needed to build
    schema-conformant ``load_forecast_record`` documents with prediction
    intervals. Build instances via :func:`train`.

    Attributes:
        region: The ISO/RTO region this model was trained for (e.g. "PJM").
        model: The fitted :class:`GradientBoostingRegressor`.
        residual_low: Lower residual quantile (e.g. 10th percentile) on the
            held-out split, used as the lower prediction-interval offset.
        residual_high: Upper residual quantile (e.g. 90th percentile), used as
            the upper prediction-interval offset.
        interval_level: Central interval coverage the residual quantiles target
            (e.g. 0.80 for an 80% interval).
        test_mape: Held-out MAPE (percent) recorded at training time.
        n_train: Number of training rows.
        n_test: Number of held-out test rows.
    """

    region: str
    model: GradientBoostingRegressor
    residual_low: float
    residual_high: float
    interval_level: float
    test_mape: float
    n_train: int
    n_test: int
    feature_columns: list[str] = field(default_factory=lambda: list(_FEATURE_COLUMNS))

    def _predict_point(self, features: pd.DataFrame) -> np.ndarray:
        """Run the fitted model on a feature frame and return point forecasts."""
        return self.model.predict(features[self.feature_columns].to_numpy())


def _normalize_region(region: str) -> str:
    """Validate and canonicalize a region name to upper-case.

    Raises ``ValueError`` listing the regions that have bundled fixtures if the
    requested region cannot be trained.
    """
    canon = region.strip().upper()
    if canon not in _REGIONS_WITH_FIXTURES:
        raise ValueError(
            f"No bundled synthetic training fixture for region {region!r}. "
            f"Regions with fixtures: {list(_REGIONS_WITH_FIXTURES)}."
        )
    return canon


def train(
    region: str,
    *,
    test_fraction: float = 0.2,
    interval_level: float = 0.80,
) -> LoadForecaster:
    """Train a deterministic day-ahead load forecaster for ``region``.

    Loads the bundled synthetic load+weather fixture for ``region``, builds
    calendar + weather features, fits a :class:`GradientBoostingRegressor`
    (``random_state=42``) on a chronological training split, and records the
    held-out residual quantiles and MAPE.

    Args:
        region: ISO/RTO region with a bundled fixture ("PJM" or "ERCOT").
        test_fraction: Fraction of the (chronologically ordered) series held out
            for evaluation. Must be in (0, 1).
        interval_level: Central coverage targeted by the residual-quantile
            prediction interval (e.g. 0.80 => 10th/90th residual percentiles).

    Returns:
        A fitted :class:`LoadForecaster`.

    Raises:
        ValueError: If ``region`` has no fixture, or ``test_fraction`` /
            ``interval_level`` are out of range.
    """
    if not (0.0 < test_fraction < 1.0):
        raise ValueError(f"test_fraction must be in (0, 1), got {test_fraction!r}")
    if not (0.0 < interval_level < 1.0):
        raise ValueError(f"interval_level must be in (0, 1), got {interval_level!r}")

    canon = _normalize_region(region)
    df = read_csv(_fixture_path(canon))
    # Chronological order is essential for an honest day-ahead split: sort by the
    # ISO timestamp so the held-out tail is strictly "the future" relative to the
    # training head (no look-ahead leakage).
    df = df.sort_values("timestamp_utc").reset_index(drop=True)

    features = _build_features(df)
    target = df["load_mw"].astype(float).to_numpy()

    n = len(df)
    n_test = max(1, int(round(n * test_fraction)))
    n_train = n - n_test
    if n_train < 24:
        raise ValueError(
            f"Not enough training rows ({n_train}) after a {test_fraction:.0%} "
            f"holdout on {n} rows."
        )

    x_train = features.iloc[:n_train].to_numpy()
    x_test = features.iloc[n_train:].to_numpy()
    y_train = target[:n_train]
    y_test = target[n_train:]

    # GradientBoostingRegressor is deterministic given random_state. Modest depth
    # and learning rate keep it well-behaved on the small synthetic series.
    model = GradientBoostingRegressor(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=1.0,
        random_state=SEED,
    )
    model.fit(x_train, y_train)

    # Held-out residuals drive both the MAPE report and the prediction interval.
    y_pred_test = model.predict(x_test)
    residuals = y_test - y_pred_test
    test_mape = _mape(y_test, y_pred_test)

    # Residual quantiles for the central `interval_level` interval. For an 80%
    # interval we take the 10th and 90th percentiles of the held-out residuals.
    lower_q = (1.0 - interval_level) / 2.0
    upper_q = 1.0 - lower_q
    residual_low = float(np.quantile(residuals, lower_q))
    residual_high = float(np.quantile(residuals, upper_q))

    return LoadForecaster(
        region=canon,
        model=model,
        residual_low=residual_low,
        residual_high=residual_high,
        interval_level=interval_level,
        test_mape=test_mape,
        n_train=n_train,
        n_test=n_test,
    )


def _iso(dt: datetime) -> str:
    """Render a UTC datetime as an ISO-8601 'Z' string (schema date-time)."""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def predict_day_ahead(
    region: str,
    *,
    forecaster: LoadForecaster | None = None,
    issued_at_utc: datetime | None = None,
    horizon_hours: int = 24,
    forecast_id_prefix: str = "CRICAT-FC",
) -> list[dict[str, Any]]:
    """Produce day-ahead hourly ``load_forecast_record`` documents for ``region``.

    For each hour in the forecast window (default the 24 hours starting one day
    after ``issued_at_utc``), this builds the model features deterministically
    from the calendar position plus a synthetic seasonal/diurnal temperature
    proxy, runs the fitted model, and attaches a prediction interval from the
    held-out residual quantiles.

    Args:
        region: ISO/RTO region ("PJM" or "ERCOT").
        forecaster: A pre-trained :class:`LoadForecaster`. If ``None``, a model
            is trained on the fly via :func:`train` (deterministic).
        issued_at_utc: Issuance time. Defaults to a fixed synthetic reference
            epoch so output is reproducible. The target window starts 24h later.
        horizon_hours: Number of hourly records to emit (default 24).
        forecast_id_prefix: Prefix for generated ``forecast_id`` values.

    Returns:
        A list of ``load_forecast_record`` dicts conforming to the schema
        registry, one per hour of the window.

    Raises:
        ValueError: If ``region`` has no fixture or ``horizon_hours`` < 1.
    """
    if horizon_hours < 1:
        raise ValueError(f"horizon_hours must be >= 1, got {horizon_hours!r}")

    canon = _normalize_region(region)
    fc = forecaster if forecaster is not None else train(canon)
    if fc.region != canon:
        raise ValueError(
            f"Provided forecaster is for {fc.region!r}, not requested {canon!r}."
        )

    # Fixed synthetic issuance epoch keeps the output reproducible. This is a
    # demonstration reference time, not a claim about any real forecast run.
    if issued_at_utc is None:
        issued_at_utc = datetime(2026, 3, 12, 0, 0, 0, tzinfo=UTC)
    else:
        issued_at_utc = issued_at_utc.astimezone(UTC)

    window_start = issued_at_utc + timedelta(hours=24)

    # Build the per-hour feature rows from the calendar position. The synthetic
    # temperature proxy mirrors the fixture generator's seasonal+diurnal shape so
    # inference features stay in-distribution with training.
    rows: list[dict[str, Any]] = []
    target_times: list[datetime] = []
    for h in range(horizon_hours):
        ts = window_start + timedelta(hours=h)
        doy = ts.timetuple().tm_yday
        temp_c = (
            12.0
            + 10.0 * np.sin(2 * np.pi * (doy - 80) / 365.25)
            + 4.0 * np.sin(2 * np.pi * (ts.hour - 15) / 24)
        )
        rows.append(
            {
                "hour_of_day": ts.hour,
                "day_of_week": ts.weekday(),
                "is_weekend": int(ts.weekday() >= 5),
                "day_of_year": doy,
                "temp_c": round(float(temp_c), 2),
                "timestamp_utc": _iso(ts),
            }
        )
        target_times.append(ts)

    feat_df = _build_features(pd.DataFrame(rows))
    point = fc._predict_point(feat_df)

    records: list[dict[str, Any]] = []
    for i, ts in enumerate(target_times):
        predicted = float(round(point[i], 1))
        low = float(round(predicted + fc.residual_low, 1))
        high = float(round(predicted + fc.residual_high, 1))
        # Enforce ordering low <= predicted <= high even if residual quantiles
        # are asymmetric and one bound crosses the point forecast.
        low = min(low, predicted)
        high = max(high, predicted)
        records.append(
            {
                "forecast_id": f"{forecast_id_prefix}-{canon}-{i:04d}",
                "iso_region": canon,
                "forecast_issued_at_utc": _iso(issued_at_utc),
                "target_window_start_utc": _iso(ts),
                "target_window_end_utc": _iso(ts + timedelta(hours=1)),
                "predicted_load_mw": predicted,
                "prediction_interval_low_mw": low,
                "prediction_interval_high_mw": high,
                "model_id": MODEL_ID,
                "input_data_sources": list(INPUT_DATA_SOURCES),
            }
        )
    return records


def report_mape(region: str, *, test_fraction: float = 0.2) -> float:
    """Train on ``region`` and return the held-out MAPE (percent).

    Convenience wrapper around :func:`train` for the validation-roadmap
    methodology demonstration. The returned MAPE is computed on a chronological
    holdout of the bundled synthetic series, so it measures genuine
    out-of-sample error (on synthetic data, clearly labeled).

    Args:
        region: ISO/RTO region ("PJM" or "ERCOT").
        test_fraction: Holdout fraction passed through to :func:`train`.

    Returns:
        Held-out MAPE in percent (finite, non-negative).
    """
    return train(region, test_fraction=test_fraction).test_mape
