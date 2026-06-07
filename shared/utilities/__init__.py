"""Shared utility modules for the oefaf-platform codebase.

Importable as ``shared.utilities.<module>``:

- ``schema_loader`` — YAML schema-registry loading + JSON Schema generation +
  record validation via ``jsonschema``.
- ``io`` — fixture read/write helpers and repository-root resolution.
- ``synthetic_data`` — deterministic synthetic fixture generators.
"""

from shared.utilities import io, schema_loader, synthetic_data

__all__ = ["io", "schema_loader", "synthetic_data"]
