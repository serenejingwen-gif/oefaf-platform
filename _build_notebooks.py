"""Assemble the six demonstration notebooks as .ipynb files.

This is a build-time helper (not part of the shipped platform package). It uses
``nbformat`` to write each notebook's cells to disk; the notebooks are then
executed in place via ``jupyter nbconvert --execute`` so the committed .ipynb
files carry real, reproduced outputs.

Every notebook opens with a markdown cell stating it uses ONLY synthetic /
illustrative public-style data and contains no proprietary content, and a code
"bootstrap" cell that puts the repo root on ``sys.path`` so component imports
resolve regardless of the working directory nbconvert runs from.

This helper reads no network and writes only inside the oefaf-platform tree.
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO = Path(__file__).resolve().parent

# A repo-root sys.path bootstrap dropped at the top of every notebook so that
# `import gea...`, `import cricat...`, `import sdmac...`, `import shared...` all
# resolve when nbconvert executes the notebook from any working directory.
BOOTSTRAP = (
    "import sys\n"
    "from pathlib import Path\n"
    "\n"
    "# Put the oefaf-platform repository root on sys.path so the platform\n"
    "# component packages (gea, cricat, sdmac, shared) import cleanly no matter\n"
    "# what working directory this notebook is executed from.\n"
    "_REPO_ROOT = Path.cwd()\n"
    "while not (_REPO_ROOT / 'sdmac' / 'schema_registry').is_dir():\n"
    "    if _REPO_ROOT == _REPO_ROOT.parent:\n"
    "        raise RuntimeError('Could not locate the oefaf-platform repo root.')\n"
    "    _REPO_ROOT = _REPO_ROOT.parent\n"
    "if str(_REPO_ROOT) not in sys.path:\n"
    "    sys.path.insert(0, str(_REPO_ROOT))\n"
    "print('repo root located:', _REPO_ROOT.name)"
)

SYNTHETIC_BANNER = (
    "> **Synthetic data only.** Every dataset used in this notebook is "
    "*synthetic illustrative data generated for demonstration*. It is **NOT** "
    "real agency data and is **NOT** derived from any proprietary or employer "
    "source. The notebook performs no network access and uses only public-style, "
    "open-source components."
)


def _write_and_register(name: str, path: Path, cells: list) -> Path:
    """Build a notebook from ``cells`` and write it to ``path``."""
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python"}
    path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, path)
    return path


# --------------------------------------------------------------------------- #
# Notebook 1 — GEA event-scoring walkthrough
# --------------------------------------------------------------------------- #
def build_gea_event_scoring() -> Path:
    cells = [
        new_markdown_cell(
            "# GEA — Event-Scoring Walkthrough\n\n"
            "**Component:** GEA (Geopolitical-Event Analytics)\n\n"
            "This notebook walks through the GEA event-scoring pipeline: it loads the "
            "bundled synthetic public-style feeds (sanctions-style listings, AIS "
            "vessel positions, weather observations), assembles per-candidate-event "
            "features, scores each candidate, and emits "
            "`supply_disruption_event` records conforming to the SD-MAC schema "
            "registry.\n\n"
            + SYNTHETIC_BANNER
        ),
        new_code_cell(BOOTSTRAP),
        new_markdown_cell(
            "## 1. Load synthetic feeds and assemble candidate-event features\n\n"
            "`gea.ingestion.loaders.assemble_event_features` reads the three bundled "
            "synthetic GEA fixtures and derives one transparent, normalized feature "
            "row per candidate region."
        ),
        new_code_cell(
            "import pandas as pd\n"
            "from gea.ingestion.loaders import (\n"
            "    assemble_event_features,\n"
            "    load_ais_positions,\n"
            "    load_sanctions_events,\n"
            "    load_weather_observations,\n"
            ")\n"
            "\n"
            "sanctions = load_sanctions_events()\n"
            "ais = load_ais_positions()\n"
            "weather = load_weather_observations()\n"
            "print('synthetic sanctions rows:', len(sanctions))\n"
            "print('synthetic AIS rows:      ', len(ais))\n"
            "print('synthetic weather rows:  ', len(weather))\n"
            "\n"
            "features = assemble_event_features(sanctions, ais, weather)\n"
            "print('\\ncandidate events:', len(features))\n"
            "features[[\n"
            "    'region_iso', 'commodity', 'sanctions_intensity',\n"
            "    'ais_disruption', 'weather_stress', 'n_sources',\n"
            "]]"
        ),
        new_markdown_cell(
            "## 2. Run the transparent scorer and emit schema records\n\n"
            "`gea.scoring.scorer.build_events` scores each candidate with a "
            "fixed-weight, fully inspectable aggregation (severity) and a logistic "
            "evidence-agreement signal (confidence), then emits complete "
            "`supply_disruption_event` records."
        ),
        new_code_cell(
            "from gea.scoring.scorer import FEATURE_WEIGHTS, build_events\n"
            "\n"
            "print('severity feature weights (sum = 1.0):', FEATURE_WEIGHTS)\n"
            "\n"
            "events = build_events(features)\n"
            "print('emitted supply_disruption_event records:', len(events))\n"
            "\n"
            "events_df = pd.DataFrame(events)\n"
            "events_df[[\n"
            "    'event_id', 'region_iso', 'commodity',\n"
            "    'severity_score', 'confidence', 'source_categories',\n"
            "]]"
        ),
        new_markdown_cell(
            "### Inspect one full emitted record\n\n"
            "Each record carries every `supply_disruption_event` field. The "
            "`public_evidence_refs` are clearly illustrative `example.org` "
            "placeholders — not real agency URLs presented as real."
        ),
        new_code_cell(
            "import json\n"
            "\n"
            "print(json.dumps(events[0], indent=2))"
        ),
        new_markdown_cell(
            "## 3. Confirm every emitted record conforms to the registry schema\n\n"
            "`shared.utilities.schema_loader.validate_record` converts the registry "
            "YAML to JSON Schema and validates each record."
        ),
        new_code_cell(
            "from shared.utilities.schema_loader import validate_record\n"
            "\n"
            "all_ok = all(\n"
            "    validate_record(rec, 'supply_disruption_event') for rec in events\n"
            ")\n"
            "print('all', len(events), 'records valid against supply_disruption_event:', all_ok)"
        ),
        new_markdown_cell(
            "## 4. Severity bar chart\n\n"
            "A simple bar of severity per emitted event (synthetic data)."
        ),
        new_code_cell(
            "%matplotlib inline\n"
            "import matplotlib.pyplot as plt\n"
            "\n"
            "fig, ax = plt.subplots(figsize=(8, 4), dpi=150)\n"
            "ax.bar(events_df['event_id'], events_df['severity_score'], color='#33691e')\n"
            "ax.set_ylim(0, 1)\n"
            "ax.set_ylabel('severity_score (0–1)')\n"
            "ax.set_xlabel('event_id')\n"
            "ax.set_title('GEA emitted event severity (synthetic illustrative data)')\n"
            "plt.xticks(rotation=45, ha='right')\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "print('chart rendered for', len(events_df), 'synthetic events')"
        ),
        new_markdown_cell(
            "---\n\n"
            "**Recap.** The pipeline loaded synthetic public-style feeds, assembled "
            "candidate-event features, scored them with transparent logic, emitted "
            "schema-conformant `supply_disruption_event` records, and validated every "
            "record against the SD-MAC schema registry. All data shown is synthetic "
            "illustrative data; no proprietary or employer content is used."
        ),
    ]
    return _write_and_register(
        "gea_event_scoring_walkthrough",
        REPO / "gea" / "notebooks" / "gea_event_scoring_walkthrough.ipynb",
        cells,
    )


# --------------------------------------------------------------------------- #
# Notebook 2 — CRICAT PJM load-forecast replication
# --------------------------------------------------------------------------- #
def build_cricat_pjm_forecast() -> Path:
    cells = [
        new_markdown_cell(
            "# CRICAT — PJM Day-Ahead Load-Forecast Replication\n\n"
            "**Component:** CRICAT (Climate-Risk Integrated Capacity-Allocation "
            "Toolkit)\n\n"
            "This notebook trains the CRICAT day-ahead load forecaster on the bundled "
            "**synthetic** PJM load+weather series, evaluates it on a chronological "
            "hold-out (no look-ahead leakage), reports MAPE, and plots actual vs. "
            "predicted load. It demonstrates the *methodology* against synthetic "
            "data — it is **not** a benchmark claim on real PJM data.\n\n"
            + SYNTHETIC_BANNER
        ),
        new_code_cell(BOOTSTRAP),
        new_markdown_cell(
            "## 1. Train the forecaster on the synthetic PJM series\n\n"
            "`cricat.load_forecasting.forecaster.train` fits a deterministic "
            "`GradientBoostingRegressor` (`random_state=42`) on calendar + synthetic "
            "weather features, with a chronological train/test split."
        ),
        new_code_cell(
            "from cricat.load_forecasting.forecaster import (\n"
            "    MODEL_ID,\n"
            "    _build_features,\n"
            "    _fixture_path,\n"
            "    train,\n"
            ")\n"
            "from shared.utilities.io import read_csv\n"
            "\n"
            "fc = train('PJM', test_fraction=0.2, interval_level=0.80)\n"
            "print('model_id:      ', MODEL_ID)\n"
            "print('train rows:    ', fc.n_train)\n"
            "print('held-out rows: ', fc.n_test)\n"
            "print(f'hold-out MAPE: {fc.test_mape:.3f}%  (synthetic data)')"
        ),
        new_markdown_cell(
            "## 2. Reconstruct the hold-out split and compute actual vs. predicted\n\n"
            "We reload the same synthetic fixture, rebuild the features the model was "
            "trained on, and predict on the identical chronological hold-out tail so "
            "the actual-vs-predicted comparison matches the reported MAPE."
        ),
        new_code_cell(
            "df = read_csv(_fixture_path('PJM')).sort_values('timestamp_utc').reset_index(drop=True)\n"
            "feat = _build_features(df)\n"
            "y = df['load_mw'].astype(float).to_numpy()\n"
            "\n"
            "n = len(df)\n"
            "n_test = fc.n_test\n"
            "n_train = n - n_test\n"
            "\n"
            "x_test = feat.iloc[n_train:]\n"
            "y_test = y[n_train:]\n"
            "y_hat = fc.model.predict(x_test.to_numpy())\n"
            "\n"
            "ts_test = df['timestamp_utc'].iloc[n_train:].reset_index(drop=True)\n"
            "print('hold-out window:', ts_test.iloc[0], '->', ts_test.iloc[-1])\n"
            "print('hold-out points:', len(y_test))"
        ),
        new_markdown_cell(
            "## 3. MAPE (recomputed) and a metric sanity check\n\n"
            "The recomputed MAPE matches the value the trainer recorded."
        ),
        new_code_cell(
            "from cricat.load_forecasting.forecaster import _mape\n"
            "\n"
            "mape_recomputed = _mape(y_test, y_hat)\n"
            "print(f'recomputed hold-out MAPE: {mape_recomputed:.3f}%')\n"
            "print(f'trainer-reported  MAPE:   {fc.test_mape:.3f}%')\n"
            "assert abs(mape_recomputed - fc.test_mape) < 1e-6, 'MAPE mismatch'\n"
            "print('MAPE values agree (synthetic data).')"
        ),
        new_markdown_cell(
            "## 4. Plot actual vs. predicted load (synthetic PJM hold-out)"
        ),
        new_code_cell(
            "%matplotlib inline\n"
            "import matplotlib.pyplot as plt\n"
            "\n"
            "fig, ax = plt.subplots(figsize=(11, 4.5), dpi=150)\n"
            "ax.plot(range(len(y_test)), y_test, label='actual (synthetic)', color='#1565c0', linewidth=1.4)\n"
            "ax.plot(range(len(y_hat)), y_hat, label='predicted', color='#ef6c00', linewidth=1.4, linestyle='--')\n"
            "ax.set_xlabel('hold-out hour index')\n"
            "ax.set_ylabel('load (MW)')\n"
            "ax.set_title(f'CRICAT PJM day-ahead load: actual vs. predicted '\n"
            "             f'(synthetic data, MAPE = {fc.test_mape:.2f}%)')\n"
            "ax.legend()\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "print('actual-vs-predicted chart rendered (synthetic PJM hold-out).')"
        ),
        new_markdown_cell(
            "## 5. Emit a day-ahead `load_forecast_record` and validate it\n\n"
            "`predict_day_ahead` produces schema-conformant records with prediction "
            "intervals derived from the held-out residual quantiles."
        ),
        new_code_cell(
            "import json\n"
            "\n"
            "from cricat.load_forecasting.forecaster import predict_day_ahead\n"
            "from shared.utilities.schema_loader import validate_record\n"
            "\n"
            "records = predict_day_ahead('PJM', forecaster=fc, horizon_hours=24)\n"
            "print('emitted load_forecast_record documents:', len(records))\n"
            "print(json.dumps(records[0], indent=2))\n"
            "\n"
            "all_ok = all(validate_record(r, 'load_forecast_record') for r in records)\n"
            "print('\\nall', len(records), 'records valid against load_forecast_record:', all_ok)"
        ),
        new_markdown_cell(
            "---\n\n"
            "**Recap.** The forecaster trained and evaluated on a chronological "
            "hold-out of the synthetic PJM series, the recomputed MAPE matched the "
            "trainer's report, actual-vs-predicted was plotted, and emitted "
            "`load_forecast_record` documents validated against the registry. "
            "All inputs and outputs are synthetic illustrative data; no proprietary "
            "or employer content is used."
        ),
    ]
    return _write_and_register(
        "cricat_pjm_load_forecast_replication",
        REPO / "cricat" / "notebooks" / "cricat_pjm_load_forecast_replication.ipynb",
        cells,
    )


# --------------------------------------------------------------------------- #
# Notebook 3 — CRICAT ERCOT capacity-stress scenario
# --------------------------------------------------------------------------- #
def build_cricat_ercot_scenario() -> Path:
    cells = [
        new_markdown_cell(
            "# CRICAT — ERCOT Capacity-Stress Scenario\n\n"
            "**Component:** CRICAT (Climate-Risk Integrated Capacity-Allocation "
            "Toolkit)\n\n"
            "This notebook builds an ERCOT capacity-stress `capacity_allocation_"
            "scenario` from a small set of analyst assumptions, using the transparent "
            "CRICAT grid-modeling math: a standard reserve-margin definition and a "
            "monotone-decreasing probability-of-stress curve. It then sweeps the "
            "assumed capacity to show how reserve margin and stress probability move "
            "together.\n\n"
            + SYNTHETIC_BANNER
        ),
        new_code_cell(BOOTSTRAP),
        new_markdown_cell(
            "## 1. Build an ERCOT extreme-heat capacity-stress scenario\n\n"
            "`cricat.scenarios.builder.build_scenario` computes the reserve margin and "
            "probability of stress and returns a `capacity_allocation_scenario` "
            "document. The demand/capacity magnitudes here are synthetic illustrative "
            "assumptions only."
        ),
        new_code_cell(
            "import json\n"
            "\n"
            "from cricat.scenarios.builder import build_scenario\n"
            "\n"
            "scenario = build_scenario(\n"
            "    scenario_label='summer_2027_extreme_heat_ercot',\n"
            "    stress_drivers=['heatwave', 'forced_outage'],\n"
            "    regions=['ERCOT'],\n"
            "    time_horizon_hours=24,\n"
            "    assumed_demand_mw=82_000.0,        # synthetic illustrative peak demand\n"
            "    assumed_available_capacity_mw=80_500.0,  # synthetic illustrative capacity\n"
            ")\n"
            "print(json.dumps(scenario, indent=2))"
        ),
        new_markdown_cell(
            "## 2. Read out reserve margin and probability of stress\n\n"
            "A negative reserve margin (demand exceeds capacity) drives the stress "
            "probability above 0.5."
        ),
        new_code_cell(
            "print(f\"scenario_id:            {scenario['scenario_id']}\")\n"
            "print(f\"reserve_margin_pct:     {scenario['reserve_margin_pct']:.2f}%\")\n"
            "print(f\"probability_of_stress:  {scenario['probability_of_stress']:.3f}\")\n"
            "print(f\"stress_drivers:         {scenario['stress_drivers']}\")"
        ),
        new_markdown_cell(
            "## 3. Confirm the scenario conforms to the registry schema"
        ),
        new_code_cell(
            "from shared.utilities.schema_loader import validate_record\n"
            "\n"
            "ok = validate_record(scenario, 'capacity_allocation_scenario')\n"
            "print('scenario valid against capacity_allocation_scenario:', ok)"
        ),
        new_markdown_cell(
            "## 4. Sweep assumed capacity: reserve margin vs. stress probability\n\n"
            "Holding demand fixed and varying assumed available capacity shows the "
            "transparent, monotone relationship between reserve margin and "
            "probability of stress."
        ),
        new_code_cell(
            "from cricat.grid_modeling.reserve import (\n"
            "    probability_of_stress,\n"
            "    reserve_margin_pct,\n"
            ")\n"
            "\n"
            "demand_mw = 82_000.0\n"
            "capacities = [c * 1000.0 for c in range(74, 95)]  # 74,000 .. 94,000 MW\n"
            "margins = [reserve_margin_pct(demand_mw, c) for c in capacities]\n"
            "probs = [probability_of_stress(m) for m in margins]\n"
            "\n"
            "for c, m, p in zip(capacities[::4], margins[::4], probs[::4], strict=True):\n"
            "    print(f'capacity={c:>8.0f} MW  margin={m:>7.2f}%  P(stress)={p:.3f}')"
        ),
        new_code_cell(
            "%matplotlib inline\n"
            "import matplotlib.pyplot as plt\n"
            "\n"
            "fig, ax1 = plt.subplots(figsize=(9, 4.5))\n"
            "ax1.plot(margins, probs, color='#b71c1c', marker='o', markersize=3)\n"
            "ax1.axhline(0.5, color='grey', linestyle=':', linewidth=1)\n"
            "ax1.axvline(0.0, color='grey', linestyle=':', linewidth=1)\n"
            "ax1.scatter([scenario['reserve_margin_pct']], [scenario['probability_of_stress']],\n"
            "            color='#1b5e20', zorder=5, s=70, label='ERCOT scenario')\n"
            "ax1.set_xlabel('reserve margin (%)')\n"
            "ax1.set_ylabel('probability of stress (0–1)')\n"
            "ax1.set_title('CRICAT ERCOT: reserve margin vs. P(stress) (synthetic data)')\n"
            "ax1.legend()\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "print('reserve-margin / stress-probability curve rendered (synthetic).')"
        ),
        new_markdown_cell(
            "---\n\n"
            "**Recap.** A `capacity_allocation_scenario` was built from synthetic "
            "ERCOT assumptions, its reserve margin and stress probability were read "
            "out and schema-validated, and the monotone reserve-margin / "
            "stress-probability relationship was demonstrated. All values are "
            "synthetic illustrative data; no proprietary or employer content is used."
        ),
    ]
    return _write_and_register(
        "cricat_ercot_capacity_scenario",
        REPO / "cricat" / "notebooks" / "cricat_ercot_capacity_scenario.ipynb",
        cells,
    )


# --------------------------------------------------------------------------- #
# Notebook 4 — SD-MAC API demo (TestClient)
# --------------------------------------------------------------------------- #
def build_sdmac_api_demo() -> Path:
    cells = [
        new_markdown_cell(
            "# SD-MAC — API Demo (in-process, no live server)\n\n"
            "**Component:** SD-MAC (Sector-Wide Deployable Modular Analytics "
            "Commons)\n\n"
            "This notebook exercises **all seven** record endpoints of the SD-MAC "
            "FastAPI application plus the operational `/healthz` probe, using "
            "`fastapi.testclient.TestClient` — so no live server is required. The app "
            "serves entirely from bundled synthetic fixtures and schema-registry "
            "manifests.\n\n"
            + SYNTHETIC_BANNER
        ),
        new_code_cell(BOOTSTRAP),
        new_markdown_cell(
            "## 0. Boot the app in-process\n\n"
            "`TestClient(app)` wraps the ASGI app and dispatches requests in-process."
        ),
        new_code_cell(
            "import json\n"
            "\n"
            "from fastapi.testclient import TestClient\n"
            "from sdmac.api.main import app\n"
            "\n"
            "client = TestClient(app)\n"
            "\n"
            "def show(label, resp):\n"
            "    body = resp.json()\n"
            "    n = len(body) if isinstance(body, list) else 1\n"
            "    print(f'{label}: HTTP {resp.status_code}  ({n} record(s))')\n"
            "    return body\n"
            "\n"
            "health = show('GET /healthz', client.get('/healthz'))\n"
            "print(json.dumps(health, indent=2))"
        ),
        new_markdown_cell(
            "## 1. GEA — `GET /v1/events` (list, with filters)\n\n"
            "Returns the compact event projection. We also demonstrate the "
            "`min_severity` filter."
        ),
        new_code_cell(
            "events = show('GET /v1/events', client.get('/v1/events'))\n"
            "print(json.dumps(events[:2], indent=2))\n"
            "\n"
            "filtered = show(\n"
            "    'GET /v1/events?min_severity=0.3',\n"
            "    client.get('/v1/events', params={'min_severity': 0.3}),\n"
            ")\n"
            "first_event_id = events[0]['event_id']\n"
            "print('first event_id:', first_event_id)"
        ),
        new_markdown_cell(
            "## 2. GEA — `GET /v1/events/{event_id}` (full record)"
        ),
        new_code_cell(
            "full_event = show(\n"
            "    f'GET /v1/events/{first_event_id}',\n"
            "    client.get(f'/v1/events/{first_event_id}'),\n"
            ")\n"
            "print(json.dumps(full_event, indent=2))"
        ),
        new_markdown_cell(
            "## 3. CRICAT — `GET /v1/forecasts/{iso_region}`"
        ),
        new_code_cell(
            "forecasts = show(\n"
            "    'GET /v1/forecasts/PJM',\n"
            "    client.get('/v1/forecasts/PJM'),\n"
            ")\n"
            "print(json.dumps(forecasts[0], indent=2))"
        ),
        new_markdown_cell(
            "## 4. CRICAT — `POST /v1/scenarios` then `GET /v1/scenarios/{id}`\n\n"
            "Demonstrates that a POST-created scenario persists in the in-memory store "
            "and is retrievable by the GET endpoint (round-trip)."
        ),
        new_code_cell(
            "create_resp = client.post(\n"
            "    '/v1/scenarios',\n"
            "    json={\n"
            "        'scenario_label': 'demo_winter_cold_snap_pjm',\n"
            "        'stress_drivers': ['cold_snap', 'fuel_constraint'],\n"
            "        'regions': ['PJM'],\n"
            "        'time_horizon_hours': 48,\n"
            "    },\n"
            ")\n"
            "created = show('POST /v1/scenarios', create_resp)\n"
            "scenario_id = created['scenario_id']\n"
            "print(json.dumps(created, indent=2))\n"
            "\n"
            "fetched = show(\n"
            "    f'GET /v1/scenarios/{scenario_id}',\n"
            "    client.get(f'/v1/scenarios/{scenario_id}'),\n"
            ")\n"
            "assert fetched['scenario_id'] == scenario_id, 'round-trip id mismatch'\n"
            "print('POST -> GET scenario round-trip OK:', scenario_id)"
        ),
        new_markdown_cell(
            "## 5. SD-MAC — `GET /v1/modules` then `GET /v1/modules/{id}`"
        ),
        new_code_cell(
            "modules = show('GET /v1/modules', client.get('/v1/modules'))\n"
            "for m in modules:\n"
            "    print(f\"  {m['module_id']:<26} {m['platform_component']:<8} {m['validation_status']}\")\n"
            "\n"
            "first_module_id = modules[0]['module_id']\n"
            "full_module = show(\n"
            "    f'GET /v1/modules/{first_module_id}',\n"
            "    client.get(f'/v1/modules/{first_module_id}'),\n"
            ")\n"
            "print(json.dumps(full_module, indent=2))"
        ),
        new_markdown_cell(
            "## 6. Summary — all seven record endpoints exercised"
        ),
        new_code_cell(
            "checks = [\n"
            "    ('GET  /v1/events', client.get('/v1/events').status_code),\n"
            "    (f'GET  /v1/events/{first_event_id}', client.get(f'/v1/events/{first_event_id}').status_code),\n"
            "    ('GET  /v1/forecasts/PJM', client.get('/v1/forecasts/PJM').status_code),\n"
            "    ('POST /v1/scenarios', create_resp.status_code),\n"
            "    (f'GET  /v1/scenarios/{scenario_id}', client.get(f'/v1/scenarios/{scenario_id}').status_code),\n"
            "    ('GET  /v1/modules', client.get('/v1/modules').status_code),\n"
            "    (f'GET  /v1/modules/{first_module_id}', client.get(f'/v1/modules/{first_module_id}').status_code),\n"
            "    ('GET  /healthz', client.get('/healthz').status_code),\n"
            "]\n"
            "for ep, code in checks:\n"
            "    print(f'{code}  {ep}')\n"
            "assert all(code in (200, 201) for _, code in checks), 'an endpoint did not return 2xx'\n"
            "print('\\nAll seven record endpoints (+ /healthz) returned 2xx.')"
        ),
        new_markdown_cell(
            "---\n\n"
            "**Recap.** All seven record endpoints plus `/healthz` were exercised "
            "in-process via `TestClient`, including a POST→GET scenario round-trip. "
            "Every response is synthetic illustrative data served from bundled "
            "fixtures; no live server, network access, or proprietary content is "
            "involved."
        ),
    ]
    return _write_and_register(
        "sdmac_api_demo",
        REPO / "sdmac" / "notebooks" / "sdmac_api_demo.ipynb",
        cells,
    )


# --------------------------------------------------------------------------- #
# Notebook 5 — SD-MAC schema-validation demo
# --------------------------------------------------------------------------- #
def build_sdmac_schema_validation() -> Path:
    cells = [
        new_markdown_cell(
            "# SD-MAC — Schema-Validation Demo\n\n"
            "**Component:** SD-MAC (Sector-Wide Deployable Modular Analytics "
            "Commons)\n\n"
            "This notebook validates sample records against the SD-MAC schema "
            "registry via "
            "`shared.utilities.schema_loader`. It shows a **passing** record and a "
            "**deliberately invalid** record being caught, demonstrating the "
            "schema-conformance check.\n\n"
            + SYNTHETIC_BANNER
        ),
        new_code_cell(BOOTSTRAP),
        new_markdown_cell(
            "## 1. List the registry schemas and render one as JSON Schema\n\n"
            "`load_schema` reads the registry YAML; `to_json_schema` converts it to a "
            "Draft-7 JSON Schema document used for validation."
        ),
        new_code_cell(
            "import json\n"
            "\n"
            "from shared.utilities.schema_loader import (\n"
            "    load_schema,\n"
            "    schema_registry_dir,\n"
            "    to_json_schema,\n"
            "    validate_record,\n"
            ")\n"
            "\n"
            "schemas = sorted(p.stem for p in schema_registry_dir().glob('*.yaml'))\n"
            "print('registry schemas:', schemas)\n"
            "\n"
            "reg = load_schema('supply_disruption_event')\n"
            "js = to_json_schema(reg)\n"
            "print('\\nsupply_disruption_event -> JSON Schema (Draft-7):')\n"
            "print(json.dumps(js, indent=2))"
        ),
        new_markdown_cell(
            "## 2. A passing record\n\n"
            "A well-formed synthetic `supply_disruption_event` validates cleanly."
        ),
        new_code_cell(
            "valid_event = {\n"
            "    'event_id': 'GEA-EVT-DEMO-0001',\n"
            "    'detected_at_utc': '2026-03-15T12:00:00Z',\n"
            "    'commodity': 'natural_gas',\n"
            "    'region_iso': 'USA',\n"
            "    'source_categories': ['sanctions', 'weather'],\n"
            "    'severity_score': 0.62,\n"
            "    'confidence': 0.74,\n"
            "    'public_evidence_refs': [\n"
            "        'https://example.org/synthetic-evidence/natural_gas/USA/0001/1',\n"
            "    ],\n"
            "}\n"
            "print('validating a well-formed synthetic record ...')\n"
            "ok = validate_record(valid_event, 'supply_disruption_event')\n"
            "print('PASS — record is schema-conformant:', ok)"
        ),
        new_markdown_cell(
            "## 3. A deliberately invalid record (caught)\n\n"
            "This record has `severity_score = 1.8` (outside the registry's "
            "`0.0_to_1.0` bound) and a `commodity` value not in the enum. "
            "`validate_record` raises `jsonschema.ValidationError`, which we catch and "
            "report — the failure is never silently swallowed."
        ),
        new_code_cell(
            "import jsonschema\n"
            "\n"
            "invalid_event = {\n"
            "    'event_id': 'GEA-EVT-DEMO-BAD',\n"
            "    'detected_at_utc': '2026-03-15T12:00:00Z',\n"
            "    'commodity': 'unobtanium',          # not in the commodity enum\n"
            "    'region_iso': 'USA',\n"
            "    'source_categories': ['weather'],\n"
            "    'severity_score': 1.8,               # outside [0, 1]\n"
            "    'confidence': 0.74,\n"
            "    'public_evidence_refs': ['https://example.org/synthetic-evidence/bad/1'],\n"
            "}\n"
            "\n"
            "try:\n"
            "    validate_record(invalid_event, 'supply_disruption_event')\n"
            "    raise AssertionError('expected the invalid record to be rejected')\n"
            "except jsonschema.ValidationError as exc:\n"
            "    print('CAUGHT — invalid record correctly rejected.')\n"
            "    print('failing path :', list(exc.absolute_path))\n"
            "    print('message      :', exc.message)"
        ),
        new_markdown_cell(
            "## 4. Conformance sweep over the bundled synthetic fixtures\n\n"
            "Every bundled synthetic record validates against its registry schema, "
            "giving a 100% conformance rate on the demonstration fixtures."
        ),
        new_code_cell(
            "from shared.utilities.io import read_json, repo_root\n"
            "\n"
            "fx = repo_root() / 'shared' / 'data_sources' / 'fixtures'\n"
            "checks = [\n"
            "    (fx / 'gea' / 'supply_disruption_events.json', 'supply_disruption_event'),\n"
            "    (fx / 'cricat' / 'load_forecast_records.json', 'load_forecast_record'),\n"
            "    (fx / 'cricat' / 'capacity_allocation_scenarios.json', 'capacity_allocation_scenario'),\n"
            "    (fx / 'sdmac' / 'module_manifests.json', 'module_manifest'),\n"
            "]\n"
            "\n"
            "total = 0\n"
            "for path, schema_name in checks:\n"
            "    records = read_json(path)\n"
            "    for rec in records:\n"
            "        validate_record(rec, schema_name)\n"
            "    total += len(records)\n"
            "    print(f'{schema_name:<32} {len(records):>2} record(s)  -> all valid')\n"
            "print(f'\\nconformance rate: {total}/{total} synthetic fixture records valid (100%).')"
        ),
        new_markdown_cell(
            "---\n\n"
            "**Recap.** The registry YAML was rendered to JSON Schema, a well-formed "
            "synthetic record passed, a deliberately invalid record was caught and "
            "reported, and every bundled synthetic fixture record validated against "
            "its schema. All data is synthetic illustrative data; no proprietary or "
            "employer content is used."
        ),
    ]
    return _write_and_register(
        "sdmac_schema_validation_demo",
        REPO / "sdmac" / "notebooks" / "sdmac_schema_validation_demo.ipynb",
        cells,
    )


# --------------------------------------------------------------------------- #
# Notebook 6 — OEFAF governance pipeline (narrative)
# --------------------------------------------------------------------------- #
def build_oefaf_governance_pipeline() -> Path:
    cells = [
        new_markdown_cell(
            "# OEFAF — Governance & Contribution-Review Pipeline (Process Walkthrough)\n\n"
            "This notebook is a **narrative, process-only** walkthrough of the "
            "**planned** OEFAF contribution, code-review, and security-review "
            "pipeline. It reads from governance documents only "
            "(`GOVERNANCE.md`, `CONTRIBUTING.md`) and renders a small process "
            "diagram. It demonstrates the planned governance process and "
            "cross-references the full draft governance and nonprofit plan.\n\n"
            "> **Planned / conditional only.** The Open Energy Finance Analytics "
            "Foundation (OEFAF) is **in formation as a Section 501(c)(3) public "
            "charity**; its Articles of Incorporation have **not** been filed. "
            "Everything in this notebook is described in planned and conditional "
            "tense. Nothing here is a present-tense claim of incorporation or legal "
            "status.\n\n"
            + SYNTHETIC_BANNER
        ),
        new_code_cell(BOOTSTRAP),
        new_markdown_cell(
            "## 1. Source governance documents (read-only)\n\n"
            "The pipeline below is sourced entirely from the repository's governance "
            "documents — no proprietary or employer process is described."
        ),
        new_code_cell(
            "from shared.utilities.io import repo_root\n"
            "\n"
            "root = repo_root()\n"
            "for doc in ['GOVERNANCE.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md']:\n"
            "    p = root / doc\n"
            "    print(f'{doc:<20} present={p.is_file()}  ({p.stat().st_size if p.is_file() else 0} bytes)')"
        ),
        new_markdown_cell(
            "## 2. The planned contribution → review → release pipeline\n\n"
            "The planned pipeline has the following stages. Each stage is "
            "**conditional** and reflects the policy drafted in `GOVERNANCE.md` and "
            "`CONTRIBUTING.md`:\n\n"
            "1. **Proposal** — a contributor opens an issue describing the change "
            "and the public/openly licensed inputs it would use.\n"
            "2. **Clean-room / public-data gate** — the contribution must use only "
            "public or openly licensed inputs, developed independently of any "
            "proprietary system (non-negotiable rule).\n"
            "3. **Maintainer code review** — at least one maintainer reviews "
            "correctness, reproducibility (seeded, offline, Python 3.12), and schema "
            "conformance for any registry record types.\n"
            "4. **Security review (conditional)** — changes touching the API "
            "surface, data ingestion, or dependency manifests would receive an "
            "additional security review (input validation, dependency provenance, "
            "no non-public data paths).\n"
            "5. **Schema-conformance check** — emitted records would be validated "
            "against the SD-MAC schema registry.\n"
            "6. **Merge & public release** — accepted under the MIT License, "
            "intended for public release under the planned OEFAF governance.\n\n"
            "Each stage is intended to be overseen, upon incorporation, by the "
            "planned board of directors and technical advisory committee described "
            "in the draft governance and nonprofit plan."
        ),
        new_code_cell(
            "# The planned pipeline as structured, conditional data (process only).\n"
            "pipeline_stages = [\n"
            "    ('Proposal', 'Contributor opens an issue describing the change and its public inputs.'),\n"
            "    ('Clean-room / public-data gate', 'Public or openly licensed inputs only; clean-room development (non-negotiable).'),\n"
            "    ('Maintainer code review', 'At least one maintainer reviews correctness, reproducibility, schema conformance.'),\n"
            "    ('Security review (conditional)', 'API / ingestion / dependency changes get an added security review.'),\n"
            "    ('Schema-conformance check', 'Emitted records validated against the SD-MAC schema registry.'),\n"
            "    ('Merge & public release', 'Accepted under MIT; intended for public release under planned OEFAF governance.'),\n"
            "]\n"
            "for i, (stage, desc) in enumerate(pipeline_stages, start=1):\n"
            "    print(f'{i}. {stage}\\n   -> {desc}')"
        ),
        new_markdown_cell(
            "## 3. Mermaid source for the planned pipeline\n\n"
            "The planned pipeline as a Mermaid flowchart (text source — renderable in "
            "any Mermaid viewer). All nodes are planned/conditional process steps."
        ),
        new_code_cell(
            "mermaid_src = '''flowchart TD\n"
            "    A[Proposal: open issue] --> B{Clean-room and public-data gate}\n"
            "    B -- fails --> X[Cannot be accepted]\n"
            "    B -- passes --> C[Maintainer code review]\n"
            "    C --> D{Touches API / ingestion / deps?}\n"
            "    D -- yes --> E[Security review]\n"
            "    D -- no --> F[Schema-conformance check]\n"
            "    E --> F\n"
            "    F --> G[Merge and public release under MIT]\n"
            "    G --> H[(Planned OEFAF governance oversight, upon incorporation)]\n"
            "'''\n"
            "print(mermaid_src)"
        ),
        new_markdown_cell(
            "## 4. A simple matplotlib rendering of the planned flow\n\n"
            "A lightweight, dependency-free flow rendering so the notebook is "
            "self-contained even without a Mermaid renderer."
        ),
        new_code_cell(
            "%matplotlib inline\n"
            "import matplotlib.pyplot as plt\n"
            "from matplotlib.patches import FancyArrowPatch, FancyBboxPatch\n"
            "\n"
            "labels = [s for s, _ in pipeline_stages]\n"
            "fig, ax = plt.subplots(figsize=(7.5, 9))\n"
            "ax.set_xlim(0, 10)\n"
            "ax.set_ylim(0, len(labels) * 2 + 1)\n"
            "ax.axis('off')\n"
            "ax.set_title('Planned OEFAF contribution-review pipeline\\n(process only; conditional)', fontsize=11)\n"
            "\n"
            "y = len(labels) * 2\n"
            "centers = []\n"
            "for label in labels:\n"
            "    box = FancyBboxPatch((1.0, y - 0.6), 8.0, 1.1,\n"
            "                         boxstyle='round,pad=0.1', linewidth=1.2,\n"
            "                         edgecolor='#2e3b4e', facecolor='#e8eef5')\n"
            "    ax.add_patch(box)\n"
            "    ax.text(5.0, y - 0.05, label, ha='center', va='center', fontsize=9)\n"
            "    centers.append(y - 0.6)\n"
            "    y -= 2\n"
            "\n"
            "for top, bottom in zip(centers[:-1], centers[1:], strict=True):\n"
            "    arrow = FancyArrowPatch((5.0, top), (5.0, bottom + 1.1),\n"
            "                            arrowstyle='-|>', mutation_scale=14, color='#2e3b4e')\n"
            "    ax.add_patch(arrow)\n"
            "\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "print('planned-pipeline flow rendered (process only, conditional tense).')"
        ),
        new_markdown_cell(
            "---\n\n"
            "**Recap.** This notebook described the **planned** OEFAF contribution, "
            "code-review, and security-review pipeline as a process walkthrough, "
            "sourced from governance documents only, in planned/conditional tense. "
            "OEFAF is in formation as a Section 501(c)(3) public charity; its Articles "
            "have not been filed. A full draft governance and nonprofit plan "
            "accompanies the platform. No proprietary or employer content is used."
        ),
    ]
    return _write_and_register(
        "oefaf_governance_pipeline",
        REPO / "sdmac" / "notebooks" / "oefaf_governance_pipeline.ipynb",
        cells,
    )


def main() -> None:
    builders = [
        build_gea_event_scoring,
        build_cricat_pjm_forecast,
        build_cricat_ercot_scenario,
        build_sdmac_api_demo,
        build_sdmac_schema_validation,
        build_oefaf_governance_pipeline,
    ]
    for build in builders:
        path = build()
        print("wrote", path)


if __name__ == "__main__":
    main()
