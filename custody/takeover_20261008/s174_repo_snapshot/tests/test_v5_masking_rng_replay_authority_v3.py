import hashlib

import pytest

from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import (
    CANONICAL_REGISTRY_SHA256,
    CELL_KEY_COMMON_RANDOM_BASE_MASK,
    CELL_KEY_MASK_REMOVAL_ORDER,
    CELL_KEY_PREFIX3_INNER_GROUPING,
    FULL104_SUBSTRATE_SHA256,
    MaskingRngReplayAuthorityV3,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def authority(**updates) -> MaskingRngReplayAuthorityV3:
    values = dict(
        authority_id="TEST_V3",
        full104_substrate_sha256=FULL104_SUBSTRATE_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        outer_split_receipt_sha256=h("split"),
        qualification_parameters_authority_sha256=h("parameters"),
        burden_ladder_authority_sha256=h("burden"),
    )
    values.update(updates)
    return MaskingRngReplayAuthorityV3(**values)


def test_global_seed_is_derived_and_stable_without_target_panel() -> None:
    a = authority()
    b = authority()
    assert a.global_seed == b.global_seed
    assert isinstance(a.global_seed, int)
    assert "global_seed" not in a.__dataclass_fields__
    assert "target_panel_authority_sha256" not in a.__dataclass_fields__


def test_target_panel_size_cannot_reroll_v3_by_construction() -> None:
    a = authority()
    assert a.derive_seed(target_id="gene-x", outer_fold=2, cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK) == (
        authority().derive_seed(target_id="gene-x", outer_fold=2, cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK)
    )


@pytest.mark.parametrize(
    "field",
    [
        "outer_split_receipt_sha256",
        "qualification_parameters_authority_sha256",
        "burden_ladder_authority_sha256",
    ],
)
def test_current_root_change_changes_global_seed(field: str) -> None:
    assert authority().global_seed != authority(**{field: h(field + "-changed")}).global_seed


def test_target_and_fold_still_key_replay_seed() -> None:
    a = authority()
    base = a.derive_seed(target_id="q1", outer_fold=0, cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK)
    assert base != a.derive_seed(target_id="q2", outer_fold=0, cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK)
    assert base != a.derive_seed(target_id="q1", outer_fold=1, cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK)
    assert base != a.derive_seed(
        target_id="q1", outer_fold=0, cell_key=CELL_KEY_MASK_REMOVAL_ORDER
    )


def test_wrong_current_substrate_or_registry_fails_closed() -> None:
    with pytest.raises(ValueError, match="FULL104 substrate"):
        authority(full104_substrate_sha256=h("other-substrate")).validate()
    with pytest.raises(ValueError, match="canonical registry"):
        authority(canonical_registry_sha256=h("other-registry")).validate()


def test_postoutcome_or_training_authority_is_rejected() -> None:
    with pytest.raises(ValueError, match="before terminal outcomes"):
        authority(terminal_outcomes_inspected_before_freeze=True).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()


def test_method_name_is_not_an_input_to_replay_seed() -> None:
    a = authority()
    # There is no method argument at all: the common base mask is replayable
    # independently of which policy is later evaluated.
    seed = a.derive_seed(target_id="q", outer_fold=0, cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK)
    assert seed == a.derive_seed(target_id="q", outer_fold=0, cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK)


def test_free_string_cell_key_is_rejected() -> None:
    a = authority()
    for bad in ["base", "target_panel=4096", "policy=RIDGE8", "cell-123", ""]:
        with pytest.raises(ValueError, match="fixed masking RNG namespace"):
            a.derive_seed(target_id="q", outer_fold=0, cell_key=bad)


def test_all_three_production_mask_namespaces_are_distinct() -> None:
    a = authority()
    seeds = {
        a.derive_seed(target_id="q", outer_fold=0, cell_key=key)
        for key in (
            CELL_KEY_COMMON_RANDOM_BASE_MASK,
            CELL_KEY_PREFIX3_INNER_GROUPING,
            CELL_KEY_MASK_REMOVAL_ORDER,
        )
    }
    assert len(seeds) == 3


def test_only_four_authenticated_outer_folds_are_allowed() -> None:
    a = authority()
    for bad in (-1, 4, 99):
        with pytest.raises(ValueError, match="four authenticated folds"):
            a.derive_seed(
                target_id="q",
                outer_fold=bad,
                cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK,
            )
