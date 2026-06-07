"""Transparent, deterministic GEA event scoring.

This module turns a per-candidate-event feature dict into a calibrated
``severity_score`` and ``confidence``, both in the closed interval [0, 1], and
assembles full ``supply_disruption_event`` records conforming to the SD-MAC
schema registry.

Method (fully transparent — no black box)
-----------------------------------------
``severity_score``
    A fixed-weight linear aggregation of three normalized feature signals
    (``sanctions_intensity``, ``ais_disruption``, ``weather_stress``), each
    expected in [0, 1]. The weights (:data:`FEATURE_WEIGHTS`) sum to 1.0, so the
    weighted sum is itself bounded to [0, 1]; we additionally clip defensively.

``confidence``
    A logistic squashing of an *evidence-agreement* signal: more contributing
    public source categories and a higher mean feature magnitude raise
    confidence. The logistic maps the real line to (0, 1); we report it
    rounded, bounded to [0, 1].

Both quantities are pure deterministic functions of the input feature dict —
the same input always yields the same output (no RNG, no global state).

All inputs are synthetic illustrative data generated for demonstration; no real
agency data and no proprietary or employer source. Emitted ``public_evidence_refs``
are illustrative ``https://example.org/synthetic-evidence/...`` placeholders —
they are NOT real agency URLs presented as real. No network access is performed.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from gea.ingestion.loaders import (
    COMMODITY_ENUM,
    SOURCE_CATEGORIES,
    assemble_event_features,
)

# Severity weights over the three normalized feature signals. They sum to 1.0,
# which guarantees the weighted sum stays in [0, 1] when each feature is in
# [0, 1]. Sanctions and AIS disruption are weighted slightly above weather
# because direct supply-chain signals are more indicative of a disruption than
# ambient weather stress — a transparent, documented modeling choice.
FEATURE_WEIGHTS: dict[str, float] = {
    "sanctions_intensity": 0.40,
    "ais_disruption": 0.35,
    "weather_stress": 0.25,
}

# Logistic parameters for the confidence signal. The signal combines the number
# of agreeing source categories (more independent corroboration -> higher
# confidence) with the mean feature magnitude. Constants are fixed (not fit) so
# the mapping is fully reproducible and inspectable.
_CONF_INTERCEPT = -1.20  # baseline log-odds with one weak source
_CONF_SOURCE_GAIN = 0.55  # log-odds added per contributing source category
_CONF_MAGNITUDE_GAIN = 1.80  # log-odds added for fully saturated features

# Tolerance for floating-point bound checks (records are rounded to 3 dp).
_EPS = 1e-9


def _sigmoid(x: float) -> float:
    """Numerically stable logistic squashing of ``x`` into (0, 1)."""
    # Stable form avoids overflow in exp for large-magnitude inputs.
    if x >= 0:
        z = np.exp(-x)
        return float(1.0 / (1.0 + z))
    z = np.exp(x)
    return float(z / (1.0 + z))


def _coerce_feature(value: Any) -> float:
    """Coerce a feature to a float clipped to [0, 1]; missing -> 0.0."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0.0
    return float(np.clip(float(value), 0.0, 1.0))


