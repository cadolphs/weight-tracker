# Mutation report — graph-first-home (per-feature strategy, scoped to modified files)

- **Tool**: cosmic-ray 8.4.3 (project venv, local distributor); config/session in session
  scratchpad (`cr-gfh.toml` / `cr-gfh.sqlite`)
- **Scope**: feature delta via `git-filter` (branch = pre-feature HEAD `653e671`) over
  `src/weight_tracker/web/routes.py` at HEAD `3971ec5` — the feature's only Python
  production diff (templates/JS/CSS are outside cosmic-ray's mutable surface)
- **Killers**: milestone-8 + milestone-9 acceptance steps + the three feature property
  suites —
  `pytest -x tests/weight-trend-tracker/acceptance/steps/test_milestone_8.py tests/weight-trend-tracker/acceptance/steps/test_milestone_9.py tests/weight-trend-tracker/acceptance/properties/test_recent_list_properties.py tests/weight-trend-tracker/acceptance/properties/test_save_recent_properties.py tests/weight-trend-tracker/acceptance/properties/test_study_beacon_properties.py`
  (31 tests, ~7.6 s/mutant — above the 5 s note threshold; dominated by Hypothesis
  examples in the three property suites; total exec wall time ~13 min for 58 mutants)
- **Post-run safety**: `git checkout -- src/ tests/` → `git status` clean on `src/`;
  full suite re-verified GREEN (165 passed). See the safety incident note below.

## Results

| Metric | Value |
|---|---|
| Jobs | 271 (213 skipped by git filter — outside the feature delta) |
| Executed | 58 |
| Killed | 41 |
| Surviving | 17 |
| Equivalent mutants | 12 |
| Raw kill rate | 41/58 = 70.7% |
| **Effective kill rate (excluding equivalents)** | **41/46 = 89.1% — PASS (>= 80%)** |

Pinned by the killers, among others: the `home.graph.shown` emission and its
entries-exist guard (`if entries:` flips killed by the empty-record scenario), the
`trend.study.opened` append on `/graph`, the closed-vocabulary gate in
`parse_study_signal` (shape check, per-field membership, string-type check — all
comparison and boolean-operator flips killed by the fail-closed 400 properties), the
7-entry `recent_head` slice (`RECENT_LIST_ENTRIES` 7→6/7→8 killed by the recent-list
PBT), the one row grammar (`entry_row_text` format literals), the shared
`entry_wire_pair` shape, the save response's `recent` hand-back, the `/stats`
rolling-week study and home-graph counters, and the beacon's 400-on-unknown-vocabulary
path.

## Equivalent mutants — 12

| Mutation | Count | Why equivalent |
|---|---|---|
| `dict[str, str] \| None` return-annotation `BitOr` swaps on `parse_study_signal` (routes.py:90) | 11 | `from __future__ import annotations` — annotations are lazy strings, never evaluated at runtime (same class as the home-trend-display and fix-device-day-reads runs) |
| `STUDY_VALUES = frozenset(lens…) \| frozenset(scale…)` `\|`→`^` (routes.py:80) | 1 | Lens tokens `{"trend","raw"}` and scale tokens `{"1W","1M","3M","6M","1Y","ALL"}` are provably disjoint, and for disjoint sets symmetric difference ≡ union. The sibling operators at the same site (`&`, `-`, arithmetic) were all KILLED, confirming the union itself is behaviorally pinned |

## Surviving non-equivalent mutants — 5

### Tolerated — 2

| Mutation | Why tolerated |
|---|---|
| 2 × `NumberReplacer` routes.py:556 — beacon `Response(status_code=204)` → 203/205 | The AT contract (ADR-009 fire-and-forget) pins "answers 2xx, never 500"; the beacon property asserts `200 <= status < 300`. Killing requires pinning the exact 204, i.e. testing implementation detail (same disposition as `RECENT_ANCHOR_ENTRIES` in the fix-device-day-reads run) |

### Genuine — 3 (routed follow-up: `nw-acceptance-designer`, AT-strength findings)

| Mutation | Gap |
|---|---|
| `ExceptionReplacer` routes.py:554 — `except Exception as failure:` around the beacon's `store.append_event` swallow | No killer exercises a FAILING append on the study beacon. The Forge-condition-3 containment ("a failing append is swallowed with a structured `trend.study.append_degraded` log; the beacon still answers 2xx, never 500") is unpinned — the milestone-8 series-failure scenarios cover the glance/series degrade, not the beacon append degrade |
| `Add_BitOr` + `Add_BitXor` routes.py:587 — `trend_study_this_week = opened + interaction` | No scenario has BOTH `trend.study.opened` ≥ 1 AND `trend.study.interaction` ≥ 1 in the same week (milestone-9's count scenario is 2 + 0; milestone-8's tap scenario is 0 + 2), so `+`, `\|` and `^` are indistinguishable in the current test universe. A week mixing one History open with one tap (1 + 1 = 2, but 1 \| 1 = 1, 1 ^ 1 = 0) would kill both — a real KPI-3 undercount risk |

Per SLIM scope, no tests were added by the crafter; both findings route to
`nw-acceptance-designer` as AT-gap back-pressure. Neither blocks the gate (89.1% ≥ 80%).

## Verdict

**PASS — effective kill rate 41/46 = 89.1% (>= 80% gate).** Two genuine AT-strength
findings routed to `nw-acceptance-designer` (beacon append-degrade containment;
mixed-intent week for the KPI-3 sum); two tolerated status-code constants; twelve
argued equivalents.

## Safety incident — post-run restore vs uncommitted DISTILL edits (resolved)

The mandated post-run `git checkout -- src/ tests/` also reverted three test files that
carried UNCOMMITTED DISTILL amendments from the deliver session (the G-5
"moving parts" clause renegotiation and the milestone-6 AT-contract note):
`tests/weight-trend-tracker/acceptance/steps/steps_theme.py`,
`tests/weight-trend-tracker/acceptance/milestone-7-calm-visual-theme.feature`,
`tests/weight-trend-tracker/acceptance/milestone-6-home-trend-glance.feature` — leaving
milestone-7 RED at HEAD (HEAD's `steps_theme.py` called a `ThemeService` method the
renegotiation had replaced). The four lost Edit operations were recovered verbatim from
the deliver-session transcript, replayed onto bases byte-verified against the session's
pre-edit checkpoints, and the full suite re-verified at 165 passed — the working tree
is byte-for-byte back to its pre-mutation-run state. Process recommendation: commit (or
`git stash push -- tests/`) outstanding test edits BEFORE any mutation run, since the
mandatory restore step assumes `src/` and `tests/` are clean at HEAD.
