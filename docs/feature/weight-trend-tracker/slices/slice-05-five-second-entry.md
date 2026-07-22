# Slice 05: five-second-entry

**Goal**: Cut morning logging from ≤10 s to a measured median ≤5 s: home-screen launch, instant interactivity, auto-focused decimal keypad, yesterday's value as reference — plus the timing instrumentation that proves it.

**Stories**: US-006 (user-visible value; carries KPI-1 instrumentation as embedded AC, not a separate `@infrastructure` story). Slice composition gate satisfied.

## IN

- Launchable from phone home screen (install affordance)
- Interactive ≤2 s on phone over mobile connection
- Weight field auto-focused with numeric/decimal keypad
- "yesterday: 82.6 kg" reference next to the input
- Client-side open→save timing captured with each entry (KPI-1); trend-view open counter (KPI-3)

## OUT

- Offline entry queueing (revisit if timing data shows connectivity misses)
- Reminders/notifications, streak displays (out of product scope)
- Any further onboarding — single user already onboarded

## Learning Hypothesis

Disproves "friction, not motivation, is what breaks logging habits" if, after shipping, a week of real timing data shows median >5 s or logging adherence does not hold at ≥6/7 days — either result redirects effort (deeper perf work vs. accepting the habit is motivation-bound).

## Acceptance Criteria

- US-006 scenarios 1–3 green (launch-to-typing, yesterday reference, 7-day ≤5 s median @property)
- KPI-1 and KPI-3 instrumentation emitting and queryable
- Dogfood: next real morning log timed via the new instrumentation the day this ships

## Dependencies

Slice 01 (entry flow). Independent of Slices 02–04 (could ship earlier if habit friction appears sooner).

## Effort / Reference Class

~0.5–1 day. Reference class: web app installability + input ergonomics + lightweight client telemetry — low-moderate; main unknown is load-time budget on mobile network.

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (launch → focused input → save → timing persisted) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS |
| 4. Production data + same-day dogfood moment | PASS (timed real morning log) |
| 5. Named, falsifiable learning hypothesis | PASS |
