# Public Data-Source Inventory

This page catalogs the public and openly licensed data sources identified for
use across GEA, CRICAT, and SD-MAC. It is kept in sync with the machine-readable
inventory at
[`shared/data_sources/sources.yaml`](../../shared/data_sources/sources.yaml).

All sources listed below are public or openly licensed; no proprietary or
restricted feeds appear. Verified public URLs are intentionally **not** invented
here — the `Public access reference` column uses the `<JING_WEN_TO_FILL>`
placeholder convention until the verified links are filled in.

> **Note on bundled data.** Any sample or fixture data bundled in this
> repository is synthetic illustrative data generated for demonstration. It is
> NOT real agency data and NOT derived from any proprietary or employer source.

| Data source | Provider | License / access | Platform component | Public access reference |
|---|---|---|---|---|
| NCEP / NWS numerical weather forecasts | NOAA National Centers for Environmental Prediction | U.S. Government public domain | CRICAT (load forecasting); GEA (weather-driven supply disruption) | `<JING_WEN_TO_FILL: verified public URL for NCEP/NWS data>` |
| ECMWF Open Data | European Centre for Medium-Range Weather Forecasts | ECMWF Open Data License (CC BY 4.0) | CRICAT; GEA | `<JING_WEN_TO_FILL: verified public URL for ECMWF Open Data>` |
| EIA Open Data API | U.S. Energy Information Administration | U.S. Government public domain | GEA (supply); CRICAT (capacity) | `<JING_WEN_TO_FILL: verified public URL for the EIA Open Data API>` |
| FERC eLibrary | Federal Energy Regulatory Commission | U.S. Government public domain | CRICAT (regulatory); SD-MAC (governance reference) | `<JING_WEN_TO_FILL: verified public URL for FERC eLibrary>` |
| NERC reliability assessments and event reports | North American Electric Reliability Corporation | Publicly published | CRICAT (reliability) | `<JING_WEN_TO_FILL: verified public URL for NERC publications>` |
| OFAC SDN list and sanctions data | U.S. Department of the Treasury, Office of Foreign Assets Control | U.S. Government public domain | GEA (sanctions / event detection) | `<JING_WEN_TO_FILL: verified public URL for OFAC SDN list>` |
| Public AIS vessel-position aggregators | Multiple (public AIS aggregators) | Public / licensed-public terms | GEA (shipping disruption monitoring) | `<JING_WEN_TO_FILL: verified public URL(s) for selected public AIS aggregator(s)>` |
| Sentinel-2 / Landsat 8/9 satellite imagery | Copernicus / NASA / USGS | Free and open (Copernicus / USGS) | GEA (satellite-based event detection); CRICAT (infrastructure) | `<JING_WEN_TO_FILL: verified public URL for the Copernicus Open Access Hub and USGS EarthExplorer entry points>` |
| ISO/RTO public market data — PJM, ERCOT, MISO | PJM Interconnection; ERCOT; MISO | Public market data terms | CRICAT (load and capacity); SD-MAC (replication benchmarks) | `<JING_WEN_TO_FILL: verified public URLs for PJM Data Miner 2, ERCOT Public Reports, MISO Market Reports>` |
| USGS earthquake, hydrology, and infrastructure data | U.S. Geological Survey | U.S. Government public domain | GEA (event detection); CRICAT (infrastructure exposure) | `<JING_WEN_TO_FILL: verified public URL for the relevant USGS data services>` |
| USDA NASS agricultural statistics | U.S. Department of Agriculture, National Agricultural Statistics Service | U.S. Government public domain | GEA (agricultural / commodity supply context) | `<JING_WEN_TO_FILL: verified public URL for USDA NASS Quick Stats>` |
| DOE / EIA Form data (e.g., Form 860, Form 923) | U.S. Department of Energy / EIA | U.S. Government public domain | CRICAT (generation capacity); SD-MAC (reference data) | `<JING_WEN_TO_FILL: verified public URLs for DOE/EIA Form 860 and Form 923 datasets>` |
