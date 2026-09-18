import hashlib
import pytest

from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v2 import (
    NonlinearMaskingChallengeAuthorityV2,
)


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def authority(**updates):
    values=dict(
        authority_id="TEST",
        primary_parameters_authority_sha256=h("parameters"),
        outer_split_authority_sha256=h("split"),
        target_panel_authority_sha256=h("panel"),
        historical_nonlinear_script_sha256=h("hist-script"),
        historical_nonlinear_summary_sha256=h("hist-summary"),
    )
    values.update(updates)
    return NonlinearMaskingChallengeAuthorityV2(**values)


def test_current_full104_nonlinear_settings_are_frozen_and_seed_is_root_derived():
    a=authority()
    a.validate()
    assert a.feature_count == 32
    assert a.max_cells_per_donor == 256
    assert a.max_iter == 50
    assert a.max_leaf_nodes == 15
    assert a.min_samples_leaf == 20
    assert a.max_bins == 255
    assert a.random_seed == authority().random_seed


def test_historical_seed_is_not_an_authority_field():
    assert "random_seed" not in authority().__dataclass_fields__


@pytest.mark.parametrize("field,value", [
    ("feature_count",31), ("max_cells_per_donor",255), ("max_iter",49),
    ("max_leaf_nodes",14), ("min_samples_leaf",19), ("max_bins",254),
])
def test_capacity_drift_fails_closed(field,value):
    with pytest.raises(ValueError, match=field):
        authority(**{field:value}).validate()


def test_historical_provenance_roots_are_required_but_do_not_authorize_training():
    with pytest.raises(ValueError, match="SHA-256"):
        authority(historical_nonlinear_script_sha256="placeholder").validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
