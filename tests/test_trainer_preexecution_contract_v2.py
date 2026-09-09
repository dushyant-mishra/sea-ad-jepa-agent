import pytest

from sea_ad_jepa.v5.trainer_preexecution_contract_v2 import (
    MECHANICS_CHAIN_V2,
    PROTECTED_PARAMETERS,
    PROTECTED_ROLES,
    REQUIRED_AUTHORITY_SHAS,
    REQUIRED_CRITICAL_TESTS_V2,
    TrainerPreexecutionAuthorityV2,
    TrainerPreexecutionError,
    validate_authority_bundle,
    validate_critical_test_execution,
    validate_design_transition,
    validate_mechanics_chain,
    validate_protected_registry,
)


def registry():
    return [
        {
            "block_index": b,
            "role": r,
            "parameter": p,
            "tensor_name": f"blocks.{b}.{r}.{p}",
        }
        for b in range(6)
        for r in PROTECTED_ROLES
        for p in PROTECTED_PARAMETERS
    ]


def critical():
    return {k: "EXECUTED_PASS" for k in REQUIRED_CRITICAL_TESTS_V2}


def authorities():
    return {k: "a" * 64 for k in REQUIRED_AUTHORITY_SHAS}


def test_exact_complete_chain_passes():
    assert validate_mechanics_chain(MECHANICS_CHAIN_V2)["status"] == "PASS"


def test_old_chain_without_cursor_and_atomic_commit_fails():
    with pytest.raises(TrainerPreexecutionError, match="chain mismatch"):
        validate_mechanics_chain(MECHANICS_CHAIN_V2[:-2])


def test_registry_is_exact_48():
    out = validate_protected_registry(registry())
    assert out["expected_tensors"] == 48
    with pytest.raises(TrainerPreexecutionError, match="48"):
        validate_protected_registry(registry()[:-1])


def test_critical_skip_is_failure():
    statuses = critical()
    statuses["LIVE_TENSOR_SUBNORMAL_GRADIENT_REGRESSION"] = "SKIPPED_NO_TORCH"
    with pytest.raises(TrainerPreexecutionError, match="not executed-pass"):
        validate_critical_test_execution(statuses)


def test_authority_bundle_requires_all_and_no_extras():
    assert len(validate_authority_bundle(authorities())) == len(
        REQUIRED_AUTHORITY_SHAS
    )
    missing = authorities()
    missing.pop("dimension_authority_sha256")
    with pytest.raises(TrainerPreexecutionError):
        validate_authority_bundle(missing)
    extra = authorities()
    extra["stale_horizon_constant"] = "b" * 64
    with pytest.raises(TrainerPreexecutionError, match="unexpected"):
        validate_authority_bundle(extra)


def test_preexecution_has_no_internal_training_authority():
    reg = validate_protected_registry(registry())
    fixture_values = {
        "presentation_horizon": 10,
        "ema_half_life_presentations": 3,
        "singleton_queries_per_base_cell": 2,
        "effective_base_cells_per_update": 2,
    }
    authority = TrainerPreexecutionAuthorityV2(
        authorities=authorities(),
        protected_registry_sha256=reg["registry_sha256"],
        **fixture_values,
        relational_training_active=False,
        optimizer_started=False,
    )
    authority.validate()
    assert len(authority.canonical_digest()) == 64
    invalid = TrainerPreexecutionAuthorityV2(
        authorities=authorities(),
        protected_registry_sha256=reg["registry_sha256"],
        **fixture_values,
        relational_training_active=False,
        optimizer_started=False,
        training_authorized=True,
    )
    with pytest.raises(
        TrainerPreexecutionError,
        match="cannot itself authorize",
    ):
        invalid.validate()


def test_no_flex_after_freeze():
    before = {
        "optimizer_started": False,
        "design_frozen": True,
        "scientific_design": {"x": 1},
    }
    after = {
        "optimizer_started": False,
        "design_frozen": True,
        "scientific_design": {"x": 2},
    }
    with pytest.raises(TrainerPreexecutionError, match="NO_FLEX"):
        validate_design_transition(before, after)
