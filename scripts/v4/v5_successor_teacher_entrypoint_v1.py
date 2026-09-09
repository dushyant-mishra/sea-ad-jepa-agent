#!/usr/bin/env python3
"""The teacher training entrypoint, with the gradient gate in the real path.

`stage81a3_prod41k_teacher_t1.py` is the script that actually ran T1. Its loop
calls `phase_e.run_update` directly, and accepts the update when
`step_succeeded`, `online_moved` and `ema_equation["equal"]` all hold -- every
one of which held for 205 consecutive updates while all 48 protected attention
tensors were dead. Adopting the gate anywhere short of this call site leaves the
path that produced the failure exactly as it was.

The historical file is not edited. Its digest is bound in the preservation
manifests and in the T1 evaluation freeze, and it is the only faithful record of
what was run, so changing it would break that provenance and destroy the ability
to reproduce the failure. Instead the successor entrypoint is derived from its
source by textual substitution, the same technique the corrective variants use
on `run_update`: one declared change, everything else byte-identical, and a diff
that can be read.

The single declared change:

    result = phase_e.run_update(     ->     result = _v5_successor_step(phase_e)(

`_v5_successor_step` is injected into the derived module's namespace. It builds
the gated, corrected step through `v5_successor_training_step_v1`, which
verifies the built source before returning it and offers no ungated path, then
memoises it so the 205-update loop pays for the verification once. Passing
`phase_e` at the call site rather than binding it up front matters: the module
loads `phase_e` during its own execution, so there is nothing to bind until the
loop is already running.

What this changes about training. The step is the `successor` variant, so the
backward runs outside fp16 autocast and the gate rejects, before the optimizer
sees them, any update where a protected tensor's gradient is missing, nonfinite
or exactly zero. A run that would historically have completed silently now stops
at the first dead update. That is the intended behaviour and the reason the
entrypoint exists.

This module starts no training by itself beyond what the historical script does
when invoked; it takes the same arguments and forwards them.
"""

from __future__ import annotations

import argparse
import difflib
import sys
import types
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_RELATIVE = Path("scripts") / "v4" / "stage81a3_prod41k_teacher_t1.py"

# Kept for callers and tests that only want to inspect the derivation; a run
# against a different root passes it explicitly.
HISTORICAL = ROOT / HISTORICAL_RELATIVE

REQUIRED_FOR_EXECUTION = (
    Path("exports") / "contextual_biology_v6r5a_20260822",
    Path("exports") / "static_context_decomposition_v4_20260821",
    Path("src") / "sea_ad_jepa" / "v4",
)


def resolve_repo_root(repo_root: Any = None) -> Path:
    """The root the derived module will run against.

    Defaults to this entrypoint's own repository, which is right wherever the
    gate stack sits alongside the data. It is refused early if it does not hold
    the historical script, because the alternative is a failure much later and
    much harder to read.
    """
    root = Path(repo_root).resolve() if repo_root else ROOT
    if not (root / HISTORICAL_RELATIVE).is_file():
        _fail("no historical teacher script under %s" % root)
    return root


def missing_execution_inputs(root: Path) -> list[str]:
    """What the teacher script needs from its root and would not find here.

    Reported rather than raised: the derivation and its verification are
    perfectly meaningful in a checkout that cannot run training, and refusing to
    inspect them there would be needless.
    """
    return [str(item) for item in REQUIRED_FOR_EXECUTION
            if not (root / item).exists()]

ORIGINAL_CALL = "result = phase_e.run_update("
SUCCESSOR_CALL = "result = _v5_successor_step(phase_e)("

STOP_DERIVATION = "STOP_V5_SUCCESSOR_TEACHER_ENTRYPOINT_DERIVATION_REFUSED"


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP_DERIVATION, message))


