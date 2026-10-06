import pytest

from sea_ad_jepa.qualification.authorities import (
    AuthorityBundleV1,
    ClaimAuthorityV1,
    ClaimLevel,
    ExperimentScope,
    MutationAuthorityV1,
    MutationStatus,
    ScientificExperimentAuthorityV1,
)
from sea_ad_jepa.qualification.canonical import canonical_digest
from sea_ad_jepa.qualification.identity import FeatureIdentityReceiptV1, QualificationBatchIdentityV1
from sea_ad_jepa.qualification.pipeline import (
    BatchFieldV1,
    QualificationBatchV1,
    ZeroUpdateViolation,
    run_zero_update_qualification,
)
from sea_ad_jepa.qualification.protocol import (
    APPROVED_V3_GOVERNANCE_DIGEST,
    ExecutionMode,
    QualificationProtocolV1,
    ThresholdStatus,
)
from sea_ad_jepa.qualification.qsafe import QSafetyPolicyV1, REQUIRED_Q_SAFETY_CHANNELS
from sea_ad_jepa.qualification.visibility import FieldDeclaration, VisibilityClass


def _protocol(**overrides):
    values = {
        "governance_digest": APPROVED_V3_GOVERNANCE_DIGEST,
        "qualification_contract_version": "qualification-v1",
        "runtime_interface_version": "runtime-interface-v1",
        "representation_family": "GLOBAL_CELL_STATE",
        "target_evidence_construction_id": "synthetic-target-v1",
        "q_safety_policy_id": "qsafe-v1",
        "observation_operator_policy_id": "operator-v1",
        "biological_evidence_operator_id": "evidence-v1",
        "measurement_depth_operator_id": "depth-v1",
        "split_resampling_protocol_id": "donor-primary-v1",
        "representation_stability_protocol_id": "stability-v1",
        "transport_ood_axes": ("DONOR_TRANSFER",),
        "diagnostic_readout_firewall_id": "readout-firewall-v1",
        "unit_of_inference": "DONOR",
        "estimand_spec": "DONOR_WEIGHTED",
        "threshold_status": ThresholdStatus.EXPLORATORY_ONLY,
        "deciding_numeric_thresholds": "UNSET_REQUIRES_APPROVAL",
        "exploratory_thresholds": (("score", 0.8),),
        "execution_mode": ExecutionMode.ZERO_UPDATE_QUALIFICATION,
        "claim_ceiling": "RNA_REPRESENTATION",
    }
    values.update(overrides)
    p = QualificationProtocolV1(**values)
    p.validate()
    return p


def _authorities(protocol):
    return AuthorityBundleV1(
        scientific=ScientificExperimentAuthorityV1(
            protocol_digest=protocol.digest(),
            scope=ExperimentScope.SYNTHETIC_PIPELINE_VALIDITY,
            evaluation_authorized=True,
        ),
        mutation=MutationAuthorityV1(MutationStatus.MUTATION_NOT_AUTHORIZED),
        claim=ClaimAuthorityV1(ClaimLevel.SYNTHETIC_PIPELINE_VALIDITY),
    )


def _batch(protocol, *, inference_unit="DONOR", extra_fields=()):
    features = ("g1", "g2", "g3")
    feature_receipt = FeatureIdentityReceiptV1.from_ordered_ids(
        registry_ids=features,
        reader_axis_ids=features,
        tokenizer_axis_ids=features,
        tensor_feature_axis_ids=features,
        synthetic=True,
    )
    identity = QualificationBatchIdentityV1(
        observation_ids=("c1", "c2", "c3"),
        feature_receipt_digest=feature_receipt.digest(),
        query_spec_digest=canonical_digest({"q": "g2"}),
        evidence_mask_digest=canonical_digest([1, 0, 1]),
        measurement_mask_digest=canonical_digest([1, 1, 1]),
        operator_context_digest=canonical_digest({"depth": "low"}),
        evaluation_weight_digest=canonical_digest([1.0, 1.0, 1.0]),
        grouping_digest=canonical_digest(["d1", "d1", "d2"]),
        split_digest=canonical_digest(["inner", "inner", "held"]),
        target_spec_digest=canonical_digest({"target": "synthetic-target-v1"}),
    )
    fields = (
        BatchFieldV1(FieldDeclaration("expression", VisibilityClass.MODEL_VISIBLE), (1.0, 2.0, 3.0)),
        BatchFieldV1(FieldDeclaration("normalization_context", VisibilityClass.PREPROCESSING_VISIBLE), "q-safe-only"),
        BatchFieldV1(FieldDeclaration("depth", VisibilityClass.LAWFUL_OPERATOR_CONTEXT), "low"),
        BatchFieldV1(FieldDeclaration("donor_id", VisibilityClass.SPLIT_ONLY), ("d1", "d1", "d2")),
        BatchFieldV1(FieldDeclaration("diagnostic_label", VisibilityClass.READOUT_ONLY), (0, 1, 0)),
        BatchFieldV1(FieldDeclaration("source_file", VisibilityClass.PROVENANCE_ONLY), "synthetic://v77"),
    ) + tuple(extra_fields)
    return QualificationBatchV1(
        experiment_run_id="run-zero-001",
        adapter_id="v77-adapter-v1",
        adapter_digest="1" * 64,
        feature_identity_receipt=feature_receipt,
        scientific_identity=identity,
        q_safety_policy=QSafetyPolicyV1(REQUIRED_Q_SAFETY_CHANNELS),
        fields=fields,
        inference_unit=inference_unit,
        inference_group_ids=("d1", "d1", "d2"),
        code_commit="1234567890abcdef1234567890abcdef12345678",
        environment_digest="2" * 64,
        synthetic_realization_id="v77-challenge-001",
        challenge_partition="DEVELOPMENT_CALIBRATION",
    )


