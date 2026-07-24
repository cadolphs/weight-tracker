"""AccessGate: passphrase login + signed-cookie session guard (ADR-003).

Driving middleware over the whole route surface: POST /login verifies the
passphrase against the argon2id hash and issues a signed HttpOnly cookie;
every other route (except the open paths) requires a valid session cookie.

Login is rate-limited (in-process, single instance per ADR-003): repeated
wrong guesses in a row throttle further attempts -- even the right
passphrase waits out the cooldown. The throttle decision logic is pure
(state value in, verdict/new state out); the gate holds one mutable
reference and the current instant arrives from the injected clock.

Session ageing (ADR-003): the signed token embeds its issue instant, and
expiry is a pure judgement of that instant against the injected clock's
now -- an unlock lasts 90 days, then the passphrase is asked again.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import argon2
from argon2.exceptions import VerifyMismatchError
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, Signer

from weight_tracker.ports import ClockPort

SESSION_COOKIE = "session"
SESSION_LIFETIME = timedelta(days=90)
SESSION_MAX_AGE_SECONDS = int(SESSION_LIFETIME.total_seconds())

#: The gate's contract: shell assets open, record routes locked. Reachable while
#: LOCKED are the login door, the health surface, and the no-personal-data shell
#: (theme/vendored assets, PWA manifest, service worker) per the ADR-003 threat
#: model -- what is protected is the weight RECORD, not the tracker's clothes.
OPEN_PATHS = frozenset({"/login", "/healthz", "/manifest.webmanifest", "/sw.js"})
OPEN_PREFIXES = ("/static/",)


def path_is_open(path: str) -> bool:
    """Pure gate decision: may this path be served without a session?"""
    return path in OPEN_PATHS or path.startswith(OPEN_PREFIXES)


THROTTLE_AFTER_WRONG_GUESSES = 10
THROTTLE_COOLDOWN = timedelta(minutes=15)


# ---------------------------------------------------------------- the passphrase door

#: The gate's human face (AT_GAP-5): a locked browser navigation is met by this
#: page rather than a bare machine refusal. API clients keep the JSON contract.
_door_templates = Jinja2Templates(directory=Path(__file__).parent.parent / "web" / "templates")

WRONG_PASSPHRASE_MESSAGE = "Wrong passphrase — the record stays closed."
THROTTLED_MESSAGE = "Too many attempts — the door rests a while. Try again later."


def prefers_html(request: Request) -> bool:
    """A human page navigation announces itself with Accept: text/html."""
    return "text/html" in request.headers.get("accept", "")


def door_page(
    request: Request, *, rejection: str | None = None, status_code: int = 401
) -> Response:
    """Render the passphrase door: a label + password form submitting back to /login."""
    return _door_templates.TemplateResponse(
        request=request,
        name="door.html",
        context={"rejection": rejection},
        status_code=status_code,
    )


# ---------------------------------------------------------------- pure core


@dataclass(frozen=True)
class ThrottleState:  # probe-exempt
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


def session_fresh(issued_at: datetime, now: datetime) -> bool:
    """Pure expiry judgement: an unlock lasts SESSION_LIFETIME from its issue instant."""
    return now - issued_at < SESSION_LIFETIME


@dataclass(frozen=True)
class Unlocked:  # probe-exempt
    session_token: str


@dataclass(frozen=True)
class Rejected:  # probe-exempt
    pass


@dataclass(frozen=True)
class Throttled:  # probe-exempt
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

    def session_open(self, session_token: str | None, now: datetime) -> bool:
        """A session is open when its signature holds AND its embedded issue instant is fresh."""
        if not session_token:
            return False
        try:
            issued_at_raw = self._signer.unsign(session_token).decode()
            issued_at = datetime.fromisoformat(issued_at_raw)
        except (BadSignature, ValueError):
            return False
        return session_fresh(issued_at, now)


def install_access_gate(app: FastAPI, gate: AccessGate, clock: ClockPort) -> None:
    """Guard all routes behind the gate, leaving only `path_is_open` paths reachable
    while locked (shell assets open, record routes locked).

    Session age is judged against the injected clock (never the wall clock)."""

    @app.middleware("http")
    async def guard_routes(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if path_is_open(request.url.path):
            return await call_next(request)
        if gate.session_open(request.cookies.get(SESSION_COOKIE), now=clock.now_utc()):
            return await call_next(request)
        if prefers_html(request):
            return door_page(request)
        return JSONResponse({"detail": "locked"}, status_code=401)
