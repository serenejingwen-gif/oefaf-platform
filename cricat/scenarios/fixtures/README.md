# Synthetic fixtures — CRICAT capacity-allocation scenarios

> Synthetic illustrative data generated for demonstration. NOT real agency data and NOT derived from any proprietary or employer source.

These JSON files are example `capacity_allocation_scenario` documents produced
by `cricat/scenarios/builder.py::build_scenario`. Each file is a single
scenario keyed by its deterministic `scenario_id`.

- The `scenario_id` values are content-derived (a stable SHA-256 prefix of the
  label and regions), so regenerating from the same inputs yields the same ids.
- `reserve_margin_pct` and `probability_of_stress` are computed from the assumed
  demand and capacity by `cricat/grid_modeling/reserve.py`.
- The demand/capacity magnitudes are illustrative synthetic figures. No real
  ISO/RTO market data is used.
- `data_provenance` is preserved as a `<JING_WEN_TO_FILL: ...>` placeholder —
  no verified public URLs are invented here.

Regenerate by re-running the scenario builder over the example specs (see the
`cricat_ercot_capacity_scenario` notebook and the CRICAT tests).
