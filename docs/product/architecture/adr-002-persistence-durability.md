# ADR-002: Persistence and Durability — SQLite (WAL, synchronous=FULL) + Litestream → Cloudflare R2

## Status

Accepted (2026-07-22)

## Context

Guardrail KPI: zero lost entries, ever; a confirmed save must survive restarts, redeploys, and host loss (US-001 anxiety-path scenario). Data volume is tiny (≤1 row/day + KPI events). Fly volumes are single-host block devices — a volume alone does not survive host failure. Container filesystems are known to lie about fsync (overlayfs/tmpfs).

## Decision

SQLite file on the Fly volume, WAL mode, `synchronous=FULL`; save confirmed to the user only after commit returns. Litestream runs as supervisor process (`litestream replicate -exec ...`) continuously streaming WAL segments to a Cloudflare R2 bucket (free tier). Schema: `entries(date TEXT PRIMARY KEY, weight_kg REAL, logged_at TEXT, entry_ms INTEGER)` + append-only `events` for KPI instrumentation. EntryStore adapter `probe()` at startup: open, `PRAGMA integrity_check`, assert WAL + `synchronous=FULL`, sentinel write→fsync→readback, statfs ≠ tmpfs; failure ⇒ `health.startup.refused`, no traffic.

## Alternatives Considered

- **Managed Postgres (Fly Postgres / Neon / Supabase)**: Rejected. A network database server for ≤400 rows/year is disproportionate; adds cost, connection handling, and a second process to operate; free tiers add vendor coupling without improving the durability story beyond what replication gives SQLite.
- **Fly volume snapshots only (no Litestream)**: Rejected. Daily snapshots leave up to 24 h of loss window and do not survive volume corruption between snapshots; violates the zero-loss guardrail.
- **Cloudflare D1**: Rejected with Option B in ADR-001 (parity + probe-ability).

## Consequences

- Positive: point-in-time recovery with seconds-level loss window; off-host replica discharges the durability guardrail; local dev = same SQLite file semantics; restore is one command (`litestream restore`).
- Negative: replication liveness must be monitored (handed to platform-architect: health check + scheduled restore drill = the contract test for this boundary); single-writer model (fine: one user); R2 credentials become a secret to manage.
