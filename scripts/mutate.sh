#!/usr/bin/env bash
# Per-feature mutation gate (CLAUDE.md): cosmic-ray, scoped by its git filter to the
# lines that differ from BASE, run against the killer tests you name. Kill rate gate:
# >= 80 % effective, where "effective" excludes equivalent mutants (see the report).
#
#   scripts/mutate.sh <base-ref> [pytest targets...]
#
# Default targets: the whole suite. Narrow to the feature's property files and
# milestone scenarios to make the run shorter; every property pins its own
# max_examples, so the target list is the only speed lever.
#
# cosmic-ray mutates src/ IN PLACE and restores it after each job: src/ must be
# committed clean before a run, and nothing may edit src/ while it runs.
set -euo pipefail

BASE="${1:?usage: scripts/mutate.sh <base-ref> [pytest targets...]}"
shift || true
TARGETS="${*:-tests}"
CR="cosmic-ray==8.4.3"

if [ -n "$(git status --porcelain src/)" ]; then
  echo "src/ has uncommitted changes; commit first (cosmic-ray mutates files in place)" >&2
  exit 1
fi

WORK="${MUTATION_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/mutation.XXXXXX")}"
CONF="$WORK/cosmic-ray.toml"
DB="$WORK/session.sqlite"

cat > "$CONF" <<TOML
[cosmic-ray]
module-path = "src/weight_tracker"
timeout = 180.0
excluded-modules = []
test-command = "uv run pytest -x -q -p no:cacheprovider $TARGETS"

[cosmic-ray.distributor]
name = "local"

[cosmic-ray.filters.git-filter]
branch = "$BASE"
TOML

echo "session: $DB"
uvx --from "$CR" cosmic-ray init "$CONF" "$DB"
# The git filter is a separate console script and reads the config via --config.
uvx --from "$CR" cr-filter-git --config "$CONF" "$DB"
uvx --from "$CR" cosmic-ray baseline "$CONF"
uvx --from "$CR" cosmic-ray exec "$CONF" "$DB"

REPORT="$(uvx --from "$CR" cr-report "$DB")"
EXECUTED=$(printf '%s\n' "$REPORT" | grep -c "WorkerOutcome.NORMAL" || true)
KILLED=$(printf '%s\n' "$REPORT" | grep -c "TestOutcome.KILLED" || true)
SURVIVED=$(printf '%s\n' "$REPORT" | grep -c "TestOutcome.SURVIVED" || true)
# `|` inside an annotation is never evaluated under `from __future__ import
# annotations`, so every ReplaceBinaryOperator_BitOr_* mutant there is equivalent.
# Confirm by eye that each BitOr survivor sits in an annotation before excluding it.
BITOR=$(printf '%s\n' "$REPORT" | grep -B1 "TestOutcome.SURVIVED" | grep -c "BitOr" || true)
EFFECTIVE_DENOM=$((EXECUTED - BITOR))

echo
echo "executed: $EXECUTED  killed: $KILLED  surviving: $SURVIVED  (of which BitOr-in-annotation: $BITOR)"
if [ "$EFFECTIVE_DENOM" -gt 0 ]; then
  echo "effective kill rate: $KILLED / $EFFECTIVE_DENOM = $((100 * KILLED / EFFECTIVE_DENOM)) %  (gate >= 80 %)"
fi
echo
echo "survivors by file and operator (occurrence-collapsed):"
printf '%s\n' "$REPORT" | grep -B1 "TestOutcome.SURVIVED" | grep '^src' | awk '{print $1, $2}' \
  | sed -E 's/_(Add|Sub|Mul|Div|FloorDiv|Mod|Pow|RShift|LShift|BitAnd|BitXor)$/_*/' | sort | uniq -c
echo
echo "full report: uvx --from $CR cr-report $DB"
