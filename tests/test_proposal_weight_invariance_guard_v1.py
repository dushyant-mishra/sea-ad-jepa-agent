import numpy as np
import pytest

from sea_ad_jepa.v5.proposal_weight_invariance_guard_v1 import (
    ProposalWeightInvarianceAuthorityV1,
    qualify_proposal_weight_invariance,
)


def authority():
    return ProposalWeightInvarianceAuthorityV1(
        authority_id="proposal-weight-invariance-v1",
        proposal_policy_authority_id="proposal-policy-v1",
        schedule_authority_id="schedule-v1",
        full_reader_expression_artifact_sha256="a" * 64,
        schedule_artifact_sha256="b" * 64,
        rules_frozen_before_optimizer_start=True,
    )


def test_repacking_can_reorder_presentations_but_not_change_identity_bound_weights():
    out = qualify_proposal_weight_invariance(
        reference_presentation_ids=["p0", "p1", "p2", "p3"],
        reference_weights=np.array([1.0, 2.0, 0.5, 4.0], dtype=np.float64),
        repacked_presentation_ids=["p2", "p0", "p3", "p1"],
        repacked_weights=np.array([0.5, 1.0, 4.0, 2.0], dtype=np.float64),
        authority=authority(),
    )
    assert out["passed"] is True
    assert out["packing_position_enters_weight"] is False
    assert out["training_authorized"] is False


def test_same_values_attached_to_wrong_identities_stop():
    with pytest.raises(RuntimeError, match="CHANGED_BY_REPACKING"):
        qualify_proposal_weight_invariance(
            reference_presentation_ids=["p0", "p1"],
            reference_weights=[1.0, 2.0],
            repacked_presentation_ids=["p1", "p0"],
            repacked_weights=[1.0, 2.0],
            authority=authority(),
        )


def test_missing_presentation_stops():
    with pytest.raises(RuntimeError, match="PRESENTATION_SET_MISMATCH"):
        qualify_proposal_weight_invariance(
            reference_presentation_ids=["p0", "p1"], reference_weights=[1.0, 2.0],
            repacked_presentation_ids=["p0", "p2"], repacked_weights=[1.0, 2.0],
            authority=authority(),
        )


def test_one_ulp_weight_change_stops():
    changed = np.nextafter(np.float64(2.0), np.float64(3.0))
    with pytest.raises(RuntimeError, match="CHANGED_BY_REPACKING"):
        qualify_proposal_weight_invariance(
            reference_presentation_ids=["p0", "p1"], reference_weights=[1.0, 2.0],
            repacked_presentation_ids=["p0", "p1"], repacked_weights=[1.0, changed],
            authority=authority(),
        )


def test_after_optimizer_freeze_claim_is_rejected():
    a = ProposalWeightInvarianceAuthorityV1(
        "x", "proposal", "schedule", "a" * 64, "b" * 64, False
    )
    with pytest.raises(ValueError, match="frozen before optimizer start"):
        qualify_proposal_weight_invariance(
            reference_presentation_ids=["p0"], reference_weights=[1.0],
            repacked_presentation_ids=["p0"], repacked_weights=[1.0], authority=a,
        )
