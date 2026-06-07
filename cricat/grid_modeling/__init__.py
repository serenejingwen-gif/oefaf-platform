"""CRICAT grid-modeling subpackage.

Exposes transparent reserve-margin and probability-of-stress math used by the
capacity-allocation scenario analysis.
"""

from __future__ import annotations

from cricat.grid_modeling.reserve import probability_of_stress, reserve_margin_pct

__all__ = ["reserve_margin_pct", "probability_of_stress"]