def test_zero_update_runner_exposes_filtered_views_and_freezes_outputs():
    protocol = _protocol()
    seen = {}

    def representation_fn(model_view):
        seen["model"] = tuple(sorted(model_view.model_inputs))
        seen["operator"] = tuple(sorted(model_view.lawful_operator_context))
        assert not hasattr(model_view, "preprocessing_context")
        assert "donor_id" not in model_view.model_inputs
        assert "diagnostic_label" not in model_view.model_inputs
        return {"embedding": [0.1, 0.2]}

    def readout_fn(representation, readout_view):
        seen["readout"] = tuple(sorted(readout_view.readout_only))
        assert "diagnostic_label" in readout_view.readout_only
        assert "source_file" not in readout_view.readout_only
        return {"score": 0.5, "embedding": representation["embedding"]}

    frozen = run_zero_update_qualification(
        protocol, _authorities(protocol), _batch(protocol), representation_fn, readout_fn
    )
    assert frozen.run_id == "run-zero-001"
    assert len(frozen.output_digest) == 64
    assert len(frozen.provenance_receipt_digest) == 64
    assert seen["model"] == ("expression",)
    assert seen["operator"] == ("depth",)


def test_oracle_only_field_is_physically_rejected_from_ordinary_batch():
    protocol = _protocol()
    oracle_field = BatchFieldV1(
        FieldDeclaration("z_reg_private", VisibilityClass.ORACLE_ONLY), "sealed"
    )
    with pytest.raises(ValueError, match="ORACLE_ONLY"):
        _batch(protocol, extra_fields=(oracle_field,))


def test_donor_inference_protocol_rejects_cell_only_grouping_metadata():
    protocol = _protocol()
    with pytest.raises(ValueError, match="unit of inference"):
        run_zero_update_qualification(
            protocol, _authorities(protocol), _batch(protocol, inference_unit="CELL"),
            lambda view: {"embedding": [0.0]}, lambda rep, view: {"score": 0.0},
        )


def test_mutation_or_ema_signal_from_callback_is_hard_failure():
    protocol = _protocol()
    with pytest.raises(ZeroUpdateViolation, match="mutation"):
        run_zero_update_qualification(
            protocol, _authorities(protocol), _batch(protocol),
            lambda view: {"optimizer_event": "step", "embedding": [0.0]},
            lambda rep, view: {"score": 0.0},
        )
    with pytest.raises(ZeroUpdateViolation, match="EMA"):
        run_zero_update_qualification(
            protocol, _authorities(protocol), _batch(protocol),
            lambda view: {"embedding": [0.0]},
            lambda rep, view: {"ema_event": "updated", "score": 0.0},
        )


def test_bounded_mutation_protocol_cannot_run_through_zero_update_runner():
    protocol = _protocol(execution_mode=ExecutionMode.BOUNDED_MUTATION_REHEARSAL)
    with pytest.raises(ZeroUpdateViolation, match="ZERO_UPDATE"):
        run_zero_update_qualification(
            protocol, _authorities(protocol), _batch(protocol),
            lambda view: {"embedding": [0.0]}, lambda rep, view: {"score": 0.0},
        )
