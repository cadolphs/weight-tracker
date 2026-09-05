# 2026-09-05 — R2 replication was never active; restore drill red since first run

**What happened.** Every scheduled `restore-drill` run since 2026-07-27 failed at
`litestream restore` with `cannot lookup bucket region: InvalidAccessKeyId` (AWS request ids).
Litestream 0.3.13's `s3.ParseHost` has host rules for AWS, Backblaze, Filebase, DigitalOcean,
Scaleway and Linode only; an `*.r2.cloudflarestorage.com` host falls through to
bucket=<whole host>, endpoint="", and the region lookup goes to AWS. Production ran the same
version with the same `url: ${REPLICA_URL}` config, so Litestream logged `monitor error` once a
second from first deploy and never wrote a byte to R2. Nothing surfaced: the monitor loop only
logs and retries, and `/healthz` `replication_status` reports "active" whenever the local
`.weight.db-litestream` directory exists.

**Evidence.** Drill run 33942011733 with the endpoint fixed authenticated against R2 with the
read-only token and got `no matching backups found` (bucket empty). `fly logs` on the same day
showed the AWS error every second. Guardrail G-1 (zero lost entries) was violated from launch:
the Fly volume held the only copy (14 entries, 2026-07-23 … 2026-09-04). A manual SQLite
`.backup` was pulled to the operator's machine before touching anything.

**Fix.** Drill: derive bucket/endpoint/path from the secret and restore via `-config` with an
explicit `endpoint`. Production: `entrypoint.sh` derives the same three values from
`REPLICA_URL`; `/etc/litestream.yml` uses `bucket`/`path`/`endpoint`/`region: auto` instead of
`url`. A malformed `REPLICA_URL` now refuses startup instead of running unreplicated. The
runbook's restore command uses the `-config` form.

**Still open.** `/healthz` should report real replication state (last successful sync, not a
directory check); the runbook and secret-setup still talk about a "replication lag" figure the
app never exposed. Upgrading Litestream (0.5.x) would not remove the need for an explicit
endpoint.

**Lesson.** A guardrail that has never been seen green is not a guardrail. The first scheduled
drill run should have been treated as an incident on 2026-07-27, and the drill should have been
dispatched by hand right after the first deploy.
