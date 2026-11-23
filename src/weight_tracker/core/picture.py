"""The Picture -- everything the pages know about the record, from ONE smoothing (ADR-014).

GLOSSARY: Picture. Built once per request by `picture_of` from the single
`all_entries()` read; the Kalman+RTS pass (`trend_series`, ADR-004) runs exactly
once here and every other field is a derivation over its output or over the
entries themselves. Eager by design: one call, one smoothing, visible cost.

Only `trend_series` ever sees entries for smoothing. Anything that needs a scale
or a day (windowed series, windowed raw entries, the axis) stays OUTSIDE the
picture as a pure function over `picture.series` -- the picture takes no parameters
beyond the record, so it is one value, not a family.

Pure Domain Core module: no I/O, no clock, imports nothing from the shell
(import-linter contract). Numbers only; display text belongs to the shell.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from weight_tracker.core.glance import GlanceSummary, glance_of
from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry, TrendPoint

#: The recent list's depth (US-011, A18): the last 7 ENTRIES, never days --
#: missing days are simply absent because entries, not calendar days, are sliced.
RECENT_LIST_ENTRIES = 7


@dataclass(frozen=True)
class Picture:
    """One record, read once, smoothed once, derived every way the pages need."""

    series: tuple[TrendPoint, ...]
    """The trend: the smoothed series on the daily grid, first to last entry day."""
    trend_by_day: Mapping[date, float]
    """The SAME series keyed by calendar day (ADR-013): total over every entry day."""
    glance: GlanceSummary | None
    """The trend's end value and weekly rate (ADR-006); None for an empty record."""
    recent_head: tuple[Entry, ...]
    """The newest seven entries, newest first (D-18/D-19): the one slice both the
    front page's list and the save's hand-back read."""
    record_weights: Mapping[str, float]
    """The WHOLE record as {iso_day: kg} (ADR-010): one map answering both the
    yesterday anchor and the edit prefill. A day with no entry is simply absent."""
    earliest_pickable_day: date | None
    """How far back the date row may reach: the record's first day minus one
    calendar year (D-25); None while there is no record to reach back into."""


def picture_of(entries: Sequence[Entry]) -> Picture:
    """The picture of this record. Pure function of the entry SET: read order
    cannot change a single value (ADR-004), and the same record always answers
    identically (G-3)."""
    series = tuple(trend_series(entries))
    return Picture(
        series=series,
        trend_by_day={point.day: point.trend_kg for point in series},
        glance=glance_of(series),
        recent_head=_recent_head(entries),
        record_weights=_record_weights(entries),
        earliest_pickable_day=_earliest_pickable_day(entries),
    )


def trendless_picture_of(entries: Sequence[Entry]) -> Picture:
    """The picture with no trend in it: what the shell serves when the smoothing
    fails (ADR-014's one degrade boundary). Everything that needs no smoothing is
    still computed, so rows keep their date and raw weight, the prefill map and
    the date row stand, and only the glance line and the trend cells are absent."""
    return Picture(
        series=(),
        trend_by_day={},
        glance=None,
        recent_head=_recent_head(entries),
        record_weights=_record_weights(entries),
        earliest_pickable_day=_earliest_pickable_day(entries),
    )


def _recent_head(entries: Sequence[Entry]) -> tuple[Entry, ...]:
    newest_first = sorted(entries, key=lambda entry: entry.day, reverse=True)
    return tuple(newest_first[:RECENT_LIST_ENTRIES])


def _record_weights(entries: Sequence[Entry]) -> dict[str, float]:
    return {entry.day.isoformat(): entry.weight_kg for entry in entries}


def _earliest_pickable_day(entries: Sequence[Entry]) -> date | None:
    if not entries:
        return None
    return _one_calendar_year_earlier(min(entry.day for entry in entries))


def _one_calendar_year_earlier(day: date) -> date:
    """The same day of the same month, a year back. 29 February has no counterpart
    in a common year and settles on the 28th rather than drifting into March --
    a year of slack either way, never a day of silent calendar arithmetic."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)
