<!-- markdownlint-disable MD024 -->
# Feature Delta: weight-trend-tracker

## Wave: DISCUSS

### [REF] Persona ID

`clemens` — see `docs/product/personas/clemens.yaml`. Sole customer, sole user, sole developer. Phone-first, half-awake at time of use, metric units, ~82 kg range, currently paying $30/month for one feature.

### [REF] JTBD One-Liner

Job `track-true-weight-trend` (`docs/product/jobs.yaml`): *When I step off the scale each morning, I want to capture my weight in seconds and see my true underlying trend, so I can judge real progress without being misled by daily fluctuations.*

Forces: **Push** $30/month bloatware, 30–45 s entry flow. **Pull** owned single-purpose tool, ≤5 s entry, trustworthy trend. **Anxiety** data loss, entry friction breaking the habit, naive smoothing lying across gaps. **Habit** years of logging in the old app; history lives there. Opportunity scoring skipped (single job).

### [REF] Locked Decisions

- **D1** Feature type: user-facing.
- **D2** Walking skeleton: YES (greenfield).
- **D3** UX research depth: lightweight — quick journey map, happy-path focus, single persona.
- **D4** JTBD: yes, proportionate to a single-user personal tool.
- **D5** Density: mode=lean (Tier-1 [REF] only), expansion_prompt=ask-intelligent (triggers reported to orchestrator).

### [REF] Scope Assessment

**PASS — 6 stories, 1 bounded context (weight tracking), estimated ~5 dev days.** Oversized signals checked: stories 6/10 threshold, bounded contexts 1/3, walking-skeleton integration points 3/5 (UI form → one-entry-per-day rule → entry store), effort ~1 week < 2 weeks, single user outcome. Zero signals fired; no split needed.

### [REF] Journey Summary

SSOT: `docs/product/journeys/daily-weight-tracking.yaml`. Four steps: Log today's weight → Review raw history → Judge the trend → Maintain the record. Emotional arc: half-awake routine → micro-satisfaction on save → reassured confidence at the trend (Problem Relief pattern: raw spike resolves into noise on the trend view). Shared artifacts: `weight_entry` (entry store = single source of truth, HIGH risk), `selected_time_scale` (must survive Trend↔Raw toggle, MEDIUM), `today_date` (device-local calendar day, MEDIUM — midnight edge), `unit_label_kg` (single constant, LOW). Error paths per step captured as `failure_modes` in the journey YAML.

### [REF] Story Map

User: `clemens` · Goal: unbroken daily record + trustworthy trend.

| Capture weight | Review history | Judge trend | Maintain record |
|---|---|---|---|
| Log today (US-001) — **WS** | See saved entries list (US-001) — **WS** | *(deferred: needs data)* | Re-save today to correct (US-001) — **WS** |
| ≤5 s entry polish (US-006) | Raw graph + time scales (US-002) | Trend line (US-004) | Backfill/edit past days (US-003) |
| | | Trend↔Raw toggle (US-005) | |

**Walking skeleton** = Slice 01 (US-001): tap icon → enter 82.4 → persisted → confirmation + entries list. Covers 3 of 4 activities end-to-end; "Judge trend" deliberately deferred — a trend over 2 data points teaches nothing (see Priority Rationale).

