"""Typed test-side domain vocabulary (Mandate-12 SSOT + zero duplication).

Domain nouns are defined ONCE in `weight_tracker.core.types` (production SSOT)
and re-exported here; this module adds only test-side typed vocabulary
(phrase-to-reason mapping, scale labels, date parsing for Gherkin surface).
Step methods and composition services consume these types -- never raw strings
where an enum exists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from weight_tracker.core.types import (  # noqa: F401  (re-exports are the point)
    MAX_DEVICE_SKEW_DAYS,
    MAX_WEIGHT_KG,
    MIN_WEIGHT_KG,
    PRECISION_KG,
    Entry,
    Rejected,
    RejectionReason,
    Saved,
    TimeScale,
    TrendPoint,
    ViewMode,
)

TEST_PASSPHRASE = "correct-horse-battery-staple"

#: Business-language rejection phrases (Gherkin surface) -> closed reason set (C6b/C6c).
REASON_PHRASES: dict[str, RejectionReason] = {
    "the value must be between 30.0 and 250.0 kg": RejectionReason.OUT_OF_RANGE,
    "the value is finer than the 0.1 kg scale": RejectionReason.BAD_PRECISION,
    "that is not a weight": RejectionReason.NOT_A_WEIGHT,
    "a weight is required": RejectionReason.MISSING_VALUE,
    "future dates cannot be logged": RejectionReason.FUTURE_DATE,
    "the date is not recognisable": RejectionReason.BAD_DATE,
}

#: Gherkin scale labels -> TimeScale enum.
SCALE_LABELS: dict[str, TimeScale] = {
    "1W": TimeScale.ONE_WEEK,
    "1M": TimeScale.ONE_MONTH,
    "3M": TimeScale.THREE_MONTHS,
    "6M": TimeScale.SIX_MONTHS,
    "1Y": TimeScale.ONE_YEAR,
    "All": TimeScale.ALL,
    "ALL": TimeScale.ALL,
}

#: Window length in days per scale (pinned at DISTILL; window = [today - (N-1), today]).
SCALE_WINDOW_DAYS: dict[TimeScale, int] = {
    TimeScale.ONE_WEEK: 7,
    TimeScale.ONE_MONTH: 30,
    TimeScale.THREE_MONTHS: 91,
    TimeScale.SIX_MONTHS: 182,
    TimeScale.ONE_YEAR: 365,
}

VIEW_WORDS: dict[str, ViewMode] = {
    "Trend": ViewMode.TREND,
    "trend": ViewMode.TREND,
    "Raw": ViewMode.RAW,
    "raw": ViewMode.RAW,
}


class TrendDirection(Enum):
    """Recent movement of the record, as the Gherkin surface speaks it (US-007)."""

    FALLING = "falling"
    RISING = "rising"
    STEADY = "steady"


class RateDisposition(Enum):
    """Whether the weekly rate is shown or honestly held back (ADR-006 span rule)."""

    SHOWN = "shown"
    HELD_BACK = "held back"


_WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def parse_day(text: str) -> date:
    """Parse a Gherkin day like 'Tuesday 21 July 2026', '21 July 2026' or ISO."""
    cleaned = text.strip()
    for weekday in _WEEKDAYS:
        cleaned = cleaned.removeprefix(weekday).strip()
    for fmt in ("%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unparseable Gherkin day: {text!r}")


def parse_scale(label: str) -> TimeScale:
    return SCALE_LABELS[label]


def parse_view(word: str) -> ViewMode:
    return VIEW_WORDS[word]


def parse_direction(word: str) -> TrendDirection:
    return TrendDirection(word)


def parse_rate_disposition(phrase: str) -> RateDisposition:
    return RateDisposition(phrase)


def parse_reason(phrase: str) -> RejectionReason:
    return REASON_PHRASES[phrase]


def window_start(scale: TimeScale, today: date) -> date | None:
    """First day of the window for a scale, or None for ALL (unbounded)."""
    if scale is TimeScale.ALL:
        return None
    return today - timedelta(days=SCALE_WINDOW_DAYS[scale] - 1)


# --------------------------------------------------------------------------
# calm-visual-theme (US-008 / US-009) typed vocabulary + pure contrast checker
# --------------------------------------------------------------------------


class ColorScheme(Enum):
    """The two first-class appearances (DISCUSS D7: follow the system scheme)."""

    DAYLIGHT = "daylight"
    DIM_LIGHT = "dim light"


class ContrastClass(Enum):
    """WCAG AA class of a color pairing: readable text vs distinguishable non-text."""

    TEXT = "text"
    NON_TEXT = "non-text"


#: Required minimum contrast ratio per class (DISCUSS requirement, G-4).
MIN_CONTRAST_RATIO: dict[ContrastClass, float] = {
    ContrastClass.TEXT: 4.5,
    ContrastClass.NON_TEXT: 3.0,
}


@dataclass(frozen=True)
class ColorPairing:
    """One ink-on-surface pairing from the DESIGN token table (the G-4 contract).

    `ink` and `surface` name the custom properties carrying the two colors; the
    checker asserts the RATIO between whatever hex values the served theme
    declares -- never pinned hexes (Q6: one-hex-step nudges stay green)."""

    label: str
    ink: str
    surface: str
    contrast_class: ContrastClass


#: The full G-4 contract: every pairing of the DESIGN § Design Tokens table,
#: checked in BOTH schemes. The AT checker is the authoritative verifier (Q1/Q6).
CONTRAST_CONTRACT: tuple[ColorPairing, ...] = (
    ColorPairing("body text on the page", "--text", "--bg", ContrastClass.TEXT),
    ColorPairing("muted text on the page", "--text-muted", "--bg", ContrastClass.TEXT),
    ColorPairing("links on the page", "--link", "--bg", ContrastClass.TEXT),
    ColorPairing("button label on its own fill", "--btn-text", "--btn-bg", ContrastClass.TEXT),
    ColorPairing("chart axis labels", "--chart-axis", "--bg", ContrastClass.TEXT),
    ColorPairing("control borders", "--border", "--bg", ContrastClass.NON_TEXT),
    ColorPairing("chart gridlines", "--chart-grid", "--bg", ContrastClass.NON_TEXT),
    ColorPairing("raw series stroke", "--chart-raw", "--bg", ContrastClass.NON_TEXT),
    ColorPairing("trend series stroke", "--chart-trend", "--bg", ContrastClass.NON_TEXT),
)


class Screen(Enum):
    """The three user-facing screens dressed by the theme (DISCUSS D8)."""

    ENTRY = "entry screen"
    DOOR = "door"
    GRAPH = "graph page"


def parse_screen(phrase: str) -> Screen:
    return Screen(phrase)


# ---- WCAG relative-luminance arithmetic (pure; Q1 resolution) --------------

_HEX_COLOR = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_CUSTOM_PROPERTY = re.compile(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b")
_DARK_BLOCK_OPEN = re.compile(r"@media[^{]*prefers-color-scheme:\s*dark[^{]*\{")


def expand_hex(color: str) -> str:
    """Normalise #abc to #aabbcc; pass 6-digit hexes through."""
    raw = color.lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return f"#{raw.lower()}"


