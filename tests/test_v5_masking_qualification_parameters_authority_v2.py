from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import (
    PRIMARY_ATTACKER_ID,
    PRIMARY_SCORE_ID,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v2 import (
    BURDEN_SEPARATION_POLICY_ID,
    CONFIRMATION_ROLE_ID,
    ORIGIN_POLICY_ID,
    MaskingQualificationParametersAuthorityV2,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_FULL104_CONFIRMATION_PARAMETERS_AUTHORITY_V2",
        primary_attacker_id=PRIMARY_ATTACKER_ID,
        primary_score_id=PRIMARY_SCORE_ID,
        targeted_partner_cap=8,
        ridge_candidate_pool_count=64,
        ridge_score_feature_count=32,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=20,
        prefix_floor_numerator=1,
        prefix_floor_denominator=20,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
        discovery_expanded_validation_report_sha256=h("report"),
        discovery_universe_scale_script_sha256=h("universe"),
        discovery_outside800_unified_script_sha256=h("outside"),
        discovery_provenance_note_sha256=h("provenance"),
        parameter_origin_policy_id=ORIGIN_POLICY_ID,
        confirmation_role_id=CONFIRMATION_ROLE_ID,
        burden_separation_policy_id=BURDEN_SEPARATION_POLICY_ID,
    )
    values.update(updates)
    return MaskingQualificationParametersAuthorityV2(**values)


def test_explicit_discovery_defined_confirmation_tuple_is_valid() -> None:
    a = authority()
    a.validate()
    assert a.ridge_alpha == pytest.approx(0.01)
    assert a.prefix_floor == pytest.approx(0.05)
    assert a.prefix_reduction == pytest.approx(0.5)


@pytest.mark.parametrize(
    "field,value",
    [
        ("targeted_partner_cap", 7),
        ("ridge_candidate_pool_count", 63),
        ("ridge_score_feature_count", 31),
        ("ridge_alpha_numerator", 2),
        ("prefix_candidate_count", 21),
        ("prefix_floor_numerator", 2),
        ("prefix_reduction_numerator", 2),
    ],
)
def test_parameter_drift_fails_closed(field: str, value: int) -> None:
    with pytest.raises(ValueError, match=field):
        authority(**{field: value}).validate()


def test_provenance_roots_must_be_real_and_distinct() -> None:
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(
            discovery_expanded_validation_report_sha256=same,
            discovery_universe_scale_script_sha256=same,
        ).validate()
    with pytest.raises(ValueError, match="SHA-256"):
        authority(discovery_provenance_note_sha256="placeholder").validate()


def test_terminal_outcomes_cannot_have_been_seen_before_parameter_freeze() -> None:
    with pytest.raises(ValueError, match="before terminal FULL104"):
        authority(terminal_full104_masking_outcomes_inspected=True).validate()


def test_burden_is_not_part_of_the_parameter_authority() -> None:
    fields = set(authority().__dataclass_fields__)
    assert "mask_fraction" not in fields
    assert "mask_fraction_numerator" not in fields
    assert "mask_fraction_denominator" not in fields
