"""Transparent reserve-margin and probability-of-stress math for CRICAT.

These two functions are the entire grid-reliability arithmetic the scenario
builder depends on. They are intentionally simple, fully documented, and
deterministic so that any reviewer can verify them by hand:

- :func:`reserve_margin_pct` is the standard grid reserve-margin definition,
  ``(capacity - demand) / demand * 100``.
- :func:`probability_of_stress` maps a reserve margin (percent) to a
  probability in ``[0, 1]`` via a logistic curve that is **monotone decreasing**
  in the reserve margin: more headroom => lower probability of stress.

No proprietary parameters, models, or thresholds are used. The logistic
parameters below are illustrative public-methodology defaults chosen so the
curve crosses 0.5 at a zero reserve margin and is smooth; they are not derived
from any employer or proprietary calibration.
"""

from __future__ import annotations

import math

# Illustrative logistic parameters (public methodology, not proprietary).
#   p(stress) = 1 / (1 + exp(k * (margin - midpoint)))
# midpoint=0 -> p=0.5 exactly at a zero reserve margin (capacity == demand).
# k>0 with the (margin - midpoint) term gives a curve DECREASING in margin.
_STRESS_LOGISTIC_MIDPOINT_PCT: float = 0.0
_STRESS_LOGISTIC_STEEPNESS: float = 0.15


def reserve_margin_pct(demand: float, capacity: float) -> float:
    """Return the reserve margin as a percentage of demand.

    Reserve margin is the standard grid-reliability ratio::

        (capacity - demand) / demand * 100

    A positive value means available capacity exceeds demand (headroom); a
    negative value means demand exceeds capacity (a shortfall).

    Args:
        demand: Assumed (peak) demand in megawatts. Must be strictly positive —
            a zero or negative demand makes the ratio undefined.
        capacity: Assumed available capacity in megawatts.

    Returns:
        Reserve margin in percent (may be negative).

    Raises:
        ValueError: If ``demand`` is not strictly positive.
    """
    if demand <= 0:
        # Guard the division: a non-positive demand is physically meaningless
        # here and would otherwise produce inf/NaN silently.
        raise ValueError(f"demand must be strictly positive, got {demand!r}")
    return (capacity - demand) / demand * 100.0


def probability_of_stress(reserve_margin_pct: float) -> float:
    """Map a reserve margin (percent) to a probability of grid stress in [0, 1].

    The mapping is a logistic function that is **monotone decreasing** in the
    reserve margin: as headroom grows, the probability of stress falls toward 0;
    as the margin goes deeply negative (a shortfall), it rises toward 1. At a
    zero reserve margin the probability is exactly 0.5.

    The output is mathematically bounded in ``(0, 1)`` by the logistic form and
    additionally clipped to the closed interval ``[0, 1]`` to defend against
    floating-point edge values.

    Args:
        reserve_margin_pct: Reserve margin in percent (e.g. the output of
            :func:`reserve_margin_pct`).

    Returns:
        Probability of stress, a float in ``[0, 1]``.
    """
    z = _STRESS_LOGISTIC_STEEPNESS * (reserve_margin_pct - _STRESS_LOGISTIC_MIDPOINT_PCT)
    # 1 / (1 + exp(+z)) is decreasing in z, hence decreasing in the margin.
    # Guard against overflow for extreme margins so we never raise on inf.
    if z > 700:  # exp(700) is near the float64 ceiling
        prob = 0.0
    elif z < -700:
        prob = 1.0
    else:
        prob = 1.0 / (1.0 + math.exp(z))
    # Clip defensively; the logistic already lies in (0, 1) but rounding could
    # nudge it microscopically outside, and the schema requires [0, 1].
    return float(min(1.0, max(0.0, prob)))
