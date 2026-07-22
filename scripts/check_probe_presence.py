"""Pre-commit AST gate: every driven-adapter class in the shell defines `probe()`.

Layer 2 of the brief.md dependency-rule enforcement: import-linter proves the
core imports nothing outward but cannot assert method presence; this hook proves
the composition root's wire -> probe -> serve contract is satisfiable for every
adapter class in `src/weight_tracker/shell/`.

A top-level class that is deliberately not a driven adapter may opt out with a
`# probe-exempt` marker on its `class` line.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SHELL_DIR = Path("src/weight_tracker/shell")
EXEMPT_MARKER = "# probe-exempt"


def classes_missing_probe(source: str) -> list[str]:
    """Names of top-level classes in `source` lacking a `probe` method (pure)."""
    lines = source.splitlines()
    return [
        node.name
        for node in ast.parse(source).body
        if isinstance(node, ast.ClassDef)
        and not _defines_probe(node)
        and EXEMPT_MARKER not in lines[node.lineno - 1]
    ]


def _defines_probe(class_def: ast.ClassDef) -> bool:
    return any(
        isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef) and member.name == "probe"
        for member in class_def.body
    )


def main() -> int:
    violations = [
        f"{module_path}: class {class_name} has no probe() method"
        for module_path in sorted(SHELL_DIR.glob("*.py"))
        for class_name in classes_missing_probe(module_path.read_text())
    ]
    for violation in violations:
        print(violation, file=sys.stderr)
    if violations:
        print(
            "Every driven adapter must define probe() (brief.md wire->probe->serve). "
            f"Non-adapter classes may carry a `{EXEMPT_MARKER}` marker on the class line.",
            file=sys.stderr,
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
