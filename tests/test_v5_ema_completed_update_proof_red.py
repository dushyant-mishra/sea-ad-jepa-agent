from pathlib import Path

import pytest
import torch

from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.ema_bound_runtime_proof_v1 import (
    PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    issue_presentation_ema_bound_authority_from_checkpoint,
    run_presentation_ema_bound_guarded_reference_update,
)
import sea_ad_jepa.v5.ema_bound_runtime_proof_v1 as ema_binding
from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import (
    capture_prefreeze_bound_checkpoint,
    load_persisted_prefreeze_bound_checkpoint,
    reference_checkpoint_sha256,
    restore_prefreeze_bound_checkpoint,
)
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules,
    capture_reference_checkpoint,
)


ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
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
            view_index=view,
            mask_fraction=.40,
            block_count=4,
        )
        for view in range(2)
    ]
    return expression, measured, cells, ops, weights, views, {0: len(op0), 1: len(op1)}


def _completed_transition():
    data = _case()
    modules = _modules()
    parent = capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
    )
    authority = issue_presentation_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    )

    def completed_state_digest():
        checkpoint = capture_reference_checkpoint(
            modules,
            next_update_index=1,
            presentations_seen=len(data[0]),
        )
        return reference_checkpoint_sha256(checkpoint)

    report = run_presentation_ema_bound_guarded_reference_update(
        modules,
        authority=authority,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
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


def _completed_report():
    _, authority, report, _ = _completed_transition()
    return authority, report


def test_completed_update_emits_digest_bound_presentation_ema_proof():
    authority, report = _completed_report()
    proof = report.get("presentation_ema_completion_proof")
    assert isinstance(proof, dict), (
        "completed optimizer+EMA transition is not yet bound to its presentation-EMA configuration"
    )
    assert proof["schema"] == "V5_PRESENTATION_EMA_COMPLETED_UPDATE_PROOF_V1"
    assert proof["ema_configuration_identity"] == authority.ema_configuration_identity
    assert proof["ema_bound_authority_digest"] == authority.binding_digest
    assert proof["completed_guard_receipt_digest"] == report["completed_guard_receipt"]["receipt_digest"]
    assert proof["completion_checkpoint_digest"] == report["completed_guard_receipt"]["checkpoint_digest"]
    assert proof["presentations_this_update"] == len(_case()[0])
    assert len(proof["proof_digest"]) == 64
    assert proof["execution_authorized"] is False
    assert proof["training_authorized"] is False
    assert proof["production_promotable"] is False


def test_completed_update_proof_rejects_ema_or_guard_receipt_drift():
    authority, report = _completed_report()
    proof = report.get("presentation_ema_completion_proof")
    verify = getattr(ema_binding, "verify_presentation_ema_completed_update_proof", None)
    assert callable(verify), "no verifier exists for the completed presentation-EMA proof"
    assert verify(
        proof,
        authority=authority,
        completed_guard_receipt=report["completed_guard_receipt"],
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    ) is True
    with pytest.raises(RuntimeError, match="EMA|ema|configuration"):
        verify(
            proof,
            authority=authority,
            completed_guard_receipt=report["completed_guard_receipt"],
            half_life_presentations=HALF_LIFE + 1,
            presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
        )
    tampered_receipt = dict(report["completed_guard_receipt"])
    tampered_receipt["receipt_digest"] = "0" * 64
    with pytest.raises(RuntimeError, match="receipt|digest"):
        verify(
            proof,
            authority=authority,
            completed_guard_receipt=tampered_receipt,
            half_life_presentations=HALF_LIFE,
            presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
        )


def test_noninitial_checkpoint_cannot_reissue_ema_authority_without_persisted_configuration_proof():
    modules, _, _, child = _completed_transition()
    with pytest.raises(RuntimeError, match="persisted|EMA|proof"):
        issue_presentation_ema_bound_authority_from_checkpoint(
            modules,
            child,
            premise_state_path=PREMISE,
            half_life_presentations=HALF_LIFE,
            presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
        )


def test_persisted_ema_proof_survives_roundtrip_and_rejects_restart_configuration_drift(tmp_path):
    modules, authority, report, child = _completed_transition()
    persist = getattr(ema_binding, "persist_and_verify_presentation_ema_checkpoint", None)
    assert callable(persist), "presentation-EMA identity is not carried through physical checkpoint proof"
    checkpoint_path = tmp_path / "ema-bound-parent.pt"
    persisted = persist(
        child,
        checkpoint_path,
        premise_state_path=PREMISE,
        authority=authority,
        completed_update_proof=report["presentation_ema_completion_proof"],
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    )
    assert persisted["schema"] == "V5_PRESENTATION_EMA_PERSISTED_CHECKPOINT_PROOF_V1"
    assert persisted["ema_configuration_identity"] == authority.ema_configuration_identity
    assert persisted["presentation_ema_completion_proof_digest"] == report["presentation_ema_completion_proof"]["proof_digest"]
    assert persisted["logical_checkpoint_sha256"] == reference_checkpoint_sha256(child.reference_checkpoint)
    assert persisted["presentations_seen"] == len(_case()[0])
    assert persisted["persisted_verified_reload"] is True
    assert persisted["execution_authorized"] is False
    assert persisted["training_authorized"] is False
    assert persisted["production_promotable"] is False

    loaded = load_persisted_prefreeze_bound_checkpoint(
        checkpoint_path,
        expected_sha256=persisted["artifact_sha256"],
    )
    resumed = _modules()
    cursor, presentations = restore_prefreeze_bound_checkpoint(
        resumed,
        loaded,
        premise_state_path=PREMISE,
    )
    assert (cursor, presentations) == (1, len(_case()[0]))

    continued = issue_presentation_ema_bound_authority_from_checkpoint(
        resumed,
        loaded,
        premise_state_path=PREMISE,
        half_life_presentations=HALF_LIFE,
        presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
        persisted_ema_proof=persisted,
    )
    assert continued.ema_configuration_identity == authority.ema_configuration_identity

    with pytest.raises(RuntimeError, match="EMA|ema|configuration"):
        issue_presentation_ema_bound_authority_from_checkpoint(
            resumed,
            loaded,
            premise_state_path=PREMISE,
            half_life_presentations=HALF_LIFE + 1,
            presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
            persisted_ema_proof=persisted,
        )
