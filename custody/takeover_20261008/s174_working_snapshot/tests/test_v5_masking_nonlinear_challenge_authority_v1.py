from dataclasses import MISSING
import hashlib
import pytest

from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v1 import (
    CHALLENGE_ID, DONOR_WEIGHTING_POLICY_ID, MODEL_FAMILY_ID,
    RETUNING_POLICY_ID, SAMPLING_POLICY_ID, NonlinearMaskingChallengeAuthorityV1,
)


def h(name):
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="TEST",
        primary_parameters_authority_sha256=h("parameters"),
        outer_split_authority_sha256=h("split"),
        target_panel_authority_sha256=h("panel"),
        challenge_id=CHALLENGE_ID,
        model_family_id=MODEL_FAMILY_ID,
        sampling_policy_id=SAMPLING_POLICY_ID,
        donor_weighting_policy_id=DONOR_WEIGHTING_POLICY_ID,
        retuning_policy_id=RETUNING_POLICY_ID,
        feature_count=3,
        max_cells_per_donor=3,
        learning_rate_numerator=1,
        learning_rate_denominator=10,
        max_iter=5,
        max_leaf_nodes=3,
        min_samples_leaf=2,
        l2_regularization_numerator=1,
        l2_regularization_denominator=1,
        max_bins=16,
        random_seed=7,
    )
    values.update(updates)
    return NonlinearMaskingChallengeAuthorityV1(**values)


def test_all_runtime_sensitive_numeric_fields_have_no_production_default():
    numeric = (
        "feature_count", "max_cells_per_donor", "learning_rate_numerator",
        "learning_rate_denominator", "max_iter", "max_leaf_nodes",
        "min_samples_leaf", "l2_regularization_numerator",
        "l2_regularization_denominator", "max_bins", "random_seed",
    )
    fields = authority().__dataclass_fields__
    for name in numeric:
        assert fields[name].default is MISSING
        assert fields[name].default_factory is MISSING


def test_explicit_fixture_authority_validates():
    a = authority()
    a.validate()
    assert a.learning_rate == pytest.approx(0.1)
    assert a.l2_regularization == pytest.approx(1.0)


def test_placeholder_root_and_post_outcome_freeze_fail_closed():
    with pytest.raises(ValueError, match="SHA-256"):
        authority(primary_parameters_authority_sha256="placeholder").validate()
    with pytest.raises(ValueError, match="before terminal outcomes"):
        authority(terminal_outcomes_inspected_before_freeze=True).validate()
