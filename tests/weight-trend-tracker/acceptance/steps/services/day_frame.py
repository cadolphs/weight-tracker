"""Client-authoritative day frame on READ surfaces (fix-device-day-reads)."""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from domain_types import TimeScale

from services._base import Service


class DayFrameService(Service):
    """Regression oracle contract (NON-TAUTOLOGICAL): every expected day derives
    from the phone's declared day (composition.device_day), never from
    fake_clock.today() -- at the 02:00-UTC skew moment the two diverge, and
    borrowing the server clock would make the oracle agree with the bug.
    """

    def evening_skew(self, utc_day: date, device_day: date) -> None:
        """02:00 UTC on `utc_day` while the phone still lives `device_day`."""
        assert utc_day == device_day + timedelta(days=1), (
            "skew frame: the UTC day must sit exactly one day ahead of the phone"
        )
        self.comp.fake_clock.set_small_hours_utc(utc_day)
        self.comp.clock.set_device_day(device_day)

    def _device_day(self) -> date:
        day = self.comp.device_day
        assert day is not None, "day-frame scenarios must declare the phone's day"
        return day

    # -- journey moves (the phone always claims its own day, as graph.html does) ---

    def open_history(self, scale: TimeScale) -> Any:
        return self.comp.actor().get(
            "/entries", params={"scale": scale.value, "today": self._device_day().isoformat()}
        )

    def open_trend(self, scale: TimeScale, ctx: SimpleNamespace) -> None:
        resp = self.comp.actor().get(
            "/trend", params={"scale": scale.value, "today": self._device_day().isoformat()}
        )
        assert resp.status_code == 200, f"trend not available: {resp.status_code}"
        ctx.trend = [(p["date"], p["trend_kg"]) for p in resp.json()["points"]]

    def ask_with_claimed_day(self, lens: str, claimed_day: str) -> Any:
        path = {"raw": "/entries", "trend": "/trend"}[lens]
        return self.comp.actor().get(
            path, params={"scale": TimeScale.ONE_WEEK.value, "today": claimed_day}
        )

    # -- outcome assertions ---------------------------------------------------------

    def assert_anchor_names(self, ctx: SimpleNamespace, day: date, kg: float) -> None:
        assert day == self._device_day() - timedelta(days=1), (
            "scenario frame: the named day must be the phone's own yesterday"
        )
        shown = self.comp.screen.shown_yesterday_kg(ctx)
        assert shown == kg, (
            f"at the skew moment the yesterday anchor must name {day}'s {kg:.1f} kg "
            f"(the phone's yesterday), but the screen shows {shown} -- "
            "the server clock framed the day"
        )

    def assert_trend_spans_exactly(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        expected = [
            (start + timedelta(days=offset)).isoformat() for offset in range((end - start).days + 1)
        ]
        days = sorted(day for day, _ in ctx.trend)
        assert days == expected, (
            f"the 1W trend must span exactly {start}..{end} in the phone's frame, got "
            f"{days[0] if days else '-'}..{days[-1] if days else '-'} ({len(days)} days)"
        )

    def assert_garbled_day_refused(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 400, (
            "a garbled day claim must be turned away with 400 (C6: parse totally, "
            f"never a silent ignore, never a 500), got {ctx.response.status_code}"
        )
