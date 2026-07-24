# Evolution: calm-visual-theme (2026-07-23)

Presentation-only delta feature delivered 2026-07-23 in a single day through DISCUSS → DESIGN → DISTILL → DELIVER. **DEVOPS skipped** — audited and conditionally approved by Forge (`nw-platform-architect-reviewer`): no new ports/adapters/containers, no pipeline delta; the one operational risk (PWA app-shell cache staleness) was converted into a binding DELIVER condition instead (sw.js APP_SHELL + `-v2` cache bump, executed in step 01-01). Workspace preserved at `docs/feature/calm-visual-theme/`; architecture SSOT in `docs/product/architecture/` (brief.md + new ADR-007).

## Feature Summary and Business Context

**US-008 + US-009 — the tracker stops looking like a prototype.** The entry, door, and graph screens now wear a calm, minimal, system-font theme that follows `prefers-color-scheme` — dark at 06:45 in the dim bathroom, light in the afternoon — with WCAG-AA contrast in both schemes. Job `track-true-weight-trend`, new moment `js-5-quality` (emotional dimension: "the daily habit feels like using a finished product"), directly supporting KPI-4 (cancel the $30/month subscription without hesitation). Two slices: 01 shared theme + entry/door (US-008), 02 graph controls + scheme-reactive chart (US-009). **Zero behavior change** — DOM ids, form semantics, fetch flow, telemetry, and all milestone 1–6 acceptance tests untouched and green.

## Key Decisions

- **DISCUSS (D6–D9)**: D6 calm-minimal direction (user-locked; matches "single-purpose minimalism" persona value). D7 follow-system color scheme — explicitly falsifiable hypothesis: the 06:45 dim-bathroom case should land dark automatically; if dogfood mornings still land bright, revisit as dark-only or manual toggle. D8 all three screens (door rides slice 01 — same form idiom, avoids a scale-duplicate slice). D9 CSS mechanism deferred to DESIGN with requirement-level pins: ≤ 10 KB uncompressed, zero external requests, zero new entry-screen JS, progressive enhancement.
- **DESIGN (DDD-1..6, ADR-007)**: DDD-1 hand-written design-token stylesheet `web/static/theme.css` — Pico.css (~70–80 KB) and Simple.css (~12–13.5 KB with overrides) rejected on byte arithmetic. DDD-2 **CUBE-lite adopted** (user-requested CUBE CSS evaluation): Tokens → Global → Composition (one flow primitive) → Utility (*deliberately empty*) → Block (id/element-keyed, zero new classes) → Exception (`aria-pressed`/`hidden` attribute states); ≈ 0 byte overhead, no template class churn. DDD-3 chart theming: `renderChart` reads `--chart-*` via `getComputedStyle`; one `matchMedia` listener re-renders through the existing `showGraph`, preserving lens + scale (~8 lines JS, graph page only). DDD-4 palette pinned with hand-computed AA ratios as the G-4 contract. DDD-5 PWA alignment: manifest colors + theme.css into sw.js APP_SHELL. DDD-6 no port/adapter/container/C4/paradigm changes.
- **DISTILL**: the AT-side WCAG relative-luminance checker (pure Python, `domain_types.py`) is the authoritative G-4 instrument, pinned to required **ratios**, never hexes — one-hex-step nudges stay green (Q1/Q6). Missing theme.css = AssertionError RED, never BROKEN (tolerant client). Step-reuse 3.50× (63 invocations / 18 new decorators).

## Work Completed

4 roadmap steps, all RED→GREEN→COMMIT PASS (execution log 4/4; DES integrity exit 0):

- **01-01** walking skeleton: theme.css ships with the app shell + sw.js `-v2` bump + manifest colors (`f8d8f4f`)
- **01-02** door themed; morning flows provably invariant — save, rejection, wrong passphrase, entry speed (`8053a4b`)
- **01-03** theme contract guardrails green — contrast, dark parity, byte budget, degradation (`1602f57`)
- **02-01** graph themed from the single palette; scheme-reactive chart, pressed state beyond color (`4cafaf7`)

**Outcomes**: theme.css **3,394 bytes** final (2,859 after slice 01) vs 10,240-byte budget — 33% used. **18/18 contrast pairings** AT-verified across both schemes; tightest pair light `--chart-grid` at **3.30:1** (≥ 3:1 non-text floor). All **11 milestone-7 scenarios** green; full suite **123 passed, 0 skipped**. Zero behavior change: milestones 1–6 green unmodified.

