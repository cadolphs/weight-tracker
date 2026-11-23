# Coding standards

Read during `/code-review`. Judgement calls only: anything mechanical is a gate (ruff, mypy strict, import-linter, vulture, the probe-presence AST check) and lives in `.pre-commit-config.yaml`, not here.

## An oracle never calls the rule under test

A test's expected value comes from a source the code under test cannot reach: a known-good literal, a worked example, or a core function for a *different* rule. An oracle that calls the function under test is **tautological**: it passes by construction and keeps mutants alive. (The `/trend` window oracle called the production windowing function and hid four boundary mutants across two features.) Importing the core for *other* shipped rules is the right move; re-implementing a shipped rule test-side with its own constants is duplication, and belongs only while that rule is still red.

## The core returns numbers; the shell phrases them

Display text, precisions and wire shapes live in `web/views.py`; core functions return frozen values. `core/glance.py` states the rule. `Saved.confirmation` in `core/types.py` is the known exception: move it, never copy the pattern.

## One picture per request

A handler reads `all_entries()` once and derives everything through `picture_of` (ADR-014). A second smoothing, a second projection path, or a handler reaching for `trend_series` directly is a defect, even when the output matches.

## A seam needs two adapters

A port, an injected callable or a `build_app` override earns its place only when production and a test each pass a different adapter through it. One adapter is indirection: inline it. A test that monkeypatches module attributes to reach behind a seam is the sign the seam is in the wrong place (ADR-014's `picture_of` door is the precedent for fixing it).
