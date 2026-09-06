#!/usr/bin/env python3
"""Detect `.backward()` executed inside an ENABLED autocast region.

The C2 causal condition. Grep cannot answer this: a file can contain both an
autocast block and a backward call without the backward being inside it, and a
backward inside a nested `autocast(enabled=False)` is safe. This walks the AST.

Reports per file, per backward call:
  INSIDE_ENABLED_AUTOCAST  - inherits the established C2 defect condition
  INSIDE_DISABLED_AUTOCAST - explicitly shielded
  OUTSIDE_AUTOCAST         - unaffected
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


def _is_autocast(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    parts = []
    func = node.func
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    return "autocast" in parts


def _enabled_state(node: ast.Call) -> str:
    """Return 'enabled', 'disabled', or 'dynamic' for an autocast call."""
    for keyword in node.keywords:
        if keyword.arg == "enabled":
            value = keyword.value
            if isinstance(value, ast.Constant):
                return "enabled" if value.value else "disabled"
            return "dynamic"
    return "enabled"  # autocast defaults to enabled


def _is_backward(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "backward"
    )


def scan_file(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return [{"line": 0, "verdict": "UNPARSEABLE", "autocast_stack": []}]

    results: list[dict] = []

    def walk(node: ast.AST, stack: list[str]) -> None:
        if isinstance(node, (ast.With, ast.AsyncWith)):
            states = [
                _enabled_state(item.context_expr)
                for item in node.items
                if _is_autocast(item.context_expr)
            ]
            inner = stack + states
            for child in node.body:
                walk(child, inner)
            for item in node.items:
                for child in ast.iter_child_nodes(item.context_expr):
                    walk(child, stack)
            return
        if _is_backward(node):
            # The innermost autocast state governs.
            if not stack:
                verdict = "OUTSIDE_AUTOCAST"
            elif stack[-1] == "disabled":
                verdict = "INSIDE_DISABLED_AUTOCAST"
            elif stack[-1] == "dynamic":
                verdict = "INSIDE_DYNAMIC_AUTOCAST"
            else:
                verdict = "INSIDE_ENABLED_AUTOCAST"
            results.append(
                {"line": getattr(node, "lineno", 0), "verdict": verdict,
                 "autocast_stack": list(stack)}
            )
        for child in ast.iter_child_nodes(node):
            walk(child, stack)

    walk(tree, [])
    return results


def main() -> int:
    root = Path(sys.argv[1])
    targets = sorted(
        p for p in root.rglob("*.py")
        if ".git" not in p.parts and "node_modules" not in p.parts
    )
    affected, shielded, clean, unparseable = [], [], [], []
    for path in targets:
        for hit in scan_file(path):
            relative = path.relative_to(root).as_posix()
            record = {"file": relative, **hit}
            if hit["verdict"] == "INSIDE_ENABLED_AUTOCAST":
                affected.append(record)
            elif hit["verdict"] == "INSIDE_DYNAMIC_AUTOCAST":
                # `enabled=<expression>` is the defect condition whenever that
                # expression is true at runtime. run_update writes
                # `enabled=device.type == "cuda"`, which is true on every GPU run.
                affected.append(record)
            elif hit["verdict"] == "INSIDE_DISABLED_AUTOCAST":
                shielded.append(record)
            elif hit["verdict"] == "UNPARSEABLE":
                unparseable.append(record)
            else:
                clean.append(record)

    by_file: dict[str, int] = {}
    for record in affected:
        by_file[record["file"]] = by_file.get(record["file"], 0) + 1

    print("scanned python files: %d" % len(targets))
    print("backward calls inside an ENABLED or RUNTIME-ENABLED autocast: %d across %d files"
          % (len(affected), len(by_file)))
    print("backward calls inside an explicitly disabled autocast: %d" % len(shielded))
    print("backward calls outside any autocast: %d" % len(clean))
    print("unparseable files: %d" % len(unparseable))
    print("\naffected files:")
    for name in sorted(by_file):
        print("  %3d  %s" % (by_file[name], name))
    Path("BACKWARD_IN_AUTOCAST_SCAN.json").write_text(
        json.dumps({"root": str(root), "scanned": len(targets),
                    "affected": affected, "shielded": shielded,
                    "unparseable": unparseable}, indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
