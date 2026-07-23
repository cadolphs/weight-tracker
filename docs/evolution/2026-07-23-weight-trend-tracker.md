# Evolution: weight-trend-tracker (2026-07-23)

Feature delivered 2026-07-22..23 through the full nWave cycle (DISCUSS → DESIGN → DEVOPS → DISTILL → DELIVER). Workspace preserved at `docs/feature/weight-trend-tracker/` (lean v3.14 single-file layout); architecture SSOT lives permanently in `docs/product/architecture/`, journeys in `docs/product/journeys/`.

## Feature Summary and Business Context

A single-purpose, single-user, mobile-first weight tracker: log today's weight in seconds, review raw history at selectable time scales, and see a trustworthy smoothed trend through daily noise — replacing a $30/month app whose only used feature took 30–45 s per entry.

- **Persona**: `clemens` (sole customer, user, and developer) — phone-first, half-awake at 06:45, metric units.
- **JTBD** (`track-true-weight-trend`): *When I step off the scale each morning, I want to capture my weight in seconds and see my true underlying trend, so I can judge real progress without being misled by daily fluctuations.*
- **Outcome KPIs**: KPI-1 entry speed (median ≤5 s, p90 ≤10 s, client-timed `entry_ms`); **KPI-2 North Star** — logging adherence ≥6/7 days over 4 consecutive weeks; KPI-3 trend-view opens ≥3/week; KPI-4 (lagging) cancel the $30/month subscription within 30 days of the trend shipping. Guardrails: zero lost entries, graph interactive ≤2 s, trend determinism.
- **Scope**: 6 stories (US-001..006), 1 bounded context, walking-skeleton-first, direct-to-production strategy (no staging; all data is production data from entry 1).

## Key Decisions

### DISCUSS (D1–D5)

D1 user-facing · D2 walking skeleton YES (greenfield) · D3 lightweight UX research · D4 JTBD proportionate · D5 lean density. Assumptions A1–A8 (range 30.0–250.0 kg, 0.1 precision, device-local day, edit-not-delete, no import); OQ-1..5 all resolved 2026-07-22 (passphrase protection; no old-app import — slice ordering freed; no export in v1; A5 and time scales confirmed).

### DESIGN (D-05–D-11) + ADR index

| # | Decision | ADR |
|---|---|---|
| D-05 | Modular monolith, ports-and-adapters, single deployable | brief.md |
| D-06 | Python/FastAPI on Fly.io (Option A); Cloudflare/D1 and Go/VPS rejected | ADR-001 |
| D-07 | Durability: SQLite WAL + `synchronous=FULL` + Litestream → R2; earned-trust startup probes refuse start on a lying substrate | ADR-002 |
| D-08 | Access: single passphrase, argon2id hash, signed HttpOnly 90-day cookie, rate-limited login | ADR-003 |
| D-09 | Trend: local-level Kalman + RTS smoother, daily grid, R=0.20, α=0.10, Huber δ=1.0, missing day = predict-only; smoothed display (retrospective revision intentional); full O(n) recompute per read | ADR-004 |
| D-10 | Paradigm: Functional Core / Imperative Shell; crafter = nw-functional-software-crafter | ADR-005 |
| D-11 | PWA: manifest + minimal service worker (app-shell cache only, no offline queueing) | ADR-001 |

### DEVOPS (Decisions 1–9)

Fly.io single machine · no orchestration · GitHub Actions · greenfield · minimal custom observability (structured logs + `/healthz` + UptimeRobot email + `/stats`) · recreate deploys with a rollback-first contract (image revert via Fly registry; data via Litestream PITR, continuously exercised by the weekly restore drill) · no continuous-learning infra · trunk-based · per-feature mutation testing (≥80% kill gate, local, not CI). Peer review (Forge): needs_revision cycle 1 addressed — C-001..003, H-001..005 fixed/dispositioned, M-001..004 documented.

### AT_GAP Adjudications (DELIVER-era, all test-side; zero production-behavior defects)

| # | Finding | Adjudication |
|---|---|---|
| AT_GAP-1 | Responsiveness oracle anchored the "1 kg visible" claim on `series[onset_day]` — a smoothed value RTS retrospectively revises; unattainable for ANY correct ADR-004 implementation (max attainable 0.6503 kg vs required 1.0) | Authoring defect. Fixed at DISTILL: endpoint compared against the fixed pre-onset plateau; within-7-days clause strengthened to a second rendering that fails an over-lagging smoother. ADR-004 constants untouched |
| AT_GAP-2 | Precision-threshold mutant (−1 → −2) survived — no AT rejected a two-decimal weight | Scenario converted to an outline with "81.234" + "82.45" boundary examples |
| AT_GAP-3 | `trend_views_this_week` 7-day cutoff unpinned — events older than a week not excluded by any oracle | New scenario: view logged, clock advanced 8 days, second view, count asserted = 1 |
| AT_GAP-4 | Milestone-5 gaps: yesterday-anchor only tested with one entry; empty speed report unpinned | Two new scenarios: neighbours-distinct yesterday anchor; honest-nulls empty speed report (`sample_count: 0`). Accepted residuals documented: `_p90` sandwich looseness (contract-intentional), `sw.js` browser-only caching |

