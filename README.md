# OEFAF Platform

**Open Energy Finance Analytics Foundation (OEFAF) reference platform** — a
**planned**, public, nonprofit-governed open-source analytics commons for
energy-supply and grid-reliability analytics, built entirely on public and
openly licensed data and open-source components.

This repository documents **independent, clean-room development on public data**.
It contains the runnable code, schemas, API, documentation, and notebooks for the
platform. All work here is non-proprietary: it uses only public/licensed data and
open-source libraries and imports no proprietary or employer code, data, dashboards,
models, parameters, configurations, screenshots, or identifiers.

> ## All bundled data is synthetic illustrative data
>
> **Every dataset bundled in this repository is synthetic illustrative data
> generated for demonstration. It is NOT real agency data and is NOT derived
> from any proprietary or employer source.** The fixtures exist solely so that
> the components, API, tests, and notebooks run end-to-end offline. They do not
> represent real observations from any provider listed in the data inventory.

---

## The three components

### GEA — Geopolitical-Event Analytics

GEA detects supply-disruption signals for energy commodities from public source
categories (for example, public sanctions data, public AIS vessel-position
aggregators, public satellite imagery, and public weather feeds). It scores each
candidate event for **severity** and **confidence** using a transparent,
deterministic weighted feature aggregation and emits records conforming to the
`supply_disruption_event` schema. The scoring logic is fully auditable and
contains no proprietary model parameters.

### CRICAT — Climate-Risk Integrated Capacity-Allocation Toolkit

CRICAT produces short-horizon power-load forecasts for public ISO/RTO regions
(for example, PJM and ERCOT) from calendar and weather features using
open-source scikit-learn models, with chronological train/test splits, held-out
MAPE reporting, and residual-based prediction intervals. It also models grid
reserve margin and a monotone probability-of-stress, and builds
capacity-allocation scenarios. Outputs conform to the `load_forecast_record` and
`capacity_allocation_scenario` schemas.

### SD-MAC — Sector-Wide Deployable Modular Analytics Commons

SD-MAC is the integration and dissemination layer. It hosts the draft schema
registry, the deployable-module manifests, and a FastAPI service that exposes
platform analytics over a documented REST surface. SD-MAC lets external users
(federal agencies, ISOs/RTOs, utilities, regulators, universities, and
researchers) discover modules, validate records against the registry, and query
analytics reproducibly. Outputs conform to the `module_manifest` schema.

---

## Planned governance (OEFAF)

The platform is intended to be governed by the **Open Energy Finance Analytics
Foundation (OEFAF)**, which is **in formation as a Section 501(c)(3) public
charity**. The Foundation is **planned**; its Articles of Incorporation have
**not** been filed. References throughout this repository use planned and
conditional tense ("in formation," "planned," "to be filed," "upon
incorporation"). OEFAF is not controlled by any employer or for-profit entity,
and no proprietary or employer intellectual property will be used by the
platform. The platform proceeds as a structurally independent public-interest
endeavor regardless of where any contributor is employed. The high-level governance summary is in
[`GOVERNANCE.md`](GOVERNANCE.md) and [`docs/governance/charter_draft.md`](docs/governance/charter_draft.md);
these documents describe the full draft governance and nonprofit plan.

---

## Repository layout

```
oefaf-platform/
├── README.md  LICENSE (MIT)  CONTRIBUTING.md  CODE_OF_CONDUCT.md  GOVERNANCE.md
├── pyproject.toml  requirements.txt  Makefile  .gitignore
├── .github/workflows/ci.yml          # GitHub Actions: ruff + pytest on push/PR
├── gea/                              # Geopolitical-Event Analytics
│   ├── ingestion/                    # loaders for synthetic public-source fixtures
│   ├── scoring/                      # transparent severity/confidence scoring
│   ├── notebooks/                    # gea_event_scoring_walkthrough.ipynb
│   └── tests/
├── cricat/                          # Climate-Risk Integrated Capacity-Allocation Toolkit
│   ├── load_forecasting/             # scikit-learn day-ahead load forecasting + MAPE
│   ├── grid_modeling/                # reserve margin + probability of stress
│   ├── scenarios/                    # capacity-allocation scenario builder (+ fixtures/)
│   ├── notebooks/                    # cricat_pjm_load_forecast_replication.ipynb,
│   │                                 #   cricat_ercot_capacity_scenario.ipynb
│   └── tests/
├── sdmac/                           # Sector-Wide Deployable Modular Analytics Commons
│   ├── api/                          # FastAPI app (sdmac.api.main:app) + openapi.yaml
│   ├── schema_registry/              # 4 draft YAML schemas (version 0.1)
│   ├── manifests/                    # module_manifest YAML per shipped module
│   ├── notebooks/                    # sdmac_api_demo.ipynb, sdmac_schema_validation_demo.ipynb,
│   │                                 #   oefaf_governance_pipeline.ipynb
│   └── tests/
├── shared/                          # cross-component utilities + data inventory
│   ├── data_sources/                 # sources.yaml + synthetic fixtures/ (with READMEs)
│   ├── utilities/                    # schema_loader.py, synthetic_data.py, io.py
│   └── docs/
└── docs/                            # platform documentation
    ├── architecture/                 # overview.md + diagrams/ (Mermaid .mmd + .svg + .png)
    ├── data_inventory/               # sources.md (public data-source inventory)
    ├── validation_roadmap/           # overview.md + gea.md, cricat.md, sdmac.md
    ├── governance/                   # charter_draft.md (draft governance charter)
    ├── api/                          # API usage documentation
    └── wireframes/                   # public-portal wireframe descriptions + diagrams
```

---

## Quickstart

The platform is **fully offline and deterministic** (all randomness is seeded
with `seed=42`). No network access is required or performed.

```bash
# 1. Create and populate a reproducible virtual environment.
python -m venv .venv
pip install -r requirements.txt

# 2. Run the component test suites (GEA, CRICAT, SD-MAC, shared).
make test

# 3. Boot the SD-MAC public analytics API locally.
make api          # serves sdmac.api.main:app via uvicorn at http://127.0.0.1:8000

# 4. Execute all six demonstration notebooks end-to-end.
make notebooks
```

Additional targets: `make setup` (create the `.venv` and install dependencies),
`make lint` (ruff), and `make diagrams` (render the Mermaid architecture and
wireframe diagrams). See the [`Makefile`](Makefile) for details.

> On some systems the project virtual environment lives at `.venv/`; the
> `Makefile` targets call the interpreter and tools from `.venv/bin/` directly,
> so activate the environment or run the `make` targets from the repository
> root.

---

## What this repository demonstrates

- **Independent, clean-room development.** All code, schemas, and notebooks are
  developed using public/licensed data and open-source components only, with no
  proprietary or employer-internal inputs.
- **Public-data methodology.** GEA scoring, CRICAT forecasting and grid
  modeling, and SD-MAC schema validation all operate on synthetic
  public-illustrative fixtures and demonstrate the same methodology the
  validation roadmap (`docs/validation_roadmap/`) specifies against real public
  benchmarks.
- **Reproducibility.** Deterministic seeds, pinned dependencies, executable
  notebooks, an exported `openapi.yaml`, and CI-checked tests make every result
  independently reproducible.

---

## License and hosting

Released under the [MIT License](LICENSE). Intended public hosting:
https://github.com/serenejingwen-gif/oefaf-platform.

Bundled sample data is synthetic illustrative data generated for demonstration
and is labeled as such throughout the repository.
