from __future__ import annotations

import importlib
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
    return modules, parent, authority, report, child


def _successor():
    try:
        return importlib.import_module("sea_ad_jepa.v5.ema_persisted_continuation_v2")
    except ModuleNotFoundError as exc:
        pytest.fail(f"canonical EMA continuation manifest layer is missing: {exc}")


def test_persisted_ema_continuation_manifest_physically_binds_checkpoint_and_proof(tmp_path):
    _, parent, authority, report, child = _completed_state()
    successor = _successor()
    path = tmp_path / "presentation-ema-continuation.json"
    digest = successor.persist_presentation_ema_continuation_checkpoint(
        child,
        path,
        premise_state_path=PREMISE,
        parent_checkpoint=parent,
        authority=authority,
        completed_update_proof=report["presentation_ema_completion_proof"],
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )
    assert path.is_file()
    assert len(digest) == 64
    checkpoint_sidecar = tmp_path / "presentation-ema-continuation.json.checkpoint.pt"
    assert checkpoint_sidecar.is_file(), "EMA proof manifest exists but physical checkpoint sidecar is missing"

    loaded = successor.load_presentation_ema_continuation_checkpoint(
        path,
        expected_sha256=digest,
        premise_state_path=PREMISE,
    )
    assert loaded.base_checkpoint == child
    assert loaded.ema_configuration_identity == authority.ema_configuration_identity
    assert loaded.presentation_unit_id == UNIT
    assert loaded.half_life_presentations == HALF_LIFE
    assert loaded.training_authorized is False
    assert loaded.execution_authorized is False
    assert loaded.production_promotable is False


def test_persisted_ema_continuation_restart_refuses_configuration_drift(tmp_path):
    _, parent, authority, report, child = _completed_state()
    successor = _successor()
    path = tmp_path / "presentation-ema-continuation.json"
    digest = successor.persist_presentation_ema_continuation_checkpoint(
        child,
        path,
        premise_state_path=PREMISE,
        parent_checkpoint=parent,
        authority=authority,
        completed_update_proof=report["presentation_ema_completion_proof"],
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )
    loaded = successor.load_presentation_ema_continuation_checkpoint(
        path,
        expected_sha256=digest,
        premise_state_path=PREMISE,
    )

    resumed_modules = _modules()
    resumed = successor.restore_and_issue_presentation_ema_continuation_authority(
        resumed_modules,
        loaded,
        premise_state_path=PREMISE,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )
    assert resumed.ema_configuration_identity == authority.ema_configuration_identity

    with pytest.raises(RuntimeError, match="EMA|ema|configuration|half-life"):
        successor.restore_and_issue_presentation_ema_continuation_authority(
            _modules(),
            loaded,
            premise_state_path=PREMISE,
            half_life_presentations=HALF_LIFE + 1,
            presentation_unit_id=UNIT,
        )


def test_persisted_ema_manifest_or_completed_proof_tamper_fails_closed(tmp_path):
    _, parent, authority, report, child = _completed_state()
    successor = _successor()
    path = tmp_path / "presentation-ema-continuation.json"

    tampered_proof = dict(report["presentation_ema_completion_proof"])
    tampered_proof["completion_checkpoint_digest"] = "0" * 64
    with pytest.raises(RuntimeError, match="checkpoint|proof|digest|mismatch"):
        successor.persist_presentation_ema_continuation_checkpoint(
            child,
            path,
            premise_state_path=PREMISE,
            parent_checkpoint=parent,
            authority=authority,
            completed_update_proof=tampered_proof,
            half_life_presentations=HALF_LIFE,
            presentation_unit_id=UNIT,
        )

    digest = successor.persist_presentation_ema_continuation_checkpoint(
        child,
        path,
        premise_state_path=PREMISE,
        parent_checkpoint=parent,
        authority=authority,
        completed_update_proof=report["presentation_ema_completion_proof"],
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=UNIT,
    )
    raw = bytearray(path.read_bytes())
    raw[-2] ^= 1
    path.write_bytes(bytes(raw))
    with pytest.raises(RuntimeError, match="digest|manifest"):
        successor.load_presentation_ema_continuation_checkpoint(
            path,
            expected_sha256=digest,
            premise_state_path=PREMISE,
        )
