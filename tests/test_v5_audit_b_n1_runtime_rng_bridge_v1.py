from __future__ import annotations

import hashlib

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_n1_runtime_rng_bridge_v1 import (
    AuditBN1RuntimeRngBridgeV1,
    RNG_V3_GLOBAL_SEED,
    base_mask_seed,
    prefix3_inner_seed,
    removal_order_digest,
)
from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import (
    _base_uniform_mask,
    _removable_order,
    _seed,
)
from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import (
    CELL_KEY_COMMON_RANDOM_BASE_MASK,
    CANONICAL_REGISTRY_SHA256,
    FULL104_SUBSTRATE_SHA256,
    MaskingRngReplayAuthorityV3,
)


def test_bridge_authority_is_outcome_blind_and_nontraining() -> None:
    a = AuditBN1RuntimeRngBridgeV1(
        authority_id="JEPA_V5_FULL104_AUDIT_B_N1_RUNTIME_RNG_BRIDGE_V1"
    )
    a.validate()
    assert a.rng_v3_global_seed == RNG_V3_GLOBAL_SEED
    assert a.method_in_base_mask_seed is False
    assert a.target_panel_in_any_runtime_seed is False
    assert a.masks_executed_before_freeze is False
    assert a.burden_outcomes_inspected_before_freeze is False
    assert a.terminal_masking_authorized is False
    assert a.training_authorized is False
    assert len(a.canonical_digest()) == 64


def test_base_mask_seed_exactly_matches_frozen_planner_namespace() -> None:
    universe = np.arange(100, dtype=np.int64)
    target = 37
    fold = 2
    expected_seed = _seed(
        "V5_COMMON_RANDOM_BASE_MASK",
        RNG_V3_GLOBAL_SEED,
        fold,
        target,
        universe.size,
    )
    assert base_mask_seed(
        outer_fold=fold,
        target_address=target,
        universe_size=universe.size,
    ) == expected_seed

    expected = _base_uniform_mask(
        universe,
        target_col=target,
        co_mask_count=20,
        fold_index=fold,
        target_id=target,
        global_seed=RNG_V3_GLOBAL_SEED,
    )
    rng = np.random.default_rng(expected_seed)
    pool = universe[universe != target]
    chosen = rng.choice(pool, size=20, replace=False)
    observed = {target, *map(int, chosen)}
    assert observed == expected


def test_prefix3_seed_exactly_matches_frozen_source_namespace() -> None:
    for source in ("HVS", "NPH52", "SEA_AD"):
        assert prefix3_inner_seed(source_name=source) == _seed(
            "V5_PREFIX3_INNER",
            RNG_V3_GLOBAL_SEED,
            source,
        )


def test_removal_digest_exactly_matches_frozen_removal_order() -> None:
    base = {9, 2, 8, 1, 5, 4}
    target = 9
    fold = 3
    expected = _removable_order(
        base,
        target_col=target,
        fold_index=fold,
        target_id=target,
        global_seed=RNG_V3_GLOBAL_SEED,
    )
    observed = tuple(
        sorted(
            (x for x in base if x != target),
            key=lambda col: removal_order_digest(
                outer_fold=fold,
                target_address=target,
                candidate_address=col,
            ),
        )
    )
    assert observed == expected


def test_typed_rng_v3_derive_seed_is_deliberately_not_runtime_bridge() -> None:
    # This test makes the distinction explicit rather than accidentally assuming
    # the isolated V3 typed helper is the B4-frozen planner's downstream seed.
    a = MaskingRngReplayAuthorityV3(
        authority_id="TEST",
        full104_substrate_sha256=FULL104_SUBSTRATE_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        outer_split_receipt_sha256=hashlib.sha256(b"split").hexdigest(),
        qualification_parameters_authority_sha256=hashlib.sha256(b"parameters").hexdigest(),
        burden_ladder_authority_sha256=hashlib.sha256(b"burden").hexdigest(),
    )
    typed = a.derive_seed(
        target_id="37",
        outer_fold=2,
        cell_key=CELL_KEY_COMMON_RANDOM_BASE_MASK,
    )
    legacy_runtime = _seed(
        "V5_COMMON_RANDOM_BASE_MASK",
        a.global_seed,
        2,
        37,
        100,
    )
    assert typed != legacy_runtime


def test_bridge_rejects_postoutcome_or_training_scope() -> None:
    with pytest.raises(ValueError, match="masks_executed_before_freeze"):
        AuditBN1RuntimeRngBridgeV1(
            authority_id="X",
            masks_executed_before_freeze=True,
        ).validate()
    with pytest.raises(ValueError, match="training_authorized"):
        AuditBN1RuntimeRngBridgeV1(
            authority_id="X",
            training_authorized=True,
        ).validate()
