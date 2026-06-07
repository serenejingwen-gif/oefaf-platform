"""Guard that the SD-MAC API's probability-of-stress map stays in sync.

The canonical probability-of-stress curve lives in
:func:`cricat.grid_modeling.reserve.probability_of_stress`. The SD-MAC API keeps
a mirrored copy (:func:`sdmac.api.store._probability_of_stress`) so the API does
not import the CRICAT package, but the two must agree numerically. This test
fails if the mirrored constants drift apart.

All inputs are synthetic illustrative values; no real agency data and no
proprietary or employer source.
"""

from __future__ import annotations

import pytest
from cricat.grid_modeling.reserve import probability_of_stress as canonical

from sdmac.api.store import _probability_of_stress as mirrored


@pytest.mark.parametrize("margin", [-10.0, -5.0, 0.0, 5.0, 10.0, 20.0])
def test_mirrored_probability_matches_canonical(margin: float) -> None:
    """The mirrored API curve equals the canonical CRICAT curve at each margin."""
    assert mirrored(margin) == pytest.approx(canonical(margin), abs=1e-9)


def test_probability_at_zero_margin_is_one_half() -> None:
    """At a zero reserve margin both curves give exactly P(stress) = 0.5."""
    assert mirrored(0.0) == pytest.approx(0.5, abs=1e-9)
    assert canonical(0.0) == pytest.approx(0.5, abs=1e-9)
