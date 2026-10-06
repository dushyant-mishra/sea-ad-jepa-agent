import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
AUTH_PATH = ROOT / "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py"
REHEARSAL_PATH = ROOT / "src/sea_ad_jepa/v5/prefreeze_guarded_rehearsal.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


auth = _load("prefreeze_runtime_authority", AUTH_PATH)
rehearsal = _load("prefreeze_guarded_rehearsal", REHEARSAL_PATH)


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _future_test_authority():
    state = json.loads(STATE_PATH.read_text())
    state = deepcopy(state)
    state["training_authorized"] = True
    state["stage_a_execution_authorized"] = True
    return auth.CurrentTrainingAuthorityV2.issue(
        governance_state=state,
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )


def test_rehearsal_runs_exact_guarded_order_and_roundtrip():
    events = []
    counter = {"value": 11}
    authority = _future_test_authority()
    guard = auth.OptimizerGuardV4(authority)

    def backward(): events.append("backward")
    def unscale(): events.append("unscale")
    def validate(): events.append("validate"); return True
    def optimizer_step():
        events.append("optimizer_step")
        counter["value"] += 1
    def ema_update(): events.append("ema")
    def checkpoint(): events.append("checkpoint"); return _sha("checkpoint-B")

    result = rehearsal.run_test_only_guarded_rehearsal(
        authority=authority,
        guard=guard,
        optimizer_identity="adamw:v1",
        optimizer_step_index=lambda: counter["value"],
        backward=backward,
        unscale=unscale,
        validate_gradients=validate,
        optimizer_step=optimizer_step,
        ema_update=ema_update,
        checkpoint=checkpoint,
    )

    assert events == ["backward", "unscale", "validate", "optimizer_step", "ema", "checkpoint"]
    assert counter["value"] == 12
    assert result["optimizer_step_before"] == 11
    assert result["optimizer_step_after"] == 12
    assert result["schema"] == "V5_PREFREEZE_GUARDED_REHEARSAL_V1"
    assert result["training_authorized"] is False
    assert result["execution_authorized"] is False
    assert result["starting_checkpoint_digest"] == _sha("checkpoint-A")
    assert result["checkpoint_digest"] == _sha("checkpoint-B")
    receipt = result["checkpoint_receipt"]
    assert receipt["parent_checkpoint_digest"] == _sha("checkpoint-A")
    assert receipt["checkpoint_digest"] == _sha("checkpoint-B")
    verified = auth.CurrentTrainingAuthorityV2.verify_completed_checkpoint_receipt(
        receipt, _sha("checkpoint-B")
    )
    assert verified["checkpoint_digest"] == _sha("checkpoint-B")


def test_failed_gradient_validation_prevents_optimizer_ema_and_checkpoint():
    events = []
    authority = _future_test_authority()
    guard = auth.OptimizerGuardV4(authority)

    with pytest.raises(auth.StepCompletionError, match="gradient validation failed"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            optimizer_step_index=lambda: 0,
            backward=lambda: events.append("backward"),
            unscale=lambda: events.append("unscale"),
            validate_gradients=lambda: events.append("validate") or False,
            optimizer_step=lambda: events.append("optimizer_step"),
            ema_update=lambda: events.append("ema"),
            checkpoint=lambda: events.append("checkpoint") or _sha("checkpoint-B"),
        )
    assert events == ["backward", "unscale", "validate"]


def test_optimizer_exception_prevents_ema_and_checkpoint():
    events = []
    authority = _future_test_authority()
    guard = auth.OptimizerGuardV4(authority)

    def boom():
        events.append("optimizer_step")
        raise RuntimeError("step exploded")

    with pytest.raises(RuntimeError, match="step exploded"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            optimizer_step_index=lambda: 0,
            backward=lambda: events.append("backward"),
            unscale=lambda: events.append("unscale"),
            validate_gradients=lambda: events.append("validate") or True,
            optimizer_step=boom,
            ema_update=lambda: events.append("ema"),
            checkpoint=lambda: events.append("checkpoint") or _sha("checkpoint-B"),
        )
    assert events == ["backward", "unscale", "validate", "optimizer_step"]


def test_noop_optimizer_prevents_ema_and_checkpoint():
    events = []
    counter = {"value": 5}
    authority = _future_test_authority()
    guard = auth.OptimizerGuardV4(authority)
    with pytest.raises(auth.StepCompletionError, match="exactly once"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            optimizer_step_index=lambda: counter["value"],
            backward=lambda: events.append("backward"),
            unscale=lambda: events.append("unscale"),
            validate_gradients=lambda: events.append("validate") or True,
            optimizer_step=lambda: events.append("optimizer_step"),
            ema_update=lambda: events.append("ema"),
            checkpoint=lambda: events.append("checkpoint") or _sha("checkpoint-B"),
        )
    assert events == ["backward", "unscale", "validate", "optimizer_step"]


def test_post_update_checkpoint_must_be_new_state():
    counter = {"value": 0}
    authority = _future_test_authority()
    guard = auth.OptimizerGuardV4(authority)
    with pytest.raises(auth.PrefreezeGovernanceError, match="new post-update state"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=authority,
            guard=guard,
            optimizer_identity="adamw:v1",
            optimizer_step_index=lambda: counter["value"],
            backward=lambda: None,
            unscale=lambda: None,
            validate_gradients=lambda: True,
            optimizer_step=lambda: counter.__setitem__("value", 1),
            ema_update=lambda: None,
            checkpoint=lambda: _sha("checkpoint-A"),
        )


def test_completed_checkpoint_receipt_rejects_wrong_reload_digest():
    authority = _future_test_authority()
    receipt = authority.completed_checkpoint_receipt(_sha("checkpoint-B"))
    with pytest.raises(auth.PrefreezeGovernanceError, match="checkpoint digest"):
        auth.CurrentTrainingAuthorityV2.verify_completed_checkpoint_receipt(
            receipt, _sha("checkpoint-C")
        )


def test_rehearsal_refuses_non_test_authority_object():
    class FakeAuthority:
        test_only = False
    with pytest.raises(auth.PrefreezeGovernanceError, match="test-only"):
        rehearsal.run_test_only_guarded_rehearsal(
            authority=FakeAuthority(),
            guard=None,
            optimizer_identity="adamw:v1",
            optimizer_step_index=lambda: 0,
            backward=lambda: None,
            unscale=lambda: None,
            validate_gradients=lambda: True,
            optimizer_step=lambda: None,
            ema_update=lambda: None,
            checkpoint=lambda: _sha("checkpoint-B"),
        )
