# ADR-010: Edit Prefill Delivery — Whole-Record Day→Weight Map Rendered Inline

## Status

Accepted (2026-07-24, user-selected; feature `entry-date-picker`, US-014)

## Context

D7/A24 require that selecting **any** stored day prefills the weight field with the stored value — a March entry read in July must be correct, not just the recent days the yesterday anchor already covers. Binding constraints: entry screen interactive ≤2 s with the date row present (KPI-1 guardrail); the default morning flow pays nothing for the picker; lookup failure degrades to the no-entry presentation without blocking entry or save; read-only ports gain no write methods (ADR-005). Today the entry screen embeds `recent_weights_map` — the **latest four** entries as `{iso_day: kg}` — inside its one inline script, and the phone resolves its own device-local yesterday against it (`fix-device-day-reads`, A5 extended to reads). `GET /` already performs a single `store.all_entries()` read for the recent list and the glance, so the whole record is in hand at render time at zero additional I/O.

One constraint is decisive and easy to miss: **the acceptance suite has no browser.** The shipped yesterday-anchor tests extract the embedded map from the rendered HTML by regex and emulate the client lookup in Python. Any prefill mechanism that resolves client-side after a network round trip is, in this suite, unobservable — the headline AC ("an entry from Tue 3 Mar 2026 prefills 84.9") could only be asserted indirectly.

## Decision

`recent_weights_map` widens into `record_weights_map(entries)` — **every** stored entry as `{iso_day: kg}`, same shape, same template slot, same single `all_entries()` read. **One** client map answers both the yesterday anchor and the edit prefill; lookup is a dictionary read on data already delivered with the page. Degrade-to-absent is structural: key missing ⇒ `No entry for {day} yet` and an empty field; map absent entirely ⇒ the script guards and the save path is untouched. The map is refreshed in place after a save by merging the response's own `date`/`weight_kg` and `recent` fields — both already on the wire.

Byte cost, at the KPI-2 target of ~6 logged days/week (~313 entries/year) and ~18 B per `"2026-07-24":82.4,` pair:

| Horizon | Entries | Added HTML (raw) | ~compressed | Share of the 2,000 ms budget |
|---|---|---|---|---|
| 1 year | ~313 | 5.6 KB | ~1.5 KB | ~4 ms transfer, ~1 ms parse |
| 3 years | ~940 | 17 KB | ~4 KB | ~12 ms |
| 5 years | ~1,570 | 28 KB | ~7 KB | ~20 ms |
| 10 years | ~3,130 | 56 KB | ~14 KB | ~40 ms + ~5 ms parse |

For scale: `theme.css` is 3,394 B and the vendored uPlot ~45 KB. Even the ten-year case is ≤3 % of the entry-primacy budget.

**Reversal trigger (pinned):** when the record exceeds ~2,000 entries (~36 KB raw) **or** the entry-screen ≤2 s acceptance margin degrades, collapse to the hybrid — keep the server-seeded recent map, fetch `GET /entries?scale=ALL` lazily on first date-row focus, merge into the same one map. That is ~15 lines and no port, route, or contract change; the decision is deliberately cheap to reverse.

## Alternatives Considered

- **Lazy client fetch of the existing `GET /entries?scale=ALL`** (no new route; the same read `graph.js` already performs): Rejected. Entry-screen bytes would stay constant forever and ADR-008's reasoning transfers cleanly (prefill is not on the input-readiness path — it belongs to the ≤30 s KPI-8 repair flow). But it introduces an async race and a "not yet loaded" hint state: picking an old day can render `No entry for Tue 3 Mar yet` and then flip to `Editing Tue 3 Mar — was 84.9 kg` — a wrong-then-right flicker on the one feature whose entire purpose is trust in the record. It also needs prefetch-on-focus to hide latency, a real degradation path to specify and maintain, and — decisively — it moves the headline AC out of reach of the browser-less acceptance suite.
- **Hybrid: one map, server-seeded then lazily extended**: Rejected for now. Buys instant prefill for the common recent repair with bounded HTML, but carries the same flicker window for old days, two freshness semantics, and two AT surfaces — complexity unearned at a ~135-entry record. Retained verbatim as the reversal target above.
- **New per-day read endpoint (`GET /entries/{day}`)**: Rejected. A new route and a new read surface for what `?scale=ALL` already returns, plus one round trip per date change instead of one per session.
- **Bounded window (e.g. the last 400 days) rendered inline**: Rejected outright — it fails A24 by construction. A March-2026 entry must still prefill in 2028.

## Consequences

- Positive: zero added I/O and zero added HTTP; no async, no race, no new failure mode — degrade-to-absent falls out of a dictionary miss; the "any stored day" AC is assertable with the **shipped** AT harness (extract the map, assert the key) with no new test infrastructure; one map means the anchor and the prefill can never disagree; read-only ports gain no methods at all, since the map is a pure projection of a read the driving adapter already performs (the last-7-slice precedent).
- Negative / disclosed: the morning HTML grows linearly with the record, forever, and — unlike the service-worker-cached uPlot bundle — is re-downloaded on every entry-screen open. Quantified above as immaterial against the guardrail for at least a decade, with the ~2,000-entry reversal trigger recorded so the growth is watched rather than assumed. The map is a render-time snapshot: freshness after a save depends on merging the save response (already delivered), not on a reload.
