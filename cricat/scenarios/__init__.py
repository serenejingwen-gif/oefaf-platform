"""CRICAT scenarios subpackage.

Exposes the capacity-allocation scenario builder that emits
``capacity_allocation_scenario`` documents.
"""

from __future__ import annotations

from cricat.scenarios.builder import build_scenario

__all__ = ["build_scenario"]
