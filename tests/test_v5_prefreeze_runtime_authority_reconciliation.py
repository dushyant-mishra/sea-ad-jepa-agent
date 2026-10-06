import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
MODULE_PATH = ROOT / "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py"

spec = importlib.util.spec_from_file_location("prefreeze_runtime_authority", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

CurrentTrainingAuthorityV2 = module.CurrentTrainingAuthorityV2
OptimizerGuardV4 = module.OptimizerGuardV4
PrefreezeGovernanceError = module.PrefreezeGovernanceError
StepCompletionError = module.StepCompletionError


def _state():
    return json.loads(STATE_PATH.read_text())


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _future_fixture():
    state = deepcopy(_state())
    state["training_authorized"] = True
    state["stage_a_execution_authorized"] = True
    return state


def _armed_guard():
    authority = CurrentTrainingAuthorityV2.issue(
        governance_state=_future_fixture(),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    guard = OptimizerGuardV4(authority)
    token = guard.begin_step("adamw:v1", _sha("checkpoint-A"))
    return authority, guard, token


def test_canonical_prefreeze_state_refuses_training_authority():
    with pytest.raises(PrefreezeGovernanceError, match="training_authorized=false"):
        CurrentTrainingAuthorityV2.issue(
            governance_state=_state(),
            optimizer_identity="adamw:v1",
            checkpoint_digest=_sha("checkpoint-A"),
        )


def test_stage_a_off_independently_refuses_training_authority():
    state = _future_fixture()
    state["stage_a_execution_authorized"] = False
    with pytest.raises(PrefreezeGovernanceError, match="stage_a_execution_authorized=false"):
        CurrentTrainingAuthorityV2.issue(
            governance_state=state,
            optimizer_identity="adamw:v1",
            checkpoint_digest=_sha("checkpoint-A"),
        )


def test_mutated_prefreeze_state_cannot_issue_production_authority():
    with pytest.raises(PrefreezeGovernanceError, match="production issuance disabled"):
        CurrentTrainingAuthorityV2.issue(
            governance_state=_future_fixture(),
            optimizer_identity="adamw:v1",
            checkpoint_digest=_sha("checkpoint-A"),
            test_only=False,
        )


def test_old_scientific_roots_cannot_substitute_for_current_prefreeze_state():
    old_v64 = {
        "training_authorized": True,
        "stage_a_execution_authorized": True,
        "authority_roots": ["RNA_PLUS_E2_INTEGRATION_AUTHORITY"],
    }
    with pytest.raises(PrefreezeGovernanceError, match="schema"):
        CurrentTrainingAuthorityV2.issue(
            governance_state=old_v64,
            optimizer_identity="adamw:v1",
            checkpoint_digest=_sha("checkpoint-A"),
        )


def test_future_fixture_can_exercise_mechanical_guard_without_changing_canonical_state():
    authority = CurrentTrainingAuthorityV2.issue(
        governance_state=_future_fixture(),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    assert authority.test_only is True
    assert _state()["training_authorized"] is False


def test_authority_digest_binds_entire_governance_state_not_selected_subset():
    state_a = _future_fixture()
    state_b = deepcopy(state_a)
    state_b["representation_winner"] = "ILLEGAL_TEST_MUTATION"
    a = CurrentTrainingAuthorityV2.issue(
        governance_state=state_a,
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    b = CurrentTrainingAuthorityV2.issue(
        governance_state=state_b,
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    assert a.governance_digest != b.governance_digest
    assert a.authority_digest != b.authority_digest


def test_optimizer_identity_mismatch_is_rejected():
    authority = CurrentTrainingAuthorityV2.issue(
        governance_state=_future_fixture(),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    guard = OptimizerGuardV4(authority)
    with pytest.raises(PrefreezeGovernanceError, match="optimizer identity"):
        guard.begin_step("sgd:v1", _sha("checkpoint-A"))


def test_checkpoint_digest_mismatch_is_rejected():
    authority = CurrentTrainingAuthorityV2.issue(
        governance_state=_future_fixture(),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    guard = OptimizerGuardV4(authority)
    with pytest.raises(PrefreezeGovernanceError, match="checkpoint digest"):
        guard.begin_step("adamw:v1", _sha("checkpoint-B"))


def test_gradient_validation_must_follow_unscale_and_precede_step():
    _, guard, token = _armed_guard()
    with pytest.raises(StepCompletionError, match="unscaled"):
        guard.mark_gradients_valid(token)
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    guard.run_optimizer_step(token, lambda: None)
    assert guard.assert_step_complete(token) is True


def test_manual_step_completion_cannot_be_forged():
    _, guard, _ = _armed_guard()
    assert not hasattr(guard, "mark_optimizer_step_complete")


def test_rejected_step_cannot_advance_ema():
    _, guard, token = _armed_guard()
    guard.mark_unscaled(token)
    guard.reject_step(token, "nonfinite gradients")
    with pytest.raises(StepCompletionError, match="EMA"):
        guard.authorize_ema(token)


def test_incomplete_step_cannot_advance_ema():
    _, guard, token = _armed_guard()
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    with pytest.raises(StepCompletionError, match="EMA"):
        guard.authorize_ema(token)


def test_failed_optimizer_call_cannot_advance_ema():
    _, guard, token = _armed_guard()
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)

    def fail():
        raise RuntimeError("optimizer failure")

    with pytest.raises(RuntimeError, match="optimizer failure"):
        guard.run_optimizer_step(token, fail)
    with pytest.raises(StepCompletionError, match="EMA"):
        guard.authorize_ema(token)


def test_successful_optimizer_step_is_required_before_ema():
    _, guard, token = _armed_guard()
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    called = []
    guard.run_optimizer_step(token, lambda: called.append("stepped"))
    assert called == ["stepped"]
    assert guard.authorize_ema(token) is True


def test_step_completion_token_is_one_shot_and_cannot_be_replayed():
    _, guard, token = _armed_guard()
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    guard.run_optimizer_step(token, lambda: None)
    assert guard.authorize_ema(token) is True
    with pytest.raises(StepCompletionError, match="already consumed"):
        guard.authorize_ema(token)


def test_restart_authority_binds_exact_checkpoint_digest():
    authority = CurrentTrainingAuthorityV2.issue(
        governance_state=_future_fixture(),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    receipt = authority.checkpoint_receipt()
    assert receipt["checkpoint_digest"] == _sha("checkpoint-A")
    assert CurrentTrainingAuthorityV2.reload(receipt, _sha("checkpoint-A")).checkpoint_digest == _sha("checkpoint-A")
    with pytest.raises(PrefreezeGovernanceError, match="checkpoint digest"):
        CurrentTrainingAuthorityV2.reload(receipt, _sha("checkpoint-B"))


def test_completed_checkpoint_receipt_reconstructs_parent_authority_digest():
    authority = CurrentTrainingAuthorityV2.issue(
        governance_state=_future_fixture(),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    receipt = authority.completed_checkpoint_receipt(_sha("checkpoint-B"))
    forged = deepcopy(receipt)
    forged["authority_digest"] = _sha("forged-authority")
    core = {k: v for k, v in forged.items() if k != "receipt_digest"}
    forged["receipt_digest"] = module._digest(core)
    with pytest.raises(PrefreezeGovernanceError, match="authority digest"):
        CurrentTrainingAuthorityV2.verify_completed_checkpoint_receipt(
            forged, _sha("checkpoint-B")
        )


def test_runtime_layer_never_selects_scientific_winners():
    authority = CurrentTrainingAuthorityV2.issue(
        governance_state=_future_fixture(),
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
        test_only=True,
    )
    receipt = authority.checkpoint_receipt()
    assert "production_target_winner" not in receipt
    assert "representation_winner" not in receipt
    assert "selected_estimand" not in receipt
