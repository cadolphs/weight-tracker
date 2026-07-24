"""Layer-1 pure-core properties for the phone's claimed day (US-013/US-014) -- PBT full.

Driving ports = the pure functions `bounded_day_frame` and `is_backdated`
(ADR-011 pinned signatures). Both are total over hostile input, read no clock,
and touch no I/O: `server_utc_today` / `device_today` arrive as parameters.

Contract shape: pure-function (return-only), universe empty -- no state-delta
matcher applies here (documented bypass: pure-function / no-side-effect code,
per the Delta-First bypass list). The claim strategies deliberately span days
well outside +/- MAX_DEVICE_SKEW_DAYS in BOTH directions, the extremes of the
calendar, and unparseable text.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from weight_tracker.core.types import MAX_DEVICE_SKEW_DAYS
from weight_tracker.core.validation import bounded_day_frame, is_backdated

pytestmark = [pytest.mark.property, pytest.mark.us_013, pytest.mark.us_014]

#: Server days stay inside a realistic clock range -- the hostile input under
#: test is the phone's *claim*, never the server's own UTC day.
server_days = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))
claimed_days = st.dates()
skew_offsets = st.integers(-3650, 3650)

UNPARSEABLE_CLAIMS = ["", "   ", "yesterday", "someday-soon", "2026-13-45", "19/07/2026", "NaN"]


@given(today=server_days, offset=skew_offsets)
@settings(max_examples=300, deadline=None)
@example(today=date(2026, 7, 21), offset=0)  # the phone agrees with the server
@example(today=date(2026, 7, 21), offset=1)  # one timezone ahead: taken at its word
@example(today=date(2026, 7, 21), offset=-1)  # one timezone behind: taken at its word
@example(today=date(2026, 7, 21), offset=2)  # a lying clock ahead: clamped back
@example(today=date(2026, 7, 21), offset=-900)  # a wildly wrong clock: clamped forward
def test_a_claim_is_taken_at_its_word_inside_the_skew_bound_and_clamped_outside(today, offset):
    claimed = today + timedelta(days=offset)

    framed = bounded_day_frame(claimed.isoformat(), today)

    if abs(offset) <= MAX_DEVICE_SKEW_DAYS:
        assert framed == claimed
    else:
        nearest_bound = today + timedelta(days=MAX_DEVICE_SKEW_DAYS * (1 if offset > 0 else -1))
        assert framed == nearest_bound


@given(today=server_days, claimed=claimed_days)
@settings(max_examples=200, deadline=None)
@example(today=date(2026, 7, 21), claimed=date.min)
@example(today=date(2026, 7, 21), claimed=date.max)
def test_every_parseable_claim_lands_inside_the_devices_plausible_window(today, claimed):
    framed = bounded_day_frame(claimed.isoformat(), today)

    assert framed is not None
    assert today - timedelta(days=MAX_DEVICE_SKEW_DAYS) <= framed
    assert framed <= today + timedelta(days=MAX_DEVICE_SKEW_DAYS)


@given(today=server_days, raw=st.text(max_size=30))
@settings(max_examples=300, deadline=None)
def test_hostile_claim_text_never_crashes_the_core(today, raw):
    framed = bounded_day_frame(raw, today)

    assert framed is None or (
        today - timedelta(days=MAX_DEVICE_SKEW_DAYS)
        <= framed
        <= today + timedelta(days=MAX_DEVICE_SKEW_DAYS)
    )


@given(today=server_days, raw=st.sampled_from(UNPARSEABLE_CLAIMS))
@settings(max_examples=50, deadline=None)
def test_a_day_that_cannot_be_read_at_all_answers_none(today, raw):
    assert bounded_day_frame(raw, today) is None


@given(today=server_days, offset=skew_offsets)
@settings(max_examples=200, deadline=None)
def test_framing_an_already_framed_day_changes_nothing(today, offset):
    claimed = today + timedelta(days=offset)

    framed = bounded_day_frame(claimed.isoformat(), today)

    assert framed is not None
    assert bounded_day_frame(framed.isoformat(), today) == framed


@given(entry_day=claimed_days, device_today=claimed_days)
@settings(max_examples=300, deadline=None)
@example(entry_day=date(2026, 7, 19), device_today=date(2026, 7, 20))  # a repair
@example(entry_day=date(2026, 7, 20), device_today=date(2026, 7, 20))  # this morning
def test_a_save_is_backdated_exactly_when_it_is_not_the_devices_own_day(entry_day, device_today):
    assert is_backdated(entry_day, device_today) == (entry_day != device_today)


@given(day=claimed_days)
@settings(max_examples=100, deadline=None)
def test_the_devices_own_day_is_never_a_repair(day):
    assert is_backdated(day, day) is False
