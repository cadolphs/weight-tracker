"""Layer-1 pure-core properties for the honest y-axis (US-015, ADR-012) -- PBT full.

Driving port = the pure function `y_axis_range` (its signature IS the port).
Oracle = ADR-012 § Range Rule (R-1), with FLOOR_KG = 2.0, GRID_KG = 0.5,
AUTO_PAD_FRACTION = 0.1 and the snap epsilon 1e-9:

  * None iff nothing is plotted
  * containment: lo <= min and max <= hi; lo < hi always
  * honesty floor: hi - lo >= 2.0
  * clean edges: both bounds are exact half-integers (0.5 * Z)
  * below the floor: width in [2.0, 3.0], centre within 0.25 kg of the data midpoint
  * at or above the floor: exactly the padded range snapped outward
  * order invariance and determinism over any finite float sequence

Pinned rows 1-8 (feature-delta § Range Rule) include the branch boundary (span
exactly 2.0 is ordinary) and the epsilon case (three x 77.0 stays on the grid).

# bypass: state-delta universe not declared -- `y_axis_range` is a pure function with
# a single return value and no observable state surface (tdd-methodology exempt class).
"""

from __future__ import annotations

import math

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from weight_tracker.core.axis import (
    AUTO_PAD_FRACTION,
    FLOOR_KG,
    GRID_KG,
    AxisRange,
    y_axis_range,
)

pytestmark = [pytest.mark.property, pytest.mark.us_015]

SNAP_EPSILON = 1e-9
CENTRE_TOLERANCE_KG = 0.25

raw_kg = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 0.1-precise
trend_kg = st.floats(min_value=30.0, max_value=250.0, allow_nan=False, allow_infinity=False)
plotted = st.one_of(st.lists(raw_kg, max_size=60), st.lists(trend_kg, max_size=60))
plotted_non_empty = st.one_of(
    st.lists(raw_kg, min_size=1, max_size=60), st.lists(trend_kg, min_size=1, max_size=60)
)

PINNED_ROWS = [
    ([77.1, 77.3], AxisRange(76.0, 78.5)),  # 1: 1M trend plateau
    ([78.4, 77.4], AxisRange(76.5, 79.0)),  # 2: 1M trend, 1.0 kg of loss
    ([82.1, 77.2], AxisRange(76.5, 83.0)),  # 3: 6M trend, ordinary range
    ([76.8, 77.4], AxisRange(76.0, 78.5)),  # 4: 1W raw week
    ([77.2], AxisRange(76.0, 78.5)),  # 5a: single entry
    ([77.0, 77.0, 77.0], AxisRange(76.0, 78.0)),  # 5b: all-equal, epsilon keeps the grid
    ([77.15, 77.32], AxisRange(76.0, 78.5)),  # 6: awkward midpoint
    ([76.0, 78.0], AxisRange(75.5, 78.5)),  # 7: span exactly 2.0 is ordinary
    ([90.3, 77.2], AxisRange(75.5, 92.0)),  # 8: >= 10 kg span
]


def snapped_outward(lo_raw: float, hi_raw: float) -> AxisRange:
    steps = 1 / GRID_KG
    return AxisRange(
        lo_kg=math.floor(steps * lo_raw + SNAP_EPSILON) / steps,
        hi_kg=math.ceil(steps * hi_raw - SNAP_EPSILON) / steps,
    )


def is_half_integer(bound: float) -> bool:
    return (bound / GRID_KG).is_integer()


def test_the_rule_constants_are_pinned_by_adr_012():
    assert (FLOOR_KG, GRID_KG, AUTO_PAD_FRACTION) == (2.0, 0.5, 0.1)


@pytest.mark.parametrize(("values", "expected"), PINNED_ROWS)
def test_pinned_rows_from_the_range_rule(values, expected):
    assert y_axis_range(values) == expected


@given(values=plotted)
@settings(max_examples=100, deadline=None)
def test_no_axis_iff_nothing_is_plotted(values):
    assert (y_axis_range(values) is None) == (len(values) == 0)


@given(values=plotted_non_empty)
@settings(max_examples=200, deadline=None)
@example(values=[77.2])
@example(values=[77.0, 77.0, 77.0])
@example(values=[76.0, 78.0])
def test_every_plotted_value_sits_inside_an_axis_at_least_two_kilograms_tall(values):
    axis = y_axis_range(values)
    assert axis is not None
    assert axis.lo_kg <= min(values) and max(values) <= axis.hi_kg
    assert axis.hi_kg - axis.lo_kg >= FLOOR_KG
    assert axis.lo_kg < axis.hi_kg


@given(values=plotted_non_empty)
@settings(max_examples=200, deadline=None)
@example(values=[77.0, 77.0, 77.0])
@example(values=[77.15, 77.32])
def test_both_bounds_are_exact_half_integers(values):
    axis = y_axis_range(values)
    assert axis is not None
    assert is_half_integer(axis.lo_kg) and is_half_integer(axis.hi_kg)


@given(values=plotted_non_empty)
@settings(max_examples=200, deadline=None)
def test_below_the_floor_the_band_is_two_to_three_wide_and_centred_on_the_data(values):
    lowest, highest = min(values), max(values)
    if highest - lowest >= FLOOR_KG:
        return
    axis = y_axis_range(values)
    assert axis is not None
    assert FLOOR_KG <= axis.hi_kg - axis.lo_kg <= FLOOR_KG + 2 * GRID_KG
    centre = (axis.lo_kg + axis.hi_kg) / 2
    assert abs(centre - (lowest + highest) / 2) <= CENTRE_TOLERANCE_KG


@given(values=plotted_non_empty)
@settings(max_examples=200, deadline=None)
@example(values=[76.0, 78.0])
@example(values=[90.3, 77.2])
def test_at_or_above_the_floor_the_axis_is_the_padded_range_snapped_outward(values):
    lowest, highest = min(values), max(values)
    span = highest - lowest
    if span < FLOOR_KG:
        return
    assert y_axis_range(values) == snapped_outward(
        lowest - AUTO_PAD_FRACTION * span, highest + AUTO_PAD_FRACTION * span
    )


@given(values=plotted_non_empty, seed=st.randoms())
@settings(max_examples=100, deadline=None)
def test_the_order_of_the_values_never_changes_the_axis(values, seed):
    shuffled = list(values)
    seed.shuffle(shuffled)
    assert y_axis_range(shuffled) == y_axis_range(values)
    assert y_axis_range(values) == y_axis_range(values)
