"""Pytest bootstrap for the oefaf-platform reference codebase.

Ensures the repository root is importable so the component packages
(``gea``, ``cricat``, ``sdmac``, ``shared``) resolve as top-level imports
regardless of the directory pytest is launched from. The package is not
pip-installed in the demonstration ``.venv``; this conftest makes the
in-tree layout importable without an install step.

This file performs no I/O and no network access.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    # Insert at the front so the in-tree packages win over any same-named
    # site-packages module.
    sys.path.insert(0, str(_REPO_ROOT))
