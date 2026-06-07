# SD-MAC Public Analytics API

> **Synthetic illustrative data generated for demonstration. NOT real agency
> data and NOT derived from any proprietary or employer source.**

This page documents the SD-MAC (Sector-Wide Deployable Modular Analytics
Commons) public analytics API for the Integrated Commodity Risk Analytics
Platform — GEA (Geopolitical-Event Analytics), CRICAT (Climate-Risk Integrated
Capacity-Allocation Toolkit), and SD-MAC. The platform is intended for public
release under the planned governance of the Open Energy Finance Analytics
Foundation (OEFAF, in formation as a Section 501(c)(3) public charity).

The API is a draft (`version 0.1.0`). It serves entirely from bundled synthetic
fixtures and the schema-registry module manifests; it performs **no network
access** and reads **no proprietary or employer-internal data**. Every record it
returns is synthetic illustrative data for demonstration only.

The machine-readable OpenAPI specification is committed at
[`sdmac/api/openapi.yaml`](../../sdmac/api/openapi.yaml). It is generated from
the FastAPI application with:

```bash
python sdmac/api/export_openapi.py
```

## Running the API

The application object is `sdmac.api.main:app`. For local exploration:

```bash
# from the repository root, with the project virtualenv active
uvicorn sdmac.api.main:app --reload
```

Interactive docs are then available at `http://127.0.0.1:8000/docs` (Swagger UI)
and `http://127.0.0.1:8000/redoc`.

The examples below show `curl` against a locally running server and the
equivalent in-process `httpx` calls (no live server required) via FastAPI's
`TestClient`. The `httpx`-style client is exactly what the notebooks and tests
use.

```python
from fastapi.testclient import TestClient   # thin wrapper over httpx
from sdmac.api.main import app

client = TestClient(app)
resp = client.get("/v1/events")
print(resp.status_code, resp.json())
```

## Endpoints

Seven versioned record endpoints plus one operational endpoint.

| Endpoint | Method | Component | Purpose |
|---|---|---|---|
| `/v1/events` | GET | GEA | List supply-disruption event summaries (filterable) |
| `/v1/events/{event_id}` | GET | GEA | Full `supply_disruption_event` record |
| `/v1/forecasts/{iso_region}` | GET | CRICAT | Array of `load_forecast_record` for a region |
| `/v1/scenarios` | POST | CRICAT | Create a `capacity_allocation_scenario` |
| `/v1/scenarios/{scenario_id}` | GET | CRICAT | Full `capacity_allocation_scenario` record |
| `/v1/modules` | GET | SD-MAC | List `module_manifest` records (filterable) |
| `/v1/modules/{module_id}` | GET | SD-MAC | Full `module_manifest` record |
| `/healthz` | GET | ops | **Operational liveness probe** (not a versioned record endpoint) |

---

### `GET /v1/events` (GEA)

List supply-disruption event **summaries**. Query parameters (all optional,
conjunctive): `commodity`, `region`, `since` (ISO-8601 UTC; returns events with
`detected_at_utc >= since`), `min_severity` (returns events with
`severity_score >= min_severity`).

Each item is the compact projection: `event_id`, `detected_at_utc`,
`severity_score`, `public_evidence_refs[]`.

```bash
curl "http://127.0.0.1:8000/v1/events?commodity=crude_oil&min_severity=0.8"
```

```python
client.get("/v1/events", params={"commodity": "crude_oil", "min_severity": 0.8})
```

Example response:

```json
[
  {
    "event_id": "GEA-EVT-0000",
    "detected_at_utc": "2026-01-05T23:00:00Z",
    "severity_score": 0.828,
    "public_evidence_refs": [
      "https://example.org/public-evidence/crude_oil/0000/0",
      "https://example.org/public-evidence/crude_oil/0000/1",
      "https://example.org/public-evidence/crude_oil/0000/2"
    ]
  }
]
```

### `GET /v1/events/{event_id}` (GEA)

Return the full `supply_disruption_event` record. Returns `404` if unknown.

```bash
curl "http://127.0.0.1:8000/v1/events/GEA-EVT-0000"
```

```python
client.get("/v1/events/GEA-EVT-0000")
```

Example response:

```json
{
  "event_id": "GEA-EVT-0000",
  "detected_at_utc": "2026-01-05T23:00:00Z",
  "commodity": "crude_oil",
  "region_iso": "SAU",
  "source_categories": ["weather"],
  "severity_score": 0.828,
  "confidence": 0.984,
  "public_evidence_refs": [
    "https://example.org/public-evidence/crude_oil/0000/0",
    "https://example.org/public-evidence/crude_oil/0000/1",
    "https://example.org/public-evidence/crude_oil/0000/2"
  ]
}
```

### `GET /v1/forecasts/{iso_region}` (CRICAT)

Return an array of `load_forecast_record` for an ISO/RTO region. `iso_region`
must be one of `PJM, ERCOT, MISO, NYISO, ISO_NE, CAISO, SPP` (an invalid value
returns `422`). Optional query bounds: `target_window_start` (returns records
with `target_window_start_utc >= ...`) and `target_window_end` (returns records
with `target_window_end_utc <= ...`).

```bash
curl "http://127.0.0.1:8000/v1/forecasts/PJM?target_window_start=2026-01-01T00:00:00Z"
```

```python
client.get("/v1/forecasts/PJM", params={"target_window_start": "2026-01-01T00:00:00Z"})
```

Example response:

