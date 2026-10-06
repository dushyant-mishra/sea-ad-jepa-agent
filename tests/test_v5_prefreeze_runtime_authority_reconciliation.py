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

Authority = module.PrefreezeMechanicalAuthorityV1
Guard = module.PrefreezeOptimizerGuardV1
PrefreezeGovernanceError = module.PrefreezeGovernanceError
StepCompletionError = module.StepCompletionError


def _state():
    return json.loads(STATE_PATH.read_text())


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Handle:
    def __init__(self, collection, fn):
        self.collection = collection
        self.fn = fn

    def remove(self):
        if self.fn in self.collection:
            self.collection.remove(self.fn)


class FakeOptimizer:
    def __init__(self, *, fail=False, skip_post=False):
        self.pre = []
        self.post = []
        self.mutations = 0
        self.fail = fail
        self.skip_post = skip_post

    def register_step_pre_hook(self, fn):
        self.pre.append(fn)
        return Handle(self.pre, fn)

    def register_step_post_hook(self, fn):
        self.post.append(fn)
        return Handle(self.post, fn)

    def step(self, *args, **kwargs):
        for fn in list(self.pre):
            out = fn(self, args, kwargs)
            if out is not None:
                args, kwargs = out
        if self.fail:
            raise RuntimeError("optimizer failure")
        self.mutations += 1
        if not self.skip_post:
            for fn in list(self.post):
                fn(self, args, kwargs)
        return self.mutations


def _authority(state=None):
    return Authority.issue(
        governance_state=_state() if state is None else state,
        optimizer_identity="adamw:v1",
        checkpoint_digest=_sha("checkpoint-A"),
    )


def _armed(*, optimizer=None):
    authority = _authority()
    optimizer = optimizer or FakeOptimizer()
    guard = Guard(authority, optimizer)
    token = guard.begin_step("adamw:v1", _sha("checkpoint-A"))
    return authority, optimizer, guard, token


def _ready(guard, token):
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)


def test_canonical_prefreeze_state_issues_only_non_authorizing_mechanical_authority():
    authority = _authority()
    assert authority.rehearsal_only is True
    assert authority.training_authorized is False
    assert authority.execution_authorized is False


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("training_authorized", True),
        ("multimodal_training_authorized", True),
        ("stage_a_execution_authorized", True),
        ("stage4_authorized", True),
        ("five_hundred_k_authorized", True),
        ("optimizer_updates_during_target_discrimination", 1),
        ("ema_updates_during_target_discrimination", 1),
        ("test_state", "OPEN"),
        ("morabito_state", "OPEN"),
        ("production_target_winner", "ILLEGAL"),
        ("representation_winner", "ILLEGAL"),
        ("selected_estimand", "DONOR_WEIGHTED"),
        ("deciding_numeric_thresholds", "SET"),
    ],
)
def test_every_hard_prefreeze_boundary_is_required(field, bad_value):
    state = deepcopy(_state())
    state[field] = bad_value
    with pytest.raises(PrefreezeGovernanceError, match="prefreeze mechanical authority"):
        _authority(state)


def test_old_v64_authority_graph_cannot_substitute_for_current_governance():
    old = {
        "schema": "V64_CURRENT_TRAINING_AUTHORITY",
        "training_authorized": False,
        "authority_roots": ["RNA_PLUS_E2_INTEGRATION_AUTHORITY"],
    }
    with pytest.raises(PrefreezeGovernanceError, match="governance"):
        _authority(old)


def test_full_machine_governance_is_digest_bound():
    state_a = _state()
    state_b = deepcopy(state_a)
    state_b["claim_ladder"] = list(state_b["claim_ladder"]) + ["ILLEGAL_TEST_MUTATION"]
    a = _authority(state_a)
    b = _authority(state_b)
    assert a.governance_digest != b.governance_digest
    assert a.authority_digest != b.authority_digest


def test_historical_training_authority_names_are_not_reintroduced():
    assert not hasattr(module, "CurrentTrainingAuthorityV2")
    assert not hasattr(module, "OptimizerGuardV4")


def test_optimizer_must_support_real_step_hooks():
    class NotAnOptimizer:
        def step(self):
            pass

    with pytest.raises(PrefreezeGovernanceError, match="register_step_pre_hook"):
        Guard(_authority(), NotAnOptimizer())


def test_optimizer_identity_and_checkpoint_are_exact_bound():
    authority = _authority()
    guard = Guard(authority, FakeOptimizer())
    with pytest.raises(PrefreezeGovernanceError, match="optimizer identity"):
        guard.begin_step("sgd:v1", _sha("checkpoint-A"))
    with pytest.raises(PrefreezeGovernanceError, match="checkpoint digest"):
        guard.begin_step("adamw:v1", _sha("checkpoint-B"))


def test_gradient_validation_must_follow_unscale():
    _, _, guard, token = _armed()
    with pytest.raises(StepCompletionError, match="unscaled"):
        guard.mark_gradients_valid(token)


def test_direct_optimizer_step_is_denied_by_installed_guard():
    _, optimizer, _, _ = _armed()
    with pytest.raises(StepCompletionError, match="not armed"):
        optimizer.step()
    assert optimizer.mutations == 0


def test_guard_executes_the_bound_optimizer_not_a_caller_callback():
    _, optimizer, guard, token = _armed()
    _ready(guard, token)
    result = guard.run_optimizer_step(token)
    assert result == 1
    assert optimizer.mutations == 1
    assert guard.assert_step_complete(token) is True
    assert "step_callable" not in Guard.run_optimizer_step.__code__.co_varnames
    assert "optimizer_step_probe" not in Guard.begin_step.__code__.co_varnames


