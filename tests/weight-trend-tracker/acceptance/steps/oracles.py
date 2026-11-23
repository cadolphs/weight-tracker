"""Oracles for SHIPPED rules -- the core's own functions, never a second copy.

While a feature is RED, DISTILL keeps its oracle on the test side so the
acceptance tests stay RED until production agrees with the rule. Once the
feature has shipped, that rationale expires: the rule is pinned by its own
property tests (`properties/test_axis_range_properties.py`,
`test_glance_properties.py`, `test_recent_list_properties.py`,
`test_trend_math_properties.py`), and a second implementation here would only
drift from the first. So each expectation below IMPORTS the shipped rule:

    honest axis          -> `weight_tracker.core.axis.y_axis_range`
    glance line and rate -> `weight_tracker.core.glance` (+ the shell's phrasing)
    entries-list row     -> `weight_tracker.web.views.entry_row`
    day grammar          -> `weight_tracker.core.types.day_label`

What stays INDEPENDENT is the falsifier the feature files carry themselves: the
literal bands, widths, centres, line-share percentages, row texts and glance
fragments written in Gherkin. An oracle here says "the surface agrees with the
shipped rule over the record as read back"; the scenario literals say "and the
rule is the one DISCUSS asked for".
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date

from domain_types import AxisBand
from pages import Row

from weight_tracker.core.axis import y_axis_range
from weight_tracker.core.glance import glance_of, quantize_rate, rate_glyph
from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry, TrendPoint
from weight_tracker.web.views import entry_row, glance_display_text


def honest_band(values: Sequence[float]) -> AxisBand | None:
    """The honest axis for what is plotted (ADR-012 § Range Rule); None when
    nothing is plotted."""
    axis = y_axis_range(values)
    return None if axis is None else AxisBand(lo_kg=axis.lo_kg, hi_kg=axis.hi_kg)


def rate_text(rate_kg_per_week: float) -> str:
    """The rate half of the glance line: `↓0.25 kg/week` -- quantized onto the
    0.05 grid, glyph from the ROUNDED sign (ADR-006)."""
    quantized = quantize_rate(rate_kg_per_week)
    return f"{rate_glyph(quantized)}{abs(quantized):.2f} kg/week"


def glance_text(entries: Iterable[Entry]) -> str | None:
    """The glance line the record demands: series end at 0.1 kg, plus the
    trailing-week rate once the 7-day entry span is earned; None without a trend."""
    summary = glance_of(trend_series(list(entries)))
    return None if summary is None else glance_display_text(summary)


def series_by_day(series: Iterable[TrendPoint]) -> dict[date, float]:
    return {point.day: point.trend_kg for point in series}


def entry_row_cells(day: date, kg: float, trend_kg: float | None) -> Row:
    """The one row grammar every entries list speaks (A18 as revised by US-016):
    the day, the raw weight at 0.1 kg, the trend at 0.01 kg, an EMPTY trend cell
    when the picture could not supply one (D-34/A37)."""
    row = entry_row(day, kg, trend_kg)
    return Row(day=row.day_text, raw=row.raw_text, trend=row.trend_text)


def expected_rows(entries: Iterable[Entry], smoothed: dict[date, float]) -> list[Row]:
    """Rows for exactly these entries, in the order given, each trend looked up by
    its own day -- the same lookup the shell performs (A36: one series, one rounding)."""
    return [
        entry_row_cells(entry.day, entry.weight_kg, smoothed.get(entry.day)) for entry in entries
    ]
