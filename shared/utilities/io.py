"""I/O helpers for reading and writing bundled synthetic fixtures.

These helpers wrap pandas and the standard library for the small CSV/JSON
fixtures shipped with the oefaf-platform demonstration codebase. They are
intentionally minimal and fully offline — no network access is performed.

All fixtures these helpers read or write are synthetic illustrative data
generated for demonstration. They are NOT real agency data and are NOT derived
from any proprietary or employer source.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

# The exact synthetic-data disclaimer required for every fixture file/dir.
# Defined once here so io, synthetic_data, and tests all stamp identical text.
SYNTHETIC_DISCLAIMER: str = (
    "Synthetic illustrative data generated for demonstration. "
    "NOT real agency data and NOT derived from any proprietary or employer source."
)


def repo_root() -> Path:
    """Return the absolute path to the ``oefaf-platform`` repository root.

    Resolution strategy (robust to where the interpreter is launched from):

    1. Walk upward from this file's location looking for a directory that
       contains the ``sdmac/schema_registry`` marker (a stable repo landmark).
    2. Fall back to three parents up from this file
       (``shared/utilities/io.py`` -> ``shared/utilities`` -> ``shared`` ->
       repo root), which is correct for the committed layout.

    The walk-up makes the helper resilient to being imported from notebooks,
    tests, or the API regardless of the current working directory.
    """
    here = Path(__file__).resolve()
    # Intent: find the repo root by a stable structural landmark rather than a
    # hard-coded depth, so the helper keeps working if the module is relocated.
    for parent in here.parents:
        if (parent / "sdmac" / "schema_registry").is_dir():
            return parent
    # Assumption: committed layout is shared/utilities/io.py -> root is parents[2].
    return here.parents[2]


def ensure_dir(path: str | Path) -> Path:
    """Create ``path`` (and parents) if missing; return it as a ``Path``."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    """Write ``df`` to ``path`` as CSV without the pandas index.

    The directory is created if needed. Returns the written path.
    """
    p = Path(path)
    ensure_dir(p.parent)
    # index=False: fixtures are row records, not indexed frames — keep them clean.
    df.to_csv(p, index=False)
    return p


def read_csv(path: str | Path) -> pd.DataFrame:
    """Read a CSV fixture into a DataFrame."""
    return pd.read_csv(Path(path))


def write_json(obj: Any, path: str | Path) -> Path:
    """Write ``obj`` to ``path`` as pretty-printed, deterministic JSON.

    ``sort_keys`` is intentionally False so field order mirrors the schema
    registry definition order (more readable as an exhibit artifact). Output is
    deterministic because the generators that build ``obj`` are seeded.
    """
    p = Path(path)
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return p


def read_json(path: str | Path) -> Any:
    """Read a JSON fixture and return the parsed object."""
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_readme(directory: str | Path, body: str) -> Path:
    """Write a ``README.md`` into ``directory`` that begins with the disclaimer.

    Every fixture directory gets one of these so the synthetic nature of the
    data is unambiguous at every level of the tree.
    """
    d = ensure_dir(directory)
    readme = d / "README.md"
    content = f"# Synthetic fixtures\n\n> {SYNTHETIC_DISCLAIMER}\n\n{body.rstrip()}\n"
    readme.write_text(content, encoding="utf-8")
    return readme
