from __future__ import annotations

from pathlib import Path

import pytest
import torch

from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    capture_prefreeze_bound_checkpoint,
    reference_checkpoint_sha256,
)
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules,
    capture_reference_checkpoint,
)
import sea_ad_jepa.v5.ema_bound_runtime_proof_v1 as ema_binding


ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
UNIT = ema_binding.PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS
HALF_LIFE = 1000  # test-only mechanical value; not production authority


def _modules():
    return build_reference_modules(
        vocabulary_size=32,
        width=16,
        heads=4,
        blocks=1,
        ffn_width=24,
        dropout=.10,
        learning_rate=3e-4,
        betas=(.9, .999),
        eps=1e-8,
        weight_decay=.01,
        init_seed=8113002,
    )


def _case():
    torch.manual_seed(707)
    n, vocab = 6, 32
    ops = [0, 1, 0, 1, 1, 0]
    op0 = torch.tensor([0, 1, 3, 5, 7, 9, 12, 15, 18, 21, 25, 29])
    op1 = torch.tensor([0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31])
    measured = torch.zeros((n, vocab), dtype=torch.bool)
    for row, op in enumerate(ops):
        measured[row, op0 if op == 0 else op1] = True
    expression = torch.randn(n, vocab)
    expression[~measured] = 0
    cells = torch.tensor([70_001, 70_002, 70_003, 70_004, 70_005, 70_006], dtype=torch.int64)
    weights = torch.tensor([.4, 2.0, 1.1, .7, 3.2, .6], dtype=torch.float32)
    views = [
        sample_uniform_target_blocks(
            measured,
            production_seed=8813003,
            cell_indices=cells,
            sample_pass=0,
            view_index=v,
            mask_fraction=.40,
            block_count=4,
        )
        for v in range(2)
    ]
    return expression, measured, cells, ops, weights, views, {0: len(op0), 1: len(op1)}


def _completed_state():
    modules = _modules()
    data = _case()
    parent = capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
    )
    authority = ema_binding.issue_presentation_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )

    def completed_state_digest():
        checkpoint = capture_reference_checkpoint(
            modules,
            next_update_index=1,
            presentations_seen=len(data[0]),
        )
        return reference_checkpoint_sha256(checkpoint)

    report = ema_binding.run_presentation_ema_bound_guarded_reference_update(
        modules,
        authority=authority,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
        completion_checkpoint_digest=completed_state_digest,
        expression=data[0],
        measurement_mask=data[1],
        stable_cell_keys=data[2],
        operator_ids=data[3],
        scientific_cell_weights=data[4],
        target_block_views=data[5],
        measured_tokens_by_operator=data[6],
        max_teacher_tokens_per_microbatch=40,
        run_seed=8113002,
        update_index=0,
    )
    child = capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=1,
        presentations_seen=len(data[0]),
        premise_state_path=PREMISE,
        completed_guard_receipt=report["completed_guard_receipt"],
    )
    return modules, authority, report, child


def _bound(authority, report, child):
    return ema_binding.bind_completed_checkpoint_to_presentation_ema(
        child,
        report["presentation_ema_completion_proof"],
        authority=authority,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )


def test_typed_ema_continuation_physically_binds_checkpoint_and_completion_proof(tmp_path):
    _, authority, report, child = _completed_state()
    envelope = _bound(authority, report, child)
    assert envelope.base_checkpoint == child
    assert envelope.ema_configuration_identity == authority.ema_configuration_identity
    assert envelope.presentation_unit_id == UNIT
    assert envelope.half_life_presentations == HALF_LIFE
    assert envelope.training_authorized is False
    assert envelope.execution_authorized is False
    assert envelope.production_promotable is False

    path = tmp_path / "presentation-ema-continuation.pt"
    digest = ema_binding.persist_presentation_ema_bound_checkpoint(
        envelope,
        path,
        premise_state_path=PREMISE,
    )
    assert path.is_file() and len(digest) == 64
    loaded = ema_binding.load_presentation_ema_bound_checkpoint(
        path,
        expected_sha256=digest,
        premise_state_path=PREMISE,
    )
    assert loaded == envelope
    assert loaded.presentation_ema_completion_proof == report["presentation_ema_completion_proof"]


def test_typed_ema_continuation_restart_refuses_configuration_drift(tmp_path):
    _, authority, report, child = _completed_state()
    envelope = _bound(authority, report, child)
    path = tmp_path / "presentation-ema-continuation.pt"
    digest = ema_binding.persist_presentation_ema_bound_checkpoint(
        envelope,
        path,
        premise_state_path=PREMISE,
    )
    loaded = ema_binding.load_presentation_ema_bound_checkpoint(
        path,
        expected_sha256=digest,
        premise_state_path=PREMISE,
    )

    resumed = ema_binding.issue_presentation_ema_bound_authority_from_persisted_checkpoint(
        _modules(),
        loaded,
        premise_state_path=PREMISE,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )
    assert resumed.ema_configuration_identity == authority.ema_configuration_identity
    assert resumed.parent_presentations_seen == child.reference_checkpoint.presentations_seen

    with pytest.raises(RuntimeError, match="EMA|ema|configuration|half-life"):
        ema_binding.issue_presentation_ema_bound_authority_from_persisted_checkpoint(
            _modules(),
            loaded,
            premise_state_path=PREMISE,
            half_life_presentations=HALF_LIFE + 1,
            presentation_unit_id=UNIT,
        )


def test_typed_ema_continuation_rejects_detached_proof_and_artifact_tamper(tmp_path):
    _, authority, report, child = _completed_state()
    tampered_proof = dict(report["presentation_ema_completion_proof"])
    tampered_proof["completion_checkpoint_digest"] = "0" * 64
    with pytest.raises(RuntimeError, match="checkpoint|proof|digest|mismatch"):
        ema_binding.bind_completed_checkpoint_to_presentation_ema(
            child,
            tampered_proof,
            authority=authority,
            half_life_presentations=HALF_LIFE,
            presentation_unit_id=UNIT,
        )

    envelope = _bound(authority, report, child)
    path = tmp_path / "presentation-ema-continuation.pt"
    digest = ema_binding.persist_presentation_ema_bound_checkpoint(
        envelope,
        path,
        premise_state_path=PREMISE,
    )
    raw = bytearray(path.read_bytes())
    raw[-1] ^= 1
    path.write_bytes(bytes(raw))
    with pytest.raises(RuntimeError, match="digest"):
        ema_binding.load_presentation_ema_bound_checkpoint(
            path,
            expected_sha256=digest,
            premise_state_path=PREMISE,
        )
