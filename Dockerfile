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

# Litestream replica config. No secrets baked in: REPLICA_URL (s3://<bucket>.<account>.r2.
# cloudflarestorage.com/<path>) plus LITESTREAM_ACCESS_KEY_ID / LITESTREAM_SECRET_ACCESS_KEY
# arrive as Fly secrets at runtime (secret-setup.md) and are expanded by Litestream.
COPY <<'EOF' /etc/litestream.yml
dbs:
  - path: /data/weight.db
    replicas:
      - url: ${REPLICA_URL}
EOF

ENV PATH="/app/.venv/bin:$PATH" \
    DB_PATH=/data/weight.db \
    PYTHONUNBUFFERED=1

# SQLite lives on the Fly volume mounted at /data (fly.toml [mounts]); the volume
# must survive every recreate deploy — entry data is never part of the image (DA-2).
VOLUME ["/data"]
EXPOSE 8080

CMD ["litestream", "replicate", "-exec", "uvicorn weight_tracker.main:app --host 0.0.0.0 --port 8080"]
