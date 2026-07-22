"""Acceptance-suite conftest: fixtures + tag handling.

- Gherkin tags are normalized to valid pytest markers (hyphens/colons -> underscores).
- @pending scenarios (authored by DISTILL, awaiting their DELIVER step) are skipped
  by default -- one-scenario-at-a-time discipline. Setting RED_GATE_ALL=1 runs the
  full suite for the fail-for-the-right-reason gate classification.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from composition import TrackerComposition
from fake_clock import FakeClock


def pytest_bdd_apply_tag(tag: str, function):
    normalized = tag.replace("-", "_").replace(":", "_").replace(".", "_").lower()
    return getattr(pytest.mark, normalized)(function)


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RED_GATE_ALL"):
        return
    for item in items:
        if item.get_closest_marker("pending"):
            item.add_marker(
                pytest.mark.skip(
                    reason="pending -- DISTILL scaffold, enabled one-at-a-time in DELIVER"
                )
            )


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def composition(tmp_path, fake_clock):
    home = tmp_path / "record"
    home.mkdir()
    comp = TrackerComposition(db_path=home / "weight.db", fake_clock=fake_clock)
    yield comp
    os.chmod(home, 0o700)  # restore if a scenario made the record's home unwritable


@pytest.fixture
def ctx() -> SimpleNamespace:
    return SimpleNamespace()
