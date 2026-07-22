# ATDD Infrastructure Policy

Per `nw-distill` § Project Infrastructure Policy. One file per project. Apply-if-exists;
write-if-absent; rewrite with `--policy=fresh`. Git history is the audit trail.
Bootstrapped 2026-07-22 (first DISTILL in project, feature `weight-trend-tracker`).

## Driving

| Port | Mechanism | Note |
|---|---|---|
| HTTP endpoints (WeightLogging POST, WeightHistory GET, TrendProjection GET, graph/entry pages) | `fastapi.testclient.TestClient` over the production composition root (`weight_tracker.composition.build_app`) | real HTTP protocol layer; walking skeleton uses the same mechanism |
| AccessGate (login) | same TestClient, real POST /login with real argon2 verification | test passphrase hashed with real argon2 in conftest |

## Driven internal (real)

| Port | Mechanism | Note |
|---|---|---|
| EntryStore (SQLite `entries` table) | real SQLite file on `tmp_path`, production pragmas (WAL, `synchronous=FULL`) | ALL acceptance scenarios use the real store; restart-durability scenario reopens the same file with a fresh composition |
| TelemetryStore (SQLite `events` table, append-only) | same real SQLite file | KPI scenarios (@kpi) read back via /stats |

## Driven external / non-deterministic (fake)

| Port | Fake | Note |
|---|---|---|
| Clock | `FakeClock` (tests/weight-trend-tracker/acceptance/steps/fake_clock.py) | manual advance; needed for midnight, timezone-skew, and 90-day-session scenarios |
| Litestream -> Cloudflare R2 replication | NOT modeled in acceptance tests | deployment-level integration; contract test = weekly restore drill in CI (DEVOPS). Acceptance tests cannot model host loss / replication lag. |
