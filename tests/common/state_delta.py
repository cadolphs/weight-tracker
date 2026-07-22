"""Project-local state-delta port (Python).

Bootstrapped by DISTILL per the nw-distill polyglot contract.

Universe assertion contract: every state-mutating test at layers 1-3 calls
`assert_state_delta(before, after, universe, expected)`. `universe` declares the
port-exposed observable names the test promises to track; `expected` maps a subset
of them to predicates. Any universe slot NOT in `expected` must be identical
between before and after -- fail-closed.

Predicate library (full eight per the polyglot contract): set_to, unchanged,
appended_with, prepended_with, containing, normalized_to, idempotent_after,
legacy_healed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

Predicate = Callable[[Any, Any], tuple[bool, str]]


def set_to(value: Any) -> Predicate:
    def check(before: Any, after: Any) -> tuple[bool, str]:
        return (after == value, f"expected slot set to {value!r}, got {after!r}")

    return check


def unchanged() -> Predicate:
    def check(before: Any, after: Any) -> tuple[bool, str]:
        return (before == after, f"expected unchanged, but {before!r} -> {after!r}")

    return check


def appended_with(item: Any) -> Predicate:
    def check(before: Any, after: Any) -> tuple[bool, str]:
        ok = list(after)[: len(list(before))] == list(before) and list(after)[
            len(list(before)) :
        ] == [item]
        return (ok, f"expected {before!r} appended with {item!r}, got {after!r}")

    return check


def prepended_with(item: Any) -> Predicate:
    def check(before: Any, after: Any) -> tuple[bool, str]:
        ok = list(after)[:1] == [item] and list(after)[1:] == list(before)
        return (ok, f"expected {before!r} prepended with {item!r}, got {after!r}")

    return check


def containing(item: Any) -> Predicate:
    def check(before: Any, after: Any) -> tuple[bool, str]:
        return (item in after, f"expected {after!r} to contain {item!r}")

    return check


def normalized_to(value: Any) -> Predicate:
    """Slot may have held any legacy shape before; after must equal the normalized value."""

    def check(before: Any, after: Any) -> tuple[bool, str]:
        return (after == value, f"expected slot normalized to {value!r}, got {after!r}")

    return check


def idempotent_after(first_result: Any) -> Predicate:
    """Second application must land on the same value as the first application."""

    def check(before: Any, after: Any) -> tuple[bool, str]:
        return (after == first_result, f"expected idempotent value {first_result!r}, got {after!r}")

    return check


def legacy_healed(healthy_value: Any) -> Predicate:
    """Slot held a broken/legacy value before; after must equal the healed value."""

    def check(before: Any, after: Any) -> tuple[bool, str]:
        return (
            after == healthy_value,
            f"expected legacy slot healed to {healthy_value!r}, got {after!r}",
        )

    return check


def assert_state_delta(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    universe: set[str],
    expected: Mapping[str, Predicate],
    *,
    strict: bool = True,
) -> None:
    """Assert the observable state delta over `universe` matches `expected` exactly.

    - every universe slot must be present in both snapshots
    - every expected slot's predicate must pass
    - every universe slot WITHOUT an expected entry must be unchanged (fail-closed)
    - expected keys outside the universe are an error (test-authoring bug)
    """
    stray = set(expected) - universe
    assert not stray, f"expected keys outside declared universe: {sorted(stray)}"

    missing = [s for s in universe if s not in before or s not in after]
    assert not missing, f"universe slots missing from snapshots: {sorted(missing)}"

    failures: list[str] = []
    for slot in sorted(universe):
        if slot in expected:
            ok, msg = expected[slot](before[slot], after[slot])
            if not ok:
                failures.append(f"[{slot}] {msg}")
        elif strict and before[slot] != after[slot]:
            failures.append(
                f"[{slot}] mutated unexpectedly (no expected entry): "
                f"{before[slot]!r} -> {after[slot]!r}"
            )
    assert not failures, "state-delta violations:\n" + "\n".join(failures)
