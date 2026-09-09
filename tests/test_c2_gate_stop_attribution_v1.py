"""The runner must not record a non-gate failure as the gate working.

The production-geometry runner writes a "GATE STOPPED the update" record when
the update raises and the gate is judged responsible. That record is the
evidence that the historical failure cannot recur, so the way it decides
responsibility has to be tested rather than reasoned about -- a handler that
accepts too much would manufacture exactly the proof the lane is trying to earn.

`attribute_gate_stop` is control flow, so it is tested here against a stub gate.
The gate's own adjudication is covered by `test_c2_mandatory_gradient_gate_v1`
and is not re-litigated. `stop_state_evidence` is tested against real tensors,
including the case where state *did* change, because an evidence function that
cannot report movement makes "nothing moved" an empty sentence.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

ROOT = Path(__file__).resolve().parents[1]


def _runner():
    path = ROOT / "scripts" / "v4" / "run_c2_t1_exact_path_forensic_v3.py"
    spec = importlib.util.spec_from_file_location("c2_forensic_runner", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["c2_forensic_runner"] = module
    spec.loader.exec_module(module)
    return module


class _StubGate:
    """A gate that objects to everything, so only the guards can return None."""

    def __init__(self, registry_passes: bool = True, tensors_pass: bool = False):
        self._registry_passes = registry_passes
        self._tensors_pass = tensors_pass

    def validate_registry(self, module):
        return {"passed": self._registry_passes, "discovered_count": 48,
                "expected_count": 48, "missing": [], "unexpected": []}

    def gate_module(self, module):
        return {"passed": self._tensors_pass, "rejected_count":
                0 if self._tensors_pass else 48, "total": 48}


def test_an_objecting_gate_in_a_gated_variant_is_attributed() -> None:
    """The true positive the two regression runs depend on."""
    runner = _runner()
    verdict = runner.attribute_gate_stop(
        RuntimeError("mandatory gradient gate rejected 48 of 48 tensors"),
        None, _StubGate(), "gated_historical")
    assert verdict is not None
    assert verdict["tensors"]["rejected_count"] == 48


def test_an_out_of_memory_error_is_never_a_gate_stop() -> None:
    """OOM subclasses RuntimeError, and OOM at this geometry is a real failure.

    Without this guard, running out of memory while the protected gradients
    happened to be dead would be written down as the gate working.
    """
    runner = _runner()
    oom = getattr(torch.cuda, "OutOfMemoryError", None)
    if oom is not None:
        assert runner.attribute_gate_stop(
            oom("CUDA out of memory."), None, _StubGate(),
            "successor") is None
    # Also by message, for builds that raise plain RuntimeError for OOM.
    assert runner.attribute_gate_stop(
        RuntimeError("CUDA out of memory. Tried to allocate 2.00 GiB"),
        None, _StubGate(), "successor") is None


def test_an_ungated_variant_can_never_be_attributed_to_the_gate() -> None:
    """In `historical` every protected gradient is dead, but no gate is present.

    The re-adjudication alone would object on every historical run, so without
    the variant guard the ungated control could report itself as gated.
    """
    runner = _runner()
    for variant in ("historical", "backward_autocast_disabled",
                    "production_safe"):
        assert runner.attribute_gate_stop(
            RuntimeError("invalid active gradients: missing=0, nonfinite=3"),
            None, _StubGate(), variant) is None


def test_a_satisfied_gate_means_the_failure_was_something_else() -> None:
    """`run_update` raises for its own reasons; those must propagate unchanged."""
    runner = _runner()
    assert runner.attribute_gate_stop(
        RuntimeError("EMA target received gradients"), None,
        _StubGate(tensors_pass=True), "successor") is None


def test_a_non_runtime_error_is_not_a_gate_stop() -> None:
    runner = _runner()
    assert runner.attribute_gate_stop(
        ValueError("unrelated"), None, _StubGate(), "successor") is None


class _Model(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.w = torch.nn.Parameter(torch.ones(4))


def test_stop_state_evidence_reports_a_clean_stop() -> None:
    model = _Model()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    before = {"w": model.w.detach().float().clone()}
    runner = _runner()
    evidence = runner.stop_state_evidence(before, model, optimizer, ["w"])
    assert evidence["no_optimizer_state_created"] is True
    assert evidence["no_parameter_moved"] is True


def test_stop_state_evidence_is_not_vacuous() -> None:
    """It must be able to fail, or "nothing moved" asserts nothing at all."""
    model = _Model()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    before = {"w": model.w.detach().float().clone()}
    model.w.grad = torch.ones_like(model.w)
    optimizer.step()
    runner = _runner()
    evidence = runner.stop_state_evidence(before, model, optimizer, ["w"])
    assert evidence["no_optimizer_state_created"] is False
    assert evidence["tensors_with_adam_moments"] == ["w"]
    assert evidence["no_parameter_moved"] is False
    assert evidence["tensors_moved"] == ["w"]


def test_the_runner_exposes_both_gated_variants() -> None:
    """The regression cannot be run at production geometry without these."""
    source = (ROOT / "scripts" / "v4"
              / "run_c2_t1_exact_path_forensic_v3.py").read_text(encoding="utf-8")
    assert '"successor"' in source
    assert '"gated_historical"' in source
