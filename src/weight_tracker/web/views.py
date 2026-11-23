"""Shell-side phrasing of the Picture (ADR-014): rows, wire shapes, the glance line.

The core judges the numbers; this module only phrases them. Every function here
is pure and takes a `Picture` (or a piece of one) -- no store, no clock, no
request -- so the templates place cells and format nothing, and a test can
assert a rendering without an app.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from weight_tracker.core.axis import AxisRange
from weight_tracker.core.glance import GlanceSummary, quantize_rate, rate_glyph
from weight_tracker.core.picture import Picture
from weight_tracker.core.types import Entry, day_label

#: The two weight columns' headings. `kg` is stated ONCE per column (D-38), never
#: in a cell, so `unit_label_kg` keeps a single source per rendered table.
ENTRY_COLUMN_HEADINGS = ("Date", "Raw (kg)", "Trend (kg)")

#: Rendered precision per column (A35, retuned at DELIVER dogfood -- OQ-15 closed).
#: The raw weight is shown at the scale's OWN 0.1 kg: a second digit there would be
#: invented, because the scale never measured it. The smoothed trend is shown at
#: 0.01 kg because it is a DERIVED value with real resolution below 0.1, and the
#: filter is damped enough that a week of genuine movement is often ~0.05 kg -- at
#: one decimal a whole front-page week printed the same digits seven times and the
#: column read as frozen, which is the exact failure OQ-15 named as its falsifier.
RAW_DECIMALS = 1
TREND_DECIMALS = 2


@dataclass(frozen=True)
class EntryRow:
    """The ONE row every entries list speaks (A18 as revised by US-016, Mandate-12):
    the day, the raw weight, the smoothed trend weight -- each already phrased, so a
    template places cells and formats nothing. The front page's last-7 list and the
    History page's complete record are the same rows, cut to different lengths."""

    day_text: str
    raw_text: str
    trend_text: str


def entry_row(day: date, weight_kg: float, trend_kg: float | None) -> EntryRow:
    """One row: 'Fri 24 Jul', '82.2', '82.43'.

    The two columns speak different precisions on purpose (A35): the raw weight
    at the scale's own 0.1 kg, the trend at 0.01 kg so slow movement is legible.
    Both are the SAME underlying numbers the chart plots and the glance reports --
    the glance's `Trend: 82.4 kg` is this row's 82.43 at one decimal, never a
    second computation (A36).

    A trend the picture could not supply renders as an EMPTY cell (D-34/A37):
    never a zero, never a stale value, never a copy of the raw weight."""
    return EntryRow(
        day_text=day_label(day),
        raw_text=f"{weight_kg:.{RAW_DECIMALS}f}",
        trend_text="" if trend_kg is None else f"{trend_kg:.{TREND_DECIMALS}f}",
    )


def entry_rows(entries: Sequence[Entry], trend_by_day: Mapping[date, float]) -> list[EntryRow]:
    """Rows for exactly these entries, in the order given. The trend is looked up
    with `.get`, which is why no degrade branch exists anywhere in this path: a
    trendless picture (ADR-014) renders empty trend cells and leaves everything
    else standing, and a day off the grid -- impossible by A32 -- degrades the same way."""
    return [entry_row(entry.day, entry.weight_kg, trend_by_day.get(entry.day)) for entry in entries]


def recent_entry_rows(picture: Picture) -> list[EntryRow]:
    """The last 7 entries as display rows, newest first: the picture's recent head
    (D-18, zero port changes). Fewer entries -> a shorter list; none -> no rows."""
    return entry_rows(picture.recent_head, picture.trend_by_day)


def complete_record_rows(entries: Sequence[Entry], picture: Picture) -> list[EntryRow]:
    """The COMPLETE record as display rows in the order given, newest first (US-012,
    D-17): the whole all_entries() read, never windowed by the chart's selected
    scale. Same one row definition as the front page's recent list (Mandate-12)."""
    return entry_rows(entries, picture.trend_by_day)


def entry_wire_pair(entry: Entry) -> dict[str, Any]:
    """The ONE {date, weight_kg} wire shape an entry travels as: the /entries
    read-back and the save's `recent` hand-back speak it from this single place
    (D-18 single source -- the two surfaces must tell the same story)."""
    return {"date": entry.day.isoformat(), "weight_kg": entry.weight_kg}


def axis_range_wire(axis: AxisRange | None) -> list[float] | None:
    """The ONE place the honest axis becomes its wire shape (ADR-012, D-31):
    `[lo, hi]` when something is plotted, `null` when nothing is. Route-level
    enrichment beside the series reads -- never a port widening."""
    if axis is None:
        return None
    return [axis.lo_kg, axis.hi_kg]


def recent_entries_payload(picture: Picture) -> list[dict[str, Any]]:
    """The save response's `recent` hand-back (D-19): the SAME newest-first
    seven-entry slice the front page renders (01-04's one slice), spoken as
    {date, weight_kg} wire pairs for the client's in-place list repaint --
    route-level enrichment on the glance/confirmation precedent, port untouched.

    Each pair carries an additive `trend_kg` (always present, null under a
    trendless picture) so the repaint can rebuild the trend column without a
    second fetch and without a second lookup (ADR-013 / D-37). This is the ONLY
    place the trend reaches the wire: `GET /entries` is the raw lens's read and
    stays untouched -- the trend lens has `/trend`, and one series must never
    travel two paths (A36)."""
    return [
        {**entry_wire_pair(entry), "trend_kg": picture.trend_by_day.get(entry.day)}
        for entry in picture.recent_head
    ]


def glance_display_text(summary: GlanceSummary) -> str:
    """ADR-006 pinned display: `Trend: {value:.1f} kg` with the rate segment
    ` · {glyph}{abs:.2f} kg/week` (glyph directly prefixing the quantized
    magnitude) once the 7-day entry span is earned. The core judges the numbers;
    this shell only phrases them."""
    value_text = f"Trend: {summary.trend_kg:.1f} kg"
    if summary.rate_kg_per_week is None:
        return value_text
    quantized_rate = quantize_rate(summary.rate_kg_per_week)
    return f"{value_text} · {rate_glyph(quantized_rate)}{abs(quantized_rate):.2f} kg/week"
