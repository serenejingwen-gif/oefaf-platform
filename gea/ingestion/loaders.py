"""Load synthetic GEA fixtures and assemble per-candidate-event features.

This module reads the three bundled GEA input fixtures —

  * ``sanctions_events.csv``      (public sanctions-style listings)
  * ``ais_vessel_positions.csv``  (public-category AIS vessel positions)
  * ``weather_observations.csv``  (public-category weather observations)

— into pandas DataFrames, then derives a per-candidate-event feature frame
(one row per candidate disruption event) by aggregating the three feeds within
a region over a fixed observation window. The resulting frame feeds the
transparent GEA scorer (:mod:`gea.scoring.scorer`).

All data read here is synthetic illustrative data generated for demonstration.
It is NOT real agency data and is NOT derived from any proprietary or employer
source. Source-category labels are public category names only. No network
access is performed — fixtures are read from the local repository tree.

Determinism
-----------
Candidate events are derived purely from the (already deterministic, seed=42)
fixtures via sorted groupings and arithmetic only — there is no randomness in
this module, so ``assemble_event_features`` is reproducible across runs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from shared.utilities.io import read_csv, repo_root

# Commodity universe shared with the schema enum (supply_disruption_event.commodity).
# Used to map a region's dominant AIS cargo / sanctions program to a commodity.
COMMODITY_ENUM: tuple[str, ...] = (
    "crude_oil",
    "natural_gas",
    "refined_products",
    "electricity",
    "lng",
    "coal",
    "agricultural",
)

# The public source-category labels GEA tracks. These are category *names* only.
SOURCE_CATEGORIES: tuple[str, ...] = (
    "ais",
    "satellite",
    "sanctions",
    "weather",
    "regulatory",
)


def gea_fixtures_dir() -> Path:
    """Absolute path to the bundled synthetic GEA fixture directory."""
    return repo_root() / "shared" / "data_sources" / "fixtures" / "gea"


# --------------------------------------------------------------------------- #
# Raw fixture loaders
# --------------------------------------------------------------------------- #
def load_sanctions_events(path: str | Path | None = None) -> pd.DataFrame:
    """Load the synthetic sanctions-style listings fixture.

    Columns: ``record_id``, ``listed_at_utc``, ``entity_label``, ``program``,
    ``region_iso``. The timestamp column is parsed to timezone-aware UTC.
    """
    p = Path(path) if path is not None else gea_fixtures_dir() / "sanctions_events.csv"
    df = read_csv(p)
    df["listed_at_utc"] = pd.to_datetime(df["listed_at_utc"], utc=True)
    return df


def load_ais_positions(path: str | Path | None = None) -> pd.DataFrame:
    """Load the synthetic AIS vessel-position fixture.

    Columns: ``synthetic_mmsi``, ``observed_at_utc``, ``latitude``,
    ``longitude``, ``speed_knots``, ``cargo_category``. The timestamp column is
    parsed to timezone-aware UTC.
    """
    p = (
        Path(path)
        if path is not None
        else gea_fixtures_dir() / "ais_vessel_positions.csv"
    )
    df = read_csv(p)
    df["observed_at_utc"] = pd.to_datetime(df["observed_at_utc"], utc=True)
    return df


def load_weather_observations(path: str | Path | None = None) -> pd.DataFrame:
    """Load the synthetic weather-observation fixture.

    Columns: ``station_id``, ``observed_at_utc``, ``region_iso``, ``temp_c``,
    ``wind_mps``, ``precip_mm``. The timestamp column is parsed to
    timezone-aware UTC.
    """
    p = (
        Path(path)
        if path is not None
        else gea_fixtures_dir() / "weather_observations.csv"
    )
    df = read_csv(p)
    df["observed_at_utc"] = pd.to_datetime(df["observed_at_utc"], utc=True)
    return df


# --------------------------------------------------------------------------- #
# Feature assembly
# --------------------------------------------------------------------------- #
def _dominant_cargo_commodity(ais_region: pd.DataFrame) -> str:
    """Pick the region's most frequent AIS cargo category as the commodity.

    Falls back to ``"crude_oil"`` when a region has no AIS rows (so every
    candidate event still carries a valid commodity from the enum). Ties are
    broken deterministically by the COMMODITY_ENUM order.
    """
    if ais_region.empty:
        return "crude_oil"
    counts = ais_region["cargo_category"].value_counts()
    top = counts.max()
    # Deterministic tie-break: among the modal cargos, take the one that appears
    # earliest in the fixed commodity enum ordering.
    tied = sorted(
        [c for c, n in counts.items() if n == top],
        key=lambda c: COMMODITY_ENUM.index(c) if c in COMMODITY_ENUM else len(COMMODITY_ENUM),
    )
    chosen = tied[0]
    return chosen if chosen in COMMODITY_ENUM else "crude_oil"


def _weather_stress(weather_region: pd.DataFrame) -> float:
    """Compute a normalized [0, 1] weather-stress signal for a region.

    Combines temperature extremity (distance from an ~18 C comfort point),
    high wind, and precipitation into a transparent normalized index. Returns
    0.0 when a region has no weather observations.
    """
    if weather_region.empty:
        return 0.0
    # Temperature extremity: |T - 18| normalized by a 30 C reference span.
    temp_extremity = (weather_region["temp_c"] - 18.0).abs().mean() / 30.0
    # Wind: mean wind speed normalized by a 20 m/s reference.
    wind = weather_region["wind_mps"].mean() / 20.0
    # Precipitation: mean precip normalized by a 10 mm reference.
    precip = weather_region["precip_mm"].mean() / 10.0
    # Weighted blend, then clip to [0, 1]; weights favor temperature extremity.
    raw = 0.5 * temp_extremity + 0.3 * wind + 0.2 * precip
    return float(np.clip(raw, 0.0, 1.0))


def assemble_event_features(
    sanctions: pd.DataFrame | None = None,
    ais: pd.DataFrame | None = None,
    weather: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Join the three GEA feeds into a per-candidate-event feature frame.

    One candidate disruption event is produced per region that appears in any
    of the three feeds. For each region we derive transparent, normalized
    features in [0, 1] plus supporting metadata:

      * ``region_iso``               — the candidate region (groupby key)
      * ``commodity``                — dominant AIS cargo (enum-valid)
      * ``sanctions_intensity``      — sanctions count normalized by the
                                       busiest region's count
      * ``ais_disruption``           — fraction of slow / stationary vessels
                                       (speed < 3 knots) in the region
      * ``weather_stress``           — normalized weather-stress index
      * ``source_categories``        — sorted public source-category labels
                                       that contributed evidence for the region
      * ``n_sources``                — number of contributing source categories
      * ``earliest_signal_utc``      — earliest contributing timestamp (UTC)
      * ``detected_at_utc``          — detection time (latest contributing
                                       timestamp; when a region is "confirmed")

    Passing explicit frames is supported for testing; otherwise the bundled
    synthetic fixtures are loaded. The output is sorted by ``region_iso`` for
    deterministic ordering.
    """
    sanctions = load_sanctions_events() if sanctions is None else sanctions
    ais = load_ais_positions() if ais is None else ais
    weather = load_weather_observations() if weather is None else weather

    # Region universe = union of regions seen in sanctions and weather, plus a
    # synthetic region attribution for AIS (AIS rows have no region column, so
    # AIS contributes its signal to every region it could plausibly affect via
    # the global slow-vessel fraction — see below). We anchor the region set on
    # the feeds that carry region_iso.
    regions = sorted(
        set(sanctions["region_iso"].unique().tolist())
        | set(weather["region_iso"].unique().tolist())
    )

    # Sanctions intensity normalizer: the busiest region's sanctions count.
    sanctions_counts = sanctions.groupby("region_iso").size()
    max_sanctions = int(sanctions_counts.max()) if not sanctions_counts.empty else 1

    # AIS is region-agnostic in the fixtures (positions are global), so the
    # disruption signal is a global slow-vessel fraction applied uniformly. This
    # is a transparent, documented modeling choice for the demonstration data.
    if not ais.empty:
        global_ais_disruption = float((ais["speed_knots"] < 3.0).mean())
    else:
        global_ais_disruption = 0.0

    rows: list[dict[str, object]] = []
    for region in regions:
        san_r = sanctions[sanctions["region_iso"] == region]
        wx_r = weather[weather["region_iso"] == region]

        sanctions_intensity = (
            float(len(san_r) / max_sanctions) if max_sanctions > 0 else 0.0
        )
        weather_stress = _weather_stress(wx_r)
        commodity = _dominant_cargo_commodity(ais)  # global dominant cargo

        # Which public source categories contributed evidence for this region?
        contributing: list[str] = []
        timestamps: list[pd.Timestamp] = []
        if not san_r.empty:
            contributing.append("sanctions")
            timestamps.extend(san_r["listed_at_utc"].tolist())
        if not wx_r.empty:
            contributing.append("weather")
            timestamps.extend(wx_r["observed_at_utc"].tolist())
        if global_ais_disruption > 0.0:
            contributing.append("ais")
            # AIS timestamps are global; include their span for the time window.
            timestamps.extend(ais["observed_at_utc"].tolist())

        source_categories = sorted(set(contributing))
        if not source_categories:
            # A region with no contributing evidence is not a candidate event.
            continue

        earliest = min(timestamps)
        latest = max(timestamps)

        rows.append(
            {
                "region_iso": region,
                "commodity": commodity,
                "sanctions_intensity": round(float(np.clip(sanctions_intensity, 0, 1)), 6),
                "ais_disruption": round(float(np.clip(global_ais_disruption, 0, 1)), 6),
                "weather_stress": round(float(weather_stress), 6),
                "source_categories": source_categories,
                "n_sources": len(source_categories),
                "earliest_signal_utc": earliest,
                "detected_at_utc": latest,
            }
        )

    features = pd.DataFrame(rows)
    if not features.empty:
        features = features.sort_values("region_iso").reset_index(drop=True)
    return features
