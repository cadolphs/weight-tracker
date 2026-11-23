"""Tier A acceptance driver -- the production composition root under test.

Pillar 3: the SUT is built EXCLUSIVELY via `weight_tracker.composition.build_app`
(production wiring). Real SQLite on tmp_path (prod pragmas); the ONLY fake is the
Clock (driven external / non-deterministic). Session-age checks in AccessGate are
judged against the injected clock (testability contract for the 90-day scenarios).

This module is the DRIVER layer and nothing else: it builds the app, hands out the
actor (the scenario's own session) and the observer (a second authed session used
only for read-back), captures the port-exposed universe (Mandate 8), restarts the
app over the same record, and owns ADR-014's one fault-injection door. It knows no
page grammar and no service; `composition.py` adds the typed services on top.

The HTTP surface contract (routes, request and response shapes, status codes) has ONE
source: the `build_app` docstring in `weight_tracker.composition`. Read it there; this
module restates none of it.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from argon2 import PasswordHasher
from domain_types import TEST_PASSPHRASE, TimeScale, parse_day
from fake_clock import FakeClock

from weight_tracker.composition import build_app
from weight_tracker.core.types import Entry, TrendPoint

#: The shared universe every mutating flow is judged over (Mandate 8):
#:     record.entries                  -- (iso_date, weight_kg) pairs via WeightHistory
#:     telemetry.entry_logged_count    -- via the KPI query surface
#:     telemetry.trend_view_opened_count
UNIVERSE = {
    "record.entries",
    "telemetry.entry_logged_count",
    "telemetry.trend_view_opened_count",
}

WRONG_PASSPHRASE = "not-the-passphrase"
SESSION_SIGNING_KEY = "test-session-signing-key"


class TrackerDriver:
    """One production app instance per scenario: build, drive, observe, restart."""

    def __init__(self, db_path: Path, fake_clock: FakeClock) -> None:
        self.db_path = db_path
        self.fake_clock = fake_clock
        self.device_day: date | None = None  # phone-local day override (timezone skew)
        self.passphrase_hash = PasswordHasher().hash(TEST_PASSPHRASE)
        self._app: Any = None
        #: ADR-014's one fault-injection door: the picture override handed to
        #: build_app. None = production wiring; a raising callable = a failing picture.
        self.picture_of: Any = None
        self._actor: Any = None
        self._observer: Any = None

    # -- composition root (lazy: nothing is built until first use) ----------------

    def _build(self) -> Any:
        if self._app is None:
            overrides = {} if self.picture_of is None else {"picture_of": self.picture_of}
            self._app = build_app(
                db_path=self.db_path,
                clock=self.fake_clock,
                passphrase_hash=self.passphrase_hash,
                session_signing_key=SESSION_SIGNING_KEY,
                **overrides,
            )
        return self._app

    def restart(self) -> None:
        """Recreate the app over the SAME record file (durability contract); the
        actor keeps its cookies, so an unlocked session survives the restart."""
        cookies = dict(self._actor.cookies) if self._actor is not None else {}
        self._app = None
        self._actor = None
        self._observer = None
        for name, value in cookies.items():
            self.actor().cookies.set(name, value)

    def break_picture(self) -> None:
        """The picture cannot be computed (ADR-014): rebuild the app through its own
        seam with a raising `picture_of`. No module attribute is touched -- the test
        crosses the interface the degrade boundary owns, so it holds whatever the
        crafter's import style."""

        def failing_picture(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("picture failed (injected fault)")

        self.picture_of = failing_picture
        self.restart()

    # -- sessions ------------------------------------------------------------------

    def actor(self) -> Any:
        from fastapi.testclient import TestClient

        if self._actor is None:
            self._actor = TestClient(self._build(), raise_server_exceptions=True)
        return self._actor

    def observer(self) -> Any:
        """Separate authed session used only for universe capture / read-back."""
        from fastapi.testclient import TestClient

        if self._observer is None:
            self._observer = TestClient(self._build(), raise_server_exceptions=True)
            resp = self._observer.post("/login", data={"passphrase": TEST_PASSPHRASE})
            assert resp.status_code in (200, 303), f"observer login failed: {resp.status_code}"
        return self._observer

    def stranger(self, *, raise_server_exceptions: bool = True) -> Any:
        """A fresh cookie-less client: what a locked visitor (or a health probe) sees."""
        from fastapi.testclient import TestClient

        return TestClient(self._build(), raise_server_exceptions=raise_server_exceptions)

    # -- the record as the observer reads it back ------------------------------------

    def capture_universe(self) -> dict[str, Any]:
        obs = self.observer()
        entries = obs.get("/entries", params={"scale": TimeScale.ALL.value}).json()["entries"]
        stats = obs.get("/stats").json()
        return {
            "record.entries": tuple((e["date"], e["weight_kg"]) for e in entries),
            "telemetry.entry_logged_count": stats["entry_logged_count"],
            "telemetry.trend_view_opened_count": stats["trend_view_opened_count"],
        }

    def served_stats(self) -> dict[str, Any]:
        return self.observer().get("/stats").json()

    def stored_entries(self) -> list[Entry]:
        """The whole record as `/entries?scale=ALL` serves it: newest first."""
        served = self.observer().get("/entries", params={"scale": TimeScale.ALL.value}).json()
        return [
            Entry(day=date.fromisoformat(e["date"]), weight_kg=e["weight_kg"])
            for e in served["entries"]
        ]

    def stored_weights(self) -> dict[str, float]:
        """The record as {iso_day: kg} -- the shape the entry screen's map speaks."""
        return {entry.day.isoformat(): entry.weight_kg for entry in self.stored_entries()}

    def served_series(self, scale: TimeScale = TimeScale.ALL) -> list[TrendPoint]:
        """The smoothed series as `/trend` serves it -- the chart's own line, read
        over the HTTP boundary by the observer (a pure read since ADR-009)."""
        resp = self.observer().get("/trend", params={"scale": scale.value})
        assert resp.status_code == 200, f"trend not available: {resp.status_code}"
        return [
            TrendPoint(day=date.fromisoformat(p["date"]), trend_kg=p["trend_kg"])
            for p in resp.json()["points"]
        ]

    # -- days ----------------------------------------------------------------------

    def today(self) -> date:
        """The phone's day when one is declared, else the server clock's."""
        return self.device_day or self.fake_clock.today()

    def resolve_day(self, spec: str) -> date:
        if spec == "today":
            return self.today()
        if spec == "yesterday":
            return self.today() - timedelta(days=1)
        return parse_day(spec)
