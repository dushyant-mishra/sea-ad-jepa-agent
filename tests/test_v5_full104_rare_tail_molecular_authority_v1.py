import dataclasses

import pytest

from sea_ad_jepa.v5.full104_rare_tail_molecular_authority_v1 import (
    FAIL_TERMINAL,
    NOT_ESTIMABLE_TERMINAL,
    PASS_TERMINAL,
    STRUCTURAL_PREFLIGHT_SHA256,
    Full104RareTailMolecularAuthorityV1,
    case_pass,
    full_gate_terminal,
)


def authority(**updates) -> Full104RareTailMolecularAuthorityV1:
    values = dict(
        authority_id="JEPA_V5_FULL104_RARE_TAIL_MOLECULAR_AUTHORITY_V1"
    )
    values.update(updates)
    return Full104RareTailMolecularAuthorityV1(**values)


def test_authority_is_executable_for_molecular_gate_only() -> None:
    a = authority()
    a.validate()
    assert a.structural_preflight_sha256 == STRUCTURAL_PREFLIGHT_SHA256
    assert a.molecular_execution_authorized is True
    assert a.teacher_tail_evaluation_authorized is False
    assert a.td60_authorized is False
    assert a.training_authorized is False
    assert a.required_cases == 24
    assert len(a.canonical_digest()) == 64


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("locality_denominator", 3, "locality_denominator drifted"),
        ("tail_denominator", 10, "tail_denominator drifted"),
        ("triplets_per_stratum_cap", 65, "triplets_per_stratum_cap drifted"),
        ("min_resolved_triplets_per_donor", 19, "min_resolved_triplets_per_donor drifted"),
        ("null_replicates", 63, "null_replicates drifted"),
        ("min_measurable_donors_per_case", 3, "min_measurable_donors_per_case drifted"),
        ("required_cases", 23, "required_cases drifted"),
    ],
)
def test_molecular_mechanics_cannot_drift(field, value, match) -> None:
    with pytest.raises(ValueError, match=match):
        authority(**{field: value}).validate()


def test_structural_receipt_cannot_be_rebound() -> None:
    with pytest.raises(ValueError, match="structural_preflight_sha256"):
        authority(structural_preflight_sha256="0" * 64).validate()


@pytest.mark.parametrize(
    "field",
    [
        "expression_selection_allowed",
        "pathology_labels_allowed",
        "disease_labels_allowed",
        "native_class_labels_allowed",
        "broad_class_labels_allowed",
        "rare_state_labels_allowed",
        "teacher_tail_evaluation_authorized",
        "td60_authorized",
        "training_authorized",
    ],
)
def test_forbidden_scope_stays_false(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        authority(**{field: True}).validate()


def test_case_gate_is_strictly_above_half_and_strictly_above_null_p95() -> None:
    nulls = tuple([0.4] * 61 + [0.45] * 3)
    assert case_pass(
        observed_median_donor_agreement=0.5000001,
        null_values=nulls,
    ) is True
    assert case_pass(
        observed_median_donor_agreement=0.5,
        null_values=nulls,
    ) is False

    # sorted index 60 is 0.4 for this vector. Equality does not pass.
    assert case_pass(
        observed_median_donor_agreement=0.4,
        null_values=nulls,
    ) is False


def test_case_gate_requires_exactly_64_finite_nulls() -> None:
    with pytest.raises(ValueError, match="exactly 64"):
        case_pass(observed_median_donor_agreement=0.7, null_values=(0.4,) * 63)
    with pytest.raises(ValueError, match="finite"):
        case_pass(
            observed_median_donor_agreement=0.7,
            null_values=(0.4,) * 63 + (float("nan"),),
        )


def test_full_gate_requires_24_of_24_and_not_estimable_dominates() -> None:
    assert full_gate_terminal(("PASS",) * 24) == PASS_TERMINAL
    assert full_gate_terminal(("PASS",) * 23 + ("FAIL",)) == FAIL_TERMINAL
    assert (
        full_gate_terminal(("PASS",) * 22 + ("FAIL", "NOT_ESTIMABLE"))
        == NOT_ESTIMABLE_TERMINAL
    )
    with pytest.raises(ValueError, match="exactly 24"):
        full_gate_terminal(("PASS",) * 23)


def test_authority_digest_changes_if_identity_changes() -> None:
    a = authority()
    b = dataclasses.replace(a, authority_id="OTHER")
    assert a.canonical_digest() != b.canonical_digest()
