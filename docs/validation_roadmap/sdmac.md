# Validation Roadmap — SD-MAC (Sector-Wide Deployable Modular Analytics Commons)

This page covers the SD-MAC rows of the platform's model-validation roadmap
(rows 7–10). See [`overview.md`](overview.md) for the full 10-row table and the
synthetic-data and placeholder notices, which apply here as well.

> **Synthetic data notice.** The SD-MAC fixtures, API, and notebooks in this
> repository use **synthetic illustrative data generated for demonstration. It
> is NOT real agency data and is NOT derived from any proprietary or employer
> source.** Reproducibility, conformance, and latency figures produced in the
> notebooks are illustrative methodology demonstrations on synthetic data. The
> targets below use the `<JING_WEN_TO_FILL>` placeholder convention; they are
> not invented here.

## SD-MAC validation activities

| # | Validation activity | Public dataset | Expected metric | Target threshold | Target date |
|---|---|---|---|---|---|
| 7 | SD-MAC module reproducibility check | Public ISO/RTO replication benchmark | Reproducibility (% of runs matching reference output within tolerance) | `<JING_WEN_TO_FILL: target threshold, e.g. ">= 99.0%">` | `<JING_WEN_TO_FILL: target date>` |
| 8 | SD-MAC schema-conformance check | Sample public-data records | Conformance rate (% records validating against registry) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 9 | End-to-end API performance | Synthetic public-data load test | p95 response latency (ms) | `<JING_WEN_TO_FILL: target threshold>` | `<JING_WEN_TO_FILL: target date>` |
| 10 | Public-benchmark comparison memo | All of the above | Memo published with reproducible notebooks | `<JING_WEN_TO_FILL: target threshold, e.g. "memo + companion notebooks released">` | `<JING_WEN_TO_FILL: target date>` |

## Methodology notes

### Row 7 — Module reproducibility check

Reproducibility validation re-runs each registered module against a public
ISO/RTO replication benchmark and measures the fraction of runs whose output
matches a reference within tolerance. Determinism is a precondition: all platform
randomness is seeded (`seed=42`).

- **Demonstration notebook:** `sdmac/notebooks/sdmac_api_demo.ipynb` exercises the
  modules end-to-end through the API and shows reproducible outputs across runs.
- **Component code exercised:** the module manifests in `sdmac/manifests/*.yaml`
  (each conforms to `module_manifest`, `validation_status: draft`) and the
  underlying GEA/CRICAT module code they describe.

### Row 8 — Schema-conformance check

Conformance validation measures the percentage of sample public-data records that
validate against the draft schema registry.

- **Demonstration notebook:**
  `sdmac/notebooks/sdmac_schema_validation_demo.ipynb` validates synthetic sample
  records against each registry schema and reports the conformance rate.
- **Component code exercised:** `shared.utilities.schema_loader` (loads the
  registry YAML into JSON Schema and validates records via `jsonschema`) over the
  four schemas in `sdmac/schema_registry/` (`supply_disruption_event`,
  `load_forecast_record`, `capacity_allocation_scenario`, `module_manifest`).

### Row 9 — End-to-end API performance (p95 latency)

Performance validation measures p95 response latency for the API under a
synthetic public-data load test.

- **Demonstration notebook:** `sdmac/notebooks/sdmac_api_demo.ipynb` calls the
  FastAPI app via `TestClient` (no live server required) and times responses.
- **Component code exercised:** the FastAPI app `sdmac.api.main:app` (the seven
  REST endpoints, served from bundled synthetic fixtures and the schema
  registry); the in-memory `sdmac.api.store.RecordStore`.

### Row 10 — Public-benchmark comparison memo

The capstone activity publishes a comparison memo against the public benchmarks,
accompanied by reproducible notebooks.

- **Demonstration notebook:**
  `sdmac/notebooks/oefaf_governance_pipeline.ipynb` walks the OEFAF governance and
  contribution-review process (governance documents only) by which the comparison
  memo and its companion notebooks would be reviewed and published under the
  planned nonprofit governance.
- **Inputs:** results from all of the above rows (GEA backtest and latency; CRICAT
  PJM/ERCOT/MISO MAPE and scenario calibration; SD-MAC reproducibility,
  conformance, and latency).

## Schemas and provenance

SD-MAC records conform to `module_manifest`. The SD-MAC test suite
(`sdmac/tests/test_api.py`) hits all seven endpoints, checks 200 responses and
response-schema conformance, and verifies the `POST /v1/scenarios` →
`GET /v1/scenarios/{id}` round-trip.