## Quality Gates

| Gate | Outcome |
|---|---|
| Roadmap review | Approved — 11/11 scenarios mapped across 4 steps, 0 orphans, avg dimension score 9.38/10, all 3 mandates pass |
| Steps | 4/4 COMMIT PASS; complete DES traces; integrity exit 0 |
| Phase 3 refactor | Empty scope — CSS/template/manifest data only; no Python refactor warranted |
| Post-merge integration (3.5) | PASS — local-dev full suite 123/0 + live-server demo (uvicorn + curl, production env contract): door + entry + graph carry the theme link, theme.css 200 at 3,394 bytes with dark block, zero hard-coded chart hexes, save flow byte-identical. ci + production deferred to the pipeline on push |
| Adversarial review (Phase 4) | **APPROVED — zero findings** (0 blockers / 0 high / 0 low) |
| Mutation (Phase 5, per-feature) | **Scope nil — skip** justified: sole Python production diff across all 4 commits = two manifest color literals in `routes.py` (`PWA_MANIFEST`); zero logic, empty effective mutation universe. CSS/templates are outside mutation scope by tool definition |

## Wave Review Verdicts

| Reviewer | Wave | Verdict |
|---|---|---|
| Eclipse (`nw-product-owner-reviewer`) | DISCUSS | approved — 0 findings; DoR 9/9 |
| Architect (`nw-solution-architect-reviewer`) | DESIGN | approved — 0 findings; contrast arithmetic spot-checked |
| Forge (`nw-platform-architect-reviewer`) | DEVOPS (skip audit) | conditionally approved — skip justified; sw.js cache condition executed in 01-01; condition 1c (post-deploy cache-eviction check) outstanding below |
| Sentinel (`nw-acceptance-designer-reviewer`) | DISTILL | conditionally approved — 1 high (missing `@kpi` tag) fixed same session |
| Adversarial review | DELIVER | approved — zero findings |

## Outstanding Post-Ship Items

Tracked to closure in the weekly /stats review; DoD items 1, 6, 9 of the feature-delta remain open until these land:

1. **Live scheme-flip dogfood on the open graph** — TestClient cannot drive `matchMedia`; the AT asserts single-palette structure only. Verify on a real phone: open /graph, toggle OS dark mode, chart re-renders keeping lens + time scale (DISTILL dogfood note).
2. **Post-deploy sw.js `-v2` cache-eviction verification** (Forge condition 1c) — on the real phone after deploy: theme.css loads on first visit and the old `weight-tracker-shell-v1` cache is evicted; stale-shell clients are the one operational risk this feature carries.
3. **KPI-6 self-report** — finished-feel ≥ 4/5 after 7 dogfood mornings, recorded in iteration notes (single-user manual instrument; baseline entered as `pending-dogfood` in `kpi-contracts.yaml`).
4. **D7 hypothesis check** — does follow-system actually land dark at 06:45 in the bathroom? If mornings land bright, revisit as dark-only or a manual toggle (explicitly out of scope this feature).

## Lessons Learned

1. **A DEVOPS skip can still yield the feature's most important operational catch**: Forge's skip audit surfaced the PWA app-shell staleness risk and converted it into a binding same-commit condition (APP_SHELL + cache bump in 01-01) — auditing the skip was cheaper than the wave and caught what no AT could.
2. **Ratio-pinned (never hex-pinned) contrast oracles made palette tuning frictionless**: the DISTILL checker asserting WCAG ratios over whatever tokens the served asset declares let DELIVER nudge hexes freely — 18/18 pairings green without a single test edit.
3. **Presentation-only features legitimately produce empty refactor and mutation phases** — the honest evidence is the diff itself (two color literals of Python); documenting the nil scope beats running theater.

## References

- Workspace: `docs/feature/calm-visual-theme/` (feature-delta.md incl. full wave record + finalize record, slices/, deliver/{roadmap,execution-log}.json)
- Architecture SSOT: `docs/product/architecture/brief.md` (Component Inventory, calm-visual-theme paragraph), `adr-007-theming-mechanism.md`
- KPI contracts: `docs/product/kpi-contracts.yaml` (G-4/G-5 hard gates + measured baselines, KPI-6 pending-dogfood)
- Scenario SSOT: `tests/weight-trend-tracker/acceptance/milestone-7-calm-visual-theme.feature` (11 scenarios)
- Commit range: `f8d8f4f..4cafaf7` on main (steps 01-01, 01-02, 01-03, 02-01); deploy path = existing pipeline on push
