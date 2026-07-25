"""The date row's DRESS and the shell that carries it (US-013/US-014, D-25,
ADR-007, DELIVER pre-requisites 3 and 4).

WHY-NEW-FILE: acceptance/properties/test_date_row_dress.py
  CLOSEST-EXISTING: acceptance/properties/test_entry_hint_wiring.py
  EXTENSION-COST: that module is pinned to ONE oracle -- the entry template's text --
    and its docstring promises exactly that ("as they SHIP inside the entry screen's
    single inline script"). The two guarantees here read two DIFFERENT shipped
    artifacts (the stylesheet and the service worker) and would force that module to
    re-open its subject, its imports and its promise to hold assertions about neither
    the hint's wording nor the submitted payload.
  PARALLEL-RATIONALE: a stylesheet block and a cache-name constant have a different
    failure mode from script wiring -- they break SILENTLY and only for a user whose
    morning is offline or whose thumb is already on the field -- so they are owed a
    file whose docstring names the two silent breakages and can be read on its own
    when either regresses.

WHAT THESE PINS PROVE, AND WHAT THEY DO NOT
-------------------------------------------
They prove the two guarantees THIS step adds are present in what ships:

  1. the one hint line reserves its height permanently, so the mid-session state
     change (D-24: anchor -> "Editing ..." -> "No entry for ... yet") cannot move
     the weight field under a thumb that is already resting on it (D-25 no-reflow);
  2. the app-shell cache name has MOVED, so an offline open reinstalls the worker
     instead of serving the pre-date-row entry screen from `weight-tracker-shell-v3`.

They do NOT measure pixels. No browser lays this stylesheet out in this repository
(no package.json, no driver, G-5 forbids gaining one for a dress), so "the form did
not jump" is owed to a browser and is discharged at dogfood -- exactly as for the
date row's own `value`/`max` framing (client-paint precedent D-15). What is
falsifiable here is that the RESERVING RULE and the MOVED NAME ship at all.

The AA-contrast half of the date row's dress is DELIBERATELY not restated: the
milestone-7 G-4 scenarios already prove `--text`/`--bg` and `--text-muted`/`--bg`
clear 4.5:1 in BOTH schemes, over the served asset, with WCAG arithmetic. That gate
covers this row exactly as long as the new blocks borrow those tokens and name no
ink of their own -- which is what `test_the_new_blocks_name_no_ink_of_their_own`
pins here, turning the existing gate into this row's gate too.

Oracle: the files the shipped routes serve from (`routes._static_dir`), the same
directory `/static/theme.css` and `/sw.js` answer out of. That DELIVERY is gated
separately by the milestone-7 and access-protection scenarios; this module reads the
artifact whose delivery those scenarios already prove.

Contract shape: pure-function (return-only reads of two shipped files); universe
empty -- no state-delta matcher applies (documented bypass: pure-function /
no-side-effect code).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import weight_tracker.web.routes as routes

pytestmark = [pytest.mark.us_013]

THEME = (Path(routes._static_dir) / "theme.css").read_text(encoding="utf-8")
SERVICE_WORKER = (Path(routes._static_dir) / "sw.js").read_text(encoding="utf-8")

#: The app shell as it stands: this step adds NO asset, so the list may not move.
APP_SHELL_ENTRIES = (
    "/",
    "/static/uplot.iife.min.js",
    "/static/uplot.min.css",
    "/static/graph.js",
    "/static/theme.css",
)


def block(selector: str) -> str:
    """The declarations of the one rule keyed on `selector`, or a failed assertion."""
    found = re.search(rf"(?m)^{re.escape(selector)}\s*\{{(.*?)\}}", THEME, re.DOTALL)
    assert found, f"the theme must carry a block rule for {selector}"
    return found.group(1)


# ------------------------------------------------- the line that holds its place


def test_the_one_hint_line_reserves_its_height_permanently():
    """The old anchor appeared and vanished BEFORE first paint only. The one line
    now changes MID-SESSION -- every time a day is picked -- so an unreserved
    height would move the weight field under a thumb already resting on it.
    Technique and precedent: `#home-graph #chart { min-height: 320px }`."""
    assert re.search(r"min-height:", block("#entry-hint")), (
        "the one hint line must hold its height even while it is empty (D-25 "
        "no-reflow): without a reserved minimum, picking a day moves the form "
        "under the thumb mid-session"
    )


def test_the_yesterday_anchors_selector_was_renamed_and_not_duplicated():
    assert "#yesterday-reference" not in THEME, (
        "the retired anchor's selector is RENAMED to #entry-hint, never left "
        "beside it: a dead selector is how two hint dresses start"
    )


def test_the_date_row_is_dressed_in_its_own_right():
    assert re.search(r"(?m)^#entry-date\s*\{", THEME), (
        "the date row is dressed by the theme (criterion 1); its box comes from "
        "the shipped `input { min-height: 44px; width: 100% }`, so only what "
        "those tokens cannot give belongs here"
    )


def test_the_new_blocks_name_no_ink_of_their_own():
    """This is what makes the milestone-7 G-4 gate cover the date row: every colour
    the row wears is a contracted token, so proving the tokens clear 4.5:1 in both
    schemes proves the row does."""
    for selector in ("#entry-date", "#entry-hint"):
        assert not re.search(r"#[0-9a-fA-F]{3,6}\b", block(selector)), (
            f"{selector} must borrow the palette, never name a colour: an ink of "
            "its own escapes the G-4 contrast contract in one or both schemes"
        )


def test_the_dress_still_adds_no_class_and_no_outside_request():
    assert not re.search(r"(?m)^\s*\.[A-Za-z]", THEME), (
        "ADR-007: the stylesheet stays id/element-keyed with an empty utility "
        "layer -- zero classes, this step included"
    )
    for mark in ("@import", "url(//", "http://", "https://"):
        assert mark not in THEME, f"the theme reaches beyond no wall of its own ({mark})"


# ------------------------------------------------- the shell that carries the row


def test_the_app_shell_cache_moved_so_an_offline_open_is_not_served_yesterdays_screen():
    """No new asset ships -- but APP_SHELL pre-caches `/` ITSELF, and `/` is the
    page that just grew a date row. Fetch is network-first, so an online morning
    never notices; an OFFLINE open would keep being served the pre-date-row entry
    screen until the worker reinstalls, and only a new cache name reinstalls it."""
    named = re.search(r'const SHELL_CACHE = "([^"]+)";', SERVICE_WORKER)
    assert named, "the service worker must still name its app-shell cache"
    assert named.group(1) == "weight-tracker-shell-v4", (
        "the app-shell cache must move to weight-tracker-shell-v4 now that the "
        f"pre-cached `/` carries the date row, but it still names {named.group(1)!r}"
    )


def test_the_shell_itself_is_unchanged_because_this_step_ships_no_asset():
    declared = SERVICE_WORKER.split("APP_SHELL = [")[1].split("]")[0]
    listed = tuple(re.findall(r'"(/[^"]*)"', declared))
    assert listed == APP_SHELL_ENTRIES, (
        "the cache name moves; the shell does not. This step adds no asset and no "
        f"origin, so APP_SHELL must still list exactly {list(APP_SHELL_ENTRIES)}, "
        f"found {list(listed)}"
    )
