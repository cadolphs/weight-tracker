# Slice 01: log-todays-weight (Walking Skeleton)

**Goal**: From a phone, enter today's weight in kg, have it durably stored, and see it confirmed in a history list — the full vertical loop, deployed to production day 1.

**Stories**: US-001 (user-visible value). No `@infrastructure` stories; scaffolding (repo, deploy pipeline, persistence) is carried *inside* this value slice — slice composition gate satisfied.

## IN

- Entry screen: today preselected, focused weight field, Save button
- Validation: 30.0–250.0 kg, 0.1 precision, empty-submit guard
- One-entry-per-day invariant (re-save replaces today's value)
- Durable persistence; confirmation line; simple reverse-chronological entries list
- Deploy to phone-reachable production URL

## OUT

- Graphs of any kind (Slice 02), trend (Slice 04)
- Past-day entry/edit (Slice 03)
- Home-screen install, keypad/prefill polish (Slice 05)
- Auth mechanism beyond DESIGN-chosen minimum (OQ-1)

## Learning Hypothesis

Disproves "a self-built web form can replace the paid app's logging" if, after deployment, a real morning log takes >10 s or any confirmed entry is lost within the first week.

## Acceptance Criteria

- US-001 scenarios 1–5 green (capture, range typo, replace-not-duplicate, restart durability, empty submit)
- Open → saved ≤10 s (p90) on Clemens's phone
- Dogfood: at least one real weigh-in logged in production the day this ships

## Dependencies

None (greenfield). Requires DESIGN decisions: hosting, persistence, access protection.

## Effort / Reference Class

~1 day. Reference class: single-form CRUD web feature with persistence — well-understood, low uncertainty (extra half-risk: first-time deploy pipeline).

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (UI → domain rule → store → read-back) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS |
| 4. Production data + same-day dogfood moment | PASS (morning weigh-in) |
| 5. Named, falsifiable learning hypothesis | PASS |
