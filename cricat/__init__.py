"""CRICAT — Climate-Risk Integrated Capacity-Allocation Toolkit.

CRICAT is the grid-reliability component of the Open Energy Finance Analytics
Foundation (OEFAF) reference platform. It provides:

- ``cricat.load_forecasting`` — a deterministic, open-source day-ahead power-load
  forecaster (scikit-learn) producing ``load_forecast_record`` documents with
  prediction intervals, trained on bundled synthetic load+weather fixtures.
- ``cricat.grid_modeling`` — transparent reserve-margin and probability-of-stress
  math used by the capacity-allocation analysis.
- ``cricat.scenarios`` — a builder that emits ``capacity_allocation_scenario``
  documents from a small set of analyst-supplied assumptions.

All inputs bundled with this package are synthetic illustrative data generated
for demonstration. They are NOT real agency data and are NOT derived from any
proprietary or employer source. All logic is fully offline and deterministic
(``random_state=42``); no network access is performed.
"""

from __future__ import annotations

__all__ = ["load_forecasting", "grid_modeling", "scenarios"]
