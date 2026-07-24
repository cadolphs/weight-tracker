"""Closed-vocabulary properties for the deliberate-study beacon (US-010, ADR-009) -- PBT full.

Driving port = POST /telemetry/trend-study through the production composition
root (one app + one SQLite record per module; each property measures its own
state DELTA, so accumulated appends never leak between examples).

DISTILL-pinned contract, as properties:
  - bounded change: any payload speaking the closed vocabulary
    {surface: home|history, control: lens|scale, value: ViewMode|TimeScale tokens}
    answers 2xx and appends EXACTLY ONE trend.study.interaction -- nothing else moves;
  - unbounded preservation: ANY other body answers 400 (never 500) and the
    append-only trail stays untouched -- no free text ever reaches it.

Vocabulary reuse (Mandate-12): surface/control token sets are pinned here as the
executable spec; value tokens derive from the core's own TimeScale/ViewMode enums.
"""

from __future__ import annotations

import pytest
from argon2 import PasswordHasher
from domain_types import TEST_PASSPHRASE
from fake_clock import FakeClock
from hypothesis import example, given, settings
from hypothesis import strategies as st
from state_delta import assert_state_delta, set_to

from weight_tracker.composition import build_app
from weight_tracker.core.types import TimeScale, ViewMode

pytestmark = [pytest.mark.property, pytest.mark.kpi, pytest.mark.us_010]

BEACON_PATH = "/telemetry/trend-study"

STUDY_SURFACES = ("home", "history")
STUDY_CONTROLS = ("lens", "scale")
STUDY_VALUES = tuple(lens.value for lens in ViewMode) + tuple(scale.value for scale in TimeScale)

#: Port-exposed trail surface (/stats): every counter a beacon COULD touch.
TRAIL_UNIVERSE = {
    "trail.trend_study_this_week",
    "trail.home_graph_shown_this_week",
    "trail.trend_glance_shown_count",
    "trail.trend_view_opened_count",
    "trail.entry_logged_count",
}


def speaks_the_vocabulary(body: object) -> bool:
    """The closed vocabulary, verbatim from the DISTILL contract (the oracle)."""
    return (
        isinstance(body, dict)
        and set(body) == {"surface", "control", "value"}
        and body["surface"] in STUDY_SURFACES
        and body["control"] in STUDY_CONTROLS
        and body["value"] in STUDY_VALUES
    )


@pytest.fixture(scope="module")
def actor(tmp_path_factory):
    """One production app over a real SQLite record; an unlocked TestClient."""
    from fastapi.testclient import TestClient

    home = tmp_path_factory.mktemp("beacon-record")
    app = build_app(
        db_path=home / "weight.db",
        clock=FakeClock(),
        passphrase_hash=PasswordHasher().hash(TEST_PASSPHRASE),
        session_signing_key="test-session-signing-key",
    )
    client = TestClient(app, raise_server_exceptions=True)
    unlocked = client.post("/login", data={"passphrase": TEST_PASSPHRASE})
    assert unlocked.status_code in (200, 303), f"unlock failed: {unlocked.status_code}"
    return client


def trail_counts(actor) -> dict[str, int]:
    stats = actor.get("/stats").json()
    return {slot: stats[slot.removeprefix("trail.")] for slot in TRAIL_UNIVERSE}


# ---------------------------------------------------------------- bounded change

closed_vocabulary_signals = st.fixed_dictionaries(
    {
        "surface": st.sampled_from(STUDY_SURFACES),
        "control": st.sampled_from(STUDY_CONTROLS),
        "value": st.sampled_from(STUDY_VALUES),
    }
)


@given(signal=closed_vocabulary_signals)
@settings(max_examples=50, deadline=None)
def test_every_closed_vocabulary_signal_is_exactly_one_deliberate_study_mark(actor, signal):
    before = trail_counts(actor)
    response = actor.post(BEACON_PATH, json=signal)
    assert 200 <= response.status_code < 300, (
        f"a closed-vocabulary tap must be accepted as deliberate study, got {response.status_code}"
    )
    assert_state_delta(
        before=before,
        after=trail_counts(actor),
        universe=TRAIL_UNIVERSE,
        expected={
            "trail.trend_study_this_week": set_to(before["trail.trend_study_this_week"] + 1),
        },
    )


# ---------------------------------------------------------- unbounded preservation

near_vocabulary_words = (
    STUDY_SURFACES + STUDY_CONTROLS + STUDY_VALUES + ("kitchen", "mood", "loud", "")
)

free_words = st.one_of(
    st.sampled_from(near_vocabulary_words),
    st.text(max_size=12),
    st.none(),
    st.booleans(),
    st.integers(-10, 10),
)

garbled_bodies = st.one_of(
    # right shape, wrong words (any field off the closed set)
    st.fixed_dictionaries({"surface": free_words, "control": free_words, "value": free_words}),
    # wrong shape: missing/extra/renamed keys
    st.dictionaries(st.text(max_size=10), free_words, max_size=4),
    # not an object at all
    free_words,
    st.lists(free_words, max_size=3),
).filter(lambda body: not speaks_the_vocabulary(body))


@given(body=garbled_bodies)
@settings(max_examples=75, deadline=None)
@example(body={"surface": "kitchen", "control": "mood", "value": "loud"})  # the AT's garble
@example(body={"surface": "home", "control": "lens", "value": "trend", "note": "free text"})
@example(body={"surface": ["home"], "control": "lens", "value": "trend"})  # unhashable, never 500
@example(body={})
def test_anything_outside_the_closed_vocabulary_is_refused_without_a_mark(actor, body):
    before = trail_counts(actor)
    response = actor.post(BEACON_PATH, json=body)
    assert response.status_code == 400, (
        f"an unknown study vocabulary must be refused with 400 -- never served, "
        f"never a 500 (ADR-009), got {response.status_code}"
    )
    assert_state_delta(
        before=before,
        after=trail_counts(actor),
        universe=TRAIL_UNIVERSE,
        expected={},  # fail-closed: NOTHING reaches the append-only trail
    )


@given(raw=st.binary(max_size=40))
@settings(max_examples=25, deadline=None)
@example(raw=b"")
@example(raw=b"surface=home&control=lens")  # a form body is not the beacon's tongue
@example(raw=b'{"surface": "home"')  # truncated JSON mid-flight
def test_an_unparseable_body_is_refused_without_a_mark(actor, raw):
    before = trail_counts(actor)
    response = actor.post(BEACON_PATH, content=raw, headers={"content-type": "application/json"})
    assert response.status_code == 400, (
        f"a body that is not JSON must be turned away with 400, never a 500, "
        f"got {response.status_code}"
    )
    assert_state_delta(
        before=before,
        after=trail_counts(actor),
        universe=TRAIL_UNIVERSE,
        expected={},
    )
