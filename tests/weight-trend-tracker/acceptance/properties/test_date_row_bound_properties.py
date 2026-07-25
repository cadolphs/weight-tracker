"""Pure-core properties for the date row's earliest reachable day (US-013, D-25/OQ-11).

WHY-NEW-FILE: tests/weight-trend-tracker/acceptance/properties/test_date_row_bound_properties.py
  CLOSEST-EXISTING: tests/weight-trend-tracker/acceptance/properties/test_prefill_map_properties.py
  EXTENSION-COST: that file's whole contract is the {iso_day: kg} BIJECTION -- its
    module docstring, its `newest_first_record` sizing and its every property are
    about nothing being dropped or invented; a calendar-arithmetic bound (leap-day
    behaviour, empty-record absence) shares only the entry-list strategy with it.
  PARALLEL-RATIONALE: this file additionally carries the browser-unreachable
    client-wiring pin (the served template's inline script), which is a structural
    assertion over rendered markup, not a property over the record -- folding it
    into the bijection file would put a non-Hypothesis, non-record assertion
    inside a module whose docstring promises PBT over the prefill map.

Driving port = the pure function `date_row_earliest_day` (its signature IS the
port). It is a projection of the SAME newest-first `all_entries()` read the entry
screen already performs -- no clock, no I/O, no second store call.

Contract shape: pure-function (return-only), universe empty -- no state-delta
matcher applies (documented bypass: pure-function / no-side-effect code, per the
Delta-First bypass list), exactly as for its siblings `record_weights_map`,
`recent_entry_rows` and `complete_record_rows`.

DISTILL-pinned contract (D-25, OQ-11 resolved at DESIGN), as properties:

  * the bound is the record's FIRST day minus one CALENDAR year -- the record
    begins at the tail of the newest-first read, so the bound never depends on
    how recently Clemens last weighed himself;
  * one year means the same day of the same month a year earlier, not a
    365-day subtraction: 29 February has no counterpart in a common year and
    settles on the 28th rather than drifting a day;
  * the bound always lies strictly before the record's own beginning, so every
    stored day the picker must reach stays reachable;
  * an empty record has NO bound at all -- None, never a sentinel day and never
    an empty-string attribute, because there is no record to reach back into.

Why the bound exists at all is worth restating, because it reads like a business
rule and is not one: the trend grid spans first->last entry day, so one mistyped
year (2026 -> 2016) would permanently stretch every recompute to ~3,650 grid
points, and entry deletion is out of scope -- recovery would be manual SQL. It is
a cheap UX guard; `validate_entry_date` remains the sole authority on what may be
saved, and widening the bound later is one attribute.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

import weight_tracker.web.routes as routes
from weight_tracker.core.types import Entry
from weight_tracker.web.routes import date_row_earliest_day

pytestmark = [pytest.mark.property, pytest.mark.us_013]

#: Multi-year span BY DESIGN: the bound is calendar arithmetic, so the strategy
#: must straddle leap years and century boundaries rather than one recent month.
record_days = st.dates(min_value=date(2020, 1, 1), max_value=date(2032, 12, 31))
weights = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 30.0..250.0 kg


@st.composite
def newest_first_record(draw, min_size: int = 0, max_size: int = 40) -> list[Entry]:
    """Distinct-day entries ordered newest first -- the shape `all_entries()`
    serves. The record's FIRST day is therefore the tail, which is exactly the
    detail a head-reading implementation would get wrong on every record but
    the one-entry one."""
    picked = draw(st.sets(record_days, min_size=min_size, max_size=max_size))
    kgs = draw(st.lists(weights, min_size=len(picked), max_size=len(picked)))
    return [
        Entry(day=d, weight_kg=kg) for d, kg in zip(sorted(picked, reverse=True), kgs, strict=True)
    ]


# ---------------------------------------------------------------- one year before the beginning


@given(entries=newest_first_record(min_size=1))
@settings(max_examples=200, deadline=None)
@example(entries=[Entry(day=date(2026, 3, 3), weight_kg=84.9)])  # the headline AC's own day
def test_the_bound_is_one_calendar_year_before_the_record_began(entries):
    first_day = min(entry.day for entry in entries)
    bound = date_row_earliest_day(entries)
    assert (bound.year, bound.month) == (first_day.year - 1, first_day.month), (
        f"the picker must reach back exactly one year before the record began "
        f"({first_day}), not to some other month -- got {bound}"
    )
    assert bound.day == first_day.day or (first_day.month, first_day.day) == (2, 29), (
        f"only 29 February may move the day of the month (a common year has none); "
        f"the bound for {first_day} landed on {bound}"
    )


@given(entries=newest_first_record(min_size=1))
@settings(max_examples=200, deadline=None)
def test_the_bound_reads_the_first_day_not_the_latest(entries):
    oldest = [Entry(day=min(e.day for e in entries), weight_kg=entries[-1].weight_kg)]
    assert date_row_earliest_day(entries) == date_row_earliest_day(oldest), (
        "the bound is anchored on where the record BEGINS: adding later mornings "
        "on top of it must never move how far back the picker may reach"
    )


@given(entries=newest_first_record(min_size=1))
@settings(max_examples=200, deadline=None)
def test_every_stored_day_stays_reachable(entries):
    bound = date_row_earliest_day(entries)
    assert all(bound < entry.day for entry in entries), (
        "a bound that excluded a stored day would make that day unrepairable -- "
        f"the record spans {min(e.day for e in entries)}..{max(e.day for e in entries)}, "
        f"the picker stops at {bound}"
    )


@given(entries=newest_first_record(min_size=1))
@settings(max_examples=200, deadline=None)
def test_the_bound_is_a_year_wide_not_a_fixed_day_count(entries):
    """A year of slack, give or take the leap day -- never a decade, never a week."""
    first_day = min(entry.day for entry in entries)
    reach = first_day - date_row_earliest_day(entries)
    assert timedelta(days=365) <= reach <= timedelta(days=366), (
        f"the reach behind {first_day} must be one year (365-366 days), got {reach.days} days"
    )


@given(day=st.dates(min_value=date(2020, 3, 1), max_value=date(2032, 2, 28)))
@settings(max_examples=200, deadline=None)
@example(day=date(2028, 2, 29))  # the leap day: a common year has no counterpart
def test_the_leap_day_settles_on_the_last_february_rather_than_drifting(day):
    bound = date_row_earliest_day([Entry(day=day, weight_kg=82.0)])
    assert bound.year == day.year - 1, f"{day} must reach back into {day.year - 1}, got {bound}"
    if (day.month, day.day) == (2, 29):
        assert (bound.month, bound.day) == (2, 28), (
            f"a common year has no 29 February: the bound settles on the last day of "
            f"that February rather than drifting into March, got {bound}"
        )


# ---------------------------------------------------------------- degrade-to-absent


def test_an_empty_record_has_no_bound_at_all():
    assert date_row_earliest_day([]) is None, (
        "there is no record to reach back into, so the row carries NO min -- "
        "never a sentinel day, never an empty-string attribute"
    )


# ---------------------------------------------------------------- browser-unreachable client pin

#: DELIVER pre-requisite 2, client-paint precedent D-15. `value` and `max` are the
#: PHONE's to set: the server has no device day (A5), and this repository ships no
#: JS test harness and gains none for this step. The honest fallback is therefore
#: structural -- the shipped inline script must WIRE both attributes to the one
#: existing `deviceLocalDay()` helper -- backed by dogfood verification of what the
#: picker actually opens on. A behavioural pin is owed to a browser, not to pytest.
ENTRY_TEMPLATE = Path(routes.__file__).parent / "templates" / "index.html"

DATE_ROW_VALUE_WIRING = re.compile(r"\.value\s*=\s*(deviceLocalDay\(\)|\w+)\s*;")
DATE_ROW_MAX_WIRING = re.compile(r"\.max\s*=\s*(deviceLocalDay\(\)|\w+)\s*;")


def test_the_inline_script_frames_the_date_row_on_the_devices_own_day():
    markup = ENTRY_TEMPLATE.read_text(encoding="utf-8")
    assert 'id="entry-date"' in markup, "the template must ship the date row itself"
    assert "deviceLocalDay" in markup, (
        "the device day must come from the ONE shipped deviceLocalDay() helper -- "
        "a second copy of the calendar rule is how the anchor and the picker drift apart"
    )
    assert DATE_ROW_VALUE_WIRING.search(markup) and DATE_ROW_MAX_WIRING.search(markup), (
        "the inline script must set the date row's `value` (where the picker opens) "
        "and `max` (the future stays closed) -- both from the device's own day, "
        "because the server cannot know the phone's calendar day (A5/D-25)"
    )
