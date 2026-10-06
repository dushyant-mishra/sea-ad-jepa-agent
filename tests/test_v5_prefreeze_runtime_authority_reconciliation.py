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


def _state(): return json.loads(STATE_PATH.read_text())
def _sha(text): return hashlib.sha256(text.encode()).hexdigest()


class Handle:
    def __init__(self, coll, fn): self.coll, self.fn = coll, fn
    def remove(self):
        if self.fn in self.coll: self.coll.remove(self.fn)


class FakeOptimizer:
    def __init__(self, *, fail=False, skip_post=False):
        self.pre, self.post, self.mutations = [], [], 0
        self.fail, self.skip_post = fail, skip_post
    def register_step_pre_hook(self, fn): self.pre.append(fn); return Handle(self.pre, fn)
    def register_step_post_hook(self, fn): self.post.append(fn); return Handle(self.post, fn)
    def step(self, *args, **kwargs):
        for fn in list(self.pre):
            out = fn(self, args, kwargs)
            if out is not None: args, kwargs = out
        if self.fail: raise RuntimeError("optimizer failure")
        self.mutations += 1
        if not self.skip_post:
            for fn in list(self.post): fn(self, args, kwargs)
        return self.mutations


def _authority(state=None):
    return Authority.issue(
        governance_state=_state() if state is None else state,
        optimizer_identity="adamw:v1", checkpoint_digest=_sha("checkpoint-A"))


def _armed(optimizer=None):
    authority, optimizer = _authority(), optimizer or FakeOptimizer()
    guard = Guard(authority, optimizer)
    token = guard.begin_step("adamw:v1", authority.checkpoint_digest)
    return authority, optimizer, guard, token


def _ready(guard, token): guard.mark_unscaled(token); guard.mark_gradients_valid(token)


def test_authority_is_rehearsal_only():
    a = _authority()
    assert (a.rehearsal_only, a.training_authorized, a.execution_authorized) == (True, False, False)


@pytest.mark.parametrize("field,bad", [
    ("training_authorized", True), ("multimodal_training_authorized", True),
    ("stage_a_execution_authorized", True), ("stage4_authorized", True),
    ("five_hundred_k_authorized", True), ("optimizer_updates_during_target_discrimination", 1),
    ("ema_updates_during_target_discrimination", 1), ("test_state", "OPEN"),
    ("morabito_state", "OPEN"), ("production_target_winner", "ILLEGAL"),
    ("representation_winner", "ILLEGAL"), ("selected_estimand", "DONOR_WEIGHTED"),
    ("deciding_numeric_thresholds", "SET")])
def test_all_hard_prefreeze_boundaries_are_required(field, bad):
    state = deepcopy(_state()); state[field] = bad
    with pytest.raises(PrefreezeGovernanceError, match="prefreeze mechanical authority"):
        _authority(state)


def test_old_v64_authority_graph_is_rejected():
    old = {"schema": "V64_CURRENT_TRAINING_AUTHORITY", "training_authorized": False,
           "authority_roots": ["RNA_PLUS_E2_INTEGRATION_AUTHORITY"]}
    with pytest.raises(PrefreezeGovernanceError, match="governance"):
        _authority(old)


def test_entire_governance_object_is_digest_bound():
    a_state, b_state = _state(), deepcopy(_state())
    b_state["claim_ladder"] = list(b_state["claim_ladder"]) + ["ILLEGAL_TEST_MUTATION"]
    a, b = _authority(a_state), _authority(b_state)
    assert a.governance_digest != b.governance_digest
    assert a.authority_digest != b.authority_digest


def test_historical_training_authority_names_not_exposed():
    assert not hasattr(module, "CurrentTrainingAuthorityV2")
    assert not hasattr(module, "OptimizerGuardV4")


def test_optimizer_requires_real_hook_interface():
    class Bad: 
        def step(self): pass
    with pytest.raises(PrefreezeGovernanceError, match="register_step_pre_hook"):
        Guard(_authority(), Bad())


def test_optimizer_identity_and_parent_checkpoint_are_bound():
    a, opt = _authority(), FakeOptimizer(); g = Guard(a, opt)
    with pytest.raises(PrefreezeGovernanceError, match="optimizer identity"):
        g.begin_step("sgd:v1", a.checkpoint_digest)
    with pytest.raises(PrefreezeGovernanceError, match="checkpoint digest"):
        g.begin_step("adamw:v1", _sha("checkpoint-B"))


def test_gradient_validation_requires_unscale():
    _, _, g, t = _armed()
    with pytest.raises(StepCompletionError, match="unscaled"): g.mark_gradients_valid(t)


def test_direct_optimizer_step_is_blocked():
    _, opt, _, _ = _armed()
    with pytest.raises(StepCompletionError, match="not armed"): opt.step()
    assert opt.mutations == 0


def test_guard_executes_bound_optimizer_not_caller_proof():
    _, opt, g, t = _armed(); _ready(g, t)
    assert g.run_optimizer_step(t) == 1
    assert opt.mutations == 1 and g.assert_step_complete(t)
    assert "step_callable" not in Guard.run_optimizer_step.__code__.co_varnames
    assert "optimizer_step_probe" not in Guard.begin_step.__code__.co_varnames


