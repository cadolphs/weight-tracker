"""HTTP routes (driving adapters over the driving ports).

Route contract = `build_app` docstring in weight_tracker.composition (executable
spec). Dependencies arrive as function parameters (functional DI): the router is
built over the entry store port, the access gate, and the clock port.

Walking-skeleton scope: login, save-entry happy path, history read-back,
telemetry counts, entry-screen page shell. Remaining surface (trend, graph,
healthz, manifest, scale windowing) lands with its dedicated steps.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from weight_tracker.core.types import Entry, Saved
from weight_tracker.core.validation import validate_entry_date, validate_weight
from weight_tracker.ports import ClockPort, EntryStorePort
from weight_tracker.shell.access_gate import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    AccessGate,
    Rejected,
    Throttled,
    Unlocked,
)

ENTRY_SAVED_EVENT = "entry.saved"
TREND_VIEW_OPENED_EVENT = "trend.view.opened"

_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _log_auth_event(name: str) -> None:
    """Structured auth trail: auth.login.{ok,rejected,rate_limited} (ADR-003)."""
    print(json.dumps({"event": name}), file=sys.stderr)


def build_router(*, store: EntryStorePort, gate: AccessGate, clock: ClockPort) -> APIRouter:
    router = APIRouter()

    @router.post("/login")
    async def login(request: Request) -> JSONResponse:
        form = parse_qs((await request.body()).decode())
        passphrase = form.get("passphrase", [""])[0]
        match gate.attempt_login(passphrase, now=clock.now_utc()):
            case Throttled():
                _log_auth_event("auth.login.rate_limited")
                return JSONResponse({"detail": "too many attempts"}, status_code=429)
            case Rejected():
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
        weight_kg = validate_weight(str(submitted.get("weight", "")))
        day = validate_entry_date(
            str(submitted.get("date", "")), server_utc_today=clock.now_utc().date()
        )
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

    return router
