<!-- markdownlint-disable MD024 -->
# Feature Delta: entry-date-picker

## Wave: DISCUSS

### [REF] Persona ID

`clemens` — see `docs/product/personas/clemens.yaml`. Sole customer, sole user, sole developer. Phone-first, half-awake at 06:45, metric units, ~82 kg range. Unchanged from prior features.

### [REF] JTBD One-Liner

Job `track-true-weight-trend` (`docs/product/jobs.yaml`, status: validated). This feature delivers the **maintenance moment** (`js-3-maintain`: *"I notice I forgot to log yesterday or mistyped a value three days ago — add or correct past days in place — so I can trust that my record and the trend derived from it are accurate"*), the last journey moment (step 4) still without a UI.

**Bridge decision**: **no new job-story moment.** `js-3-maintain` has named this moment since the initial DISCUSS (2026-07-21); the backend has honored it since `weight-trend-tracker` (`POST /entries` takes any non-future date, upserts on the date key). This feature closes the gap by surfacing the date on the entry screen. A dated note on `js-3-maintain` and the feature-list entry in `jobs.yaml` record the delivery (js-4/js-5 precedent; no JTBD re-run).

### [REF] Locked Decisions

- **D1** Feature type: user-facing.
- **D2** Walking skeleton: NO — brownfield; the full vertical exists; this feature rides it. Backend already complete (date-accepting save, no-future validation, one-per-day upsert).
- **D3** UX research depth: lightweight — journey delta, happy path, single persona.
- **D4** JTBD: bridge only to existing validated job `track-true-weight-trend`, moment `js-3-maintain`; no re-analysis.
- **D5** Density: mode=lean (Tier-1 [REF] only), expansion_prompt=ask-intelligent (triggers evaluated — **none fired**, silent-lean).
- **D6** (user) **Native date input, always visible**: `<input type="date">` above the weight field, prefilled with device-local today. Zero extra taps for the default morning flow; tapping it opens the phone's native picker. No JS picker library.
- **D7** (user) **Edit prefill**: picking a date that already has an entry prefills the weight field with the stored value plus an editing hint (`Editing Thu 23 Jul — was 82.4 kg`). Save = correct in place.
- **D8** (user) **Post-save reset to today**: after any save the picker returns to device-local today and the field clears — supports the common combo *backfill yesterday, then log today* and prevents habit-typing from overwriting a past day. The confirmation line always names the saved date.

### [REF] Scope Assessment

**PASS — 2 stories, 1 bounded context (weight tracking), estimated ~0.5–1 day total.** Oversized signals checked: stories 2/10; bounded contexts 1/3; walking skeleton N/A (exists); effort ≪ 2 weeks; user outcomes — backfill and correct are two situations of one mechanism (the date control) and ship together as one slice. No signal fired; no split needed. Reference class: US-006/US-011-scale deltas landed in ~0.25–0.5 day each; this touches one template + one route concern (KPI-1 purity).

### [REF] Journey Summary

SSOT: `docs/product/journeys/daily-weight-tracking.yaml` — **delta on steps 1 and 4**; steps 2–3 untouched. Changelog entry dated 2026-07-24.

