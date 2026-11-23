"""Typed services: one per surface or feature, each a set of assertions over
typed page structs (`pages.py`) and shipped-rule oracles (`oracles.py`), driving
the app only through the driver. Method names are the step files' vocabulary."""

from __future__ import annotations

from services.axis import AxisService
from services.dated_entry import DatedEntryService
from services.day_frame import DayFrameService
from services.glance import GlanceService
from services.home import (
    HistoryRecordService,
    HomeGraphService,
    RecentListService,
    StudyService,
    TrendRowsService,
)
from services.theme import ThemeService
from services.tracker import (
    AccessService,
    ClockService,
    GraphService,
    HealthService,
    HistoryService,
    LoggingService,
    ScreenService,
    StatsService,
    SystemService,
    TrendService,
)

__all__ = [
    "AccessService",
    "AxisService",
    "ClockService",
    "DatedEntryService",
    "DayFrameService",
    "GlanceService",
    "GraphService",
    "HealthService",
    "HistoryRecordService",
    "HistoryService",
    "HomeGraphService",
    "LoggingService",
    "RecentListService",
    "ScreenService",
    "StatsService",
    "StudyService",
    "SystemService",
    "ThemeService",
    "TrendRowsService",
    "TrendService",
]