## Work Completed

- **15 roadmap steps** across 3 phases, all RED→GREEN→COMMIT with complete DES traces (execution log: 15/15 COMMIT PASS, one intra-step GREEN retry at 01-03):
  - **Phase 01** — walking skeleton through the production composition root (01-01), pure validation core / 7 properties (01-02), Kalman+RTS trend core / 7 properties (01-03), deploy rail: Dockerfile + Litestream 0.3.13 supervisor, fly.toml, CI gates→deploy→smoke + weekly restore drill, local hooks, import-linter (01-04).
  - **Phase 02** — passphrase gate (02-01), 90-day session via injected clock + `/healthz` + probe refusal (02-02), inline validation (02-03), one-per-day persistence, restart durability, device-day (02-04).
  - **Phase 03** — raw graph with time scales (03-01), backfill/correct (03-02), date-edge/skew semantics (03-03), trend view (03-04), trend↔raw toggle + KPI-3 telemetry (03-05), five-second entry: PWA, yesterday anchor, speed report (03-06), schema-version rollback guard, DEVOPS pre-req 2a (03-07).
- **Test outcome**: 49/49 Gherkin scenarios green (75 acceptance instances incl. 14 PBT properties) + 8 integration tests = **83 passed, 0 skipped** at HEAD `cf6e199`. `@pending` discipline fully unwound. Static gates all green (ruff, ruff format, mypy --strict, import-linter core-pure, probe-presence hook).
- **Adversarial review (Phase 4)**: APPROVED after 1 revision — blocking defect D1 (`?scale=All` → 500) fixed (`bc1637a`) and verified.
- **Mutation verdict (Phase 5, per-feature, cosmic-ray)**: **PASS — 82.5% effective kill rate** (85/103 on the disposition basis: 13 equivalents + 22 accepted residuals excluded) on the closing full-file run over `routes.py` + `telemetry_store.py`. Step 03-07's step-delta kill rate was 100%; 03-03's core validation run hit 97.4%. The 18 genuine closing-run survivors collapse into 5 oracle-sized test-side findings (below).
- **Post-merge integration gate (3.5)**: PASS on `local-dev` + `ci-mirror-local`; all 6 stories demoed over real HTTP against a real server with the production env contract; production environment deferred to operator prerequisites.
- **DoD**: 7/9 PASS; items 6 (deployed to production URL) and 7 (same-day dogfood) BLOCKED on operator prerequisites — CI deploys on first push once present.

Commit range: `edd9940..cf6e199` — 15 Step-Id-trailed step commits plus refactor commits (`118183c`, `894633e`, `66a86a8`), the Phase 3 L1-L6 pass (`17e8377`), the review fix (`bc1637a`), and two DISTILL back-propagation commits (`910fe57`, `cf6e199`).

## Lessons Learned

