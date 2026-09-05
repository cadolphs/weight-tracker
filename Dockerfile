# syntax=docker/dockerfile:1
# Production image (DEVOPS Pre-Requisite 6): Litestream supervisor + uvicorn app.
# Litestream is PID 1 (`replicate -exec`); the app exits non-zero on any fatal
# error (StartupRefused at import) so Fly restarts the machine (coexistence rule).

FROM python:3.12-slim

# Litestream pinned to EXACTLY 0.3.13 (M-003) — never `latest`.
ADD https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.deb /tmp/litestream.deb
RUN dpkg -i /tmp/litestream.deb && rm /tmp/litestream.deb

# uv, pinned; dependencies from the committed lock file only.
COPY --from=ghcr.io/astral-sh/uv:0.9.24 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

# Litestream replica config. No secrets baked in: REPLICA_URL
# (s3://<bucket>.<account>.r2.cloudflarestorage.com[/<path>]) plus LITESTREAM_ACCESS_KEY_ID /
# LITESTREAM_SECRET_ACCESS_KEY arrive as Fly secrets at runtime (secret-setup.md).
#
# Litestream 0.3.13 cannot take an R2 replica as a bare `url:` — its host parser has no
# rule for *.r2.cloudflarestorage.com, so it treats the whole host as an AWS bucket name and
# fails every sync with "cannot lookup bucket region" (2026-09-05 evolution note). The
# entrypoint derives bucket / endpoint / path from REPLICA_URL and the config names them
# explicitly. Region "auto" is what R2 expects for SigV4.
COPY <<'EOF' /etc/litestream.yml
dbs:
  - path: /data/weight.db
    replicas:
      - type: s3
        bucket: ${R2_BUCKET}
        path: "${R2_PATH}"
        endpoint: ${R2_ENDPOINT}
        region: auto
EOF

COPY --chmod=755 <<'EOF' /usr/local/bin/entrypoint.sh
#!/bin/sh
# Derive R2_BUCKET / R2_ENDPOINT / R2_PATH from REPLICA_URL, then exec Litestream as PID 1.
# A missing or malformed REPLICA_URL is fatal on purpose: silently running without an
# off-host replica is the failure this guards against (durability guardrail G-1).
set -eu
case "${REPLICA_URL:-}" in
  s3://*) ;;
  *) echo 'startup.refused: REPLICA_URL must be s3://<bucket>.<account>.r2.cloudflarestorage.com[/<path>]' >&2; exit 1 ;;
esac
rest="${REPLICA_URL#s3://}"
host="${rest%%/*}"
case "$rest" in */*) rpath="${rest#*/}" ;; *) rpath="" ;; esac
bucket="${host%%.*}"
endpoint="https://${host#*.}"
case "$host" in
  *.r2.cloudflarestorage.com) ;;
  *) echo "startup.refused: REPLICA_URL host is not an R2 host" >&2; exit 1 ;;
esac
export R2_BUCKET="$bucket" R2_ENDPOINT="$endpoint" R2_PATH="$rpath"
exec litestream replicate -exec "uvicorn weight_tracker.main:app --host 0.0.0.0 --port 8080"
EOF

ENV PATH="/app/.venv/bin:$PATH" \
    DB_PATH=/data/weight.db \
    PYTHONUNBUFFERED=1

# SQLite lives on the Fly volume mounted at /data (fly.toml [mounts]); the volume
# must survive every recreate deploy — entry data is never part of the image (DA-2).
VOLUME ["/data"]
EXPOSE 8080

CMD ["/usr/local/bin/entrypoint.sh"]
