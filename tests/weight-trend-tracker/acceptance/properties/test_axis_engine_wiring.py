"""The served axis, as the shared graph engine SHIPS it to the chart, and the
shell cache that carries the engine (US-015, ADR-012 D-31, D-32, R-5).

WHY-NEW-FILE: acceptance/properties/test_axis_engine_wiring.py
  CLOSEST-EXISTING: acceptance/properties/test_date_row_dress.py
  EXTENSION-COST: that module reads the stylesheet and the service worker for
    ONE reason its docstring names -- the date row's dress and the cache move
    that row forced -- and is marked us_013; holding the graph engine's own
    wiring there would make a dress module the home of a chart-scale contract
    and re-open a shipped pin's subject to add a third artifact it never named.
  PARALLEL-RATIONALE: the subject here is a different shipped artifact
    (`graph.js`) with a different obligation -- it must CONSUME a served pair
    and COMPUTE nothing -- and its failure mode is a chart that quietly draws
    its own axis again; that deserves a file whose docstring says exactly which
    silence it guards against, and which can be read on its own when the engine
    regresses, while the -v5 pin sits beside it because the cache moved FOR the
    engine, not for the row.

WHAT THESE PINS PROVE, AND WHAT THEY DO NOT
-------------------------------------------
They prove the WIRING SHIPS: that the one engine driving both surfaces (ADR-008)
reads the server's `y_range` on both lenses, hands it to uPlot's `scales.y.range`
behind a shape guard (an array of exactly two finite numbers, lo < hi), and on
any other shape omits the override so uPlot's own range renders -- an imperfect
axis, never a blank chart (degrade-to-absent). They prove the engine carries NO
rule literal of its own (no standalone 2.0 / 0.5 / 0.1) and does no range
arithmetic: one definition (`core/axis.py`), one consumer (the engine), both
mounts. And they prove the app-shell cache MOVED to -v5 with the shell itself
unchanged, because `graph.js` is pre-cached and an offline open would otherwise
keep the pre-axis engine until the worker reinstalls (D-32).

They do NOT prove a browser EXECUTES it. This repository ships no JS harness --
no package.json, no driver -- and gains none for this step (G-2/G-5: zero new
fetches, scripts, origins, taps or telemetry). The paint is owed to a browser
and is discharged at dogfood (client-paint precedent D-15). The RULE itself is
property-tested over the pure core (test_axis_range_properties, 01-01) and pinned
at the served boundary by milestone-11; what is left over is genuinely the text
of the engine.

Oracle: the files the shipped routes serve from (`routes._static_dir`), read
once, as test_date_row_dress.py reads the service worker.

Contract shape: pure-function (return-only reads of two static files); universe
empty -- no state-delta matcher applies.
# bypass: pure-function / no-side-effect reads of two shipped files; no
# Hypothesis strategy ranges over a script's text.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import weight_tracker.web.routes as routes

pytestmark = [pytest.mark.us_015]

GRAPH_ENGINE = (Path(routes._static_dir) / "graph.js").read_text(encoding="utf-8")
SERVICE_WORKER = (Path(routes._static_dir) / "sw.js").read_text(encoding="utf-8")

#: The rule's own constants (D6 floor, D9 grid, D-28 pad) as decimal literals.
#: Word-bounded on both sides so `width: 2`, `height: 320`, `- 32`, `slice(0, 10)`
#: -- integers and integer pairs -- are never mistaken for a range constant.
RULE_LITERAL = re.compile(r"(?<![\w.])(?:2\.0|0\.5|0\.1)(?![\w.])")

#: The one guard predicate, from its `function` keyword to its closing brace at
#: the engine's two-space indent.
GUARD_BODY = re.compile(r"function isAxisPair\(yRange\) \{(.*?)\n  \}", re.DOTALL)

#: Each mount's renderChart call, from its series argument to the served pair.
RAW_MOUNT = re.compile(
    r"renderChart\(dailyGridSeries\(history\.entries\),.*?history\.y_range", re.DOTALL
)
TREND_MOUNT = re.compile(
    r"renderChart\(trendGridSeries\(trend\.points\),.*?trend\.y_range", re.DOTALL
)
#: The override, added only through the guard's ternary.
GUARDED_OVERRIDE = re.compile(r"isAxisPair\(yRange\)\s*\?\s*\{\s*scales:")
SCALE_RANGE = re.compile(r"scales:\s*\{\s*y:\s*\{\s*range:\s*\(\)\s*=>\s*yRange\s*\}\s*\}")

#: The app shell as it stands: this step changes a pre-cached file, not the list.
APP_SHELL_ENTRIES = (
    "/",
    "/static/uplot.iife.min.js",
    "/static/uplot.min.css",
    "/static/graph.js",
    "/static/theme.css",
)


def guard_body() -> str:
    found = GUARD_BODY.search(GRAPH_ENGINE)
    assert found, "the shape guard must be ONE named predicate, `isAxisPair(yRange)`, to be judged"
    return found.group(1)


# ---------------------------------------------------------------- the served pair reaches the chart


def test_the_engine_reads_the_served_axis_on_both_lenses():
    assert RAW_MOUNT.search(GRAPH_ENGINE), (
        "the Raw lens hands the pair the /entries read served (`history.y_range`) "
        "into renderChart -- the axis rides the very series it already fetches"
    )
    assert TREND_MOUNT.search(GRAPH_ENGINE), (
        "the Trend lens hands the pair the /trend read served (`trend.y_range`) "
        "into renderChart -- one rule, both lenses, parity by construction (ADR-008)"
    )
    assert GRAPH_ENGINE.count("y_range") == 2, (
        "`y_range` is read at exactly the two mounts and nowhere else: the engine "
        "consumes the pair, it never re-derives or reshapes it"
    )


def test_the_engine_hands_the_pair_to_uplot_as_the_y_scale_range():
    assert re.search(r"function renderChart\(data, lineOptionsFor, yRange\)", GRAPH_ENGINE), (
        "renderChart takes the served pair as its third argument (D-31)"
    )
    assert SCALE_RANGE.search(GRAPH_ENGINE), (
        "the pair is handed to uPlot UNTOUCHED as `scales: { y: { range: () => yRange } }` "
        "-- a function returning the served [min, max], the form uPlot 1.6.32 already honours"
    )


# ---------------------------------------------------------------- the guard, degrade-to-absent


def test_the_scale_override_sits_behind_a_shape_guard():
    body = guard_body()
    assert "Array.isArray(yRange)" in body, "absent / null / an object is not a pair"
    assert "yRange.length === 2" in body, "[77] and [1, 2, 3] are not a pair"
    assert "Number.isFinite" in body, '["a", "b"], NaN and Infinity are not bounds'
    assert re.search(r"yRange\[0\]\s*<\s*yRange\[1\]", body), (
        "[78.5, 76.0] is not an axis: lo must lie strictly below hi"
    )
    assert GUARDED_OVERRIDE.search(GRAPH_ENGINE), (
        "the override is added ONLY when the guard passes; otherwise the `scales` key "
        "is omitted and uPlot's own range renders -- an imperfect axis, never a blank chart"
    )


def test_the_engine_holds_no_rule_literal_and_does_no_range_arithmetic():
    """One definition, one consumer. The floor, the grid and the pad live in
    core/axis.py alone; an engine that knew them would be a second rule that
    could drift from the served one without any scenario noticing."""
    assert not RULE_LITERAL.search(GRAPH_ENGINE), (
        "graph.js carries no standalone 2.0 / 0.5 / 0.1: the rule's constants are "
        f"the core's alone (found {RULE_LITERAL.findall(GRAPH_ENGINE)})"
    )
    body = guard_body()
    assert not re.search(r"[-+*/]\s*\d|\d\s*[-+*/]|Math\.", body), (
        "the guard judges the pair's SHAPE and computes nothing: no arithmetic, no Math"
    )


# ---------------------------------------------------------------- the shell that carries the engine


def test_the_app_shell_cache_moved_because_the_pre_cached_engine_changed():
    """`graph.js` is in APP_SHELL. Fetch is network-first, so an online morning
    never notices; an OFFLINE open would keep being served the pre-axis engine
    until the worker reinstalls, and only a new cache name reinstalls it (D-32, R-5)."""
    named = re.search(r'const SHELL_CACHE = "([^"]+)";', SERVICE_WORKER)
    assert named, "the service worker must still name its app-shell cache"
    assert named.group(1) == "weight-tracker-shell-v5", (
        "the app-shell cache must move to weight-tracker-shell-v5 now that the "
        f"pre-cached graph.js applies the served axis, but it still names {named.group(1)!r}"
    )


def test_the_shell_itself_is_unchanged_because_this_step_ships_no_asset():
    declared = SERVICE_WORKER.split("APP_SHELL = [")[1].split("]")[0]
    listed = tuple(re.findall(r'"(/[^"]*)"', declared))
    assert listed == APP_SHELL_ENTRIES, (
        "the cache name moves; the shell does not. This step adds no asset, no "
        f"origin, no script, so APP_SHELL must still list exactly {list(APP_SHELL_ENTRIES)}, "
        f"found {list(listed)}"
    )
