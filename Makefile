# OEFAF Platform — developer task runner.
#
# All bundled data used by these targets is synthetic illustrative data
# generated for demonstration. It is NOT real agency data and is NOT derived
# from any proprietary or employer source. Every target runs fully offline and
# deterministically (randomness is seeded with seed=42).
#
# Targets:
#   setup      create the .venv and install pinned dependencies
#   test       run the GEA / CRICAT / SD-MAC / shared pytest suites
#   api        boot the SD-MAC public analytics API (uvicorn, reload)
#   notebooks  execute all six demonstration notebooks end-to-end (nbconvert)
#   diagrams   render the Mermaid architecture + wireframe diagrams (npx)
#   lint       run ruff over the component packages

# Interpreter and tools come from the project virtual environment so runs are
# reproducible regardless of the caller's shell.
VENV        := .venv
PY          := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
PYTEST      := $(VENV)/bin/pytest
RUFF        := $(VENV)/bin/ruff
UVICORN     := $(VENV)/bin/uvicorn
JUPYTER     := $(VENV)/bin/jupyter

# Notebook filenames (kept stable; do not rename). Order is irrelevant to
# execution; each is run in place by nbconvert.
NOTEBOOKS := \
	gea/notebooks/gea_event_scoring_walkthrough.ipynb \
	cricat/notebooks/cricat_pjm_load_forecast_replication.ipynb \
	cricat/notebooks/cricat_ercot_capacity_scenario.ipynb \
	sdmac/notebooks/sdmac_api_demo.ipynb \
	sdmac/notebooks/sdmac_schema_validation_demo.ipynb \
	sdmac/notebooks/oefaf_governance_pipeline.ipynb

# Mermaid diagram sources (architecture + wireframes).
DIAGRAMS := \
	docs/architecture/diagrams/platform_overview.mmd \
	docs/architecture/diagrams/gea.mmd \
	docs/architecture/diagrams/cricat.mmd \
	docs/architecture/diagrams/sdmac.mmd \
	docs/wireframes/gea_disruption_monitor.mmd \
	docs/wireframes/cricat_grid_stress_monitor.mmd \
	docs/wireframes/sdmac_public_portal.mmd

.DEFAULT_GOAL := test
.PHONY: setup test api notebooks diagrams lint help

help:
	@echo "OEFAF Platform make targets:"
	@echo "  setup      create .venv and install pinned dependencies"
	@echo "  test       run pytest across gea, cricat, sdmac, shared"
	@echo "  api        boot the SD-MAC API via uvicorn (reload)"
	@echo "  notebooks  execute all six demonstration notebooks (nbconvert)"
	@echo "  diagrams   render Mermaid architecture + wireframe diagrams (npx)"
	@echo "  lint       run ruff over the component packages"

# Create the reproducible virtual environment and install pinned dependencies.
setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Run the component test suites. testpaths are configured in pyproject.toml,
# but we name the component test directories explicitly here for clarity.
test:
	$(PYTEST) gea/tests cricat/tests sdmac/tests shared

# Boot the SD-MAC public analytics API. The app object is sdmac.api.main:app.
# Serves entirely from bundled synthetic fixtures; performs no network access.
api:
	$(UVICORN) sdmac.api.main:app --reload

# Execute all six notebooks in place so their outputs are populated and any
# execution error fails the target. Uses TestClient (not a live server) where a
# notebook exercises the API.
notebooks:
	$(JUPYTER) nbconvert --to notebook --execute --inplace $(NOTEBOOKS)

# Render each Mermaid source to SVG and PNG using the mermaid CLI via npx.
# Requires Node/npx on PATH; produces sibling .svg and .png next to each .mmd.
diagrams:
	@for src in $(DIAGRAMS); do \
		echo "Rendering $$src"; \
		npx -y @mermaid-js/mermaid-cli -i $$src -o $${src%.mmd}.svg; \
		npx -y @mermaid-js/mermaid-cli -i $$src -o $${src%.mmd}.png; \
	done

# Lint the component packages (configuration in pyproject.toml [tool.ruff]).
lint:
	$(RUFF) check .
