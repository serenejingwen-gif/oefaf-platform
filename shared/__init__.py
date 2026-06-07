"""Shared utilities and synthetic fixtures for the oefaf-platform codebase.

This package provides cross-component helpers used by GEA, CRICAT, and SD-MAC:

- :mod:`shared.utilities.schema_loader` — load the SD-MAC schema-registry YAML
  files and convert them to JSON Schema (Draft-7) for record validation.
- :mod:`shared.utilities.io` — small CSV/JSON fixture read/write helpers and a
  robust repository-root resolver.
- :mod:`shared.utilities.synthetic_data` — deterministic (seed=42) generators
  that materialize the bundled *synthetic* demonstration fixtures.

All bundled data produced by this package is synthetic illustrative data
generated for demonstration. It is NOT real agency data and is NOT derived from
any proprietary or employer source.
"""

__all__ = ["utilities"]