def _memoised_step() -> Callable[[Any], Callable[..., Any]]:
    """Build the verified gated step once, on first use."""
    cache: dict[str, Callable[..., Any]] = {}

    def get(phase_e: Any) -> Callable[..., Any]:
        if "step" not in cache:
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            from scripts.v4.v5_successor_training_step_v1 import (
                successor_step_report, successor_training_step)
            step = successor_training_step(phase_e)
            report = successor_step_report(phase_e)
            print("[v5] gated successor step verified: gate at lines %s, "
                  "optimizer steps at %s, ordering %s"
                  % (report["structure"]["gate_lines"],
                     report["structure"]["optimizer_step_lines"],
                     report["ordering"]), flush=True)
            cache["step"] = step
        return cache["step"]

    return get


def derived_source(repo_root: Any = None) -> str:
    """The historical script with exactly one call site redirected."""
    root = resolve_repo_root(repo_root)
    text = (root / HISTORICAL_RELATIVE).read_text(encoding="utf-8")
    occurrences = text.count(ORIGINAL_CALL)
    if occurrences != 1:
        _fail("expected exactly one `%s` call site, found %d"
              % (ORIGINAL_CALL, occurrences))
    return text.replace(ORIGINAL_CALL, SUCCESSOR_CALL, 1)


def derivation_diff(repo_root: Any = None) -> str:
    root = resolve_repo_root(repo_root)
    historical = (root / HISTORICAL_RELATIVE).read_text(
        encoding="utf-8").splitlines()
    derived = derived_source(root).splitlines()
    return "\n".join(difflib.unified_diff(
        historical, derived, "historical_teacher_t1", "v5_successor_teacher",
        lineterm="", n=2))


def verify_derivation(repo_root: Any = None) -> dict[str, Any]:
    """One line changed, and it is the update call. Nothing else moved.

    Checked on the derived text rather than asserted, because a substitution
    that quietly matched somewhere else would put the gate in a path nobody
    inspected while still producing a module that runs.
    """
    root = resolve_repo_root(repo_root)
    diff = derivation_diff(root)
    added = [line[1:] for line in diff.splitlines()
             if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in diff.splitlines()
               if line.startswith("-") and not line.startswith("---")]
    if len(added) != 1 or len(removed) != 1:
        _fail("expected one changed line, got +%d/-%d" % (len(added), len(removed)))
    if ORIGINAL_CALL not in removed[0] or SUCCESSOR_CALL not in added[0]:
        _fail("the changed line is not the update call: -%r +%r"
              % (removed[0], added[0]))

    derived = derived_source(root)
    if ORIGINAL_CALL in derived:
        _fail("an ungated `phase_e.run_update(` call survives the substitution")
    return {"repo_root": str(root), "added": added, "removed": removed,
            "ungated_call_sites_remaining": 0,
            "missing_execution_inputs": missing_execution_inputs(root)}


def build_module(repo_root: Any = None,
                 name: str = "v5_successor_teacher") -> types.ModuleType:
    """Execute the derived script as a module without running its main().

    `__file__` is set to the historical script under the chosen root so the
    script's own `parents[2]` arithmetic resolves to that root. Without this the
    module would read its loader and exports from wherever the gate stack
    happens to live.
    """
    root = resolve_repo_root(repo_root)
    verify_derivation(root)
    missing = missing_execution_inputs(root)
    if missing:
        _fail("root %s cannot run training; missing %s" % (root, missing))
    module = types.ModuleType(name)
    module.__file__ = str(root / HISTORICAL_RELATIVE)
    module.__dict__["__name__"] = name
    module.__dict__["_v5_successor_step"] = _memoised_step()
    sys.modules[name] = module
    exec(compile(derived_source(root), "<v5_successor_teacher>", "exec"),
         module.__dict__)
    return module


def main(argv: Any = None) -> None:
    parser = argparse.ArgumentParser(
        description="Teacher training with the mandatory gradient gate.",
        add_help=False)
    parser.add_argument("--repo-root", default=None,
                        help="repository root holding the loader, exports and "
                             "data; defaults to this entrypoint's own root")
    known, rest = parser.parse_known_args(
        sys.argv[1:] if argv is None else argv)
    # The remainder belongs to the historical script's own parser.
    sys.argv = [sys.argv[0]] + rest
    module = build_module(known.repo_root)
    module.main()


if __name__ == "__main__":
    main()
