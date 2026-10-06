import math
import pytest

from sea_ad_jepa.qualification.protocol import (
    APPROVED_V3_GOVERNANCE_DIGEST,
    ExecutionMode,
    QualificationProtocolV1,
    ThresholdStatus,
)


def _valid_protocol(**overrides):
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
        "transport_ood_axes": ("DONOR_TRANSFER", "BIOLOGICAL_SUPPORT_OOD"),
        "diagnostic_readout_firewall_id": "inner-train-freeze-v1",
        "unit_of_inference": "DONOR",
        "estimand_spec": "UNSET_REQUIRES_APPROVAL",
        "threshold_status": ThresholdStatus.UNSET_REQUIRES_APPROVAL,
        "deciding_numeric_thresholds": "UNSET_REQUIRES_APPROVAL",
        "execution_mode": ExecutionMode.ZERO_UPDATE_QUALIFICATION,
        "claim_ceiling": "RNA_REPRESENTATION",
    }
    values.update(overrides)
    return QualificationProtocolV1(**values)


def test_valid_protocol_binds_exact_governance_and_neutral_science():
    protocol = _valid_protocol()
    protocol.validate()
    assert protocol.governance_digest == "ab0603b0a9c92c3680badc252205ddd27fa74ae83ef3ada4019b4dcf637b7611"
    assert protocol.execution_mode is ExecutionMode.ZERO_UPDATE_QUALIFICATION
    assert protocol.estimand_spec == "UNSET_REQUIRES_APPROVAL"
    assert protocol.deciding_numeric_thresholds == "UNSET_REQUIRES_APPROVAL"
    assert len(protocol.digest()) == 64


def test_protocol_rejects_noncanonical_governance_digest():
    with pytest.raises(ValueError, match="governance"):
        _valid_protocol(governance_digest="0" * 64).validate()


def test_protocol_rejects_fifth_representation_family():
    with pytest.raises(ValueError, match="representation"):
        _valid_protocol(representation_family="UNAPPROVED_FIFTH_FAMILY").validate()


def test_unset_threshold_status_cannot_carry_deciding_thresholds():
    with pytest.raises(ValueError, match="threshold"):
        _valid_protocol(deciding_numeric_thresholds={"score": 0.8}).validate()


def test_protocol_requires_explicit_execution_mode():
    with pytest.raises(ValueError, match="execution_mode"):
        _valid_protocol(execution_mode=None).validate()


def test_canonical_digest_rejects_nonfinite_values():
    from sea_ad_jepa.qualification.canonical import canonical_digest

    with pytest.raises((TypeError, ValueError)):
        canonical_digest({"bad": math.nan})


def test_canonical_digest_rejects_opaque_objects():
    from sea_ad_jepa.qualification.canonical import canonical_digest

    with pytest.raises((TypeError, ValueError)):
        canonical_digest({"opaque": object()})
