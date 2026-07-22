"""Layer-1 pure-core properties for validation + upsert resolution (US-001/US-003) -- PBT full.

Driving ports = the pure functions `validate_weight`, `validate_entry_date`,
`apply_entry`. Covers C1 (boundaries by construction of the strategies),
C4 (idempotency), C6a (hostile input), C6c (closed rejection-reason set).
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from state_delta import assert_state_delta, set_to
from weight_tracker.core.types import (
    MAX_DEVICE_SKEW_DAYS,
    MAX_WEIGHT_KG,
    MIN_WEIGHT_KG,
    Rejected,
    RejectionReason,
)
from weight_tracker.core.validation import apply_entry, validate_entry_date, validate_weight

pytestmark = [pytest.mark.pending, pytest.mark.property, pytest.mark.us_001, pytest.mark.us_003]

tenths_in_range = st.integers(300, 2500).map(lambda i: i / 10)  # 30.0..250.0 at 0.1
days = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))


@given(kg=tenths_in_range)
@settings(max_examples=100, deadline=None)
@example(kg=30.0)
@example(kg=250.0)
def test_every_plausible_tenth_precision_weight_is_accepted(kg):
    assert validate_weight(f"{kg:.1f}") == kg


@given(
    kg=st.one_of(
        st.integers(0, 299).map(lambda i: i / 10),      # 0.0..29.9
        st.integers(2501, 9999).map(lambda i: i / 10),  # 250.1..999.9
    )
)
@settings(max_examples=100, deadline=None)
@example(kg=29.9)
@example(kg=250.1)
@example(kg=824.0)
def test_every_out_of_range_weight_is_rejected(kg):
    assert validate_weight(f"{kg:.1f}") == Rejected(RejectionReason.OUT_OF_RANGE)


@given(raw=st.text(max_size=30))
@settings(max_examples=200, deadline=None)
@example(raw="")
@example(raw="81.234")
@example(raw="eighty two")
@example(raw="NaN")
@example(raw="inf")
@example(raw="82,4")
def test_hostile_input_never_crashes_and_reasons_form_a_closed_set(raw):
    result = validate_weight(raw)
    if isinstance(result, Rejected):
        assert result.reason in set(RejectionReason)
    else:
        assert MIN_WEIGHT_KG <= result <= MAX_WEIGHT_KG


@given(today=days, offset=st.integers(-3650, 365))
@settings(max_examples=200, deadline=None)
@example(today=date(2026, 7, 21), offset=1)   # phone one timezone ahead: allowed
@example(today=date(2026, 7, 21), offset=2)   # two days ahead: rejected
def test_dates_are_accepted_exactly_up_to_the_device_skew_bound(today, offset):
    candidate = today + timedelta(days=offset)
    result = validate_entry_date(candidate.isoformat(), server_utc_today=today)
    if offset <= MAX_DEVICE_SKEW_DAYS:
        assert result == candidate
    else:
        assert result == Rejected(RejectionReason.FUTURE_DATE)


@given(raw=st.text(max_size=30), today=days)
@settings(max_examples=100, deadline=None)
@example(raw="someday-soon", today=date(2026, 7, 21))
def test_unparseable_dates_are_rejected_never_crashing(raw, today):
    result = validate_entry_date(raw, server_utc_today=today)
    assert isinstance(result, (date, Rejected))


@given(
    record=st.dictionaries(days, tenths_in_range, max_size=40),
    day=days,
    kg=tenths_in_range,
)
@settings(max_examples=100, deadline=None)
def test_apply_entry_replaces_never_duplicates_and_touches_nothing_else(record, day, kg):
    result = apply_entry(record, day, kg)
    universe = {d.isoformat() for d in record} | {day.isoformat()}
    assert_state_delta(
        before={d.isoformat(): w for d, w in record.items()} | {day.isoformat(): record.get(day)},
        after={d.isoformat(): result.get(d) for d in record} | {day.isoformat(): result[day]},
        universe=universe,
        expected={day.isoformat(): set_to(kg)},
    )
    assert len(result) == len(record) + (0 if day in record else 1)


@given(
    record=st.dictionaries(days, tenths_in_range, max_size=40),
    day=days,
    kg=tenths_in_range,
)
@settings(max_examples=100, deadline=None)
def test_apply_entry_is_idempotent(record, day, kg):
    once = apply_entry(record, day, kg)
    assert apply_entry(once, day, kg) == once