def score_event(features: dict[str, Any]) -> dict[str, float]:
    """Score one candidate event.

    Parameters
    ----------
    features
        A feature dict carrying (at minimum) the normalized signals
        ``sanctions_intensity``, ``ais_disruption``, and ``weather_stress`` in
        [0, 1]. Optionally ``n_sources`` (int) and/or ``source_categories``
        (list[str]) to inform confidence; if neither is present, the number of
        non-zero feature signals is used as a proxy.

    Returns
    -------
    dict
        ``{"severity_score": float, "confidence": float}`` — each in [0, 1],
        rounded to 3 decimal places. Deterministic: identical input -> identical
        output.
    """
    sanctions = _coerce_feature(features.get("sanctions_intensity"))
    ais = _coerce_feature(features.get("ais_disruption"))
    weather = _coerce_feature(features.get("weather_stress"))

    # --- severity: fixed-weight linear aggregation, clipped to [0, 1] -------
    severity = (
        FEATURE_WEIGHTS["sanctions_intensity"] * sanctions
        + FEATURE_WEIGHTS["ais_disruption"] * ais
        + FEATURE_WEIGHTS["weather_stress"] * weather
    )
    severity = float(np.clip(severity, 0.0, 1.0))

    # --- confidence: logistic over an evidence-agreement signal -------------
    # Number of corroborating source categories. Prefer explicit metadata; fall
    # back to a proxy = count of non-zero feature signals.
    if "n_sources" in features and features["n_sources"] is not None:
        n_sources = int(features["n_sources"])
    elif features.get("source_categories"):
        n_sources = len(features["source_categories"])
    else:
        n_sources = int(sanctions > 0) + int(ais > 0) + int(weather > 0)

    mean_magnitude = (sanctions + ais + weather) / 3.0
    log_odds = (
        _CONF_INTERCEPT
        + _CONF_SOURCE_GAIN * float(n_sources)
        + _CONF_MAGNITUDE_GAIN * mean_magnitude
    )
    confidence = _sigmoid(log_odds)

    return {
        "severity_score": round(severity, 3),
        "confidence": round(confidence, 3),
    }


def _public_evidence_refs(commodity: str, region_iso: str, idx: int) -> list[str]:
    """Build illustrative synthetic evidence URLs for an emitted record.

    These are clearly illustrative ``example.org`` placeholders — NOT real
    agency endpoints presented as real. They are valid URIs so emitted records
    satisfy the ``array<url>`` schema constraint.
    """
    base = "https://example.org/synthetic-evidence"
    return [
        f"{base}/{commodity}/{region_iso}/{idx:04d}/1",
        f"{base}/{commodity}/{region_iso}/{idx:04d}/2",
    ]


def _to_iso_z(ts: Any) -> str:
    """Render a pandas/py timestamp as an ISO-8601 UTC string with 'Z' suffix."""
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_events(
    features: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """Run ingestion -> scoring and emit ``supply_disruption_event`` records.

    Parameters
    ----------
    features
        Optional pre-assembled feature frame (as from
        :func:`gea.ingestion.loaders.assemble_event_features`). When omitted,
        the bundled synthetic fixtures are loaded and assembled.

    Returns
    -------
    list[dict]
        ``supply_disruption_event`` records, each carrying every schema field:
        ``event_id``, ``detected_at_utc``, ``commodity``, ``region_iso``,
        ``source_categories``, ``severity_score``, ``confidence``, and
        ``public_evidence_refs``. Deterministic and ordered by ``region_iso``
        (the feature frame's order).

    Notes
    -----
    The records validate against the ``supply_disruption_event`` schema via
    :func:`shared.utilities.schema_loader.validate_record`. ``commodity`` is
    constrained to :data:`COMMODITY_ENUM`; ``source_categories`` are drawn from
    :data:`SOURCE_CATEGORIES` (public category labels only).
    """
    if features is None:
        features = assemble_event_features()

    events: list[dict[str, Any]] = []
    if features.empty:
        return events

    for idx, row in features.reset_index(drop=True).iterrows():
        scored = score_event(row.to_dict())

        commodity = str(row["commodity"])
        # Defensive: keep commodity within the schema enum.
        if commodity not in COMMODITY_ENUM:
            commodity = "crude_oil"

        # Keep only recognized public source-category labels, sorted & unique.
        raw_sources = row.get("source_categories") or []
        source_categories = sorted(
            {s for s in raw_sources if s in SOURCE_CATEGORIES}
        )

        region_iso = str(row["region_iso"])

        events.append(
            {
                "event_id": f"GEA-EVT-{int(idx):04d}",
                "detected_at_utc": _to_iso_z(row["detected_at_utc"]),
                "commodity": commodity,
                "region_iso": region_iso,
                "source_categories": source_categories,
                "severity_score": scored["severity_score"],
                "confidence": scored["confidence"],
                "public_evidence_refs": _public_evidence_refs(
                    commodity, region_iso, int(idx)
                ),
            }
        )

    return events
