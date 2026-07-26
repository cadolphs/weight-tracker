# Mutation report — entry-date-picker (per-feature strategy, scoped to modified files)

- **Tool**: cosmic-ray 8.4.3 (local distributor); config/session in the session scratchpad
  (`cr-edp.toml` / `cr-edp.sqlite`)
- **Scope**: feature delta via `git-filter` (branch = pre-feature HEAD `b85b575`) over
  `src/weight_tracker/` at HEAD `3e3c616`. The filter reduced 1371 candidate jobs to
  **108 executed** — the feature's Python production diff only
  (`core/validation.py`, `web/routes.py`, `shell/telemetry_store.py`, `composition.py`).
  Templates / inline JS / CSS / `sw.js` are outside cosmic-ray's mutable surface.
- **Killers**: milestone-10 + the two adjacent shipped suites the delta touches
  (day-frame, milestone-5 readiness) + the five feature property suites + the KPI-8
  integration query —
  `uv run pytest -x -q tests/weight-trend-tracker/acceptance/steps/test_milestone_10.py tests/weight-trend-tracker/acceptance/steps/test_day_frame.py tests/weight-trend-tracker/acceptance/steps/test_milestone_5.py tests/weight-trend-tracker/acceptance/properties/test_day_frame_properties.py tests/weight-trend-tracker/acceptance/properties/test_date_row_bound_properties.py tests/weight-trend-tracker/acceptance/properties/test_prefill_map_properties.py tests/weight-trend-tracker/acceptance/properties/test_entry_hint_wiring.py tests/weight-trend-tracker/acceptance/properties/test_date_row_dress.py tests/weight-trend-tracker/integration/test_repair_count_query.py`
  (68 tests, ~5.3 s/mutant; total exec wall time ~9 min)
- **Post-run safety**: outstanding edits committed BEFORE the run (the graph-first-home
  process rule); `git checkout -- src/ tests/` → `git status` clean on both trees.

## Results

| Metric | Value |
|---|---|
| Jobs | 1371 (1263 skipped by git filter — outside the feature delta) |
| Executed | 108 |
| Killed | 83 |
| Surviving | 25 |
| Equivalent mutants | 22 |
| Raw kill rate | 83/108 = 76.9% |
| **Effective kill rate (excluding equivalents), as run** | **83/86 = 96.5% — PASS (>= 80%)** |
| **Effective kill rate after the survivors were closed** (see § Survivors closed) | **86/86 = 100%** |

Pinned by the killers, among others: the write-time classification branch and the
`entry_ms = None` withholding (ADR-011), the `"backdated"` payload stamp, the
`backdated_saves_since` payload predicate and its rolling-week boundary, the
whole-record `{iso: kg}` projection and its empty-record case, `date_row_earliest_day`
(the `min` bound and its one-year offset), `is_backdated`'s equality, the
`bounded_day_frame` clamp arithmetic on both sides, the `isinstance` type gate on the
device-day claim, and the `/stats` key.

## Equivalent mutants — 22

| Mutation | Count | Why equivalent |
|---|---|---|
| `date \| None` return-annotation `BitOr` swaps on `routes.date_row_earliest_day` and `validation.bounded_day_frame` | 22 (11 each) | `from __future__ import annotations` — annotations are lazy strings, never evaluated at runtime. Same catalogued class as the weight-trend-tracker, home-trend-display, fix-device-day-reads and graph-first-home runs |

## Surviving non-equivalent mutants — 3 (all AT-strength findings, none behavioural defects)

Routed follow-up: `nw-acceptance-designer`. None blocks the gate (96.5% >= 80%).

| # | Mutation | Gap |
|---|---|---|
| 1 | `ReplaceComparisonOperator_Is_IsNot` — `routes.py:189` `return server_utc_today if framed is None else framed` → `is not None` | **The phone's claimed day is never observed DISAGREEING with the server's UTC day on a save.** Every milestone-10 scenario passes `today` equal to the fake clock's day, and the two garbled-claim examples save a *past* date, which classifies as a repair either way. So a mutant that judges saves against server UTC instead of the phone's day is indistinguishable. Real risk it hides: a phone one timezone ahead saves for ITS today while the server is still on yesterday — ADR-011 says that is a morning, the mutant calls it a repair, and the morning loses its KPI-1 sample. **Missing scenario**: device claims `D+1` while the server is on `D`, save dated `D+1` ⇒ counted as a morning, `entry_ms` preserved, repair count unmoved. |
| 2 | `AddNot` — `routes.py:189` `not framed is None` | Semantically identical to #1 (same site, same inversion). One scenario closes both. |
| 3 | `ReplaceComparisonOperator_Gt_GtE` — `validation.py:56` `if parsed > _latest_plausible_day(...)` → `>=` | **No save is dated exactly at the forward skew boundary** (`server_utc_today + MAX_DEVICE_SKEW_DAYS`, i.e. +1 day). The mutant rejects that day as `FUTURE_DATE`; the shipped rule accepts it — that acceptance is exactly the "a phone one timezone ahead may already be in its new day" allowance the no-future rule is written around. `device-day-frame.feature` exercises the boundary on READS, not on saves. **Missing scenario**: a save dated `server_utc_today + 1` is accepted and stored; `server_utc_today + 2` is still rejected. |

Findings 1 and 3 are two views of the same untested axis: **the suite never puts the
device clock and the server clock on different days during a SAVE.** One scenario pair
covering the skew-ahead morning would kill all three mutants.

Per SLIM scope no tests were added by the crafter; the findings routed to
`nw-acceptance-designer`.

## Survivors closed — all three, same day (`0bd47f0`)

The gate passed at 96.5% without this work; the user chose to close the axis rather than
carry it as back-pressure, because it is the feature's own headline invariant (a
timezone-ahead morning must not be misfiled as a repair). `nw-acceptance-designer` added
three scenarios to `milestone-10-dated-entry.feature`, **test-side only — no production
change was needed, and all three went GREEN immediately**:

| Scenario | Tags | Kills |
|---|---|---|
| A morning from a phone already in tomorrow is still a morning | `@driving_port @kpi @US-013 @contract-shape:bounded-change` | #1, #2 |
| The day his phone has already reached is served | `@driving_port @US-013 @contract-shape:bounded-change` | #3 |
| The day beyond his phone's own stays closed | `@driving_port @error @kpi @US-013 @contract-shape:unbounded-preservation` | #3 |

**Zero new step definitions** — every Given/When/Then already existed, including
`his phone is already in {day}` (`steps_record.py:32`), the same `device_day` machinery
`test_day_frame.py` uses on reads. The divergence is composed at the HTTP boundary:
`composition.device_day` feeds the payload's `today` claim while `FakeClock` stays on the
Background's Fri 24 Jul — two independent inputs, never a client convention.

By-hand kill verification (mutation applied to the working tree, run, reverted):

| # | Mutation | Result |
|---|---|---|
| 1 | `routes.py:189` `framed is None` → `framed is not None` | **KILLED** — sole failure `test_a_morning_from_a_phone_already_in_tomorrow_is_still_a_morning` |
| 2 | `routes.py:189` → `not framed is None` | **KILLED** — same sole failure |
| 3 | `validation.py:56` `parsed >` → `parsed >=` | **KILLED** — 3 failures across all three new scenarios |

Suite: 216 → **219 passed**. `git status --porcelain src/` empty afterwards.

## Verdict

**PASS — 83/86 = 96.5% as run, 86/86 = 100% after the three survivors were closed.**
Twenty-two argued equivalents in the known lazy-annotation class; zero open AT gaps.
