import inspect
from dataclasses import replace
import hashlib

import numpy as np
import pytest

from scripts.v77.v77_synthetic_batch_adapter import (
    SyntheticConversion,
    SyntheticModelBatch,
    SyntheticOperatorContext,
    SyntheticOracleRecord,
    SyntheticReadoutRecord,
    SyntheticSplitContext,
)
from sea_ad_jepa.qualification import v77_join
from sea_ad_jepa.qualification.canonical import canonical_digest
from sea_ad_jepa.qualification.physical_binding_v2 import PhysicalRowValueBindingV2
from sea_ad_jepa.qualification.qsafe import REQUIRED_Q_SAFETY_CHANNELS
from sea_ad_jepa.qualification.receipts import (
    BOUND_ADAPTER_Q_SAFETY_PROOF_SCHEMA,
    BoundAdapterQSafetyProofV1,
    QSafetyChannelExecutionEvidenceV1,
)


def _batch(adapter_digest):
    measurement = np.array([[True, True, True, True], [True, True, True, True]], dtype=bool)
    hidden = np.array([[False, True, False, False], [False, False, True, False]], dtype=bool)
    conversion = SyntheticConversion(
        model=SyntheticModelBatch(
            gene_ids=np.tile(np.arange(4, dtype=np.int64), (2, 1)),
            student_expression=np.array(
                [[1.0, 0.0, 2.0, 3.0], [1.5, 2.5, 0.0, 3.5]], dtype=np.float32
            ),
            measurement_mask=measurement,
            hidden_target_mask=hidden,
        ),
        operator_context=SyntheticOperatorContext(
            source_index=np.array([0, 0], dtype=np.int16),
            operator_index=np.array([0, 0], dtype=np.int16),
            visible_library_size=np.array([10.0, 11.0], dtype=np.float32),
            n_measured=np.array([4, 4], dtype=np.int32),
        ),
        split_context=SyntheticSplitContext(donor_index=np.array([0, 1], dtype=np.int32)),
        readout=SyntheticReadoutRecord(
            query_counts=np.array([[0.0, 4.0, 0.0, 0.0], [0.0, 0.0, 5.0, 0.0]], dtype=np.float32),
            full_library_size=np.array([14.0, 16.0], dtype=np.float32),
        ),
        oracle=SyntheticOracleRecord(
            global_cell_index=np.array([101, 102], dtype=np.int64),
            latents={},
            b3_arm_membership=None,
            b6_ladder_level=None,
            substate=None,
            annotated_class=None,
        ),
        global_cell_index=np.array([101, 102], dtype=np.int64),
        provenance={
            "observer_manifest_sha256": "d" * 64,
            "structural_support_rule": "test-support-v1",
            "observation_identity": {
                "source_roster": ["SRC"],
                "operator_ids": ["OP"],
                "operator_source_map": [["OP", "SRC"]],
                "donor_ids": ["D0", "D1"],
            },
        },
    )
    return v77_join.build_qualification_batch_from_v77_conversion(
        conversion,
        feature_ids=("g0", "g1", "g2", "g3"),
        experiment_run_id="v77-zero-update-001",
        adapter_id="v77-synthetic-batch-adapter",
        adapter_digest=adapter_digest,
        code_commit="1234567890abcdef1234567890abcdef12345678",
        environment_digest="e" * 64,
        synthetic_realization_id="v77-zero-update-dev",
        challenge_partition="DEVELOPMENT_CALIBRATION",
    )


def _proof(batch, runtime_source_sha256):
    return BoundAdapterQSafetyProofV1(
        schema=BOUND_ADAPTER_Q_SAFETY_PROOF_SCHEMA,
        q_safety_policy_id="qsafe-v1",
        adapter_id=batch.adapter_id,
        adapter_digest=batch.adapter_digest,
        batch_scientific_identity_digest=batch.scientific_identity.digest(),
        runtime_source_sha256=runtime_source_sha256,
        channel_evidence=tuple(
            QSafetyChannelExecutionEvidenceV1(
                channel=channel,
                evidence_digest=f"{index + 1:064x}",
                executed=True,
            )
            for index, channel in enumerate(REQUIRED_Q_SAFETY_CHANNELS)
        ),
        execution_authorized=False,
        training_authorized=False,
        production_promotable=False,
    )


def _bindings(batch):
    rows = batch.model_view().model_inputs["student_expression"]
    feature_digest = batch.feature_identity_receipt.digest()
    bindings = []
    for row_index, (observation_id, donor_id, row) in enumerate(
        zip(batch.scientific_identity.observation_ids, batch.inference_group_ids, rows)
    ):
        values_digest = canonical_digest(tuple(float(value) for value in row))
        payload_digest = hashlib.sha256(f"synthetic-payload-{row_index}".encode("utf-8")).hexdigest()
        bindings.append(
            PhysicalRowValueBindingV2(
                expression_row=row_index,
                source_row_index=row_index,
                block_row_index=row_index,
                selected_block_row_index=row_index,
                logical_cell_id=observation_id,
                source_cell_id=observation_id,
                logical_donor_id=donor_id,
                source_donor_id=donor_id,
                matrix_slot="model/student_expression",
                authenticated_matrix_slot="model/student_expression",
                feature_space_sha256=feature_digest,
                authenticated_feature_space_sha256=feature_digest,
                payload_location=f"synthetic-batch:row-{row_index}",
                authenticated_payload_location=f"synthetic-batch:row-{row_index}",
                payload_sha256=payload_digest,
                authenticated_payload_sha256=payload_digest,
                authenticated_values_sha256=values_digest,
                consumed_values_sha256=values_digest,
            )
        )
    return tuple(bindings)


