<!-- markdownlint-disable MD024 -->
# Feature Delta: home-trend-display

## Wave: DISCUSS

### [REF] Persona ID

`clemens` — see `docs/product/personas/clemens.yaml`. Sole customer, sole user, sole developer. Phone-first, half-awake at 06:45, metric units, ~82 kg range. Unchanged from `weight-trend-tracker`.

### [REF] JTBD One-Liner

Job `track-true-weight-trend` (`docs/product/jobs.yaml`, status: validated). This feature serves the **judging moment** (`js-2-judge`: *"see a smoothed trend that absorbs water-weight noise so I can decide based on real movement, not noise"*) — but at a **new moment of use**: the capture moment itself, not a deliberate graph visit.

**Bridge decision**: a new job-story moment `js-4-glance` was appended to `jobs.yaml` (2026-07-23): *When I've just stepped off the scale and my eye is still on the entry screen, I want to see my current trend weight and weekly rate at a glance, so I can know where I stand and which way I'm moving before pocketing the phone.* Rationale: `js-2-judge` is triggered by anxiety (a raw spike) and answered by a deliberate trend-view visit; the glance is ambient, happens every morning, and requires zero navigation — a distinct moment of the same job, not a new job. No re-run of JTBD analysis (D4).

**Content decision (locked, from user)**: the home screen shows **trend weight + weekly rate** — e.g. `Trend: 82.3 kg · ↓0.25 kg/week`. The number answers "where am I"; the rate answers "which way am I moving".

### [REF] Locked Decisions

- **D1** Feature type: user-facing.
- **D2** Walking skeleton: NO — brownfield; the full vertical (port → route → template → prod) exists; this feature is one thin slice on it.
- **D3** UX research depth: lightweight — journey delta, happy path, single persona.
- **D4** JTBD: bridge only to existing validated job `track-true-weight-trend`; no full re-analysis.
- **D5** Density: mode=lean (Tier-1 [REF] only), expansion_prompt=ask-intelligent (triggers evaluated and reported to orchestrator — none fired).

### [REF] Scope Assessment

**PASS — 1 story, 1 bounded context (weight tracking), estimated ~0.5–1 day.** Oversized signals checked: stories 1/10 threshold, bounded contexts 1/3, walking-skeleton integration points N/A (skeleton exists; slice touches 1 read surface + 1 template), effort ~1 day ≪ 2 weeks, single user outcome (glanceable orientation at log time). **Zero of five signals fired**; no split needed. Reference class: prior slices (US-001…006) each landed in ~0.5–1 day.

### [REF] Journey Summary

SSOT: `docs/product/journeys/daily-weight-tracking.yaml` — **delta only**; steps 2–4 untouched. Step 1 ("Log today's weight") extended:

- Screen gains a glance line `Trend: 82.3 kg · ↓0.25 kg/week` visible without scrolling while the keypad is open; entry field autofocus + decimal keypad + ≤2 s interactivity unchanged (KPI-1 guardrail).
- After a successful save the glance line **refreshes in place** (the save flow is already an inline fetch — no reload). This relocates the Problem Relief beat: the post-sushi reassurance ("83.6 raw, trend barely moved") now lands at the sink, at the moment of capture, instead of two taps away.
- New shared artifact `current_trend_display` — derived from the same smoothed series as the graph's trend view (single source: `TrendProjection`; derived, never stored). Integration checkpoint: home glance value must equal the graph trend line's value for the same entry set.
- New failure modes: trend lookup failure must degrade to an absent line (never block entry/save); glance must not inflate the deliberate trend-view KPI counter; rate must not be shown on a days-old record.

Emotional delta (step 1 exit): "done — quiet satisfaction" → "done and **oriented** — knows where he stands and which way he's moving." Changelog entry added, dated 2026-07-23.

### [REF] Story Map

Extends the `weight-trend-tracker` map (same persona, same goal). New task under the existing **Capture weight** activity; no new activities.

| Capture weight | Review history | Judge trend | Maintain record |
|---|---|---|---|
| Log today (US-001) ✅ | Entries list (US-001) ✅ | Trend line (US-004) ✅ | Backfill/edit (US-003) ✅ |
| ≤5 s entry (US-006) ✅ | Raw graph + scales (US-002) ✅ | Trend↔Raw toggle (US-005) ✅ | |
| **Glance trend while logging (US-007)** — this feature | | | |

**Walking skeleton**: N/A — exists (delivered 2026-07-23, `weight-trend-tracker`). This feature = **Slice 01** (`slices/slice-01-glanceable-trend.md`), one thin end-to-end slice riding the existing vertical: `TrendProjection` read → route context → template render → inline post-save refresh.

### [REF] Priority Rationale

