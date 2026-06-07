# Validation Roadmap — Overview

This page presents the platform's model-validation roadmap. It enumerates the
validation activities to be performed against **public benchmarks**, the public
dataset each activity uses, the expected metric, the target threshold, and the
target date.

> **Synthetic data notice.** The bundled fixtures and notebooks in this
> repository use **synthetic illustrative data generated for demonstration. It
> is NOT real agency data and is NOT derived from any proprietary or employer
> source.** The roadmap below describes validation against *real public
> benchmarks*; the notebooks demonstrate the *methodology* of each activity on
> clearly labeled synthetic data. Computed metrics in the notebooks (for
> example, a MAPE) are illustrative methodology demonstrations, not validated
> results against real public data.

> **Targets are placeholders.** The target thresholds and target dates below
> use the `<JING_WEN_TO_FILL: ...>` placeholder convention. They are **not**
> invented here. Jing Wen will confirm or revise each target and date before the
> roadmap is finalized.

## Validation activities (all 10 rows)

| # | Validation activity | Public dataset | Expected metric | Target threshold | Target date |
|---|---|---|---|---|---|
| 1 | GEA supply-disruption event detection — backtest | EIA + public AIS + OFAC public archives | Precision at top-decile severity | `<JING_WEN_TO_FILL: target threshold, e.g. ">= 0.70 precision">` | `<JING_WEN_TO_FILL: target date>` |
| 2 | GEA event-detection latency | Synthetic public-event timeline | Median detection lag (minutes) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 3 | CRICAT day-ahead PJM load forecast | PJM Data Miner 2 historical load | Mean absolute percentage error (MAPE) | `<JING_WEN_TO_FILL: target threshold, e.g. "<= 3.0% MAPE">` | `<JING_WEN_TO_FILL: target date>` |
| 4 | CRICAT day-ahead ERCOT load forecast | ERCOT public reports | MAPE | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 5 | CRICAT day-ahead MISO load forecast | MISO Market Reports | MAPE | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 6 | CRICAT capacity-stress scenario calibration | NERC reliability assessments | Calibration error (Brier score) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 7 | SD-MAC module reproducibility check | Public ISO/RTO replication benchmark | Reproducibility (% of runs matching reference output within tolerance) | `<JING_WEN_TO_FILL: target threshold, e.g. ">= 99.0%">` | `<JING_WEN_TO_FILL: target date>` |
| 8 | SD-MAC schema-conformance check | Sample public-data records | Conformance rate (% records validating against registry) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 9 | End-to-end API performance | Synthetic public-data load test | p95 response latency (ms) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 10 | Public-benchmark comparison memo | All of the above | Memo published with reproducible notebooks | `<JING_WEN_TO_FILL: target threshold, e.g. "memo + companion notebooks released">` | `<JING_WEN_TO_FILL: target date>` |

## Per-component pages

The activities are split by platform component, with methodology notes pointing
to the corresponding demonstration notebook(s):

- **GEA** — rows 1–2. See [`gea.md`](gea.md).
- **CRICAT** — rows 3–6. See [`cricat.md`](cricat.md).
- **SD-MAC** — rows 7–10. See [`sdmac.md`](sdmac.md).

## How the notebooks relate to the roadmap

Each demonstration notebook exercises the *methodology* of one or more roadmap
rows on synthetic illustrative data, so the approach is reproducible before
validation against real public benchmarks:

| Notebook | Demonstrates roadmap rows |
|---|---|
| `gea/notebooks/gea_event_scoring_walkthrough.ipynb` | 1 (and informs 2) |
| `cricat/notebooks/cricat_pjm_load_forecast_replication.ipynb` | 3 (methodology shared with 4, 5) |
| `cricat/notebooks/cricat_ercot_capacity_scenario.ipynb` | 6 (and the ERCOT side of 4) |
| `sdmac/notebooks/sdmac_schema_validation_demo.ipynb` | 8 |
| `sdmac/notebooks/sdmac_api_demo.ipynb` | 7, 9 |
| `sdmac/notebooks/oefaf_governance_pipeline.ipynb` | 10 (process for publishing the comparison memo) |
