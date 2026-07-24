"""Save hand-back + ambient-defaults properties (US-010/US-011, D-19/A17) -- PBT full.

Driving ports = POST /entries and GET / through the production composition root
(one app + one SQLite record per module -- the beacon-properties precedent; every
property measures its own state DELTA, so accumulated saves never leak between
examples).

DISTILL-pinned contracts, as properties:

  * D-19 (route-level enrichment, glance/confirmation precedent): a SAVED
    response carries `recent` -- up to 7 {date, weight_kg} wire pairs, newest
    first, today's entry on top, EQUAL to the head of the /entries read
    (single source, D-18); confirmation and glance ride unchanged beside it.
    The WeightLogging universe stays exactly the bounded change it always
    was -- one {date} row + one entry.saved event per save (plus the glance
    delivery already riding the response): the hand-back adds NOTHING else.

  * A17 (unit-level pin, no AT spend): the front page IGNORES ?view=/?scale=
    -- the mount always opens at the ambient defaults trend/3M, and a
    deep-linked open stays ambient (D-16): deliberate study never moves.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

import pytest
from argon2 import PasswordHasher
from domain_types import TEST_PASSPHRASE
from fake_clock import FakeClock
from hypothesis import example, given, settings
from hypothesis import strategies as st
from state_delta import assert_state_delta, set_to

from weight_tracker.composition import build_app

pytestmark = [pytest.mark.property, pytest.mark.us_010, pytest.mark.us_011]

#: The feature's own morning (Background): Friday 24 July 2026.
TODAY = date(2026, 7, 24)

#: The save response's bounded universe (Mandate 8): the record itself plus every
#: /stats counter a save COULD touch. strict=True -- anything else moving fails.
SAVE_UNIVERSE = {
    "record.entries",
    "trail.entry_logged_count",
    "trail.trend_glance_shown_count",
    "trail.trend_study_this_week",
    "trail.home_graph_shown_this_week",
    "trail.trend_view_opened_count",
}

HOME_MOUNT = re.compile(r'<[a-z]+[^>]*id="home-graph"[^>]*>')

weights = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 30.0..250.0 kg


@pytest.fixture(scope="module")
def actor(tmp_path_factory):
    """One production app over a real SQLite record; an unlocked TestClient.

    One past entry is seeded so the front page always mounts its graph area
    (an empty record keeps the page simple by design -- not under test here)."""
    from fastapi.testclient import TestClient

    clock = FakeClock()
    clock.set_today(TODAY)
    home = tmp_path_factory.mktemp("save-recent-record")
    app = build_app(
        db_path=home / "weight.db",
        clock=clock,
        passphrase_hash=PasswordHasher().hash(TEST_PASSPHRASE),
        session_signing_key="test-session-signing-key",
    )
    client = TestClient(app, raise_server_exceptions=True)
    unlocked = client.post("/login", data={"passphrase": TEST_PASSPHRASE})
    assert unlocked.status_code in (200, 303), f"unlock failed: {unlocked.status_code}"
    seeded = client.post(
        "/entries", json={"date": (TODAY - timedelta(days=1)).isoformat(), "weight": "82.4"}
    )
    assert seeded.json()["outcome"] == "saved", "fixture seed must land"
    return client


def observable_state(actor: Any) -> dict[str, Any]:
    """Snapshot of the declared universe -- pure reads only (D-16), so capturing
    it never moves any slot it reports."""
    entries = actor.get("/entries", params={"scale": "ALL"}).json()["entries"]
    stats = actor.get("/stats").json()
    return {
        "record.entries": tuple((e["date"], e["weight_kg"]) for e in entries),
        "trail.entry_logged_count": stats["entry_logged_count"],
        "trail.trend_glance_shown_count": stats["trend_glance_shown_count"],
        "trail.trend_study_this_week": stats["trend_study_this_week"],
        "trail.home_graph_shown_this_week": stats["home_graph_shown_this_week"],
        "trail.trend_view_opened_count": stats["trend_view_opened_count"],
    }


# ---------------------------------------------------------------- D-19: the hand-back


@given(
    seeded=st.dictionaries(st.integers(min_value=1, max_value=9), weights, max_size=9),
    today_kg=weights,
)
@settings(max_examples=25, deadline=None)
@example(seeded={1: 82.4}, today_kg=82.2)  # the AT's own morning
def test_a_save_hands_back_the_recent_head_with_today_on_top(actor, seeded, today_kg):
    for offset, kg in seeded.items():
        planted = actor.post(
            "/entries",
            json={"date": (TODAY - timedelta(days=offset)).isoformat(), "weight": f"{kg:.1f}"},
        )
        assert planted.json()["outcome"] == "saved", "seeding through the port must land"
    before = observable_state(actor)

    response = actor.post("/entries", json={"date": TODAY.isoformat(), "weight": f"{today_kg:.1f}"})

    body = response.json()
    assert response.status_code == 200 and body["outcome"] == "saved"
    assert "recent" in body, (
        "a saved response must hand back the refreshed recent list (`recent`, D-19)"
    )
    recent = body["recent"]
    assert recent[0] == {"date": TODAY.isoformat(), "weight_kg": today_kg}, (
        f"today's save must sit on top of the hand-back, got {recent[:1]}"
    )
    assert len(recent) <= 7, f"the hand-back is capped at 7 entries, got {len(recent)}"
    shown_days = [row["date"] for row in recent]
    assert shown_days == sorted(shown_days, reverse=True), "newest first, always"
    stored = actor.get("/entries", params={"scale": "ALL"}).json()["entries"]
    assert recent == stored[:7], (
        "the hand-back must EQUAL the head of the /entries read -- one source (D-18), "
        "never a second story"
    )
    assert "confirmation" in body and "glance" in body, (
        "confirmation and glance ride unchanged beside the hand-back (D-19)"
    )

    merged = {d: kg for d, kg in before["record.entries"]} | {TODAY.isoformat(): today_kg}
    assert_state_delta(
        before=before,
        after=observable_state(actor),
        universe=SAVE_UNIVERSE,
        expected={
            "record.entries": set_to(tuple(sorted(merged.items(), reverse=True))),
            "trail.entry_logged_count": set_to(before["trail.entry_logged_count"] + 1),
            "trail.trend_glance_shown_count": set_to(before["trail.trend_glance_shown_count"] + 1),
        },
        strict=True,  # the hand-back adds NOTHING to the save's bounded change
    )


# ---------------------------------------------------------------- A17: ambient defaults


deep_link_tokens = st.one_of(
    st.sampled_from(("trend", "raw", "1W", "1M", "3M", "6M", "1Y", "ALL", "", "eternity")),
    st.text(max_size=8),
)


@given(view=deep_link_tokens, scale=deep_link_tokens)
@settings(max_examples=50, deadline=None)
@example(view="raw", scale="1Y")  # a well-formed deep link is ignored just the same
def test_the_front_page_ignores_view_and_scale_deep_links(actor, view, scale):
    before = observable_state(actor)

    response = actor.get("/", params={"view": view, "scale": scale})

    assert response.status_code == 200, "the front page never chokes on a deep link (C6)"
    mount = HOME_MOUNT.search(response.text)
    assert mount, "the front page must offer the graph mount over a non-empty record"
    for default in ('data-view="trend"', 'data-scale="3M"'):
        assert default in mount.group(0), (
            f"the front page ALWAYS opens at the ambient defaults regardless of "
            f"?view=/?scale= (A17/D-20), missing {default} on: {mount.group(0)}"
        )
    assert_state_delta(
        before=before,
        after=observable_state(actor),
        universe=SAVE_UNIVERSE,
        expected={
            "trail.trend_glance_shown_count": set_to(before["trail.trend_glance_shown_count"] + 1),
            "trail.home_graph_shown_this_week": set_to(
                before["trail.home_graph_shown_this_week"] + 1
            ),
        },
        strict=True,  # notably: deliberate study NEVER moves -- a deep link stays ambient
    )
