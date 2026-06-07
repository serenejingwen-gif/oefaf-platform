"""Export the SD-MAC API OpenAPI specification to ``sdmac/api/openapi.yaml``.

Dumps ``app.openapi()`` (the FastAPI-generated OpenAPI 3.x document) to YAML so
the spec is a committed, human-readable artifact alongside the application code.
Run from anywhere; the output path is resolved relative to the repository root.

This script reads no network or proprietary data. The API it documents serves
only synthetic illustrative data generated for demonstration.

Usage:
    python sdmac/api/export_openapi.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Ensure the repository root is importable when this file is run as a script
# (``python sdmac/api/export_openapi.py``). When imported as a module the path
# is already present, so this is a no-op then. This module lives at
# ``<repo>/sdmac/api/export_openapi.py`` -> repo root is two parents up.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from shared.utilities.io import repo_root  # noqa: E402

from sdmac.api.main import app  # noqa: E402  (import after sys.path bootstrap)


def export_openapi(output_path: Path | None = None) -> Path:
    """Write ``app.openapi()`` as YAML to ``output_path`` and return that path.

    Defaults to ``<repo_root>/sdmac/api/openapi.yaml``.
    """
    if output_path is None:
        output_path = repo_root() / "sdmac" / "api" / "openapi.yaml"
    spec = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        # sort_keys=False preserves FastAPI's path/section ordering for
        # readability; allow_unicode keeps descriptions intact.
        yaml.safe_dump(spec, fh, sort_keys=False, allow_unicode=True)
    return output_path


if __name__ == "__main__":
    written = export_openapi()
    print(f"Wrote OpenAPI spec to {written}")
