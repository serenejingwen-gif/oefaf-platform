"""GEA — Geopolitical-Event Analytics.

GEA is the supply-disruption detection and scoring component of the
oefaf-platform reference codebase. It ingests public-category data feeds
(sanctions-style listings, AIS vessel positions, and weather observations),
assembles per-candidate-event features, and produces ``supply_disruption_event``
records conforming to the SD-MAC schema registry.

All bundled data used by this component is synthetic illustrative data
generated for demonstration. It is NOT real agency data and is NOT derived
from any proprietary or employer source. Source-category labels (``ais``,
``satellite``, ``sanctions``, ``weather``, ``regulatory``) are public category
names only; any URLs are illustrative ``example.org`` placeholders.

This component runs fully offline; it performs no network access.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
