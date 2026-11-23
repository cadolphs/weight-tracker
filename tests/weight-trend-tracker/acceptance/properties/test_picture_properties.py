"""Pure-core properties for the Picture (ADR-014) -- PBT full.

Driving port = the pure function `picture_of` (its signature IS the port). The
picture is everything the pages know about the record, derived from ONE smoothing
of all entries (GLOSSARY: Picture). These properties pin what used to be held by
convention across two call sites:

  * one series: the glance's end value IS the newest entry day's trend value, and
    `trend_by_day` IS the series keyed by day -- never a second computation (A36);
  * the series is the shipped `trend_series` (ADR-004), the single Kalman run;
  * the recent head is the newest seven entries whatever order the record arrives in;
  * the whole-record weights and the earliest pickable day are order-invariant;
  * the trendless picture keeps everything that needs no smoothing.
"""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from weight_tracker.core.picture import picture_of, trendless_picture_of
from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry

pytestmark = [pytest.mark.property]

days = st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))
weights = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 30.0..250.0 kg


@st.composite
def records(draw, min_size: int = 0, max_size: int = 25) -> list[Entry]:
    """A record: distinct days, one entry each, in arbitrary read order."""
    picked = draw(st.sets(days, min_size=min_size, max_size=max_size))
    kgs = draw(st.lists(weights, min_size=len(picked), max_size=len(picked)))
    entries = [Entry(day=d, weight_kg=kg) for d, kg in zip(sorted(picked), kgs, strict=True)]
    return draw(st.permutations(entries))


@given(entries=records(min_size=1))
@settings(max_examples=100, deadline=None)
def test_the_glance_end_value_is_the_newest_days_trend(entries):
    picture = picture_of(entries)
    newest = max(entry.day for entry in entries)
    assert picture.glance is not None
    assert picture.glance.trend_kg == picture.trend_by_day[newest], (
        "the glance line and the top row must state ONE number (A36): the glance is "
        "the series' end value and the row reads the same series at the same day"
    )


@given(entries=records())
@settings(max_examples=100, deadline=None)
def test_the_series_is_the_single_kalman_run_and_trend_by_day_is_its_view(entries):
    picture = picture_of(entries)
    assert list(picture.series) == trend_series(entries)
    assert picture.trend_by_day == {p.day: p.trend_kg for p in picture.series}


@given(entries=records())
@settings(max_examples=100, deadline=None)
def test_the_recent_head_is_the_newest_seven_whatever_the_read_order(entries):
    picture = picture_of(entries)
    newest_first = sorted(entries, key=lambda e: e.day, reverse=True)
    assert list(picture.recent_head) == newest_first[:7], (
        "D-18: the front page's list and the save's hand-back read ONE slice, the "
        "newest seven entries -- a pure function of the entry set, not of read order"
    )


@given(entries=records())
@settings(max_examples=100, deadline=None)
def test_read_order_cannot_change_the_picture(entries):
    assert picture_of(entries) == picture_of(list(reversed(entries))), (
        "ADR-004: the picture is a pure function of the entry SET"
    )


@given(entries=records(min_size=1))
@settings(max_examples=100, deadline=None)
def test_the_trendless_picture_keeps_everything_that_needs_no_smoothing(entries):
    healthy, trendless = picture_of(entries), trendless_picture_of(entries)
    assert trendless.series == () and trendless.trend_by_day == {} and trendless.glance is None
    assert trendless.recent_head == healthy.recent_head
    assert trendless.record_weights == healthy.record_weights
    assert trendless.earliest_pickable_day == healthy.earliest_pickable_day


def test_an_empty_record_has_an_empty_picture():
    picture = picture_of([])
    assert picture.series == ()
    assert picture.trend_by_day == {}
    assert picture.glance is None
    assert picture.recent_head == ()
    assert picture.record_weights == {}
    assert picture.earliest_pickable_day is None


def test_a_picture_cannot_be_edited_after_the_fact():
    """The picture is FROZEN (ADR-005 / ADR-014): one value is handed to the glance
    line, the recent rows, the save hand-back and the prefill map in the same
    request, so a picture that could be rewritten between two of those readers
    is how one screen would start telling two stories about the same day."""
    picture = picture_of([Entry(day=date(2026, 7, 24), weight_kg=77.2)])
    with pytest.raises(dataclasses.FrozenInstanceError):
        picture.glance = None
