"""Theme delivery + G-4/G-5 verification (US-008/US-009, ADR-007, Q1/Q6)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from domain_types import (
    CONTRAST_CONTRACT,
    MIN_CONTRAST_RATIO,
    TEST_PASSPHRASE,
    ColorPairing,
    ColorScheme,
    ContrastClass,
    Screen,
    contrast_ratio,
)
from pages import THEME_ASSET_PATH, Page, ThemeSheet, read_page, read_theme

from services._base import BROWSER_HTML, Service

#: DISCUSS D9 / G-5 pin: total added CSS budget, uncompressed.
THEME_BUDGET_BYTES = 10 * 1024
#: Shell assets carrying no personal data (ADR-003 threat model protects the
#: RECORD): the door's clothes and the PWA shell stay reachable while locked.
OPEN_SHELL_ASSETS = (THEME_ASSET_PATH, "/manifest.webmanifest", "/sw.js")
#: G-5 script clause as consciously renegotiated by graph-first-home (2026-07-24):
#: the ONLY script sources the morning screen may carry -- same-origin, vendored.
SANCTIONED_ENTRY_SCRIPTS = frozenset({"/static/uplot.iife.min.js", "/static/graph.js"})


class ThemeService(Service):
    """The theme is a pure static asset with an EMPTY mutation universe (DESIGN):
    every method here is a read-only probe, so no state-delta applies (Mandate 8
    is carried by the reused logging/glance steps in the same scenarios). The
    contrast checker below is the AUTHORITATIVE G-4 instrument: WCAG
    relative-luminance arithmetic (pure, in domain_types) over the hex tokens
    the served asset actually declares -- pinned to required RATIOS, never to
    hex values, so one-hex-step nudges (Q6) stay green."""

    def _authed_probe(self) -> Any:
        """Tolerant authed client: server faults become status codes, never raises,
        so a missing asset fails a 200-assertion (RED) instead of erroring (BROKEN)."""
        if getattr(self, "_probe", None) is None:
            self._probe = self.comp.stranger(raise_server_exceptions=False)
            resp = self._probe.post("/login", data={"passphrase": TEST_PASSPHRASE})
            assert resp.status_code in (200, 303), f"probe login failed: {resp.status_code}"
        return self._probe

    def _locked_browser(self) -> Any:
        """A fresh cookie-less browser navigation: what a locked visitor sees."""
        return self.comp.stranger(raise_server_exceptions=False)

    def _page(self, screen: Screen) -> Page:
        if screen is Screen.DOOR:
            resp = self._locked_browser().get("/", headers=BROWSER_HTML)
        else:
            path = {Screen.ENTRY: "/", Screen.GRAPH: "/graph"}[screen]
            resp = self._authed_probe().get(path, headers=BROWSER_HTML)
        ctx_ok = resp.status_code in (200, 401)  # the door answers 401 with its page
        assert ctx_ok, f"the {screen.value} did not open: {resp.status_code}"
        return read_page(resp)

    def _theme(self, ctx: SimpleNamespace) -> ThemeSheet:
        if getattr(ctx, "theme", None) is None:
            self.fetch_delivered(ctx)
        return ctx.theme

    # -- wearing / delivery -------------------------------------------------

    def assert_screen_wears_theme(self, ctx: SimpleNamespace, screen: Screen) -> None:
        assert self._page(screen).wears_theme, (
            f"the {screen.value} must wear the calm theme "
            f"(a stylesheet link to {THEME_ASSET_PATH}), but its page carries none"
        )

    def fetch_delivered(self, ctx: SimpleNamespace) -> None:
        """Fetch the theme from the tracker itself; THE RED anchor while it is unbuilt."""
        resp = self._authed_probe().get(THEME_ASSET_PATH)
        assert resp.status_code == 200, (
            f"the calm theme must be delivered by the tracker itself at {THEME_ASSET_PATH}, "
            f"got {resp.status_code}"
        )
        ctx.theme = read_theme(resp)

    def assert_shell_assets_open_while_locked(self, ctx: SimpleNamespace) -> None:
        """US-008 regression: a cookie-less browser still receives the shell
        assets (theme, manifest, service worker) -- they carry no personal data
        (ADR-003), so the door arrives dressed while the record stays locked."""
        locked = self._locked_browser()
        answers = {asset: locked.get(asset) for asset in OPEN_SHELL_ASSETS}
        refused = {a: r.status_code for a, r in answers.items() if r.status_code != 200}
        assert not refused, (
            "shell assets carry no personal data and must dress the door even "
            f"while the record is locked, but the gate refused: {refused}"
        )
        ctx.theme = read_theme(answers[THEME_ASSET_PATH])
        assert ctx.theme.looks_like_stylesheet, (
            "the locked visitor must receive the stylesheet itself, "
            f"not a substitute body: {ctx.theme.css[:120]!r}"
        )

    def assert_dressed_for_both_lights(self, ctx: SimpleNamespace) -> None:
        appearances = self._theme(ctx).appearances
        for scheme in ColorScheme:
            missing = {"--bg", "--text"} - appearances[scheme].keys()
            assert not missing, (
                f"the theme must define a {scheme.value} appearance "
                f"(page and ink colors), missing {sorted(missing)}"
            )

    def examine_appearances(self, ctx: SimpleNamespace) -> None:
        ctx.appearances = self._theme(ctx).appearances

    # -- G-4: the contrast contract ------------------------------------------

    def assert_contrast_class_holds(
        self, ctx: SimpleNamespace, contrast_class: ContrastClass
    ) -> None:
        required = MIN_CONTRAST_RATIO[contrast_class]
        complaints = [
            f"{pairing.label} in {scheme.value}: {self._pairing_verdict(ctx, scheme, pairing)}"
            for scheme in ColorScheme
            for pairing in CONTRAST_CONTRACT
            if pairing.contrast_class is contrast_class
            and self._pairing_verdict(ctx, scheme, pairing) is not None
        ]
        assert not complaints, (
            f"every {contrast_class.value} pairing must reach {required}:1 "
            f"in both lights (G-4), but:\n  " + "\n  ".join(complaints)
        )

    def _pairing_verdict(
        self, ctx: SimpleNamespace, scheme: ColorScheme, pairing: ColorPairing
    ) -> str | None:
        tokens = ctx.appearances[scheme]
        if pairing.ink not in tokens or pairing.surface not in tokens:
            return f"colors {pairing.ink}/{pairing.surface} are not declared"
        ratio = contrast_ratio(tokens[pairing.ink], tokens[pairing.surface])
        required = MIN_CONTRAST_RATIO[pairing.contrast_class]
        return None if ratio >= required else f"{ratio:.2f}:1 falls short of {required}:1"

    def assert_dim_light_answers_daylight(self, ctx: SimpleNamespace) -> None:
        contract_names = {p.ink for p in CONTRAST_CONTRACT} | {p.surface for p in CONTRAST_CONTRACT}
        declared = ctx.appearances[ColorScheme.DAYLIGHT].keys() & contract_names
        unanswered = declared - self._theme(ctx).dark_overrides
        assert not unanswered, (
            "every color the daylight appearance names must be answered in dim light "
            f"(or 06:45 gets the flashbang back), unanswered: {sorted(unanswered)}"
        )

    # -- G-5: the cost of the look --------------------------------------------

    def tally_cost(self, ctx: SimpleNamespace) -> None:
        self.fetch_delivered(ctx)
        ctx.dressed_pages = {screen: self._page(screen) for screen in Screen}

    def assert_budget_kept(self, ctx: SimpleNamespace, kilobytes: int) -> None:
        assert ctx.theme.byte_size <= kilobytes * 1024, (
            f"the whole look must weigh no more than {kilobytes} KB uncompressed (G-5), "
            f"but weighs {ctx.theme.byte_size} bytes"
        )

    def assert_self_contained(self, ctx: SimpleNamespace) -> None:
        reaching = {"the theme itself": ctx.theme.other_origin_marks} | {
            f"the {screen.value}": page.other_origin_marks
            for screen, page in ctx.dressed_pages.items()
        }
        reaching = {name: marks for name, marks in reaching.items() if marks}
        assert not reaching, (
            f"no screen may reach beyond the tracker's own walls (G-5), but: {reaching}"
        )

    def assert_entry_moving_parts_own(self, ctx: SimpleNamespace) -> None:
        """G-5 script clause, CONSCIOUSLY renegotiated 2026-07-24 (graph-first-home
        DISTILL, per the ADR-008 disclosure and the DISCUSS System-Constraints flag):
        the literal "0 new entry-screen scripts" count cannot survive a front-page
        graph; the surviving intent -- zero external origins, no third-party cost --
        is pinned as: exactly one inline script plus, at most, the two SAME-ORIGIN
        vendored chart scripts. Never a silent deletion."""
        entry: Page = ctx.dressed_pages[Screen.ENTRY]
        foreign = [src for src in entry.script_sources if src not in SANCTIONED_ENTRY_SCRIPTS]
        assert entry.inline_script_count == 1 and not foreign, (
            "every moving part on the morning screen must be the tracker's own "
            "(G-5 as renegotiated: one inline script + sanctioned same-origin chart "
            f"scripts only), found {entry.inline_script_count} inline and foreign "
            f"sources {foreign}"
        )

    # -- structural promises carried by the asset ------------------------------

    def assert_touch_comfort_promised(self, ctx: SimpleNamespace) -> None:
        assert self._theme(ctx).promises_touch_comfort, (
            "the theme must promise comfortable touch targets everywhere "
            "(the door's 44px rule, now global)"
        )

    def assert_pressed_beyond_color(self, ctx: SimpleNamespace) -> None:
        assert self._theme(ctx).styles_pressed_state, (
            "the pressed control must be promised a look of its own beyond color "
            "(a styled pressed state in the theme)"
        )

    def assert_chart_single_palette(self, ctx: SimpleNamespace) -> None:
        hardcoded = self._page(Screen.GRAPH).hex_colors
        assert not hardcoded, (
            "the chart must draw every line from the tracker's single palette; "
            f"the graph page still carries its own colors: {hardcoded}"
        )

    # -- progressive enhancement (US-008 domain example 3) ---------------------

    def break_delivery(self, monkeypatch: Any) -> None:
        """The theme goes missing: the static shelf is emptied for this scenario."""
        from weight_tracker.web import routes

        bare_shelf = self.comp.db_path.parent / "bare-static-shelf"
        bare_shelf.mkdir(exist_ok=True)
        monkeypatch.setattr(routes, "_static_dir", bare_shelf)

    def assert_morning_still_ready(self, ctx: SimpleNamespace) -> None:
        probe = SimpleNamespace(response=self.comp.screen.open_entry())
        assert probe.response.status_code == 200, "the morning screen must still open"
        self.comp.screen.assert_ready_for_typing(probe)
