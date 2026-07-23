# RED Classification — home-trend-display (DISTILL fail-for-right-reason gate)

Date: 2026-07-23 · Command: `RED_GATE_ALL=1 uv run pytest tests/weight-trend-tracker/acceptance/steps/test_milestone_6.py tests/weight-trend-tracker/acceptance/properties/test_glance_properties.py`
(RED_GATE_ALL runs @pending scenarios too; the committed default runs only the glance
walking skeleton, rest skipped one-at-a-time). Result: **26 failed, 0 errors, 0 skipped**.
Prior-feature regression: `uv run pytest tests/` excluding the two new modules = **86 passed**;
full-suite collection clean (**112 collected, 0 errors**).

## Verdict: ALL 26 tests are RED for the right reason — `MISSING_FUNCTIONALITY`

Every failure is an `AssertionError`, none reaches a KeyError/TypeError/ImportError.
Presence-first assertion structure was used wherever a missing dict key or missing HTML
element could otherwise raise a non-assertion error (glance element regex, `"glance"`
save-response key, `trend_glance_shown_count` stats key).

| Scenario / property | Failing assertion (site) | Classification |
|---|---|---|
| The morning verdict arrives with the log and survives the save (WS, **enabled**) | glance line absent on `/` (composition.py `_shown_line`) | MISSING_FUNCTIONALITY |
| Where-am-I and which-way are answered in one glance | glance line absent on `/` | MISSING_FUNCTIONALITY |
| A sushi-morning spike is defused at the moment of logging | glance line absent (Given anchor) | MISSING_FUNCTIONALITY |
| Every direction is information, never judgment [falling ↓] | glance line absent | MISSING_FUNCTIONALITY |
| Every direction is information, never judgment [rising ↑] | glance line absent | MISSING_FUNCTIONALITY |
| Every direction is information, never judgment [steady →] | glance line absent | MISSING_FUNCTIONALITY |
| Standing still is reported plainly | glance line absent | MISSING_FUNCTIONALITY |
| A young record holds its tongue [span 3 → held back] | glance line absent | MISSING_FUNCTIONALITY |
| A young record holds its tongue [span 6 → held back] | glance line absent | MISSING_FUNCTIONALITY |
| A young record holds its tongue [span 7 → shown] | glance line absent | MISSING_FUNCTIONALITY |
| A resting record still reports where its line ends | glance line absent | MISSING_FUNCTIONALITY |
| An empty record shows no trend line until the first save brings one | `trend_glance_shown_count` missing from /stats (presence-first, Given anchor) | MISSING_FUNCTIONALITY |
| The glance never taxes the entry | glance line absent (timing + focus asserts pass; the glance assert REDs) | MISSING_FUNCTIONALITY |
| A trend hiccup hides the glance, not the morning | glance line absent (healthy-render Given anchor, before the fault is injected) | MISSING_FUNCTIONALITY |
| A trend hiccup never blocks the save | glance line absent (Given anchor; `"glance"` save-key presence also REDs) | MISSING_FUNCTIONALITY |
| A rejected save leaves not even a glance behind | glance line absent (Given anchor) | MISSING_FUNCTIONALITY |
| The stats page still tells deliberate study from ambient glances | `trend_glance_shown_count` missing from /stats | MISSING_FUNCTIONALITY |
| 7 glance pure-core properties (`test_glance_properties.py`) | `core/glance.py::glance` scaffold `AssertionError: Not yet implemented -- RED scaffold` | MISSING_FUNCTIONALITY |
| 2 quantize/glyph properties | `core/glance.py::quantize_rate` / `rate_glyph` scaffold AssertionError | MISSING_FUNCTIONALITY |

- `IMPORT_ERROR` / `FIXTURE_BROKEN` / `SETUP_FAILURE`: **0** — collection clean; the
  Mandate-7 scaffold `src/weight_tracker/core/glance.py` (`__SCAFFOLD__ = True`)
  satisfies all imports.
- `WRONG_ASSERTION` / `OBSERVABLE_NOT_AT_PORT`: **0** — universes are port-exposed only
  (`record.entries`, `telemetry.entry_logged_count`, `telemetry.trend_view_opened_count`,
  `telemetry.trend_glance_shown_count` via WeightHistory + the KPI query surface).

## Notes for DELIVER (RED phase entry)

1. Default suite state: the glance walking skeleton is **enabled** (RED); the other 12
   scenario blocks are `@pending` (skipped). Unskip = remove `@pending` one-at-a-time.
2. **Deliberate design: several scenarios assert absences** (no line on empty record,
   no line on degradation, no glance on rejection) that would be vacuously green
   pre-implementation. Each carries a discriminating RED anchor — a chained Given
   ("the entry screen shows the trend at a glance" / "he has seen the entry screen
   without a trend line", which captures the glance universe and asserts the /stats
   key) — so every scenario is genuinely RED. Do NOT remove those Givens to "simplify".
3. The DELIVER-facing HTTP contract (glance element markup, save-response `glance`
   field semantics incl. null-on-degrade and absent-on-reject, `trend.glance.shown`
   event, `trend_glance_shown_count` stats key) is the executable spec in
   `tests/weight-trend-tracker/acceptance/steps/composition.py::GlanceService` docstring.
4. The fault-injection step ("the trend computation is failing") monkeypatches
   `weight_tracker.core.glance.glance` PLUS the rebinding sites
   (`weight_tracker.composition.glance`, `weight_tracker.web.routes.glance`,
   `raising=False`) and restarts the composition — the injected failure holds
   regardless of the crafter's import style. Keep the glance callable resolvable
   under at least one of those names.
5. The scaffold module is `src/weight_tracker/core/glance.py`. DESIGN leaves
   glance-in-`trend.py` vs own module as the crafter's call — if folded into
   `trend.py`, re-export `glance`, `quantize_rate`, `rate_glyph`, `GlanceSummary`
   from `core/glance.py` or update the imports (steps + properties) in the same step.
6. `@pending` → pytest marker via `conftest.pytest_collection_modifyitems`;
   `RED_GATE_ALL=1` is the gate/re-classification escape hatch only.
