"""GEA scoring subpackage.

Transparent, deterministic scoring of candidate supply-disruption events:
a weighted aggregation of normalized features yields a ``severity_score`` in
[0, 1], and a logistic squashing of an evidence/agreement signal yields a
``confidence`` in [0, 1]. ``build_events`` runs ingestion -> scoring and emits
``supply_disruption_event`` records conforming to the SD-MAC schema registry.

All inputs are synthetic illustrative data generated for demonstration; no real
agency data and no proprietary or employer source.
"""

from __future__ import annotations

from gea.scoring.scorer import (
    FEATURE_WEIGHTS,
    build_events,
    score_event,
)

__all__ = ["FEATURE_WEIGHTS", "build_events", "score_event"]
