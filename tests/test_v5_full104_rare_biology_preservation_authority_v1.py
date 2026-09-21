from __future__ import annotations

import dataclasses
import hashlib

import pytest

from sea_ad_jepa.v5.full104_rare_biology_preservation_authority_v1 import (
    Full104RareBiologyPreservationAuthorityV1,
)


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def authority(**updates) -> Full104RareBiologyPreservationAuthorityV1:
    values = dict(
        authority_id="TEST_FULL104_RARE_BIOLOGY_PRESERVATION",
        full104_population_authority_sha256=h("population"),
        dataset_etl_atlas_sha256=h("etl"),
        td59_protocol_sha256=h("td59"),
        teacher_relational_target_authority_sha256=h("teacher-relational"),
        selector_id="TD59_Z_NEAREST_HALF_BOUNDARY_DISTANCE_V1",
        stratification_id=(
            "WITHIN_DONOR_OPERATOR__OPERATOR_DOES_NOT_SET_OBJECTIVE_MASS_V1"
        ),
        tail_id="Q95_ISOLATION_TAIL__MIN5_ANCHORS_V1",
        molecular_gate_id=(
            "FULL104_XY_RELATIONAL_RECURRENCE_REQUIRED_BEFORE_TEACHER_TAIL_CLAIM_V1"
        ),
        null_id="TD59_MATCHED_WRONG_CELL_Y_NULL__64_REPLICATES_V1",
        primary_weighting_id="DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1",
        label_firewall_id=(
            "NO_PATHOLOGY_DISEASE_NATIVE_CLASS_OR_RARE_STATE_LABEL_IN_TAIL_SELECTION_V1"
        ),
    )
    values.update(updates)
    return Full104RareBiologyPreservationAuthorityV1(**values)


def test_v1_is_prospective_and_nonexecuting() -> None:
    a = authority()
    a.validate()
    assert a.molecular_prequalification_complete is False
    assert a.teacher_tail_evaluation_authorized is False
    assert a.training_authorized is False
    assert len(a.canonical_digest()) == 64


@pytest.mark.parametrize(
    "field",
    [
        "pathology_labels_used",
        "disease_labels_used",
        "native_class_labels_used",
        "rare_state_labels_used",
    ],
)
def test_no_biological_label_can_define_tail(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        authority(**{field: True}).validate()


def test_q95_and_historical_minimum_are_frozen_before_outcomes() -> None:
    with pytest.raises(ValueError, match="q95"):
        authority(tail_quantile=0.90).validate()
    with pytest.raises(ValueError, match="frozen at 5"):
        authority(min_tail_anchors=4).validate()


def test_td59_null_and_donor_level_measurability_are_frozen() -> None:
    with pytest.raises(ValueError, match="null_replicates"):
        authority(null_replicates=63).validate()
    with pytest.raises(ValueError, match="min_resolved_triplets_per_donor"):
        authority(min_resolved_triplets_per_donor=19).validate()
    with pytest.raises(ValueError, match="min_measurable_donors_per_half"):
        authority(min_measurable_donors_per_half=3).validate()


def test_v1_cannot_promote_itself_after_outcomes() -> None:
    with pytest.raises(ValueError, match="cannot self-declare"):
        authority(molecular_prequalification_complete=True).validate()
    with pytest.raises(ValueError, match="teacher tail evaluation is forbidden"):
        authority(teacher_tail_evaluation_authorized=True).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()


def test_scientific_roots_are_digest_bearing() -> None:
    base = authority()
    changed = dataclasses.replace(base, td59_protocol_sha256=h("other-td59"))
    assert base.canonical_digest() != changed.canonical_digest()
