"""Adapter integration: schema-version rollback guard (DEVOPS pre-requisite 2a).

Real SQLite on tmp_path through the production composition root (build_app).
Single-example per paradigm rules -- integration verifies WIRING, not input
equivalence classes.

Contract (feature-delta.md, Wave: DEVOPS, Pre-Requisites 2a):
- schema_version table created and populated on first startup; migrations
  are additive-only and idempotent (second startup over the same file is a no-op).
- Probe passes when code version >= DB version.
- Probe refuses start (StartupRefused, probe=entry_store.schema_version in the
  structured health.startup.refused log) when DB version > code version --
  i.e. a rollback landed behind a schema change.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from argon2 import PasswordHasher
from fake_clock import FakeClock

from weight_tracker.composition import StartupRefused, build_app

# The pre-existing schema (entries + events, ADR-002) folds as migration version 1
# (feature-delta.md DEVOPS 2a); bump alongside future additive migrations.
CURRENT_SCHEMA_VERSION = 1


def _start_tracker(db_path: Path) -> Any:
    """One production startup over the given record file (production wiring)."""
    return build_app(
        db_path=db_path,
        clock=FakeClock(),
        passphrase_hash=PasswordHasher().hash("integration-test-passphrase"),
        session_signing_key="integration-test-signing-key",
    )


def _schema_version_rows(db_path: Path) -> list[tuple[int, str]]:
    with sqlite3.connect(db_path) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        ).fetchone()
        assert table is not None, "schema_version table must exist after startup"
        return connection.execute(
            "SELECT version, applied_ts FROM schema_version ORDER BY version"
        ).fetchall()


@pytest.mark.adapter_integration
@pytest.mark.real_io
def test_first_startup_stamps_schema_version_and_restart_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "weight.db"

    _start_tracker(db_path)
    rows_after_first_startup = _schema_version_rows(db_path)

    _start_tracker(db_path)  # restart over the SAME file: migrations must be idempotent
    rows_after_restart = _schema_version_rows(db_path)

    assert [version for version, _ in rows_after_first_startup] == [CURRENT_SCHEMA_VERSION]
    assert all(applied_ts for _, applied_ts in rows_after_first_startup), (
        "each applied migration must be recorded with its applied_ts"
    )
    assert rows_after_restart == rows_after_first_startup, (
        "a second startup must not re-apply or re-stamp migrations"
    )


@pytest.mark.adapter_integration
@pytest.mark.real_io
@pytest.mark.error
def test_db_version_ahead_of_code_refuses_start(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "weight.db"
    _start_tracker(db_path)  # healthy v-current record...

    with sqlite3.connect(db_path) as connection:  # ...then a newer release stamps ahead
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_version"
            " (version INTEGER PRIMARY KEY, applied_ts TEXT NOT NULL)"
        )
        connection.execute(  # the VERY NEXT version: pins the exact refusal boundary
            "INSERT INTO schema_version (version, applied_ts) VALUES (?, '2099-01-01T00:00:00')",
            (CURRENT_SCHEMA_VERSION + 1,),
        )
        connection.commit()

    with pytest.raises(StartupRefused):  # the rolled-back code must fail safe, not serve
        _start_tracker(db_path)

    refusal = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert refusal["event"] == "health.startup.refused"
    assert refusal["probe"] == "entry_store.schema_version"
