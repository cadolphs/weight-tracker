# Evolution: numeric-trend-history (2026-09-09)

Small delta feature (1 story, 1 slice) delivered in a single day, 2026-09-09, through DISCUSS → DESIGN → DISTILL → DELIVER (DEVOPS inherited — pipeline unchanged, no infrastructure surface). Workspace preserved at `docs/feature/numeric-trend-history/` (lean single-file layout); architecture SSOT in `docs/product/architecture/` (brief.md + new ADR-013).

## Feature Summary and Business Context

**US-016 — the trend has a readable history.** The smoothed trend existed as a *number* exactly once — the glance line, for the most recent entry day — and as a *shape* everywhere else. "How much has the trend moved since mid-August?" is a subtraction of two numbers, and the product answered it by asking the user to read pixels off a curve whose y-axis the previous feature (US-015) had deliberately widened so that small movements look small. The two features are complements: the chart now refuses to exaggerate, so the numbers had to become available where the eye cannot resolve them.

Job `track-true-weight-trend`, moment `js-2-judge`, secondary `js-4-glance`. **No new job-story moment**: the job already names the outcome; the entries lists are an existing surface that gained the number they were always missing. Both lists — the front page's last seven and the History page's complete record — are now aligned `Date | Raw | Trend` tables reading the same smoothed series the chart plots, at each entry's own day.

The KPI story is structural again: **nothing is instrumented, because rendering a list is not intent** (ADR-009). KPI-10 (trend-readable-as-numbers, 100 % answered from a list within 10 s, 0 chart fallbacks over 7 mornings) is self-reported; the values are AT-pinned against the chart's own endpoint, so what dogfood measures is whether numbers actually beat the picture for this question.

## Key Decisions

- **DISCUSS (D6–D8 user-pinned before the wave opened; D9–D12, A32–A39)**: aligned columns rather than an inline row or a Raw/Trend toggle — hiding one number to read the other defeats the comparison. Both lists change together, because they share one row grammar and forking it is the specific failure to avoid. The value comes from the existing full-record smoothed series by day, derived never stored. A semantic `<table>`, because two columns of numbers under headings are tabular data. Retrospective revision after a backfill is *accepted and named*, so it is never mistaken for instability. Degrade to absent, never to stale or fake.
- **DESIGN (D-32–D-41, ADR-013)**: **D-32** the day→trend view is a pure core projection in `core/trend.py`, not a new module — unlike ADR-012's axis rule, a day-keyed view of the series *is* the series. **D-33** injected as a third read-only callable (ADR-006 precedent), which is what makes containment testable by fault injection. **D-34** degradation is one shell function returning an **empty mapping**, so the row builder carries no degrade branch at all — a miss is already an empty cell. **D-35** one `EntryRow` definition; the single-string `entry_row_text` retires with its grammar. **D-36** the `"Fri 24 Jul"` wording gets one definition in `core/types.py`, with the save confirmation's output byte-identical. **D-37** the trend reaches the wire on the save's `recent` hand-back **only**; `GET /entries` stays the raw lens's untouched read, because publishing smoothed values on the raw endpoint would give the chart two paths to one series and would run a full Kalman pass for a consumer that discards it. **D-38–D-41** table markup on the existing ids, theme rules on the same selectors, `SHELL_CACHE -v6`, nothing else moves.
- **DISTILL**: 12 scenarios on `milestone-12-trend-in-the-record.feature`, error-edge share 42 %. **Every expected trend value is re-derived from `GET /trend` at `ALL`** — the chart's own series over the HTTP boundary — which is what turns "one value per day across the glance, both lists and the chart" from a comment into a claim that fails at an assertion. Five shipped assertions were renegotiated in the open as intended AC deltas; the confirmation and hint lines were guarded as byte-identical.

## Work Completed

Two commits:

- **`95794e0`** waves 1–3: feature-delta, slice brief, ADR-013, SSOT back-propagation (jobs, persona, journey, brief), the 12-scenario feature file, the step module, the `TrendRowsService` oracle, the rewritten row-property suite and the new projection-property suite, and the five renegotiated assertions
- **`a38e8fa`** implementation: `trend_by_day`, `day_label`, `EntryRow` + the row builders + the degrade closure + the wire enrichment, composition wiring, both templates, `theme.css`, `sw.js`

**Outcomes**: 12/12 milestone-12 scenarios green; full suite **278 passed, 0 skipped** (baseline 255). Production diff: 8 files, +235/−51 across `src/`; zero port changes, zero new adapters, routes, assets, dependencies, external origins, probes, events or migrations.

## Quality Gates

| Gate | Outcome |
|---|---|
| Static | PASS — `ruff check`, `ruff format --check`, `mypy --strict` on `src/`, `lint-imports` (functional-core contract kept), AST probe-presence gate |
| Acceptance | PASS — 12/12 milestone-12; full suite 278 passed, 0 skipped |
| Properties | PASS — 12 row properties (incl. the positional-zip falsifier and the frozen-row guard) + 7 projection properties |
| Outcome collision check | PASS — `nwave-ai outcomes check-delta` exit 0 |
| Mutation (per-feature, cosmic-ray 8.4.3) | **PASS — 20/20 = 100 % effective**; raw 20/31. Eleven survivors are binary-operator mutants inside one `float | None` annotation, provably equivalent under `from __future__ import annotations`; the one genuine survivor (`frozen=True` on `EntryRow`) was closed test-side |
| Live render check | PASS — real composition root over a seeded 31-day declining record: the front page's seven rows, the History page's 31, and the glance line all agreeing on the same day's value |

