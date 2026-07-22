# ADR-005: Development Paradigm — Functional Core / Imperative Shell (Functional-First Python)

## Status

Accepted (2026-07-22, user-approved)

## Context

Python is multi-paradigm; the crafter needs one committed style. The domain's essence is pure computation: validation rules, one-per-day upsert resolution, windowing, and a Kalman+RTS trend that is literally a fold plus a backward pass. US-004 demands determinism; the effect-isolation mandate requires that "read paths silently write" be non-representable.

## Decision

Functional Core / Imperative Shell. Core = pure functions over frozen dataclasses (`validate`, `upsert_resolution`, `trend_series`, window filters) — no I/O, no clock, no globals. Shell = FastAPI routes, `AccessGate`, SQLite `EntryStore`, `Clock` — the only impure layer, kept thin. Read-only driving ports (`WeightHistory`, `TrendProjection`) expose no write methods. Capability injection at boundaries (adapters passed in at the composition root; core never imports `sqlite3`, `datetime.now`, or `os`). DELIVER crafter: **nw-functional-software-crafter**. Enforcement: import-linter layer contract (core imports nothing outward), mypy strict, AST pre-commit hook for adapter `probe()` presence.

## Alternatives Considered

- **Class-based OOP (service classes + repository pattern)**: Rejected. Adds ceremony and mutable service state for a domain with ~4 pure operations; invites logic drift into stateful services; determinism becomes a testing goal rather than a structural property.
- **Unstructured "script-style" Python (logic in route handlers)**: Rejected. Fastest day 1, but couples trend math to HTTP/DB, making the US-004 property tests (Hypothesis over entry sets) and the AC-threshold verification needlessly awkward; erodes within the first refactor.

## Consequences

- Positive: trend determinism AC is structurally true; core is 100% property-testable without I/O; smallest possible impure surface to probe; matches crafter agent's strengths.
- Negative: light indirection at the boundary (ports/Protocols) for a small app — accepted as the cost of testability and effect isolation.
