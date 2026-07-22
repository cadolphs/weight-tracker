"""Driving-adapter integration: scale query param robustness (review D1, C6).

Real SQLite on tmp_path through the production composition root (build_app).
Single-example per paradigm rules -- integration verifies WIRING, not input
equivalence classes.

Contract (adversarial review D1, C6 principle):
- Hostile input must never 500: an unknown ?scale= value answers HTTP 400
  with a JSON message listing the valid scales (1W, 1M, 3M, 6M, 1Y, ALL).
- Scale tokens are STRICT (pinned at revision): `All` is not `ALL` -- a
  mis-cased token is corrected via the 400 message, never guessed at.
- A valid scale still answers 200 on every windowed route.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from argon2 import PasswordHasher
from fake_clock import FakeClock
from fastapi.testclient import TestClient

from weight_tracker.composition import build_app

PASSPHRASE = "integration-test-passphrase"
VALID_SCALES = ("1W", "1M", "3M", "6M", "1Y", "ALL")


def _unlocked_client(tmp_path: Path) -> TestClient:
    """One production startup + unlocked session (hostile responses stay HTTP)."""
    app = build_app(
        db_path=tmp_path / "weight.db",
        clock=FakeClock(),
        passphrase_hash=PasswordHasher().hash(PASSPHRASE),
        session_signing_key="integration-test-signing-key",
    )
    client = TestClient(app, raise_server_exceptions=False)
    assert client.post("/login", data={"passphrase": PASSPHRASE}).status_code == 200
    return client


@pytest.mark.driving_adapter
@pytest.mark.real_io
@pytest.mark.error
@pytest.mark.parametrize(
    ("path", "hostile_scale"),
    [("/entries", "All"), ("/trend", "garbage"), ("/graph", "nope")],
)
def test_unknown_scale_answers_400_listing_valid_scales(
    tmp_path: Path, path: str, hostile_scale: str
) -> None:
    response = _unlocked_client(tmp_path).get(path, params={"scale": hostile_scale})

    assert response.status_code == 400, (
        f"{path}?scale={hostile_scale} must answer 400, got {response.status_code}"
    )
    message = response.json()["detail"]
    assert all(scale in message for scale in VALID_SCALES), (
        f"the 400 message must list every valid scale for correction, got {message!r}"
    )


@pytest.mark.driving_adapter
@pytest.mark.real_io
@pytest.mark.parametrize("path", ["/entries", "/trend", "/graph"])
def test_valid_scale_still_answers_200(tmp_path: Path, path: str) -> None:
    response = _unlocked_client(tmp_path).get(path, params={"scale": "ALL"})

    assert response.status_code == 200, (
        f"{path}?scale=ALL must keep answering 200, got {response.status_code}"
    )
