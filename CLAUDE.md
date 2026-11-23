# weight-tracker

## Development Paradigm

This project follows the **functional programming paradigm** (Functional Core / Imperative Shell — see `docs/product/architecture/adr-005-functional-core-paradigm.md`). Use **@nw-functional-software-crafter** for DELIVER-wave implementation work. User approved FP (DESIGN wave, 2026-07-22).

- Domain core: pure functions over frozen dataclasses; no I/O, no clock access, no globals.
- Effects only in the thin shell (FastAPI routes, SQLite adapter, composition root).
- Read-only ports (`WeightHistory`, `TrendProjection`) must never expose write methods.
- Architecture SSOT: `docs/product/architecture/brief.md` + ADR-001…005.

## Mutation Testing Strategy

This project uses **per-feature** mutation testing. Runs after refactoring during each delivery, scoped to modified files. Kill rate gate: >= 80%.

Run it with `scripts/mutate.sh <base-ref> [pytest targets...]` from a clean, committed `src/`; the script's header explains the scope, the targets, and how to read survivors.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `cadolphs/weight-tracker` (use the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` at the root; ADRs in `docs/product/architecture/adr-NNN-*.md`. See `docs/agents/domain.md`.
