"""Pure-core properties for the whole-record prefill map (US-014, ADR-010/D-21) -- PBT full.

Driving port = the pure function `record_weights_map` (its signature IS the
port). It is a projection of the newest-first `all_entries()` read the entry
screen already performs -- no clock, no I/O, no store call of its own.

Contract shape: pure-function (return-only), universe empty -- no state-delta
matcher applies (documented bypass: pure-function / no-side-effect code, per
the Delta-First bypass list), exactly as for its siblings `recent_entry_rows`
and `complete_record_rows`.

DISTILL-pinned contract, as properties:

  * the map is a BIJECTION onto {iso_day: kg}: its key set equals the record's
    day set exactly -- nothing dropped however old the day is (A24: a March
    2026 entry must still answer the picker in 2028), nothing invented;
  * every value is the stored weight UNCOERCED -- the map is the record's own
    number, not a rounded or re-derived one;
  * a day with no entry is simply ABSENT -- never a sentinel, never a null,
    never a zero, because the client offers a gap as a gap and a blind
    overwrite is what the prefill exists to prevent;
  * an empty record yields an empty map, and the save path is untouched.

The day strategy deliberately spans years: the head-4 slice this projection
replaced would satisfy every small-record example and fail only on depth.
"""

from __future__ import annotations

from datetime import date

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from weight_tracker.core.types import Entry
from weight_tracker.web.routes import record_weights_map

pytestmark = [pytest.mark.property, pytest.mark.us_014]

#: Multi-year span BY DESIGN (A24): the map keys on the full ISO day, so unlike
#: the year-less row grammar it stays injective across years -- and the March
#: 2026 day the headline AC pins lives outside any recent window.
record_days = st.dates(min_value=date(2024, 1, 1), max_value=date(2028, 12, 31))
weights = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 30.0..250.0 kg


@st.composite
def newest_first_record(draw, min_size: int = 0, max_size: int = 40) -> list[Entry]:
    """Distinct-day entries ordered newest first -- the shape `all_entries()`
    serves (one person's record lives in one running calendar, one day one
    entry). Sizes reach well past any recent window so depth is exercised."""
    picked = draw(st.sets(record_days, min_size=min_size, max_size=max_size))
    kgs = draw(st.lists(weights, min_size=len(picked), max_size=len(picked)))
    return [
        Entry(day=d, weight_kg=kg) for d, kg in zip(sorted(picked, reverse=True), kgs, strict=True)
    ]


# ---------------------------------------------------------------- the bijection


@given(entries=newest_first_record())
@settings(max_examples=200, deadline=None)
def test_every_stored_day_answers_and_only_stored_days_answer(entries):
    offered = record_weights_map(entries)
    assert set(offered) == {entry.day.isoformat() for entry in entries}, (
        "the map must key on EVERY stored day and no other (A24): a day dropped "
        "is a repair the record refuses, a day invented is a value never logged"
    )


@given(entries=newest_first_record())
@settings(max_examples=200, deadline=None)
def test_the_whole_record_survives_the_projection(entries):
    assert len(record_weights_map(entries)) == len(entries), (
        "nothing may be dropped or collapsed -- the map is the whole record, "
        "never a window (ADR-010: a bounded window fails A24 by construction)"
    )


@given(entries=newest_first_record())
@settings(max_examples=200, deadline=None)
@example(entries=[Entry(day=date(2026, 3, 3), weight_kg=84.9)])  # the headline AC's own day
def test_each_day_offers_its_own_weight_uncoerced(entries):
    offered = record_weights_map(entries)
    for entry in entries:
        assert offered[entry.day.isoformat()] == entry.weight_kg, (
            f"{entry.day} must offer back the weight the record stores, unrounded "
            f"and unre-derived -- got {offered[entry.day.isoformat()]}"
        )


# ---------------------------------------------------------------- degrade-to-absent


@given(data=st.data(), entries=newest_first_record(min_size=1))
@settings(max_examples=200, deadline=None)
def test_a_day_without_an_entry_is_absent_never_a_sentinel(data, entries):
    logged = {entry.day for entry in entries}
    gap = data.draw(record_days.filter(lambda day: day not in logged))
    assert gap.isoformat() not in record_weights_map(entries), (
        f"{gap} holds no entry, so it must be ABSENT from the map -- a sentinel, "
        f"a null or a zero would let the client overwrite a gap blindly"
    )


def test_an_empty_record_offers_nothing_to_correct():
    assert record_weights_map([]) == {}
