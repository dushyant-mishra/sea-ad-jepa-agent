from __future__ import annotations

from pathlib import Path

import pytest

from sea_ad_jepa.v5.masking_authority_v1 import MaskingAuthorityV1
from sea_ad_jepa.v5.target_address_query_authority_v1 import TargetAddressQueryAuthorityV1
from test_v5_current_authority_closure_v1 import call, fixtures, h


ROOT = Path(__file__).resolve().parents[1]


def test_stage_a_firewall_tracks_current_successors_not_superseded_schemas() -> None:
    from test_v5_current_stage_a_spillover_firewall_v1 import (
        CURRENT_STAGE_A_SOURCE_PATHS,
        QUARANTINED_V5_MODULES,
    )

    assert "current_target_address_provider_authority_v1.py" in CURRENT_STAGE_A_SOURCE_PATHS
    assert "current_masking_policy_authority_v2.py" in CURRENT_STAGE_A_SOURCE_PATHS
    assert "teacher_target_semantics_authority_v2.py" in CURRENT_STAGE_A_SOURCE_PATHS
    assert "remaining_rna_necessity_v1.py" in CURRENT_STAGE_A_SOURCE_PATHS

    assert "target_address_query_authority_v1.py" not in CURRENT_STAGE_A_SOURCE_PATHS
    assert "masking_authority_v1.py" not in CURRENT_STAGE_A_SOURCE_PATHS
    assert "teacher_target_semantics_authority_v1.py" not in CURRENT_STAGE_A_SOURCE_PATHS
    assert "target_address_query_authority_v1" in QUARANTINED_V5_MODULES
    assert "masking_authority_v1" in QUARANTINED_V5_MODULES
    assert "teacher_target_semantics_authority_v1" in QUARANTINED_V5_MODULES


def test_current_closure_rejects_superseded_target_address_schema_even_if_self_consistent() -> None:
    f = fixtures()
    legacy = TargetAddressQueryAuthorityV1(
        authority_id="LEGACY_BUT_SELF_CONSISTENT",
        address_registry_authority_sha256=h("registry"),
        query_provider_id="trust_me_shared",
        query_artifact_sha256=h("query"),
        replay_policy_id="legacy_replay",
        parameter_sharing_policy_id="legacy_sharing",
        gradient_policy_id="legacy_gradient",
    )
    f["address"] = legacy

    with pytest.raises(ValueError, match="current target-address provider schema"):
        call(f)


def test_current_closure_rejects_superseded_masking_schema_even_if_self_consistent() -> None:
    f = fixtures()
    legacy = MaskingAuthorityV1(
        policy_id="LEGACY_SELF_CONSISTENT_MASK",
        dependency_source_authority_id="legacy_dependency",
        random_mixture_numerator=1,
        structural_mixture_numerator=0,
        mixture_denominator=1,
        target_evidence_budget_authority_id="legacy_budget",
        rng_authority_id="legacy_rng",
    )
    f["masking"] = legacy

    with pytest.raises(ValueError, match="current masking policy schema"):
        call(f)


def test_current_closure_source_names_all_current_successor_schemas() -> None:
    source = (ROOT / "src" / "sea_ad_jepa" / "v5" / "current_authority_closure_v1.py").read_text(
        encoding="utf-8"
    )
    assert "CurrentTargetAddressProviderAuthorityV1" in source
    assert "CurrentMaskingPolicyAuthorityV2" in source
    assert "RemainingRnaNecessityAuthorityV1" in source
    assert "TeacherTargetSemanticsAuthorityV2" in source
