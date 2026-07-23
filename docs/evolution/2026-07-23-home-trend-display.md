# Evolution: home-trend-display (2026-07-23)

Small delta feature delivered 2026-07-23 in a single day through the full nWave cycle (DISCUSS → DESIGN → DISTILL → DELIVER; DEVOPS inherited — pipeline unchanged from `weight-trend-tracker`). Workspace preserved at `docs/feature/home-trend-display/` (lean v3.14 single-file layout); architecture SSOT in `docs/product/architecture/` (brief.md + new ADR-006).

## Feature Summary and Business Context

**US-007 — Glance where you stand while you log**: the entry screen now shows `Trend: 82.3 kg · ↓0.25 kg/week` beside the form, and the line refreshes in place from the save response. This relocates the product's core emotional payoff — "the sushi-morning spike barely moved the trend" — from two taps away on the graph page to the one screen used every logging morning, at zero navigation and zero entry-speed cost. Job `track-true-weight-trend`, new moment `js-4-glance` (appended to `jobs.yaml`; bridge, not a new job). One story, one slice, ~1 day — all substrate (TrendProjection, inline save flow, telemetry trail) existed.

## Key Decisions

- **DISCUSS**: D1 user-facing · D2 no walking skeleton (brownfield) · D3 lightweight UX delta · D4 JTBD bridge only · D5 lean density. New assumptions A9–A13 (0.1 kg value precision; 0.05 kg/week rate steps with ↓/↑/→ from the rounded sign; rate only at ≥7-day entry span; in-place refresh, degrade-to-absent; separate glance telemetry event). Content locked by user: trend weight + weekly rate.
- **D-12 (ADR-006)**: weekly rate = trailing-7-day endpoint difference of the smoothed series (`smoothed[-1] − smoothed[-8]` on the daily grid ending at the last entry day); visibility threshold = entry-based span ≥7 days; quantization `round(rate/0.05)*0.05` with round-half-even ties pinned. Rejected: LS slope (free parameter, sign can contradict visible movement); local-linear-trend state model (would supersede ADR-004). ADR-004 untouched.
- **D-13**: glance delivery = server-render on `GET /` (zero added I/O — reuses the entries already fetched) + `glance` field in the `POST /entries` response for in-place refresh. KPI-3 separation structural: the glance never touches `GET /trend`. Failure degrades to `glance = null` → absent line; saving never blocked.
- **D-14**: event `trend.glance.shown`, fired per delivery, no per-day dedup; KPI-5's per-calendar-day pairing computed at read time on /stats. `/stats` key `trend_glance_shown_count` uses the same rolling 7-day window as `trend_views_this_week` (reviewer-confirmed at DELIVER).

## Work Completed

4 roadmap steps, all RED→GREEN→COMMIT with complete DES traces (execution log 4/4; DES integrity exit 0):

- **01-01** pure glance core greens its 9-property suite (`ea9cba3`)
- **01-02** walking skeleton: render + save-refresh + telemetry (`03de8f9`)
- **01-03** render semantics: directions, sparse honesty, first appearance (`fb7dbcd`)
- **01-04** degrade-to-null, entry primacy, KPI separation (`a9da482`) + L3 refactor `_log_structured` (`8181842`)

**Test outcome**: 13/13 milestone-6 blocks green (17 instances) + 9/9 pure-core glance properties; full suite **112 passed, 0 skipped**.

## Quality Gates

| Gate | Outcome |
|---|---|
| Roadmap review | Approved — 13/13 blocks + 9/9 properties, 0 orphans |
| Steps | 4/4 COMMIT PASS; complete DES traces |
| Phase 3 refactor | 01-03 empty batch (nothing warranted); 01-04 L3 extraction |
| Post-merge integration (3.5) | PASS — local-dev full suite + live-server demo: `GET /` first HTML carried the glance line; save response carried the co-revised glance; `/stats` trend_views 0 vs glance_shown 16 (KPI-3 unpolluted). ci + production deferred to the pipeline on push |
| Adversarial review (Phase 4) | APPROVED — 0 blockers / 0 high / 1 low (stale facade comment, fixed at finalize); Testing Theater 7/7 clean; test budget 22/44. 01-02 AT-infra fixes adjudicated legitimate, no assertions weakened |
| Mutation (Phase 5, per-feature, cosmic-ray 8.4.3) | PASS — post-01-03 scope 107/107 effective kills (100%); post-01-04 delta scope 1/1 effective (11 runtime-inert annotation survivors documented equivalent). Zero genuine survivors — no AT gaps routed |

## KPI-5 and the KPI-3 Substitution Note

KPI-5 (glance presence ≥95% of logging days): instrumentation verified live 2026-07-23; **measured baseline 0% pre-ship** (trend only reachable via /graph). Guardrails intact: KPI-1 entry primacy (glance never focuses/delays input), KPI-3 counter structurally unpolluted. **Expected substitution**: deliberate trend-view opens (KPI-3) may now drop toward "study sessions only" — that is the glance working, not a regression; standing note for the weekly /stats review (recorded in `kpi-contracts.yaml`).

## Lessons Learned

1. **Verbatim-pinned upstream oracles produced a zero-defect DELIVER**: encoding ADR-006's exact expressions in the DISTILL oracles (quantization verbatim, boundary rows logging ON the boundary day, the resting-record D-12 discriminator) left no unpinned behavior — zero AT_GAPs, zero genuine mutation survivors, review with no high findings. The prior feature's retrospective countermeasures (feasibility-derived oracles, exhaustive anchoring audits) visibly paid off in this delta.
2. **Known equivalent-mutant classes triage fast**: all 46 survivors across both runs fell into the pre-catalogued families (`from __future__ import annotations` BitOr swaps, frozen-dataclass, post-guard sign checks) — the prior feature's exclusion-list lesson cut mutation triage to minutes.
3. **CLI defect persists**: `nwave-ai outcomes register` still exits 1 (mis-packaged schema.json); OUT-7 appended manually, `check-delta` green (exit 0, 0 collisions). Re-register via CLI when fixed upstream.

## References

- Workspace: `docs/feature/home-trend-display/` (feature-delta.md incl. full DELIVER section, deliver/{roadmap,execution-log}.json, deliver/mutation/mutation-report.md)
- Architecture SSOT: `docs/product/architecture/brief.md` (Domain Core + TrendProjection rows, glance-delivery note, Component Inventory), `adr-006-glance-rate-derivation.md`
- KPI contracts: `docs/product/kpi-contracts.yaml` (KPI-5, `trend.glance.shown`, baselines) · Outcomes: `docs/product/outcomes/registry.yaml` (OUT-7)
- Commit range: `ea9cba3..8181842` on main (Step-Id trailers 01-01..01-04); deploy path = existing pipeline on push
