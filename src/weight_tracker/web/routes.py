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
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from weight_tracker.core.types import Entry, Saved
from weight_tracker.core.validation import validate_entry_date, validate_weight
from weight_tracker.ports import ClockPort, EntryStorePort
from weight_tracker.shell.access_gate import SESSION_COOKIE, SESSION_MAX_AGE_SECONDS, AccessGate

ENTRY_SAVED_EVENT = "entry.saved"
TREND_VIEW_OPENED_EVENT = "trend.view.opened"

_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def build_router(*, store: EntryStorePort, gate: AccessGate, clock: ClockPort) -> APIRouter:
    router = APIRouter()

    @router.post("/login")
    async def login(request: Request):
        form = parse_qs((await request.body()).decode())
        passphrase = form.get("passphrase", [""])[0]
        if not gate.passphrase_matches(passphrase):
            return JSONResponse({"detail": "wrong passphrase"}, status_code=401)
        response = JSONResponse({"status": "unlocked"})
        response.set_cookie(
            SESSION_COOKIE,
            gate.issue_session(issued_at=clock.now_utc()),
            max_age=SESSION_MAX_AGE_SECONDS,
            httponly=True,
            samesite="lax",
        )
        return response

    @router.get("/")
    def entry_screen(request: Request):
        return _templates.TemplateResponse(request=request, name="index.html")

    @router.post("/entries")
    async def save_entry(request: Request):
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
    def history(scale: str = "ALL"):
        entries = store.all_entries()  # newest first; scale windowing lands in later steps
        return {
            "entries": [
                {"date": entry.day.isoformat(), "weight_kg": entry.weight_kg}
                for entry in entries
            ],
            "invite_first_log": not entries,
        }

    @router.get("/stats")
    def stats():
        return {
            "entry_logged_count": store.count_events(ENTRY_SAVED_EVENT),
            "trend_view_opened_count": store.count_events(TREND_VIEW_OPENED_EVENT),
        }

    return router