Single slice — no internal ordering to rationalize. Placement in the product stream: **do now, ahead of any new feature ideas**. Value 4 (relocates the product's core emotional payoff — noise-vs-signal reassurance — to the one screen used 365 mornings/year; directly feeds KPI-2 adherence and the judging job), Urgency 2 (no deadline; but dogfooding is live daily, so every morning without it is a lost glance), Effort 1 (all substrate exists). Priority score 8 — quick win. MoSCoW: Must (explicit user request; trend + rate content locked).

### [REF] System Constraints

- Prior constraints and assumptions **A1–A8 all hold** (range 30.0–250.0 kg, 0.1 kg precision, device-local day, one entry/day, edit-not-delete, single user, passphrase gate, metric only).
- **Entry primacy (KPI-1 guardrail)**: the glance is context, never a competing action. Entry screen interactive ≤2 s; weight field autofocus + decimal keypad unchanged; the trend line never receives focus and never delays input readiness. A failed/slow trend lookup degrades to an absent line — logging and saving are never blocked.
- **Single smoothed series**: the glanced trend value is the same smoothed, deterministic, gap-robust series the graph renders (behavioral constraint; `TrendProjection` is the single source — derived per read, never stored). No second trend algorithm.
- **Rate is behavioral only**: how the weekly rate is derived (Kalman state, trend-endpoint differencing, …) is a DESIGN decision. Behavioral requirements: deterministic; consistent in sign and magnitude with the displayed trend's movement; expressed in kg/week.
- **Display precision**: trend at 0.1 kg (A9); rate at 0.05 kg/week steps, two decimals (A10). Direction glyphs ↓ / ↑ / → are neutral — identical styling for loss and gain; no colors, no judgment, no gamification (persona value: single-purpose minimalism).
- **Sparse-record honesty**: rate shown only once the record spans ≥7 days (A11); trend value shown from the first entry (consistent with US-004 "available from the first entry").
- **KPI integrity**: rendering the home glance must NOT count as a deliberate trend-view open (KPI-3 event `trend.view.opened` must not fire); the glance emits its own telemetry event (naming/mechanism = DESIGN, `append_event` pattern exists).
- **Read-only surface**: extends read ports only; `WeightHistory`/`TrendProjection` must never expose write methods (CLAUDE.md / ADR-005).

### [REF] User Stories

One story. `job_id: track-true-weight-trend` (moment `js-4-glance`, serving `js-2-judge`'s outcome). Persona: Clemens.

#### US-007: Glance where you stand while you log

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.5–1 day

##### Problem

Clemens logs 83.6 kg the Friday morning after a sushi dinner and the raw number stings — but the reassuring answer ("the trend barely moved") lives two taps away on the graph page. Every morning he wants a one-second answer to "where am I, and which way am I moving?" at the moment of logging, without a navigation detour that would tax a half-awake 06:45 routine.

##### Elevator Pitch

- **Before**: The entry screen shows only the form, yesterday's reference, and — after saving — "Saved: 83.6 kg — Fri 24 Jul". To judge whether that number matters he must tap History → wait for the graph → read the trend line (~2 taps and a context switch he skips most mornings).
- **After**: Opens `/` → sees `Trend: 82.3 kg · ↓0.25 kg/week` beside the entry form → types `83.6`, taps **Save** → the confirmation appears AND the glance line refreshes in place to `Trend: 82.4 kg · ↓0.20 kg/week` — no reload, no navigation.
- **Decision enabled**: "Do I need to care about this morning's number — adjust anything, or stay the course?" — answered at the sink, before the phone is pocketed, from trend direction rather than the raw reading.

##### Domain Examples

1. *Happy path*: Thu 23 Jul 2026, 06:45 — trend stable at 82.3 kg, losing 0.25 kg/week. Home shows `Trend: 82.3 kg · ↓0.25 kg/week`; Clemens logs 82.1, sees the confirmation and the refreshed line — verdict "on track" in one glance.
2. *Reassurance (sushi morning)*: Fri 24 Jul — scale says 83.6 after last night's omakase. Pre-save glance: `Trend: 82.3 kg · ↓0.25 kg/week`. He saves 83.6; the line refreshes to `Trend: 82.4 kg · ↓0.20 kg/week` — the spike is visibly absorbed (US-004 guarantees ≤0.3 kg movement); decision: change nothing.
3. *Gaining, shown plainly*: after a two-week vacation the trend reads 83.1 kg rising 0.30 kg/week → `Trend: 83.1 kg · ↑0.30 kg/week` — same typography as the losing case; information, not alarm.
4. *Young record*: fresh start — entries only since Mon 20 Jul, today is Thu 23 Jul (span 3 days). Home shows `Trend: 82.5 kg` with **no rate** — a 3-day rate would be noise dressed as insight. Boundary: first entry Thu 16 Jul + today 23 Jul (span exactly 7 days) → rate appears.
5. *Steady state*: trend flat at 82.0 kg, rate rounds to 0.00 → `Trend: 82.0 kg · → 0.00 kg/week`.
6. *Empty record*: brand-new install, 0 entries — no trend line at all; the entry form is the whole screen (matches the yesterday-reference behavior).

##### UAT Scenarios (BDD)

###### Scenario: Where-am-I and which-way are answered in one glance

- **Given** Clemens's smoothed trend is 82.3 kg, declining 0.25 kg/week, on Thursday 23 July 2026
- **When** he opens the tracker to log his morning weight
- **Then** the entry screen shows "Trend: 82.3 kg · ↓0.25 kg/week" without scrolling, with the keypad open
- **And** the displayed trend value equals the trend the graph view renders for the same entries

###### Scenario: A sushi-morning spike is defused at the moment of logging

- **Given** the entry screen shows "Trend: 82.3 kg · ↓0.25 kg/week"
- **When** Clemens saves 83.6 kg the morning after a sushi dinner
- **Then** the save confirmation appears as before
- **And** the glance line refreshes in place — without a page reload — to the trend recomputed with today's entry

###### Scenario: Gaining is shown as plainly as losing

- **Given** Clemens's trend is 83.1 kg, rising 0.30 kg/week after a vacation
- **When** he opens the entry screen
- **Then** it shows "Trend: 83.1 kg · ↑0.30 kg/week" with styling identical to the declining case

###### Scenario: A young record holds its tongue about the rate

- **Given** Clemens's first entry is Monday 20 July 2026 and today is Thursday 23 July
- **When** he opens the entry screen
- **Then** it shows the trend value (e.g., "Trend: 82.5 kg") with no weekly rate

###### Scenario: An empty record shows no trend line

- **Given** the tracker has no entries yet
- **When** Clemens opens the entry screen
- **Then** no trend line is shown and the weight field is focused, exactly as before
- **And** after he saves his first entry, the trend line appears with that value

###### Scenario: The glance never taxes the entry (@property)

- **Given** Clemens opens the entry screen on his phone over a mobile connection
- **Then** the screen is interactive within 2 seconds with the weight field focused and decimal keypad shown
- **And** if the trend cannot be shown (lookup failure), the line is simply absent and saving still works

###### Scenario: The stats page still tells deliberate study from ambient glances

- **Given** Clemens opens the entry screen 7 mornings in a week and opens the graph's trend view twice
- **When** he checks the stats page
- **Then** the deliberate trend-view count for the week reads 2, not 9

##### Acceptance Criteria

- [ ] Entry screen shows `Trend: {value} kg · {↓|↑|→}{rate} kg/week` whenever a trend exists; visible without scrolling with the keypad open.
- [ ] Trend value at 0.1 kg precision; rate at 0.05 kg/week steps (two decimals); glyph ↓/↑ from the rounded rate's sign, → when it rounds to 0.00; identical neutral styling in all three cases.
- [ ] Glanced trend value equals the graph trend line's value for the same entry set (single smoothed series, deterministic).
- [ ] After a successful save, the glance line refreshes in place (no reload) to the trend including the new entry — including first appearance after the very first entry.
- [ ] Rate shown only when the record spans ≥7 days (latest − earliest entry date); trend value shown from the first entry; 0 entries → no line.
- [ ] Entry primacy preserved: interactive ≤2 s, field autofocus + decimal keypad unchanged; trend lookup failure degrades to an absent line and never blocks or delays typing or saving.
- [ ] Rendering the glance does not increment the deliberate trend-view counter (KPI-3); glance availability is recorded as its own telemetry event.

##### Technical Notes

- All substrate exists: `TrendProjection` (Kalman+RTS, ADR-004) recomputed per read; entry screen save flow is already an inline fetch; telemetry `append_event` pattern established.
- Rate derivation (Kalman state vs. trend-endpoint differencing) is a DESIGN decision constrained by the behavioral ACs (deterministic, sign-consistent with the displayed trend).
- KPI-3 non-pollution likely requires the glance NOT to reuse `GET /trend` as-is (that route emits `trend.view.opened` per open) — surface/mechanism is DESIGN's call; the behavioral requirement is the counter separation.
- Dependencies: US-004 (trend, delivered), US-006 (entry screen, delivered). No external dependencies.

### [REF] Out of Scope

Weekly-rate annotation on the graph page; goal lines, targets, or "when will I reach X" predictions; color-coding or judgment of direction (green/red); streaks or gamification; configurable display (units, precision, thresholds); trend on the login (passphrase) page; history sparkline on the home screen; persisting glance history. Everything on the prior feature's out-of-scope list remains out.

### [REF] Walking Skeleton Strategy

**N/A — brownfield.** The full production vertical (ports → routes → templates → Fly.io deploy with CI gates and smoke) was delivered by `weight-trend-tracker`. This feature reuses it end-to-end: one read surface, one template change, one telemetry event; deploys through the existing pipeline; dogfooded with the next real morning entry.

### [REF] Driving Ports

Behavioral, solution-neutral; DESIGN owns shapes and adapters. Read-only ports must never expose write methods (CLAUDE.md).

- **TrendProjection** (driving, read-only) — **extended read surface**: in addition to `trend_series_in(range)`, the system must be able to answer *"current trend value and weekly rate as of today"* deterministically from the entry record. Whether this is a new port operation or a shell derivation over the existing series is a DESIGN decision. Used by US-007 (and US-004/005 unchanged).
- **WeightHistory** (driving, read-only) — unchanged (yesterday anchor already served).
- **WeightLogging** (driving) — unchanged; the save response/refresh flow may carry or trigger the updated glance (mechanism = DESIGN).
- Telemetry (driven, established `append_event` trail) — one new glance event, counted separately from `trend.view.opened`.

### [REF] Pre-Requisites

None blocking DESIGN. For DELIVER: DESIGN must pick the rate-derivation method satisfying US-007's determinism/sign-consistency ACs and the KPI-3-separation mechanism. Production pipeline live (prior feature); same-day dogfood possible with the next morning entry.

### [REF] Outcome KPIs

**Objective**: The morning verdict — where am I, which way am I moving — becomes ambient: delivered on the entry screen every logging morning, at zero navigation cost and zero entry-speed cost.

Extends the existing registry (KPI-1…4 unchanged, see `weight-trend-tracker`). New:

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|-----|-----------|-------------|----------|-------------|------|
| 5 | Clemens | sees trend + weekly rate at the moment of logging | glance present on ≥95% of logging days (once a trend exists) | 0% (trend only reachable via /graph) | glance telemetry event paired with `entry.saved` per calendar day, surfaced on /stats | Leading |

- **Relationship to KPI-3** (trend-view opens ≥3/week): the glance intentionally satisfies routine reassurance in-context, so deliberate graph opens may drop toward "study sessions only". A KPI-3 decline after this ships is an **expected substitution, not a regression** — reviewer note for the weekly /stats review. KPI-3's measurement must stay unpolluted (guardrail below).
- **Guardrails (must not degrade)**: KPI-1 entry speed (median ≤5 s, p90 ≤10 s, client-timed); screen interactive ≤2 s; KPI-3 counter counts only deliberate graph trend views (glances excluded by construction); trend determinism; zero lost entries.
- **Hypothesis**: We believe showing trend + weekly rate on the entry screen for Clemens will make daily progress-judgment ambient (glance present ≥95% of logging days) without slowing entry (KPI-1 unchanged), reinforcing the logging habit (KPI-2, North Star) because every log now pays back an answer.
- **Measurement plan**: glance event via the existing `append_event` trail; pairing computed from the event trail + entry store; reviewed in the established weekly /stats cadence. No new instrumentation infrastructure.

### [REF] DoR Validation

| DoR Item | US-007 | Evidence |
|----------|--------|----------|
| 1. Problem clear, domain language | PASS | Sushi-morning 83.6 sting; reassurance two taps away; 06:45 half-awake context |
| 2. Persona specific | PASS | `clemens` — phone-first, 82 kg range, single-purpose minimalism values |
| 3. 3+ domain examples, real data | PASS | 6 examples with real dates/values (82.3 ↓0.25 on Thu 23 Jul; 83.6 sushi on Fri 24 Jul; 7-day-span boundary 16→23 Jul; → 0.00 steady case) |
| 4. UAT 3–7 scenarios G/W/T | PASS (7) | Happy, anxiety/reassurance, neutrality, sparse, empty, @property guardrail, KPI-integrity |
| 5. AC derived from UAT | PASS | 7 ACs map to the 7 scenarios plus quantified precision/threshold rules (0.1 kg, 0.05 kg/week, ≥7-day span, ≤2 s) |
| 6. Right-sized (1–3 d, 3–7 sc.) | PASS | ~0.5–1 day, 7 scenarios, single demo (one morning's log) |
| 7. Technical notes/constraints | PASS | Technical Notes + System Constraints (rate derivation = DESIGN; KPI-3 separation; read-only ports) |
| 8. Dependencies resolved/tracked | PASS | US-004/US-006 delivered 2026-07-23; no external deps |
| 9. Outcome KPIs, numeric targets | PASS | KPI-5 (≥95% glance presence) + explicit guardrails; measurement method named |

**DoR Status: PASSED (1/1 story, 9/9 items).**

**Requirements completeness score: 0.96** — functional behavior fully specified (display, refresh, sparse/empty/error states, telemetry separation), NFRs quantified (≤2 s interactive, precision rules, determinism, KPI-1 guardrail), business rules explicit (≥7-day span for rate, single smoothed series). Deduction: A11's 7-day rate threshold and A10's 0.05 kg/week step are analyst-chosen values pending user confirmation (OQ-6).

### [REF] DoD 9-Item Checklist

Per story, at DELIVER completion (unchanged from prior feature):

1. All UAT scenarios green (automated).
2. Supporting unit/integration tests green.
3. Code refactored; no obvious debt (per-feature mutation gate ≥80% on modified files).
4. Code reviewed (self-review with reviewer agent — solo project).
5. Merged to main.
6. Deployed to the phone-reachable production URL via the existing pipeline.
7. Dogfooded same day with a real morning entry showing the glance.
8. KPI-5 glance event emitting; KPI-1/KPI-3 guardrails verified on /stats.
9. Story demonstrable end-to-end on the phone.

### [REF] Wave Decisions Summary

Locked upstream: D1–D5 (above) + user content decision (trend weight + weekly rate, `Trend: 82.3 kg · ↓0.25 kg/week`). Prior assumptions A1–A8 unchanged and still binding.

New assumptions (subagent mode — chosen autonomously, flagged for confirmation):

- **A9** Home trend value displayed at 0.1 kg precision (matches entry precision and graph).
- **A10** Weekly rate displayed in 0.05 kg/week steps, two decimals (`0.25`, `0.30`); direction glyph from the rounded rate's sign: ↓ declining, ↑ rising, → when it rounds to 0.00; identical neutral styling for all three.
- **A11** Weekly rate shown only once the record spans ≥7 days (latest − earliest entry date); trend value shown from the first entry; 0 entries → no trend line. Rationale: US-004's responsiveness AC says real change becomes visible within ~7 days — any rate quoted on a younger record is noise presented as insight.
- **A12** The glance refreshes in place after a successful save (inline, no reload — the save flow is already fetch-based); trend lookup failure degrades to an absent line and never blocks entry or save.
- **A13** The glance emits its own telemetry event and must not increment `trend.view.opened` (KPI-3 stays a deliberate-engagement metric); event naming/mechanism = DESIGN.

Open questions (non-blocking; defaults above apply unless overridden):

- **OQ-6** Confirm the rate-display rules: 0.05 kg/week step (A10) and the ≥7-day-span visibility threshold (A11) — or prefer a coarser/finer step or an earlier/later rate debut?

Risk notes: negligible technical risk (all substrate delivered and mutation-tested); product risk = visual clutter on the five-second screen (mitigated by the entry-primacy guardrail AC and @property scenario); KPI-3 substitution effect documented as expected. JTBD traceability intact (`js-4-glance` appended to jobs.yaml; story is N:1 to the single validated job). No DIVERGE wave for this delta — consistent with the product's accepted pattern (user = customer; content decision made directly by the user); noted as accepted risk, not a gap. Density telemetry skipped: `scripts/shared/telemetry.py` not present in this repo.

## Wave: DESIGN

Architect: solution-architect (Morgan), 2026-07-23. Mode: Propose (2 open decisions analyzed; user selected among options). SSOT updated: `docs/product/architecture/brief.md` (§ Application Architecture — Domain Core row, TrendProjection row, glance-delivery note, ADR index) + new `docs/product/architecture/adr-006-glance-rate-derivation.md`. ADR-001…005 unchanged; ADR-004 **not** superseded. No C4 L1/L2 changes (no new containers, actors, or external systems). Per-wave peer review skipped (no trigger: no contested ADR, no novel pattern, no security change; consolidated review at end of DISTILL). Density: lean, no Tier-2 expansions; density telemetry skipped (`scripts/shared/telemetry.py` absent).

### [REF] DDD Assessment

Trivial delta — prior D-01…D-04 verdicts hold: ONE bounded context (weight tracking), no new aggregates (glance is a pure derivation over the existing entry record; no new consistency boundary), ES/CQRS still rejected. Ubiquitous-language additions: `glance`, `glance summary`, `weekly rate` (kg/week, trailing-7-day).

### [REF] Component Decomposition

Delta only — authoritative table: `brief.md` § Component Decomposition and Ports.

| Component | Delta |
|---|---|
| Domain Core | + pure `glance(entries) -> GlanceSummary \| None` (frozen dataclass: series-end `trend_kg`, `rate_kg_per_week \| None`) + pure quantize/glyph rule (ADR-006). Contract shape: pure-function (return-only). |
| Web UI (`index.html`) | + glance line in initial server-rendered HTML (Jinja conditional, `yesterday-reference` pattern); save handler updates it from the save response. String formatting lives here/shell, not in core. |
| Routes | `GET /`: context gains glance (reuses already-fetched entries — zero added I/O). `POST /entries`: response gains `glance` field (or null). `GET /stats`: + glance event count (KPI-5). `GET /trend`: **unchanged**. |
| Composition root | + wires the glance pure callable into `build_router`. No new adapters ⇒ no new probes (glance path is pure over the already-probed `EntryStore`). |

### [REF] Driving Ports

| Port | Delta |
|---|---|
| `TrendProjection` | **Extended read surface**: glance summary injected as a second pure callable at the composition root (established functional-DI pattern, `routes.py` type alias). Still read-only, derived-never-stored — no write methods. |
| `WeightLogging` | **Unchanged.** The `glance` field in the save response + route-level `trend.glance.shown` emission are driving-adapter (route) concerns, NOT a widening of `record_or_replace` (bounded-change universe stays one `{date}` row + one `entry.saved` event; precedent: derived `confirmation` field). |
| `WeightHistory`, `AccessGate` | Unchanged. |

### [REF] Driven Ports and Adapters

Unchanged — no new driven ports, adapters, or probes. `EntryStorePort.append_event` (established) carries the new event name; `telemetry_store.py` query functions are name-parameterised and need no change.

### [REF] Technology Choices

Unchanged — zero new dependencies. All work lands in existing Python core/shell + one Jinja template.

### [REF] Decisions

Numbering continues from prior feature (D-11).

| # | Decision | ADR |
|---|---|---|
| D-12 | Weekly rate = trailing-7-day endpoint difference of the smoothed series: `smoothed[-1] − smoothed[-8]` on the daily grid; visibility threshold = entry-based span ≥7 days (latest − earliest entry date ⇔ grid ≥8 points); quantization `round(rate / 0.05) * 0.05` (Python round-half-even ties, pinned), two decimals; glyph from rounded sign (↓/↑, → at 0.00). Rejected: LS slope over last N days (free parameter, sign can contradict visible endpoint movement); local-linear-trend state model (would supersede ADR-004, re-derive AC margins). Rate maths + quantize/glyph rule = Domain Core (pure); formatting = shell/template. | ADR-006 |
| D-13 | Glance delivery = server-render on `GET /` (reuse already-fetched entries; line present in first HTML paint; zero added HTTP against the ≤2 s guardrail) + `glance` field in `POST /entries` JSON response for in-place refresh (covers first appearance after the very first entry). KPI-3 separation structural: glance never touches `GET /trend` (which emits `trend.view.opened` unconditionally). Failure degrades to `glance = null` → absent line; save never blocked. Rejected: separate `GET /glance` (extra round-trip, post-paint pop-in, second post-save fetch); `GET /trend?glance=1` event-suppress flag (KPI-3 integrity by fragile convention). | ADR-006 (delivery noted), brief.md |
| D-14 | Glance telemetry event = `trend.glance.shown`; fires **per delivery** of glance data (each `GET /` render with data + each save response carrying glance), no per-day dedup — KPI-5's per-calendar-day pairing with `entry.saved` is computed at read time on /stats from the trail. Exact-name counters ⇒ no collision with `trend.view.opened`. | brief.md |

### [REF] Reuse Analysis

Brownfield — every touch point EXTENDs a shipped component; zero CREATE-NEW components (codebase verified 2026-07-23).

| Component | Verdict | Contract shape · universe · crafter assertion mechanism |
|---|---|---|
| Domain Core (`core/trend.py`, `core/types.py`) | EXTEND | pure-function (return-only) · no mutation universe · property tests (determinism, sign-consistency), as `trend_series` (OUT-5 pattern). New `core/glance.py` vs extending `trend.py` = crafter's call, same component. |
| `TrendProjection` port (`routes.py:63` Callable alias) | EXTEND | read-only, derived-never-stored · second injected pure callable · AT determinism @property |
| Route `GET /` | EXTEND | shell read path · reuses `store.all_entries()` already fetched for yesterday anchor · AT on rendered HTML |
| Route `POST /entries` | EXTEND | shell over bounded-change port (port untouched, see Driving Ports) · +`glance` response field, +`trend.glance.shown` append · AT on save-response JSON |
| Route `GET /trend` | REUSE unchanged | must not change — emits KPI-3 unconditionally |
| Route `GET /stats` | EXTEND | shell read · + glance event count via existing generic counters |
| `index.html` | EXTEND | driving adapter · glance line + save-handler update in the existing submit handler |
| `telemetry_store.py` | REUSE unchanged | name-parameterised queries |
| `EntryStorePort` | REUSE unchanged | `append_event` already exists |
| Composition root | EXTEND | shell wiring only; no new probes |

### [REF] Open Questions / DISTILL Pinning Notes

1. **Entry-based span semantics** (pin at DISTILL): rate-visibility threshold = latest − earliest **entry** date ≥7 days (AC literal wording), NOT today − first entry. Guarantees the trailing-7-day lookback exists (grid ≥8 points) even on a stale record.
2. **Glance value = series-end value**: the "current" trend is the smoothed value at the **last entry day** (the grid ends there, `core/trend.py` — not today). Identical to where the graph's line ends, which is exactly the single-source AC. Oracle: glance value == last point of `GET /trend` (ALL) for the same entry set.
3. **RTS co-revision**: after a save, trend value AND rate both revise (both rate endpoints move with the line) — the sushi example (0.25 → 0.20) is this behavior. Oracles must assert coherence of the currently rendered pair, not immutability of prior renderings (extends prior feature's OQ-3 gap-oracle framing).
4. **First-entry appearance**: the glance's first appearance rides the save response (page had no glance at 0 entries) — AT must cover save-response delivery, not only page render. Also the KPI-5 day-1 pairing case (`trend.glance.shown` fires from the save delivery).
5. **Quantization tie rule**: `round(rate / 0.05) * 0.05` with Python round-half-even ties is part of the determinism contract (ADR-006); PBT may pin it.
6. **Outcome registry** (DELIVER, per established convention — prior feature registered OUT-1…6 at delivery): add one operation entry for the glance summary, `related: [OUT-3, OUT-5]`. Manual collision check vs `registry.yaml` (2026-07-23): no overlap with OUT-1…6; OUT-3/OUT-5 are extended, not duplicated. `nwave-ai outcomes check-delta` not run: no shell access in this DESIGN session, and the CLI is documented defective in `registry.yaml` header (mis-packaged schema.json, exit 1); re-check at DELIVER.

### Changed Assumptions

- **DISCUSS said**: AC/A11 wording — "Rate shown only when the record spans ≥7 days **(latest − earliest entry date)**"; but Domain Example 4's boundary phrasing — "first entry Thu 16 Jul + **today** 23 Jul (span exactly 7 days) → rate appears" — measures span against *today*.
- **Now (pinned at DESIGN, D-12)**: span = **latest entry date − earliest entry date** (the AC's literal parenthetical). The two readings differ only on a stale record (no entry today); the boundary example implicitly assumes an entry on 23 Jul and is consistent under the pin.
- **Rationale**: the smoothed grid ends at the last entry day (ADR-004, `core/trend.py`), so only the entry-based span guarantees the trailing-7-day lookback is defined; a today-based span could demand a rate the series cannot support. Back-propagation: DISTILL should phrase the boundary scenario with an entry logged on the boundary day.

## Wave: DISTILL

Acceptance designer: Quinn, 2026-07-23. Density: lean (Tier-1 [REF] only), no Tier-2 expansions; density telemetry skipped (`scripts/shared/telemetry.py` absent in this repo). Reconciliation HARD GATE: **passed — 0 contradictions** (DESIGN's Changed Assumptions already pinned A11 to the entry-based span, resolving DISCUSS's only internal tension; boundary scenario phrased with an entry ON the boundary day per the back-propagation note). Graceful degradation: **WARN — DEVOPS artifacts missing; infra inherited from `weight-trend-tracker`, no env matrix change** (pipeline delivered by the prior feature, intentionally not re-run). Infrastructure Policy: `--policy=inherit`, all ports in scope already covered (TestClient over production `build_app`, real SQLite on tmp_path, FakeClock); no rows appended. `[lang-mode] python` · `[port-mode] inherited (tests/common/state_delta.py)`.

### [REF] Telemetry naming reconciliation

Code grammar wins (verified in `routes.py`): on-trail event names are dotted (`entry.saved`, `trend.view.opened`); the underscore spellings in `kpi-contracts.yaml` are the /stats JSON keys. New event = `trend.glance.shown` (DESIGN D-14, grammar-consistent); new /stats key = `trend_glance_shown_count` (mechanical transform, precedent `trend.view.opened` → `trend_view_opened_count`). Note added to `kpi-contracts.yaml`.

### [REF] Scenario list with tags

SSOT: `tests/weight-trend-tracker/acceptance/milestone-6-home-trend-glance.feature` (13 blocks → 17 scenario instances) + `tests/weight-trend-tracker/acceptance/properties/test_glance_properties.py` (9 pure-core PBT properties). All carry `@US-007` + a `@contract-shape:` tag; all except the walking skeleton are `@pending`.

| Scenario | Tags | RED anchor |
|---|---|---|
| The morning verdict arrives with the log and survives the save | @walking_skeleton @driving_port @driving_adapter @real-io @contract-shape:bounded-change | glance line absent (Given anchor) |
| Where-am-I and which-way are answered in one glance | @driving_port @contract-shape:pure-function | glance line absent |
| A sushi-morning spike is defused at the moment of logging | @driving_port @contract-shape:bounded-change | glance line absent (Given anchor) |
| Every direction is information, never judgment (outline ↓/↑/→) | @driving_port @contract-shape:pure-function | glance line absent |
| Standing still is reported plainly | @driving_port @contract-shape:pure-function | glance line absent |
| A young record holds its tongue about the rate (outline: span 3 / 6 / 7, entry-based) | @driving_port @error @contract-shape:pure-function | glance line absent |
| A resting record still reports where its line ends (stale-record pin discriminator) | @driving_port @error @contract-shape:pure-function | glance line absent |
| An empty record shows no trend line until the first save brings one | @driving_port @error @contract-shape:bounded-change | /stats glance key absent (Given anchor) |
| The glance never taxes the entry (≤2 s, focus, keypad) | @driving_port @property @kpi @contract-shape:pure-function | glance line absent |
| A trend hiccup hides the glance, not the morning | @driving_port @error @contract-shape:pure-function | glance line absent (healthy-render Given anchor) |
| A trend hiccup never blocks the save | @driving_port @error @contract-shape:bounded-change | glance line absent + save `glance` key absent |
| A rejected save leaves not even a glance behind | @driving_port @error @contract-shape:unbounded-preservation | glance line absent (Given anchor) |
| The stats page still tells deliberate study from ambient glances (7 home opens + 2 trend opens → 2) | @driving_port @kpi @real-io @adapter-integration @contract-shape:bounded-change | /stats glance key absent |

Error-path density: 8 of 17 scenario instances tagged `@error` = **47%** (≥40% mandate met). Journey `failure_modes` (step 1 delta) all covered: degrade-to-absent (2 hiccup scenarios), KPI-counter separation (stats scenario), sparse-rate honesty (young-record outline + resting record).

Pure-core properties (layer 1, PBT full — Mandate 9): determinism · input-order invariance · value == trend-line END (single source) · rate == `smoothed[-1] − smoothed[-8]` (sign-consistency by construction, oracle = shipped `trend_series`/OUT-5) · rate None iff entry span <7 (pinned `@example`s at span 6 and 7) · empty → None · first entry → value without rate · quantization == `round(r/0.05)*0.05` verbatim (float ties pinned, `@example` 0.025/0.075/−0.01) · glyph from rounded sign incl. negative zero → "→". Layer-3 HTTP scenarios are example-only (Mandate 9/11); `@property`-tagged acceptance criteria are example-pinned at this layer, PBT-full at layer 1.

### [REF] WS strategy

Prior feature's WS exists and is green; per skill this feature still proves its OWN e2e wiring: ONE scenario tagged `@walking_skeleton @driving_port @driving_adapter @real-io` through the production composition root (`build_app` + TestClient + real SQLite) covering the render → save → in-place-refresh loop. Enabled (not @pending) = the first RED to drive. Tier B state-machine PBT: **not emitted** — the glance is a pure derivation over the entry record (no new state machine to model; the only mutable state is the record, already covered by the prior feature); the domain-rich input space is explored at layer 1 via the pure-core PBT suite instead (per Mandate 10 skip conditions + Hebert model-shape trigger).

### [REF] Adapter coverage

| Adapter | Treatment (policy) | @real-io scenario |
|---|---|---|
| EntryStore (SQLite, entries + events) | real file on tmp_path, prod pragmas | WS + "The stats page still tells deliberate study from ambient glances" (@real-io @adapter-integration: `trend.glance.shown` rows appended and read back via /stats) |
| Clock | FakeClock (driven external / non-deterministic) | n/a — per policy |
| No new driven adapters / probes | — | DESIGN: glance path is pure over the already-probed EntryStore |

### [REF] Scaffolds

`src/weight_tracker/core/glance.py` (`__SCAFFOLD__ = True`; `glance(entries) -> GlanceSummary | None`, `quantize_rate`, `rate_glyph`, frozen `GlanceSummary` — bodies raise AssertionError). Existing modules (`routes.py`, `composition.py`, `index.html`) NOT scaffolded: scenarios against them RED on assertions (presence-first structure prevents KeyError/regex-None BROKEN classification). Module placement is the crafter's call per DESIGN — re-export from `core/glance.py` if folded into `trend.py`.

### [REF] Test placement

Extended the existing suite: `tests/weight-trend-tracker/acceptance/` (milestone-6 file + `steps/steps_glance.py` + `steps/test_milestone_6.py` + `properties/test_glance_properties.py`). Justification: the `composition`/`fake_clock`/`ctx` fixtures and the `@pending` skip hook are scoped to that suite's conftest, and `pyproject pythonpath` registers exactly that `steps/` dir as the single Mandate-12 step vocabulary — a parallel `tests/home-trend-display/` tree would duplicate the conftest and split the SSOT.

### [REF] Driving adapter coverage

| Entry point (DESIGN) | Scenario coverage |
|---|---|
| `GET /` (glance in server-rendered HTML) | WS + all render scenarios (real HTTP via TestClient) |
| `POST /entries` (save response gains `glance` field \| null; absent on rejection) | WS refresh, sushi refresh, first-save, hiccup-save (null), rejected-save (absent) |
| `GET /stats` (+ `trend_glance_shown_count`) | KPI-separation scenario + all glance-universe captures |
| `GET /trend` | must stay UNCHANGED — asserted via `trend views this week = 2` after 7 ambient renders |

DELIVER-facing HTTP contract (glance element `<p id="trend-glance">Trend: 82.3 kg · ↓0.25 kg/week</p>`, neutral markup for all glyphs; response/null/absent semantics; event-per-delivery) = executable spec in `composition.py::GlanceService` docstring. Format assumption flagged: glyph directly prefixes the magnitude (`↓0.25`, `→0.00`) per the AC formula `{↓|↑|→}{rate}`; DISCUSS example 5 showed a space (`→ 0.00`) — cosmetic, pinned to the AC literal.

### [REF] Mandate-12 evidence (four criteria)

1. Domain types module: `steps/domain_types.py` extended with `TrendDirection`, `RateDisposition` (+ parsers); production types re-exported as before. 2. Composition services consume typed parameters (`seed_recent(TrendDirection)`, `assert_rate_disposition(RateDisposition)`). 3. AST check: all 25 new step bodies are ≤2 statements delegating to `composition.<service>.<method>(...)`, zero control flow. 4. Step-reuse ratio (informational natural ceiling): milestone-6 = 70 step occurrences / 25 new decorators = **2.80×** (plus reuse of 10 pre-existing decorators: Background, seeding, save/confirmation, stats); suite-wide = 268/107 = **2.50×**. Below 4× as expected for a single-slice read-surface feature; criteria 1–3 met, no forced collapse (Pillar 1 outranks ratio).

### [REF] AT-completeness audit (15-item, Phase 2.5)

C1a ✔ (empty record; PBT span 0) · C1b ✔ (span 3/6/7 outline, entry ON boundary day) · C2a ✔ (glance state machine in `steps_glance.py` docstring) · C2b ✔ (rejected-save, failure-mid-morning, young-record-rate-demand per state) · C3 ✔ (0/1/many entries: empty→first-save, single-entry property, two-week seeds) · C4a ✔ (determinism PBT = render-twice idempotency; re-save covered by prior feature + co-revision oracle) · C4b ✔-N/A (no inverse op exists — edit-not-delete product rule A1–A8; documented) · C5a ✔ (no mode flags; the rate-shown/held decision table IS the young-record outline) · C5b ✔-N/A (no flags to keep orthogonal) · C6a ✔ (rejected out-of-range save with glance showing; hostile `?scale=` covered by prior feature) · C6b ✔ (declared degrade contract: line absent / glance null / save unaffected) · C6c ✔ (rejection reason closed-set assert reused; degraded path never 500s — `raise_server_exceptions=True` throughout) · C7a ✔ (failing dependency = degraded-resource analog; broken-store startup covered by prior feature) · C7b ✔-N/A (single-request read path; restart durability owned by prior feature scenarios; documented) · C7c ✔-N/A (single user by locked constraint A6; documented). **15/15 → COMPLETE.** Zero SPECIFICATION_AMBIGUITY findings — all gaps were in delivery scope and filled in-phase. No domain-extension overlays opted in (`distill/at-completeness-extensions.yaml` absent).

### [REF] Outcome registration

`nwave-ai outcomes register --id OUT-7 --kind operation …` attempted 2026-07-23: **exit 1**, the documented tool defect (mis-packaged `schema.json`, FileNotFoundError — not the exit-2 duplicate contract). **Deferred to DELIVER** per established convention (prior feature registered OUT-1…6 at delivery; DESIGN pin 6). Candidate row: OUT-7, kind operation, summary "Glance summary — series-end trend value + trailing-week rate on the entry screen", keywords `glance-summary, home-entry-screen, trailing-week-rate, quantize-glyph, save-response-refresh` (no overlap with OUT-1…6; `related: [OUT-3, OUT-5]`), artifact `tests/weight-trend-tracker/acceptance/milestone-6-home-trend-glance.feature`.

### [REF] Pre-Requisites

For DELIVER: DESIGN pins D-12/D-13/D-14 (all honored verbatim in the oracles); RED gate classification at `distill/red-classification.md` (26/26 MISSING_FUNCTIONALITY, prior suite 86 green, collection 112 clean); `pyproject.toml` gained the `us_007` marker; `kpi-contracts.yaml` gained `trend.glance.shown` + KPI-5 + AT links (KPI-3 link extended with the separation scenario). Deliberate-absence scenarios carry chained Given RED anchors — do not remove them (red-classification note 2). Mutation gate (per-feature, ≥80%) applies to `core/glance.py` + touched routes/template at DELIVER.

## Wave: DELIVER

### [REF] Implementation Summary

DELIVER wave executed 2026-07-23 by nw-deliver orchestrator + nw-functional-software-crafter (ADR-005 paradigm). Shipped US-007's glance line on the entry screen: a new pure Domain Core module `core/glance.py` (`glance(entries) -> GlanceSummary | None`, `quantize_rate`, `rate_glyph`, frozen `GlanceSummary` — trailing-7-day endpoint-difference rate with the pinned 0.05 quantization grid and rounded-sign glyphs, per ADR-006/D-12); server-rendered glance in `GET /`'s first HTML reusing the already-fetched entries, plus a `glance` field in the `POST /entries` JSON response driving the in-place refresh incl. first appearance after the very first entry (D-13); `trend.glance.shown` appended per delivery with `trend_glance_shown_count` surfaced on `/stats` over the same rolling 7-day window as `trend_views_this_week` (D-14); shell-level degrade-to-null containment so a trend hiccup hides the line but never blocks entry or save; KPI-3 separation structural (`GET /trend` untouched). 4 roadmap steps, all RED→GREEN→COMMIT through DES.

### [REF] Files Modified

Production (4 files + marker): `src/weight_tracker/core/glance.py` (new), `src/weight_tracker/web/routes.py`, `src/weight_tracker/web/templates/index.html`, `src/weight_tracker/composition.py`; `pyproject.toml` (`us_007` marker).
Tests (5 files): `tests/weight-trend-tracker/acceptance/milestone-6-home-trend-glance.feature` (new), `steps/steps_glance.py` (new), `steps/test_milestone_6.py` (new), `steps/composition.py` + `steps/domain_types.py` (extended); plus DISTILL-authored `properties/test_glance_properties.py` (lands with the finalize commit).
Docs: feature-delta.md (this file), deliver/{roadmap,execution-log}.json, deliver/mutation/mutation-report.md.

### [REF] Scenarios Green Count

**13 of 13 milestone-6 blocks green** (17 scenario instances after outline expansion) **+ 9 of 9 pure-core glance properties** enabled and green. Full suite: **112 passed, 0 skipped, 0 failed**, 2026-07-23. `@pending` discipline fully unwound for US-007.

### [REF] DoD Check

| # | DoD item (DISCUSS) | Status |
|---|---|---|
| 1 | All UAT scenarios green (automated) | PASS — 13/13 blocks (17 instances) |
| 2 | Supporting unit/integration tests green | PASS — 9/9 glance properties; full suite 112/112 |
| 3 | Code refactored; mutation gate ≥80% on modified files | PASS — Phase 3 pass + 100% effective kill rate (both runs) |
| 4 | Code reviewed | PASS — adversarial review APPROVED, 0 blockers / 0 high / 1 low (fixed) |
| 5 | Merged to main | PASS — trunk-based, all commits on main |
| 6 | Deployed to the phone-reachable production URL | **PENDING-PUSH** — existing pipeline (gates→deploy→smoke) runs on the finalize push to main |
| 7 | Dogfooded same day with a real morning entry showing the glance | **PENDING-PUSH** — follows the deploy; next real morning entry |
| 8 | KPI-5 glance event emitting; KPI-1/KPI-3 guardrails verified on /stats | PARTIAL-PASS — instrumentation verified live in demo (`trend_glance_shown_count` 16 vs `trend_views` 0; KPI-3 unpolluted); real-life KPI-1 guardrail data accrues post-deploy at the weekly /stats review |
| 9 | Story demonstrable end-to-end on the phone | PASS — live-server demo evidence below; on-phone demo follows the push-triggered deploy |

### [REF] Demo Evidence

Post-merge integration gate (Phase 3.5), 2026-07-23, recorded in `deliver/execution-log.json` `gates[]`: real server (`uvicorn`, production env contract), real HTTP via curl. Full suite on local-dev: 112 passed, 0 skipped. `ci` + `production` environments deferred to the existing pipeline on push.

| Story | Demo command | Saw |
|---|---|---|
| US-007 render | `GET /` | first server-rendered HTML contained `<p id="trend-glance">Trend: 83.0 kg · ↓0.10 kg/week</p>` |
| US-007 save-refresh | `POST /entries` (valid save) | saved response carried `"glance": "Trend: 82.9 kg · ↓0.10 kg/week"` — trend + rate co-revised with today's entry (RTS co-revision) |
| US-007 KPI separation | `GET /stats` | `trend_views` 0 vs `trend_glance_shown_count` 16 — KPI-3 unpolluted by ambient glances |

### [REF] Quality Gates

| Phase | Outcome |
|---|---|
| Roadmap + review | Approved (13/13 blocks + 9/9 properties covered, 0 orphans; conditionally→approved after scenario_name fix) |
| Steps 01-01..01-04 | 4/4 COMMIT PASS (`ea9cba3`, `03de8f9`, `fb7dbcd`, `a9da482`); DES integrity: all 4 steps complete traces, exit 0 |
| 01-02 AT-infra fixes | Adjudicated legitimate by reviewer (parser vocabulary constraint, save-flow capture fallback) — no assertions weakened |
| Refactoring (Phase 3) | PASS — 01-03 empty batch (nothing warranted); 01-04 L3 extraction `_log_structured` (`8181842`) |
| Post-merge integration (3.5) | PASS — local-dev full suite + live-server demo (evidence above); ci + production deferred to pipeline on push |
| Adversarial review (Phase 4) | APPROVED — 0 blockers, 0 high, 1 low (stale facade comment in `steps/composition.py:661`, fixed in the finalize commit); Testing Theater 7/7 patterns clean; test budget 22/44 |
| Mutation (Phase 5, per-feature) | PASS — cosmic-ray 8.4.3, two runs: post-01-03 scope 107/107 effective kills; post-01-04 delta scope (`routes.py`) 1/1 effective, 11 runtime-inert annotation survivors documented equivalent. Report: `deliver/mutation/mutation-report.md` |

### [REF] Pre-Requisites

Depended on: DISTILL milestone-6 feature file + glance property suite (authoritative spec — zero oracle defects surfaced during DELIVER), DESIGN pins D-12/D-13/D-14 (honored verbatim: entry-based span, series-end value, structural KPI-3 separation, per-delivery event), ADR-006 (+ ADR-001..005 unchanged), `distill/red-classification.md`, `pyproject.toml` `us_007` marker. Production pipeline inherited from `weight-trend-tracker` — intentionally unchanged; deploy + same-day dogfood ride the finalize push. OUT-7 registered at finalize (per DISTILL § Outcome registration deferral).
