from dataclasses import replace
from pathlib import Path

import pytest
import torch

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    PREFREEZE_RUNTIME_CONTRACT,
    capture_prefreeze_bound_checkpoint,
    restore_prefreeze_bound_checkpoint,
)
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules


ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"


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
        _modules(),
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
    )
    assert envelope.runtime_contract == PREFREEZE_RUNTIME_CONTRACT
    assert len(envelope.premise_state_sha256) == 64
    assert envelope.training_authority_digest is None
    assert envelope.execution_authorized is False
    assert envelope.training_authorized is False
    assert envelope.production_promotable is False


def test_restore_roundtrip_requires_exact_premise_and_preserves_mechanics_state():
    source=_modules(); envelope=capture_prefreeze_bound_checkpoint(
        source,next_update_index=0,presentations_seen=0,premise_state_path=PREMISE)
    restored=_modules()
    cursor,presentations=restore_prefreeze_bound_checkpoint(
        restored,envelope,premise_state_path=PREMISE)
    assert (cursor,presentations)==(0,0)
    _assert_modules_equal(source,restored)


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
