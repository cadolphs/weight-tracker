# Evolution: graph-first-home (2026-07-24)

Medium delta feature (3 stories, 2 slices) delivered 2026-07-24 in a single day through DISCUSS → DESIGN → DISTILL → DELIVER (DEVOPS inherited — pipeline unchanged; Forge's platform audit converted its findings into three binding DELIVER conditions, all discharged in-flight). Workspace preserved at `docs/feature/graph-first-home/` (lean v3.14 single-file layout); architecture SSOT in `docs/product/architecture/` (brief.md + new ADR-008 and ADR-009).

## Feature Summary and Business Context

**US-010 + US-011 + US-012 — the whole progress picture becomes the front door.** The entry screen now opens on the trend curve itself — full `Trend|Raw` + `1W…ALL` controls above the untouched entry form — with the last-7 entries list below, and "History" leads to the combined page: full-control graph on top, the **complete numeric record** beneath it. Job `track-true-weight-trend`, deepening the **ambient orientation moment** (`js-4-glance`: the curve's shape, not just its endpoint, lands at the sink every morning) and sharpening the **deliberate judging moment** (`js-2-judge`: History is now the full-record study and audit surface). No new job-story moment — same job, same moments, richer delivery. The KPI story is structural: an ambient front-page trend render every morning would have inflated the deliberate-study counter ~7×, so KPI-3 was redefined (A19/ADR-009) and a new ambient-presence KPI-7 added, with purity pinned as a hard behavioral AC ("a log-only morning adds 0").

## Key Decisions

- **DISCUSS (D6–D9, user-locked; A14–A19)**: D6 entry primacy kept with the graph above the form — keypad covering the graph on open explicitly *accepted, not a failure*. D7 front-page graph carries the FULL controls of `/graph`. D8 History = combined full-history page (graph + complete list). D9 front-page recent list = last 7 entries, display-only. A14 glance line kept beside the curve; A17 per-surface lens/scale at Trend/3M defaults, no persistence; A18 last-7 *entries* (not days), missing days simply absent; A19 deliberate study = History opens + explicit lens/scale interactions on either surface. G-5's "0 new entry-screen scripts" clause flagged for conscious renegotiation, never silent deletion.
- **DESIGN (D-15–D-20, ADR-008/009)**: D-15 front-page graph = async fetch via shared **extracted** `graph.js` — one chart code path makes the lens/scale-parity AC true by construction (rejected: inline-embedded series, server-side SVG). D-16 intent telemetry route-level: `home.graph.shown` (ambient, KPI-7), `trend.study.opened` (History render), `trend.study.interaction` via closed-vocabulary beacon `POST /telemetry/trend-study`; the `trend.view.opened` **emission retired** — data reads become pure (rejected: `?ambient=` suppression flags, History-opens-only). D-17 History = extended `/graph`, complete list server-rendered from `all_entries()` independent of the chart window. D-18 last-7 + complete list via existing `all_entries()` + pure slicing — **zero port changes** (strongest form of "no write methods"). D-19 save refresh: `recent` response field + client refetch at current lens/scale, absent-never-stale. D-20 per-surface state; OQ-7/8/9 confirmed at DISCUSS defaults.
- **KPI-3 redefinition**: instrument switched 2026-07-24 from `trend.view.opened` (frozen-historical counter on /stats) to `trend.study.*` raw rolling-week counts (`trend_study_this_week`, Q2 — no session collapse). A further KPI-3 decline post-ship is an expected substitution, not a regression.
- **DISTILL**: 19 scenarios across milestone-8/9, zero production scaffolds needed (all RED anchors HTTP-observable absences — 18 MISSING_FUNCTIONALITY / 1 preserved-behavior GREEN / 0 BROKEN); executable markup/response/beacon contracts pinned for the crafter; the G-5 clause consciously amended ("every moving part on the morning screen is the tracker's own" — same-origin sanctioned script set), green before and after.

## Work Completed

7 roadmap steps + refactor pass, all 3-phase RED→GREEN→COMMIT (DES: 21/21 events, integrity exit 0):

- **01-01** shared graph engine extracted + front-page graph mount; sw.js APP_SHELL + `-v3` bump (Forge condition 1) (`15bc1e6`)
- **01-02** intent telemetry — ambient recorded, data reads pure; /stats frozen-historical label (Forge condition 2) (`5923768`)
- **01-03** deliberate-study beacon with closed vocabulary; fire-and-forget containment (Forge condition 3) (`766c6e6`)
- **01-04** last-7 recent entries list below the form (`8034639`) + PBT absence-oracle hardening (`2ed9b1e`)
- **01-05** save hands back the refreshed morning picture (`recent` field + in-place refresh) (`416e232`)
- **02-01** complete record beneath the History graph (`b9be06a`)
- **02-02** history guarantees green — feature scenarios complete (`c7fe18b`)
- **Refactor** L1-L6 pass over feature-modified files, 4 L2 extractions (`3971ec5`)

**Outcomes**: 19/19 feature scenarios green (13 milestone-8 + 6 milestone-9), zero `@pending`; full suite **165 passed, 0 skipped**; amended G-5 + redirected milestone-4/6 clauses green — no inherited AT silently broken. Production diff: 6 files (`routes.py`, new `graph.js`, `sw.js`, `theme.css`, `index.html`, `graph.html`); zero port changes, zero new dependencies, zero new external origins.

## Quality Gates

| Gate | Outcome |
|---|---|
| Roadmap review | Approved (1 review) — 19/19 scenarios mapped across 7 steps |
| Steps | 7/7 COMMIT PASS; complete DES traces (21/21 events); integrity exit 0 |
| Refactor | L1-L6 pass, 4 L2 extractions (`3971ec5`) |
| Post-merge integration | PASS — full suite 165 passed + production-composition Elevator Pitch demos (135-entry seed; KPI purity live: ambient renders added 0, one History open moved `trend_study_this_week` 2→3, `home_graph_shown_this_week` 2) |
| Adversarial review | **APPROVED — 0 blockers** |
| Mutation (per-feature, cosmic-ray) | **PASS — 41/46 = 89.1% effective** (≥80% gate); 12 argued equivalents, 2 tolerated (beacon 204 constant), 3 genuine survivors routed to `nw-acceptance-designer` (beacon append-degrade containment; mixed-intent week for the KPI-3 sum) — `deliver/mutation/mutation-report.md` |
| Final wave review gate (DISTILL) | Eclipse approved 0/0/0 · Architect approved 0/0/0 · Forge conditionally approved (3 conditions → all discharged in DELIVER 01-01/01-02/01-03) · Sentinel approved 0/0/1-low |

## Outstanding Post-Ship Items

1. **Push → deploy → same-day dogfood** (DoD items 5–9): commits are on main locally; the existing pipeline deploys on push; dogfood = a real morning entry on the graph-first front page + a real History-page audit on the phone.
2. **KPI verification on production /stats**: KPI-7 pairing accruing, KPI-3 purity on a real log-only morning, KPI-1/≤2 s guardrails with the graph present.
3. **AT-strength follow-ups routed to `nw-acceptance-designer`**: a killer for the beacon's append-degrade containment; a mixed-intent week (one History open + one tap) to pin the `trend_study_this_week` sum.
4. **Outcome-registry CLI re-check**: `nwave-ai outcomes check-delta` still blocked by the upstream mis-packaged schema.json (OUT-7 precedent); OUT-8/OUT-9 registered manually.
5. **D6 falsification watch**: slice-01 dogfood is the test of "a graph above the form doesn't tax the five-second entry" — revisit layout if mornings feel slower.

## Lessons Learned

1. **PBT absence oracles must be injective over the rendered grammar**: the 01-04 recent-list property asserted "absent dates appear nowhere" against the year-less row grammar (`Fri 24 Jul — 82.2 kg`), so Hypothesis found two *different* dates in different years rendering the same day-month text — a false counterexample against correct production code. Fix: constrain the strategy to a single year so text equality ⇔ date equality (`2ed9b1e`). When the display format drops information, either strengthen the oracle's parser or shrink the input domain to where the format is injective.
2. **The mutation run's mandatory restore (`git checkout -- src/ tests/`) assumes a clean tree — it wiped three test files carrying uncommitted DISTILL amendments** (the G-5 renegotiation and milestone-6 redirect), leaving milestone-7 RED at HEAD. The lost edits were recovered verbatim from the session transcript and byte-verified back; future runs must `git stash push -- tests/` (or commit) outstanding test edits BEFORE any mutation run. Recorded as a process rule in the mutation report.
3. **Preserved-behavior scenarios legitimately pass at RED**: the empty-record and stranger-beacon scenarios (both in 02-02) were green before their step's implementation — one guards behavior the front page already had, the other rides the AccessGate every route inherits. Documenting them as preserved-behavior guards (as the RED-gate classification did for 1 of 19) beats contriving artificial reds for behavior the system already delivers.

## References

- Workspace: `docs/feature/graph-first-home/` (feature-delta.md incl. full DELIVER section, slices/, deliver/{roadmap,execution-log}.json, deliver/mutation/mutation-report.md, distill/red-classification.md)
- Architecture SSOT: `docs/product/architecture/brief.md` (ADR index + Component Inventory, graph-first-home paragraph), `adr-008-front-page-graph-delivery.md`, `adr-009-intent-telemetry.md`
- KPI contracts: `docs/product/kpi-contracts.yaml` (events, KPI-3 redefinition, KPI-7, G-5 amendment note, measured baselines) · Outcomes: `docs/product/outcomes/registry.yaml` (OUT-8, OUT-9)
- Scenario SSOT: `tests/weight-trend-tracker/acceptance/milestone-8-graph-first-front-page.feature` (13) + `milestone-9-whole-record-history.feature` (6)
- Commit range: `15bc1e6..3971ec5` on main (steps 01-01…02-02 + refactor); deploy path = existing pipeline on push
