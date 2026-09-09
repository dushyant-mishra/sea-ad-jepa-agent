"""The adoption entrypoint must refuse anything that could step ungated.

`v5_successor_training_step_v1` is the module a successor training run asks for
its step function. Its value is entirely in what it refuses, so the refusals are
what is tested here. A verifier that cannot reject is a verifier that certifies
everything, which is worse than no verifier because it produces a record saying
the path was checked.

The synthetic sources below are deliberately near-misses: each is gated, and
each is gated in a way that does not protect the optimizer step.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"))

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.v4 import v5_successor_training_step_v1 as adoption  # noqa: E402


def _canonical() -> Path:
    for root in CANONICAL_ROOTS:
        if (root / "scripts/v4/stage81a3_prod41k_engineering_smoke.py").is_file():
            return root
    pytest.skip("canonical repository not reachable")


def _phase_e():
    root = _canonical()
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "exports" / "static_context_decomposition_v4_20260821"))
    spec = importlib.util.spec_from_file_location(
        "phase_e", root / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase_e"] = module
    spec.loader.exec_module(module)
    return module


GATED = '''
def run_update_successor(*, online, optimizer, scaler):
    scaler.unscale_(optimizer)
    _mandatory_gate.enforce_registry(online)
    _mandatory_gate.enforce(online)
    scaler.step(optimizer)
'''

UNGATED = '''
def run_update(*, online, optimizer, scaler):
    scaler.unscale_(optimizer)
    scaler.step(optimizer)
'''

GATE_AFTER_STEP = '''
def run_update_successor(*, online, optimizer, scaler):
    scaler.unscale_(optimizer)
    scaler.step(optimizer)
    _mandatory_gate.enforce_registry(online)
    _mandatory_gate.enforce(online)
'''

GATE_BEFORE_UNSCALE = '''
def run_update_successor(*, online, optimizer, scaler):
    _mandatory_gate.enforce_registry(online)
    _mandatory_gate.enforce(online)
    scaler.unscale_(optimizer)
    scaler.step(optimizer)
'''

GATE_IN_A_BRANCH = '''
def run_update_successor(*, online, optimizer, scaler, check):
    scaler.unscale_(optimizer)
    if check:
        _mandatory_gate.enforce_registry(online)
        _mandatory_gate.enforce(online)
    scaler.step(optimizer)
'''

# Accepted, and worth saying why. A second step after the gate applies
# gradients the gate has already adjudicated -- nothing rewrites `.grad` in
# between -- so the dead-gradient failure cannot recur through it. Double
# stepping is a training defect, but it is not this gate's contract.
SECOND_STEP_AFTER_THE_GATE = '''
def run_update_successor(*, online, optimizer, scaler, fallback):
    scaler.unscale_(optimizer)
    _mandatory_gate.enforce_registry(online)
    _mandatory_gate.enforce(online)
    scaler.step(optimizer)
    if fallback:
        optimizer.step()
'''

# Refused. The gate passed on one set of gradients and the optimizer applies a
# different set, so the record in front of the step means nothing.
BACKWARD_AFTER_THE_GATE = '''
def run_update_successor(*, online, optimizer, scaler, extra_loss):
    scaler.unscale_(optimizer)
    _mandatory_gate.enforce_registry(online)
    _mandatory_gate.enforce(online)
    extra_loss.backward()
    scaler.step(optimizer)
'''

# Refused, and the most direct form of it: every protected gradient is set to
# zero after the only check that would have noticed.
ZERO_GRAD_AFTER_THE_GATE = '''
def run_update_successor(*, online, optimizer, scaler):
    scaler.unscale_(optimizer)
    _mandatory_gate.enforce_registry(online)
    _mandatory_gate.enforce(online)
    optimizer.zero_grad(set_to_none=False)
    scaler.step(optimizer)
'''


def test_a_properly_gated_source_is_accepted() -> None:
    """Otherwise every rejection below would be uninformative."""
    report = adoption.verify_successor_source(GATED)
    assert report["gate_precedes_every_optimizer_step"] is True
    assert report["gate_is_unconditional"] is True


@pytest.mark.parametrize("source,why", [
    (UNGATED, "no gate at all"),
    (GATE_AFTER_STEP, "gate runs after the step it should have prevented"),
    (GATE_BEFORE_UNSCALE, "gate reads scaled gradients"),
    (GATE_IN_A_BRANCH, "a branch skips the gate"),
    (BACKWARD_AFTER_THE_GATE, "the applied gradients are not the gated ones"),
    (ZERO_GRAD_AFTER_THE_GATE, "gradients are zeroed after the check"),
])
def test_unsafe_sources_are_refused(source: str, why: str) -> None:
    with pytest.raises(RuntimeError) as caught:
        adoption.verify_successor_source(source)
    assert adoption.STOP_UNVERIFIED in str(caught.value), why


def test_a_second_step_after_the_gate_is_accepted() -> None:
    """Documenting a deliberate limit of scope, not an oversight.

    I first wrote this case as one the verifier must refuse. It should not: the
    gate adjudicated the gradients this step applies, so the historical failure
    cannot recur through it. Recording the decision here keeps a later reader
    from "fixing" the verifier to reject it.
    """
    report = adoption.verify_successor_source(SECOND_STEP_AFTER_THE_GATE)
    assert report["gate_precedes_every_optimizer_step"] is True


def test_the_real_successor_step_verifies_and_is_callable() -> None:
    phase_e = _phase_e()
    step = adoption.successor_training_step(phase_e)
    assert callable(step)
    report = adoption.successor_step_report(phase_e)
    assert report["structure"]["gate_precedes_every_optimizer_step"] is True
    assert len(report["declared_difference"]["added"]) == 4
    assert len(report["declared_difference"]["removed"]) == 1


def test_the_canonical_function_would_not_pass_this_verifier() -> None:
    """The path a naive V5 launcher would import is exactly what is refused."""
    import inspect

    phase_e = _phase_e()
    with pytest.raises(RuntimeError):
        adoption.verify_successor_source(inspect.getsource(phase_e.run_update))
