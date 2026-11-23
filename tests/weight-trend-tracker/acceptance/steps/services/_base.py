"""What every service shares: the driver it speaks through, one-parse page
access, the timed open, and the /stats vocabulary.

Mandate-12: all assertion/business logic for steps lives in the services
(single source of truth); step bodies delegate in <=2 statements. A service is
assertions over typed page structs (`pages.py`) and shipped-rule oracles
(`oracles.py`); it drives the app only through the driver's actor/observer.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from pages import EntryScreen, HistoryPage, read_entry_screen, read_history_page

if TYPE_CHECKING:
    from composition import TrackerComposition

#: Browser-flavored navigation: what the phone sends when Clemens taps the icon.
BROWSER_HTML = {"accept": "text/html"}

#: /stats read surface. ADR-009 intent telemetry (DISTILL contract; Q2 resolved:
#: raw rolling-week event counts over the SAME week frame as
#: trend_views_this_week, no read-time session collapse). Deliberate =
#: trend.study.opened + trend.study.interaction; ambient = home.graph.shown.
STUDY_COUNT_KEY = "trend_study_this_week"
AMBIENT_COUNT_KEY = "home_graph_shown_this_week"
#: Glance deliveries (grammar: `trend.view.opened` -> trend_view_opened_count).
GLANCE_COUNT_KEY = "trend_glance_shown_count"
#: In-app repairs (KPI-8): backdated saves over the same rolling week frame.
REPAIR_COUNT_KEY = "backdated_saves_this_week"


def read_once[PageT](ctx: SimpleNamespace, reader: Callable[[Any], PageT]) -> PageT:
    """`ctx.response` parsed by `reader` exactly once: the struct is remembered on
    the ctx beside the response it came from, and forgotten when a step stores a
    new response."""
    remembered = getattr(ctx, "pages", None)
    if remembered is None or remembered[0] is not ctx.response:
        ctx.pages = (ctx.response, {})
    pages: dict[Any, Any] = ctx.pages[1]
    if reader not in pages:
        pages[reader] = reader(ctx.response)
    return pages[reader]


def timed(ctx: SimpleNamespace, request: Callable[[], Any]) -> Any:
    """One request with its wall-clock cost remembered as `ctx.elapsed_ms`."""
    started = time.monotonic()
    resp = request()
    ctx.elapsed_ms = (time.monotonic() - started) * 1000
    return resp


class Service:
    def __init__(self, comp: TrackerComposition) -> None:
        self.comp = comp

    def entry_screen(self, ctx: SimpleNamespace) -> EntryScreen:
        return read_once(ctx, read_entry_screen)

    def history_page(self, ctx: SimpleNamespace) -> HistoryPage:
        return read_once(ctx, read_history_page)

    def assert_opened_within(self, ctx: SimpleNamespace, budget_ms: int, what: str) -> None:
        assert ctx.response.status_code == 200
        assert ctx.elapsed_ms <= budget_ms, (
            f"{what} took {ctx.elapsed_ms:.0f} ms, budget {budget_ms} ms"
        )