def test_wrong_token_cannot_mutate_optimizer():
    _, opt, g, t = _armed(); _ready(g, t)
    with pytest.raises(StepCompletionError, match="supplied token"):
        opt.step(**{module.STEP_TOKEN_KWARG: "forged"})
    assert opt.mutations == 0


def test_rejected_or_failed_step_cannot_ema():
    _, opt, g, t = _armed(); g.mark_unscaled(t); g.reject_step(t, "bad gradients")
    with pytest.raises(StepCompletionError): g.run_optimizer_step(t)
    with pytest.raises(StepCompletionError): g.run_ema(t, lambda: None)
    assert opt.mutations == 0
    _, opt2, g2, t2 = _armed(FakeOptimizer(fail=True)); _ready(g2, t2)
    with pytest.raises(RuntimeError, match="optimizer failure"): g2.run_optimizer_step(t2)
    with pytest.raises(StepCompletionError): g2.run_ema(t2, lambda: None)
    assert opt2.mutations == 0


def test_missing_post_hook_is_ambiguous_and_blocks_ema():
    _, opt, g, t = _armed(FakeOptimizer(skip_post=True)); _ready(g, t)
    with pytest.raises(StepCompletionError, match="did not complete"): g.run_optimizer_step(t)
    assert opt.mutations == 1
    with pytest.raises(StepCompletionError): g.run_ema(t, lambda: None)


def test_ema_is_after_optimizer_and_one_shot():
    _, _, g, t = _armed(); _ready(g, t)
    with pytest.raises(StepCompletionError): g.run_ema(t, lambda: None)
    g.run_optimizer_step(t); calls = []
    g.run_ema(t, lambda: calls.append("ema")); assert calls == ["ema"]
    with pytest.raises(StepCompletionError, match="already consumed"): g.run_ema(t, lambda: None)


def test_guard_is_exactly_one_optimizer_update():
    a, _, g, t = _armed(); _ready(g, t); g.run_optimizer_step(t)
    with pytest.raises(StepCompletionError, match="exactly one"):
        g.begin_step("adamw:v1", a.checkpoint_digest)


def test_ema_exception_poisons_and_blocks_checkpoint():
    a, _, g, t = _armed(); _ready(g, t); g.run_optimizer_step(t)
    with pytest.raises(RuntimeError, match="ema failure"):
        g.run_ema(t, lambda: (_ for _ in ()).throw(RuntimeError("ema failure")))
    with pytest.raises(StepCompletionError, match="successful EMA"):
        g.completed_checkpoint_receipt(t, _sha("checkpoint-B"))
    with pytest.raises(StepCompletionError, match="poisoned"):
        g.begin_step("adamw:v1", a.checkpoint_digest)


def test_authority_itself_cannot_fabricate_completed_receipt():
    assert not hasattr(_authority(), "completed_checkpoint_receipt")


def test_completed_receipt_requires_guarded_step_and_ema_and_current_governance():
    a, _, g, t = _armed(); _ready(g, t); g.run_optimizer_step(t)
    with pytest.raises(StepCompletionError, match="successful EMA"):
        g.completed_checkpoint_receipt(t, _sha("checkpoint-B"))
    g.run_ema(t, lambda: None)
    receipt = g.completed_checkpoint_receipt(t, _sha("checkpoint-B"))
    core = Authority.verify_completed_checkpoint_receipt(
        receipt, _sha("checkpoint-B"), governance_state=_state())
    assert core["parent_checkpoint_digest"] == a.checkpoint_digest
    assert core["guarded_step_token"] == t


def test_completed_checkpoint_must_be_new_and_exact():
    a, _, g, t = _armed(); _ready(g, t); g.run_optimizer_step(t); g.run_ema(t, lambda: None)
    with pytest.raises(PrefreezeGovernanceError, match="new state"):
        g.completed_checkpoint_receipt(t, a.checkpoint_digest)
    receipt = g.completed_checkpoint_receipt(t, _sha("checkpoint-B"))
    with pytest.raises(PrefreezeGovernanceError, match="checkpoint digest"):
        Authority.verify_completed_checkpoint_receipt(receipt, _sha("checkpoint-C"), governance_state=_state())


def test_start_checkpoint_roundtrip_is_exact_current_and_non_authorizing():
    a = _authority(); receipt = a.start_checkpoint_receipt()
    restored = Authority.reload_start_checkpoint(receipt, a.checkpoint_digest, governance_state=_state())
    assert restored.checkpoint_digest == a.checkpoint_digest
    assert not restored.training_authorized and not restored.execution_authorized


def test_guard_close_removes_hooks_and_duplicate_guard_is_rejected():
    a, opt = _authority(), FakeOptimizer(); g = Guard(a, opt)
    with pytest.raises(PrefreezeGovernanceError, match="already has"): Guard(a, opt)
    assert opt.pre and opt.post; g.close(); assert opt.pre == [] and opt.post == []
    with pytest.raises(StepCompletionError, match="closed"): g.begin_step("adamw:v1", a.checkpoint_digest)


def test_optimizer_exception_poisons_guard():
    a, _, g, t = _armed(FakeOptimizer(fail=True)); _ready(g, t)
    with pytest.raises(RuntimeError): g.run_optimizer_step(t)
    with pytest.raises(StepCompletionError, match="poisoned"):
        g.begin_step("adamw:v1", a.checkpoint_digest)
