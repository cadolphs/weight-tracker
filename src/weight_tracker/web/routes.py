"""HTTP routes (driving adapters over the driving ports).

Route contract = `build_app` docstring in weight_tracker.composition (executable
spec). Dependencies arrive as function parameters (functional DI): the router is
built over the entry store port, the access gate, and the clock port.

Current scope: login, save-entry (confirmed and rejected paths, inline
messaging), history read-back, telemetry counts, entry-screen page shell.
Remaining surface (trend, graph, manifest, scale windowing) lands with its
dedicated steps.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from weight_tracker.core.types import Entry, Rejected, RejectionReason, Saved
from weight_tracker.core.validation import validate_entry_date, validate_weight
from weight_tracker.ports import ClockPort, EntryStorePort
from weight_tracker.shell.access_gate import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    AccessGate,
    Throttled,
    Unlocked,
)
from weight_tracker.shell.access_gate import (
    Rejected as PassphraseRejected,
)

ENTRY_SAVED_EVENT = "entry.saved"
TREND_VIEW_OPENED_EVENT = "trend.view.opened"

#: Shell translation of the core's closed RejectionReason set into inline messages (C6b/C6c).
#: The core judges; the shell phrases. No validation logic lives here.
REJECTION_MESSAGES: dict[RejectionReason, str] = {
    RejectionReason.OUT_OF_RANGE: "The value must be between 30.0 and 250.0 kg.",
    RejectionReason.BAD_PRECISION: "The value is finer than the 0.1 kg scale.",
    RejectionReason.NOT_A_WEIGHT: "That is not a weight.",
    RejectionReason.MISSING_VALUE: "A weight is required.",
    RejectionReason.FUTURE_DATE: "Future dates cannot be logged.",
    RejectionReason.BAD_DATE: "The date is not recognisable.",
}


def _rejected_save(rejected: Rejected, typed_value: str) -> dict[str, Any]:
    """Rejected-save response: closed reason, inline message, typed value kept for correction."""
    return {
        "outcome": "rejected",
        "reason": rejected.reason.value,
        "message": REJECTION_MESSAGES[rejected.reason],
        "echo": typed_value,
    }


_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _log_auth_event(name: str) -> None:
    """Structured auth trail: auth.login.{ok,rejected,rate_limited} (ADR-003)."""
    print(json.dumps({"event": name}), file=sys.stderr)


def build_router(
    *,
    store: EntryStorePort,
    gate: AccessGate,
    clock: ClockPort,
    replication_status: Callable[[], str],
) -> APIRouter:
    router = APIRouter()

    @router.post("/login")
    async def login(request: Request) -> JSONResponse:
        form = parse_qs((await request.body()).decode())
        passphrase = form.get("passphrase", [""])[0]
        match gate.attempt_login(passphrase, now=clock.now_utc()):
            case Throttled():
                _log_auth_event("auth.login.rate_limited")
                return JSONResponse({"detail": "too many attempts"}, status_code=429)
            case PassphraseRejected():
                _log_auth_event("auth.login.rejected")
                return JSONResponse({"detail": "wrong passphrase"}, status_code=401)
            case Unlocked(session_token=session_token):
                _log_auth_event("auth.login.ok")
                response = JSONResponse({"status": "unlocked"})
                response.set_cookie(
                    SESSION_COOKIE,
                    session_token,
                    max_age=SESSION_MAX_AGE_SECONDS,
                    httponly=True,
                    samesite="lax",
                )
                return response
        raise AssertionError("unreachable: LoginOutcome is a closed choice type")

    @router.get("/")
    def entry_screen(request: Request) -> Response:
        return _templates.TemplateResponse(request=request, name="index.html")

    @router.post("/entries")
    async def save_entry(request: Request) -> dict[str, Any]:
        submitted = await request.json()
        typed_weight = str(submitted.get("weight", ""))
        weight_kg = validate_weight(typed_weight)
        if isinstance(weight_kg, Rejected):
            return _rejected_save(weight_kg, typed_value=typed_weight)
        day = validate_entry_date(
            str(submitted.get("date", "")), server_utc_today=clock.now_utc().date()
        )
        if isinstance(day, Rejected):
            return _rejected_save(day, typed_value=typed_weight)
        logged_at = clock.now_utc().isoformat()
        entry = Entry(day=day, weight_kg=weight_kg, entry_ms=submitted.get("entry_ms"))
        store.upsert(entry, logged_at=logged_at)
        store.append_event(
            ts=logged_at,
            name=ENTRY_SAVED_EVENT,
            payload=json.dumps({"date": day.isoformat(), "entry_ms": entry.entry_ms}),
        )
        saved = Saved(day=day, weight_kg=weight_kg)
        return {
            "outcome": "saved",
            "confirmation": saved.confirmation,
            "date": day.isoformat(),
            "weight_kg": weight_kg,
        }

    @router.get("/entries")
    def history(scale: str = "ALL") -> dict[str, Any]:
        entries = store.all_entries()  # newest first; scale windowing lands in later steps
        return {
            "entries": [
                {"date": entry.day.isoformat(), "weight_kg": entry.weight_kg} for entry in entries
            ],
            "invite_first_log": not entries,
        }

    @router.get("/stats")
    def stats() -> dict[str, Any]:
        return {
            "entry_logged_count": store.count_events(ENTRY_SAVED_EVENT),
            "trend_view_opened_count": store.count_events(TREND_VIEW_OPENED_EVENT),
        }

    @router.get("/healthz")
    def healthz() -> dict[str, str]:
        """Unauthenticated operational surface: status only, never record data.

        Serving at all means every startup probe passed (build_app refuses otherwise)."""
        return {
            "status": "ok",
            "startup_probe": "passed",
            "replication": replication_status(),
        }

    return router
