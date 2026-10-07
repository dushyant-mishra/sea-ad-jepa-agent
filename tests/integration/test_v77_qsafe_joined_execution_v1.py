from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse
import torch

from scripts.v77 import v77_synthetic_batch_adapter as AD
from sea_ad_jepa.qualification.qsafe import REQUIRED_Q_SAFETY_CHANNELS
from sea_ad_jepa.qualification.receipts import BoundAdapterQSafetyProofV1
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules


GCI = np.array([10, 11], dtype=np.int64)
SUPPORT = np.ones((2, 6), dtype=bool)
UNIVERSE = np.arange(6, dtype=np.int64)
SEED = 12345
HIDDEN_FRACTION = 0.5


def _write_world(root: Path, counts: np.ndarray) -> None:
    truth_dir = root / "hidden_truth"
    obs_dir = root / "observable_raw" / "obs"
    truth_dir.mkdir(parents=True)
    obs_dir.mkdir(parents=True)
    np.savez(
        truth_dir / "TRUTH_000.npz",
        global_cell_index=GCI,
        source_index=np.array([0, 0], dtype=np.int64),
        operator_index=np.array([0, 0], dtype=np.int64),
        donor_index=np.array([0, 1], dtype=np.int64),
    )
    matrix = sparse.csr_matrix(np.asarray(counts, dtype=np.float64))
    np.savez(
        obs_dir / "SHARD_000.npz",
        data=matrix.data,
        indices=matrix.indices,
        indptr=matrix.indptr,
        global_cell_index=GCI,
        support_mask_packed=np.packbits(SUPPORT, axis=1),
        support_count=SUPPORT.sum(1),
        source_index=np.array([0, 0], dtype=np.int64),
        operator_index=np.array([0, 0], dtype=np.int64),
        donor_index=np.array([0, 1], dtype=np.int64),
    )
    manifest = {
        "schema": "JOINED_QSAFE_TEST_OBSERVER_V1",
        "n_addresses": 6,
        "shards": [{"file": "SHARD_000.npz"}],
        "structural_support_rule": "TEST_FULL_SUPPORT",
        "observation_identity": {
            "source_roster": ["SRC"],
            "operator_ids": ["OP"],
            "operator_source_map": [["OP", "SRC"]],
            "donor_ids": ["D0", "D1"],
        },
    }
    (obs_dir / "OBSERVER_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")


def _counterfactual_pair(tmp_path: Path):
    base = np.array(
        [[11, 13, 17, 19, 23, 29], [31, 37, 41, 43, 47, 53]],
        dtype=np.float64,
    )
    hidden = AD.sample_hidden_targets(SUPPORT, GCI, HIDDEN_FRACTION, SEED)
    assert hidden.any()
    changed = base.copy()
    changed[hidden] += 101.0
    world_a = tmp_path / "a"
    world_b = tmp_path / "b"
    _write_world(world_a, base)
    _write_world(world_b, changed)
    conv_a = AD.build_from_world(world_a, "obs", UNIVERSE, HIDDEN_FRACTION, SEED)
    conv_b = AD.build_from_world(world_b, "obs", UNIVERSE, HIDDEN_FRACTION, SEED)
    return conv_a, conv_b


def _modules():
    return build_reference_modules(
        vocabulary_size=6,
        width=8,
        heads=2,
        blocks=1,
        ffn_width=12,
        dropout=0.0,
        learning_rate=3e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
        init_seed=8113002,
    )


def test_joined_qsafe_execution_proves_all_channels_and_student_invariance(tmp_path):
    import sea_ad_jepa.qualification.v77_qsafe_joined as joined

    conv_a, conv_b = _counterfactual_pair(tmp_path)
    assert np.array_equal(conv_a.model.hidden_target_mask, conv_b.model.hidden_target_mask)
    assert np.array_equal(conv_a.model.student_expression, conv_b.model.student_expression)
    assert np.array_equal(conv_a.operator_context.visible_library_size, conv_b.operator_context.visible_library_size)
    assert not np.array_equal(conv_a.readout.query_counts, conv_b.readout.query_counts)

    input_a = joined.assemble_qsafe_v77_v5_input(conv_a)
    input_b = joined.assemble_qsafe_v77_v5_input(conv_b)
    evidence = conv_a.model.evidence_mask
    hidden = conv_a.model.hidden_target_mask

    assert torch.equal(input_a.student_expression, input_b.student_expression)
    assert torch.equal(input_a.teacher_expression[evidence], input_a.student_expression[evidence])
    assert torch.equal(input_b.teacher_expression[evidence], input_b.student_expression[evidence])
    assert not torch.equal(input_a.teacher_expression[hidden], input_b.teacher_expression[hidden])

    proof = joined.prove_executed_v77_q_safety(
        conv_a,
        conv_b,
        modules=_modules(),
        adapter_id="V77_SYNTHETIC_BATCH_ADAPTER_V3",
        batch_scientific_identity_digest="e" * 64,
        runtime_source_sha256="9" * 64,
        q_safety_policy_id="qsafe-v1",
        run_seed=77,
        update_index=0,
    )
    assert isinstance(proof, BoundAdapterQSafetyProofV1)
    assert tuple(item.channel for item in proof.channel_evidence) == REQUIRED_Q_SAFETY_CHANNELS
    assert all(item.executed for item in proof.channel_evidence)
    assert proof.execution_authorized is False
    assert proof.training_authorized is False
    assert proof.production_promotable is False


def test_joined_qsafe_execution_rejects_non_counterfactual_student_change(tmp_path):
    import sea_ad_jepa.qualification.v77_qsafe_joined as joined

    conv_a, conv_b = _counterfactual_pair(tmp_path)
    altered_model = AD.SyntheticModelBatch(
        gene_ids=conv_b.model.gene_ids,
        student_expression=conv_b.model.student_expression.copy(),
        measurement_mask=conv_b.model.measurement_mask,
        hidden_target_mask=conv_b.model.hidden_target_mask,
    )
    altered_model.student_expression[0, 0] += 0.25
    altered = AD.SyntheticConversion(
        model=altered_model,
        operator_context=conv_b.operator_context,
        split_context=conv_b.split_context,
        readout=conv_b.readout,
        oracle=conv_b.oracle,
        global_cell_index=conv_b.global_cell_index,
        provenance=conv_b.provenance,
    )
    with pytest.raises(ValueError, match="student|counterfactual|q-safety"):
        joined.prove_executed_v77_q_safety(
            conv_a,
            altered,
            modules=_modules(),
            adapter_id="V77_SYNTHETIC_BATCH_ADAPTER_V3",
            batch_scientific_identity_digest="e" * 64,
            runtime_source_sha256="9" * 64,
            q_safety_policy_id="qsafe-v1",
            run_seed=77,
            update_index=0,
        )