## Outstanding Post-Ship Items

1. **Push → deploy → dogfood (DoD items 6, 7, 9)**: both commits plus this finalize are on `main` locally; the existing pipeline deploys on push. Dogfood = read the seven trend values on `/` over the real record and judge the week without opening the chart, then subtract two trend values a month apart on `/graph`. Confirm the `-v6` shell pickup (an offline open would otherwise keep serving the pre-column `/` out of `-v5`).
2. **Client-paint verification owed** (D-15 precedent): the in-browser repaint building `<tr>`/`<td>` from the hand-back, the rebuilt header after a *first* morning's save (the only path that constructs the table client-side), decimal alignment under `tabular-nums`, and no wrap at a 360 px viewport. A browser-less suite pins the markup and the theme rules; the pixels are owed to the phone.
3. **KPI-10 7-morning self-report** — recorded as `pending-dogfood` in `kpi-contracts.yaml`. This is also the second falsification pass on OQ-15: if a week of rows still reads frozen at two decimals, or a morning still ends in a tap through to `/graph`, `TREND_DECIMALS` retunes in one line.
4. **Persona SSOT staleness** (carried from y-axis-floor, still open): `personas/clemens.yaml` says "around 82 kg"; the record is ~77 kg.
5. **Exact-name cache pins** (carried from y-axis-floor, now demonstrated twice): two modules pin `SHELL_CACHE` by exact version, so every bump is a renegotiation by construction. This feature bumped it again and touched both pins again. Worth loosening to "moved past the previous name" the next time `sw.js` is touched.
6. **Outcome-registry CLI**: `check-delta` works, `outcomes register` still blocked by the upstream mis-packaged `schema.json`; OUT-13 registered manually.

## Lessons Learned

1. **The falsifier fired within minutes of the first real render, and it was worth writing down in advance.** DISCUSS pinned both columns at 0.1 kg and OQ-15 named its own disproof: *"if a week of rows reads as an identical number seven times while the curve visibly slopes, the default is wrong."* On the first render against a realistic declining month, that is exactly what happened — the Kalman filter is damped enough that a week moves the smoothed value ~0.05 kg, so every front-page row printed `77.5`. The default was retuned to 0.01 kg before the feature shipped rather than after a week of dogfood. Writing the falsifier as a *concrete observable* ("seven identical rows while the curve slopes") rather than as a worry ("precision might be wrong") is what made it recognisable the moment it appeared.
2. **Asymmetric precision is the honest choice when only one of two numbers was measured.** The instinct — and the pinned decision — was that every weight on a screen should read at the same precision. But the scale measured the raw weight to a tenth and never measured a hundredth, while the trend is derived and has real resolution below 0.1. Rendering both at 0.1 hid real movement; rendering both at 0.01 would invent a raw digit. The rule that survived is per-column and stated as two named constants. The equality that matters was sharpened at the same time: every rendering is checked against the *series*, never against another rendering, so re-rounding an already-rounded number cannot pass by looking self-consistent.
3. **An empty mapping deleted an entire error path.** The degrade requirement — "a failing trend empties the trend cells and nothing else" — reads like it needs a flag threaded through the row builder and both templates. Returning `{}` from the containment function instead makes it structural: the builder already looks a day up with `.get`, so a miss is already an empty cell, and the same single mechanism covers the injected fault and the impossible-by-construction missing day. There is no degrade branch anywhere in the row path to get wrong, and the property that pins it ("an empty mapping costs only the trend column") is one assertion.
4. **Choosing the oracle decided how much the acceptance tests were worth.** The tests could have compared rendered rows against a re-implementation of the formatter, which would have proven only that two copies of the same code agree. Reading the expectation from `GET /trend` — the endpoint the chart itself fetches — means a second algorithm, a second rounding path, or a windowed re-smoothing on either surface fails at an assertion rather than in a comment. The feature's sharpest claim and its cheapest test turned out to be the same thing.
5. **A "small" presentation delta moved five shipped assertions, and that was predictable at DISCUSS.** The row grammar was pinned in three test modules and two CSS selectors before this feature started; the delta enumerated all of them in Pre-Requisites (b) at DISCUSS, so DELIVER renegotiated them in the open with the intent restated in each docstring instead of discovering them as red tests. The cost of the sweep was one grep; the alternative is a DELIVER step that looks like a regression and gets "fixed" by weakening a pin.

## References

- Workspace: `docs/feature/numeric-trend-history/` (feature-delta.md incl. DISCUSS/DESIGN/DISTILL/DELIVER + § Changed Assumptions, slices/slice-01-trend-column.md, deliver/mutation/mutation-report.md)
- Architecture SSOT: `docs/product/architecture/brief.md` (trend-column delta paragraph, ADR index, Component Inventory), `adr-013-entry-row-trend-delivery.md`
- KPI contracts: `docs/product/kpi-contracts.yaml` (KPI-10, AT mapping, baseline) · Outcomes: `docs/product/outcomes/registry.yaml` (OUT-13)
- Scenario SSOT: `tests/weight-trend-tracker/acceptance/milestone-12-trend-in-the-record.feature` (12 scenarios); paired properties `properties/test_recent_list_properties.py` (rewritten) and `properties/test_trend_by_day_properties.py` (new)
- Commit range: `95794e0..HEAD` on main; deploy path = existing pipeline on push
