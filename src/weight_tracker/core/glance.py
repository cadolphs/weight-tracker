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

from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry, TrendPoint

#: ADR-006 fixed display rules (determinism contract; changed only by a superseding ADR).
RATE_STEP_KG_PER_WEEK = 0.05
RATE_SPAN_MIN_DAYS = 7  # entry-based span (latest - earliest entry date)


@dataclass(frozen=True)
class GlanceSummary:
    """Series-end trend value + raw trailing-7-day rate (None below the span threshold)."""

    trend_kg: float
    rate_kg_per_week: float | None


def glance(entries: Sequence[Entry]) -> GlanceSummary | None:
    """Current trend value and weekly rate as of the last entry day; None for an empty record.

    trend_kg = smoothed series END value (where the graph's line ends -- single source);
    rate_kg_per_week = smoothed[-1] - smoothed[-8] iff span >= RATE_SPAN_MIN_DAYS, else None.
    Pure function of the full entry set: deterministic, input-order invariant.
    """
    series = trend_series(entries)
    if not series:
        return None
    return GlanceSummary(
        trend_kg=series[-1].trend_kg,
        rate_kg_per_week=_trailing_week_rate(series, _entry_span_days(entries)),
    )


def _entry_span_days(entries: Sequence[Entry]) -> int:
    """Entry-based span in days: latest entry date minus earliest entry date (ADR-006)."""
    days = [entry.day for entry in entries]
    return (max(days) - min(days)).days


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
