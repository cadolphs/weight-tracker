# Secret Setup and Rotation

Scope: production secrets for weight-tracker (ADR-003, ADR-002). All secrets live in Fly
secrets (runtime) and GitHub Actions secrets (CI); never in the repo, never echoed in CI logs.

## Inventory

| Secret | Where | Purpose |
|---|---|---|
| `PASSPHRASE_HASH` | Fly | argon2id hash of the login passphrase (ADR-003) |
| `SESSION_SIGNING_KEY` | Fly | signs the session cookie (itsdangerous) |
| `LITESTREAM_ACCESS_KEY_ID` / `LITESTREAM_SECRET_ACCESS_KEY` | Fly | R2 write credentials for Litestream replication |
| `FLY_API_TOKEN` | GitHub Actions | deploy from CI (`fly tokens create deploy -x 999999h`) |
| R2 read-only credentials | GitHub Actions | weekly restore drill (separate token, read-only) |

## Generation

```sh
# PASSPHRASE_HASH — choose a passphrase, hash it (argon2-cffi is a project dep):
python -c "from argon2 import PasswordHasher; import getpass; print(PasswordHasher().hash(getpass.getpass('passphrase: ')))"

# SESSION_SIGNING_KEY — 32 random bytes, hex:
python -c "import secrets; print(secrets.token_hex(32))"
```

R2 credentials: Cloudflare dashboard → R2 → *Manage R2 API Tokens* → create **two** tokens
scoped to the replica bucket only: one **Object Read & Write** (production/Litestream), one
**Object Read** (CI restore drill).

## Setting

```sh
fly secrets set PASSPHRASE_HASH='<argon2-hash>' \
                SESSION_SIGNING_KEY='<hex>' \
                LITESTREAM_ACCESS_KEY_ID='<id>' \
                LITESTREAM_SECRET_ACCESS_KEY='<key>'
# GitHub: repo Settings → Secrets and variables → Actions → FLY_API_TOKEN, R2 read-only pair
```

Note: `fly secrets set` restarts the machine (recreate semantics — fine). Startup probes
refuse to serve if any secret is missing or unparseable (`health.startup.refused`).

## `.env.example` (DELIVER must create; the real `.env` is git-ignored)

```
PASSPHRASE_HASH=            # argon2id hash — generate per secret-setup.md
SESSION_SIGNING_KEY=        # 32-byte hex
LITESTREAM_ACCESS_KEY_ID=   # leave empty locally to run without replication
LITESTREAM_SECRET_ACCESS_KEY=
DB_PATH=./dev.db            # local SQLite file (prod: /data/weight.db)
```

## Rotation and consequences

| Rotate | How | Consequence |
|---|---|---|
| Passphrase | re-hash, `fly secrets set PASSPHRASE_HASH=...` | existing sessions stay valid (cookie-based); next login needs new passphrase |
| `SESSION_SIGNING_KEY` | new hex, `fly secrets set ...` | **global logout** — all cookies invalidated immediately; this is also the revocation mechanism (ADR-003: signed-cookie revocation is expiry-only, key rotation forces logout) |
| R2 credentials | new tokens in Cloudflare, update Fly + GitHub secrets, revoke old | replication pauses during swap — watch `/healthz` lag returns to seconds; drill uses new read token next run |
| `FLY_API_TOKEN` | `fly tokens create deploy`, update GitHub secret, revoke old | none at runtime; next CI deploy uses it |

Cadence: rotate on suspicion or leak, not on a schedule (solo operator; scheduled rotation
adds risk of lockout without threat-model benefit).
