"""GEA ingestion subpackage.

Loaders for the synthetic public-category GEA fixtures (sanctions, AIS, and
weather) and a feature-assembly step that joins them into a per-candidate-event
feature frame for scoring. All inputs are synthetic illustrative data generated
for demonstration; no real agency data and no proprietary or employer source.
"""

from __future__ import annotations

from gea.ingestion.loaders import (
    assemble_event_features,
    load_ais_positions,
    load_sanctions_events,
    load_weather_observations,
)

__all__ = [
    "assemble_event_features",
    "load_ais_positions",
    "load_sanctions_events",
    "load_weather_observations",
]
