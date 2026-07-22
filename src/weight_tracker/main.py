"""Production entrypoint (imperative shell): `uvicorn weight_tracker.main:app`.

Runs as the child of the Litestream supervisor (Dockerfile CMD, DEVOPS
coexistence rule). Configuration arrives from the environment (Fly secrets,
`docs/product/architecture/secret-setup.md`):

    PASSPHRASE_HASH       argon2id hash of the login passphrase (required)
    SESSION_SIGNING_KEY   signs the session cookie (required)
    DB_PATH               SQLite path (default /data/weight.db)

A missing secret or a failing startup probe raises at import time, so uvicorn
exits non-zero, Litestream (PID 1) terminates, and Fly restarts the machine —
the app never serves traffic past a refused probe (`health.startup.refused`).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from weight_tracker.composition import build_app
from weight_tracker.shell.clock import SystemClock

DEFAULT_DB_PATH = "/data/weight.db"


def build_production_app() -> Any:
    """Wire the production composition from environment configuration."""
    return build_app(
        db_path=Path(os.environ.get("DB_PATH", DEFAULT_DB_PATH)),
        clock=SystemClock(),
        passphrase_hash=os.environ["PASSPHRASE_HASH"],
        session_signing_key=os.environ["SESSION_SIGNING_KEY"],
    )


app = build_production_app()
