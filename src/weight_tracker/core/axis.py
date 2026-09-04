"""Honest y-axis range -- pure projection over the plotted values (US-015, ADR-012).

ADR-012 § Range Rule: nothing plotted => no axis. Otherwise `span = max - min`;
below the floor (`span < FLOOR_KG`) the band is `[mid - 1.0, mid + 1.0]` with no
extra pad; at or above it the ordinary range `[min - 0.1*span, max + 0.1*span]`.
Both bounds then snap OUTWARD to the half-kilogram grid, `floor(2x + eps) / 2`
and `ceil(2x - eps) / 2` with `eps = 1e-9`: every multiple of 0.5 is an exact
binary float, so bounds are exact on the wire (76.5, never 76.49999), and eps
keeps a value within float noise of a grid line on that line.

Pure Domain Core module: no I/O, no clock, imports nothing from the shell
(import-linter contract). The rule takes VALUES, not entries -- it is lens-
agnostic and windowing happens upstream. The wire phrasing (`[lo, hi]` / null)
belongs to the shell, NOT here.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

#: ADR-012 rule constants (D-30): defined here and nowhere else.
FLOOR_KG = 2.0  # minimum visible y-span, absolute (D6)
GRID_KG = 0.5  # bounds snap outward to this grid (D9)
AUTO_PAD_FRACTION = 0.1  # ordinary-range pad per side, as a fraction of the span (D-28)
SNAP_EPSILON = 1e-9  # grid tolerance absorbing float noise from the pre-snap arithmetic


@dataclass(frozen=True)
class AxisRange:
    """The visible y-axis a chart is offered: lo_kg < hi_kg, both on the half-kg grid."""

    lo_kg: float
    hi_kg: float


#: A pre-snap `(lo, hi)` pair -- the rule's working value before it earns the grid.
_Bounds = tuple[float, float]


def y_axis_range(values: Sequence[float]) -> AxisRange | None:
    """The honest axis for what is plotted; None when nothing is.

    Total over any finite float sequence, order-invariant, deterministic."""
    if not values:
        return None
    lo_kg, hi_kg = _snap_outward(_unsnapped_bounds(min(values), max(values)))
    return AxisRange(lo_kg=lo_kg, hi_kg=hi_kg)


def _unsnapped_bounds(lowest: float, highest: float) -> _Bounds:
    """Floor band below FLOOR_KG of movement; the padded ordinary range at or above it."""
    if highest - lowest < FLOOR_KG:
        return _floor_band(lowest, highest)
    return _padded_range(lowest, highest)


def _floor_band(lowest: float, highest: float) -> _Bounds:
    """`[mid - FLOOR_KG/2, mid + FLOOR_KG/2]` -- widen around the data, never clip."""
    mid = (lowest + highest) / 2
    return mid - FLOOR_KG / 2, mid + FLOOR_KG / 2


def _padded_range(lowest: float, highest: float) -> _Bounds:
    """`[min - pad, max + pad]` with `pad = AUTO_PAD_FRACTION * span` (explicit, D-28)."""
    pad = AUTO_PAD_FRACTION * (highest - lowest)
    return lowest - pad, highest + pad


def _snap_outward(bounds: _Bounds) -> _Bounds:
    """Each bound to its nearest grid line AWAY from the data: lo down, hi up
    (eps keeps a value within float noise of a grid line on that line)."""
    lo, hi = bounds
    lines_per_kg = 1 / GRID_KG
    return (
        math.floor(lines_per_kg * lo + SNAP_EPSILON) / lines_per_kg,
        math.ceil(lines_per_kg * hi - SNAP_EPSILON) / lines_per_kg,
    )
