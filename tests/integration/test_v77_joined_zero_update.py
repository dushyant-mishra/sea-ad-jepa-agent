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
from sea_ad_jepa.qualification.pipeline import QualificationBatchV1
from sea_ad_jepa.qualification.qsafe import REQUIRED_Q_SAFETY_CHANNELS
from sea_ad_jepa.qualification.receipts import (
    BOUND_ADAPTER_Q_SAFETY_PROOF_SCHEMA,
    BoundAdapterQSafetyProofV1,
    QSafetyChannelExecutionEvidenceV1,
    QSafetyExecutionProofStatus,
)
from sea_ad_jepa.qualification.v77_join import (
    PhysicalRowValueBindingV1,
    build_learnable_model_context,
)


def _valid_binding(**overrides):
    values = dict(
        expression_row=91,
        source_row_index=91,
        block_row_index=3,
        selected_block_row_index=3,
        logical_cell_id="cell-91",
        source_cell_id="cell-91",
        payload_sha256="a" * 64,
        authenticated_values_sha256="b" * 64,
        consumed_values_sha256="b" * 64,
    )
    values.update(overrides)
    return PhysicalRowValueBindingV1(**values)


def _valid_q_safety_proof(**overrides):
    values = dict(
        schema=BOUND_ADAPTER_Q_SAFETY_PROOF_SCHEMA,
        q_safety_policy_id="qsafe-v1",
        adapter_id="v77-synthetic-batch-adapter",
        adapter_digest="a" * 64,
        batch_scientific_identity_digest="b" * 64,
        runtime_source_sha256="c" * 64,
        channel_evidence=tuple(
            QSafetyChannelExecutionEvidenceV1(
                channel=channel,
                evidence_digest=f"{i + 1:064x}",
                executed=True,
            )
            for i, channel in enumerate(REQUIRED_Q_SAFETY_CHANNELS)
        ),
        execution_authorized=False,
        training_authorized=False,
        production_promotable=False,
    )
    values.update(overrides)
    return BoundAdapterQSafetyProofV1(**values)


def _minimal_conversion():
    measurement = np.array([[True, True, False], [True, False, True]], dtype=bool)
    hidden = np.array([[False, True, False], [False, False, True]], dtype=bool)
    model = SyntheticModelBatch(
        gene_ids=np.array([[0, 1, 2], [0, 1, 2]], dtype=np.int64),
        student_expression=np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]], dtype=np.float32),
        measurement_mask=measurement,
        hidden_target_mask=hidden,
    )
    operator = SyntheticOperatorContext(
        source_index=np.array([0, 0], dtype=np.int16),
        operator_index=np.array([0, 0], dtype=np.int16),
        visible_library_size=np.array([11.0, 7.0], dtype=np.float32),
        n_measured=np.array([2, 2], dtype=np.int32),
    )
    split = SyntheticSplitContext(donor_index=np.array([0, 1], dtype=np.int32))
    readout = SyntheticReadoutRecord(
        query_counts=np.array([[0.0, 3.0, 0.0], [0.0, 0.0, 5.0]], dtype=np.float32),
        full_library_size=np.array([14.0, 12.0], dtype=np.float32),
    )
    oracle = SyntheticOracleRecord(
        global_cell_index=np.array([101, 102], dtype=np.int64),
        latents={},
        b3_arm_membership=None,
        b6_ladder_level=None,
        substate=None,
        annotated_class=None,
    )
    return SyntheticConversion(
        model=model,
        operator_context=operator,
        split_context=split,
        readout=readout,
        oracle=oracle,
        global_cell_index=np.array([101, 102], dtype=np.int64),
        provenance={
            "observer_manifest_sha256": "d" * 64,
            "structural_support_rule": "name-mapped-registry-relative-v1",
            "observation_identity": {
                "source_roster": ["SEA_AD"],
                "operator_ids": ["op-a"],
                "operator_source_map": [["op-a", "SEA_AD"]],
                "donor_ids": ["d1", "d2"],
            },
        },
    )


def test_physical_row_value_binding_accepts_one_inseparable_chain():
    binding = _valid_binding()
    assert binding.expression_row == 91
    assert binding.consumed_values_sha256 == binding.authenticated_values_sha256


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"source_row_index": 7}, "source row"),
        ({"selected_block_row_index": 4}, "block row"),
        ({"source_cell_id": "cell-7"}, "cell identity"),
        ({"consumed_values_sha256": "c" * 64}, "consumed values"),
    ],
)
def test_physical_row_value_binding_rejects_historical_substitutions(overrides, message):
    with pytest.raises(ValueError, match=message):
        _valid_binding(**overrides)


