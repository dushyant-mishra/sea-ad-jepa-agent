from dataclasses import replace
from pathlib import Path
import pytest

from sea_ad_jepa.v5.base_training_estimand_recovery_v1 import (
    EXPECTED_ESTIMAND_ID,
    EXPECTED_FULL_READER_REPLAY_SHA256,
    EXPECTED_OPERATOR_MASS_POLICY_ID,
    EXPECTED_POPULATION_AUTHORITY_SHA256,
    EXPECTED_PROPOSAL_SEPARATION_POLICY_ID,
    EXPECTED_SOURCE_MASS_POLICY_ID,
    EXPECTED_SUPPORT_ELIGIBILITY_SHA256,
    EXPECTED_SUPPORT_ESTIMABILITY_SHA256,
    EXPECTED_TARGET_AUTHORITY_SHA256,
    EXPECTED_TARGET_PROBABILITY_FORMULA,
    EXPECTED_WEIGHT_NORMALIZATION_ID,
    EXPECTED_WEIGHT_UNIT_ID,
    RecoveredScientificWeightLawV1,
    build_current_recovered_base_estimand_v1,
    validate_current_recovered_base_estimand_v1,
)


def law() -> RecoveredScientificWeightLawV1:
    return RecoveredScientificWeightLawV1(
        authority_id="JEPA_V5_RECOVERED_BASE_TRAINING_SCIENTIFIC_WEIGHT_LAW_V1",
        source_scientific_target_authority_sha256=EXPECTED_TARGET_AUTHORITY_SHA256,
        source_full_reader_replay_sha256=EXPECTED_FULL_READER_REPLAY_SHA256,
        population_authority_sha256=EXPECTED_POPULATION_AUTHORITY_SHA256,
        support_estimability_authority_sha256=EXPECTED_SUPPORT_ESTIMABILITY_SHA256,
        support_eligibility_authority_sha256=EXPECTED_SUPPORT_ELIGIBILITY_SHA256,
        estimand_id=EXPECTED_ESTIMAND_ID,
        target_probability_formula=EXPECTED_TARGET_PROBABILITY_FORMULA,
        weight_normalization_id=EXPECTED_WEIGHT_NORMALIZATION_ID,
        weight_unit_id=EXPECTED_WEIGHT_UNIT_ID,
        source_mass_policy_id=EXPECTED_SOURCE_MASS_POLICY_ID,
        operator_mass_policy_id=EXPECTED_OPERATOR_MASS_POLICY_ID,
        proposal_separation_policy_id=EXPECTED_PROPOSAL_SEPARATION_POLICY_ID,
    )


def test_recovered_law_builds_exact_current_base_estimand():
    weight_law=law(); weight_law.validate_current_binding()
    authority=build_current_recovered_base_estimand_v1(weight_law)
    validate_current_recovered_base_estimand_v1(weight_law,authority)
    assert authority.estimand_id == EXPECTED_ESTIMAND_ID
    assert authority.scientific_weight_artifact_sha256 == weight_law.canonical_digest()
    assert authority.training_authorized is False

@pytest.mark.parametrize("field,bad",[
    ("estimand_id","EMPIRICAL_FULL104_CELL_UNIFORM"),
    ("estimand_id","SOURCE_UNIFORM"),
    ("estimand_id","DONOR_PRIMARY_OPERATOR_BALANCED"),
    ("operator_mass_policy_id","EQUAL_OPERATOR_MASS"),
    ("source_mass_policy_id","SOURCE_UNIFORM_OBJECTIVE_MASS"),
    ("target_probability_formula","1/N_cells"),
    ("population_authority_sha256","0"*64),
    ("support_estimability_authority_sha256","1"*64),
    ("support_eligibility_authority_sha256","2"*64),
    ("source_scientific_target_authority_sha256","3"*64),
    ("source_full_reader_replay_sha256","4"*64),
])
def test_recovered_law_rejects_semantic_or_provenance_substitution(field,bad):
    with pytest.raises(ValueError,match="current recovered estimand binding mismatch"):
        replace(law(),**{field:bad}).validate_current_binding()


def test_recovered_law_cannot_authorize_training():
    with pytest.raises(ValueError,match="cannot authorize training"):
        replace(law(),training_authorized=True).validate()


def test_generic_authority_weight_root_splice_is_rejected():
    weight_law=law(); authority=build_current_recovered_base_estimand_v1(weight_law)
    bad=replace(authority,scientific_weight_artifact_sha256="f"*64)
    with pytest.raises(ValueError,match="does not match recovered"):
        validate_current_recovered_base_estimand_v1(weight_law,bad)


def test_recovery_source_has_no_mechanics_or_dimension_carryover():
    source=Path("src/sea_ad_jepa/v5/base_training_estimand_recovery_v1.py").read_text(encoding="utf-8")
    forbidden=(
        "full104_dimension_interface",
        "alpha_target",
        "gamma_source_uniform",
        "presentation_horizon",
        "physical_batch_size",
        "PRODUCTION_CONFIG",
        "production_update",
        "0.996",
        "mask_fraction",
        "target_blocks",
    )
    assert [token for token in forbidden if token in source] == []
