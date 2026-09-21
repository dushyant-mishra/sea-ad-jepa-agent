from __future__ import annotations

import dataclasses
import hashlib

import pytest

from sea_ad_jepa.v5.full104_teacher_relational_target_qualification_authority_v1 import (
    Full104TeacherRelationalTargetQualificationAuthorityV1,
    require_source_complete_relational_gate_v1,
)


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def authority(**updates) -> Full104TeacherRelationalTargetQualificationAuthorityV1:
    values = dict(
        authority_id="TEST_FULL104_RELATIONAL_TARGET_AUTHORITY",
        full104_population_authority_sha256=h("population"),
        canonical_address_registry_sha256=h("registry"),
        operator_address_support_authority_sha256=h("support"),
        dataset_etl_atlas_sha256=h("etl"),
        scientific_weight_law_sha256=h("weight"),
        teacher_target_semantics_authority_sha256=h("semantics"),
        td57b_protocol_sha256=h("td57b"),
        td59_protocol_sha256=h("td59"),
        td60_legacy_prospective_protocol_sha256=h("td60"),
        state_semantics_id="BIOLOGICAL_CELLULAR_LATENT_STATE_V1",
        teacher_state_id="EMA_DIRECT_CELL_STATE__NO_PROJECTION_HEAD_V1",
        primary_weighting_id="DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1",
        source_policy_id=(
            "SOURCE_IS_ROBUSTNESS_STRATUM__ALL_THREE_SOURCES_REPORTED_SEPARATELY_V1"
        ),
        relational_policy_id=(
            "TD57B_GLOBAL_PLUS_TD59_NEAREST_HALF_MESOSCALE__NO_NEW_SEARCH_V1"
        ),
        rare_biology_policy_id=(
            "RARE_BIOLOGY_PROTECTED_BY_DONOR_RECURRENCE__NO_RARE_LABEL_TARGET_V1"
        ),
        label_firewall_id=(
            "NO_PATHOLOGY_DISEASE_NATIVE_CLASS_OR_RARE_STATE_LABEL_IN_TARGET_CONSTRUCTION_V1"
        ),
        locality_policy_id=(
            "TD59_NEAREST_HALF_ONLY__TD57C_NEAREST_THIRD_REMAINS_FAILED_V1"
        ),
        promotion_policy_id=(
            "RELATIONAL_CONTINUITY_REQUIRED_BEFORE_TEACHER_CELL_STATE_TARGET_AUTHORITY_V1"
        ),
    )
    values.update(updates)
    return Full104TeacherRelationalTargetQualificationAuthorityV1(**values)


def test_current_full104_authority_validates_and_digests() -> None:
    a = authority()
    a.validate()
    assert len(a.canonical_digest()) == 64
    assert a.training_authorized is False


def test_cell_count_dominance_cannot_become_scientific_weighting() -> None:
    with pytest.raises(ValueError, match="primary_weighting_id"):
        authority(primary_weighting_id="CELL_UNIFORM_ACROSS_4P55M").validate()
    with pytest.raises(ValueError, match="cell_uniform_population_weighting_allowed"):
        authority(cell_uniform_population_weighting_allowed=True).validate()
    with pytest.raises(ValueError, match="source_cell_mass_weighting_allowed"):
        authority(source_cell_mass_weighting_allowed=True).validate()


@pytest.mark.parametrize(
    "field",
    [
        "pathology_labels_allowed_in_target",
        "disease_labels_allowed_in_target",
        "native_class_labels_allowed_in_target",
        "rare_state_labels_allowed_in_target",
    ],
)
def test_labels_cannot_define_teacher_target(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        authority(**{field: True}).validate()


def test_historical_search_space_cannot_be_reopened_silently() -> None:
    with pytest.raises(ValueError, match="new_gene_panel_search_allowed"):
        authority(new_gene_panel_search_allowed=True).validate()
    with pytest.raises(ValueError, match="new_locality_search_allowed"):
        authority(new_locality_search_allowed=True).validate()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reader_fit_cells", 4_553_406),
        ("reader_fit_donors", 103),
        ("operators", 41),
        ("source_donors", (("HVS", 41), ("NPH52", 18), ("SEA_AD", 45))),
    ],
)
def test_authenticated_full104_geometry_is_not_reinterpreted(field: str, value) -> None:
    with pytest.raises(ValueError, match="drifted"):
        authority(**{field: value}).validate()


def test_all_three_sources_must_be_visible_to_the_decision() -> None:
    require_source_complete_relational_gate_v1(
        {"HVS": True, "NPH52": True, "SEA_AD": True}
    )
    with pytest.raises(ValueError, match="requires exactly"):
        require_source_complete_relational_gate_v1(
            {"HVS": True, "SEA_AD": True}
        )
    with pytest.raises(ValueError, match="failed or was not estimable"):
        require_source_complete_relational_gate_v1(
            {"HVS": True, "NPH52": False, "SEA_AD": True}
        )


def test_root_changes_change_canonical_scientific_state() -> None:
    base = authority()
    changed = dataclasses.replace(base, dataset_etl_atlas_sha256=h("etl-changed"))
    assert base.canonical_digest() != changed.canonical_digest()


def test_outcome_adaptation_and_training_are_forbidden() -> None:
    with pytest.raises(ValueError, match="relational_outcomes_inspected_before_freeze"):
        authority(relational_outcomes_inspected_before_freeze=True).validate()
    with pytest.raises(ValueError, match="training_authorized"):
        authority(training_authorized=True).validate()
