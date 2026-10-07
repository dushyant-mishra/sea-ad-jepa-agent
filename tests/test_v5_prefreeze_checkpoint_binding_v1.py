from dataclasses import replace
from pathlib import Path

import pytest
import torch
import sea_ad_jepa.v5.inactive_checkpoint_binding_v1 as binding

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    PREFREEZE_RUNTIME_CONTRACT,
    capture_prefreeze_bound_checkpoint,
    restore_prefreeze_bound_checkpoint,
)
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules


ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
CHECKPOINT_BINDING = ROOT / "src/sea_ad_jepa/v5/inactive_checkpoint_binding_v1.py"


def _modules():
    return build_reference_modules(
        vocabulary_size=32,
        width=16,
        heads=4,
        blocks=1,
        ffn_width=24,
        dropout=.10,
        learning_rate=3e-4,
        betas=(.9,.999),
        eps=1e-8,
        weight_decay=.01,
        init_seed=8113002,
    )


def _assert_modules_equal(a, b):
    for ma, mb in ((a.online,b.online),(a.teacher,b.teacher),(a.predictor,b.predictor)):
        sa=ma.state_dict(); sb=mb.state_dict(); assert sa.keys()==sb.keys()
        for name in sa:
            assert torch.equal(sa[name],sb[name]), name


def test_capture_binds_frozen_premise_and_remains_non_authorizing():
    envelope = capture_prefreeze_bound_checkpoint(
        _modules(), next_update_index=0, presentations_seen=0, premise_state_path=PREMISE)
    assert envelope.runtime_contract == PREFREEZE_RUNTIME_CONTRACT
    assert len(envelope.premise_state_sha256) == 64
    assert envelope.training_authority_digest is None
    assert envelope.execution_authorized is False
    assert envelope.training_authorized is False
    assert envelope.production_promotable is False


def test_checkpoint_provenance_binds_actual_canonical_runtime_not_legacy_guard():
    source = CHECKPOINT_BINDING.read_text(encoding="utf-8")
    required = (
        "inactive_update_reference.py",
        "inactive_guarded_update_v1.py",
        "prefreeze_runtime_authority.py",
        "inactive_checkpoint_binding_v1.py",
    )
    for name in required:
        assert name in source, f"checkpoint runtime provenance omits {name}"
    assert "inactive_runtime_step_guard_v1.py" not in source


def test_restore_roundtrip_requires_exact_premise_and_preserves_mechanics_state():
    source=_modules(); envelope=capture_prefreeze_bound_checkpoint(
        source,next_update_index=0,presentations_seen=0,premise_state_path=PREMISE)
    restored=_modules()
    cursor,presentations=restore_prefreeze_bound_checkpoint(
        restored,envelope,premise_state_path=PREMISE)
    assert (cursor,presentations)==(0,0)
    _assert_modules_equal(source,restored)


def test_bound_checkpoint_roundtrip_preserves_amp_scaler_state():
    source=_modules(); source_scaler=torch.amp.GradScaler('cpu',init_scale=8.0,growth_interval=1)
    envelope=capture_prefreeze_bound_checkpoint(
        source,next_update_index=0,presentations_seen=0,premise_state_path=PREMISE,scaler=source_scaler)
    assert envelope.reference_checkpoint.amp_scaler_used is True
    restored=_modules(); restored_scaler=torch.amp.GradScaler('cpu',init_scale=2.0,growth_interval=17)
    cursor,presentations=restore_prefreeze_bound_checkpoint(
        restored,envelope,premise_state_path=PREMISE,scaler=restored_scaler)
    assert (cursor,presentations)==(0,0)
    assert restored_scaler.state_dict()==source_scaler.state_dict()
    _assert_modules_equal(source,restored)
    with pytest.raises(ValueError,match='scaler|AMP'):
        restore_prefreeze_bound_checkpoint(_modules(),envelope,premise_state_path=PREMISE)


def test_persisted_checkpoint_is_hashed_reloaded_and_tamper_evident(tmp_path):
    assert callable(getattr(binding,"persist_prefreeze_bound_checkpoint",None)), (
        "canonical checkpoint has no physical persistence function")
    assert callable(getattr(binding,"load_persisted_prefreeze_bound_checkpoint",None)), (
        "canonical checkpoint has no verified reload function")
    envelope=capture_prefreeze_bound_checkpoint(
        _modules(),next_update_index=0,presentations_seen=0,premise_state_path=PREMISE)
    path=tmp_path/'checkpoint.pt'
    digest=binding.persist_prefreeze_bound_checkpoint(envelope,path)
    assert path.is_file()
    assert len(digest)==64
    loaded=binding.load_persisted_prefreeze_bound_checkpoint(path,expected_sha256=digest)
    assert loaded==envelope
    payload=bytearray(path.read_bytes()); payload[-1]^=1; path.write_bytes(payload)
    with pytest.raises(RuntimeError,match='digest'):
        binding.load_persisted_prefreeze_bound_checkpoint(path,expected_sha256=digest)


def test_noninitial_bound_checkpoint_requires_completed_guard_receipt():
    modules=_modules()
    modules.optimizer.zero_grad(set_to_none=True)
    for group in modules.optimizer.param_groups:
        for parameter in group['params']:
            parameter.grad=torch.zeros_like(parameter)
    modules.optimizer.step()
    with pytest.raises(RuntimeError, match='completed guard receipt'):
        capture_prefreeze_bound_checkpoint(
            modules,next_update_index=1,presentations_seen=6,premise_state_path=PREMISE)


def test_authority_is_issued_only_from_exact_parent_bound_state():
    assert callable(getattr(binding,"issue_prefreeze_authority_from_bound_checkpoint",None)), (
        "canonical runtime has no parent-checkpoint-bound authority issuer")
    modules=_modules()
    parent=capture_prefreeze_bound_checkpoint(
        modules,next_update_index=0,presentations_seen=0,premise_state_path=PREMISE)
    authority=binding.issue_prefreeze_authority_from_bound_checkpoint(
        modules,parent,premise_state_path=PREMISE)
    assert authority.checkpoint_digest==binding.reference_checkpoint_sha256(parent.reference_checkpoint)

    with torch.no_grad():
        next(modules.online.parameters()).add_(1.0)
    with pytest.raises(RuntimeError,match='parent|state'):
        binding.issue_prefreeze_authority_from_bound_checkpoint(
            modules,parent,premise_state_path=PREMISE)


def test_restore_rejects_premise_drift(tmp_path):
    envelope=capture_prefreeze_bound_checkpoint(
        _modules(),next_update_index=0,presentations_seen=0,premise_state_path=PREMISE)
    changed=tmp_path/'premise.json'
    changed.write_bytes(PREMISE.read_bytes()+b'\n')
    with pytest.raises(RuntimeError,match='premise state digest mismatch'):
        restore_prefreeze_bound_checkpoint(_modules(),envelope,premise_state_path=changed)


def test_restore_rejects_authority_or_promotion_injection():
    envelope=capture_prefreeze_bound_checkpoint(
        _modules(),next_update_index=0,presentations_seen=0,premise_state_path=PREMISE)
    for corrupt in (
        replace(envelope,training_authority_digest='0'*64),
        replace(envelope,training_authorized=True),
        replace(envelope,execution_authorized=True),
        replace(envelope,production_promotable=True),
        replace(envelope,runtime_contract='HISTORICAL_OR_UNKNOWN_RUNTIME'),
    ):
        with pytest.raises(RuntimeError):
            restore_prefreeze_bound_checkpoint(_modules(),corrupt,premise_state_path=PREMISE)
