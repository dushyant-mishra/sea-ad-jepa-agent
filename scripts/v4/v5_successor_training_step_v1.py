#!/usr/bin/env python3
"""The one supported way to obtain a successor (V5) training step.

The gradient gate exists, is tested, and has now been proven at the exact
historical 128x8 geometry. None of that protects a training run that simply does
not call it. `phase_e.run_update` is still the ungated historical function, and
anything importing it directly gets the path that ran 205 updates with all 48
protected attention tensors dead.

So the adoption is this module: a successor training path asks here for its step
function and receives one that cannot be ungated. There is deliberately no
parameter to disable the gate and no ungated return path.

Why a derived function rather than an edited `run_update`. The step is produced
by textual substitution on `inspect.getsource` of the canonical function, so
every line except the declared changes is byte-identical to the historical
implementation. Retyping the update loop to add two lines would put a
transcription risk in the middle of the exact code whose behaviour is under
study, and the whole causal result rests on that code being unchanged.

Why the structural check runs here and not only in the tests. The suite already
proves the successor source is gated, unconditionally, after the unscale and
before every optimizer step. But a test proves it on the machine that ran the
test. Training launched from a different checkout, a stale copy of `phase_e`, or
a future edit to the canonical function is not covered by that. Verifying at
build time means the property is established for the run that is about to
happen, and a run whose step cannot be verified does not start.

The two declared differences from the historical function:

    scaler.scale(scaled_loss).backward()   ->   wrapped in autocast(enabled=False)
    after scaler.unscale_(optimizer)       ->   enforce_registry(online); enforce(online)

which places the gate exactly at `unscale -> gate -> optimizer step -> Adam
moments -> EMA`.
"""

from __future__ import annotations

import ast
from typing import Any, Callable

from scripts.v4.c2_corrective_run_update_v3 import build_variant, variant_diff

STOP_UNVERIFIED = "STOP_V5_SUCCESSOR_STEP_FAILED_STRUCTURAL_VERIFICATION"

# The successor differs from the canonical function by exactly this much: two
# gate calls, one autocast-disable line, and the backward re-indented beneath
# it, against one removed backward. The rename is excluded as cosmetic.
EXPECTED_ADDED_LINES = 4
EXPECTED_REMOVED_LINES = 1


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP_UNVERIFIED, message))


def verify_successor_source(source: str) -> dict[str, Any]:
    """Establish that this source cannot reach an optimizer step ungated.

    Checked on the built source rather than on a description of it, because the
    question is what the function about to run actually does.
    """
    lines = source.splitlines()
    gate = [i for i, line in enumerate(lines) if "_mandatory_gate.enforce" in line]
    registry = [i for i, line in enumerate(lines)
                if "_mandatory_gate.enforce_registry" in line]
    unscale = [i for i, line in enumerate(lines) if "scaler.unscale_(" in line]
    steps = [i for i, line in enumerate(lines)
             if "scaler.step(" in line or "optimizer.step(" in line]

    if len(gate) != 2 or len(registry) != 1:
        _fail("expected one registry call and one tensor gate, found %d gate "
              "lines and %d registry lines" % (len(gate), len(registry)))
    if not unscale:
        _fail("no unscale call: the gate would read scaled gradients")
    if not steps:
        _fail("no optimizer step found; this is not a training step")
    if max(unscale) >= min(gate):
        _fail("the gate does not follow the unscale")
    for step in steps:
        if max(gate) >= step:
            _fail("an optimizer step at line %d precedes the gate" % (step + 1))

    # The adjudication holds only while the gradients it examined are the ones
    # that get applied. Anything writing `.grad` between the gate and the last
    # step would let a dead gradient reach the optimizer behind a passing gate
    # record -- `zero_grad` most directly of all. Neither occurs in the
    # canonical function; the check is what keeps a future edit from adding one.
    invalidating = [
        i for i, line in enumerate(lines)
        if max(gate) < i <= max(steps)
        and (".backward(" in line or "zero_grad(" in line)
    ]
    if invalidating:
        _fail("line %d rewrites gradients after the gate and before an "
              "optimizer step, which invalidates the adjudication"
              % (invalidating[0] + 1))

    # A gate inside a conditional is a gate that some branch skips.
    tree = ast.parse(source)
    function = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef))
    unconditional = {node.lineno for node in function.body
                     if isinstance(node, ast.Expr)
                     and isinstance(node.value, ast.Call)}
    for index in gate:
        if index + 1 not in unconditional:
            _fail("the gate call on line %d is not unconditional at function "
                  "body depth" % (index + 1))

    return {
        "gate_lines": [i + 1 for i in gate],
        "unscale_line": max(unscale) + 1,
        "optimizer_step_lines": [i + 1 for i in steps],
        "gate_is_unconditional": True,
        "gate_precedes_every_optimizer_step": True,
        "gradients_unchanged_between_gate_and_step": True,
    }


def verify_declared_difference(phase_e: Any) -> dict[str, Any]:
    """The successor must differ from the historical function only as declared.

    A step that is gated but has also quietly acquired some other change is not
    the path the causal result was established on.
    """
    diff = variant_diff(phase_e, "successor")
    added = [line[1:] for line in diff.splitlines()
             if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in diff.splitlines()
               if line.startswith("-") and not line.startswith("---")]
    added = [line for line in added if "def run_update" not in line]
    removed = [line for line in removed if "def run_update" not in line]

    if len(added) != EXPECTED_ADDED_LINES:
        _fail("%d added lines, expected %d: %r"
              % (len(added), EXPECTED_ADDED_LINES, added))
    if len(removed) != EXPECTED_REMOVED_LINES:
        _fail("%d removed lines, expected %d: %r"
              % (len(removed), EXPECTED_REMOVED_LINES, removed))
    if "backward()" not in removed[0]:
        _fail("the removed line is not the backward call: %r" % removed[0])
    return {"added": added, "removed": removed}


def successor_training_step(phase_e: Any) -> Callable[..., Any]:
    """Return the gated, corrected training step. There is no ungated option."""
    step = build_variant(phase_e, "successor")
    source = getattr(step, "__c2_variant_source__", None)
    if not source:
        _fail("the built step carries no source to verify")
    verify_successor_source(source)
    verify_declared_difference(phase_e)
    return step


def successor_step_report(phase_e: Any) -> dict[str, Any]:
    """The verification result, for a run record."""
    step = build_variant(phase_e, "successor")
    return {
        "structure": verify_successor_source(step.__c2_variant_source__),
        "declared_difference": verify_declared_difference(phase_e),
        "ordering": "unscale -> gate -> optimizer step -> Adam moments -> EMA",
    }
