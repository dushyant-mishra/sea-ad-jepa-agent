import hashlib
import pytest

from sea_ad_jepa.v5.masking_rng_replay_authority_v2 import MaskingRngReplayAuthorityV2


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="TEST",
        canonical_registry_authority_sha256=h("registry"),
        outer_split_authority_sha256=h("split"),
        target_panel_authority_sha256=h("panel"),
        burden_ladder_authority_sha256=h("burden"),
    )
    values.update(updates)
    return MaskingRngReplayAuthorityV2(**values)


def test_global_seed_is_derived_from_current_roots_not_entered_by_caller():
    a = authority()
    b = authority()
    assert a.global_seed == b.global_seed
    assert isinstance(a.global_seed, int)
    assert "global_seed" not in a.__dataclass_fields__


def test_root_change_changes_seed():
    assert authority().global_seed != authority(target_panel_authority_sha256=h("panel2")).global_seed


def test_method_name_cannot_enter_base_seed_derivation():
    a = authority()
    one = a.derive_seed(target_id="q1", outer_fold=0, cell_key="c1")
    two = a.derive_seed(target_id="q1", outer_fold=0, cell_key="c1")
    assert one == two


def test_placeholder_and_post_outcome_freeze_fail_closed():
    with pytest.raises(ValueError, match="SHA-256"):
        authority(outer_split_authority_sha256="placeholder").validate()
    with pytest.raises(ValueError, match="before terminal outcomes"):
        authority(terminal_outcomes_inspected_before_freeze=True).validate()
