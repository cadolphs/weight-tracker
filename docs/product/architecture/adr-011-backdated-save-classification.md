# ADR-011: Backdated Saves Classified at Write Time from the Phone's Claimed Day

## Status

Accepted (2026-07-24, user-selected; feature `entry-date-picker`, US-013/US-014). Does not supersede any prior ADR; extends the KPI trail established by ADR-009.

## Context

KPI-1 measures the *morning capture habit* (median ≤5 s, p90 ≤10 s over a rolling week). A backdated save is inherently slower — open the picker, recall the day, read the prefill — so A23 pins a hard requirement: **backdated saves contribute 0 entry-speed samples**, while KPI-8 (the in-app repair counter) must stay countable on `/stats`. A single backfill session would otherwise poison the weekly median the 5-second target guards.

Two shipped facts frame the mechanism. First, `entry_ms_samples_since` **already skips null `entry_ms`** — "saves submitted without a timing are not samples" is existing, mutation-tested semantics. Second, the phone already claims its own calendar day to the server on reads: `?today=` is parsed and skew-clamped by `day_frame_or_bad_request` against `MAX_DEVICE_SKEW_DAYS`, because the device-local day is canonical (A5) and the server's UTC day is not the user's calendar.

The tempting alternative is to classify at read time, comparing the payload's date against the event's UTC timestamp day — the trail already carries both. It does not survive contact with timezone skew. An 18:00 log at UTC−7 stamps `ts` on day *D+1* while the payload date is *D*: the payload sits exactly one day behind the timestamp. A genuine backfill of yesterday produces byte-identical rows. With no tolerance, ordinary evening logs are stripped of their samples; with a ±1-day tolerance, every yesterday-backfill — the single most common repair — is counted as a morning log, which is precisely the pollution the rule exists to prevent. The two cases are structurally indistinguishable after the fact.

## Decision

**Classify at write time, from the day the phone claims.** `POST /entries` accepts one **additive, optional, backward-compatible** field, `today` — the same device-day claim `?today=` already carries on reads. After validation succeeds, a pure core function decides:

- `bounded_day_frame(claimed, server_utc_today) -> date | None` — parse and clamp to `server_utc_today ± MAX_DEVICE_SKEW_DAYS`; `None` when unparseable.
- `is_backdated(entry_day, device_today) -> bool` — the entry day is not the device's own day.

An absent or garbled claim falls back to the server's UTC day and never produces a 400: a telemetry concern must never block or reject a save. Classification runs **after** `validate_entry_date`, so only accepted dates are ever classified. When the save is backdated, `entry_ms` is recorded as **null** — in the `entries` row and on the trail — so KPI-1 purity rides the shipped null-skip with zero read-side change, and the `entry.saved` payload additionally carries `"backdated": true`. `/stats` counts repairs through a new read-model query `backdated_saves_since(db_path, since)`, following the payload-parsing shape of `entry_ms_samples_since` and wired by `partial` at the composition root.

`WeightLogging`'s bounded-change universe is unchanged: **one `{date}` row + one `entry.saved` event**. The payload field is route-level enrichment on the shipped `confirmation`/`glance`/`recent` precedent, not a port widening; `ports.py` is untouched.

The rule is falsifiable at the HTTP boundary, which is the point: `POST {date: 19th, today: 20th, entry_ms: 22000}` must leave `/stats.speed.sample_count` unchanged **and** move the KPI-8 counter by one.

## Alternatives Considered

- **Write-time by client omission** (the client simply does not send `entry_ms` when the picked date differs from its device day): Rejected. It is the cheapest option and would yield 0 samples through the same null-skip, but purity becomes a **client convention that no acceptance test can falsify** — the suite composes its own payloads, so the `@property` scenario would assert nothing but the test's own behavior. A single client-side regression would silently poison KPI-1 indefinitely, and the KPI-8 marker still needs a separate mechanism.
- **Read-time classification (payload date vs event UTC timestamp day)**: Rejected on the skew collision above — evening logs and genuine yesterday-backfills are indistinguishable in either direction of the tolerance choice. It also gets the shipped "a phone already in tomorrow may log its new day" case wrong, cannot restore purity for the `speed` report without re-running the same ambiguous comparison inside `entry_ms_samples_since`, and needs a payload-aware query regardless (`count_events_since` is name-parameterised only). The house precedent is against it twice over: ADR-006 and ADR-009 both rejected KPI integrity resting on fragile convention.
- **A second event name (`entry.backdated.saved`) counted by the existing `count_events_since`**: Rejected. Cheaper on the read side — no new query at all — but it widens the save's effect universe to two events per save, breaking the one-row-one-event contract shape pinned since D-13/D-19, and forks the trail grammar for a distinction the payload already expresses.
- **Recording a `repair_ms` alongside the marker**: Deliberately not done. KPI-8's ≤30 s target is self-reported at dogfood; if it is ever automated it gets its own field, never the morning-speed field, so that "a repair counted as a morning" stays non-representable.

## Consequences

- Positive: KPI-1 purity is structural at the storage layer — a repair carries no timing in either the `entries` row or the trail, so the bug class "a slow backfill dragged the weekly median" cannot be represented; the rule is falsifiable at the HTTP boundary rather than trusted; the classifier is a pure, clock-free core function, property-testable across the full skew range; the device-day claim reuses shipped grammar instead of inventing one, and the skew clamp plus the authoritative no-future rule together contain the one newly trusted input (a lying device clock); KPI-8 becomes countable without a new event, a new route, or a schema change (`entry_ms` is already nullable).
- Negative / disclosed: correcting a past day upserts `entry_ms = NULL` over that row, **erasing the original morning's timing from the `entries` table** — harmless for `/stats`, which reads the append-only trail, but corrupting for the ad-hoc KPI-1 query documented in `kpi-contracts.yaml`, which still reads `entries.entry_ms`. That contract already diverged from the shipped code; DISTILL pins the trail as the KPI-1 SSOT and updates the contract file. Separately, a repair on a non-logging day now writes an `entry.saved` row on that day, inflating the KPI-5/KPI-7 "logging days" denominators until their read-time queries exclude `backdated` — a one-clause fix the marker makes possible. Finally, the save message is no longer strictly identical to OUT-1's registered input shape: the optional `today` claim is recorded in the composition-root route contract and amended into the outcome registry at DISTILL.
