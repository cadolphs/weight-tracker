"""Page readers -- each rendered surface parsed ONCE into a typed frozen struct.

Every regex over rendered HTML (and over the served stylesheet) lives in this
module and nowhere else: a reader runs them all once, up front, and the services
assert over the fields. ADR-013 recorded that one row-grammar change once moved
three test modules; after this split a grammar change moves one reader.

Readers are total over any response text: a JSON body or a bare door page simply
yields empty/None fields, so a service can read the entry screen off whatever
`ctx.response` holds and let its own assertion name what is missing.

Executable markup contracts (DISTILL, as revised by later features):

* graph-first-home (US-010/011/012, 2026-07-24) as REVISED by numeric-trend-history
  (US-016, 2026-09-09, D-38): the front-page graph mounts at id="home-graph"
  carrying data-view/data-scale exactly like the History page's #graph-page; both
  entries lists are server-rendered <table> elements on the SAME two ids they
  always carried -- one <th scope="col"> header row naming Date / Raw (kg) /
  Trend (kg), then one <tr> of three <td> per ENTRY: the day, the raw weight, the
  smoothed trend weight. The single-string "Fri 24 Jul — 82.2 kg" row grammar
  retired with US-016 (D6/D-35).
* entry-date-picker (US-013/014, 2026-07-24): the date row is a native
  <input type="date" id="entry-date"> INSIDE the entry form and ABOVE the weight
  field. `min` (first entry day - 1 year, D-25/OQ-11) is the only bound the
  server can supply; `value` and `max` come from the phone's own day (A5) and are
  verified at dogfood (client-paint precedent, D-15). ONE hint node (D-24,
  id="entry-hint") carries three mutually exclusive states; "never two hints at
  once" is STRUCTURAL -- there is one node -- not a convention. The inline
  script's map widens to the WHOLE record as {iso_day: kg}
  (`const recordWeights = {...}`, ADR-010/D-21, R-1a): ONE map answers both the
  yesterday anchor and the edit prefill, so the two can never disagree.
* home-trend-glance (US-007, ADR-006): the one neutral glance element (identical
  markup for ↓ / ↑ / → -- information, never judgment):
  `<p id="trend-glance">Trend: 82.3 kg · ↓0.25 kg/week</p>`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, NamedTuple

from domain_types import (
    ColorScheme,
    dark_override_names,
    hex_colors_in,
    scheme_token_maps,
)

# ---------------------------------------------------------------- the one grammar

#: The one new artifact of calm-visual-theme, served by the EXISTING static route.
THEME_ASSET_PATH = "/static/theme.css"
#: The ONE shared graph module both surfaces drive (ADR-008, D-15).
GRAPH_MODULE_PATH = "/static/graph.js"
#: Reaching beyond the tracker's own walls (G-5: zero external requests).
OTHER_ORIGIN_MARKS = ("http://", "https://", 'src="//', 'href="//', "url(//", "@import")
#: The column headings every entries table names (D-38): `kg` once per column.
COLUMN_HEADINGS = ("Date", "Raw (kg)", "Trend (kg)")

SCRIPT_SOURCE = re.compile(r'<script[^>]*\bsrc="([^"]+)"')
DATA_VIEW = re.compile(r'data-view="([^"]*)"')
DATA_SCALE = re.compile(r'data-scale="([^"]*)"')
DATA_LENS = re.compile(r'data-lens="([^"]*)"')
DATA_WINDOW = re.compile(r'data-window="([^"]*)"')

HOME_GRAPH_MOUNT = re.compile(r'<[a-z]+[^>]*id="home-graph"[^>]*>')
RECENT_LIST_BLOCK = re.compile(r'<table id="recent-entries".*?</table>', re.S)
HISTORY_LIST_BLOCK = re.compile(r'<table id="history-entries".*?</table>', re.S)
TABLE_ROW = re.compile(
    r"<tr>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*</tr>", re.S
)
TABLE_HEADER = re.compile(r'<th scope="col"[^>]*>\s*(.*?)\s*</th>', re.S)
TOUCH_AFFORDANCE = re.compile(r"<(a|button|input|form|select|textarea)\b")

GLANCE_LINE = re.compile(r'<p id="trend-glance">([^<]*)</p>')
NEUTRAL_GLANCE_OPENING = '<p id="trend-glance">'

WEIGHT_FIELD = re.compile(r'<input[^>]*id="weight"[^>]*>')
DATE_ROW = re.compile(r'<input[^>]*id="entry-date"[^>]*>')
DATE_ROW_EARLIEST = re.compile(r'min="(\d{4}-\d{2}-\d{2})"')
ENTRY_HINT_NODE = re.compile(r'<[a-z]+[^>]*id="entry-hint"[^>]*>')
RETIRED_ANCHOR_NODE = re.compile(r'id="yesterday-reference"')
RECORD_WEIGHTS_MAP = re.compile(r"const recordWeights = (\{[^;]*\});")
#: Pre-fix render source: the server-rendered anchor paragraph. Kept as fallback
#: so the skew regression fails on the wrong VALUE shown, not on a missing marker.
SERVER_RENDERED_YESTERDAY = re.compile(r"yesterday: (\d+\.\d) kg")

#: Global comfortable-touch promise (DISCUSS: >= 44 px everywhere, door rule promoted).
TOUCH_TARGET_RULE = re.compile(r"min-height:\s*44px")
#: Pressed-beyond-color promise (US-009): the aria-pressed state is styled in its own right.
PRESSED_STATE_RULE = re.compile(r'\[aria-pressed="true"\]')


# ---------------------------------------------------------------- shared pieces


class Row(NamedTuple):
    """One rendered entry row: the three cells, as read off the page or as
    re-derived by the oracle. Comparing rows compares cells, so a drift in any
    single column names itself in the failure message."""

    day: str
    raw: str
    trend: str


@dataclass(frozen=True)
class EntriesTable:
    """One server-rendered entries list: its header row, its entry rows, and the
    first touch affordance found inside it (None = display-only, D9)."""

    headings: tuple[str, ...]
    rows: tuple[Row, ...]
    touch_affordance: str | None


def _table(block: re.Match[str] | None) -> EntriesTable | None:
    if block is None:
        return None
    html = block.group(0)
    touched = TOUCH_AFFORDANCE.search(html)
    return EntriesTable(
        headings=tuple(match.group(1) for match in TABLE_HEADER.finditer(html)),
        rows=tuple(
            Row(*(cell.strip() for cell in match.groups())) for match in TABLE_ROW.finditer(html)
        ),
        touch_affordance=touched.group(1) if touched else None,
    )


def _position(html: str, marker: str) -> int | None:
    at = html.find(marker)
    return None if at < 0 else at


def _first(pattern: re.Pattern[str], text: str) -> str | None:
    found = pattern.search(text)
    return found.group(1) if found else None


@dataclass(frozen=True)
class Page:
    """What every served page has in common: its dress (theme link, origins
    reached, scripts carried, palette) and the lens/scale state it declares."""

    html: str
    is_html: bool
    wears_theme: bool
    other_origin_marks: tuple[str, ...]
    script_sources: tuple[str, ...]
    inline_script_count: int
    hex_colors: tuple[str, ...]
    links_graph_module: bool
    view: str | None
    scale: str | None


def _page_fields(response: Any) -> dict[str, Any]:
    html: str = response.text
    sources = tuple(SCRIPT_SOURCE.findall(html))
    return {
        "html": html,
        "is_html": response.headers.get("content-type", "").startswith("text/html"),
        "wears_theme": THEME_ASSET_PATH in html and "stylesheet" in html,
        "other_origin_marks": tuple(mark for mark in OTHER_ORIGIN_MARKS if mark in html),
        "script_sources": sources,
        "inline_script_count": html.count("<script") - len(sources),
        "hex_colors": hex_colors_in(html),
        "links_graph_module": GRAPH_MODULE_PATH in html,
        "view": _first(DATA_VIEW, html),
        "scale": _first(DATA_SCALE, html),
    }


def read_page(response: Any) -> Page:
    return Page(**_page_fields(response))


# ---------------------------------------------------------------- the door


@dataclass(frozen=True)
class DoorPage(Page):
    """The passphrase door a locked browser visit is met by."""

    offers_passphrase_form: bool
    shows_wrong_passphrase: bool


def read_door(response: Any) -> DoorPage:
    html = response.text
    return DoorPage(
        **_page_fields(response),
        offers_passphrase_form='action="/login"' in html and 'name="passphrase"' in html,
        shows_wrong_passphrase="wrong passphrase" in html.lower(),
    )


# ---------------------------------------------------------------- the entry screen


@dataclass(frozen=True)
class EntryScreen(Page):
    """The morning screen (`GET /`), read once: the form and its focus, the glance
    line, the recent list, the whole-record map, the date row, the hint node and
    the front-page graph mount. Positions are character offsets in the HTML so
    "above"/"below" claims can be asserted without a second search."""

    autofocus_count: int
    decimal_keypad: bool
    form_at: int | None
    weight_field: str | None
    weight_field_at: int | None
    has_tabindex: bool
    glance_line: str | None
    neutral_glance_element: bool
    recent: EntriesTable | None
    record_weights: dict[str, float] | None
    server_rendered_yesterday_kg: float | None
    date_row: str | None
    date_row_at: int | None
    date_row_native: bool
    date_row_earliest: str | None
    hint_node_count: int
    retired_anchor_present: bool
    home_graph_mount: str | None
    home_graph_mount_at: int | None
    mount_view: str | None
    mount_scale: str | None
    lens_controls: frozenset[str]
    window_controls: frozenset[str]


def read_entry_screen(response: Any) -> EntryScreen:
    html: str = response.text
    weight_field = WEIGHT_FIELD.search(html)
    glance = GLANCE_LINE.search(html)
    weights = RECORD_WEIGHTS_MAP.search(html)
    yesterday = SERVER_RENDERED_YESTERDAY.search(html)
    date_row = DATE_ROW.search(html)
    mount = HOME_GRAPH_MOUNT.search(html)
    return EntryScreen(
        **_page_fields(response),
        autofocus_count=html.count("autofocus"),
        decimal_keypad='inputmode="decimal"' in html,
        form_at=_position(html, "<form"),
        weight_field=weight_field.group(0) if weight_field else None,
        weight_field_at=weight_field.start() if weight_field else None,
        has_tabindex="tabindex" in html,
        glance_line=glance.group(1).strip() if glance else None,
        neutral_glance_element=NEUTRAL_GLANCE_OPENING in html,
        recent=_table(RECENT_LIST_BLOCK.search(html)),
        record_weights=dict(json.loads(weights.group(1))) if weights else None,
        server_rendered_yesterday_kg=float(yesterday.group(1)) if yesterday else None,
        date_row=date_row.group(0) if date_row else None,
        date_row_at=date_row.start() if date_row else None,
        date_row_native=bool(date_row) and 'type="date"' in date_row.group(0),
        date_row_earliest=_first(DATE_ROW_EARLIEST, date_row.group(0)) if date_row else None,
        hint_node_count=len(ENTRY_HINT_NODE.findall(html)),
        retired_anchor_present=RETIRED_ANCHOR_NODE.search(html) is not None,
        home_graph_mount=mount.group(0) if mount else None,
        home_graph_mount_at=mount.start() if mount else None,
        mount_view=_first(DATA_VIEW, mount.group(0)) if mount else None,
        mount_scale=_first(DATA_SCALE, mount.group(0)) if mount else None,
        lens_controls=frozenset(DATA_LENS.findall(html)),
        window_controls=frozenset(DATA_WINDOW.findall(html)),
    )


# ---------------------------------------------------------------- the History page


@dataclass(frozen=True)
class HistoryPage(Page):
    """The History page (`GET /graph`), read once: the chart, the complete record
    beneath it, the first-log invite and the way back."""

    record: EntriesTable | None
    record_at: int | None
    chart_at: int | None
    back_link: bool
    invite: bool


def read_history_page(response: Any) -> HistoryPage:
    html: str = response.text
    return HistoryPage(
        **_page_fields(response),
        record=_table(HISTORY_LIST_BLOCK.search(html)),
        record_at=_position(html, 'id="history-entries"'),
        chart_at=_position(html, 'id="chart"'),
        back_link='href="/"' in html,
        invite='id="empty-invite"' in html,
    )


# ---------------------------------------------------------------- the theme


@dataclass(frozen=True)
class ThemeSheet:
    """The calm theme as served: its text, its weight, its two appearances and
    the structural promises it carries."""

    css: str
    byte_size: int
    looks_like_stylesheet: bool
    other_origin_marks: tuple[str, ...]
    appearances: dict[ColorScheme, dict[str, str]]
    dark_overrides: frozenset[str]
    promises_touch_comfort: bool
    styles_pressed_state: bool


def read_theme(response: Any) -> ThemeSheet:
    css: str = response.text
    return ThemeSheet(
        css=css,
        byte_size=len(response.content),
        looks_like_stylesheet="{" in css and "--" in css,
        other_origin_marks=tuple(mark for mark in OTHER_ORIGIN_MARKS if mark in css),
        appearances=scheme_token_maps(css),
        dark_overrides=dark_override_names(css),
        promises_touch_comfort=TOUCH_TARGET_RULE.search(css) is not None,
        styles_pressed_state=PRESSED_STATE_RULE.search(css) is not None,
    )
