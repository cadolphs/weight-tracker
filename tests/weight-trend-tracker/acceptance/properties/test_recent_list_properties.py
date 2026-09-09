"""Pure-core properties for the entries-list rows (US-011, A18/D-18; trend column
US-016, D-35) -- PBT full.

Driving port = the pure functions `entry_row` and `recent_entry_rows` (their
signatures ARE the port; pure functions are the exempt single-output category,
so no state-delta universe applies -- there is no adjacent state).

DISTILL-pinned contract, as properties:

  * the ONE row definition (Mandate-12, reused verbatim by the History page's
    complete list): three cells -- `Fri 24 Jul` (%a, day WITHOUT a leading zero,
    %b), the raw weight at exactly 0.1 kg (the scale's own precision), the
    smoothed trend at exactly 0.01 kg (derived, and too slow to read at one
    decimal). `kg` never appears in a cell: it is stated once per column header;
  * a trend the projection could not supply renders as an EMPTY cell (D-34/A37)
    -- never a zero, never a stale value, never a copy of the raw weight;
  * the recent list is a PURE SLICE of the newest-first read (D-18, zero port
    changes): at most 7 rows, exactly n when n <= 7, order preserved, nothing
    invented -- entries past the seventh never appear, an empty record yields
    no rows (missing days are simply absent because entries, not days, are
    sliced), and the trend column is looked up per row, never positionally.
"""

from __future__ import annotations

import dataclasses
import re
from datetime import date

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from weight_tracker.core.types import Entry
from weight_tracker.web.routes import (
    ENTRY_COLUMN_HEADINGS,
    RECENT_LIST_ENTRIES,
    entry_row,
    recent_entry_rows,
)

pytestmark = [pytest.mark.property, pytest.mark.us_011, pytest.mark.us_016]

#: The pinned cell grammars, structurally: the day is weekday, day without a
#: leading zero, month; the raw weight is ONE decimal (the scale's own precision --
#: a second digit there would be invented); the trend is TWO (a derived value with
#: real resolution below 0.1, damped enough that a week often moves only ~0.05 kg).
#: Neither weight carries a unit: `kg` lives in the column header, once (A35/D-38).
DAY_CELL = re.compile(r"^[A-Z][a-z]{2} [1-9]\d? [A-Z][a-z]{2}$")
RAW_CELL = re.compile(r"^\d+\.\d$")
TREND_CELL = re.compile(r"^\d+\.\d{2}$")

days = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))
weights = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 30.0..250.0 kg
#: A SMOOTHED weight: derived, so it carries resolution the scale itself never had.
smoothed_weights = st.integers(min_value=3000, max_value=25000).map(lambda i: i / 100)

#: One calendar year of days for LIST-shaped strategies. The row drops the year
#: BY DESIGN (A18: a recent week needs none), so the day cell is NOT injective
#: across years -- 2020-01-01 and 2025-01-01 are both 'Wed 1 Jan'. Within a single
#: year (day, month) is unique per date, so marker-based absence oracles stay
#: sound (falsified 2026-07-24 by a cross-year collision).
single_year_days = st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))


@st.composite
def newest_first_entries(draw, max_size: int = 12) -> list[Entry]:
    """Distinct-day, marker-unique entry lists ordered newest first -- the shape
    all_entries() serves (one person's record lives in one running calendar)."""
    picked = draw(st.sets(single_year_days, max_size=max_size))
    kgs = draw(st.lists(weights, min_size=len(picked), max_size=len(picked)))
    return [
        Entry(day=d, weight_kg=kg) for d, kg in zip(sorted(picked, reverse=True), kgs, strict=True)
    ]


@st.composite
def record_with_trend(draw, max_size: int = 12):
    """A record plus a day-keyed trend mapping over exactly its days -- the shape
    `trend_by_day` hands the row builder for a healthy read (A32)."""
    entries = draw(newest_first_entries(max_size=max_size))
    kgs = draw(st.lists(smoothed_weights, min_size=len(entries), max_size=len(entries)))
    return entries, {e.day: kg for e, kg in zip(entries, kgs, strict=True)}


# ---------------------------------------------------------------- the row grammar


@given(day=days, kg=weights, trend=smoothed_weights)
@settings(max_examples=100, deadline=None)
@example(day=date(2026, 7, 24), kg=82.2, trend=82.43)  # the AT's own literal
def test_every_cell_speaks_its_pinned_grammar(day, kg, trend):
    row = entry_row(day, kg, trend)
    assert DAY_CELL.match(row.day_text), (
        f"day cell {row.day_text!r} breaks the 'Fri 24 Jul' grammar"
    )
    assert RAW_CELL.match(row.raw_text), f"raw cell {row.raw_text!r} must be a bare 0.1 kg number"
    assert TREND_CELL.match(row.trend_text), (
        f"trend cell {row.trend_text!r} must be a bare 0.01 kg number: at one decimal a "
        f"whole front-page week prints the same digits and the column reads frozen (A35)"
    )


