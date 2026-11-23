"""Tier A acceptance composition -- the driver plus its typed services.

Three layers, each in its own module, so a change to one never moves the others:

    driver.py      the production app under test: actor, observer, universe
                   capture, restart, ADR-014's fault door, read-backs.
    pages.py       page READERS: each rendered surface parsed ONCE into a typed
                   frozen struct; every regex over rendered HTML lives there.
    oracles.py     expectations for SHIPPED rules, imported from the core (and
                   the shell's phrasing) -- never a second copy on the test side.
    services/      the twenty typed services the step files speak to: assertions
                   over page structs and oracle values (Mandate-12 SSOT; step
                   bodies delegate in <=2 statements).

This module only composes them: `TrackerComposition` IS the driver, wearing the
services as attributes, so `composition.<service>.<method>` keeps reading as it
always did.
"""

from __future__ import annotations

from pathlib import Path

from driver import SESSION_SIGNING_KEY, UNIVERSE, WRONG_PASSPHRASE, TrackerDriver
from fake_clock import FakeClock
from services import (
    AccessService,
    AxisService,
    ClockService,
    DatedEntryService,
    DayFrameService,
    GlanceService,
    GraphService,
    HealthService,
    HistoryRecordService,
    HistoryService,
    HomeGraphService,
    LoggingService,
    RecentListService,
    ScreenService,
    StatsService,
    StudyService,
    SystemService,
    ThemeService,
    TrendRowsService,
    TrendService,
)

__all__ = ["SESSION_SIGNING_KEY", "UNIVERSE", "WRONG_PASSPHRASE", "TrackerComposition"]


class TrackerComposition(TrackerDriver):
    """One production app instance per scenario, plus typed services over it."""

    def __init__(self, db_path: Path, fake_clock: FakeClock) -> None:
        super().__init__(db_path, fake_clock)
        self.access = AccessService(self)
        self.logging = LoggingService(self)
        self.history = HistoryService(self)
        self.trend = TrendService(self)
        self.graph = GraphService(self)
        self.screen = ScreenService(self)
        self.stats = StatsService(self)
        self.health = HealthService(self)
        self.system = SystemService(self)
        self.clock = ClockService(self)
        self.glance = GlanceService(self)
        self.theme = ThemeService(self)
        self.day_frame = DayFrameService(self)
        self.home_graph = HomeGraphService(self)
        self.recent_list = RecentListService(self)
        self.history_record = HistoryRecordService(self)
        self.study = StudyService(self)
        self.dated_entry = DatedEntryService(self)
        self.axis = AxisService(self)
        self.trend_rows = TrendRowsService(self)
