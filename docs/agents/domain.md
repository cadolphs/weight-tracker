# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root.
- **`docs/product/architecture/`**: the architecture SSOT. `brief.md` is the system overview; ADRs are `adr-NNN-<slug>.md` (e.g. `adr-005-functional-core-paradigm.md`). Read the ADRs that touch the area you're about to work in. New ADRs continue the numbering in the same directory with the same naming.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

Single-context repo:

```
/
├── GLOSSARY.md
├── docs/product/architecture/
│   ├── brief.md                            ← architecture SSOT
│   ├── adr-001-stack-and-hosting.md
│   ├── adr-002-persistence-durability.md
│   └── adr-NNN-<slug>.md
└── src/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `GLOSSARY.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-005 (functional core / imperative shell), but worth reopening because…_