- **Step 4 (Maintain the record)** gains its mechanism: the entry screen's date field IS the maintenance surface. Select a past day → field prefills (existing entry) or clears with a no-entry hint (gap) → save corrects or backfills; graph, glance, and recent list recompute in place (same save-response refresh as today). Existing failure modes stand (future date, duplicate-instead-of-replace, stale trend); new ones added: blind overwrite (mitigated by D7 prefill+hint), habit-typing after a backdated save clobbering a past day (mitigated by D8 reset), maintenance saves polluting the KPI-1 morning-speed metric (must add 0 samples).
- **Step 1 (Log today's weight)** absorbs a visible date row above the weight field, prefilled today (D6). Default flow is byte-identical in tap count: open → type → save. The yesterday-anchor hint applies only while the date is today; a non-today date replaces it with the editing/no-entry hint (one hint line, never two).
- Emotional delta (step 4): entry "mild annoyance" → exit "trust restored" now happens **on the same screen within seconds**, not on a hypothetical future admin surface. The step-4 arc finally exists in the product.

### [REF] Story Map

Extends the existing map (same persona, same goal). No new activities; the Maintain column gets its first UI stories.

| Capture weight | Review history | Judge trend | Maintain record |
|---|---|---|---|
| US-001, US-006, US-007, US-008, US-010 ✅ | US-001, US-002, US-009, US-011, US-012 ✅ | US-004, US-005, US-009, US-010 ✅ | US-003 (backend rules) ✅ |
| *(date row rides the entry form, default today)* | | | **Backfill a missed day (US-013)** |
| | | | **Correct a past value (US-014)** |

**Walking skeleton**: N/A — exists. **Slice** (elephant carpaccio, ≤1 day, dogfooded same day):

- **Slice 01** — `slices/slice-01-dated-entry.md`: US-013 + US-014 (one mechanism — the date control — carrying both situations; splitting them would ship the picker twice).

### [REF] Priority Rationale

Single slice — priority question is only *whether now*. Yes: `js-3-maintain` is the last unserved journey moment; every real missed day is currently an unrepairable hole in the trend the whole product exists to protect (anxiety force: "a naive trend would lie across missing days" — a permanently wrong record is worse). Value 4 (record trust; unblocks honest trend judgment after any lapse), Urgency 2 (each passing gap is currently permanent), Effort 1 → score 6. MoSCoW: Must (explicit user request; D6–D8 locked).

### [REF] System Constraints

- Entry primacy (KPI-1): default morning flow keeps zero extra taps, weight-field autofocus, decimal keypad, interactive ≤2 s. The date row must not steal focus or reflow the form after load.
- One entry per calendar day is invariant (`entries.date` PRIMARY KEY, upsert); the picker must never create a second path around it.
- Server-side no-future rule (`validate_entry_date`, skew-bounded) stays authoritative; the client `max` attribute is UX assist only.
- Read-only ports stay read-only (CLAUDE.md / ADR-005); prefill is a read concern.
- Calm-theme rules apply: the date input styled by the existing system-scheme theme, contrast AA both schemes (G-4); zero new external origins (G-5 intent).

### [REF] User Stories

All stories: `job_id: track-true-weight-trend`, moment `js-3-maintain`. Persona: Clemens.

#### US-013: A forgotten day is backfilled where the habit lives

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.25–0.5 day

##### Problem

Clemens skipped Sunday (travel). The backend would happily accept `2026-07-19` — but the entry screen hardcodes today, so the gap is permanent unless he hand-crafts an HTTP call. A hole he *knows about* and *cannot fix in the app* corrodes exactly the trust (`js-3-maintain`) the tracker exists to build.

##### Elevator Pitch

- **Before**: Opens `/` — no date control; the client always submits the device-local today. A missed Sunday stays a gap forever.
- **After**: Opens `/` on Mon 20 Jul 2026, taps the date field (prefilled `2026-07-20`), picks `2026-07-19`, types `82.6`, taps **Save** → "Saved: 82.6 kg — Sun 19 Jul"; the graph, glance line, and recent list refresh in place with Sunday filled, and the date field is back on today for the morning's own log.
- **Decision enabled**: "Is my trend computed over a record I actually trust?" — judge progress from a complete record instead of mentally discounting known holes.

##### Domain Examples

1. *Happy path*: Mon 20 Jul 2026, 06:50 — Sunday 19 Jul missing (weekend trip). He picks 19 Jul, sees "No entry for Sun 19 Jul yet", types 82.6, saves, then logs Monday's 82.4 right after — date field already back on `2026-07-20`.
2. *Default morning untouched*: Fri 24 Jul, 06:45 — date field shows `2026-07-24`, weight field focused, keypad up. He types 82.2 and saves without ever touching the date row. Two interactions, same as every prior morning.
3. *Future blocked*: he fat-fingers the native picker toward tomorrow — the picker's `max` stops at today; a forged request for `2026-07-30` gets the existing "Future dates cannot be logged." rejection and no stored entry.
4. *KPI purity*: a backfill session (open picker, think, type) takes 22 s. The KPI-1 entry-speed samples for the week gain nothing from it; the median still reflects only real morning logs.

##### UAT Scenarios (BDD)

###### Scenario: A forgotten day is backfilled

- **Given** Clemens has entries for every day except Sunday 19 July 2026, and today is Monday 20 July 2026
- **When** he sets the date field to 19 July, types "82.6", and taps Save
- **Then** he sees "Saved: 82.6 kg — Sun 19 Jul"
- **And** the graph, glance line, and recent list refresh in place including the 19 July entry
- **And** the trend recomputes over the now-complete record

###### Scenario: The morning flow never pays for the picker

- **Given** it is Friday 24 July 2026 at 06:45
- **When** Clemens opens the tracker
- **Then** the date field is prefilled with 24 July, the weight field is focused with the decimal keypad shown, and saving a typed weight requires no interaction with the date row

###### Scenario: The picker resets to today after a backdated save

- **Given** Clemens has just saved 82.6 kg for Sunday 19 July
- **When** the confirmation appears
- **Then** the date field reads Monday 20 July (device-local today) and the weight field is empty, ready for today's log

###### Scenario: A future date cannot be logged

- **Given** today is Friday 24 July 2026
- **When** a save is submitted dated 30 July 2026
- **Then** the save is rejected with "Future dates cannot be logged." and no entry is stored
- **And** the native date field offers no date after today

###### Scenario: Maintenance never pollutes the morning-speed metric (@property)

- **Given** the KPI-1 entry-speed samples for this week hold N values
- **When** Clemens backfills any past day, however slowly
- **Then** the KPI-1 sample count for the week is still N

##### Acceptance Criteria

- Native `<input type="date">` above the weight field, prefilled device-local today (the same `deviceLocalDay()` day already used for saves), `max` = device-local today.
- Default flow unchanged: autofocus + decimal keypad on the weight field; zero date-row interactions needed; entry screen interactive ≤2 s.
- Save submits the selected date; confirmation always names the saved date; save response refresh (graph + glance + recent list) includes backdated entries by construction.
- After every successful save: date resets to device today, weight field clears.
- Server rejection for future dates surfaces exactly like existing rejections (typed value preserved for correction).
- Backdated saves (date ≠ device today) contribute **0** samples to KPI-1 entry-speed; mechanism = DESIGN (A23).

#### US-014: A mistyped past day is corrected in place

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.25–0.5 day

##### Problem

Three days ago Clemens saved 88.4 instead of 82.4 — a 6 kg phantom spike dragging the trend. The one-per-day upsert means the fix is just "save the right value for that date", but with no way to select the date, the typo — like the gap — is permanent. Worse, an edit surface that shows a *blank* field would invite blind overwrites of days he misremembers.

##### Elevator Pitch

- **Before**: A wrong value on a past day cannot be corrected in the app; the trend keeps chewing on the typo.
- **After**: Opens `/` on Fri 24 Jul 2026, sets the date to 21 Jul → the weight field prefills `88.4` with the hint "Editing Tue 21 Jul — was 88.4 kg"; he retypes `82.4`, taps **Save** → "Saved: 82.4 kg — Tue 21 Jul"; graph and trend recompute without the spike; exactly one entry exists for 21 Jul.
- **Decision enabled**: "Was that spike real or a typo?" — resolve it by *fixing the record*, then judge the trend on data he vouches for.

##### Domain Examples

1. *Typo repair*: Fri 24 Jul — Tuesday shows 88.4 (fat-fingered 8). Picks 21 Jul, field prefills 88.4, hint names the stored value, retypes 82.4, saves. Trend drops the phantom spike; history shows a single 21 Jul row at 82.4.
2. *Gap vs entry, clearly told apart*: he picks 19 Jul (no entry) — field is empty, hint "No entry for Sun 19 Jul yet". Picks 23 Jul (has 82.4) — field prefills 82.4, hint "Editing Thu 23 Jul — was 82.4 kg". He always knows whether saving adds or replaces.
3. *Hint line discipline*: with the date on today, the familiar "(yesterday: 82.4 kg)" anchor shows; the moment he picks a past day, the editing/no-entry hint takes that line's place — one hint line, never a stack.
4. *Old day, still correct*: he corrects a day from March (outside any recent-days map) — the prefilled value is the stored March value, not blank, not a guess (lookup mechanism = DESIGN, correctness for any stored day is the requirement).

##### UAT Scenarios (BDD)

###### Scenario: A mistyped value is corrected in place

- **Given** the stored entry for Tuesday 21 July 2026 is 88.4 kg and today is Friday 24 July 2026
- **When** Clemens sets the date field to 21 July
- **Then** the weight field prefills with "88.4" and the hint reads "Editing Tue 21 Jul — was 88.4 kg"
- **When** he types "82.4" and taps Save
- **Then** he sees "Saved: 82.4 kg — Tue 21 Jul"
- **And** exactly one entry exists for 21 July, at 82.4 kg
- **And** the graph and trend recompute without the 88.4 spike

###### Scenario: An empty past day is offered as a backfill, not an edit

- **Given** no entry exists for Sunday 19 July 2026
- **When** Clemens sets the date field to 19 July
- **Then** the weight field is empty and the hint reads "No entry for Sun 19 Jul yet"

###### Scenario: The hint line is singular

- **Given** the date field is on today and the yesterday anchor is showing
- **When** Clemens picks a past day and then returns the date to today
- **Then** the editing/no-entry hint replaces the anchor while a past day is selected, and the anchor returns when the date is today — never both at once

###### Scenario: Any stored day prefills correctly

- **Given** an entry from Tuesday 3 March 2026 at 84.9 kg, months outside the recent list
- **When** Clemens sets the date field to 3 March
- **Then** the weight field prefills with "84.9"

###### Scenario: Correcting a day never duplicates it

- **Given** Clemens saves 82.4 kg for a date that already has an entry
- **When** the history list and graph refresh
- **Then** that date appears exactly once, at 82.4 kg, in both

##### Acceptance Criteria

- Selecting a date with a stored entry prefills the weight field with the stored value (0.1 precision, any stored day — recent or ancient) and shows `Editing {Day dd Mon} — was {v} kg`.
- Selecting a date with no entry clears the weight field and shows `No entry for {Day dd Mon} yet`.
- The hint occupies the existing single hint line (yesterday anchor when date = today); never two hints at once.
- Saving over an existing date replaces it (one-per-day invariant observable in list + graph); confirmation names the date.
- Prefill lookup failure degrades to the no-entry presentation without blocking entry or save (degrade-to-absent precedent); a save still upserts correctly.
- Prefill reads via read-only history access — no write capability added to read ports.

### [REF] Out of Scope

Deleting an entry (record is append/correct only for now); tap-a-history-row-to-edit shortcut (rows stay display-only, graph-first-home D9); bulk/multi-day backfill; import of the old app's historical record (jobs.yaml habit force — still not committed); future-dated planning entries; notes/annotations; any change to `/graph`, `/stats`, trend algorithm, or auth. Everything on prior features' out-of-scope lists remains out.

### [REF] Walking Skeleton Strategy

**N/A — brownfield.** The full production vertical exists; the save path already accepts arbitrary valid dates end-to-end. This feature is a presentation delta on one template plus a metric-purity rule; it deploys through the existing pipeline and is dogfooded with the next real backfill or correction.

### [REF] Driving Ports

Behavioral, solution-neutral; DESIGN owns shapes and adapters. Read-only ports must never expose write methods (CLAUDE.md / ADR-005).

- **WeightLogging** (driving) — unchanged: already accepts `{date, weight}` with no-future validation and one-per-day upsert. No contract change.
- **WeightHistory** (driving, read-only) — must answer "the stored weight for day D, if any" for **any** stored day, to feed prefill (D7). The recent-days map already shipped for the yesterday anchor may cover recent days; whole-record prefill shape = DESIGN. No write methods.
- **Telemetry** (driven, established `append_event` trail) — the saved-entry event must let /stats tell today-dated from backdated saves so KPI-1 samples stay pure (A23) and KPI-8 usage is countable. Payload already carries the date; mechanism/naming = DESIGN.

### [REF] Pre-Requisites

None blocking DESIGN. Backend validation (`validate_entry_date`), upsert (`entry_store.upsert`), and save-response refresh (glance + recent list) all delivered and mutation-tested in prior features ✅. For DESIGN: pick the prefill lookup mechanism (recent map vs full-record fetch vs on-demand read) honoring degrade-to-absent, and the KPI-1 sample-purity mechanism at /stats. For DISTILL: existing entry-screen ATs assert the hardcoded `deviceLocalDay()` submission — renegotiate consciously to "selected date, defaulting to device day", never silently.

### [REF] Outcome KPIs

**Objective**: The record becomes fully self-maintainable — any noticed gap or typo is repaired on the entry screen in seconds, so the trend is always computed over a record Clemens vouches for.

Extends the existing registry (KPI-1…7 and G-1…G-5 unchanged except the KPI-1 purity rule below):

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|-----|-----------|-------------|----------|-------------|------|
| 8 | Clemens | repairs a noticed gap or typo in-app | 100% of noticed defects repairable in-app; repair ≤30 s from screen open | 0% (no in-app path; gaps/typos permanent) | backdated-save marker on the entry-saved trail, surfaced on /stats; repair time self-reported at dogfood | Leading |

**KPI-1 purity rule (required by this feature)**: entry-speed samples measure the *morning capture habit*. Backdated saves — inherently slower (picker, recall, prefill reading) — must contribute **0** samples, or a single backfill session would poison the weekly median the ≤5 s target guards. Same structural pattern as the KPI-3 ambient/deliberate split (graph-first-home).

- **Guardrails (must not degrade)**: KPI-1 entry speed (median ≤5 s, p90 ≤10 s) *and* its sample purity (a backfill week adds 0 samples); zero extra taps on the default flow; entry screen interactive ≤2 s; one entry per calendar day (G-1 family); trend determinism after recompute (G-3); contrast AA both schemes for the date row and hints (G-4); zero new external origins (G-5).
- **Hypothesis**: We believe an always-visible, today-defaulted date control for Clemens will make record repair routine (100% of noticed defects fixed, ≤30 s) without taxing the morning log (KPI-1 median and taps unchanged), deepening trust in the trend (the record never carries known holes) and thereby the habit itself (KPI-2, North Star).
- **Measurement plan**: today-vs-backdated distinction computed at read time on /stats from the existing entry-saved trail (payload already carries the date; KPI-5/KPI-7 pairing precedent). No new instrumentation infrastructure.

### [REF] DoR Validation

| DoR Item | US-013 | US-014 | Evidence |
|----------|--------|--------|----------|
| 1. Problem clear, domain language | PASS | PASS | Permanent gap despite willing backend; phantom spike + blind-overwrite risk |
| 2. Persona specific | PASS | PASS | `clemens` — phone-first, 06:45, 82 kg range, trusts only a complete record |
| 3. 3+ domain examples, real data | PASS (4) | PASS (4) | Real dates/values (82.6 on Sun 19 Jul; 88.4→82.4 on Tue 21 Jul; 84.9 on Tue 3 Mar) |
| 4. UAT 3–7 scenarios G/W/T | PASS (5) | PASS (5) | Happy, default-flow, reset, future-reject, KPI-purity / edit, gap-vs-entry, hint discipline, old-day, no-duplicate |
| 5. AC derived from UAT | PASS | PASS | AC lists map to scenarios plus quantified rules (≤2 s, 0.1 kg, 0 KPI-1 samples, max=today) |
| 6. Right-sized (1–3 d, 3–7 sc.) | PASS | PASS | ~0.25–0.5 d each; 5/5 scenarios; both demoable in one session |
| 7. Technical notes/constraints | PASS | PASS | System Constraints + port notes (prefill mechanism and KPI-purity mechanism = DESIGN; read-only ports) |
| 8. Dependencies resolved/tracked | PASS | PASS | Backend save path, recent-days map, save-response refresh, calm theme all delivered ✅; DISTILL AT renegotiation flagged |
| 9. Outcome KPIs, numeric targets | PASS | PASS | KPI-8 (100%, ≤30 s), KPI-1 purity rule (0 samples), measurement methods named |

**DoR Status: PASSED (2/2 stories, 9/9 items).**

**Requirements completeness score: 0.96** — functional behavior fully specified (default, backfill, edit-prefill, hint discipline, reset, refresh, rejection, degrade), NFRs quantified (≤2 s, taps, precision, contrast, sample purity), business rules explicit (one-per-day, no-future, today-default). Deductions: hint wording is analyst-chosen (OQ-10) and the no-lower-bound date range is a default (OQ-11).

### [REF] DoD 9-Item Checklist

Per story, at DELIVER completion (unchanged pattern):

1. All UAT scenarios green (automated).
2. Supporting unit/integration tests green — including the consciously renegotiated entry-screen AT (selected date replaces hardcoded device day; never silent breakage).
3. Code refactored; per-feature mutation gate ≥80% on modified files.
4. Code reviewed (self-review with reviewer agent — solo project).
5. Merged to main.
6. Deployed to the phone-reachable production URL via the existing pipeline.
7. Dogfooded same day: one real backfill or correction on the phone (plus a normal morning log confirming zero added friction).
8. KPI-8 marker visible on /stats; KPI-1 sample purity verified (a backdated save adds 0 speed samples); ≤2 s and tap-count guardrails verified.
9. Story demonstrable end-to-end on the phone.

### [REF] Wave Decisions Summary

Locked: D1–D5 + user decisions D6–D8 (native always-visible date input defaulting to today; prefill-with-hint edit; post-save reset to today). Prior assumptions A1–A19 unchanged and still binding.

New assumptions (chosen during requirements, flagged for confirmation):

- **A20** The date control is a native `<input type="date">` with `max` = device-local today (same `deviceLocalDay()` source as the save payload); the server's skew-bounded no-future rule remains the authority.
- **A21** One hint line: date = today → yesterday anchor (as today); past day with entry → `Editing {day} — was {v} kg`; past day without entry → `No entry for {day} yet`. Never stacked.
- **A22** After every successful save (today-dated or not): date resets to device today, weight field clears, confirmation names the saved date; the existing save-response refresh (graph + glance + recent list) is reused unchanged — backdated entries are included by construction (`all_entries()` recompute).
- **A23** KPI-1 sample purity: only today-dated saves contribute entry-speed samples; the today/backdated distinction is computed from the existing trail (payload date vs event day) — mechanism = DESIGN, requirement = 0 samples from backdated saves.
- **A24** Prefill must be correct for **any** stored day; the recent-days map may serve recent days, but the lookup mechanism for older days (full fetch vs on-demand read) is DESIGN's call, with degrade-to-absent (no-entry presentation, save unaffected) on lookup failure.

Open questions (non-blocking; defaults apply unless overridden):

- **OQ-10** Confirm hint wordings (`Editing Thu 23 Jul — was 82.4 kg` / `No entry for Sun 19 Jul yet`) — or prefer terser forms?
- **OQ-11** No lower bound on the date (any past day accepted, matching the backend). Impose one (e.g., not before the first entry — or allow, for pre-history backfill toward the old app's record)? Default: unbounded past, which keeps the door open for manual historical backfill.

Risk notes (DISCUSS-era; the AT-contract item is corrected at DESIGN — see § Changed Assumptions): **product risk** = the date row adds a visible element to the five-second screen — mitigated by D6 (native, zero-tap default) and the tap-count + ≤2 s ACs; falsifiable at first dogfood morning. **Metric risk** = KPI-1 poisoning by slow maintenance saves — pinned as a hard @property AC (0 samples), same discipline as graph-first-home's KPI-3 purity. **Overwrite risk** = blind edits — mitigated by D7 prefill+hint and the gap-vs-entry distinction (US-014). **AT-contract risk** = existing entry ATs assert the hardcoded device-day submission — flagged for conscious renegotiation at DISTILL, never silent deletion. Technical risk negligible (save path, validation, upsert, refresh all shipped and mutation-tested). JTBD traceability intact (both stories → `js-3-maintain`; no new moment). No DIVERGE — user = customer, D6–D8 decided directly (accepted pattern). Density: lean + ask-intelligent; triggers evaluated (AC ambiguity ≥2 stories, ≥3 bounded contexts, ≥3 personas, compliance terms, WS strategy D) — **none fired** → silent lean. Density telemetry skipped: `scripts/shared/telemetry.py` not present in this repository (recorded here in lieu of the event, per prior features).

## Wave: DESIGN

Architect: solution-architect (Morgan), 2026-07-24. Mode: Propose (the 2 mechanisms DISCUSS left open — A24 prefill lookup, A23 KPI-1 sample purity — plus OQ-10/OQ-11, analyzed against the live codebase; user accepted all recommendations). SSOT updated: `docs/product/architecture/brief.md` (§ Application Architecture — entry-date-picker delta paragraph, ADR index) + new `adr-010-prefill-delivery.md` + new `adr-011-backdated-save-classification.md`. ADR-001…009 unchanged; **none superseded**. Paradigm not re-decided (ADR-005 / CLAUDE.md: Functional Core / Imperative Shell). No C4 L1/L2 changes (no new containers, actors, external systems, routes, or origins); no L3 (below the 5-component threshold). Per-wave peer review deferred to the orchestrator's consolidated review at DISTILL (precedent: home-trend-display, graph-first-home) — no contested ADR, no novel pattern, no unverified performance budget, no security-boundary change (no new route; AccessGate, auth, and origins untouched). Density: lean, Tier-1 [REF] only, no Tier-2 expansions; density telemetry skipped (`scripts/shared/telemetry.py` absent).

### [REF] DDD List

Numbering continues the global DESIGN sequence from D-20 (graph-first-home); the DISCUSS decisions D1–D8 above are this feature's own local sequence.

- **D-21 Prefill lookup = whole-record `{iso_day: kg}` map rendered inline on `GET /`** (ADR-010) — **accepted**. The shipped 4-entry `recent_weights_map` (`routes.py:214-218`) widens to the whole record; **one** client map serves both the yesterday anchor and the prefill. Zero added I/O (`store.all_entries()` is already read at `routes.py:412`), zero async, zero new failure mode, and — decisively — the "any stored day prefills" AC stays assertable with the **shipped browser-less AT harness** (`steps/composition.py:565, 592-604` already extracts the embedded map and emulates the client lookup). Byte cost quantified in ADR-010 (~5.6 KB/yr, ~56 KB at ten years ⇒ ≤3 % of the 2 s budget). Rejected: lazy fetch of `GET /entries?scale=ALL` (async race, wrong-then-right hint flicker on a trust-building feature, headline AC unobservable in this suite); hybrid seeded+extended map (same flicker + two freshness semantics, unearned at a ~135-entry record); bounded window (fails A24 outright — a March-2026 entry must prefill in 2028).
- **D-22 Backdated classification at write time from the phone's claimed day** (ADR-011) — **accepted**. The save body gains an optional `today` field (the same device-day claim `?today=` already carries on reads, `routes.py:143-165`); after validation, a pure classifier decides `backdated = entry_day != device_today_frame` (parsed + skew-clamped claim, falling back to server UTC today when absent or garbled — a telemetry concern must never block or 400 a save). Backdated ⇒ `entry_ms` recorded **null**, so KPI-1 purity rides the shipped null-skip (`telemetry_store.py:36-44`) with zero read-side change. Falsifiable at the HTTP boundary. Rejected: client-omission convention (purity unfalsifiable — the AT would assert its own payload); read-time classification (skew collision, ADR-011 § Context).
- **D-23 KPI-8 marker = `"backdated": true` on the `entry.saved` payload + new `backdated_saves_since` read query** — **accepted**. Copies the payload-parsing shape of `entry_ms_samples_since`, wired by `partial` at the composition root (`composition.py:77-78`). Rejected: a second event name (`entry.backdated.saved`) counted by the existing name-parameterised `count_events_since` — cheaper to read, but it would widen `WeightLogging`'s bounded-change universe to two events per save; **one `{date}` row + one `entry.saved` event stays pinned** (brief.md § Application Architecture, D-13/D-19 precedent). Deliberately **not** stamping a `repair_ms`: KPI-8's ≤30 s is self-reported at dogfood; if ever automated it gets its own field, never the morning-speed field.
- **D-24 One hint element, three states** (A21) — **accepted**. `#yesterday-reference` → `#entry-hint`, never removed from the DOM (today's code removes it, `index.html:88`), text from a pure client function `hintFor(selectedDay, deviceToday, knownWeights)`. "Never two hints" is **structural** (one node), not conventional. Day labels reuse `dayLabel(iso)` extracted from the shipped client `entryRowText` (`index.html:123-127`) — one `Fri 24 Jul` grammar. OQ-10 resolved at the DISCUSS wordings verbatim; `yesterday: 82.4 kg` unchanged.
- **D-25 Date row = native input, client-framed, non-disturbing** — **accepted**. `value` and `max` = `deviceLocalDay()` set by the one inline script (the server cannot know the device day, A5); `min` = **first entry day − 1 year** (OQ-11 resolved: pure UX assist against a mistyped year; server rules unchanged, widening later is one attribute). The server hands the first-entry day to the template for free from the `all_entries()` read it already performs (`entries[-1].day`, newest-first); empty record ⇒ no `min`, no map. No `autofocus` on the date input; the hint line reserves its height permanently (it now changes mid-session — precedent and technique: `theme.css:139-144`). Post-save the date resets to device today and the hint re-derives (D8/A22).
- **D-26 Zero port-protocol changes; one additive optional field on the save message** — **accepted**. `ports.py` untouched; read-only ports gain **no methods at all** (strongest form of "no write methods"). The `today` claim is additive, optional and backward-compatible (absent ⇒ server-UTC frame), so every existing caller — curl and the AT seeding helpers at `steps/composition.py:273-296` — keeps working unchanged. Stated as a delta rather than "zero" on purpose: it belongs in the composition-root route contract and in OUT-1's input shape.

### [REF] Component Decomposition

Delta only — authoritative table: `brief.md` § Component Decomposition and Ports.

| Component | Path | Change |
|---|---|---|
| Entry template + its one inline script | `src/weight_tracker/web/templates/index.html` | EDIT: date row above the weight field (no autofocus); one `#entry-hint` node; pure `hintFor` + extracted `dayLabel`; submit payload `{date: picker, today: deviceLocalDay(), weight, entry_ms}`; post-save reset (date → device today, field cleared, hint re-derived); save-response `date`/`weight_kg`/`recent` merged into the client map. No new script file. |
| Route `GET /` | `src/weight_tracker/web/routes.py` | EDIT: `recent_weights_map` → `record_weights_map` (whole record, same `{iso: kg}` shape, same template slot); context gains the first-entry day for `min`. Same single `all_entries()` read. |
| Route `POST /entries` | `src/weight_tracker/web/routes.py` | EDIT: read the optional `today` claim; classify **after** validation; withhold `entry_ms` (null) when backdated; stamp `"backdated"` in the `entry.saved` payload. Response shape unchanged. |
| Route `GET /stats` | `src/weight_tracker/web/routes.py` | EDIT: one new rolling-week counter (KPI-8) beside the shipped ones. |
| Pure day judgment | `src/weight_tracker/core/validation.py` | EDIT: `bounded_day_frame(claimed, server_utc_today) -> date \| None` (clamp arithmetic extracted from `day_frame_or_bad_request` — one copy of the calendar rule) + `is_backdated(entry_day, device_today) -> bool`. Total, clock-free. |
| Telemetry read model | `src/weight_tracker/shell/telemetry_store.py` | EDIT: **CREATE** `backdated_saves_since(db_path, since) -> int` (payload predicate; `entry_ms_samples_since` pattern). |
| Composition root | `src/weight_tracker/composition.py` | EDIT: one `partial(...)` wiring + route-contract docstring (the `today` field, the purity rule). |
| Theme stylesheet | `src/weight_tracker/web/static/theme.css` | EDIT: `#entry-date` + `#entry-hint` block rules (reserved line height, AA both schemes, ≥44 px), `#yesterday-reference` selector renamed. Tokens only. |
| Shared graph module | `src/weight_tracker/web/static/graph.js` | **UNCHANGED** — the `entry-saved` refetch (`graph.js:200-202`) already repaints backdated saves by construction. |
| SQLite adapter / schema | `src/weight_tracker/shell/entry_store.py` | **UNCHANGED** — `entry_ms` already nullable; **no migration**, `CODE_SCHEMA_VERSION` stays 1. |
| `ports.py`, `core/trend.py`, `core/glance.py`, `core/types.py`, `shell/access_gate.py`, `static/sw.js` | — | **UNCHANGED** (no new asset ⇒ no APP_SHELL change, no cache bump). |

### [REF] Driving Ports

| Port | Delta |
|---|---|
| `WeightHistory` | **Unchanged; no method added.** The whole-record map is a pure projection of a read the driving adapter already performs — identical in kind to `recent_head` / `recent_entry_rows` / `complete_record_rows` (`routes.py:226-252`) and to D-18's "last-7 list = pure slice of the `all_entries()` read". Read-only stays read-only. |
| `TrendProjection` / `GlanceProjection` | **Unchanged.** A backdated save recomputes both from the refreshed full entry set (`routes.py:463`) — no new window, no second algorithm. |
| `WeightLogging` | **Message extended additively**: optional `today` claim (absent ⇒ server-UTC frame). Effect universe **unchanged** — one `{date}` row + one `entry.saved` event. The `backdated` payload field is route-level enrichment on the shipped `confirmation` / `glance` / `recent` precedent. |
| `AccessGate` | Unchanged; no new route to guard. |

### [REF] Driven Ports + Adapters

**None new — explicitly.** No new I/O, storage, external dependency, or clock use ⇒ **no new Earned-Trust probes**; `EntryStorePort.probe()` and the AST probe-presence gate (`scripts/check_probe_presence.py`) are untouched. The one newly trusted input is the phone's claimed day: bounded by `MAX_DEVICE_SKEW_DAYS` and backstopped by the server's authoritative no-future rule (`validate_entry_date`, `core/validation.py:46-59`), so the substrate lie "the device clock is wrong" is contained by construction. Fault injection instead (DISTILL): map key absent ⇒ no-entry presentation, save unaffected; map absent entirely ⇒ script guard, save unaffected; garbled/absent `today` claim ⇒ server-UTC frame, save never blocked and never 400.

### [REF] Technology Choices

**Zero new dependencies, zero new external origins, zero new assets, zero new routes.** Native `<input type="date">` (D6) — no picker library, as locked at DISCUSS. Enforcement tooling unchanged (import-linter layers, mypy strict, AST probe-presence gate — no new adapters to cover). No contract-test annotation change: no application-level third-party API exists (brief.md § External Integrations stands).

### [REF] Hint Line State Machine (A21)

One DOM node (`#entry-hint`), never removed; text from the pure `hintFor(selectedDay, deviceToday, knownWeights)`.

| Condition | Line |
|---|---|
| `selected == deviceToday`, yesterday known | `yesterday: 82.4 kg` (wording unchanged — keeps the AT fallback regex `steps/composition.py:568` honest) |
| `selected == deviceToday`, no yesterday | hidden (line height still reserved) |
| `selected != deviceToday`, day known | `Editing Thu 23 Jul — was 82.4 kg` |
| `selected != deviceToday`, day unknown | `No entry for Sun 19 Jul yet` |

"Never two at once" is structural: there is one node. Day label = shared `dayLabel(iso)`, the same `Fri 24 Jul` grammar as `entry_row_text` (`routes.py:238`) and `Saved.confirmation` (`core/types.py:115-118`).

### [REF] Date Row Rules (D6/D8/A20/A22 + KPI-1 guardrail)

- **Prefilled + bounded**: `value` = `max` = `deviceLocalDay()`, set by the inline script (A5 — the server has no device day). `min` = first entry day − 1 year, server-supplied, omitted on an empty record. All three are **UX assist only**; `validate_entry_date` remains the authority and `POST /entries` still rejects forged future dates exactly as today.
- **No focus theft**: `autofocus` stays on `#weight` alone; setting `.value` / `.max` / `.min` never moves focus.
- **No reflow**: the hint line reserves its height permanently (it now changes *during* the session, not only before first paint); the date input's box is value-independent and inherits the shipped `input { min-height: 44px; width: 100% }`. Precedent and technique: `#home-graph #chart { min-height: 320px }` — *"the entry form never jumps under the thumb"* (`theme.css:139-144`).
- **Post-save reset**: the success branch already clears the field and refocuses (`index.html:172,177`); add `dateInput.value = deviceLocalDay()` and re-derive the hint. The save response's `date` / `weight_kg` (`routes.py:467-468`) **and** `recent` (`routes.py:473`) are merged into the client map so the anchor and prefill stay fresh with no reload — both are already on the wire, free.
- **Confirmation**: no change — `Saved.confirmation` already names the saved date.

### [REF] FC/IS Placement (ADR-005)

| Layer | What lands there |
|---|---|
| **Pure core** — `core/validation.py` | `bounded_day_frame`, `is_backdated`. Total over hostile input, no clock, no I/O; Hypothesis-testable across the full skew range. |
| **Shell / route** — `web/routes.py` | Read the `today` claim; classify after validation; withhold `entry_ms`; stamp the payload marker; widen the map projection; one `/stats` key. Route-level enrichment, explicitly not a port widening. |
| **Shell / read model** — `shell/telemetry_store.py` | `backdated_saves_since`. |
| **Shell / client** — `index.html` inline script | `hintFor` and `dayLabel` kept **pure**; every DOM write isolated in one apply site; the map is read-only client state merged from the save response. |
| **Static asset** — `theme.css` | Presentation only. |

### [REF] Decisions Table

| # | Decision | ADR |
|---|---|---|
| D-21 | Prefill = whole-record `{iso_day: kg}` map inline on `GET /`; zero added I/O; reversal trigger at ~2,000 entries | ADR-010 |
| D-22 | Backdated classification at write time from the phone's claimed `today`; backdated ⇒ `entry_ms` null (0 KPI-1 samples via the shipped null-skip) | ADR-011 |
| D-23 | KPI-8 = `"backdated": true` payload flag + new `backdated_saves_since` query; one event per save stays pinned | ADR-011 |
| D-24 | One `#entry-hint` node, three states, pure `hintFor`, shared `dayLabel`; OQ-10 at DISCUSS wordings | brief.md |
| D-25 | Date row: client-set `value`/`max`, server-supplied `min` = first entry − 1 year (OQ-11), no autofocus, reserved hint line, post-save reset | brief.md |
| D-26 | Zero port-protocol changes; one additive optional `today` field on the save message | brief.md |

### [REF] Reuse Analysis

Brownfield — **one CREATE NEW** (a read-model query), everything else EXTENDs or leaves shipped components untouched (codebase verified 2026-07-24). Default is EXTEND.

| Existing component | Evidence | Verdict | Contract shape · universe · crafter assertion mechanism |
|---|---|---|---|
| `recent_weights_map` | `routes.py:214-218`; consumed at `index.html:81-93` | **EXTEND** → `record_weights_map` (drop the head-4 slice) | pure-function (return-only) · universe ∅ · existing map-regex AT (`steps/composition.py:565,599`) + new "March day prefills" AT |
| `RECENT_ANCHOR_ENTRIES = 4` | `routes.py:211` | **RETIRE** (sole consumer above) | — · — · absence check |
| `entry_row_text` / `recent_head` / `recent_entry_rows` / `complete_record_rows` | `routes.py:226-252` | **NO CHANGE** | pure-function · universe ∅ · shipped milestone-8/9 scenarios |
| client `entryRowText` | `index.html:123-127` | **EXTEND** (extract `dayLabel(iso)`) | pure JS · universe ∅ · hint-text ATs + shipped repaint ATs |
| `deliver_glance` / `glance_or_degrade` | `routes.py:344-367` | **NO CHANGE** — pure function of the full set; backdated saves recompute via `refreshed` (`routes.py:463`) | unchanged · 0–1 `trend.glance.shown` per delivery · milestone-6 |
| `validate_entry_date` | `core/validation.py:46-59` | **NO CHANGE** — no-future stays authoritative; unbounded past already permitted | pure-function, total · universe ∅ · milestone-3 |
| `day_frame_or_bad_request` | `routes.py:143-165` | **EXTEND** (extract the pure clamp into core; shell keeps the 400) | pure `bounded_day_frame` · universe ∅ · PBT over skew + `device-day-frame.feature` |
| `entry_ms_samples_since` | `telemetry_store.py:34-44` | **NO CHANGE** — the null-skip *is* the purity mechanism | read-only query · universe ∅ · `@property` AT: backfill ⇒ sample count unchanged |
| `count_events_since` | `telemetry_store.py:20-31` | **NO CHANGE** — name-parameterised; KPI-8 needs a payload predicate | read-only · universe ∅ · — |
| KPI-8 counter | no payload-filtering query exists | **CREATE NEW** `backdated_saves_since` (pattern copied from `entry_ms_samples_since`; different predicate + return) | read-only query · universe ∅ · `/stats` AT |
| inline entry script | `index.html:67-184`; G-5 pin `steps/composition.py:1150-1165` | **EXTEND** (no new script file) | shell · DOM effects at one apply site · G-5 script-count AT stays green |
| `graph.js` | `graph.js:200-202` | **NO CHANGE** | unchanged · universe ∅ · milestone-8 post-save refresh |
| `theme.css` | `theme.css:111-144` | **EXTEND** (`#entry-date`, `#entry-hint` reserved line) | static asset · universe ∅ · G-4 contrast AT (both schemes) + G-2 no-reflow |
| `POST /entries` response | `routes.py:464-474` | **NO CHANGE** — `confirmation` / `glance` / `recent` already suffice | route enrichment · universe unchanged · milestone-8 |
| `Saved.confirmation` | `core/types.py:115-118` | **NO CHANGE** — already `Saved: 82.4 kg — Tue 21 Jul` | pure-function · universe ∅ · milestone-1 |
| `entries` schema | `entry_store.py:35-39,183` | **NO CHANGE** — `entry_ms` nullable, no migration | bounded-change · one `{date}` row · schema-version probe unchanged |
| `/stats` route | `routes.py:563-594` | **EXTEND** (one key) | read-only route · universe ∅ · `/stats` AT |
| composition wiring | `composition.py:77-79` | **EXTEND** (one `partial`) | shell · universe ∅ · startup + route-contract docstring |

### [REF] C4 Note

**No diagram changes.** L1/L2 in `brief.md` remain accurate: everything lands inside the existing Browser/PWA-shell and App Server containers. No new container, route, dependency, or external origin. No L3 — below the 5-component threshold.

### [REF] Open Questions / DISTILL–DELIVER Notes

| # | Note | Owner |
|---|---|---|
| R-1 | **AT renegotiation touchpoints (corrected — see § Changed Assumptions).** Three, all loud-failure: (a) `RECENT_WEIGHTS_MAP = re.compile(r"const recentWeights = (\{[^;]*\});")` (`steps/composition.py:565`) breaks on the `recordWeights` rename — the fallback branch then fails on a *missing value*, never passes silently; (b) OUT-1's input shape gains the optional `today` claim; (c) milestone-5 `assert_ready_for_typing` (`steps/composition.py:587-590`) is **extended, not amended**, with no-focus-theft and reserved-hint-line assertions. Renegotiate all three in one commit with the G-5 comment pattern (`steps/composition.py:1150-1156`) as the template. Never silent. | DISTILL |
| R-2 | **`kpi-contracts.yaml` KPI-1 already diverges from shipped code, and this feature makes it matter.** The contract's query reads `entries.entry_ms` (kpi-contracts.yaml:74-77) while `/stats` reads the **events trail** (`routes.py:593`). Correcting a past day upserts `entry_ms = NULL` over that row (`entry_store.py:178-183`), erasing the original morning's timing from `entries` — harmless for `/stats` (the append-only trail preserves it), corrupting for the documented ad-hoc query. Fix: pin the trail as KPI-1 SSOT and update the contract file. | DISTILL |
| R-3 | **KPI-5 / KPI-7 denominators.** Both pair on `DISTINCT date(ts) FROM events WHERE name='entry.saved'` (kpi-contracts.yaml:128-132, 149-153). A repair on a non-logging day now creates an `entry.saved` row on that day, inflating the "logging days" denominator. The `backdated` flag makes the exclusion one `WHERE` clause. Same class for KPI-2 adherence (a backfill retroactively improves a past week — arguably honest, since the record *is* now complete; optional refinement via `logged_at` vs `date`). Not blocking. | DISTILL |
| R-4 | **Resolved at DESIGN** (OQ-11): `min` = first entry day − 1 year as a pure UX assist. Rationale worth keeping: the trend grid spans first→last entry day, so one mistyped year would permanently stretch every recompute to ~3,650 grid points — and entry deletion is out of scope, making recovery manual SQL. | — |
| R-5 | **Resolved at DESIGN** (OQ-10): DISCUSS hint wordings accepted verbatim; `yesterday: 82.4 kg` unchanged. Terser forms would fork the shipped `Fri 24 Jul` / em-dash grammar. | — |
| Q1 | New AT surfaces to author: "any stored day prefills" (map extraction, March key), the three hint states + singularity, post-save reset, `@property` "backdated saves add 0 KPI-1 samples" **and** "+1 KPI-8", `min`/`max` bounds present, degrade-to-absent on a missing map key. | DISTILL |
| Q2 | Outcome-registry delta entries (OUT-10 dated-entry prefill delivery, OUT-11 KPI-1 sample-purity invariant) + OUT-1 input-shape amendment; `nwave-ai outcomes check-delta` re-check. | DISTILL |
| Q3 | `kpi-contracts.yaml`: add KPI-8 and the `entry.saved` `backdated` payload field to the events contract. | DISTILL |
| Q4 | Mutation gate ≥80 % scoped to the modified files, per CLAUDE.md per-feature strategy. | DELIVER |

### Changed Assumptions

**A20, A21, A22 hold as written.** **A23 and A24 are resolved, not changed** — both moved from "mechanism = DESIGN" to decided (D-22/D-23 and D-21) with their stated requirements met exactly: 0 KPI-1 samples from backdated saves, KPI-8 countable on /stats, prefill correct for any stored day, degrade-to-absent on lookup failure, read-only ports still read-only. OQ-10 and OQ-11 resolved (R-5, R-4). A1–A19 unchanged.

**One DISCUSS risk statement is corrected.** DISCUSS wrote, in `docs/feature/entry-date-picker/feature-delta.md` § Pre-Requisites: *"For DISTILL: existing entry-screen ATs assert the hardcoded `deviceLocalDay()` submission — renegotiate consciously to 'selected date, defaulting to device day', never silently."* and, in § Wave Decisions Summary: *"**AT-contract risk** = existing entry ATs assert the hardcoded device-day submission — flagged for conscious renegotiation at DISTILL, never silent deletion."*

Codebase verification (2026-07-24) finds **no acceptance test that asserts the hardcoded submission**. The hardcoding lives only in the client, at `src/weight_tracker/web/templates/index.html:157` (`date: deviceLocalDay()`); the AT suite has no browser and posts JSON directly (`tests/weight-trend-tracker/acceptance/steps/composition.py:273-296`). The renegotiation is therefore real but **different in kind** — it is the three touchpoints listed in R-1 (map-regex rename, OUT-1 input shape, milestone-5 extension), all of which fail loudly rather than silently. The DISCUSS instruction "never silently" is honored; its stated target was inaccurate. Flagged here rather than edited in place, per the never-silent discipline.

## Wave: DISTILL

Acceptance designer, 2026-07-24. Reconciliation gate: all prior wave decisions read (DISCUSS D1–D8/A20–A24 + OQ-10/OQ-11, DESIGN D-21–D-26 + ADR-010/ADR-011 + § Changed Assumptions; no DEVOPS wave — brownfield on the shipped pipeline, WARN logged) — **0 contradictions**. DESIGN's correction of the DISCUSS AT-contract risk statement is a resolved, documented correction, not an open contradiction. Deliverable type: `application` (`.nwave/des-config.json` declares no `deliverable_type`; `~/.nwave/global-config.json` sets no default → FS detection) ⇒ no plugin/skill reviewer routing. Infrastructure policy: `--policy=inherit` — zero missing ports; the Architecture of Reference is unchanged (driving = TestClient over `build_app`, driven-internal = real SQLite on `tmp_path` with production pragmas, driven-external = `FakeClock` only). Density: lean, Tier-1 `[REF]` only; density telemetry skipped (`scripts/shared/telemetry.py` absent in this repository — recorded here per prior features).

### [REF] Scenario List

Scenario SSOT: `tests/weight-trend-tracker/acceptance/milestone-10-dated-entry.feature` (Slice 01 — US-013 + US-014). **13 scenarios / 14 executions** (one 2-example outline), all `@pending` (one-at-a-time, ADR-025). Error/edge share ≈ **42 %**.

| Scenario | Tags |
|---|---|
| A forgotten day is backfilled from the entry screen | `@pending @driving_port @US-013 @contract-shape:bounded-change` |
| The morning flow never pays for the picker | `@pending @driving_port @property @kpi @US-013 @contract-shape:pure-function` |
| The picker cannot wander off before the record began | `@pending @driving_port @US-013 @contract-shape:pure-function` |
| The future stays closed however the phone frames its day | `@pending @driving_port @error @kpi @US-013 @contract-shape:unbounded-preservation` |
| A slow repair never slows the morning record | `@pending @driving_port @property @kpi @real-io @adapter-integration @US-013 @contract-shape:bounded-change` |
| A morning still counts as a morning | `@pending @driving_port @kpi @US-013 @contract-shape:bounded-change` |
| A phone that will not say which day it is on is still served *(outline, 2 examples)* | `@pending @driving_port @error @US-013 @contract-shape:bounded-change` |
| Any day of the record answers the picker | `@pending @driving_port @US-014 @contract-shape:pure-function` |
| A gap is offered as a gap, never as a value | `@pending @driving_port @error @US-014 @contract-shape:pure-function` |
| A mistyped past day is corrected in place | `@pending @driving_port @US-014 @contract-shape:bounded-change` |
| Correcting a timed morning leaves the week's mornings intact | `@pending @driving_port @error @kpi @US-014 @contract-shape:bounded-change` |
| One hint line serves the anchor and the repair alike | `@pending @driving_port @US-014 @contract-shape:pure-function` |
| An empty record still opens straight into typing | `@pending @driving_port @error @US-013 @US-014 @contract-shape:pure-function` |

Both `@property` scenarios are layer-3 (real HTTP + real SQLite) ⇒ **example-pinned**, per Mandate 9/11; the quantified budgets (≤2 s interactive, 22 000 ms repair vs 4 200 ms morning) live in the scenario text. No new pure-core PBT files are authored here: `bounded_day_frame` / `is_backdated` are DELIVER's to write against (ADR-025 — DISTILL owns ATs, DELIVER owns paired PBTs), and a PBT importing an unbuilt module would manufacture a BROKEN import where none exists today.

**Deliberately not asserted (client-structural, dogfood-verified — the client-paint precedent D-15):** the picker's `value` and `max` (the server has no device day, A5), the hint's rendered wording, the post-save reset of the date row, and the form's submission of the picked date. ADR-011 gives the reason plainly: a browser-less suite composes its own payloads, so a purity rule resting on client omission is one "no acceptance test can falsify" — which is exactly why the classification moved server-side, where these scenarios pin it.

### [REF] Walking Skeleton Strategy

**N/A — brownfield (locked D2).** The production vertical and its `@walking_skeleton` scenario (`walking-skeleton.feature`, green) exist; this feature rides them. No strategy negotiation performed; the project policy is inherited unchanged.

### [REF] Adapter Coverage

**No new driven adapters (DESIGN: explicitly none)** ⇒ no new `@real-io` adapter scenarios owed, no new Earned-Trust probes, no schema migration. The one newly trusted input — the phone's claimed day — is covered as a driving-adapter concern below. Fault-injection coverage per DESIGN's list:

| Fault (DESIGN) | Scenario |
|---|---|
| Map key absent ⇒ no-entry presentation, save unaffected | A gap is offered as a gap, never as a value |
| Map absent entirely ⇒ script guard, save unaffected | An empty record still opens straight into typing (server half: nothing offered, entry still ready). The client guard itself is structural — one inline script, dogfood-verified |
| `today` claim absent ⇒ server-UTC frame, save never blocked | A phone that will not say which day it is on… (example 1) |
| `today` claim garbled ⇒ server-UTC frame, never a 400 | A phone that will not say which day it is on… (example 2) |
| Forged future date ⇒ server rejection, trail untouched | The future stays closed however the phone frames its day |

### [REF] Driving Adapter Coverage

Every DESIGN entry point exercised over its real protocol (TestClient = the real ASGI/HTTP layer):

| Entry point (DESIGN) | Scenarios |
|---|---|
| `GET /` — date row, `min` bound, one hint node, whole-record map | The morning flow never pays for the picker; The picker cannot wander off…; Any day of the record answers the picker; A gap is offered as a gap…; One hint line serves…; An empty record still opens… |
| `POST /entries` — optional `today` claim, classification after validation, withheld `entry_ms`, payload marker | A forgotten day is backfilled…; A slow repair…; A morning still counts…; A phone that will not say…; A mistyped past day…; Correcting a timed morning…; The future stays closed… |
| `GET /stats` — new `backdated_saves_this_week` beside the unchanged `speed` report | every `@kpi` scenario |
| `GET /trend` — recompute over the repaired record (pure read) | A forgotten day is backfilled…; A mistyped past day is corrected in place |
| `GET /entries` — the record read-back that oracles the map | Any day of the record answers the picker |

### [REF] Scaffolds

**Zero production scaffold files needed (Mandate 7 satisfied structurally).** Acceptance tests reach the SUT exclusively over HTTP through the production composition root; no test imports an unbuilt production module, so there is no ImportError surface and no BROKEN class. The RED anchors are HTTP-observable absences (see § RED Gate). Test-side infrastructure added — import-clean, every step defined: `steps/steps_dated_entry.py` (21 decorators), `DatedEntryService` in `steps/composition.py`, binding `steps/test_milestone_10.py`, typed vocabulary `DayClaim` / `CLAIM_PHRASES` / `day_label` in `steps/domain_types.py`, markers `us_013` / `us_014` in `pyproject.toml`.

### [REF] Test Placement

`tests/weight-trend-tracker/acceptance/` — the project's single acceptance tree (milestone-N precedent, features 1–9 landed the same way; `pythonpath` already pinned in `pyproject.toml`).

### [REF] Executable Contracts (DELIVER pre-requisites)

The oracles pin these shapes — the crafter implements TO them:

- **Markup**: the date row is `<input type="date" id="entry-date">`, **inside** the entry form and **above** `#weight`, carrying **no** `autofocus`; `min` = first entry day − 1 year (server-supplied, omitted on an empty record); `value` / `max` client-set. Exactly one `autofocus` on the page (the weight field) and no `tabindex` anywhere.
- **One hint node**: `<p id="entry-hint">` present on every render (never removed server-side, height reserved); `id="yesterday-reference"` retired — its presence beside the new node fails the scenario.
- **Embedded map**: `const recordWeights = {…}` inside the one inline script = the **whole** record as `{iso_day: kg}`, equal to the `/entries?scale=ALL` read-back. One map for the anchor AND the prefill.
- **Save message**: `POST /entries` accepts an additive, optional `today`; classification runs **after** `validate_entry_date`; `backdated = date != skew-clamped claim`; absent/garbled claim ⇒ server-UTC frame, **never** a 400. Backdated ⇒ `entry_ms` recorded NULL **and** `"backdated": true` on the `entry.saved` payload. Response shape unchanged (`confirmation` / `date` / `weight_kg` / `glance` / `recent` all still ride it, including for a repair).
- **`/stats` key**: `backdated_saves_this_week` (KPI-8), same rolling-week frame as its neighbours, served by the new read-model query `backdated_saves_since` (the `entry_ms_samples_since` pattern, wired by `partial`).
- **Grammar**: the hint's day label is `dayLabel(iso)` = `Thu 23 Jul` — asserted equal to the day half of the server's own rendered row, so a second calendar wording cannot appear.

### [REF] Inherited-AT Renegotiations (never silent)

1. **Map const rename (DESIGN R-1a) — green before AND after.** `RECORD_WEIGHTS_MAP` (`const recordWeights`) is read first, the shipped `RECENT_WEIGHTS_MAP` (`const recentWeights`) kept as fallback, the pre-fix server-rendered paragraph beneath it. A page carrying neither still fails on the missing VALUE, never on a missing marker. Pattern: the G-5 sanctioned-set amendment.
2. **OUT-1 input shape (DESIGN R-1b).** Amended in `docs/product/outcomes/registry.yaml` with the optional `today` claim and the explicit note that every pre-existing caller keeps working.
3. **Entry readiness (DESIGN R-1c) — resolved DIFFERENTLY from DESIGN's suggestion, deliberately.** DESIGN proposed extending the shared `assert_ready_for_typing`; that would red roughly a dozen shipped scenarios for the whole of DELIVER. Instead the readiness guarantee is extended by a NEW `@pending` scenario ("The morning flow never pays for the picker") composing the shipped readiness assertion with the date-row, ≤2 s and no-focus-theft clauses. Shipped scenarios stay green; the new guarantee is still pinned. Surviving intent identical.
4. **Timed-morning seeding — found at DISTILL, NOT listed in DESIGN R-1.** `seed_timed_week` seeded a whole week in one instant. Under ADR-011's write-time classification that is indistinguishable from seven repairs, and would strip six of the seven timings out of the KPI-1 report. The helper now walks the clock and each save claims its own day — because a morning **is** a same-day save. It fails loudly (milestone-5 asserts `sample_count == 7`), and is fixed here rather than surfacing as a mystery red mid-DELIVER. This is the concrete form the DISCUSS "AT-contract risk" actually took.

### [REF] RED Gate

`docs/feature/entry-date-picker/distill/red-classification.md`: **9 RED (all `MISSING_FUNCTIONALITY`, AssertionError only) / 5 GREEN-preserved / 0 BROKEN**, over 14 executions. Two authoring defects were caught and fixed by the first gate run (a scenario-frame contradiction — backfilling a day the timed week had already seeded; and a capture that shadowed 8 scenarios' own headline assertions behind the missing KPI-8 counter). Full suite unchanged before and after the harness renegotiations: **165 passed, 14 `@pending` skipped**.

The high GREEN-preserved count is the honest signature of this feature, not a gap: D2 pinned it as a presentation delta on a **shipped** backend, so the backfill/correct save path, its refreshed picture and its trend recompute already work — those scenarios are regression guards. Every genuinely new commitment has its own RED anchor, and the sharpest one is live: a 22-second backfill currently moves `speed.sample_count` 7 → 8, which is precisely the metric poisoning A23 exists to prevent.

### [REF] Registered Outcomes

**OUT-10** (operation: whole-record prefill delivery — any stored day answers the date row, degrade-to-absent, read-only ports unwidened) and **OUT-11** (invariant: KPI-1 sample purity — a repair is never counted as a morning; `entry_ms` NULL + `backdated` marker; the trail, not `entries.entry_ms`, is KPI-1's source of truth) added to `docs/product/outcomes/registry.yaml`; **OUT-1**'s input shape amended with the optional `today` claim. Registered manually: `nwave-ai outcomes register` still fails on the mis-packaged `schema.json` (documented upstream tool defect, OUT-7/OUT-8/OUT-9 precedent). `nwave-ai outcomes check-delta` re-check remains owed once fixed upstream.

### [REF] SSOT Updates

`docs/product/kpi-contracts.yaml`:

- **KPI-8 added** (in-app record repair: 100 % of noticed defects repairable, ≤30 s self-reported; instrument = the `backdated` payload flag, read as `backdated_saves_this_week`).
- **`entry.saved` payload contract extended** — `entry_ms` documented as NULL for repairs, new `backdated` field. No new event name: the save's effect universe stays one `{date}` row + one `entry.saved` event.
- **KPI-1 SSOT corrected (DESIGN R-2)** — the append-only trail is authoritative (which is what `/stats` has always read); the documented `entries.entry_ms` query was already divergent and is now actively wrong, because correcting a past day NULLs that column. Purity rule pinned.
- **KPI-5 / KPI-7 denominators corrected (DESIGN R-3)** — "logging days" now exclude backdated saves, one `COALESCE(json_extract(payload,'$.backdated'), 0) = 0` clause each; a repair on a non-logging day no longer inflates them.
- **KPI-2 judged and left alone (R-3, second half)** — a backfill retroactively improves a past week's adherence; that is honest (the record *is* more complete), with the `logged_at` refinement recorded as deliberately not done.
- **`at_scenario_links` tightened** — KPI-8, KPI-1 (purity + the seeding renegotiation), G-2 (entry readiness with the date row present).

**Mandate-12 evidence**: (1) typed vocabulary lives in `steps/domain_types.py` — `DayClaim` + `CLAIM_PHRASES` added, `TimeScale` / `RejectionReason` / `parse_day` reused, `day_label` shares the record's one calendar grammar rather than forking a second; (2) composition services consume typed parameters (`DayClaim`, `date`, `TimeScale`) — no raw strings where an enum exists; (3) step bodies are ≤2 statements, zero control flow, every assertion in `DatedEntryService`; (4) step-reuse ratio (informational): **69 step invocations / 21 new decorators ≈ 3.28×**, with heavy additional reuse of milestones 1–9 vocabulary (record, views, glance, access steps bound as-is) — journey-rich shape, natural ceiling consistent with prior features.

### [REF] Pre-Requisites for DELIVER

None blocking. Single slice; both stories ship together (one date control carries both situations). DELIVER owes:

1. The paired pure-core PBTs for `bounded_day_frame` / `is_backdated` over the full skew range (ADR-025 split: the ATs pin the HTTP-boundary behavior, the PBTs pin the calendar arithmetic).
2. The unit-level pins for what a browser-less suite cannot reach — the client's submitted payload (picked date + `today` claim), the post-save reset to today, the picker's `value`/`max`, the hint wording — plus dogfood verification of all four (D-15 precedent).
3. `theme.css` rules for `#entry-date` / `#entry-hint`: reserved hint-line height (the line now changes mid-session), ≥44 px touch target, AA contrast in both schemes — G-4/G-2 guardrails already gated in CI.
4. No new asset ⇒ **no `sw.js` APP_SHELL list change**. One nuance surfaced by the platform review and accepted: `APP_SHELL` pre-caches `/` itself, so bump `SHELL_CACHE` to `-v4` anyway — the fetch strategy is network-first, so an online morning is unaffected either way, but the OFFLINE fallback would otherwise serve the pre-date-row entry screen until the worker reinstalls.
5. Retire `RECENT_ANCHOR_ENTRIES` with its sole consumer; `entry_ms` stays nullable — no migration, `CODE_SCHEMA_VERSION` stays 1.
6. Mutation gate ≥80 % scoped to the modified files (CLAUDE.md per-feature strategy).

### [REF] Final Wave Review Gate

Four reviewers dispatched in parallel (Haiku), 2026-07-24.

| Reviewer | Wave | Verdict |
|---|---|---|
| Eclipse (`nw-product-owner-reviewer`) | DISCUSS | **approved** — 0 blocker / 0 high / 0 low. DoR 9/9 with evidence, JTBD traceability intact (both stories → `js-3-maintain`), zero LeanUX antipatterns, all 12 DISCUSS acceptance criteria mapped to DISTILL scenarios. |
| Architect (`nw-solution-architect-reviewer`) | DESIGN | **approved** — 0 blocker / 0 high / 0 low, **zero cross-wave contradictions**. D-21…D-26 grounded in ADR-010/011; hexagonal boundary holds (read-only ports gain no methods; the `today` claim is additive route-level, not a port widening); FC/IS placement correct. |
| Forge (`nw-platform-architect-reviewer`) | DEVOPS/platform | **conditionally approved** — see disposition below. |
| Sentinel (`nw-acceptance-designer-reviewer`) | DISTILL | **approved** — 0 blocker / 0 high / 0 low. Three contract mandates pass (hexagonal boundary, business language, complete user journey); Mandate-8 universes are port-exposed; Mandate-12 step bodies ≤2 statements; oracles non-tautological (`assert_trend_reflects` against the pure series; morning-vs-repair expectations differ, so the distinction is falsifiable); the 5 GREEN-preserved scenarios judged justified. |

**Forge disposition.** Forge returned `rejected_pending_revisions` with five blockers — all five being *"the production code does not implement this yet"*: `backdated_saves_since` absent, the classification not wired into `POST /entries`, no `backdated_saves_this_week` on `/stats`, `bounded_day_frame`/`is_backdated` absent from the core, and the composition root not wiring the new query. **That is the intended state of the world at DISTILL**, and it is exactly what the RED gate records as its nine `MISSING_FUNCTIONALITY` anchors. The five are therefore accepted as DELIVER work items (they restate § Executable Contracts) and **not** as DISTILL defects; the gate is treated as conditionally approved. Of Forge's remaining findings:

- **KPI-1 SSOT correction (medium) — already applied**, in the same edit Forge was reviewing; the comment wording that misled it ("the old query below") has been clarified.
- **KPI-5 / KPI-7 denominator clauses (high) — already applied**; Forge's own evidence cites the corrected lines. Its recommendation to seed a repair on a non-logging day and assert the presence denominator excludes it is recorded as an optional DELIVER strengthening (the read-time SQL is documentation, not a served surface, so it carries no AT today).
- **Service-worker cache (medium) — ACCEPTED and folded into Pre-Requisite 4.** A real catch: `APP_SHELL` pre-caches `/` itself, so although no new asset ships, `SHELL_CACHE` should still move to `-v4` or an offline open would serve the pre-date-row entry screen. Online mornings are unaffected (network-first).
- Time-to-restore note (a repair cannot be undone in-app) is inherited from the one-entry-per-day upsert, not introduced here; entry deletion is explicitly out of scope.

Deliverable-type routing: `application` ⇒ no plugin/skill reviewers (N/A). **Gate: PASSED — handoff to DELIVER unblocked.**

## Wave: DELIVER

Executed 2026-07-24 22:37Z → 2026-07-25 by the nw-deliver orchestrator + `nw-functional-software-crafter` (ADR-005 paradigm, CLAUDE.md routing), with `nw-acceptance-designer` closing the mutation survivors test-side. 7 roadmap steps across 3 phases, all 3-phase RED→GREEN→COMMIT (ADR-025); DES integrity `exit 0`, "All 7 steps have complete DES traces". Density: lean, Tier-1 `[REF]` only.

### [WHY] Upstream Issues

Four. None is a defect in this feature's shipped code; all four are recorded so the upstream reasoning is corrected before the next feature repeats it.

1. **DESIGN said `static/sw.js` UNCHANGED; DELIVER changed it.** § Component Decomposition states, on the untouched-files row, *"no new asset ⇒ no APP_SHELL change, no cache bump"*. The approved roadmap overrode the second half at the final step (DISTILL § Pre-Requisites for DELIVER, item 4, itself accepting Forge's platform-review catch): `APP_SHELL` pre-caches **`/` itself**, and `/` grew a date row, so without a new `SHELL_CACHE` name an OFFLINE open keeps being served the pre-date-row entry screen out of `-v3`. Online mornings are unaffected (network-first). `APP_SHELL`'s *list* is genuinely unchanged; only the cache name moved (`weight-tracker-shell-v3` → `-v4`). The deviation was pre-approved at roadmap review and shipped in `a204cad`. **Correction to carry forward: the trigger for a shell-cache bump is a change to any pre-cached RESPONSE, not only the addition of a new asset.** The DESIGN inventory phrasing, which reasons only over the asset list, will under-call this again.
2. **R-2 / R-3 remain open (raised at DESIGN, owned by DISTILL).** Both were *documented* in `kpi-contracts.yaml` during DISTILL; neither is closed as a query the product serves. **R-2**: the contract's KPI-1 query reads `entries.entry_ms` while `/stats` reads the events trail — correcting a past day upserts `entry_ms = NULL` over that row, erasing that morning's timing from `entries` (harmless for `/stats`, which the trail backs; corrupting for the documented ad-hoc query). Fix = pin the trail as KPI-1's SSOT in the contract file, which the DISTILL edit began and this feature does not extend. **R-3**: KPI-5 / KPI-7 denominators pair on `DISTINCT date(ts) … entry.saved`, so a repair on a non-logging day inflates the "logging days" denominator; the shipped `backdated` flag makes the exclusion one `WHERE` clause. Neither blocks this feature — the read-time SQL is documentation, not a served surface, so neither carries an AT today.
3. **The `des-commit` invocation template in the nw-execute DES prompt omits the `Task-Id` trailer** that this project's commits carry. Two agents hit it this wave; one amended a commit to recover. Either the template should include `Task-Id` inside `--message`, or `des-commit` should grow a `--task-id` flag. Process finding, not a code defect — recorded for the tooling owner.
4. **The DISTILL SSOT edits left two product YAML files unparseable — found at finalize, fixed here.** `kpi-contracts.yaml` (KPI-8 `instrument`) and `outcomes/registry.yaml` (OUT-10 and OUT-11 `output.shape`) each embedded a `key: value` fragment — `` `backdated: true` ``, `{iso_day: kg}`, `"backdated": true` — inside an unquoted plain scalar, which YAML reads as a nested mapping indicator (`mapping values are not allowed here`). Both files parse at `b85b575` and stopped parsing under the uncommitted DISTILL delta. Nothing red-lighted, because **no automated consumer loads either file today** — `pyproject.toml` references `kpi-contracts.yaml` only in a pytest marker description, and the outcomes CLI has been blocked on its own mis-packaged `schema.json` since OUT-7. Fixed at finalize by converting the three scalars to folded (`>`) block scalars — **zero wording changes**, verified by `yaml.safe_load` (all 11 outcomes and all 7 top-level KPI keys load). Correction to carry forward: **an SSOT file in a machine-readable format needs a parse check in its own wave**, not at the wave that happens to notice; the absence of a consumer is why this survived two waves undetected, not evidence that it was harmless.

### [REF] Implementation Summary

Shipped US-013 + US-014 as one slice: the entry screen now carries a native `<input type="date">` above the weight field, defaulted and bounded to the device-local day, so `js-3-maintain` — the last journey moment without a UI — is served in place. **Prefill (ADR-010, D-21)**: the shipped 4-entry `recent_weights_map` widened to a whole-record `{iso_day: kg}` map rendered inline in the same template slot — a pure projection of the `all_entries()` read `GET /` already performs, so *one* client map answers both the yesterday anchor and the prefill for any stored day, synchronously, with zero added I/O and no async race. **KPI-1 sample purity (ADR-011, D-22/D-23)**: the save message gained one additive, optional, backward-compatible `today` claim; a pure core pair (`bounded_day_frame` / `is_backdated`, the clamp arithmetic extracted so one copy of the calendar rule survives) classifies `backdated = entry_day != skew-clamped claim` **after** validation; a backdated save records `entry_ms` as NULL — contributing 0 entry-speed samples through the shipped null-skip — and stamps `"backdated": true` on the `entry.saved` payload, read by the new `backdated_saves_since` query as `backdated_saves_this_week` on `/stats` (KPI-8). **One hint node (D-24)**: `#yesterday-reference` → `#entry-hint`, never removed, three mutually exclusive states from a pure `hintFor`, day labels through the one `dayLabel(iso)` grammar — "never two hints" is structural, not conventional. **Date row (D-25)**: `value`/`max` client-set, `min` = first entry day − 1 year server-supplied, no `autofocus`, hint-line height reserved, post-save reset to device today. Zero port-protocol changes, zero new adapters, routes, assets, dependencies, external origins, probes, or migrations (`entry_ms` was already nullable; `CODE_SCHEMA_VERSION` stays 1).

### [REF] Files Modified

**Production — 7 files, `b85b575..0bd47f0` over `src/` (+402/−80):**

- `src/weight_tracker/core/validation.py` — `bounded_day_frame(claimed, server_utc_today) -> date | None` + `is_backdated(entry_day, device_today) -> bool`; total, clock-free, I/O-free. L3 dedup at refactor: `_latest_plausible_day` / `_earliest_plausible_day`.
- `src/weight_tracker/web/routes.py` — `record_weights_map` (whole record, replacing `recent_weights_map`); `date_row_earliest_day` (the `min` bound); write-time classification after `validate_entry_date`; `entry_ms` withheld when backdated; `"backdated"` payload stamp; `backdated_saves_this_week` on `/stats`. `RECENT_ANCHOR_ENTRIES` retired with its sole consumer.
- `src/weight_tracker/shell/telemetry_store.py` — **NEW** `backdated_saves_since` (payload predicate, `entry_ms_samples_since` pattern). L3 dedup at refactor: `_payloads_since`.
- `src/weight_tracker/composition.py` — one `partial(...)` wiring beside `entry_ms_samples_since`; route-contract docstring names the `today` field and the purity rule.
- `src/weight_tracker/web/templates/index.html` — date row above `#weight` (no `autofocus`); one `#entry-hint` node driven by pure `hintFor`; `dayLabel(iso)` extracted from `entryRowText`; submit payload `{date, today, weight, entry_ms}`; post-save reset + hint re-derivation; save response merged into the client map. No new script file.
- `src/weight_tracker/web/static/theme.css` — `#entry-date` / `#entry-hint` block rules (reserved `min-height: 1.5em`, ≥44 px target, AA both schemes); `#yesterday-reference` selector renamed. Tokens only.
- `src/weight_tracker/web/static/sw.js` — `SHELL_CACHE` → `weight-tracker-shell-v4`. `APP_SHELL` list unchanged; see [WHY] Upstream Issue 1.

**Tests — 11 files (DISTILL-authored, landing across the step commits):** `acceptance/milestone-10-dated-entry.feature` (16 scenarios / 17 executions); property suites `properties/test_day_frame_properties.py`, `test_prefill_map_properties.py`, `test_date_row_bound_properties.py`, `test_entry_hint_wiring.py`, `test_date_row_dress.py`; `integration/test_repair_count_query.py`; `steps/steps_dated_entry.py` (21 decorators); `steps/test_milestone_10.py` (binding); `steps/composition.py` (`DatedEntryService`, map extraction, the walked-clock `seed_timed_week` renegotiation); `steps/domain_types.py` (`DayClaim`, `CLAIM_PHRASES`, `day_label`). `pyproject.toml` gained the `us_013` / `us_014` markers.

**Docs:** this file; `deliver/{roadmap,execution-log}.json`; `deliver/mutation/mutation-report.md`; `distill/red-classification.md`; `slices/slice-01-dated-entry.md`. SSOT — `docs/product/architecture/brief.md` (dated-entry delta paragraph, ADR index, Component Inventory), `adr-010-prefill-delivery.md` + `adr-011-backdated-save-classification.md` (new, permanent), `kpi-contracts.yaml` (KPI-8, `entry.saved` payload contract, KPI-1 SSOT correction, KPI-5/KPI-7 denominators, `at_scenario_links`, baselines), `outcomes/registry.yaml` (OUT-10, OUT-11, OUT-1 input-shape amendment), `jobs.yaml` (js-3-maintain delivery note + feature list), `journeys/daily-weight-tracking.yaml` (steps 1 and 4 delta), `personas/clemens.yaml` (feature list).

### [REF] Scenarios Green

**16 of 16 milestone-10 scenarios green (17 executions, one 2-example outline), zero `@pending` remaining** — the 13 authored at DISTILL plus the 3 added at `0bd47f0` to close the mutation survivors. Full suite: **219 passed, 0 skipped, 0 failed** at HEAD `0bd47f0`, verified 2026-07-25 (`uv run pytest -q`, 31.1 s). Inherited suites green throughout, including all four consciously renegotiated touchpoints (map-const rename with fallback, OUT-1 input shape, the entry-readiness guarantee extended by a new scenario rather than an amended shared assertion, and the walked-clock `seed_timed_week`).

### [REF] DoD Check

| # | DoD item (DISCUSS) | Status |
|---|---|---|
| 1 | All UAT scenarios green (automated) | **PASS** — 16/16 milestone-10 (17 executions), zero `@pending` |
| 2 | Supporting tests green incl. the consciously renegotiated entry-screen ATs | **PASS** — full suite 219 passed; all four renegotiations green, none silent |
| 3 | Code refactored; per-feature mutation gate ≥80% on modified files | **PASS** — L1-L6 pass (`3e3c616`) + mutation 96.5% effective as run, 100% after the survivors were closed (`0bd47f0`) |
| 4 | Code reviewed (self-review with reviewer agent) | **PASS** — `nw-software-crafter-reviewer` **APPROVED, zero findings** |
| 5 | Merged to main | **PASS (locally)** — 9 commits on `main`, trunk-based; push is a separate user decision because it triggers the deploy pipeline |
| 6 | Deployed to the phone-reachable production URL via the existing pipeline | **OPEN — owned by the user.** Runs on the push. The local live-server demo below is a server-side proxy, not the deploy |
| 7 | Dogfooded same day: one real backfill or correction on the phone + a normal morning log | **OPEN — owned by the user.** Follows the deploy; this is the falsification test for D6 (a date row above the form must not tax the five-second morning) |
| 8 | KPI-8 marker visible on /stats; KPI-1 sample purity verified; ≤2 s and tap-count guardrails verified | **PASS (instrumentation)** — demo `/stats` read `backdated_saves_this_week: 3` beside `speed.sample_count: 1` over 4 saves; purity is structural (`entry_ms` NULL on repairs), and G-2 readiness is a hard CI gate. Production *values* accrue after item 6 |
| 9 | Story demonstrable end-to-end on the phone | **OPEN — owned by the user.** The evidence below is a real-uvicorn, real-SQLite, real-HTTP demonstration; the on-phone demonstration follows the deploy |

Items 1–5 and 8 satisfied. **Items 6, 7 and 9 OPEN**, owned by the user, and deliberately not marked done: no local run substitutes for the deploy, the dogfood, or the phone.

### [REF] Demo Evidence

Phase 3.5 hard gate, 2026-07-25. Captured from a **real `uvicorn` process on 127.0.0.1:8811 over a temp SQLite DB, driven by `curl`** — not the TestClient harness. Device day framed as Sat 25 Jul 2026.

- `POST /login` → `{"status":"unlocked"}` (HTTP 200).
- **Normal morning** — `date=2026-07-25 today=2026-07-25 entry_ms=4200` → `{"outcome":"saved","confirmation":"Saved: 82.2 kg — Sat 25 Jul", …}`.
- **Backfill of a forgotten day** — `date=2026-07-19 today=2026-07-25 entry_ms=22000` → `"Saved: 82.6 kg — Sun 19 Jul"`; the glance recomputed to `Trend: 82.4 kg` and `recent` came back carrying both days.
- **Correction in place** — `date=2026-07-22` saved 88.4, then re-saved 82.4 → `"Saved: 82.4 kg — Wed 22 Jul"`; exactly one row for that day.
- **Forged future save** — `date=2026-07-31` → `{"outcome":"rejected","reason":"future_date","message":"Future dates cannot be logged.","echo":"82.0"}`.
- **`GET /stats`** → `{"entry_logged_count":4, …, "backdated_saves_this_week":3, "speed":{"median_ms":4200,"p90_ms":4200.0,"sample_count":1}}` — **KPI-8 visible (3 repairs) and KPI-1 purity structural: 4 saves, 1 speed sample, only the timed morning.**
- **`GET /`** → `<input type="date" id="entry-date" min="2025-07-19">` (first entry 2026-07-19 minus one year); exactly **1** `id="entry-hint"` node; `const recordWeights = {"2026-07-19": 82.6, "2026-07-22": 82.4, "2026-07-25": 82.2}`; **0** occurrences of the retired `yesterday-reference`.
- **Served assets** — `theme.css` carries `#entry-hint { … min-height: 1.5em }`; `/sw.js` carries `const SHELL_CACHE = "weight-tracker-shell-v4"`.

### [REF] Quality Gates

| Gate | Outcome |
|---|---|
| Roadmap review | **Approved** — `nw-acceptance-designer-reviewer` + orchestrator re-verification; 1 BLOCKER on 2 orphan scenarios, resolved in revision; 16 scenarios mapped across 7 steps |
| Per-step TDD (3-phase canon, ADR-025) | **7/7 COMMIT PASS** — `3254d52`, `2170149`, `ef5dccb`, `5829dec`, `99d3ad4`, `8bd8a1e`, `a204cad`; DES 21/21 events |
| Post-merge integration (3.5) | **PASS** — full suite green + the real-uvicorn/real-SQLite/real-curl demo above |
| Refactor L1–L6 (`3e3c616`) | **PASS** — L3 dedup in `validation.py` (`_latest_plausible_day` / `_earliest_plausible_day`) and `telemetry_store.py` (`_payloads_since`); L1 comment/docstring accuracy in `composition.py` + `routes.py`; L1/L2 single `deviceLocalDay()` read in `index.html`; `RECENT_ANCHOR_ENTRIES` + `recent_weights_map` retired; test-side `Fri 24 Jul` grammar routed through the one `day_label` SSOT. `theme.css` / `sw.js` / `pyproject.toml` — no change warranted. 216 green throughout; ruff + `mypy --strict` clean |
| Adversarial review (`nw-software-crafter-reviewer`) | **APPROVED — zero findings.** Attacked: KPI-1 structural purity, hostile device-day input (absent / empty / garbled / wrong-type / far-future / far-past), the single-`all_entries()`-read claim, hint-line singularity, the Testing-Theater 7-pattern scan over 16 test files, and refactor behaviour preservation |
| Mutation (per-feature, cosmic-ray 8.4.3) | **PASS — 83/86 = 96.5% as run; 86/86 = 100% after the survivors were closed.** 108 executed (git-filter over the feature delta), 22 argued equivalents (the catalogued lazy-annotation `BitOr` class). The 3 genuine survivors sat on ONE axis — the suite never put the device clock and the server clock on different days during a save — closed test-side by `nw-acceptance-designer` in `0bd47f0` with **zero production change and zero new step definitions**. `deliver/mutation/mutation-report.md` |
| Integrity verification | **PASS** — `des-verify-integrity docs/feature/entry-date-picker/deliver/` exit 0, "All 7 steps have complete DES traces" |

### [REF] Pre-Requisites

All six DISTILL pre-requisites discharged: **(1)** paired pure-core PBTs for `bounded_day_frame` / `is_backdated` over the full skew range (`properties/test_day_frame_properties.py`); **(2)** unit-level pins for what a browser-less suite cannot reach — the submitted payload, the post-save reset, the picker's `value`/`max`, the hint wording (`test_entry_hint_wiring.py`, `test_date_row_bound_properties.py`), with dogfood verification still owed (DoD 7); **(3)** `theme.css` rules for `#entry-date` / `#entry-hint`, reserved line height, ≥44 px, AA both schemes (`test_date_row_dress.py`, G-4/G-2 CI gates green); **(4)** `SHELL_CACHE` bumped to `-v4` with `APP_SHELL` unchanged — see [WHY] Upstream Issue 1; **(5)** `RECENT_ANCHOR_ENTRIES` retired with its sole consumer, `entry_ms` still nullable, `CODE_SCHEMA_VERSION` still 1; **(6)** mutation gate ≥80% scoped to the modified files — cleared at 96.5%, then 100%.

Consumed from upstream: DISTILL's 13 scenarios + test-side scaffolds as the authoritative executable spec; DESIGN pins D-21…D-26 honored verbatim; ADR-010 + ADR-011 (ADR-001…009 unchanged, none superseded). Still owed upstream and **not** closed here: R-2 / R-3 (see [WHY] Upstream Issues 2) and the `nwave-ai outcomes check-delta` re-check, still blocked by the mis-packaged `schema.json` (OUT-7/8/9 precedent; OUT-10/OUT-11 registered manually at DISTILL).