def test_the_ats_pinned_example_verbatim():
    row = entry_row(date(2026, 7, 24), 82.2, 82.43)
    assert (row.day_text, row.raw_text, row.trend_text) == ("Fri 24 Jul", "82.2", "82.43")


@given(day=days, kg=weights, trend=smoothed_weights)
@settings(max_examples=100, deadline=None)
@example(day=date(2026, 7, 5), kg=82.0, trend=82.0)  # single-digit day: no leading zero
def test_the_row_carries_the_days_own_calendar_words_and_the_exact_weights(day, kg, trend):
    row = entry_row(day, kg, trend)
    assert row.day_text == f"{day:%a} {day.day} {day:%b}"
    assert (row.raw_text, row.trend_text) == (f"{kg:.1f}", f"{trend:.2f}")


@given(day=days, kg=weights)
@settings(max_examples=100, deadline=None)
def test_an_absent_trend_is_an_empty_cell_never_a_stand_in(day, kg):
    row = entry_row(day, kg, None)
    assert row.trend_text == "", (
        f"a degraded trend renders nothing at all (D12/A37), not {row.trend_text!r}"
    )
    intact = entry_row(day, kg, 77.0)
    assert (row.day_text, row.raw_text) == (intact.day_text, intact.raw_text), (
        "losing the trend must cost the row nothing else"
    )


@given(kg=weights, trend=smoothed_weights)
@settings(max_examples=50, deadline=None)
def test_no_cell_ever_carries_the_unit(kg, trend):
    row = entry_row(date(2026, 7, 24), kg, trend)
    assert "kg" not in "".join(row.day_text + row.raw_text + row.trend_text), (
        "the unit is stated once per column header, never per cell (D-38)"
    )
    assert all("kg" in heading for heading in ENTRY_COLUMN_HEADINGS[1:]), (
        f"both weight columns must name their unit, got {ENTRY_COLUMN_HEADINGS}"
    )


# ---------------------------------------------------------------- the pure slice


@given(record=record_with_trend())
@settings(max_examples=100, deadline=None)
def test_the_recent_list_is_capped_at_seven_and_honest_below_it(record):
    entries, smoothed = record
    rows = recent_entry_rows(entries, smoothed)
    assert len(rows) == min(len(entries), RECENT_LIST_ENTRIES), (
        "the recent list must show the last 7 ENTRIES, or every entry a young record has"
    )


@given(record=record_with_trend())
@settings(max_examples=100, deadline=None)
def test_rows_mirror_the_head_of_the_record_in_order(record):
    entries, smoothed = record
    rows = recent_entry_rows(entries, smoothed)
    for row, entry in zip(rows, entries, strict=False):
        assert row == entry_row(entry.day, entry.weight_kg, smoothed[entry.day]), (
            "every row must equal the stored entry it renders, newest first (single source)"
        )


@given(record=record_with_trend(max_size=12))
@settings(max_examples=100, deadline=None)
def test_nothing_past_the_seventh_entry_is_ever_shown(record):
    entries, smoothed = record
    shown = {row.day_text for row in recent_entry_rows(entries, smoothed)}
    for older in entries[RECENT_LIST_ENTRIES:]:
        assert f"{older.day:%a} {older.day.day} {older.day:%b}" not in shown, (
            f"{older.day} lies past the seventh entry and must be absent (A18)"
        )


@given(record=record_with_trend())
@settings(max_examples=100, deadline=None)
def test_the_trend_is_looked_up_by_day_never_by_position(record):
    """Shuffling the mapping's insertion order cannot move a value between rows --
    the row asks for its OWN day, so a positional zip could never be mistaken for
    correct here (the sharpest way this could silently break, A36)."""
    entries, smoothed = record
    reversed_map = dict(reversed(list(smoothed.items())))
    assert recent_entry_rows(entries, smoothed) == recent_entry_rows(entries, reversed_map)


@given(entries=newest_first_entries())
@settings(max_examples=100, deadline=None)
def test_an_empty_mapping_costs_only_the_trend_column(entries):
    """The degrade path has no branch of its own (D-34): an empty mapping is the
    whole mechanism, and it must leave every other cell exactly as it was."""
    rows = recent_entry_rows(entries, {})
    full = recent_entry_rows(entries, {e.day: 77.0 for e in entries})
    assert [row.trend_text for row in rows] == [""] * len(rows)
    assert [(r.day_text, r.raw_text) for r in rows] == [(f.day_text, f.raw_text) for f in full]


@given(day=days, kg=weights, trend=smoothed_weights)
@settings(max_examples=25, deadline=None)
def test_a_rendered_row_cannot_be_edited_after_the_fact(day, kg, trend):
    """Rows are FROZEN (ADR-005 / CLAUDE.md: pure functions over frozen
    dataclasses). Three renderers share one row definition, and two of them hand
    their rows straight to a template; a row that could be rewritten in place
    between building and rendering is how the front page and the History page
    would start telling different stories about the same day."""
    row = entry_row(day, kg, trend)
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.trend_text = "77.00"


def test_an_empty_record_yields_no_rows():
    assert recent_entry_rows([], {}) == []
