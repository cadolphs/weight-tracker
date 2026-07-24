# ADR-009: Intent Telemetry — Route-Level Ambient/Deliberate Events; Data Reads Become Pure

## Status

Accepted (2026-07-24, user-selected; feature `graph-first-home`, US-010/US-012). Retires the `trend.view.opened` **emission** (historical rows preserved); does not supersede any prior ADR.

## Context

KPI-3 is redefined (A19): deliberate trend study = History-page opens + explicit lens/scale interactions on either surface; ambient renders (front-page open at defaults, post-save refresh) must add **0**. KPI-7 needs an ambient graph-presence event. Today `GET /trend` appends `trend.view.opened` unconditionally — with an ambient front-page graph fetching it every morning, KPI-3 would inflate ~7×. A raw-lens gap also exists today: Raw taps hit `GET /entries`, which emits nothing. Structural-separation precedent: D-13/D-14 (the glance never touches `GET /trend`; events are route-level concerns).

## Decision

**Intent is recorded on intent-expressing surfaces, never inferred on data reads.** Event names follow the trail's dotted grammar:

- **`home.graph.shown`** (ambient, KPI-7): appended by the `GET /` render when entries exist (graph data delivered). Per-delivery, no per-day dedup; the KPI-7 pairing with `entry.saved` per calendar day is computed at read time on /stats (KPI-5 precedent, D-14). Server-side emission is a delivery proxy, same accepted proxy as `trend.glance.shown`.
- **`trend.study.opened`** (deliberate): appended by the `GET /graph` (History page) render — one per open, regardless of `?view=`/`?scale=` deep link.
- **`trend.study.interaction`** (deliberate, payload `{surface, control, value}`): explicit lens/scale taps on either surface fire a fire-and-forget beacon **`POST /telemetry/trend-study`**. The route accepts a **closed vocabulary** (surface ∈ {home, history}, control ∈ {lens, scale}, value from the known token sets); anything else → 400, never 500, never a free-text event on the trail. It appends via the existing `EntryStorePort.append_event` — no port change; guarded by `AccessGate` like every route. Beacon failure never blocks or delays any UI behavior.
- **`GET /trend` stops emitting** (and `GET /entries` stays emission-free): the series/history reads become pure reads. Historical `trend.view.opened` rows remain on the append-only trail; /stats keeps `trend_view_opened_count` as a frozen historical counter and gains the new counts (existing name-parameterised `count_events_since`). KPI-3 reads the `trend.study.*` events; any session-collapse refinement is computed at read time, never at write time.

Purity is structural: deliberate events can only originate at the `/graph` render and the beacon route — neither is on the ambient path (page open, ambient fetch, post-save refetch). A log-only morning adds 0 to KPI-3 **by construction**, not by convention.

## Alternatives Considered

- **Separate ambient data endpoint, keep `trend.view.opened` on `/trend` as the deliberate signal**: Rejected — Raw-lens taps (`GET /entries`) stay uncounted (undercount), a History open would double-count (page event + initial fetch event), and a second series endpoint duplicates the payload shape for no behavioral gain.
- **History-opens-only (no interaction events, no beacon)**: Rejected per the user's OQ-8 confirmation (front-page taps count as deliberate, A19). Noted as the graceful fallback: if A19 is ever narrowed, the beacon route and ~5 lines of JS are deleted and everything else stands.
- **Query-parameter event suppression (`/trend?ambient=1`)**: Rejected outright — KPI integrity by fragile convention; already rejected once at ADR-006.

## Consequences

- Positive: KPI-3 purity and the interaction counting are both structural; today's raw-lens undercount is fixed; the data reads' contract shape *improves* (read routes no longer write); the beacon is the only new endpoint (bounded-change: exactly one event append from a closed vocabulary).
- Negative / disclosed: KPI-3's instrument changes mid-history — exactly the redefinition DISCUSS mandates; /stats documents the switch (`trend_view_opened_count` frozen, new counters live). `home.graph.shown` measures data-available-at-render, not client paint — accepted proxy (glance precedent), DISTILL words the oracle accordingly.
