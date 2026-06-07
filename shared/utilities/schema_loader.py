"""Load SD-MAC schema-registry YAML and validate records via ``jsonschema``.

The schema registry (``sdmac/schema_registry/*.yaml``) stores each record type
in the lightweight registry format:

    schema: <name>
    version: 0.1
    fields:
      - name: <field>
        type: <string|timestamp|float|integer|enum|array<X>|url>
        units: <optional, e.g. "0.0_to_1.0">
        values: [...]        # for enum
        description: <optional>

This module converts that registry format into a JSON Schema (Draft-7) document
and uses ``jsonschema`` (4.23.0) to validate records.

This loader operates only on the bundled schema definitions and synthetic
demonstration records. It performs no network access.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from shared.utilities.io import repo_root

# Draft-7 is broadly supported and matches the spec's stated target.
JSON_SCHEMA_DRAFT = "http://json-schema.org/draft-07/schema#"

# Map registry scalar type tokens -> (json_schema_type, optional_format).
_SCALAR_TYPE_MAP: dict[str, tuple[str, str | None]] = {
    "string": ("string", None),
    "timestamp": ("string", "date-time"),  # ISO-8601 UTC strings
    "float": ("number", None),
    "integer": ("integer", None),
    "url": ("string", "uri"),
}

# Registry "units" markers that constrain a float to the closed interval [0, 1].
# The registry uses the literal token "0.0_to_1.0" for
# severity/confidence/probability.
_UNIT_RANGE_MARKERS = {"0.0_to_1.0"}

# array<X> pattern, e.g. "array<string>", "array<url>".
_ARRAY_RE = re.compile(r"^array<\s*([a-zA-Z_]+)\s*>$")


def schema_registry_dir() -> Path:
    """Absolute path to ``sdmac/schema_registry`` under the repo root."""
    return repo_root() / "sdmac" / "schema_registry"


def load_schema(name: str) -> dict[str, Any]:
    """Load registry YAML for ``name`` and return it as a dict.

    ``name`` may be given with or without the ``.yaml`` suffix. The path is
    resolved robustly relative to the repository root (see
    :func:`shared.utilities.io.repo_root`), so the loader works from notebooks,
    tests, and the API regardless of the current working directory.

    Raises ``FileNotFoundError`` if the schema file does not exist.
    """
    stem = name[:-5] if name.endswith(".yaml") else name
    path = schema_registry_dir() / f"{stem}.yaml"
    if not path.is_file():
        raise FileNotFoundError(
            f"Schema '{stem}' not found at {path}. "
            f"Available: {sorted(p.stem for p in schema_registry_dir().glob('*.yaml'))}"
        )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "fields" not in data:
        raise ValueError(f"Malformed schema registry file: {path} (missing 'fields')")
    return data


def _field_to_json_schema(field: dict[str, Any]) -> dict[str, Any]:
    """Convert a single registry field definition into a JSON Schema fragment.

    Handles scalars, enums, arrays (``array<X>``), and the unit-based [0,1]
    range constraint. Raises ``ValueError`` on an unrecognized type token so a
    silent mis-mapping cannot slip through.
    """
    ftype = str(field.get("type", "")).strip()
    description = field.get("description")

    def _attach_desc(frag: dict[str, Any]) -> dict[str, Any]:
        # Carry the human description through for self-documenting schemas.
        if description:
            frag["description"] = str(description)
        return frag

    # --- enum -------------------------------------------------------------
    if ftype == "enum":
        values = field.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError(f"enum field '{field.get('name')}' missing 'values' list")
        # JSON Schema enum: constrain to the exact allowed value set.
        return _attach_desc({"enum": list(values)})

    # --- array<X> ---------------------------------------------------------
    array_match = _ARRAY_RE.match(ftype)
    if array_match:
        inner = array_match.group(1)
        if inner not in _SCALAR_TYPE_MAP:
            raise ValueError(
                f"array field '{field.get('name')}' has unsupported item type '{inner}'"
            )
        item_type, item_format = _SCALAR_TYPE_MAP[inner]
        items: dict[str, Any] = {"type": item_type}
        if item_format:
            # e.g. array<url> -> items are uri-formatted strings.
            items["format"] = item_format
        return _attach_desc({"type": "array", "items": items})

    # --- scalars ----------------------------------------------------------
    if ftype in _SCALAR_TYPE_MAP:
        js_type, js_format = _SCALAR_TYPE_MAP[ftype]
        frag: dict[str, Any] = {"type": js_type}
        if js_format:
            frag["format"] = js_format
        # Floats carrying the "0.0_to_1.0" unit marker get a closed [0,1] range.
        units = str(field.get("units", "")).strip()
        if ftype == "float" and units in _UNIT_RANGE_MARKERS:
            frag["minimum"] = 0
            frag["maximum"] = 1
        return _attach_desc(frag)

    raise ValueError(
        f"Unsupported registry type '{ftype}' for field '{field.get('name')}'"
    )


def to_json_schema(schema_dict: dict[str, Any]) -> dict[str, Any]:
    """Convert a loaded registry dict into a Draft-7 JSON Schema document.

    Type mapping:
      - ``string`` -> ``{"type": "string"}``
      - ``timestamp`` -> ``{"type": "string", "format": "date-time"}``
      - ``float`` -> ``{"type": "number"}`` (with ``minimum``/``maximum`` 0/1
        when ``units == "0.0_to_1.0"``)
      - ``integer`` -> ``{"type": "integer"}``
      - ``enum`` -> ``{"enum": [...]}``
      - ``array<X>`` -> ``{"type": "array", "items": <X mapped>}``
      - ``url`` -> ``{"type": "string", "format": "uri"}``

    All declared fields are marked ``required`` because the registry describes
    full record formats. ``additionalProperties`` is left permissive (True) so
    forward-compatible extra metadata does not fail validation of a draft v0.1
    record.
    """
    fields = schema_dict.get("fields", [])
    properties: dict[str, Any] = {}
    required: list[str] = []
    for field in fields:
        fname = field.get("name")
        if not fname:
            raise ValueError("Encountered a field without a 'name'")
        properties[fname] = _field_to_json_schema(field)
        required.append(fname)

    title = schema_dict.get("schema", "record")
    version = schema_dict.get("version")
    js: dict[str, Any] = {
        "$schema": JSON_SCHEMA_DRAFT,
        "title": str(title),
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": True,
    }
    if version is not None:
        # Carry the registry version through for traceability in the JSON Schema.
        js["description"] = f"Auto-generated from registry schema '{title}' v{version}."
    return js


def validate_record(record: dict[str, Any], schema_name: str) -> bool:
    """Validate ``record`` against the named registry schema.

    Loads the registry YAML, converts to JSON Schema, and validates. Returns
    ``True`` on success; raises ``jsonschema.ValidationError`` (or
    ``jsonschema.SchemaError``) on failure — propagated to the caller so a
    failed validation is never silently swallowed.
    """
    registry = load_schema(schema_name)
    json_schema = to_json_schema(registry)
    # validate() raises ValidationError on the first failing constraint.
    jsonschema.validate(instance=record, schema=json_schema)
    return True
