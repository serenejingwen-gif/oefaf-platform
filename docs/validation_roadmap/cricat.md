# Validation Roadmap — CRICAT (Climate-Risk Integrated Capacity-Allocation Toolkit)

This page covers the CRICAT rows of the platform's model-validation roadmap
(rows 3–6). See [`overview.md`](overview.md) for the full 10-row table and the
synthetic-data and placeholder notices, which apply here as well.

> **Synthetic data notice.** The CRICAT fixtures and notebooks in this
> repository use **synthetic illustrative data generated for demonstration. It
> is NOT real agency data and is NOT derived from any proprietary or employer
> source.** Any MAPE, Brier score, or other metric computed in the notebooks is
> an illustrative methodology demonstration on synthetic data — not a validated
> result against real public benchmarks. The targets below use the
> `<JING_WEN_TO_FILL>` placeholder convention; they are not invented here.

## CRICAT validation activities

| # | Validation activity | Public dataset | Expected metric | Target threshold | Target date |
|---|---|---|---|---|---|
| 3 | CRICAT day-ahead PJM load forecast | PJM Data Miner 2 historical load | Mean absolute percentage error (MAPE) | `<JING_WEN_TO_FILL: target threshold, e.g. "<= 3.0% MAPE">` | `<JING_WEN_TO_FILL: target date>` |
| 4 | CRICAT day-ahead ERCOT load forecast | ERCOT public reports | MAPE | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 5 | CRICAT day-ahead MISO load forecast | MISO Market Reports | MAPE | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 6 | CRICAT capacity-stress scenario calibration | NERC reliability assessments | Calibration error (Brier score) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |

## Methodology notes

### Rows 3–5 — Day-ahead load forecasting (MAPE: PJM, ERCOT, MISO)

The intended validation trains the CRICAT load forecaster on real public ISO/RTO
load histories (PJM Data Miner 2, ERCOT public reports, MISO Market Reports)
with calendar and weather features, using a chronological train/test split so
the reported **MAPE** reflects genuine out-of-sample performance. The same
forecasting methodology applies to all three regions; only the public dataset
changes per row.

- **Demonstration notebook:**
  `cricat/notebooks/cricat_pjm_load_forecast_replication.ipynb` replicates the
  day-ahead forecast methodology on the synthetic PJM fixture
  (`shared/data_sources/fixtures/cricat/pjm_load_weather_hourly.csv`) and reports
  a held-out MAPE on that synthetic data. The ERCOT analogue uses
  `ercot_load_weather_hourly.csv`.
- **Component code exercised:** `cricat.load_forecasting.forecaster` —
  `train(region, ...)` (chronological split + scikit-learn model fit),
  `predict_day_ahead(...)` (produces `load_forecast_record` with residual-based
  prediction intervals), and `report_mape(region, ...)` (returns the held-out
  MAPE in percent).
- **What the notebook shows vs. what rows 3–5 validate:** the notebook computes a
  MAPE on labeled synthetic data to demonstrate the methodology; the roadmap rows
  apply the identical methodology to real public load histories to produce the
  validated per-region MAPE.

### Row 6 — Capacity-stress scenario calibration (Brier score)

Scenario calibration validation compares CRICAT's `probability_of_stress` for
capacity-allocation scenarios against realized stress outcomes published in NERC
reliability assessments, scored by **Brier score** (calibration error).

- **Demonstration notebook:**
  `cricat/notebooks/cricat_ercot_capacity_scenario.ipynb` builds an ERCOT
  capacity-stress scenario from synthetic public reports and weather inputs and
  shows the reserve-margin-to-stress-probability mapping.
- **Component code exercised:** `cricat.grid_modeling.reserve.reserve_margin_pct`
  (reserve margin = (capacity − demand) / demand) and
  `cricat.grid_modeling.reserve.probability_of_stress` (monotone, clipped-to-[0,1]
  function of reserve margin); `cricat.scenarios.builder` (emits
  `capacity_allocation_scenario` records; example scenarios in
  `cricat/scenarios/fixtures/`).

## Schemas and provenance

Forecast records conform to `load_forecast_record` and scenarios conform to
`capacity_allocation_scenario` (both in `sdmac/schema_registry/`). The CRICAT
test suite (`cricat/tests/`) checks that the synthetic MAPE is finite and
reasonable, the reserve-margin math, and record schema conformance.
