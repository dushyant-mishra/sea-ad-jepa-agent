import pytest

from sea_ad_jepa.v5.null_mobility_audit_v1 import audit_blocked_permutation_v1


PARENT = "a" * 64
SEED = "b" * 64


def test_valid_within_block_permutation_reports_complete_mobility_without_authorizing_dshared():
    out = audit_blocked_permutation_v1(
        block_labels=["d0", "d0", "d1", "d1"],
        permutation=[1, 0, 3, 2],
        parent_sha256=PARENT,
        rng_binding_sha256=SEED,
        min_changed_fraction=0.80,
    )
    assert out["population_count"] == 4
    assert out["eligible_count"] == 4
    assert out["changed_count"] == 4
    assert out["identity_count"] == 0
    assert out["changed_fraction_of_eligible"] == 1.0
    assert out["null_mobility_qualifying"] is True
    assert out["d_shared_real_outcome_access_authorized"] is False
    assert out["training_authorized"] is False


def test_singletons_are_reported_nonmovable_not_silently_dropped():
    out = audit_blocked_permutation_v1(
        block_labels=["a", "a", "singleton"],
        permutation=[1, 0, 2],
        parent_sha256=PARENT,
        rng_binding_sha256=SEED,
        min_changed_fraction=0.90,
    )
    assert out["population_count"] == 3
    assert out["eligible_count"] == 2
    assert out["noneligible_count"] == 1
    assert out["changed_count"] == 2
    assert out["population_changed_fraction"] == pytest.approx(2 / 3)
    assert out["changed_fraction_of_eligible"] == 1.0


def test_identity_null_is_visible_and_nonqualifying():
    out = audit_blocked_permutation_v1(
        block_labels=["a", "a", "b", "b"],
        permutation=[0, 1, 2, 3],
        parent_sha256=PARENT,
        rng_binding_sha256=SEED,
        min_changed_fraction=0.50,
    )
    assert out["changed_count"] == 0
    assert out["identity_count"] == 4
    assert out["null_mobility_qualifying"] is False


def test_duplicate_missing_or_cross_block_indices_fail_closed():
    common = dict(
        block_labels=["a", "a", "b", "b"],
        parent_sha256=PARENT,
        rng_binding_sha256=SEED,
        min_changed_fraction=0.50,
    )
    with pytest.raises(RuntimeError, match="STOP_NULL_MOBILITY_NOT_BIJECTION"):
        audit_blocked_permutation_v1(permutation=[0, 0, 2, 3], **common)
    with pytest.raises(RuntimeError, match="STOP_NULL_MOBILITY_CROSS_BLOCK"):
        audit_blocked_permutation_v1(permutation=[2, 3, 0, 1], **common)


def test_outcome_feedback_or_authority_escalation_is_forbidden():
    common = dict(
        block_labels=["a", "a"],
        permutation=[1, 0],
        parent_sha256=PARENT,
        rng_binding_sha256=SEED,
        min_changed_fraction=0.50,
    )
    for field in (
        "d_shared_outcomes_used",
        "protected_data_used",
        "pathology_used",
        "checkpoint_outcomes_used",
        "training_authorized",
    ):
        with pytest.raises(RuntimeError, match="STOP_NULL_MOBILITY_FORBIDDEN"):
            audit_blocked_permutation_v1(**common, **{field: True})


def test_threshold_and_hashes_are_explicit_and_valid():
    common = dict(block_labels=["a", "a"], permutation=[1, 0], rng_binding_sha256=SEED)
    with pytest.raises(ValueError):
        audit_blocked_permutation_v1(**common, parent_sha256="bad", min_changed_fraction=0.5)
    with pytest.raises(ValueError):
        audit_blocked_permutation_v1(**common, parent_sha256=PARENT, min_changed_fraction=-0.1)
    with pytest.raises(ValueError):
        audit_blocked_permutation_v1(**common, parent_sha256=PARENT, min_changed_fraction=1.1)