def test_raw_source_and_operator_identity_do_not_reach_learnable_context():
    context = build_learnable_model_context(
        model_inputs={"student_expression": [[1.0, 0.0]], "measurement_mask": [[True, True]]},
        lawful_operator_context={
            "source_index": [4],
            "operator_index": [11],
            "visible_library_size": [37.0],
            "n_measured": [2],
        },
    )
    assert set(context.operator_context) == {"visible_library_size", "n_measured"}
    assert "source_index" not in context.operator_context
    assert "operator_index" not in context.operator_context


def test_unreviewed_measurement_identity_proxy_fails_closed():
    with pytest.raises(ValueError, match="unreviewed|operator context"):
        build_learnable_model_context(
            model_inputs={"student_expression": [[1.0]]},
            lawful_operator_context={
                "source_index": [4],
                "operator_index": [11],
                "visible_library_size": [37.0],
                "n_measured": [1],
                "dataset_embedding": [99],
            },
        )


def test_policy_only_q_safety_cannot_count_as_executed_joined_proof():
    gate = getattr(v77_join, "require_executed_q_safety", None)
    assert callable(gate), "V77 join has no execution-bound q-safety gate"
    with pytest.raises(ValueError, match="executed|q-safety"):
        gate(QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN)


def test_executed_status_enum_alone_cannot_mint_q_safety_proof():
    with pytest.raises(ValueError, match="typed|proof"):
        v77_join.require_executed_q_safety(
            QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME
        )


def test_q_safety_proof_is_bound_to_exact_adapter_batch_and_runtime():
    proof = _valid_q_safety_proof()
    accepted = v77_join.require_executed_q_safety(
        QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME,
        proof,
        adapter_id="v77-synthetic-batch-adapter",
        adapter_digest="a" * 64,
        batch_scientific_identity_digest="b" * 64,
        runtime_source_sha256="c" * 64,
    )
    assert accepted is proof

    for field, wrong in (
        ("adapter_id", "wrong-adapter"),
        ("adapter_digest", "d" * 64),
        ("batch_scientific_identity_digest", "e" * 64),
        ("runtime_source_sha256", "f" * 64),
    ):
        kwargs = dict(
            adapter_id="v77-synthetic-batch-adapter",
            adapter_digest="a" * 64,
            batch_scientific_identity_digest="b" * 64,
            runtime_source_sha256="c" * 64,
        )
        kwargs[field] = wrong
        with pytest.raises(ValueError, match="identity|digest|batch|runtime|adapter"):
            v77_join.require_executed_q_safety(
                QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME,
                proof,
                **kwargs,
            )


def test_actual_v77_conversion_builds_shared_qualification_batch():
    builder = getattr(v77_join, "build_qualification_batch_from_v77_conversion", None)
    assert callable(builder), "V77 conversion is not physically joined to QualificationBatchV1"
    batch = builder(
        _minimal_conversion(),
        feature_ids=("g0", "g1", "g2"),
        experiment_run_id="v77-joined-zero-update-001",
        adapter_id="v77-synthetic-batch-adapter",
        adapter_digest="a" * 64,
        code_commit="1234567890abcdef1234567890abcdef12345678",
        environment_digest="e" * 64,
        synthetic_realization_id="v77-dev-001",
        challenge_partition="DEVELOPMENT_CALIBRATION",
    )
    assert isinstance(batch, QualificationBatchV1)
    model_view = batch.model_view()
    readout_view = batch.readout_view()
    assert "student_expression" in model_view.model_inputs
    assert "measurement_mask" in model_view.model_inputs
    assert "hidden_target_mask" in model_view.model_inputs
    assert "query_counts" not in model_view.model_inputs
    assert "query_counts" in readout_view.readout_only
    assert "donor_index" in readout_view.split_only
    learnable = build_learnable_model_context(
        model_inputs=model_view.model_inputs,
        lawful_operator_context=model_view.lawful_operator_context,
    )
    assert "source_index" not in learnable.operator_context
    assert "operator_index" not in learnable.operator_context