def test_wrong_step_token_cannot_mutate_optimizer():
    _, optimizer, guard, token = _armed()
    _ready(guard, token)
    with pytest.raises(StepCompletionError, match="supplied token"):
        optimizer.step(**{module.STEP_TOKEN_KWARG: "forged-token"})
    assert optimizer.mutations == 0


def test_rejected_step_cannot_run_optimizer_or_ema():
    _, optimizer, guard, token = _armed()
    guard.mark_unscaled(token)
    guard.reject_step(token, "nonfinite gradients")
    with pytest.raises(StepCompletionError):
        guard.run_optimizer_step(token)
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, lambda: None)
    assert optimizer.mutations == 0


def test_optimizer_exception_cannot_advance_ema():
    _, optimizer, guard, token = _armed(optimizer=FakeOptimizer(fail=True))
    _ready(guard, token)
    with pytest.raises(RuntimeError, match="optimizer failure"):
        guard.run_optimizer_step(token)
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, lambda: None)
    assert optimizer.mutations == 0


def test_missing_post_hook_completion_is_rejected():
    _, optimizer, guard, token = _armed(optimizer=FakeOptimizer(skip_post=True))
    _ready(guard, token)
    with pytest.raises(StepCompletionError, match="did not complete"):
        guard.run_optimizer_step(token)
    assert optimizer.mutations == 1
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, lambda: None)


def test_ema_requires_completed_optimizer_and_is_one_shot():
    _, _, guard, token = _armed()
    _ready(guard, token)
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, lambda: None)
    guard.run_optimizer_step(token)
    calls = []
    guard.run_ema(token, lambda: calls.append("ema"))
    assert calls == ["ema"]
    with pytest.raises(StepCompletionError, match="already consumed"):
        guard.run_ema(token, lambda: calls.append("again"))


def test_next_optimizer_step_is_forbidden_after_first_update():
    _, _, guard, token = _armed()
    _ready(guard, token)
    guard.run_optimizer_step(token)
    with pytest.raises(StepCompletionError, match="exactly one"):
        guard.begin_step("adamw:v1", _sha("checkpoint-A"))


def test_ema_exception_prevents_completed_checkpoint_receipt():
    _, _, guard, token = _armed()
    _ready(guard, token)
    guard.run_optimizer_step(token)

    def fail_ema():
        raise RuntimeError("ema failure")

    with pytest.raises(RuntimeError, match="ema failure"):
        guard.run_ema(token, fail_ema)
    with pytest.raises(StepCompletionError, match="successful EMA"):
        guard.completed_checkpoint_receipt(token, _sha("checkpoint-B"))


def test_authority_cannot_fabricate_a_completed_checkpoint_receipt():
    authority = _authority()
    assert not hasattr(authority, "completed_checkpoint_receipt")


def test_completed_checkpoint_requires_guarded_step_and_ema():
    authority, _, guard, token = _armed()
    _ready(guard, token)
    guard.run_optimizer_step(token)
    with pytest.raises(StepCompletionError, match="successful EMA"):
        guard.completed_checkpoint_receipt(token, _sha("checkpoint-B"))
    guard.run_ema(token, lambda: None)
    receipt = guard.completed_checkpoint_receipt(token, _sha("checkpoint-B"))
    verified = Authority.verify_completed_checkpoint_receipt(receipt, _sha("checkpoint-B"))
    assert verified["parent_checkpoint_digest"] == authority.checkpoint_digest
    assert verified["guarded_step_token"] == token


def test_completed_checkpoint_must_be_new_state_and_exact_on_reload():
    authority, _, guard, token = _armed()
    _ready(guard, token)
    guard.run_optimizer_step(token)
    guard.run_ema(token, lambda: None)
    with pytest.raises(PrefreezeGovernanceError, match="new state"):
        guard.completed_checkpoint_receipt(token, authority.checkpoint_digest)
    receipt = guard.completed_checkpoint_receipt(token, _sha("checkpoint-B"))
    with pytest.raises(PrefreezeGovernanceError, match="checkpoint digest"):
        Authority.verify_completed_checkpoint_receipt(receipt, _sha("checkpoint-C"))


def test_start_checkpoint_receipt_roundtrip_is_exact_and_non_authorizing():
    authority = _authority()
    receipt = authority.start_checkpoint_receipt()
    restored = Authority.reload_start_checkpoint(receipt, authority.checkpoint_digest)
    assert restored.checkpoint_digest == authority.checkpoint_digest
    assert restored.training_authorized is False
    assert restored.execution_authorized is False


def test_guard_close_removes_optimizer_hooks():
    authority = _authority()
    optimizer = FakeOptimizer()
    guard = Guard(authority, optimizer)
    assert optimizer.pre and optimizer.post
    guard.close()
    assert optimizer.pre == [] and optimizer.post == []
    with pytest.raises(StepCompletionError, match="closed"):
        guard.begin_step("adamw:v1", _sha("checkpoint-A"))


def test_optimizer_exception_poisons_guard_against_further_steps():
    _, _, guard, token = _armed(optimizer=FakeOptimizer(fail=True))
    _ready(guard, token)
    with pytest.raises(RuntimeError, match="optimizer failure"):
        guard.run_optimizer_step(token)
    with pytest.raises(StepCompletionError, match="poisoned"):
        guard.begin_step("adamw:v1", _sha("checkpoint-A"))


def test_ema_exception_poisons_guard_against_further_steps():
    _, _, guard, token = _armed()
    _ready(guard, token)
    guard.run_optimizer_step(token)
    with pytest.raises(RuntimeError, match="ema failure"):
        guard.run_ema(token, lambda: (_ for _ in ()).throw(RuntimeError("ema failure")))
    with pytest.raises(StepCompletionError, match="poisoned"):
        guard.begin_step("adamw:v1", _sha("checkpoint-A"))
