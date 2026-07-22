# weight-tracker

## Development Paradigm

This project follows the **functional programming paradigm** (Functional Core / Imperative Shell — see `docs/product/architecture/adr-005-functional-core-paradigm.md`). Use **@nw-functional-software-crafter** for DELIVER-wave implementation work. User approved FP (DESIGN wave, 2026-07-22).

- Domain core: pure functions over frozen dataclasses; no I/O, no clock access, no globals.
- Effects only in the thin shell (FastAPI routes, SQLite adapter, composition root).
- Read-only ports (`WeightHistory`, `TrendProjection`) must never expose write methods.
- Architecture SSOT: `docs/product/architecture/brief.md` + ADR-001…005.

## Mutation Testing Strategy

This project uses **per-feature** mutation testing. Runs after refactoring during each delivery, scoped to modified files. Kill rate gate: >= 80%.