def test_joined_batch_executes_canonical_v5_zero_update_without_any_mutation():
    from sea_ad_jepa.qualification import v77_bound_zero_update as v77_zero_update

    adapter_digest = v77_zero_update.canonical_v77_adapter_source_sha256()
    batch = _batch(adapter_digest)
    runtime_digest = v77_zero_update.canonical_v5_runtime_source_sha256()
    receipt = v77_zero_update.run_canonical_v5_zero_update(
        batch,
        physical_bindings=_bindings(batch),
        q_safety_proof=_proof(batch, runtime_digest),
        runtime_source_sha256=runtime_digest,
        init_seed=8113002,
    )
    assert receipt["schema"] == "V77_CANONICAL_V5_ZERO_UPDATE_V1"
    assert receipt["runtime_source_sha256"] == runtime_digest
    assert receipt["adapter_source_sha256"] == adapter_digest
    assert len(receipt["physical_bindings_digest"]) == 64
    assert receipt["checkpoint_digest_before"] == receipt["checkpoint_digest_after"]
    assert receipt["optimizer_step_before"] == receipt["optimizer_step_after"] == 0
    assert receipt["teacher_presentations_before"] == receipt["teacher_presentations_after"] == 0
    assert receipt["online_parameters_unchanged"] is True
    assert receipt["teacher_parameters_unchanged"] is True
    assert receipt["predictor_parameters_unchanged"] is True
    assert receipt["optimizer_state_unchanged"] is True
    assert receipt["ema_performed"] is False
    assert receipt["optimizer_step_performed"] is False
    assert receipt["training_authorized"] is False


def test_caller_cannot_substitute_fake_runtime_source_digest():
    from sea_ad_jepa.qualification import v77_bound_zero_update as v77_zero_update

    batch = _batch(v77_zero_update.canonical_v77_adapter_source_sha256())
    actual = v77_zero_update.canonical_v5_runtime_source_sha256()
    fake = "c" * 64
    assert fake != actual
    with pytest.raises(ValueError, match="runtime.*source|canonical.*runtime|digest"):
        v77_zero_update.run_canonical_v5_zero_update(
            batch,
            physical_bindings=_bindings(batch),
            q_safety_proof=_proof(batch, fake),
            runtime_source_sha256=fake,
            init_seed=8113002,
        )


def test_caller_cannot_substitute_fake_v77_adapter_source_digest():
    from sea_ad_jepa.qualification import v77_bound_zero_update as v77_zero_update

    actual = v77_zero_update.canonical_v77_adapter_source_sha256()
    fake = "a" * 64
    assert fake != actual
    batch = _batch(fake)
    runtime_digest = v77_zero_update.canonical_v5_runtime_source_sha256()
    with pytest.raises(ValueError, match="adapter.*source|canonical.*adapter|digest"):
        v77_zero_update.run_canonical_v5_zero_update(
            batch,
            physical_bindings=_bindings(batch),
            q_safety_proof=_proof(batch, runtime_digest),
            runtime_source_sha256=runtime_digest,
            init_seed=8113002,
        )


def test_zero_update_requires_physical_row_value_bindings_at_every_execution_boundary():
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_zero_update

    for executor in (v77_bound_zero_update.run_canonical_v5_zero_update, v77_zero_update.run_canonical_v5_zero_update):
        parameters = inspect.signature(executor).parameters
        assert "physical_bindings" in parameters
        assert parameters["physical_bindings"].default is inspect.Parameter.empty


def test_self_consistent_but_wrong_consumed_values_cannot_reach_execution():
    from sea_ad_jepa.qualification import v77_bound_zero_update as v77_zero_update

    batch = _batch(v77_zero_update.canonical_v77_adapter_source_sha256())
    bindings = list(_bindings(batch))
    wrong = "f" * 64
    bindings[0] = replace(
        bindings[0],
        authenticated_values_sha256=wrong,
        consumed_values_sha256=wrong,
    )
    runtime_digest = v77_zero_update.canonical_v5_runtime_source_sha256()
    with pytest.raises(ValueError, match="consumed values.*executed batch"):
        v77_zero_update.run_canonical_v5_zero_update(
            batch,
            physical_bindings=tuple(bindings),
            q_safety_proof=_proof(batch, runtime_digest),
            runtime_source_sha256=runtime_digest,
            init_seed=8113002,
        )
