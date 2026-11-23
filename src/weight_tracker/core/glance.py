"""Glance summary -- pure derivation from the smoothed trend series (US-007, ADR-006).

ADR-006: weekly rate = trailing-7-day endpoint difference of the smoothed series
(`smoothed[-1] - smoothed[-8]` on the daily grid, ending at the LAST ENTRY day);
rate present iff the record spans >=7 days (latest - earliest ENTRY date, which
guarantees the grid has >=8 points); quantization `round(rate / 0.05) * 0.05`
(Python built-in round, banker's ties, pinned); glyph from the ROUNDED sign.

Pure Domain Core module: no I/O, no clock, imports nothing from the shell
(import-linter contract). String formatting (`Trend: ... kg · ... kg/week`)
belongs to the shell/template, NOT here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from weight_tracker.core.types import TrendPoint

#: ADR-006 fixed display rules (determinism contract; changed only by a superseding ADR).
RATE_STEP_KG_PER_WEEK = 0.05
RATE_SPAN_MIN_DAYS = 7  # entry-based span (latest - earliest entry date)


@dataclass(frozen=True)
class GlanceSummary:
    """Series-end trend value + raw trailing-7-day rate (None below the span threshold)."""

    trend_kg: float
    rate_kg_per_week: float | None


def glance_of(series: Sequence[TrendPoint]) -> GlanceSummary | None:
    """Current trend value and weekly rate as of the last entry day; None for an empty series.

    Takes the SERIES, never the entries (ADR-014): the smoothing runs once, in the
    picture, and this is a derivation over it -- no path here can run a second Kalman.
    trend_kg = series END value (where the graph's line ends -- single source);
    rate_kg_per_week = smoothed[-1] - smoothed[-8] iff span >= RATE_SPAN_MIN_DAYS, else None.
    The entry span is the grid span: the grid runs first->last ENTRY day (ADR-004).
    """
    if not series:
        return None
    return GlanceSummary(
        trend_kg=series[-1].trend_kg,
        rate_kg_per_week=_trailing_week_rate(series, _grid_span_days(series)),
    )


def _grid_span_days(series: Sequence[TrendPoint]) -> int:
    """Span in days from the first to the last grid day == latest entry date minus
    earliest entry date (ADR-006), because the grid spans exactly the entry days."""
    return (series[-1].day - series[0].day).days


def _trailing_week_rate(series: Sequence[TrendPoint], span_days: int) -> float | None:
    """smoothed[-1] - smoothed[-8] once the span is earned; None below the threshold.

    span >= 7 days <=> the daily grid has >= 8 points, so the lookback is total."""
    if span_days < RATE_SPAN_MIN_DAYS:
        return None
    return series[-1].trend_kg - series[-8].trend_kg


def quantize_rate(rate_kg_per_week: float) -> float:
    """Snap a raw rate onto the 0.05 kg/week display grid: `round(rate / 0.05) * 0.05`.

    Uses Python built-in round (banker's ties under float division, pinned as-is)."""
    return round(rate_kg_per_week / RATE_STEP_KG_PER_WEEK) * RATE_STEP_KG_PER_WEEK


def rate_glyph(quantized_rate_kg_per_week: float) -> str:
    """Direction glyph from the ROUNDED rate's sign: ↓ negative, ↑ positive, → at 0.00.

    Negative zero compares equal to zero, so a rate quantized to -0.0 reads → (steady)."""
    if quantized_rate_kg_per_week < 0:
        return "↓"
    if quantized_rate_kg_per_week > 0:
        return "↑"
    return "→"
