from dataclasses import FrozenInstanceError
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
from sea_ad_jepa.qualification.protocol import (
    APPROVED_V3_GOVERNANCE_DIGEST,
    ExecutionMode,
    QualificationProtocolV1,
    ThresholdStatus,
)


def _protocol(**overrides):
    values = {
        "governance_digest": APPROVED_V3_GOVERNANCE_DIGEST,
        "qualification_contract_version": "qualification-v1",
        "runtime_interface_version": "runtime-interface-v1",
        "representation_family": "GLOBAL_CELL_STATE",
        "target_evidence_construction_id": "synthetic-mechanics-target-v1",
        "q_safety_policy_id": "qsafe-v1",
        "observation_operator_policy_id": "observation-operator-v1",
        "biological_evidence_operator_id": "feature-context-support-restriction-v1",
        "measurement_depth_operator_id": "count-depth-thinning-v1",
        "split_resampling_protocol_id": "donor-primary-v1",
        "representation_stability_protocol_id": "stability-v1",
        "transport_ood_axes": ("DONOR_TRANSFER",),
        "diagnostic_readout_firewall_id": "inner-train-freeze-v1",
        "unit_of_inference": "DONOR",
        "estimand_spec": "UNSET_REQUIRES_APPROVAL",
        "threshold_status": ThresholdStatus.UNSET_REQUIRES_APPROVAL,
        "deciding_numeric_thresholds": "UNSET_REQUIRES_APPROVAL",
        "exploratory_thresholds": (),
        "execution_mode": ExecutionMode.ZERO_UPDATE_QUALIFICATION,
        "claim_ceiling": "RNA_REPRESENTATION",
    }
    values.update(overrides)
    protocol = QualificationProtocolV1(**values)
    protocol.validate()
    return protocol


def _synthetic_bundle(protocol=None, **claim_overrides):
    protocol = protocol or _protocol()
    scientific = ScientificExperimentAuthorityV1(
        protocol_digest=protocol.digest(),
        scope=ExperimentScope.SYNTHETIC_PIPELINE_VALIDITY,
        evaluation_authorized=True,
    )
    mutation = MutationAuthorityV1(status=MutationStatus.MUTATION_NOT_AUTHORIZED)
    claim = ClaimAuthorityV1(
        maximum_claim_level=claim_overrides.get(
            "maximum_claim_level", ClaimLevel.SYNTHETIC_PIPELINE_VALIDITY
        )
    )
    return AuthorityBundleV1(scientific=scientific, mutation=mutation, claim=claim)


def test_v1_mutation_authority_vocabulary_is_structurally_off_only():
    assert tuple(MutationStatus) == (MutationStatus.MUTATION_NOT_AUTHORIZED,)
    with pytest.raises(ValueError, match="mutation"):
        MutationAuthorityV1(status="MUTATION_AUTHORIZED")  # type: ignore[arg-type]


def test_valid_synthetic_zero_update_bundle_passes():
    protocol = _protocol()
    bundle = _synthetic_bundle(protocol)
    bundle.validate_against(protocol)


def test_bounded_mutation_request_has_no_compatible_v1_authority():
    protocol = _protocol(execution_mode=ExecutionMode.BOUNDED_MUTATION_REHEARSAL)
    with pytest.raises(ValueError, match="mutation"):
        _synthetic_bundle(protocol).validate_against(protocol)


def test_synthetic_evidence_cannot_auto_promote_to_real_rna_claim():
    protocol = _protocol()
    with pytest.raises(ValueError, match="synthetic"):
        _synthetic_bundle(
            protocol, maximum_claim_level=ClaimLevel.RNA_REPRESENTATION
        ).validate_against(protocol)


def test_claim_cannot_exceed_protocol_claim_ceiling():
    protocol = _protocol()
    scientific = ScientificExperimentAuthorityV1(
        protocol_digest=protocol.digest(),
        scope=ExperimentScope.REAL_RNA_PREFREEZE_ONLY,
        evaluation_authorized=False,
    )
    bundle = AuthorityBundleV1(
        scientific=scientific,
        mutation=MutationAuthorityV1(MutationStatus.MUTATION_NOT_AUTHORIZED),
        claim=ClaimAuthorityV1(ClaimLevel.TRANSFERABLE_BIOLOGICAL_STATE),
    )
    with pytest.raises(ValueError, match="claim ceiling"):
        bundle.validate_against(protocol)


def test_real_rna_stage_a_cannot_be_authorized_by_this_slice():
    protocol = _protocol()
    with pytest.raises(ValueError, match="Stage A"):
        ScientificExperimentAuthorityV1(
            protocol_digest=protocol.digest(),
            scope=ExperimentScope.REAL_RNA_PREFREEZE_ONLY,
            evaluation_authorized=True,
        )


def test_mechanics_success_has_no_claim_promotion_api_and_authorities_are_frozen():
    bundle = _synthetic_bundle()
    assert not hasattr(bundle, "promote_claim_from_mechanics")
    with pytest.raises(FrozenInstanceError):
        bundle.claim = ClaimAuthorityV1(ClaimLevel.RNA_REPRESENTATION)  # type: ignore[misc]