Releases: **R1** = Slices 01–02 (record replaces old app's logging), **R2** = Slices 03–04 (trend trustworthy → cancellation decision possible), **R3** = Slice 05 (habit-grade speed).

### [REF] Priority Rationale

Order by outcome impact and riskiest-assumption-first (Value×Urgency/Effort; tie-break WS > riskiest assumption > value):

1. **Slice 01 (WS, US-001)** — validates the end-to-end loop exists and dogfooding can start day 1 with production data.
2. **Slice 02 (US-002)** — first review value; graph substrate needed by everything downstream.
3. **Slice 03 (US-003, backfill/edit)** — pulled *ahead* of trend deliberately: backfilling lets Clemens hand-copy ~30–60 days of history from the old app, so the trend slice's riskiest assumption (trend quality on real, gappy data) is testable immediately instead of after a month of fresh logging.
4. **Slice 04 (US-004 + US-005)** — the differentiating value and riskiest assumption: "a smoothed trend I actually trust." Cancellation decision hinges on this.
5. **Slice 05 (US-006)** — speed polish to hit the ≤5 s median; baseline ≤10 s already enforced in US-001.

MoSCoW: Must = US-001…US-005 (all explicitly requested behaviors). Should = US-006 (top stated value, but baseline speed AC in US-001 keeps the habit viable meanwhile).

### [REF] System Constraints

- Metric only: kg, 0.1 kg display precision, plausible range 30.0–250.0 kg (A1/A2).
- Domain invariant: at most one entry per calendar day (device-local date, A5); saving again for a day **replaces** that day's value.
- No future-dated entries.
- Mobile-first web; entry screen usable one-handed; touch targets ≥44 px; WCAG 2.2 AA basics (labels, contrast, focus).
- Durability: a confirmed save is never lost across restarts/redeploys (guardrail KPI: zero lost entries).
- Trend requirements are **behavioral only** (smoothness, gap robustness, responsiveness, determinism) — algorithm selection belongs to DESIGN.
- Product stance: single-purpose; no calorie/fitness/goal features, ever (see Out of Scope).
- Single user; no accounts. Access-protection mechanism for the hosted URL is a DESIGN decision (A6/OQ-1).

### [REF] User Stories

All stories: `job_id: track-true-weight-trend` (N:1 to `docs/product/jobs.yaml`). Persona: Clemens.

#### US-001: Log today's weight in seconds

`job_id: track-true-weight-trend` · Slice 01 (WS) · Must · ~1 day

##### Problem

Clemens steps off the scale at 06:45 with 30 seconds to spare. His current app makes him dismiss a promo and navigate three screens (~30–45 s) to log one number — and charges $30/month for it.

##### Elevator Pitch

- **Before**: Opens fitness app → dismisses promo → Log → Weight → types → saves; ~30–45 s.
- **After**: Taps the tracker icon on his phone home screen → entry screen opens with today (Mon 21 Jul) preselected and the weight field focused → types `82.4`, taps **Save** → sees "Saved: 82.4 kg — Mon 21 Jul" and the entry at the top of his history list.
- **Decision enabled**: "Is today's weigh-in captured, or do I need to re-enter it?" — the confirmation lets him pocket the phone certain the day's data point exists.

##### Domain Examples

1. *Happy path*: Mon 21 Jul, 06:45 — Clemens logs 82.4 kg; confirmation and history show it.
2. *Edge*: Same morning he realizes the scale was on carpet; re-saves 82.1 for today — the day now holds exactly one entry, 82.1.
3. *Error*: Types `824` (missed the decimal) — save is rejected with a range message; nothing is stored.

##### UAT Scenarios (BDD)

###### Scenario: Morning weight is captured in seconds

- **Given** it is Monday 21 July 2026 at 06:45 and Clemens has not logged today
- **When** he opens the tracker, types "82.4" and taps Save
- **Then** he sees "Saved: 82.4 kg — Mon 21 Jul" within 1 second
- **And** today's entry appears in his history

###### Scenario: An implausible typo is caught before it pollutes the record

- **Given** Clemens is on the entry screen
- **When** he types "824" and taps Save
- **Then** he sees an inline message that the value must be between 30.0 and 250.0 kg
- **And** no entry is stored and the field keeps his input for correction

###### Scenario: Re-saving today replaces rather than duplicates

- **Given** Clemens already logged 82.4 kg today
- **When** he enters 82.1 and taps Save
- **Then** today holds exactly one entry with value 82.1 kg

###### Scenario: A confirmed save survives a restart (anxiety path)

- **Given** Clemens saved 82.4 kg this morning
- **When** the app is restarted or redeployed and he reopens it that evening
- **Then** today's entry still shows 82.4 kg

###### Scenario: Empty submit does nothing destructive

- **Given** the weight field is empty
- **When** Clemens taps Save
- **Then** he is prompted for a value and nothing is stored

##### Acceptance Criteria

- [ ] Entry screen opens with today's date preselected and the weight field focused.
- [ ] Valid saves (30.0–250.0 kg, 0.1 precision) confirm within 1 s and appear in history.
- [ ] At most one entry per device-local calendar day; re-save replaces.
- [ ] Out-of-range and empty inputs are rejected inline with corrective guidance; store unchanged.
- [ ] Confirmed entries persist across restart/redeploy (zero loss).
- [ ] Baseline speed: open → saved achievable in ≤10 s (p90) on his phone.

##### Technical Notes

Greenfield; needs persistence + hosting decisions in DESIGN. Midnight attribution uses device-local date (A5).

#### US-002: Review weight history at selectable time scales

`job_id: track-true-weight-trend` · Slice 02 · Must · ~1 day

##### Problem

Clemens has weeks of entries but no way to see the shape of his history; a number list can't show whether June's dip was real or a blip.

##### Elevator Pitch

- **Before**: History exists only as a list of dated numbers (or inside the old paid app).
- **After**: Taps **Graph** → sees his raw weights plotted in kg with time-scale buttons `1M 3M 6M 1Y All` → taps `3M` → the plot redraws to the last three months, vacation days shown as gaps.
- **Decision enabled**: "Is that 79.1 on 15 Jul a real dip or a typo I should fix?" — spotting outliers and patterns in his own record.

##### Domain Examples

1. Clemens has 45 entries (3 Mar–21 Jul); `3M` shows late-Apr onward.
2. `All` shows the full record starting 3 Mar.
3. Vacation 10–17 Apr (no entries): the raw plot shows a gap — no zeros, no invented points.

##### UAT Scenarios (BDD)

###### Scenario: History is readable at the chosen time scale

- **Given** Clemens has 45 daily entries between 3 March and 21 July 2026
- **When** he opens the graph and selects "3M"
- **Then** only entries from the last three months are plotted with a kg axis

###### Scenario: The full record is one tap away

- **Given** the graph shows "3M"
- **When** he selects "All"
- **Then** the plot spans from his first entry (3 March) to today

###### Scenario: Missing days stay honest gaps

- **Given** Clemens logged nothing between 10 and 17 April (vacation)
- **When** he views any scale covering April
- **Then** those days show no data points — no zero values and no interpolated raw points

###### Scenario: Graph is phone-usable (@property)

- **Given** Clemens opens the graph on his phone over a mobile connection
- **Then** the graph is interactive within 2 seconds
- **And** axis labels and points are legible without zooming

##### Acceptance Criteria

- [ ] Time scales 1W / 1M / 3M / 6M / 1Y / All selectable; plot redraws to the chosen window.
- [ ] Exactly the stored entries are plotted; missing days render as gaps.
- [ ] Y-axis in kg, auto-ranged to the visible data.
- [ ] Graph interactive ≤2 s on phone; legible at mobile viewport.

##### Technical Notes

Charting approach is a DESIGN choice. Empty state (0–1 entries) must invite logging, not error.

#### US-003: Backfill and correct past days

`job_id: track-true-weight-trend` · Slice 03 · Must · ~0.5–1 day

##### Problem

Clemens forgot to log Sunday, and Tuesday's 79.1 was a fat-finger. Untrustworthy history poisons the trend he's about to rely on — and blocks hand-copying his old app's history.

##### Elevator Pitch

- **Before**: A missed or mistyped day is permanent; the record (and any trend on it) is quietly wrong.
- **After**: Taps a date (20 Jul) in history or a date picker → enters `82.6` → **Save** → the entry appears dated 20 Jul and the graph updates immediately.
- **Decision enabled**: "Can I trust this record as the basis for trend judgments — and seed it with my old app's history?"

##### Domain Examples

1. Backfill: forgot Sunday 20 Jul; adds 82.6 dated 20 Jul.
2. Correction: edits 15 Jul from 79.1 (typo) to 82.1; graph updates.
3. Boundary: tries to add 25 Jul (future) — rejected.

##### UAT Scenarios (BDD)

###### Scenario: A forgotten day is backfilled

- **Given** Clemens has no entry for Sunday 20 July 2026
- **When** he selects 20 July and saves 82.6 kg
- **Then** an entry dated 20 July with 82.6 kg appears in history and on the graph

###### Scenario: A typo from last week is corrected in place

- **Given** 15 July holds 79.1 kg (a mistyped value)
- **When** he edits 15 July to 82.1 kg and saves
- **Then** 15 July holds exactly one entry with 82.1 kg and the graph reflects it

###### Scenario: The future stays closed

- **Given** today is 21 July 2026
- **When** he attempts to save an entry for 25 July
- **Then** the save is rejected with a message that future dates cannot be logged

###### Scenario: Past-day validation matches today's rules

- **Given** he is editing 18 July
- **When** he enters "8.2" and taps Save
- **Then** the range message appears and 18 July is unchanged

##### Acceptance Criteria

- [ ] Any past date can receive a new entry or have its value replaced; one-entry-per-day invariant holds.
- [ ] Future dates rejected.
- [ ] Same validation (range, precision) as today-entry.
- [ ] Raw graph (and, once present, trend) reflect changes immediately.

##### Technical Notes

Deliberately sequenced before the trend slice to enable seeding real history. Entry deletion deferred (A7).

#### US-004: See the true trend through daily noise

`job_id: track-true-weight-trend` · Slice 04 · Must · ~1 day (with US-005)

##### Problem

Clemens's raw weight swings ±1 kg day to day (water, meals). After a sushi dinner the scale says +1.2 kg and his gut says "failure" — but nothing real changed. A simple moving average would also lie: it jumps when old points fall out of the window and breaks across his vacation gaps.

##### Elevator Pitch

- **Before**: Raw points only; every spike triggers a false verdict, and gaps make averages jump.
- **After**: Opens the graph → the default view shows a single smooth **trend line** in kg over the selected scale; after logging 83.6 post-sushi, the trend still reads ~82.4.
- **Decision enabled**: "Do I adjust what I'm doing, or stay the course?" — answered by trend direction, not this morning's number.

##### Domain Examples

1. Noise: stable ~82.3; logs 83.6 after sushi (22 Jul) → trend moves ≤0.3 kg.
2. Gap: vacation 10–17 Apr, resumes at 82.9 → trend continues smoothly through the gap, no jump or discontinuity.
3. Signal: sustained loss ~0.5 kg/week over 3 weeks in June → trend shows a steady decline beginning within ~a week of onset.
4. Correction: 15 Jul edited 79.1 → 82.1 → trend recomputes over the affected range.

##### UAT Scenarios (BDD)

###### Scenario: A restaurant-night spike is revealed as noise

- **Given** Clemens's trend has been stable around 82.3 kg for two weeks
- **When** he logs 83.6 kg the morning after a sushi dinner and opens the trend view
- **Then** the trend value moves by no more than 0.3 kg

###### Scenario: The trend survives a vacation gap (anxiety path)

- **Given** Clemens logged nothing between 10 and 17 April
- **When** he logs 82.9 kg on 18 April and views the trend
- **Then** the trend line is continuous across the gap with no jump or kink at the resumption point

###### Scenario: Real change shows up within a week

- **Given** Clemens's entries decline by about 0.5 kg per week for three consecutive weeks
- **When** he views the trend
- **Then** the trend shows a steady decline whose onset is visible within 7 days of the real change starting

###### Scenario: Corrections flow into the trend

- **Given** the trend was computed with the mistyped 79.1 kg on 15 July
- **When** he corrects 15 July to 82.1 kg
- **Then** the displayed trend recomputes and no longer shows the artificial dip

###### Scenario: The trend is deterministic (@property)

- **Given** any fixed set of entries
- **Then** every load renders an identical trend line for the same time scale

##### Acceptance Criteria

- [ ] Trend line rendered over the selected time scale; becomes available from the first entry.
- [ ] Smoothness: a single-day outlier of +1.5 kg moves the trend ≤0.3 kg.
- [ ] Gap robustness: up to 7 consecutive missing days produce no discontinuity or jump.
- [ ] Responsiveness: sustained 0.5 kg/week change visible in trend direction within 7 days.
- [ ] Deterministic: same entries → same trend, every load.
- [ ] Backfills/corrections recompute the trend over the affected range.

##### Technical Notes

Behavioral spec only — smoothing algorithm (e.g., exponential family à la Hacker's Diet) is a DESIGN-wave choice constrained by these ACs.

#### US-005: Toggle between trend and raw views

`job_id: track-true-weight-trend` · Slice 04 · Must · included in Slice 04's day

##### Problem

The trend answers "am I progressing?", but sometimes Clemens needs the raw truth — to cross-check a suspicious point or relive last week's sushi honestly.

##### Elevator Pitch

- **Before**: One fixed graph; verifying whether an alarming trend wiggle is data or smoothing means squinting at numbers.
- **After**: Taps the **Raw** toggle on the graph → same 3M window redraws with raw points; taps **Trend** → smooth line returns, scale untouched.
- **Decision enabled**: "Is this trend movement backed by real data points, or driven by one outlier I should correct?"

##### Domain Examples

1. In Trend/3M, taps Raw → raw points for the same 3M window.
2. Taps Trend again → trend line, still 3M.
3. Opens the app fresh → Trend is the default view (A4).

##### UAT Scenarios (BDD)

###### Scenario: Toggling preserves the time window

- **Given** Clemens is viewing the trend at "3M"
- **When** he taps "Raw"
- **Then** raw entries for the same three-month window are plotted

###### Scenario: Round trip is lossless

- **Given** he toggled to Raw at "3M"
- **When** he taps "Trend"
- **Then** the trend line returns at "3M" with no scale reset

###### Scenario: Trend is the default lens

- **Given** Clemens opens the graph in a new session
- **Then** the trend view is shown first

##### Acceptance Criteria

- [ ] One-tap toggle Trend↔Raw on the graph screen; state change <100 ms feedback.
- [ ] `selected_time_scale` is shared state: toggling never changes the window.
- [ ] Default view on open is Trend (A4).

#### US-006: From pocket to logged in five seconds

`job_id: track-true-weight-trend` · Slice 05 · Should · ~0.5–1 day

##### Problem

US-001 makes logging possible in ≤10 s; the habit that must survive 365 mornings a year deserves ≤5 s. Every residual tap or keyboard fumble is compound interest against the streak.

##### Elevator Pitch

- **Before**: Open browser → find tab/bookmark → wait → tap field → switch keyboard to numbers → type → save (~10 s).
- **After**: Taps the tracker's **home-screen icon** → screen is interactive ≤2 s with the field already focused and a **decimal keypad** showing, yesterday's 82.6 visible as reference → types `82.4`, taps Save — stopwatch says 4 s.
- **Decision enabled**: "Keep or kill the habit tooling" — with median ≤5 s there is no friction excuse left; also the final input to cancelling the old subscription.

##### Domain Examples

1. Home-screen launch on his phone: interactive ≤2 s, field focused, decimal keypad up.
2. Reference context: placeholder shows "yesterday: 82.6 kg" for sanity-checking.
3. Week-long self-measurement (21–27 Jul): median open→saved 4.2 s, p90 7 s → target met.

##### UAT Scenarios (BDD)

###### Scenario: Launch drops him straight into typing

- **Given** the tracker is on Clemens's phone home screen
- **When** he taps the icon
- **Then** the entry screen is interactive within 2 seconds
- **And** the weight field is focused with a decimal keypad shown

###### Scenario: Yesterday anchors today

- **Given** Clemens logged 82.6 kg yesterday
- **When** the entry screen opens
- **Then** "yesterday: 82.6 kg" is visible next to the input as reference

###### Scenario: The five-second budget holds in real life (@property)

- **Given** seven consecutive days of real morning use
- **Then** median time from icon tap to save confirmation is ≤5 s and p90 ≤10 s

##### Acceptance Criteria

- [ ] Installable/launchable from phone home screen.
- [ ] Interactive ≤2 s on his phone over mobile connection; field auto-focused; numeric/decimal keypad.
- [ ] Yesterday's value shown as reference.
- [ ] Measured median open→saved ≤5 s over 7 real days (KPI-1 instrumentation: client timing stored with entry).

### [REF] Out of Scope

Calories, exercise, workouts, goals/targets/goal lines, predictions, streak gamification, notifications/reminders, multi-user accounts, imperial units, native mobile apps, social/sharing, automated import from the old app (OQ-2), entry deletion (A7 — edit covers corrections), data export UI (durability guaranteed; export deferred, OQ-3).

### [REF] Walking Skeleton Strategy

Strategy: **single deployable, direct-to-production, no scaffolding** (simplest class — greenfield, single user, one deployable unit; no feature flags, no staged environments). Slice 01 ships to a phone-reachable production URL on day 1; every subsequent slice deploys the same day it's built; all data is production data from the first entry; dogfood moment = that morning's (or evening's) real weigh-in. WS covers UI → domain rule (one-entry-per-day, validation) → persistence → read-back, proving the full vertical before any graph/trend work.

### [REF] Driving Ports

Solution-neutral capability interfaces (hexagonal naming; DESIGN owns adapters/tech):

- **WeightLogging** (driving): `recordOrReplace(date, weight_kg)` — enforces one-entry-per-day, range validation, no-future rule. Used by US-001, US-003, US-006.
- **WeightHistory** (driving): `entriesIn(dateRange)` — raw record for lists and graphs. Used by US-001, US-002, US-005.
- **TrendProjection** (driving): `trendSeriesIn(dateRange)` — derived, deterministic, gap-robust smoothed series. Used by US-004, US-005.
- **EntryStore** (driven, noted for DESIGN): durable persistence of `{date, weight_kg}` — single source of truth for the `weight_entry` shared artifact.

### [REF] Pre-Requisites

None blocking DESIGN. For DELIVER: DESIGN must decide hosting target, persistence, access protection (OQ-1), and trend algorithm satisfying US-004's behavioral ACs; Clemens's phone available for same-day dogfooding (yes).

### [REF] Outcome KPIs

**Objective**: By end of August 2026, Clemens's entire weight-tracking habit runs on his own tool — faster than the paid app and trusted enough to cancel it.

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|-----|-----------|-------------|----------|-------------|------|
| 1 | Clemens | completes log, icon tap → save confirmation | median ≤5 s, p90 ≤10 s | ~30–45 s (old app) | client-side timing stored with each entry | Leading |
| 2 | Clemens | logs his weight | ≥6 of 7 days/week over 4 consecutive weeks | ~5–6/7 self-reported in old app | entry count per calendar week from entry store | Leading |
| 3 | Clemens | opens the trend view | ≥3 sessions/week | 0 (no trusted trend today) | trend-view open counter | Leading |
| 4 | Clemens | cancels the $30/month subscription | within 30 days of Slice 04 shipping | subscription active | subscription status, self-verified | Lagging |

- **North Star**: KPI-2 (daily logging adherence on the owned tool) — activation-stage metric; it causally precedes trust (KPI-3) and cancellation (KPI-4).
- **Guardrails**: zero lost or corrupted entries (ever); graph interactive ≤2 s on phone; trend determinism (identical inputs → identical line).
- **Hypothesis**: We believe a ≤5 s, one-entry-per-day logger with a gap-robust trend for Clemens will make him log ≥6/7 days weekly on the owned tool and cancel the $30/month subscription within 30 days of the trend shipping.
- **Measurement plan**: timing + view counters are client events persisted alongside entries (instrumentation requirement carried in US-006 AC and DEVOPS handoff); adherence derived from the entry store; KPI-4 checked manually at day 30.

### [REF] DoR Validation

All 9 items validated per story; evidence cited from this document.

| DoR Item | US-001 | US-002 | US-003 | US-004 | US-005 | US-006 | Evidence |
|----------|--------|--------|--------|--------|--------|--------|----------|
| 1. Problem clear, domain language | PASS | PASS | PASS | PASS | PASS | PASS | Each `Problem` names Clemens's concrete pain (06:45, sushi spike, forgotten Sunday) |
| 2. Persona specific | PASS | PASS | PASS | PASS | PASS | PASS | Single persona `clemens` with context (phone-first, 82 kg range, $30/month) |
| 3. 3+ domain examples, real data | PASS | PASS | PASS | PASS | PASS | PASS | Real dates/values (82.4 on 21 Jul, 79.1 typo on 15 Jul, 10–17 Apr gap) |
| 4. UAT 3–7 scenarios G/W/T | PASS (5) | PASS (4) | PASS (4) | PASS (5) | PASS (3) | PASS (3) | Counts in parentheses; anxiety + habit + property paths covered |
| 5. AC derived from UAT | PASS | PASS | PASS | PASS | PASS | PASS | Each AC list maps 1:1 to scenarios plus quantified thresholds |
| 6. Right-sized (1–3 d, 3–7 sc.) | PASS | PASS | PASS | PASS | PASS | PASS | All ≤1 day, 3–5 scenarios each |
| 7. Technical notes/constraints | PASS | PASS | PASS | PASS | PASS | PASS | Notes per story + System Constraints section |
| 8. Dependencies resolved/tracked | PASS | PASS | PASS | PASS | PASS | PASS | Slice ordering = dependency order; US-005 depends on US-002+US-004 (same slice); no external deps |
| 9. Outcome KPIs, numeric targets | PASS | PASS | PASS | PASS | PASS | PASS | KPI table above; every story traces to KPI-1/2/3/4 |

**DoR Status: PASSED (6/6 stories, 9/9 items).**

**Requirements completeness score: 0.96** — functional (all six requested behaviors covered), NFRs quantified (speed, load, durability, determinism, accessibility minimums), business rules explicit (one/day, range, precision, no-future). Deductions: access-protection UX unresolved (OQ-1), historical-import undecided (OQ-2).

### [REF] DoD 9-Item Checklist

Per story, at DELIVER completion:

1. All UAT scenarios green (automated).
2. Supporting unit/integration tests green.
3. Code refactored; no obvious debt.
4. Code reviewed (self-review with reviewer agent — solo project).
5. Merged to main.
6. Deployed to the phone-reachable production URL.
7. Dogfooded same day with a real entry (production data, per carpaccio rule).
8. KPI instrumentation for the story's metrics emitting.
9. Story demonstrable end-to-end on the phone.

### [REF] Wave Decisions Summary

Locked: D1–D5 (above). Assumptions made autonomously (subagent mode — no user interaction available):

- **A1** Plausible weight range 30.0–250.0 kg for validation.
- **A2** 0.1 kg precision (matches consumer scales).
- **A3** Time scales: 1W / 1M / 3M / 6M / 1Y / All.
- **A4** Default graph view = Trend once available.
- **A5** Calendar day = device-local date (a 00:10 log counts as the new day).
- **A6** No accounts/multi-user; some access protection for the hosted URL expected, mechanism = DESIGN decision.
- **A7** Entries are editable, not deletable, in v1.
- **A8** No automated import of old-app history in v1; Slice 03 backfill enables manual seeding.

Open questions for the user: **OQ-1** what level of access protection for the public URL? **OQ-2** import historical data from the old app (export file?) — would strengthen trend validation. **OQ-3** is a data-export/backup affordance wanted in v1, or is durable hosting enough to quiet the data-loss anxiety? **OQ-4** midnight semantics confirm (A5). **OQ-5** confirm A3 time scales.

Resolutions (2026-07-22): **OQ-1 RESOLVED** — user chose simplest option: passphrase protection. No accounts/passwords in v1; multi-user webapp with accounts is an acknowledged future possibility, explicitly out of scope now (A6 refined: mechanism = passphrase; DESIGN decides implementation details). **OQ-2 RESOLVED** — no old-app import, and no pressure to hand-seed history ("don't worry about backfill"); A8 confirmed. Consequence: the slice-03-before-trend ordering rationale (seed data for trend validation) is void — US-003 (edit/add past days) remains in scope as a stated requirement, but DELIVER may order trend (slice 04) before backfill (slice 03); trend validates on freshly accumulated data. **OQ-3 RESOLVED** — no export/backup in v1; durable hosting suffices. **OQ-4 RESOLVED** — A5 confirmed (device-local date; 00:10 log = new day). **OQ-5 RESOLVED** — time scales amended to 1W / 1M / 3M / 6M / 1Y / All (A3 updated; US-002 AC, slice-02 brief, and journey YAML updated in place).

Risk notes: missing DIVERGE wave accepted (problem pre-validated, user = customer); riskiest product assumption = trend trustworthiness (mitigated by slice order 03→04); technical risk = smoothing behavior vs. AC thresholds (DESIGN to select algorithm against US-004 ACs).

## Wave: DESIGN

Architect: solution-architect (Morgan), 2026-07-22. Mode: Propose (user selected among options). SSOT bootstrapped: `docs/product/architecture/brief.md` + ADR-001…005.

### [REF] DDD Assessment

| # | Question | Verdict |
|---|---|---|
| D-01 | Bounded contexts | ONE (weight tracking). No context map; no DDD strategic machinery warranted for a single-job, single-user domain. |
| D-02 | Aggregates | `DailyWeightEntry` keyed by `date` is the only consistency boundary (one-per-day invariant = single-row upsert). Trivial — no aggregate framework, plain pure upsert-resolution function. |
| D-03 | Event Sourcing / CQRS | REJECTED. Simple CRUD + derived read (trend recomputed on read, never stored). No audit/temporal-query requirement. |
| D-04 | Ubiquitous language | `entry`, `trend` (smoothed), `raw`, `time scale`, `backfill`, `correction` — carried from DISCUSS unchanged. |

### [REF] Component Decomposition

Authoritative table (with contract shapes + probes): `docs/product/architecture/brief.md` § Component Decomposition and Ports. Summary: Domain Core (pure: validation, upsert resolution, windowing, Kalman+RTS trend) · Web UI (Jinja2 + uPlot + PWA shell) · AccessGate middleware · EntryStore (SQLite adapter) · Clock adapter · Composition root (wire → probe → serve; probe failure ⇒ `health.startup.refused`).

### [REF] Driving Ports

| Port | Contract shape | Interface | Stories |
|---|---|---|---|
| `WeightLogging` | bounded-change (one `{date}` row + one telemetry event) | `record_or_replace(date, kg, entry_ms) -> Saved \| Rejected` | US-001, US-003, US-006 |
| `WeightHistory` | read-only (no write methods) | `entries_in(range)`, `yesterday()` | US-001, US-002, US-005, US-006 |
| `TrendProjection` | read-only, derived-never-stored | `trend_series_in(range) -> [TrendPoint]` — daily grid, Kalman+RTS smoothed (ADR-004) | US-004, US-005 |
| `AccessGate` | read-only per request | passphrase login → signed cookie; guards all routes | all (access precondition) |

### [REF] Driven Ports and Adapters

| Port | Adapter | Probe (startup, mandatory) |
|---|---|---|
| `EntryStore` | SQLite (WAL, `synchronous=FULL`) on Fly volume; Litestream sidecar → R2 | integrity_check, WAL+FULL asserted, sentinel write→fsync→readback, statfs ≠ tmpfs |
| `Clock` | system UTC clock | year sanity ∈ [2026, 2100] |
| (secrets) | Fly env: `PASSPHRASE_HASH`, `SESSION_SIGNING_KEY`, R2 creds | present + parseable, else refuse start |

### [REF] Technology Choices

Python 3.12 · FastAPI ≥0.116 · uvicorn ≥0.35 · Jinja2 3.1 · uPlot 1.6 · SQLite ≥3.45 (stdlib) · Litestream 0.3.13 · argon2-cffi 25.1 · itsdangerous 2.2 · pytest 8 + hypothesis 6 · import-linter 2.x · Fly.io shared-cpu-1x + 1 GB volume + Cloudflare R2 (~$2–3/mo). All OSS (MIT/BSD/Apache/PSF/public domain); exact patches pinned in lock files at DELIVER. Rationale + rejected options: ADR-001/002.

### [REF] Decisions

| # | Decision | ADR |
|---|---|---|
| D-05 | Modular monolith, ports-and-adapters, single deployable | brief.md |
| D-06 | Stack/hosting = Option A (Python/FastAPI on Fly.io); B (Cloudflare/D1), C (Go/VPS) rejected | ADR-001 |
| D-07 | Durability = SQLite WAL+FULL + Litestream→R2; confirm-after-commit; probes refuse start on lying substrate | ADR-002 |
| D-08 | Access = single passphrase, argon2id hash in secret, signed HttpOnly cookie 90 d, rate-limited login | ADR-003 |
| D-09 | Trend = local-level Kalman + RTS smoother, daily grid, r=0.20 kg², q≈0.00222 kg² (α-equiv 0.1), Huber δ=1.0 kg, missing day = predict-only; display SMOOTHED series (retrospective revision intentional); full O(n) recompute per read/edit. Supersedes entry-sequence EMA draft (kept as fallback Spec C). Evidence: `docs/research/algorithms/weight-trend-smoothing-comprehensive-research.md` | ADR-004 |
| D-10 | Paradigm = Functional Core / Imperative Shell; crafter = nw-functional-software-crafter | ADR-005 |
| D-11 | PWA = manifest + minimal service worker (Android install, app-shell cache only, no offline queueing) | ADR-001 |

### [REF] Reuse Analysis

**Greenfield — explicitly empty.** Full-tree scan (2026-07-22): repository contains zero application code (docs only). No existing components, no overlap candidates; every component is justified by "no existing alternative exists." Contract shapes, mutation universes, and assertion mechanisms for all new components are declared in brief.md's component table (pure-function → PBT; bounded-change → declared mutation set + AT assertions; probes → startup enforcement).

### [REF] Open Questions (deferred to DISTILL/DELIVER)

1. **Timezone skew on "no future date"** (DISTILL): client submits device-local date (A5); server sanity-bound = client date ≤ server UTC date + 1 day. Needs an explicit scenario.
2. **90-day session lifetime** (user confirm at DISTILL): a login prompt at 06:45 would blow the ≤5 s budget; 90 d proposed.
3. **Gap-rendering oracle** (DISTILL): trend now has values on gap days and **revises the recent past as entries arrive** — the gap/continuity oracle must assert smoothed continuity of the currently rendered line for a fixed entry set, NOT immutability of previously rendered values. Raw view remains immutable ground truth.
4. **uPlot final pick** (DELIVER): default uPlot 1.6; swap allowed within the ≤2 s interactive AC.
5. **Uncertainty band** (DELIVER, optional): smoothed variance is available for free; render decision deferred.
6. **Parameter sanity pass** (post-dogfood): verify σ_ε ≈ 0.45 kg against real first-difference variance; any change to r is a versioned constant change (determinism preserved), never automatic re-estimation.

### Changed Assumptions

- **DISCUSS said** (Priority Rationale #3): Slice 03 "pulled *ahead* of trend deliberately: backfilling lets Clemens hand-copy ~30–60 days of history from the old app, so the trend slice's riskiest assumption … is testable immediately"; and A8: "No automated import of old-app history in v1; Slice 03 backfill enables manual seeding."
- **Now**: OQ-2 resolution (2026-07-22) — no old-app import and no hand-seeding pressure ("don't worry about backfill"). New assumption: **slice ordering is free** — DELIVER may ship Slice 04 (trend) before Slice 03 (backfill); the trend validates on freshly accumulated production data. US-003 remains in scope as a stated requirement. Slice-03/04 dogfood ACs that mention "seeding ≥30 days" are stale and should be amended at DISTILL.
- **Rationale**: OQ-2 resolution, feature-delta Resolutions section, 2026-07-22.

## Wave: DEVOPS

Platform architect: nw-platform-architect (Apex), 2026-07-22. Decisions 1–9 locked upstream (Fly.io single machine · no orchestration · GitHub Actions · greenfield · minimal custom observability · recreate deploys · no continuous-learning infra · trunk-based · per-feature mutation testing). Machine artifacts: `docs/feature/weight-trend-tracker/environments.yaml` (DISTILL Mandate 4), `docs/product/kpi-contracts.yaml`. Ops docs: `docs/product/architecture/runbook-restore.md`, `docs/product/architecture/secret-setup.md`. Peer review: Forge (nw-platform-architect-reviewer) needs_revision cycle 1 addressed 2026-07-22 (C-001..003 fixed, H-001..005 fixed/dispositioned, M-001..004 documented).

### [REF] Environment Matrix

| Env | Platform | Runtime | Data | Secrets | Purpose |
|---|---|---|---|---|---|
| `local-dev` | macOS (Clemens's machine) | uv-managed Python 3.12 venv; `uvicorn` direct (no Litestream required) | local SQLite file (same WAL + `synchronous=FULL` pragmas as prod) | `.env` (git-ignored); dev-only passphrase hash + signing key | development, pre-commit/pre-push gates, per-feature mutation runs |
| `ci` | GitHub Actions `ubuntu-latest` | uv-installed pinned deps; ephemeral | ephemeral SQLite (tmp dir); restore-drill job pulls replica from R2 to scratch | GitHub Actions secrets: `FLY_API_TOKEN`, read-only R2 creds (drill only); no app secrets needed for tests | quality gates on every push to main; deploy on green; scheduled restore drill |
| `production` | Fly.io single app, single region, `shared-cpu-1x`, 1 GB volume at `/data` | one Docker container; `litestream replicate -exec "uvicorn …"` as PID 1 | SQLite on `/data` (WAL, FULL); Litestream → Cloudflare R2 | Fly secrets: `PASSPHRASE_HASH`, `SESSION_SIGNING_KEY`, R2 credentials | the only serving environment; all data is production data from entry 1 (no staging — walking-skeleton strategy) |

### [REF] CI/CD Pipeline Outline

Triggers: **push to `main`** (full pipeline + deploy) · **pull request** (quality gates only, no deploy — for optional short-lived branches) · **weekly cron** (restore drill, independent job) · manual `workflow_dispatch` for deploy/drill re-runs.

Stages (push to main; fail-fast, deploy requires all green):

1. **Static gates** — `ruff check` + `ruff format --check` · `mypy --strict` · `import-linter` (core-imports-nothing-outward layer contract).
2. **Tests** — `pytest`: unit + property (Hypothesis) + acceptance suite against ephemeral SQLite. Single job; suite is small enough that split/parallelization is unjustified complexity — revisit only if commit-stage wall-clock exceeds ~5 min (M-001).
3. **Deploy** — `fly deploy` (Dockerfile build via Fly builders), gated on 1–2 green; GitHub Actions concurrency group `production-deploy` (serialize; recreate strategy on a single machine must never overlap).
4. **Post-deploy smoke** — poll `GET /healthz` until 200 with `status: ok` (probes passed, replication reporting) within 3 min; failure ⇒ pipeline red + rollback procedure (below).

Scheduled **restore drill** (weekly cron, the contract test for the only external integration, R2): `litestream restore` to CI scratch → `PRAGMA integrity_check` = ok → row-count sanity. **State mechanism (C-001)**: the drill persists `drill-state.json` (`{run_ts, entries_count, restored_wal_ts}`) as a GitHub Actions artifact named `restore-drill-state`, retention **90 days** (≫ 7-day cadence). Compare procedure: download the most recent `restore-drill-state` artifact; assert `entries_count_restored >= previous.entries_count` (valid invariant: entries are replace-only, never deleted). **First run**: no prior artifact found ⇒ skip comparison, record baseline, log `drill.baseline.recorded`. Every run uploads the new state artifact. **Point-in-time exercise (H-002)**: every 4th run (monthly) additionally restores with `litestream restore -timestamp <now − 7 days>` to a second scratch path and integrity-checks it, proving the PITR path used by the data-rollback contract — not just latest-generation restore. Drill failure ⇒ red workflow + GitHub email notification: durability guardrail no longer discharged → follow `docs/product/architecture/runbook-restore.md`.

**Explicit split**: per-feature mutation testing runs **locally in the DELIVER cycle** (after refactoring, scoped to modified files, ≥80% kill gate) — it is NOT a CI stage. CI stays fast (target <5 min to deploy); mutation depth lives at the point of change.

Local gates mirror commit stage: pre-commit = ruff + AST `probe()`-presence hook (brief.md dependency-rule enforcement); pre-push = ruff + mypy + import-linter + pytest.

### [REF] Monitoring Contracts

Full machine-readable contract: `docs/product/kpi-contracts.yaml`.

| KPI | Instrument | Storage | Query surface | Alert |
|---|---|---|---|---|
| KPI-1 entry timing (median ≤5 s, p90 ≤10 s) | client-measured `entry_ms` (icon tap → save confirm) submitted with save; persisted on the entry + `entry_logged` event | `entries.entry_ms` + `events` table (same SQLite DB) | `/stats` read-only page (AccessGate-protected): 7-day rolling median/p90 | none automated — weekly manual review on `/stats` (single user; paging himself is noise) |
| KPI-2 adherence (≥6/7 days over 4 consecutive weeks) — **North Star** | none needed — derived from the entry record itself | `entries` table | `/stats`: entries per ISO week, last 8 weeks, 6/7 threshold marker | none automated — weekly manual review |
| KPI-3 trend-view opens (≥3 sessions/week) | `trend_view_opened` event emitted server-side on trend page render | `events` table (append-only) | `/stats`: opens per week | none automated — weekly manual review |
| KPI-4 subscription cancelled (≤30 d after Slice 04) | manual, self-verified | n/a | day-30 checklist item in iteration close | calendar reminder, manual |
| Guardrail: zero lost entries | `/healthz` replication-lag check + weekly restore drill (monthly PITR variant) | Litestream metrics + R2 replica; `restore-drill-state` CI artifact | `/healthz` JSON; drill workflow history | UptimeRobot email: `/healthz` non-200 or replication lag > 15 min (5-min poll, RPO statement in `kpi-contracts.yaml`); drill failure = CI email → `runbook-restore.md` |
| Guardrail: graph interactive ≤2 s · trend determinism | acceptance tests (`@property`) in CI, every push | CI history | CI status | red main = deploy blocked |

Product-KPI thresholds are deliberately **not** CI gates (H-003 disposition): synthetic timing in CI proves nothing about real phone entry speed; CI asserts only that instrumentation is *wired* (acceptance tests over `entry_ms` persistence and event emission). Threshold judgment stays with the weekly human review.

### [REF] Deployment Strategy and Rollback Contract

**Recreate** (Decision 6): `fly deploy` stops the old machine and starts the new image against the same `/data` volume; brief downtime is acceptable for a single user, and a single machine with an attached volume makes rolling/blue-green structurally unavailable anyway. Startup is self-gating: the composition root probes all driven adapters before serving; a bad release refuses traffic (`health.startup.refused`) and the smoke stage catches it. **Rollback contract — code**: `fly releases` → `fly deploy --image registry.fly.io/<app>@<previous-digest>` (or `fly releases revert` where supported) restores the prior image against the untouched volume. **Image reproducibility (H-005)**: Fly stores the built image per release in its registry — rollback re-uses the stored image ref, never a rebuild; no bit-for-bit reproducible build needed. **Rollback-mismatch guard (schema)**: schema changes are additive-only and recorded in a `schema_version` table; the EntryStore startup probe refuses start if DB schema version > highest version the running code knows — so an accidental rollback across a schema change fails safe instead of corrupting (see Pre-Requisites 2a). **Rollback contract — data**: Litestream point-in-time restore (`litestream restore -timestamp <t>` from R2) for corruption/bad-write scenarios; seconds-level loss window per ADR-002; procedure exercised by the restore drill (weekly latest-generation + monthly PITR variant), so the rollback path is continuously tested, not aspirational; operator procedure: `docs/product/architecture/runbook-restore.md`. **Volume-presence pre-deploy check (H-004 disposition)**: no separate pre-deploy check — a missing/detached/ephemeral volume is already caught fail-safe at startup by the EntryStore probe (sentinel write→fsync→readback on `/data`, statfs ≠ tmpfs) ⇒ `health.startup.refused` ⇒ red smoke stage; accepted as sufficient at solo scale. Preconditions asserted before any deploy: Fly secrets present (probes refuse start otherwise), one machine only.

### [REF] Mutation Testing Strategy

Per-feature (Decision 9; project <50k LOC, per-slice delivery cadence): runs locally after the refactor step of each delivery, scoped to files modified in the slice, kill-rate gate ≥80%. Tool selection (e.g., `mutmut` or `cosmic-ray`) at DELIVER. Persisted to project `CLAUDE.md` § Mutation Testing Strategy. Not in CI (see pipeline split above).

### [REF] Observability Stack

Minimal custom (Decision 5) — no Prometheus/Grafana/Datadog. (a) Structured JSON logs to stdout, captured by Fly; canonical event names: `health.startup.refused`, `entry.saved`, `auth.login.{ok,rejected,rate_limited}`, `trend_view.opened`. (b) `/healthz` (unauthenticated, no data exposure): overall status, last successful Litestream replication timestamp/lag, last startup probe result. (c) UptimeRobot free tier polls `/healthz` every 5 min → email alert on down or lag > 15 min — the single alert channel. (d) KPI query surface = `/stats` read-only page over the `events` + `entries` tables (behind AccessGate); SQL snippets documented in `kpi-contracts.yaml` double as an ad-hoc notebook interface via `sqlite3` against a restored replica. Alert routing is **deliberately email-only** (M-002): one operator, one channel he already reads; SMS/push/PagerDuty-style escalation is a documented future option, not a gap. Secrets setup and rotation procedures: `docs/product/architecture/secret-setup.md`.

### [REF] Branching Strategy

Trunk-based (Decision 8): `main` is the only long-lived branch; short-lived branches optional (PR trigger runs gates without deploying); every push to `main` runs the full pipeline and deploys on green; no release branches, no environment promotion (production is the only environment); version = deployed commit SHA (Fly release history is the ledger). Branch protection on `main`: required status check = the quality-gates workflow.

### [REF] Coexistence Matrix

| Existing mechanism | New mechanism | Rule |
|---|---|---|
| nWave git hooks (workflow tracking) | project pre-commit/pre-push hooks (ruff, AST probe check, mypy, pytest) | must_not_break — chain hooks (pre-commit framework alongside existing hook scripts), never overwrite `.git/hooks` entries |
| CLAUDE.md § Development Paradigm | § Mutation Testing Strategy | append-only; existing sections untouched |
| Litestream (PID 1) | app server (uvicorn child via `-exec`) | Litestream owns process lifecycle; app must exit non-zero on fatal error so Fly restarts the machine |
| Fly volume `/data` | recreate deploys | volume must survive every redeploy; deploy never recreates/detaches the volume |

### [REF] Pre-Requisites

DESIGN constraints the platform work must satisfy (contract with DELIVER; all traced to brief.md/ADRs):

1. **Startup invariant**: wire → probe all driven adapters → serve; any probe failure = `health.startup.refused` structured log + no traffic (composition root, brief.md).
2. **EntryStore probe**: `PRAGMA integrity_check`; WAL + `synchronous=FULL` asserted; sentinel write→fsync→readback; statfs ≠ tmpfs (ADR-002).
   - **2a. Schema-version guard (C-003)**: DB carries a `schema_version` table (single row, integer version + applied_ts log). Migrations are additive-only, applied idempotently at startup before probing, each recorded in `schema_version`. The probe asserts: app code's known schema version ≥ DB version; if **DB version > highest version the app code knows** (i.e., a rollback landed behind a schema change) ⇒ refuse start (`health.startup.refused`, probe=`entry_store.schema_version`). Cross-wave responsibility, stated explicitly: this runtime enforcement is a **DEVOPS pre-requisite implemented by DELIVER** in the composition root / EntryStore probe — it extends, not replaces, the DESIGN wire→probe→serve invariant.
3. **Secrets**: `PASSPHRASE_HASH`, `SESSION_SIGNING_KEY`, R2 credentials as Fly secrets only — never in repo, never in CI logs; startup refuses without them (ADR-003). Generation, `fly secrets set` commands, `.env.example` spec, and rotation consequences: `docs/product/architecture/secret-setup.md` (H-001).
4. **Litestream liveness**: `/healthz` replication-lag reporting + restore drill in CI (weekly latest + monthly PITR — ADR-002's handoff, the R2 contract test); operator recovery procedure in `docs/product/architecture/runbook-restore.md` (C-002).
5. **KPI instrumentation**: append-only `events` table in the same SQLite DB; `entry_ms` on entries; `/stats` read-only query surface (brief.md § Observability, `kpi-contracts.yaml`).
6. **Deploy artifacts owned by DELIVER**: Dockerfile (`litestream replicate -exec` supervisor; **Litestream pinned to exactly 0.3.13** in the Dockerfile, not `latest` — M-003), `fly.toml`, `.github/workflows/*` implementing the pipeline outline above, pre-commit/pre-push hook configs — specified here, implemented in DELIVER (slice 01 carries the skeleton pipeline).

## Wave: DISTILL

Acceptance designer: nw-acceptance-designer (Quinn), 2026-07-22. Density: lean (Tier-1 [REF] only, per D5 + global config). Scenario SSOT = the `.feature` files; these sections are pointers + structured summaries. ADR-025: all ATs authored here as RED scaffolds; DELIVER unskips one-at-a-time.

### [REF] Scenario List

49 Gherkin scenarios (57 test instances after outline expansion) + 14 pure-core PBT properties = 71 collected tests. Error/edge-tagged: 21/49 (43%, ≥40% gate met). Every scenario carries `@contract-shape:` + `@US-N` traceability + `@driving_port`.

| File | Scenarios | Notable tags |
|---|---|---|
| `walking-skeleton.feature` | 1 | `@walking_skeleton @driving_port @driving_adapter @real-io @US-001` (bounded-change) |
| `access-protection.feature` | 9 | wrong/absent passphrase, save-while-locked, throttling, 89/91-day session, unauth health, broken-store refusal (`@real-io`) |
| `milestone-1-log-todays-weight.feature` | 9 (13 inst.) | range boundary outlines (29.9/30.0/250.0/250.1/824/8.2), precision, not-a-weight, empty submit, replace-not-duplicate, restart durability (`@real-io @adapter-integration`), midnight/device-day |
| `milestone-2-review-history.feature` | 7 (11 inst.) | window outline over 1W/1M/3M/6M/1Y, gaps-stay-gaps, empty/single record, ≤2 s readiness (`@property @kpi`, G-2) |
| `milestone-3-backfill-and-correct.feature` | 8 | backfill, in-place correction, future closed, past-day validation, idempotent re-save, skew +1 accepted / +2 rejected, unrecognisable date |
| `milestone-4-trend-through-noise.feature` | 10 | sushi spike ≤0.3 kg, gap continuity (bounded step + daily-grid coverage), decline ≤7 d, correction recompute, determinism (`@property @kpi`, G-3), first-entry trend, toggle ×2, default lens, trend-view counter (`@kpi @real-io`) |
| `milestone-5-five-second-entry.feature` | 5 | ready-for-typing, yesterday anchor, no-yesterday, home-screen install, speed report (`@property @kpi @real-io`, KPI-1) |
| `properties/test_trend_math_properties.py` | 7 PBT | ADR-004 oracles at layer 1 (pure core): determinism, order-invariance, daily-grid, spike ≤0.3, Huber clip (any magnitude), gap bounded-step, decline-visible-in-7d — exact constants R=0.20, q=R·α²/(1−α), α=0.10, δ=1.0 in `core/trend.py` |
| `properties/test_validation_properties.py` | 7 PBT | boundary acceptance/rejection, hostile-input never-crash + closed reason set (C6c), skew-bound dates, upsert replace/idempotency with state-delta universe |

### [REF] Walking Skeleton Declaration

ONE `@walking_skeleton` scenario ("Morning weight is captured in seconds and lands in the record") through the production composition root (`weight_tracker.composition.build_app`) via real HTTP (TestClient) + real SQLite on tmp_path. Greenfield, SPIKE skipped: the WS is authored RED (no green skeleton exists) and is the first scenario DELIVER drives to GREEN. Strategy per Architecture of Reference (project policy): driving = real protocol, driven-internal = real SQLite, driven-external = FakeClock.

### [REF] Adapter Coverage

| Driven adapter | @real-io scenario | Covered by |
|---|---|---|
| EntryStore (SQLite `entries`) | YES | WS (real file) + "A confirmed save survives a restart" (reopens same file, fresh composition) + "A record that cannot be stored safely refuses to open" (probe/refusal on unwritable home) |
| TelemetryStore (SQLite `events`) | YES | "Opening the trend counts toward engagement" (KPI-3) + "A week of timed mornings yields the speed report" (KPI-1) — events read back via /stats |
| Clock | FAKE (by policy) | FakeClock, manual advance — midnight, skew, 89/91-day session scenarios |
| Litestream → R2 | NOT MODELED | deployment-level; contract test = weekly restore drill (DEVOPS). ATs cannot model host loss / replication lag / fsync-lying substrates beyond the statfs/pragma probe contract. |

### [REF] Tier B Decision (Mandate 10)

SKIPPED, documented: journeys chain ≥3 scenarios, but the shell state space is a single date→kg map with one mutating op (upsert) — a state-machine model over in-memory doubles would re-model a trivial upsert. Domain-rich input exploration lives at layer 1-2 instead: 14 Hypothesis properties over the pure core (trend + validation), where iteration is cheap (Mandate 9). No `tier_b/` directory is emitted.

### [REF] Scaffolds (Mandate 7)

RED-ready, `__SCAFFOLD__ = True`, bodies `raise AssertionError("Not yet implemented -- RED scaffold")`, imports succeed: `src/weight_tracker/composition.py` (build_app + StartupRefused) · `core/validation.py` (validate_weight, validate_entry_date, apply_entry) · `core/trend.py` (trend_series + ADR-004 constants) · `shell/entry_store.py` (SqliteEntryStore + probe) · `shell/clock.py` (SystemClock). Real (non-scaffold) support modules: `core/types.py` (domain types SSOT), `ports.py` (ClockPort protocol). Plus `pyproject.toml` (uv, pytest/pytest-bdd/hypothesis/httpx) and `uv.lock`.

### [REF] Test Placement

`tests/weight-trend-tracker/acceptance/` — `*.feature` (scenario SSOT) · `conftest.py` (fixtures + tag normalization + @pending one-at-a-time skip, `RED_GATE_ALL=1` escape for the gate) · `steps/` (`domain_types.py`, `composition.py` facade, `fake_clock.py`, `steps_{record,access,views}.py`, 7 `test_*.py` bindings) · `properties/` (layer-1 PBT). Shared state-delta port bootstrapped at `tests/common/state_delta.py` (first DISTILL in project). Precedent: greenfield — placement follows nw-distill machine-artifact convention.

### [REF] Driving Adapter Coverage

Every DESIGN entry point has ≥1 scenario through the real protocol (TestClient over production ASGI app): `POST /login` (access feature) · `POST /entries` (WS + m1 + m3) · `GET /entries` (WS + m2) · `GET /trend` (m4) · `GET /graph` (m4 toggle/default) · `GET /` entry screen (m5) · `GET /stats` (m4/m5 @kpi) · `GET /healthz` (access, unauthenticated) · `GET /manifest.webmanifest` (m5 install). Zero uncovered entry points.

### [REF] AT-Completeness Audit (Phase 2.5)

Verdict: **COMPLETE — 15/15** (C1a ✓ C1b ✓ C2a ✓ docstring state machines · C2b ✓ · C3 ✓ · C4a ✓ · C4b N/A-pass: no inverse op, deletion out of scope by A7 · C5a ✓ view×scale · C5b ✓ toggle orthogonality · C6a ✓ · C6b ✓ all 6 reasons · C6c ✓ closed set asserted · C7a ✓ unwritable store → refusal · C7b ✓ restart-after-confirm as the interruption contract (single-row upsert = transaction boundary) · C7c N/A-pass: single user by locked decision, in-process rate limiter). Zero SPECIFICATION_AMBIGUITY findings. Audit log: `(weight-trend-tracker, C1..C7, findings=0, severity_max=none)`. No domain extensions opted in.

### [REF] Mandate-12 Evidence

CM-I-1 ✓ `steps/domain_types.py` re-exports production `core/types.py` enums (TimeScale, ViewMode, RejectionReason) + typed parsers. CM-I-2 ✓ composition services consume `TimeScale`/`ViewMode`/`RejectionReason`/`date` (no raw str where an enum exists). CM-I-3 ✓ step bodies ≤2 statements, final = `composition.<service>.<method>(...)`, zero control flow. CM-I-4 step-reuse ratio (informational): 176 step occurrences / 72 unique decorators = **2.44×** — natural ceiling for a single-persona journey feature; below 4× is compliant per calibrated-refusal precedent (readability outranks ratio).

### [REF] Fail-For-Right-Reason Gate

`RED_GATE_ALL=1 uv run pytest`: 71/71 FAIL, all `MISSING_FUNCTIONALITY` (AssertionError from production scaffolds: composition 57, trend 7, validation 7). Zero IMPORT_ERROR/FIXTURE_BROKEN/WRONG_ASSERTION. Full classification: `docs/feature/weight-trend-tracker/distill/red-classification.md`. Default suite state: WS RED, 70 `@pending`-skipped.

### [REF] Pre-Requisites

From DESIGN: driving ports per brief.md § Component Decomposition (HTTP routes as listed in `build_app` docstring — the executable route contract) · ADR-004 constants pinned in `core/trend.py` · AccessGate session-expiry judged via the injected ClockPort (testability contract, required by the 89/91-day scenarios). From DEVOPS: ephemeral SQLite with prod pragmas (WAL+FULL) in ci/local — matched by tmp_path store; `/healthz` unauthenticated; `/stats` KPI query surface fields `entry_logged_count`, `trend_view_opened_count`, `trend_views_this_week`, `speed{median_ms,p90_ms,sample_count}`. Timing budget note (F-004): the only wall-clock assertion is the 2 s history-readiness budget (≥200 ms rule satisfied).

### [REF] Upstream Notes (non-blocking)

1. 21 July 2026 is a **Tuesday**, not Monday as written in US-001/journey Gherkin — scenario dates and the confirmation string ("Tue 21 Jul") corrected at DISTILL to match what the app must render.
2. `nwave-ai outcomes register` tool defect: mis-packaged schema.json → exit 1; registry populated manually in canonical shape at `docs/product/outcomes/registry.yaml` (OUT-1…OUT-6). Re-register via CLI when fixed.
3. Window semantics pinned (was unspecified): scale window = last {7, 30, 91, 182, 365} days inclusive of today for 1W/1M/3M/6M/1Y (`domain_types.SCALE_WINDOW_DAYS`).
4. Sub-0.1 kg precision input (e.g. "81.234") is REJECTED, not silently rounded (Postel/C6: never silently coerce). Amendable in DELIVER via a superseding decision if rounding is preferred.

### [REF] Inherited commitments

| Origin | Commitment | DDR | Impact |
|--------|------------|-----|--------|
| DISCUSS#US-001..006 | All 6 stories covered by tagged scenarios (traceability `@US-N`, Dim 8 Check A) | n/a | every story maps to ≥1 executable scenario; DoD "story demonstrable from ATs" satisfiable |
| DISCUSS#SystemConstraints | 30.0–250.0 kg range, 0.1 precision, one-entry-per-day, no future dates | n/a | encoded as boundary outlines + PBT properties + closed rejection-reason set |
| DISCUSS#OQ-2 resolution | Seeding ACs void; slice ordering free; trend validates on fresh data | n/a | slice-03/04 briefs amended with Changed Assumptions; no seeding scenario authored |
| DESIGN#D-09 (ADR-004) | Kalman+RTS smoothed display, fixed parameters, full recompute per read | n/a | trend oracles assert current-line shape (shift/step/coverage/decline/determinism), never rendered-value immutability |
| DESIGN#OpenQ-1 | Timezone skew: client date ≤ server UTC date + 1 | n/a | pinned as skew +1 accepted / +2 rejected scenarios + PBT skew-bound property |
| DESIGN#OpenQ-2 (ADR-003) | 90-day session treated as confirmed | n/a | 89-days-pass and 91-days-pass scenarios pin the expiry boundary via injected clock |
| DESIGN#OpenQ-3 | Gap oracle = smoothed continuity of the CURRENT line | n/a | gap scenarios assert bounded daily step + daily-grid coverage across gaps |
| DEVOPS#EnvMatrix | Prod pragmas in tests; mutation testing local-only; CI runs full pytest | n/a | acceptance suite runs on ephemeral SQLite matching prod semantics; @pending discipline keeps CI green pre-DELIVER except the intentional WS RED |
| DEVOPS#MonitoringContracts | KPI-1/KPI-3 instrumentation emitting + queryable; G-2/G-3 as CI-gated ATs | n/a | @kpi scenarios bound in kpi-contracts.yaml § at_scenario_links with window + soft/hard gate class |

## Wave: DELIVER

### [WHY] Upstream Issues

#### AT_GAP-1 (2026-07-22): responsiveness oracle anchored on a retrospectively revised rendered value — adjudicated, fixed at DISTILL

- **Test**: `tests/weight-trend-tracker/acceptance/properties/test_trend_math_properties.py::test_a_sustained_half_kilo_per_week_decline_is_visible_within_7_days` (US-004 responsiveness AC).
- **Defect**: the final clause `series[last_day] < series[onset_day] - 1.0` was unattainable for ANY correct ADR-004 implementation. It anchored the "1 kg visible" claim on `series[onset_day]` — a smoothed value that RTS retrospectively revises down (~0.45 kg) in the same rendering while the endpoint lags (~0.40 kg). This is exactly the anchoring pattern ADR-004 Consequences + DESIGN OpenQ-3 forbid for oracles ("assert the CURRENT line's shape, never immutability/anchoring of previously rendered values"). DISTILL applied that discipline to the gap oracles but missed it on the responsiveness oracle — an authoring defect, not an implementation defect.
- **Oracle-verified evidence**: crafter's independent exact batch-MAP solve matched the preserved RTS implementation to 1e-13; max attainable onset-anchored delta = **0.6503 kg** (deterministic, shift-invariant — reproduced by DISTILL at kg = 60.0 / 82.3 / 110.0) vs the **1.0 kg** the assertion required.
- **Fix chosen** (crafter's option 1 + strengthened within-7-days clause):
  1. Endpoint compared against the pre-onset **plateau level** (`series[last_day] < plateau_kg - 1.0`) — the plateau is a fixed input, not a revisable rendered value. Verified margin 0.096 kg against the preserved implementation (50 Hypothesis examples pass); a flat/cumulative-mean line (~plateau − 0.6) fails it.
  2. Within-7-days clause strengthened to test the AC as the user lives it: a second rendering over `stable + decline[:7]` asserts the CURRENT line already points down when only one decline week exists (endpoint < plateau − 0.1, verified margin 0.171 kg); an over-lagging smoother (EMA α = 0.01, endpoint ≈ plateau − 0.03) fails it. The original day-21 shape clause (`series[onset+7] < series[onset] − 0.05`) is retained — it pins current-line shape, which is sound.
- **ADR-004 unchanged**: constants (R = 0.20, α = 0.10, q = R·α²/(1−α), Huber δ = 1.0, missing-day predict-only) and the smoothed-display decision are untouched. Module `pytest.mark.pending` gating untouched (crafter unskips per one-at-a-time discipline).

#### AT_GAP-2 (2026-07-22): precision boundary pinned — found by mutation survivor at DELIVER step 03-03

Mutating the precision threshold exponent −1 → −2 in core validation survived the suite: the only finer-than-scale example was "81.234" (three decimals), so no AT rejected a TWO-decimal weight. Fix at DISTILL: "A finer-than-scale value is rejected rather than silently rounded" (`milestone-1-log-todays-weight.feature`) converted to a Scenario Outline with examples "81.234" + "82.45" (boundary-pinning), tags and active (un-pended) status unchanged. Verified green against production: `test_milestone_1.py` 14 passed, 2 outline instances `[81.234]` `[82.45]`. No production or validation-constant change.

#### AT_GAP-3 (2026-07-22): KPI rolling-week boundary pinned — found by mutation survivors at DELIVER step 03-05

No scenario pinned the 7-day window of `trend_views_this_week`: a `trend_view_opened` event older than 7 days must NOT count, and two genuine mutants of the cutoff survived. Fix at DISTILL: new active scenario "A viewing from last week no longer counts toward this week" in `milestone-4-trend-through-noise.feature` (@driving_port @kpi @real-io @adapter-integration @US-004 @contract-shape:bounded-change) — opens the trend (view logged today), advances the injected clock 8 days, opens again, asserts trend views this week number 1 (the 8-day-old view excluded; without the cutoff the count would be 2 and the scenario fails; paired with "Opening the trend counts toward engagement" it pins the window from both sides). New step bindings (Mandate-12, one-statement composition delegation): `Given he opened the trend at "{scale}"` (steps_views.py, twin of the When) + `When {n:d} days pass` (steps_access.py, When-flavored twin of "days have passed"). Verified green against production: `test_milestone_4.py` 11 passed (was 10); `test_access_protection.py` 9 passed unaffected. No production change.

#### AT_GAP-4 (2026-07-22): milestone-5 oracle gaps closed — found by mutation survivors at DELIVER step 03-06

Two cheap oracle gaps in `milestone-5-five-second-entry.feature`, both pinned with new active scenarios (green against production, no production change):

1. **Yesterday-anchor with neighbours** — "Yesterday still anchors today in a well-kept record": three consecutive days hold DISTINCT values (19 Jul 83.4, yesterday 82.6, today 81.9 already logged), asserting the reference shows specifically yesterday's 82.6. Kills `weight_on` max-date mutants (would show today's 81.9) and off-by-one-older mutants (would show 83.4). Existing Given vocabulary reused — zero new bindings.
2. **Empty speed report** — "An untimed record makes no speed claims": empty record → `Then the speed report honestly shows no timed mornings yet`, pinning the honest-nulls contract shape `speed{median_ms: null, p90_ms: null, sample_count: 0}` exactly. New Then binding (steps_views.py) delegates to new `StatsService.assert_speed_report_empty` (composition.py, Mandate-12 single-delegation).

Accepted residuals (deliberately NOT oracled, per mutation report):
- `_p90` sandwich looseness (median ≤ p90 ≤ worst-case, not an exact percentile pin) is contract-intentional — the KPI contract promises an honest worst-case band, not a specific interpolation method.
- `sw.js` service-worker behavior remains a browser-only smoke concern — app-shell caching is unobservable from the HTTP test host; serving the file is already covered.

Verified: `test_milestone_5.py` 7 passed (was 5); full acceptance suite 75 passed.

#### AT_GAP-5 (2026-07-23): the human doorway was never specified — found on first real browser visit

Every scenario's "Clemens has unlocked the tracker with his passphrase" Given drove POST /login directly; a locked browser navigation returns bare JSON `{"detail":"locked"}` 401 with no login page. US-001's elevator pitch ("taps the tracker icon → entry screen opens") implies the human journey visit → passphrase door → entry screen, but no AT pinned it — a specification gap at DISTILL, not an implementation slip. Fix: three NEW active scenarios in `access-protection.feature` (chained narrative, browser-flavored steps setting Accept: text/html and following redirects; bindings delegate to new `AccessService.visit_in_browser` / `enter_passphrase_at_door` + door assertions in composition.py):

1. "A locked visit is met by the passphrase door" (@contract-shape:pure-function) — browser GET of the app root while locked → an HTML door page holding a passphrase form submitting to the login door, not raw JSON.
2. "The passphrase door opens onto the entry screen" (@contract-shape:bounded-change) — correct passphrase via the form → browser lands on the entry screen (redirect to the root, session established), record open.
3. "A wrong passphrase keeps the door shut but polite" (@contract-shape:unbounded-preservation) — wrong passphrase → the door again with a visible rejection, record still hidden.

RED evidence (fail-for-the-right-reason, all `AssertionError` at Then — MISSING_FUNCTIONALITY): (1) `not 'application/json': '{"detail":"locked"}'`; (2) `stayed at '/login'` (no redirect); (3) `not 'application/json': '{"detail":"wrong passphrase"}'`. Non-HTML/API behavior deliberately preserved: existing locked-JSON-401 scenarios untouched and green — full suite minus the three new REDs = **83 passed**. Crafter greens these three in DELIVER; no production change made at DISTILL.

## Wave: DELIVER / [REF] Demo Evidence

Post-merge integration gate (Phase 3.5), 2026-07-22. Real server: `uvicorn weight_tracker.main:app` with production env contract (`PASSPHRASE_HASH`, `SESSION_SIGNING_KEY`, `DB_PATH`), fresh SQLite, real HTTP via curl. All exit codes 0 / HTTP 200 unless stated.

| Story | Demo command | Saw |
|---|---|---|
| US-001 | `POST /login` (passphrase) → `POST /entries {"date":"2026-07-22","weight":"82.4","entry_ms":4200}` | `{"status":"unlocked"}` → `"Saved: 82.4 kg — Wed 22 Jul"`; entry at top of `GET /entries?scale=ALL` |
| US-002 | `GET /entries?scale=3M` / `?scale=ALL` | exactly the stored entries, no interpolation; `GET /graph` 200 |
| US-003 | `POST /entries {"date":"2026-07-20","weight":"82.6"}`; then `{"date":"2026-07-30",...}` | backfill `"Saved: 82.6 kg — Mon 20 Jul"`; future rejected `"Future dates cannot be logged."`, nothing stored |
| US-004 | `GET /trend?scale=1M` | smooth deterministic `trend_kg` series over the daily grid (82.50 → 82.50 → 82.50) |
| US-005 | `GET /graph` → `GET /graph?view=raw&scale=3M` | default `data-view="trend"`; raw toggle preserves `data-scale="3M"` |
| US-006 | `GET /` · `GET /manifest.webmanifest` · `GET /stats` | `autofocus` + `inputmode="decimal"`; installable manifest; `speed{median_ms:4200, p90_ms:4200, sample_count:1}` — entry_ms KPI-1 instrumentation emitting |

Environment matrix outcome: `local-dev` PASS (75 tests + ruff/format/mypy-strict/import-linter green); `ci` mirrored locally with identical tools PASS (workflows land with this wave — first CI run occurs on push); `production` NOT EXERCISED from this machine — Fly app/volume/secrets are documented operator prerequisites (step 01-04 report; DA-3); startup is self-gating (`health.startup.refused`) and the deploy pipeline's smoke stage covers first contact.

Demo finding (minor, logged): `GET /entries?scale=All` (wrong casing, hand-typed URL only — UI buttons send `ALL`) returns 500 instead of a 4xx; unhandled `ValueError` in `TimeScale(scale)`. Routed to adversarial review for severity judgment.

## Wave: DELIVER / [REF] Implementation Summary

DELIVER wave executed 2026-07-22..23 by nw-deliver orchestrator + nw-functional-software-crafter (ADR-005 paradigm). Shipped the complete weight-trend-tracker application: FastAPI shell over a pure functional core (validation railway with closed RejectionReason set; Kalman+RTS trend per ADR-004 with pinned constants), SQLite EntryStore with earned-trust startup probes + schema-version rollback guard, passphrase AccessGate (argon2id, signed 90-day cookie judged via injected ClockPort, in-process throttle), server-rendered mobile-first UI with vendored uPlot (raw/trend lenses, shared time scale), PWA manifest + app-shell service worker, KPI telemetry (entry_ms, trend_view_opened, /stats query surface), and the full deploy rail (Dockerfile with Litestream 0.3.13 supervisor, fly.toml, CI gates→deploy→smoke pipeline, weekly restore drill, pre-commit/pre-push configs, import-linter contract). 15 roadmap steps, all RED→GREEN→COMMIT through DES.

## Wave: DELIVER / [REF] Scenarios Green Count

**49 of 49 Gherkin scenarios green** (75 acceptance test instances after outline expansion and DELIVER-era oracle additions, incl. 14 PBT properties) plus 8 crafter-authored integration tests = **83 passed, 0 skipped, 0 failed** at HEAD `cf6e199`, 2026-07-23. `@pending` discipline fully unwound — no scenario remains skipped.

## Wave: DELIVER / [REF] Files Modified

Production (src): composition.py, main.py (new), ports.py, core/{types,validation,trend}.py, shell/{access_gate (new), clock, entry_store, telemetry_store (new)}.py, web/{routes.py (new), templates/{index,graph}.html (new), static/{uplot.iife.min.js, uplot.min.css, sw.js, icon.svg} (new)}.
Infrastructure: Dockerfile, fly.toml, .github/workflows/{ci-deploy,restore-drill}.yml, .pre-commit-config.yaml, pyproject.toml (dev deps + ruff/mypy/import-linter config), scripts/check_probe_presence.py, .env.example, uv.lock.
Tests: all 7 .feature files activated; steps/ bindings extended (AT_GAP fixes); properties/ oracles recalibrated (AT_GAP-1); tests/weight-trend-tracker/integration/{test_schema_version_guard,test_scale_param_robustness}.py (new); tests/common/state_delta.py.
Docs: feature-delta.md (this file), deliver/{roadmap,execution-log}.json, deliver/mutation/mutation-report.md.

## Wave: DELIVER / [REF] DoD Check

| # | DoD item (DISCUSS) | Status |
|---|---|---|
| 1 | All UAT scenarios green (automated) | PASS — 49/49 |
| 2 | Supporting unit/integration tests green | PASS — 14 PBT + 8 integration |
| 3 | Code refactored; no obvious debt | PASS — per-step + Phase 3 L1-L6 pass |
| 4 | Code reviewed | PASS — adversarial review APPROVED after 1 revision (D1) |
| 5 | Merged to main | PASS — trunk-based, all commits on main |
| 6 | Deployed to production URL | **BLOCKED (operator)** — Fly app/volume/secrets not yet created; CI deploys on push once present |
| 7 | Dogfooded same day with real entry | **BLOCKED (operator)** — follows first deploy |
| 8 | KPI instrumentation emitting | PASS — verified live in demo (entry_ms, trend_view_opened, /stats) |
| 9 | Story demonstrable end-to-end | PASS — demo evidence above; on-phone demo follows deploy |

## Wave: DELIVER / [REF] Quality Gates

| Phase | Outcome |
|---|---|
| Roadmap + review | Approved (49/49 scenario coverage, 0 orphans); +1 late step 03-07 for DEVOPS pre-req 2a |
| Steps 01-01..03-07 | 15/15 COMMIT/PASS; DES integrity: all 15 complete traces (exit 0) |
| Post-merge integration (3.5) | PASS — local-dev + ci-mirror; demos for US-001..006; production env deferred to operator |
| Refactoring (Phase 3) | PASS — light pass; probe-presence hook green |
| Adversarial review (Phase 4) | APPROVED — 1 blocking defect (scale param 500) fixed + verified |
| Mutation (Phase 5, per-feature) | PASS — closing run 82.5% effective (≥80%); 5 residual oracle-sized gaps documented in mutation-report.md |
| Static gates | ruff, ruff format, mypy --strict, import-linter (core-pure), probe-presence: all green |

## Wave: DELIVER / [REF] Pre-Requisites

Depended on: DISTILL .feature files + PBT properties (authoritative spec; 4 oracle defects found and fixed during DELIVER — AT_GAP-1..4), DESIGN component manifest (brief.md § Component Decomposition — no unauthorized components; access_gate/routes/templates/telemetry_store all sanctioned), ADR-001..005, DEVOPS pipeline outline + pre-requisites 1-6 (all implemented; 2a via late step 03-07).
Outstanding operator prerequisites for first deploy: create Fly app + 1 GB volume `data`; `fly secrets set PASSPHRASE_HASH SESSION_SIGNING_KEY REPLICA_URL LITESTREAM_ACCESS_KEY_ID LITESTREAM_SECRET_ACCESS_KEY`; GitHub secrets `FLY_API_TOKEN`, `R2_REPLICA_URL`, `R2_READONLY_*`; add a git remote and push (no remote configured at finalize time).

## Wave: DELIVER / [WHY] Retrospective

Phase 8 retrospective, 2026-07-23 (Rex, nw-troubleshooter). Two process issues in an otherwise clean wave (15/15 steps COMMIT PASS, 49/49 scenarios green, mutation 82.5%). 5 Whys per issue; evidence from this file (Upstream Issues), `docs/evolution/2026-07-23-weight-trend-tracker.md`, ADR-004.

### Issue 1 — AT_GAP-1: mathematically unattainable responsiveness oracle

- **WHY 1**: The responsiveness AT could not pass for ANY correct implementation. [Evidence: crafter's independent exact batch-MAP oracle matched the implementation to 1e-13; max attainable 0.6503 kg vs the 1.0 kg asserted — AT_GAP-1 adjudication above.]
- **WHY 2**: The final clause anchored the 1.0 kg claim on `series[onset_day]` — a smoothed value RTS retrospectively revises down (~0.45 kg) while the endpoint lags (~0.40 kg). [Evidence: AT_GAP-1 Defect entry.]
- **WHY 3**: DISTILL translated the quantified AC ("0.5 kg/week visible within 7 days") into concrete numbers with no feasibility calculation against ADR-004's pinned constants (R=0.20, α=0.10); the 1.0 kg bound was asserted, never derived — a derivation would have exposed the 0.6503 kg ceiling and forced the anchor question before authoring. [Evidence: ADR-004 § Decision, "AC margins (research arithmetic)" paragraph derives margins for spike/gap/decline-visibility but no onset-anchored delta; no DISTILL artifact contains such a derivation.]
- **WHY 4**: The known anti-anchoring discipline (ADR-004 § Consequences; DESIGN OpenQ-3) was applied trigger-based: upstream explicitly named the *gap/revision* oracles, so only those were audited; the responsiveness oracle — equally exposed to revision — was outside the named trigger. [Evidence: Inherited Commitments row DESIGN#OpenQ-3 scopes the commitment to gap scenarios; AT_GAP-1 notes the gap oracles got the discipline, the responsiveness oracle did not.]
- **WHY 5 → ROOT CAUSE 1**: The DISTILL completeness gate audits scenario coverage, not numeric attainability: the 15-item C1–C7 audit (§ AT-Completeness Audit above) contains no item requiring a feasibility derivation for quantified thresholds, nor an exhaustive anchoring audit when the design declares rendered values revisable — coverage of design consequences depends on upstream naming each affected oracle.
- **Backwards check**: absent a feasibility gate + with trigger-based auditing, an unnamed oracle anchored on a revisable value with an underived bound ships RED-unattainable → observed. VALID. **Ruled out**: AC too ambitious (the plateau-anchored fix meets the same 1.0 kg claim with 0.096 kg margin — the requirement was attainable, only the anchor was wrong); wrong constants (ADR-004 constants serve the other ACs with 4–6× margin and are design-locked).
- **COUNTERMEASURE 1 (process)**: DISTILL completeness audit gains two items: every quantified oracle claim must carry a feasibility calculation (or simulation) against the pinned algorithm constants, with the derived margin recorded; and any "values are revisable" design consequence triggers an anchoring audit across the *entire* oracle set, not only oracles named upstream.

### Issue 2 — Roadmap gap: DEVOPS Pre-Requisite 2a missed by generation and review

- **WHY 1**: The schema-version rollback guard was absent from the initial 14-step roadmap; discovered only at the Phase 3.5 integration gate by an orchestrator grep, requiring late step 03-07. [Evidence: evolution doc Issues; Quality Gates row "+1 late step 03-07".]
- **WHY 2**: The roadmap was generated from DISTILL scenario coverage, and pre-req 2a had no DISTILL scenario — it is deployment-level startup behavior with no user-observable Gherkin surface. [Evidence: evolution doc Lesson 4; DISTILL Adapter Coverage marks deployment-level concerns NOT MODELED.]
- **WHY 3**: The obligation lived only as prose in DEVOPS Pre-Requisites ("a DEVOPS pre-requisite **implemented by DELIVER**") — a cross-wave work item carried in no machine-consumed artifact class (not a scenario, not a scaffold, not a roadmap input). [Evidence: DEVOPS Pre-Requisite 2a text above.]
- **WHY 4**: The roadmap review validated scenario↔step mapping only ("49/49 scenario coverage, 0 orphans") — its checklist had no sweep of upstream pre-requisite lists, so a gap in the generator's input class was structurally invisible to the reviewer using the same input class. [Evidence: Quality Gates roadmap row.]
- **WHY 5 → ROOT CAUSE 2**: Roadmap generation and its review both treat DISTILL scenarios as the *sole* source of DELIVER work items; "implemented by DELIVER" obligations declared in other waves have no representation in the roadmap input contract, leaving discovery to ad-hoc grep.
- **Backwards check**: scenario-only input contract + scenario-only review ⇒ any non-scenario obligation is omitted by both, surfacing only at an integration gate → observed. VALID. **Ruled out**: unclear documentation (2a's text is explicit and bold about ownership — the failure is representation, not description); reviewer carelessness (a diligent reviewer using the same scenario-only input class cannot see the gap; the countermeasure must change the input, not the diligence).
- **COUNTERMEASURE 2 (process)**: Roadmap generation input contract must include a mandatory sweep of feature-delta for cross-wave "implemented by DELIVER" obligations (DEVOPS pre-requisites, DESIGN open questions deferred to DELIVER), each mapped to a step or an explicit deferral; the roadmap reviewer checklist gains a matching DEVOPS pre-requisites sweep item, not only scenario coverage.

**Cross-validation**: both root causes are the same failure class — completeness processes keyed to a single named-input class (upstream-named oracles; scenarios) instead of exhaustive sweeps of declared obligations. Consistent, non-contradictory; together they explain both symptoms with no residual gap. Scope note: AT_GAP-2..4 are not in-scope process failures — they are the mutation-testing feedback loop working as designed (survivors → oracle strengthening, adjudicated above). Notably, both escapes were caught by DELIVER's independent verification layers, which is the defense to keep.

**REPEAT (working as designed)**: independent-oracle discipline (exact-MAP second oracle turned "test fails" into "test is wrong, with proof"); mutation-driven oracle strengthening (survivors → AT_GAP-2..4 back-propagations, closing-run kills confirmed); demo gate on a real server with raw protocol (caught the `?scale=All` 500 the entire AT suite structurally could not see).
