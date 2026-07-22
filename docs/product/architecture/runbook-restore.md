# Runbook: Database Corruption / Data-Loss Recovery

Scope: weight-tracker production (single Fly.io machine, SQLite on `/data`, Litestream → R2).
Operator: Clemens (solo). Referenced by: `docs/product/kpi-contracts.yaml` G-1, feature-delta § DEVOPS.

## 1. Detection signals

Any one of these triggers this runbook:

- **Restore drill failure** — weekly/monthly CI drill workflow red (restore failed, `PRAGMA integrity_check` not ok, or entries count decreased vs. previous drill state).
- **UptimeRobot email** — `/healthz` non-200, or replication lag > 15 min.
- **`health.startup.refused`** in Fly logs — a startup probe failed (integrity_check error, fsync sentinel failure, schema-version mismatch, missing secrets).

## 2. Investigate (5–10 min)

```sh
fly status                     # machine up? restart loop?
fly logs                       # look for health.startup.refused + probe name, Litestream errors
curl -s https://<app>/healthz  # status + replication lag
```

Classify:

| Finding | Class | Go to |
|---|---|---|
| Replication lag high, app serving fine, DB healthy | Replication stall (R2 creds, network, Litestream crash) | § 3a |
| `integrity_check` failure / corrupted DB / bad writes deployed | Data corruption | § 3b |
| Probe refused after a rollback (`entry_store.schema_version`) | Rollback-schema mismatch | § 3c |

## 3. Recover

### 3a. Replication stall (no data loss yet)

1. `fly machine restart` (Litestream is PID 1 — restart re-establishes replication).
2. If still stalled: check R2 credentials validity (`fly secrets list`, Cloudflare dashboard); rotate per `secret-setup.md` if expired.
3. Confirm `/healthz` lag returns to seconds. **Do not deploy anything while replication is down** — the loss window is open.

### 3b. Corruption / bad writes — restore from replica

Never restore directly over the live file first. Restore to scratch, verify, then swap:

```sh
fly ssh console
litestream restore -o /data/restore-check.db \
  [-timestamp <ISO8601-just-before-corruption>] <replica-url-from-litestream.yml>
sqlite3 /data/restore-check.db "PRAGMA integrity_check;"      # expect: ok
sqlite3 /data/restore-check.db "SELECT COUNT(*), MAX(date) FROM entries;"  # sanity: plausible count + latest date
```

Swap (brief downtime, acceptable):

1. Stop the app: `fly machine stop` (stops Litestream too — prevents replicating the bad file further).
2. Via `fly ssh console` on a started-but-not-serving machine (or before stop, prepare): move bad file aside `mv /data/weight.db /data/weight.db.corrupt.<date>`; move verified restore into place `mv /data/restore-check.db /data/weight.db`; remove stale `-wal`/`-shm` files.
3. Start: `fly machine start`. Startup probes re-verify integrity; Litestream begins a **new replica generation** (expected — old generation stays in R2).
4. Verify: `/healthz` ok; open the app, confirm entries visible; log a test save.
5. Keep `weight.db.corrupt.<date>` for a week, then delete.

Loss window: seconds (continuous WAL streaming) — for PIT restore, whatever lies after `-timestamp`. At 1 entry/day, at most one entry; re-enter it manually.

### 3c. Rollback-schema mismatch

The probe refused start because DB schema is newer than the rolled-back code. Options: roll forward to the newer image (preferred — additive-only migrations mean the newer code is data-safe), or PIT-restore the DB to before the migration (§ 3b with `-timestamp`) if the newer release itself is the problem.

## 4. Escalate

There is no one to page. Escalation = stop using the app until fixed; the paper fallback is writing the morning weight in Notes and backfilling later (Slice 03 exists for this). If Fly or R2 has a platform outage, wait it out — the replica in R2 plus this runbook is the recovery path for total machine loss (`litestream restore` onto a fresh machine/volume).

## 5. Afterwards

- Note what happened and the fix (one paragraph, `docs/evolution/` or commit message).
- If the drill caught it: good — the drill did its job. If UptimeRobot caught it first, check why the drill didn't.
- If a probe gap allowed bad data to be served, extend the probe (via normal DELIVER cycle).
