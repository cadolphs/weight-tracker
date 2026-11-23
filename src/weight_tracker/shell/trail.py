"""The Trail's shell: one write entry point, one read (ADR-015).

Routes decide WHEN to emit (ADR-009) and call `mark`; the trail stamps the
event from the clock ONCE, here, rather than at every emission site, and hands
the row to the single driven adapter (the SQLite `events` table through
`TrailPort`). `report` is the one `/stats` read: every event in, the pure
`kpi_report` out, framed by the clock's UTC day.

Effects live here and only here; the derivation is `core/trail.py`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from weight_tracker.core.trail import EventName, kpi_report
from weight_tracker.ports import ClockPort, TrailPort


class Trail:  # probe-exempt: the trail over the port, not a driven adapter (ADR-015)
    """The trail as the routes see it: `mark` to append, `report` to read."""

    def __init__(self, *, store: TrailPort, clock: ClockPort) -> None:
        self._store = store
        self._clock = clock

    def mark(self, name: EventName, payload: Mapping[str, object] | None = None) -> None:
        """Append one event, stamped now. The name is the closed vocabulary's --
        free text cannot be marked; the payload is written as compact JSON in
        the order given, so the bytes match every row the routes wrote by hand."""
        self._store.append_event(
            ts=self._clock.now_utc().isoformat(),
            name=name.value,
            payload=json.dumps({} if payload is None else dict(payload)),
        )

    def report(self) -> dict[str, Any]:
        """The `/stats` report over the whole trail, as of the clock's UTC day."""
        return kpi_report(self._store.all_events(), today=self._clock.now_utc().date())
