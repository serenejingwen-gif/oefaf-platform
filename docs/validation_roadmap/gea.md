# Validation Roadmap — GEA (Geopolitical-Event Analytics)

This page covers the GEA rows of the platform's model-validation roadmap
(rows 1–2). See [`overview.md`](overview.md) for the full 10-row table and the
synthetic-data and placeholder notices, which apply here as well.

> **Synthetic data notice.** The GEA fixtures and notebook in this repository
> use **synthetic illustrative data generated for demonstration. It is NOT real
> agency data and is NOT derived from any proprietary or employer source.** The
> targets below use the `<JING_WEN_TO_FILL>` placeholder convention; they are
> not invented here.

## GEA validation activities

| # | Validation activity | Public dataset | Expected metric | Target threshold | Target date |
|---|---|---|---|---|---|
| 1 | GEA supply-disruption event detection — backtest | EIA + public AIS + OFAC public archives | Precision at top-decile severity | `<JING_WEN_TO_FILL: target threshold, e.g. ">= 0.70 precision">` | `<JING_WEN_TO_FILL: target date>` |
| 2 | GEA event-detection latency | Synthetic public-event timeline | Median detection lag (minutes) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |

## Methodology notes

### Row 1 — Event-detection backtest (precision at top-decile severity)

The intended validation backtests GEA's event scoring against archived public
events drawn from EIA supply data, public AIS vessel-position aggregators, and
the OFAC public sanctions archives. Detected events are ranked by
`severity_score`; precision is measured within the top decile of severity
against known public disruption events.

- **Demonstration notebook:** `gea/notebooks/gea_event_scoring_walkthrough.ipynb`
  walks the full scoring pipeline on synthetic public-source fixtures
  (synthetic sanctions, AIS, and weather observations under
  `shared/data_sources/fixtures/gea/`).
- **Component code exercised:** `gea.scoring.scorer.score_event` (the
  transparent, deterministic weighted feature aggregation that produces
  `severity_score` and `confidence`) and `gea.scoring.scorer.build_events`
  (emits `supply_disruption_event` records); ingestion loaders in
  `gea/ingestion/loaders.py`.
- **What the notebook shows vs. what row 1 validates:** the notebook demonstrates
  the ranking-and-precision *methodology* on labeled synthetic data; the roadmap
  row applies that same methodology to real public archives to produce the
  reported precision-at-top-decile metric.

### Row 2 — Event-detection latency (median detection lag)

Latency validation measures the median lag between a public event becoming
observable in the source feeds and GEA emitting the corresponding
`supply_disruption_event`. The roadmap specifies a synthetic public-event
timeline as the dataset for this activity.

- **Demonstration notebook:** the timing instrumentation around the same
  `gea/notebooks/gea_event_scoring_walkthrough.ipynb` scoring pipeline; the
  `detected_at_utc` field on emitted records is the basis for the lag
  computation.
- **Component code exercised:** `gea.scoring.scorer.build_events` (stamps
  `detected_at_utc`) over the synthetic event timeline.

## Schema and provenance

GEA validation records conform to the `supply_disruption_event` schema in
`sdmac/schema_registry/supply_disruption_event.yaml`. Schema conformance of
emitted records is itself checked under the SD-MAC roadmap (row 8) and in the
GEA test suite (`gea/tests/test_schema_conformance.py`).