1. **Oracles must never anchor on revisable rendered values** (AT_GAP-1). The smoothed-display decision (ADR-004) means RTS revises the recent past on every render; DISTILL applied that discipline to the gap oracles but missed it on the responsiveness oracle, producing an assertion no correct implementation could satisfy. It was caught by the crafter's independent oracle — an exact batch-MAP solve matching the implementation to 1e-13 proved the bound unattainable rather than the code wrong. Two lessons: (a) when the design says "the line is revisable," audit *every* oracle for anchoring, not just the obvious ones; (b) an independent second oracle is what turns "test fails" into "test is wrong, with proof."
2. **Per-feature mutation testing earned its keep as an oracle-strengthening engine**: survivors drove four DISTILL back-propagations (AT_GAP-1..4) and one production refactor (`118183c` collapsed 12 arithmetic survivors by delegating calendar math to the core's single pinned rule). The FAIL-band step results (03-05 at 50%, 03-06 at 51.8%) were correctly read as test-side findings routed to the acceptance designer, not as implementation churn — and the closing run confirmed the back-propagated oracles measurably killed their targets.
3. **The demo gate caught a real 500 the entire AT suite missed** (`GET /entries?scale=All`, wrong casing): test helpers normalized casing through the `TimeScale` enum before the request ever hit the route, so the hostile-raw-string surface was invisible to the suite. Hand-typed curl at the integration gate surfaced it; adversarial review judged it blocking; the fix landed with a dedicated integration test (`test_scale_param_robustness.py`). Lesson: convenience typing in test fixtures can silently shrink the tested input space — keep at least one raw-protocol path per query parameter.
4. **Runtime-enforced deployment invariants need roadmap slots**: DEVOPS pre-requisite 2a (schema-version rollback guard) is deployment-level behavior with no DISTILL scenario, so it fell through initial roadmap generation (see Issues). The crafter authoring the adapter integration test directly was the right patch; the class of "DEVOPS pre-req implemented by DELIVER" items should be swept into the roadmap explicitly next time.
5. **Equivalent-mutant patterns are now known**: `from __future__ import annotations` makes every annotation `BitOr` swap equivalent (77 mutants across runs); frozen-dataclass and enum-identity mutants likewise. A pre-baked exclusion list would cut future triage time substantially.

## Issues Encountered

- **Roadmap gap (Phase 3.5 discovery)**: DEVOPS Pre-Requisite 2a (schema-version rollback guard) was mandated in feature-delta but modeled by no DISTILL scenario, so the initial 14-step roadmap omitted it. Resolved by adding late step 03-07 (approved amendment); guard shipped with an adapter integration test pinning the exact refusal boundary (`CURRENT_SCHEMA_VERSION + 1`).
- **Residual test-side gaps (documented follow-ups, routed to nw-acceptance-designer)**:
  1. Probe deep-failure surface (16 survivors, pre-existing Earned-Trust lines): no test presents a corrupted DB, drifted pragmas, or a lying sentinel — a corrupted-DB-file integration fixture would retire the family. Plus the `/healthz` replication "active" branch (litestream generations dir never created in tests).
  2. `weight_on` `<=` slip: needs a record with an older entry but a gap at yesterday (must show NO reference).
  3. Week-boundary inclusion side: a view 2–6 days old must still count toward `trend_views_this_week`.
  4. Login response itself: wrong passphrase must return exactly 401; `Set-Cookie` must carry `HttpOnly`.
  5. `/static` smoke (`GET /static/uplot.iife.min.js` → 200, non-empty): one assertion retires 12 of the 18 genuine closing-run survivors.
- **Environment-limited mutation surface**: 23 mutants inside `_filesystem_type_of` (tmpfs guard) are unreachable on macOS (no `/proc/mounts`); a Linux CI mutation run is the nightly candidate if that surface should be exercised.
- **Tooling**: `nwave-ai outcomes register` mis-packaged schema.json (exit 1); outcome registry populated manually at `docs/product/outcomes/registry.yaml` (OUT-1..6) — re-register via CLI when fixed.
- **Minor upstream corrections absorbed in-wave**: 21 Jul 2026 is a Tuesday (DISCUSS Gherkin said Monday; corrected at DISTILL); window semantics pinned at DISTILL (last {7,30,91,182,365} days inclusive of today).

## Outstanding Operator Prerequisites (first deploy)

The code side of DoD is complete; deployment is self-gating (startup probes + smoke stage) once these one-time operator actions land:

1. **Fly.io**: create the app + 1 GB volume `data`; `fly secrets set PASSPHRASE_HASH SESSION_SIGNING_KEY REPLICA_URL LITESTREAM_ACCESS_KEY_ID LITESTREAM_SECRET_ACCESS_KEY` (generation/rotation procedures: `docs/product/architecture/secret-setup.md`).
2. **GitHub**: repository secrets `FLY_API_TOKEN`, `R2_REPLICA_URL`, `R2_READONLY_*` (restore drill).
3. **Git**: add a remote and push `main` (no remote configured at finalize time) — the first push triggers gates → deploy → smoke.
4. **Post-deploy**: same-day dogfood entry from the phone (DoD 7), UptimeRobot monitor on `/healthz`, weekly `/stats` review cadence, KPI-4 day-30 check after Slice 04 ships.

## References

- Workspace: `docs/feature/weight-trend-tracker/` (feature-delta.md, deliver/{roadmap,execution-log}.json, deliver/mutation/mutation-report.md, environments.yaml)
- Architecture SSOT: `docs/product/architecture/brief.md`, ADR-001..005, runbook-restore.md, secret-setup.md
- KPI contracts: `docs/product/kpi-contracts.yaml` · Outcomes: `docs/product/outcomes/registry.yaml`
- Commit range: `edd9940..cf6e199` (Step-Id trailers 01-01..03-07)
