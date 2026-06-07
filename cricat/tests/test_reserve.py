"""Tests for CRICAT reserve-margin and probability-of-stress math.

Covers the closed-form reserve-margin definition, the monotone-decreasing and
bounded probability-of-stress mapping, and input guards.
"""

from __future__ import annotations

import math

import pytest

from cricat.grid_modeling.reserve import probability_of_stress, reserve_margin_pct


def test_reserve_margin_known_values():
    # Capacity 20% above demand -> +20% reserve margin.
    assert reserve_margin_pct(demand=100.0, capacity=120.0) == pytest.approx(20.0)
    # Capacity equals demand -> 0% margin.
    assert reserve_margin_pct(demand=100.0, capacity=100.0) == pytest.approx(0.0)
    # Shortfall: capacity below demand -> negative margin.
    assert reserve_margin_pct(demand=100.0, capacity=90.0) == pytest.approx(-10.0)


def test_reserve_margin_scale_invariant_ratio():
    # The margin depends only on the capacity/demand ratio, not absolute scale.
    a = reserve_margin_pct(demand=100.0, capacity=110.0)
    b = reserve_margin_pct(demand=100000.0, capacity=110000.0)
    assert a == pytest.approx(b)


def test_reserve_margin_rejects_nonpositive_demand():
    with pytest.raises(ValueError):
        reserve_margin_pct(demand=0.0, capacity=100.0)
    with pytest.raises(ValueError):
        reserve_margin_pct(demand=-50.0, capacity=100.0)


def test_probability_of_stress_bounds():
    # Output is always within the closed interval [0, 1] across a wide sweep.
    for margin in range(-200, 201, 5):
        p = probability_of_stress(float(margin))
        assert 0.0 <= p <= 1.0
        assert math.isfinite(p)


def test_probability_of_stress_monotone_decreasing():
    # Strictly decreasing in reserve margin over the informative range.
    margins = [-50, -20, -10, -5, 0, 5, 10, 20, 50]
    probs = [probability_of_stress(float(m)) for m in margins]
    for earlier, later in zip(probs, probs[1:], strict=False):
        assert later < earlier, f"probability not decreasing: {probs}"


def test_probability_of_stress_midpoint_is_half():
    # By construction the curve crosses 0.5 at a zero reserve margin.
    assert probability_of_stress(0.0) == pytest.approx(0.5)


def test_probability_of_stress_extreme_margins_saturate():
    # Deep shortfall saturates toward 1; huge surplus saturates toward 0.
    assert probability_of_stress(-100000.0) == pytest.approx(1.0)
    assert probability_of_stress(100000.0) == pytest.approx(0.0)