```json
[
  {
    "forecast_id": "CRICAT-FC-0000",
    "iso_region": "PJM",
    "forecast_issued_at_utc": "2026-03-12T00:00:00Z",
    "target_window_start_utc": "2026-03-13T00:00:00Z",
    "target_window_end_utc": "2026-03-14T00:00:00Z",
    "predicted_load_mw": 71290.1,
    "prediction_interval_low_mw": 68438.5,
    "prediction_interval_high_mw": 74141.7,
    "model_id": "cricat-ridge-dayahead-v0.1",
    "input_data_sources": ["synthetic_load_history", "synthetic_weather", "calendar_features"]
  }
]
```

### `POST /v1/scenarios` (CRICAT)

Create a `capacity_allocation_scenario`. The request body carries only
`scenario_label`, `stress_drivers[]`, `regions[]`, and `time_horizon_hours`. The
server derives the demand/capacity assumptions, reserve margin, and probability
of stress deterministically (seeded; identical requests yield identical derived
values) and assigns a `scenario_id`. Returns `201` with the created record,
which then persists for `GET /v1/scenarios/{scenario_id}` (in-memory store for
the lifetime of the process).

```bash
curl -X POST "http://127.0.0.1:8000/v1/scenarios" \
  -H "Content-Type: application/json" \
  -d '{
        "scenario_label": "summer_2027_extreme_heat_pjm",
        "stress_drivers": ["heatwave", "outage"],
        "regions": ["PJM"],
        "time_horizon_hours": 24
      }'
```

```python
created = client.post("/v1/scenarios", json={
    "scenario_label": "summer_2027_extreme_heat_pjm",
    "stress_drivers": ["heatwave", "outage"],
    "regions": ["PJM"],
    "time_horizon_hours": 24,
}).json()
client.get(f"/v1/scenarios/{created['scenario_id']}")   # round-trip
```

Example response (`201 Created`):

```json
{
  "scenario_id": "CRICAT-SCN-0003",
  "scenario_label": "summer_2027_extreme_heat_pjm",
  "stress_drivers": ["heatwave", "outage"],
  "time_horizon_hours": 24,
  "regions": ["PJM"],
  "assumed_demand_mw": 92841.3,
  "assumed_available_capacity_mw": 80123.7,
  "reserve_margin_pct": -13.7,
  "probability_of_stress": 0.957,
  "data_provenance": [
    "https://example.org/public-provenance/summer_2027_extreme_heat_pjm/0",
    "https://example.org/public-provenance/summer_2027_extreme_heat_pjm/1"
  ]
}
```

> The numeric values above are illustrative; the exact derived magnitudes are
> computed by the seeded synthetic grid-modeling logic in `sdmac/api/store.py`.

### `GET /v1/scenarios/{scenario_id}` (CRICAT)

Return the full `capacity_allocation_scenario` record, including any scenario
created via `POST /v1/scenarios` during the current process lifetime. Returns
`404` if unknown.

```bash
curl "http://127.0.0.1:8000/v1/scenarios/CRICAT-SCN-0000"
```

```python
client.get("/v1/scenarios/CRICAT-SCN-0000")
```

### `GET /v1/modules` (SD-MAC)

List `module_manifest` records, seeded from `sdmac/manifests/*.yaml`. Optional
conjunctive filters: `platform_component` (`gea, cricat, sdmac, shared`) and
`validation_status` (`draft, internal_validated, public_validated`).

```bash
curl "http://127.0.0.1:8000/v1/modules?platform_component=cricat&validation_status=draft"
```

```python
client.get("/v1/modules", params={"platform_component": "cricat", "validation_status": "draft"})
```

Example response:

```json
[
  {
    "module_id": "cricat-load-forecasting",
    "module_name": "CRICAT Load Forecasting",
    "platform_component": "cricat",
    "license": "MIT",
    "maintainers": ["<JING_WEN_TO_FILL: maintainer handle or institutional affiliation>"],
    "public_dependencies": ["scikit-learn==1.5.1", "numpy==1.26.4", "pandas==2.2.2"],
    "data_inputs": ["synthetic_iso_load_history", "synthetic_weather_features", "calendar_features"],
    "outputs": ["load_forecast_record"],
    "validation_status": "draft",
    "documentation_url": "<JING_WEN_TO_FILL: documentation URL>"
  }
]
```

### `GET /v1/modules/{module_id}` (SD-MAC)

Return the full `module_manifest` record. Returns `404` if unknown.

```bash
curl "http://127.0.0.1:8000/v1/modules/sdmac-api"
```

```python
client.get("/v1/modules/sdmac-api")
```

### `GET /healthz` (operational)

**Operational liveness probe.** This endpoint is intentionally outside the
versioned `/v1` record API surface and is not one of the versioned record
endpoints. It reports liveness plus the count of records seeded into the
in-memory store.

```bash
curl "http://127.0.0.1:8000/healthz"
```

```python
client.get("/healthz")
```

Example response:

```json
{
  "status": "ok",
  "events_loaded": 12,
  "forecasts_loaded": 4,
  "scenarios_loaded": 3,
  "modules_loaded": 5
}
```

## Schema conformance

Every record payload returned by the API validates against the matching
schema-registry schema (`sdmac/schema_registry/*.yaml`) via
`shared.utilities.schema_loader.validate_record`. The SD-MAC test suite
(`sdmac/tests/test_api.py`) asserts this for `supply_disruption_event`,
`load_forecast_record`, `capacity_allocation_scenario`, and `module_manifest`,
and checks the `POST /v1/scenarios` → `GET /v1/scenarios/{id}` round-trip and the
event/module filters.

Run the tests and regenerate the spec:

```bash
python -m pytest sdmac/tests -q
python sdmac/api/export_openapi.py
```