def _linear_channel(byte_value: int) -> float:
    scaled = byte_value / 255
    return scaled / 12.92 if scaled <= 0.04045 else ((scaled + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """WCAG 2.x relative luminance of an sRGB hex color."""
    raw = expand_hex(color).lstrip("#")
    red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return (
        0.2126 * _linear_channel(red)
        + 0.7152 * _linear_channel(green)
        + 0.0722 * _linear_channel(blue)
    )


def contrast_ratio(ink: str, surface: str) -> float:
    """WCAG contrast ratio (>= 1.0) between two hex colors."""
    lighter, darker = sorted((relative_luminance(ink), relative_luminance(surface)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _dark_block(css: str) -> str:
    """The body of the dim-light override block, or '' when none is declared."""
    opened = _DARK_BLOCK_OPEN.search(css)
    if opened is None:
        return ""
    depth, start = 1, opened.end()
    for position in range(start, len(css)):
        depth += {"{": 1, "}": -1}.get(css[position], 0)
        if depth == 0:
            return css[start:position]
    return css[start:]


def scheme_token_maps(css: str) -> dict[ColorScheme, dict[str, str]]:
    """Custom-property -> hex maps per scheme, parsed from the served stylesheet.

    Daylight = declarations outside the dark media block; dim light = daylight
    overridden by the declarations inside it (the cascade, modelled purely)."""
    dark_body = _dark_block(css)
    light_body = css.replace(dark_body, "") if dark_body else css
    daylight = {name: expand_hex(value) for name, value in _CUSTOM_PROPERTY.findall(light_body)}
    overrides = {name: expand_hex(value) for name, value in _CUSTOM_PROPERTY.findall(dark_body)}
    return {ColorScheme.DAYLIGHT: daylight, ColorScheme.DIM_LIGHT: {**daylight, **overrides}}


def dark_override_names(css: str) -> frozenset[str]:
    """The custom properties the dim-light block declares in its own right."""
    return frozenset(name for name, _ in _CUSTOM_PROPERTY.findall(_dark_block(css)))


def hex_colors_in(document: str) -> tuple[str, ...]:
    """Every hard-coded hex color literal in a document (single-palette guard)."""
    return tuple(_HEX_COLOR.findall(document))


# --------------------------------------------------------------------------
# entry-date-picker (US-013 / US-014) typed vocabulary
# --------------------------------------------------------------------------


class DayClaim(Enum):
    """What a save says about the phone's OWN calendar day (ADR-011, D-22).

    The claim is additive and optional: present and honest for a phone-made
    save, absent for an API/curl client, garbled when a lying or broken client
    sends nonsense. Absent or garbled falls back to the server's UTC day and
    must NEVER block or reject a save -- a telemetry concern may not cost an
    entry."""

    DEVICE_DAY = "the phone's own day"
    ABSENT = "with no word about the phone's day"
    GARBLED = "with a garbled word for the phone's day"


#: Business-language claim phrases (Gherkin surface) -> the typed claim shape.
CLAIM_PHRASES: dict[str, DayClaim] = {
    "with no word about the phone's day": DayClaim.ABSENT,
    "with a garbled word for the phone's day": DayClaim.GARBLED,
    "from his phone": DayClaim.DEVICE_DAY,
}

#: The nonsense a garbled claim carries (the `?today=` garbled-claim precedent).
GARBLED_DAY_CLAIM = "someday-soon"


def parse_claim(phrase: str) -> DayClaim:
    return CLAIM_PHRASES[phrase]


def day_label(day: date) -> str:
    """The ONE day grammar every surface speaks (D-24): 'Thu 23 Jul'.

    Identical to the day half of the production row grammar
    (`routes.entry_row_text`) and of `Saved.confirmation` -- the hint line
    reuses it rather than forking a second calendar wording. Asserted against
    the server's own rendered rows, never trusted on its own."""
    return f"{day:%a} {day.day} {day:%b}"
