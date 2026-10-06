import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
MODULE_PATH = ROOT / "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py"

spec = importlib.util.spec_from_file_location("prefreeze_runtime_authority_redteam", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
Authority = module.PrefreezeMechanicalAuthorityV1
Guard = module.PrefreezeOptimizerGuardV1
PrefreezeGovernanceError = module.PrefreezeGovernanceError
StepCompletionError = module.StepCompletionError


def _sha(text): return hashlib.sha256(text.encode()).hexdigest()
def _state(): return json.loads(STATE_PATH.read_text())


class Handle:
    def __init__(self, coll, fn): self.coll, self.fn = coll, fn
    def remove(self):
        if self.fn in self.coll: self.coll.remove(self.fn)


class FakeOptimizer:
    def __init__(self): self.pre, self.post, self.mutations = [], [], 0
    def register_step_pre_hook(self, fn): self.pre.append(fn); return Handle(self.pre, fn)
    def register_step_post_hook(self, fn): self.post.append(fn); return Handle(self.post, fn)
    def step(self, *args, **kwargs):
        for fn in list(self.pre):
            out = fn(self, args, kwargs)
            if out is not None: args, kwargs = out
        self.mutations += 1
        for fn in list(self.post): fn(self, args, kwargs)
        return self.mutations


def _authority(state=None):
    return Authority.issue(governance_state=_state() if state is None else state,
                           optimizer_identity="adamw:v1", checkpoint_digest=_sha("checkpoint-A"))


def _completed_guard():
    a, opt = _authority(), FakeOptimizer(); g = Guard(a, opt)
    t = g.begin_step("adamw:v1", a.checkpoint_digest)
    g.mark_unscaled(t); g.mark_gradients_valid(t); g.run_optimizer_step(t); g.run_ema(t, lambda: None)
    return a, opt, g, t


def test_unknown_top_level_governance_field_is_rejected():
    state = deepcopy(_state()); state["historical_spillover_authority"] = "V64"
    with pytest.raises(PrefreezeGovernanceError, match="contract fields mismatch"):
        _authority(state)


def test_missing_top_level_governance_field_is_rejected():
    state = deepcopy(_state()); state.pop("claim_ladder")
    with pytest.raises(PrefreezeGovernanceError, match="contract fields mismatch"):
        _authority(state)


def test_unknown_nested_governance_field_is_rejected():
    state = deepcopy(_state()); state["diagnostic_readout_firewall"]["historical_override"] = True
    with pytest.raises(PrefreezeGovernanceError, match="diagnostic_readout_firewall fields mismatch"):
        _authority(state)


def test_missing_nested_governance_field_is_rejected():
    state = deepcopy(_state()); state["representation_stability"].pop("held_out_donors_may_influence_alignment")
    with pytest.raises(PrefreezeGovernanceError, match="representation_stability fields mismatch"):
        _authority(state)


def test_structurally_valid_scientific_mutation_is_rejected():
    state = deepcopy(_state())
    state["claim_ladder"] = ["RNA_REPRESENTATION", "ILLEGAL_REPLACEMENT", "REGULATORY_SUPPORT", "CAUSAL_PERTURBATIONAL_PREDICTION"]
    with pytest.raises(PrefreezeGovernanceError, match="canonical V3 governance digest"):
        _authority(state)


def test_prefreeze_guard_is_exactly_one_update_not_a_hidden_trainer():
    a, _, g, _ = _completed_guard()
    with pytest.raises(StepCompletionError, match="exactly one"): g.begin_step("adamw:v1", a.checkpoint_digest)


def test_completed_checkpoint_receipt_is_one_shot():
    _, _, g, t = _completed_guard(); g.completed_checkpoint_receipt(t, _sha("checkpoint-B"))
    with pytest.raises(StepCompletionError, match="already emitted"): g.completed_checkpoint_receipt(t, _sha("checkpoint-C"))


def test_duplicate_guard_installation_on_same_optimizer_is_rejected():
    a, opt = _authority(), FakeOptimizer(); Guard(a, opt)
    with pytest.raises(PrefreezeGovernanceError, match="already has"): Guard(a, opt)


def test_start_receipt_rejects_unknown_and_missing_fields():
    a = _authority(); receipt = a.start_checkpoint_receipt()
    extra = deepcopy(receipt); extra["historical_authority_root"] = "V64"
    with pytest.raises(PrefreezeGovernanceError, match="start checkpoint receipt fields mismatch"):
        Authority.reload_start_checkpoint(extra, a.checkpoint_digest, governance_state=_state())
    missing = deepcopy(receipt); missing.pop("optimizer_identity")
    with pytest.raises(PrefreezeGovernanceError, match="start checkpoint receipt fields mismatch"):
        Authority.reload_start_checkpoint(missing, a.checkpoint_digest, governance_state=_state())


def test_completed_receipt_rejects_unknown_and_missing_fields():
    _, _, g, t = _completed_guard(); receipt = g.completed_checkpoint_receipt(t, _sha("checkpoint-B"))
    extra = deepcopy(receipt); extra["historical_authority_root"] = "V64"
    with pytest.raises(PrefreezeGovernanceError, match="completed checkpoint receipt fields mismatch"):
        Authority.verify_completed_checkpoint_receipt(extra, _sha("checkpoint-B"), governance_state=_state())
    missing = deepcopy(receipt); missing.pop("guarded_step_token")
    with pytest.raises(PrefreezeGovernanceError, match="completed checkpoint receipt fields mismatch"):
        Authority.verify_completed_checkpoint_receipt(missing, _sha("checkpoint-B"), governance_state=_state())


def test_start_receipt_must_match_current_validated_governance():
    a = _authority(); receipt = a.start_checkpoint_receipt(); changed = deepcopy(_state())
    changed["claim_ladder"] = ["RNA_REPRESENTATION", "ILLEGAL_REPLACEMENT", "REGULATORY_SUPPORT", "CAUSAL_PERTURBATIONAL_PREDICTION"]
    with pytest.raises(PrefreezeGovernanceError):
        Authority.reload_start_checkpoint(receipt, a.checkpoint_digest, governance_state=changed)


def test_completed_receipt_must_match_current_validated_governance():
    _, _, g, t = _completed_guard(); receipt = g.completed_checkpoint_receipt(t, _sha("checkpoint-B")); changed = deepcopy(_state())
    changed["claim_ladder"] = ["RNA_REPRESENTATION", "ILLEGAL_REPLACEMENT", "REGULATORY_SUPPORT", "CAUSAL_PERTURBATIONAL_PREDICTION"]
    with pytest.raises(PrefreezeGovernanceError):
        Authority.verify_completed_checkpoint_receipt(receipt, _sha("checkpoint-B"), governance_state=changed)


def test_source_does_not_import_or_expose_superseded_scientific_authority():
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden = ("rna_e2_target_integration_authority", "current_authority_roots_v4",
                 "current_teacher_target_receipt_v4", "qualified_optimizer_guard_v4")
    assert [x for x in forbidden if f"import {x}" in source or f"from .{x}" in source] == []
    assert not hasattr(module, "CurrentTrainingAuthorityV2")
    assert not hasattr(module, "OptimizerGuardV4")
