from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.masking_rng_replay_authority_v1 import MaskingRngReplayAuthorityV1


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_MASKING_RNG_REPLAY_AUTHORITY_V1",
        canonical_registry_authority_sha256=h("registry"),
        outer_split_authority_sha256=h("split"),
        target_panel_authority_sha256=h("panel"),
        seed_namespace_id="V5_COMMON_RANDOM_BASE_MASK_V1",
        method_exclusion_policy_id="MASK_POLICY_ID_ABSENT_FROM_BASE_MASK_SEED_V1",
        replay_policy_id="DETERMINISTIC_EXACT_MASK_REPLAY_V1",
        global_seed=20260917,
    )
    values.update(updates)
    return MaskingRngReplayAuthorityV1(**values)


def test_seed_is_deterministic_and_has_no_method_argument() -> None:
    a = authority()
    s1 = a.derive_seed(target_id="ENSG000001", outer_fold=2, cell_key="cell-10")
    s2 = a.derive_seed(target_id="ENSG000001", outer_fold=2, cell_key="cell-10")
    assert s1 == s2
    assert isinstance(s1, int)
    assert 0 <= s1 < 2**64


def test_seed_changes_only_with_authorized_base_components() -> None:
    a = authority()
    base = a.derive_seed(target_id="q", outer_fold=1, cell_key="c")
    assert base != a.derive_seed(target_id="q2", outer_fold=1, cell_key="c")
    assert base != a.derive_seed(target_id="q", outer_fold=2, cell_key="c")
    assert base != a.derive_seed(target_id="q", outer_fold=1, cell_key="c2")


def test_behavioral_ids_are_enumerated() -> None:
    with pytest.raises(ValueError, match="seed_namespace_id"):
        authority(seed_namespace_id="RIDGE8_SEED").validate()
    with pytest.raises(ValueError, match="method_exclusion_policy_id"):
        authority(method_exclusion_policy_id="METHOD_IN_SEED").validate()
    with pytest.raises(ValueError, match="replay_policy_id"):
        authority(replay_policy_id="BEST_EFFORT_REPLAY").validate()


def test_role_roots_must_be_distinct() -> None:
    digest = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(outer_split_authority_sha256=digest, target_panel_authority_sha256=digest).validate()


def test_inputs_are_strict_and_training_is_off() -> None:
    with pytest.raises(ValueError, match="global_seed"):
        authority(global_seed=-1).validate()
    with pytest.raises(ValueError, match="outer_fold"):
        authority().derive_seed(target_id="q", outer_fold=-1, cell_key="c")
    with pytest.raises(ValueError, match="target_id"):
        authority().derive_seed(target_id="", outer_fold=0, cell_key="c")
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
