from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from sea_ad_jepa.v5.current_masking_policy_authority_v2 import CurrentMaskingPolicyAuthorityV2
from sea_ad_jepa.v5.current_target_address_provider_authority_v1 import (
    CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
    CurrentTargetAddressProviderAuthorityV1,
)
from sea_ad_jepa.v5.teacher_target_semantics_authority_v1 import TeacherTargetSemanticsAuthorityV1
from test_v5_current_authority_closure_v1 import call, fixtures, h


ROOT = Path(__file__).resolve().parents[1]


def _rebind_preexecution_roots(f: dict, **updates: str) -> None:
    roots = dict(f["roots"])
    roots.update(updates)
    f["roots"] = roots
    f["pre"].normalized_roots = lambda: dict(roots)


def _install_current_address_and_mask(f: dict) -> None:
    address = CurrentTargetAddressProviderAuthorityV1(
        authority_id="JEPA_V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_V1",
        address_registry_authority_sha256=CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
        query_provider_id="V5_SHARED_ADDRESS_QUERY_PROVIDER_V1",
        query_artifact_sha256=h("query-artifact"),
        replay_policy_id="FULL_PROVIDER_STATE_DETERMINISTIC_REPLAY_V1",
        parameter_sharing_policy_id="SHARED_TRAINABLE_ADDRESS_QUERY_MECHANISM_V1",
        gradient_policy_id="CONTEXT_EVIDENCE_TO_PREDICTION_GRADIENT_REACHABLE_V1",
    )
    masking = CurrentMaskingPolicyAuthorityV2(
        authority_id="JEPA_V5_CURRENT_MASKING_POLICY_AUTHORITY_V2",
        canonical_registry_authority_sha256=CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
        support_estimability_authority_sha256=f["support"].canonical_digest(),
        shortcut_artifact_sha256=h("shortcut-authority"),
        masking_policy_id="V5_UNIFORM_RANDOM_MASK_V1",
        target_evidence_budget_authority_id="V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        target_evidence_budget_authority_sha256=h("target-evidence-budget-authority"),
        rng_replay_authority_id="V5_DETERMINISTIC_MASK_REPLAY_AUTHORITY_V1",
        eligibility_policy_id="SUPPORT_ESTIMABILITY_AUTHORITY_ELIGIBILITY_V1",
        fallback_policy_id="DETERMINISTIC_UNIFORM_FALLBACK_V1",
        rng_replay_authority_sha256=h("rng-replay-authority"),
    )
    f["address"] = address
    f["masking"] = masking
    f["identity"].masking_authority_sha256 = masking.canonical_digest()
    f["anticheat"] = replace(f["anticheat"], masking_authority_sha256=masking.canonical_digest())
    _rebind_preexecution_roots(
        f,
        target_address_query_authority_sha256=address.canonical_digest(),
        masking_authority_sha256=masking.canonical_digest(),
        anti_cheat_authority_sha256=f["anticheat"].canonical_digest(),
    )


def test_stage_a_firewall_tracks_current_target_mask_and_teacher_semantic_successors() -> None:
    from test_v5_current_stage_a_spillover_firewall_v1 import (
        CURRENT_STAGE_A_SOURCE_PATHS,
        QUARANTINED_V5_MODULES,
    )

    for filename in (
        "current_target_address_provider_authority_v1.py",
        "current_masking_policy_authority_v2.py",
        "remaining_rna_necessity_v1.py",
        "teacher_target_semantics_authority_v2.py",
    ):
        assert filename in CURRENT_STAGE_A_SOURCE_PATHS

    for filename in (
        "target_address_query_authority_v1.py",
        "masking_authority_v1.py",
        "teacher_target_semantics_authority_v1.py",
    ):
        assert filename not in CURRENT_STAGE_A_SOURCE_PATHS

    for module in (
        "target_address_query_authority_v1",
        "masking_authority_v1",
        "teacher_target_semantics_authority_v1",
    ):
        assert module in QUARANTINED_V5_MODULES


def test_current_closure_rejects_legacy_teacher_semantics_even_when_roots_are_consistent() -> None:
    f = fixtures()
    _install_current_address_and_mask(f)

    legacy = TeacherTargetSemanticsAuthorityV1(
        authority_id="LEGACY_BUT_SELF_CONSISTENT_TEACHER_SEMANTICS",
        representation_authority_sha256=f["rep"].canonical_digest(),
        support_estimability_authority_sha256=f["support"].canonical_digest(),
        teacher_input_support_authority_sha256=h("legacy-teacher-input-support"),
        teacher_state_location_id="ANY_NONEMPTY_STATE_LABEL",
        target_aggregation_id="ANY_NONEMPTY_AGGREGATION",
        target_normalization_id="ANY_NONEMPTY_NORMALIZATION",
        target_address_query_authority_sha256=f["address"].canonical_digest(),
        student_visible_support_authority_sha256=h("legacy-student-visible-support"),
        scientific_weight_authority_sha256=f["est"].canonical_digest(),
        masking_authority_sha256=f["masking"].canonical_digest(),
        gradient_boundary_authority_id="ANY_NONEMPTY_GRADIENT_LABEL",
        ema_boundary_authority_sha256=f["ema"].canonical_digest(),
    )
    teacher_digest = legacy.canonical_digest()
    f["teacher"] = legacy
    f["measurement"].teacher_target_semantics_sha256 = teacher_digest
    f["identity"].teacher_target_semantics_sha256 = teacher_digest
    _rebind_preexecution_roots(f, teacher_target_semantics_sha256=teacher_digest)

    with pytest.raises(ValueError, match="current teacher-target semantics schema"):
        call(f)


def test_current_closure_source_names_all_three_successor_schemas() -> None:
    source = (ROOT / "src" / "sea_ad_jepa" / "v5" / "current_authority_closure_v1.py").read_text(
        encoding="utf-8"
    )
    assert "CurrentTargetAddressProviderAuthorityV1" in source
    assert "CurrentMaskingPolicyAuthorityV2" in source
    assert "TeacherTargetSemanticsAuthorityV2" in source
