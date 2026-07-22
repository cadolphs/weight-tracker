# Mutation Report — weight-trend-tracker (per-feature strategy, scoped to modified files)

## Step 03-06 — five-second entry: PWA install, yesterday anchor, speed report (2026-07-22)

- **Tool**: cosmic-ray 8.4.3 (project venv, local distributor); config/session in session scratchpad
- **Scope**: step delta only via `git-filter` (branch = pre-step HEAD `118183c`) over `web/routes.py`, `shell/telemetry_store.py`, `composition.py` (template/JS/SVG assets are outside cosmic-ray's mutable surface)
- **Killers**: milestone-5 + milestone-4 + walking-skeleton acceptance steps
- **Post-run safety**: `git status` clean on `src/`; full suite re-verified GREEN (73 passed, 0 skipped)

### Results

| Metric | Value |
|---|---|
| Jobs | 139 (72 skipped by git filter — outside the step delta) |
| Executed | 67 |
| Killed | 29 |
| Surviving | 38 |
| Equivalent mutants | 11 |
| **Effective kill rate** | **29/56 = 51.8% — FAIL band, four underlying gaps (all test-side, see below)** |

Everything wired through the driving port was killed: the manifest route and its payload,
the yesterday-anchor lookup wiring, the speed-report wiring in `/stats`, the
`entry_ms_samples_since` query (name/ts filter, null-timing exclusion), and the
composition-root partial application.

### Equivalent mutants — 11

| Mutation | Why equivalent |
|---|---|
| `routes.py:98` `float \| None` annotation `BitOr` swaps (×11) | `from __future__ import annotations` — annotations never evaluated at runtime |

### Genuine survivors — 27 (four underlying gaps)

| Mutation | Finding |
|---|---|
| `routes.py:101` `entry.day == day` → `>=`/`<=`/`is not` in `weight_on` (×3) | The only yesterday-anchor AT holds exactly one entry (yesterday's), so any comparison that matches it survives. **AT gap; routed to nw-acceptance-designer**: yesterday anchor with today already logged AND older days present must still show yesterday's value. |
| `routes.py:110` empty-window speed literals (×2) | No AT pins the empty speed report (`sample_count: 0`, null median/p90) — /stats is only asserted with 7 samples or ignored. **AT gap; routed to nw-acceptance-designer.** |
| `routes.py:122-124` `_p90` internals: single-sample branch, `n=10`, `[-1]` (×10) | The speed AT asserts the DISTILL bounded-change contract (median ≤ p90 ≤ worst case), deliberately NOT an exact percentile method — the five-second threshold judgment is human/weekly, never a gate (DEVOPS H-003). Survivors inside the sandwich are allowed by contract; the single-sample branch (one timed save in the week) is unexercised. **Noted to nw-acceptance-designer** for a 1-sample-week scenario if the contract should pin it. |
| `routes.py:192,196` `/sw.js` route removed / `_static_dir / "sw.js"` Path-join mutated (×12) | Service-worker delivery is browser-only observable today; the install AT asserts the manifest, not the worker. Same class as the 03-01 `/static` survivors. **AT gap; routed to nw-acceptance-designer**: a `/sw.js` smoke assertion (200 + `Cache` usage marker) would retire all 12. |

### Assessment

- Raw 43.3% / effective 51.8% falls in the **FAIL band**, but the 27 genuine survivors
  collapse into four findings, none implementation-side: two unpinned surfaces scheduled
  for AT authorship (`weight_on` neighbours, empty speed shape), one contract-intentional
  looseness (`_p90` sandwich), one browser-only surface (`/sw.js` smoke). Per SLIM scope
  the crafter does not author ATs — back-pressure routed to `nw-acceptance-designer`.
- No mutation-test response refactor applies: unlike 03-05's duplicated calendar
  arithmetic, the surviving surface cannot be shrunk without removing required behavior
  (the `_p90` guard is forced by `statistics.quantiles` needing ≥2 samples; the `/sw.js`
  route is forced by root-scope service-worker rules).

---

## Step 03-05 — trend/raw toggle, default lens, engagement telemetry (2026-07-22)

- **Tool**: cosmic-ray 8.4.3 (uvx, local distributor); config/session in session scratchpad
- **Scope**: step delta only via `git-filter` (branch = pre-step HEAD) over `web/routes.py`, `shell/telemetry_store.py`, `composition.py`
- **Killers**: milestone-1 + milestone-4 + access-protection + walking-skeleton acceptance steps (34 tests, ~4 s)
- **Post-run safety**: `git status` clean on `src/`; full suite re-verified GREEN (67 passed, 5 skipped)

### Results (authoritative session: post-refactor delta)

| Metric | Value |
|---|---|
| Jobs | 72 (67 skipped by git filter — outside the step delta) |
| Executed | 5 |
| Killed | 2 |
| Surviving | 3 |
| Equivalent mutants | 1 |
| **Effective kill rate** | **2/4 = 50% — FAIL band, single underlying AT gap (see below)** |

Most delta lines (trend_view_opened emission, `view="trend"` default, template toggle,
composition wiring) generate NO cosmic-ray mutants — no mutable operators on those
lines; their behavior is pinned directly by the 4 unskipped scenarios (2 right-reason
failures + 2 deletion-tested production-driven passes at RED).

### Equivalent mutants — 1

| Mutation | Why equivalent |
|---|---|
| `telemetry_store.py:30` `row[0]` → `row[-1]` | the query selects a single `COUNT(*)` column; index 0 and -1 are the same cell |

### Genuine survivors — 2 (one underlying gap)

| Mutation | Finding |
|---|---|
| `routes.py:90` `AddNot` and `IsNot→Is` on `_kpi_week_start`'s None-narrow | Both collapse to "week starts today". No AT seeds a `trend_view_opened` event OLDER than the rolling 7-day window, so `trend_views_this_week` cannot be distinguished from "views today" or "views ever". **AT gap; routed to nw-acceptance-designer** (crafter does not author ATs): a scenario where a trend view opened >7 days ago must NOT count toward `trend_views_this_week`. |

### Mutation-test response (refactor retired 11 survivors)

The pre-refactor session (same filter base) executed 27 mutants: 13 killed, 14
surviving (2 equivalent + 12 genuine — ALL twelve were operator/number mutations of
duplicated calendar arithmetic in `_kpi_week_start`, surviving on the same week-boundary
gap). Response commit `118183c` delegates the week window to the core's single pinned
`window_start(TimeScale.ONE_WEEK, today)` rule (L3 duplication removal), shrinking the
mutable surface from 13 arithmetic mutants to 2 comparison mutants. The residual gap is
test-side, not implementation-side.

### AT-sensitivity observations (routed to nw-acceptance-designer)

- `assert_view_at`'s `data-scale="X"` check also matches the static scale-picker
  buttons; this step renamed the buttons to `data-window` (and the new lens toggle uses
  `data-lens`) so `#graph-page`'s `data-scale`/`data-view` stay the only contract-matching
  markup — restoring falsifiability. A stricter selector-based assertion would make the
  contract robust against future markup.
- Week-boundary gap above (`trend_views_this_week` unpinned for events outside the window).

---

## Step 03-03 — date-edge semantics (2026-07-22)

- **Tool**: cosmic-ray 8.4.3 (uvx, local distributor); config/session in session scratchpad
- **Scope**: `src/weight_tracker/core/validation.py` (step's `files_to_modify` core; `routes.py` already covered by the 03-01 run below; the step itself shipped zero new production lines — its 4 scenarios were production-driven passes, non-vacuity proven by 4 manual mutations, all killed)
- **Killers**: milestone-1 + milestone-3 acceptance steps + validation property suite (28 tests, ~2.6 s)
- **Post-run safety**: `git status` clean on `src/`+`tests/`; full suite re-verified GREEN (56 passed, 15 skipped)

### Results

| Metric | Value |
|---|---|
| Mutants | 122 |
| Killed | 74 |
| Surviving | 48 |
| Raw kill rate | 60.7% |
| Equivalent mutants | 46 |
| **Effective kill rate** | **74/76 = 97.4% — PASS (>= 80%)** |

### Equivalent mutants — 46

| Mutation | Count | Why equivalent |
|---|---|---|
| `\|` operator swaps in return-type annotations (`float \| Rejected`, `date \| Rejected`, `Decimal \| None`, `date \| None`) | 44 | `from __future__ import annotations` — annotations never evaluated at runtime |
| `raw.strip() == ""` → `<=` / `is` | 2 | all strings compare `>= ""` lexicographically; CPython interns the empty string |

### Genuine survivors — 2 (one underlying gap)

| Mutation | Finding |
|---|---|
| `_has_tenth_precision`: exponent threshold `-1` → `-2` (USub→Invert and NumberReplacer variants) | No AT pins a **two-decimal** weight (e.g. "82.45" must be BAD_PRECISION); the only finer-than-scale example anywhere is "81.234" (3 decimals). **AT gap; routed to nw-acceptance-designer** (crafter does not author ATs). Consistent with the 03-01 note "PRECISION_KG partially pinned". |

### Survivors retired by this step

The 03-01 report listed `types.py:80 MAX_DEVICE_SKEW_DAYS = 1` as a genuine survivor ("skew bound edge not fully pinned in active scenarios"). The 4 scenarios unskipped in 03-03 now kill it: manual mutations `= 0` and `= 2` each failed exactly their target scenario, and the BAD_DATE→FUTURE_DATE reason swap plus a doubled `entry.saved` event were also killed.

---

# Mutation Report — weight-trend-tracker, step 03-01 (per-feature strategy, scoped to modified files)

- **Date**: 2026-07-22
- **Tool**: cosmic-ray 8.4.6 (ephemeral venv, local distributor)
- **Scope**: implementation files modified by step 03-01 — `src/weight_tracker/core/types.py`, `src/weight_tracker/web/routes.py`
- **Test command (killers)**: acceptance steps for milestones 1–2, walking skeleton (+ access-protection for routes.py)
- **Post-run safety**: sources restored via `git checkout -- src/`; suite re-verified GREEN (11/11 milestone-2 instances)

## Results

| File | Mutants | Killed | Surviving | Raw kill rate |
|---|---|---|---|---|
| `core/types.py` | 86 | 65 | 21 | 75.6% |
| `web/routes.py` | 62 | 44 | 18 | 71.0% |
| **Total** | **148** | **109** | **39** | **73.6% (WARN band 70–80%)** |

## Surviving-mutant review

### Equivalent mutants (no observable behavior change) — 18

| Line | Mutation | Why equivalent |
|---|---|---|
| types.py:55 (×11) | `date \| None` annotation operator swaps | `from __future__ import annotations` — annotations never evaluated at runtime |
| types.py:57 | `is` → `==` on `TimeScale.ALL` | Enum member equality == identity |
| types.py:83/92/100/111 (×5) | `frozen=True` → `False` / decorator removed | Immutability is a design constraint, not observable port-to-port; no production code mutates domain values |
| routes.py:93 | `[0]` → `[-1]` on single-element list | Same element selected |

### Genuine survivors, in scope of step 03-01 — 14

| Line | Mutation | Finding |
|---|---|---|
| types.py:71 | upper bound of `start <= entry.day <= today` weakened | No AT stores a future-dated (device-skew) entry and views it at a bounded scale — the window's upper bound is unexercised. **AT gap; routed to nw-acceptance-designer** (crafter does not author ATs). |
| routes.py:157 | `@router.get("/graph")` removed | No active AT asserts the graph page yet — milestone-4/5 graph scenarios (`@pending`) will kill this when unskipped. Page shipped ahead of its asserting scenarios per roadmap. |
| routes.py:166, 169 (×13) | `/static` route removed / `_static_dir / asset_name` Path-join mutated | Vendored-asset serving unasserted by the AT suite (browser-only observable today). Killed once a graph-page scenario loads assets, or by a future adapter smoke test. |

### Genuine survivors, outside step 03-01's diff (pre-existing lines, prior steps' ownership) — 7

| Line | Mutation | Note |
|---|---|---|
| types.py:77 (×2) | `PRECISION_KG = 0.1` replaced | Precision boundary partially pinned by milestone-1 examples |
| types.py:80 | `MAX_DEVICE_SKEW_DAYS = 1` replaced | Skew bound edge not fully pinned in active scenarios |
| routes.py:100 (×2) | wrong-passphrase `401` → other codes | Asserting scenarios still `@pending` (access milestone) |
| routes.py:108 | `httponly=True` → `False` | Cookie attribute not asserted via TestClient |
| routes.py:114 | `@router.get("/")` removed | Entry-screen scenarios land with milestone-5 |

## Assessment

- Raw kill rate 73.6% falls in the **WARN (70–80%)** band → survivors reviewed and documented above; proceed with caution per gate policy.
- Excluding the 18 equivalent mutants: effective kill rate **109/130 = 83.8%** (≥ 80% project gate).
- Every mutant of the step's core windowing algebra that changes behavior observable through the driving port was killed: all 5 `SCALE_WINDOW_DAYS` values, the `- 1` inclusive-of-today offset, the `timedelta` subtraction, the ALL guard, and the lower window bound.
- The single in-scope logic gap (window upper bound) and the unasserted `/graph` + `/static` surface are **AT-authorship findings** — back-pressure flows to `nw-acceptance-designer` per SLIM scope; several are scheduled to be killed naturally by pending milestone-4/5 scenarios.

## Step 03-07 — schema-version rollback guard (DEVOPS pre-req 2a) (2026-07-22)

- **Tool**: cosmic-ray 8.4.3 (project venv, local distributor); config/session in session scratchpad
- **Scope**: `shell/entry_store.py` + `composition.py` (`git-filter` vs pre-step HEAD `edd9940` — 0 jobs skipped: both files fully in the mutable surface, so pre-existing lines were executed alongside the step delta)
- **Killers**: schema-guard integration tests + access-protection + walking-skeleton + milestone-1 + milestone-5 acceptance steps (`pytest -x`, 2.5 s/mutant)
- **Post-run safety**: `git checkout -- src/` → `git status` clean on `src/`; full suite re-verified GREEN (75 passed, 0 skipped)

### Results

| Metric | Value |
|---|---|
| Jobs executed | 151 |
| Killed | 80 |
| Surviving | 71 |
| Equivalent mutants | 31 |
| Environment-limited (macOS-unreachable) | 23 |
| **Step-delta kill rate** | **100% — every non-equivalent mutant in this step's new code was killed** |
| Whole-file effective (excl. equivalents) | 80/120 = 66.7% |
| Whole-file effective (excl. equivalents + env-limited) | 80/97 = **82.5% — PASS (≥ 80%)** |

Mutation-response applied during this run: `CODE_SCHEMA_VERSION 1→2` initially survived
because the rollback test stamped version 99; the test now stamps
`CURRENT_SCHEMA_VERSION + 1`, pinning the exact refusal boundary — mutant killed.

### Equivalent mutants — 31

| Mutation | Why equivalent |
|---|---|
| `str \| None` / `int \| None` annotation `BitOr` swaps (×22) | `from __future__ import annotations` — annotations never evaluated at runtime |
| `_db_schema_version` sentinel `0→-1`, `row[0]→row[-1]` (×4) | single-column result row; sentinel only compared against versions ≥ 1 |
| guard `>` → `!=` / `is not` (×2) | `db_version < CODE_SCHEMA_VERSION` is unreachable through the composition root — migrations run before the probe and always raise the DB to the code version |
| `continue→break` in `apply_migrations` + `_probe_all_or_refuse` (×2) | one migration in `_MIGRATIONS`; the only probe-less adapter (test FakeClock) is last in the wiring dict |
| `_entry_from_row` `entry_ms=row[1]` (×1) | `Entry.entry_ms` is never read through any port — speed stats query `entry_ms` directly via `telemetry_store` (latent: becomes a real gap if a future feature reads it) |

### Environment-limited — 23

All inside `_filesystem_type_of` (tmpfs guard): macOS has no `/proc/mounts`, so the
function returns `None` under every mutation locally. Linux-only surface; would need a
Linux CI mutation run (nightly candidate) to exercise.

### Genuine survivors — 17 (all on pre-existing lines, outside the step delta)

| Mutation | Finding |
|---|---|
| probe deep-failure checks: `integrity != "ok"`, `journal_mode != "wal"`, `synchronous != 2`, sentinel readback `!=`/`or`/`fetchone()[0]` mutants (×16) | The only probe-failure AT is the unwritable-home refusal; no test presents a corrupted DB, drifted pragmas, or a lying sentinel. **AT/integration gap on the pre-existing Earned-Trust surface; routed to nw-acceptance-designer** — a corrupted-DB-file integration fixture would retire the integrity/pragma family. |
| `replication_status` `exists()` negation (×1) | No test creates the litestream generations dir, so `/healthz` "active" branch is unasserted. **AT gap; routed to nw-acceptance-designer.** |
