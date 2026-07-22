"""AccessGate: passphrase login + signed-cookie session guard (ADR-003).

Driving middleware over the whole route surface: POST /login verifies the
passphrase against the argon2id hash and issues a signed HttpOnly cookie;
every other route (except the open paths) requires a valid session cookie.

Login is rate-limited (in-process, single instance per ADR-003): repeated
wrong guesses in a row throttle further attempts -- even the right
passphrase waits out the cooldown. The throttle decision logic is pure
(state value in, verdict/new state out); the gate holds one mutable
reference and the current instant arrives from the injected clock.

Session ageing (90-day expiry judged against the injected clock) lands
with its dedicated access-protection steps.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

import argon2
from argon2.exceptions import VerifyMismatchError
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from itsdangerous import BadSignature, Signer

SESSION_COOKIE = "session"
SESSION_MAX_AGE_SECONDS = 90 * 24 * 60 * 60

#: Routes reachable while LOCKED: the login door itself and the health surface.
OPEN_PATHS = frozenset({"/login", "/healthz"})

THROTTLE_AFTER_WRONG_GUESSES = 10
THROTTLE_COOLDOWN = timedelta(minutes=15)


# ---------------------------------------------------------------- pure core


@dataclass(frozen=True)
class ThrottleState:
    """Consecutive wrong guesses and, once over the limit, when guessing reopens."""

    consecutive_failures: int = 0
    throttled_until: datetime | None = None


def throttle_active(state: ThrottleState, now: datetime) -> bool:
    return state.throttled_until is not None and now < state.throttled_until


def after_wrong_passphrase(state: ThrottleState, now: datetime) -> ThrottleState:
    failures = state.consecutive_failures + 1
    if failures >= THROTTLE_AFTER_WRONG_GUESSES:
        return ThrottleState(failures, now + THROTTLE_COOLDOWN)
    return ThrottleState(failures, None)


def after_right_passphrase() -> ThrottleState:
    return ThrottleState()


@dataclass(frozen=True)
class Unlocked:
    session_token: str


@dataclass(frozen=True)
class Rejected:
    pass


@dataclass(frozen=True)
class Throttled:
    pass


LoginOutcome = Unlocked | Rejected | Throttled


class AccessGate:
    def __init__(self, passphrase_hash: str, session_signing_key: str) -> None:
        self._passphrase_hash = passphrase_hash
        self._session_signing_key = session_signing_key
        self._hasher = argon2.PasswordHasher()
        self._signer = Signer(session_signing_key)
        self._throttle = ThrottleState()

    def attempt_login(self, passphrase: str, now: datetime) -> LoginOutcome:
        """Full login semantics: throttle check, verify, session issue (ADR-003)."""
        if throttle_active(self._throttle, now):
            return Throttled()
        if not self.passphrase_matches(passphrase):
            self._throttle = after_wrong_passphrase(self._throttle, now)
            if throttle_active(self._throttle, now):
                return Throttled()
            return Rejected()
        self._throttle = after_right_passphrase()
        return Unlocked(session_token=self.issue_session(issued_at=now))

    def probe(self) -> None:
        """Startup check: passphrase hash parseable as argon2, signing key present."""
        argon2.extract_parameters(self._passphrase_hash)
        if not self._session_signing_key:
            raise RuntimeError("SESSION_SIGNING_KEY is missing")

    def passphrase_matches(self, passphrase: str) -> bool:
        try:
            self._hasher.verify(self._passphrase_hash, passphrase)
        except VerifyMismatchError:
            return False
        return True

    def issue_session(self, issued_at: datetime) -> str:
        return self._signer.sign(issued_at.isoformat()).decode()

    def session_open(self, session_token: str | None) -> bool:
        if not session_token:
            return False
        try:
            self._signer.unsign(session_token)
        except BadSignature:
            return False
        return True


def install_access_gate(app: FastAPI, gate: AccessGate) -> None:
    """Guard all routes behind the gate, leaving only OPEN_PATHS reachable while locked."""

    @app.middleware("http")
    async def guard_routes(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in OPEN_PATHS:
            return await call_next(request)
        if gate.session_open(request.cookies.get(SESSION_COOKIE)):
            return await call_next(request)
        return JSONResponse({"detail": "locked"}, status_code=401)
