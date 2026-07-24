"""Pure-core properties for the recent-entries list (US-011, A18/D-18) -- PBT full.

Driving port = the pure functions `entry_row_text` and `recent_entry_rows`
(their signatures ARE the port; pure functions are the exempt single-output
category, so no state-delta universe applies -- there is no adjacent state).

DISTILL-pinned contract, as properties:

  * the ONE row grammar (Mandate-12, reused verbatim by the History page's
    complete list): `Fri 24 Jul — 82.2 kg` -- %a, day WITHOUT a leading zero,
    %b, an em dash, the weight at exactly 0.1 kg precision;
  * the recent list is a PURE SLICE of the newest-first read (D-18, zero port
    changes): at most 7 rows, exactly n when n <= 7, order preserved, nothing
    invented -- entries past the seventh never appear, an empty record yields
    no rows (missing days are simply absent because entries, not days, are
    sliced).
"""

from __future__ import annotations

import re
from datetime import date

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from weight_tracker.core.types import Entry
from weight_tracker.web.routes import RECENT_LIST_ENTRIES, entry_row_text, recent_entry_rows

pytestmark = [pytest.mark.property, pytest.mark.us_011]

#: The pinned grammar, structurally: weekday, day without a leading zero, month,
#: an em dash (never a hyphen), one decimal place, the unit.
ROW_GRAMMAR = re.compile(r"^[A-Z][a-z]{2} [1-9]\d? [A-Z][a-z]{2} — \d+\.\d kg$")

days = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))
weights = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 30.0..250.0 kg

#: One calendar year of days for LIST-shaped strategies. The row grammar drops
#: the year BY DESIGN (A18: a recent week needs none), so `entry_row_text` is
#: NOT injective across years -- 2020-01-01 and 2025-01-01 are both 'Wed 1 Jan'.
#: Within a single year (day, month) is unique per date, so marker-based
#: absence oracles stay sound (falsified 2026-07-24 by a cross-year collision).
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


# ---------------------------------------------------------------- the row grammar


@given(day=days, kg=weights)
@settings(max_examples=100, deadline=None)
@example(day=date(2026, 7, 24), kg=82.2)  # the AT's own literal
def test_every_row_speaks_the_pinned_grammar(day, kg):
    assert ROW_GRAMMAR.match(entry_row_text(day, kg)), (
        f"row {entry_row_text(day, kg)!r} breaks the 'Fri 24 Jul — 82.2 kg' grammar (A18)"
    )


def test_the_ats_pinned_example_verbatim():
    assert entry_row_text(date(2026, 7, 24), 82.2) == "Fri 24 Jul — 82.2 kg"


@given(day=days, kg=weights)
@settings(max_examples=100, deadline=None)
@example(day=date(2026, 7, 5), kg=82.0)  # single-digit day: no leading zero
def test_the_row_carries_the_days_own_calendar_words_and_the_exact_weight(day, kg):
    row = entry_row_text(day, kg)
    assert row == f"{day:%a} {day.day} {day:%b} — {kg:.1f} kg"


# ---------------------------------------------------------------- the pure slice


@given(entries=newest_first_entries())
@settings(max_examples=100, deadline=None)
def test_the_recent_list_is_capped_at_seven_and_honest_below_it(entries):
    rows = recent_entry_rows(entries)
    assert len(rows) == min(len(entries), RECENT_LIST_ENTRIES), (
        "the recent list must show the last 7 ENTRIES, or every entry a young record has"
    )


@given(entries=newest_first_entries())
@settings(max_examples=100, deadline=None)
def test_rows_mirror_the_head_of_the_record_in_order(entries):
    rows = recent_entry_rows(entries)
    for row, entry in zip(rows, entries, strict=False):
        assert row == entry_row_text(entry.day, entry.weight_kg), (
            "every row must equal the stored entry it renders, newest first (single source)"
        )


@given(entries=newest_first_entries(max_size=12))
@settings(max_examples=100, deadline=None)
def test_nothing_past_the_seventh_entry_is_ever_shown(entries):
    shown = "\n".join(recent_entry_rows(entries))
    for older in entries[RECENT_LIST_ENTRIES:]:
        assert f"{older.day:%a} {older.day.day} {older.day:%b}" not in shown, (
            f"{older.day} lies past the seventh entry and must be absent (A18)"
        )


def test_an_empty_record_yields_no_rows():
    assert recent_entry_rows([]) == []
