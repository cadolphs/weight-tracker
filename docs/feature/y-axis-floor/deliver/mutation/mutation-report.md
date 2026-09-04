# Mutation report — y-axis-floor (per-feature strategy, scoped to modified files)

- **Tool**: cosmic-ray 8.4.3 via `uvx cosmic-ray` (local distributor); config/session in the
  session scratchpad (`cr-yaf.toml` / `cr-yaf.sqlite`, `cr-yaf.html` for the survivor diffs)
- **Scope**: feature delta via `git-filter` (branch = pre-feature HEAD `14a3d14`, the
  DISCUSS/DESIGN/DISTILL commit) over the feature's two Python production files at HEAD
  `643703f`. The filter reduced 562 candidate jobs to **261 executed** — all 237 in the new
  `core/axis.py` plus the 24 on `web/routes.py`'s changed lines (the `axis` import,
  `axis_range_wire`, and the two `y_range` keys on `/entries` and `/trend`).
  `static/graph.js` and `static/sw.js` (the engine consuming the served pair and the -v5
  shell cache) are JavaScript — outside cosmic-ray's mutable surface; their wiring is pinned
  textually by `test_axis_engine_wiring.py` and the paint is owed to dogfood (D-15).
- **Killers**: milestone-11 + the feature's two property suites —
  `uv run pytest -x -q -p no:cacheprovider tests/weight-trend-tracker/acceptance/steps/test_milestone_11.py tests/weight-trend-tracker/acceptance/properties/test_axis_range_properties.py tests/weight-trend-tracker/acceptance/properties/test_axis_engine_wiring.py`
  (35 tests, ~4 s green / ~1.6 s per killed mutant under `-x`; total exec wall time ~7 min).
  The draft config's adjacent suites (milestone-2/4/9) were dropped: they lifted the run to
  ~18.5 s per mutant for no extra reach — the routes delta is two keys beside series reads that
  milestone-11 already exercises through both lenses at every scale.
- **Post-run safety**: tree committed clean before the run; `git checkout -- src/ tests/` →
  `git status --porcelain src/ tests/` empty; full suite re-run green afterwards.

## Results

| Metric | Value |
|---|---|
| Jobs | 562 (301 skipped by git filter — outside the feature delta) |
| Executed | 261 (`core/axis.py` 237, `web/routes.py` 24) |
| Killed | 224 (`axis.py` 222, `routes.py` 2) |
| Surviving | 37 (`axis.py` 15, `routes.py` 22) |
| Equivalent mutants | 36 |
| Raw kill rate | 224/261 = **85.8% — PASS (>= 80%)** |
| **Effective kill rate (excluding equivalents), as run** | **224/225 = 99.6%** |
| **Effective kill rate after the survivor was closed** (see § Survivors closed) | **225/225 = 100%** |

Per file: `core/axis.py` 222/237 raw (93.7%), 222/223 effective as run, 223/223 after
closure; `web/routes.py` 2/24 raw, 2/2 effective — the 22 survivors there are all lazy
annotations (below), and the two live sites (`if axis is None` / `[axis.lo_kg, axis.hi_kg]`)
both died to milestone-11.

Pinned by the killers, among others: the empty-input `None` (both `not values` and its
negation), `min`/`max` selection and their swap, the floor-branch predicate and its `<` vs
`<=` boundary (span exactly 2.0 is ordinary — pinned row 7 and the feature's own scenario),
the midpoint `/ 2` (its `//` twin dies on odd sums), each `FLOOR_KG / 2` sign, the pad
fraction and both `± pad` signs, the `floor`/`ceil` pair and their `+eps` / `-eps` directions,
the two `/ lines_per_kg` un-scalings, the four rule constants (pinned by
`test_the_rule_constants_are_pinned_by_adr_012`), the `AxisRange(lo_kg=, hi_kg=)` field
order, and on the wire the `None` guard and the `[lo, hi]` pair shape.

## Equivalent mutants — 36

| Mutation | Count | Why equivalent |
|---|---|---|
| `AxisRange \| None` / `list[float] \| None` `BitOr` swaps on `axis.y_axis_range` (return), `routes.axis_range_wire` (parameter + return) | 33 (11 per site) | `from __future__ import annotations` — annotations are lazy strings, never evaluated at runtime. Same catalogued class as every prior run in this repository |
| `ReplaceBinaryOperator_Div_FloorDiv` on `FLOOR_KG / 2` (both sites, `_floor_band`) | 2 | `2.0 // 2 == 2.0 / 2 == 1.0` exactly; the constant is pinned at 2.0 by the properties suite, so `//` and `/` agree on every input. Would stop being equivalent only if `FLOOR_KG` became odd — and that change is itself caught |
| `ReplaceBinaryOperator_Div_FloorDiv` on `1 / GRID_KG` (`_snap_outward`) | 1 | `1 // 0.5 == 1 / 0.5 == 2.0` exactly; `GRID_KG` is pinned at 0.5. The same operator on the two un-scaling divisions (`... / lines_per_kg`) is NOT constant-exact and both of those died |

## Surviving non-equivalent mutants — 1 (a design-contract pin, not a behavioural defect)

| # | Mutation | Gap |
|---|---|---|
| 1 | `ReplaceTrueWithFalse` — `axis.py:30` `@dataclass(frozen=True)` → `frozen=False` | **Nothing pinned that an `AxisRange` is a value object.** Under the mutant the axis becomes mutable and, because `eq=True` with `frozen=False` sets `__hash__ = None`, unhashable — a core type that quietly stops being a value, against ADR-005's frozen-dataclass core. No shipped path mutates or hashes an axis, so no existing test could see it. |

## Survivors closed — the one, same session (this commit)

The gate passed at 85.8% raw / 99.6% effective without this work; the mutant was closed
because the immutability of the core's value types is the paradigm the project declares
(CLAUDE.md, ADR-005), and the pin is one property. Added to
`tests/weight-trend-tracker/acceptance/properties/test_axis_range_properties.py`:

| Test | Kills |
|---|---|
| `test_the_axis_is_an_immutable_value` — over `plotted_non_empty`: two equal reads hash alike, and assigning a bound raises `dataclasses.FrozenInstanceError` | #1 |

**No production change** — the pin went GREEN immediately on the shipped code.

By-hand kill verification (mutation applied to the working tree, run, reverted):

| # | Mutation | Result |
|---|---|---|
| 1 | `axis.py:30` `frozen=True` → `frozen=False` | **KILLED** — sole failure `test_the_axis_is_an_immutable_value` (1 failed, 16 passed in the properties file) |

Suite: 254 → **255 passed**. `git status --porcelain src/` empty afterwards.

## Verdict

**PASS — 224/261 = 85.8% raw, 224/225 = 99.6% effective as run, 225/225 = 100% after the
one survivor was closed.** Thirty-six argued equivalents (33 lazy annotations, 3
constant-exact floor divisions); zero open AT gaps; nothing routed to `nw-acceptance-designer`.
