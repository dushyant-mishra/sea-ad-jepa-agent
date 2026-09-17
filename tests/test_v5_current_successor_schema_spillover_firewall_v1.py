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

    assert "target_address_query_authority_v1.py" not in CURRENT_STAGE_A_SOURCE_PATHS
    assert "masking_authority_v1.py" not in CURRENT_STAGE_A_SOURCE_PATHS
    assert "target_address_query_authority_v1" in QUARANTINED_V5_MODULES
    assert "masking_authority_v1" in QUARANTINED_V5_MODULES


def _rebind_preexecution_roots(f: dict, **updates: str) -> None:
    roots = dict(f["roots"])
    roots.update(updates)
    f["pre"].normalized_roots = lambda: dict(roots)


def test_current_closure_rejects_superseded_target_address_schema_even_if_roots_are_consistent() -> None:
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
    digest = legacy.canonical_digest()
    f["address"] = legacy
    f["teacher"].target_address_query_authority_sha256 = digest
    _rebind_preexecution_roots(f, target_address_query_authority_sha256=digest)

    with pytest.raises(ValueError, match="current target-address provider schema"):
        call(f)


def test_current_closure_rejects_superseded_masking_schema_even_if_roots_are_consistent() -> None:
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
    digest = legacy.canonical_digest()
    f["masking"] = legacy
    f["teacher"].masking_authority_sha256 = digest
    f["identity"].masking_authority_sha256 = digest
    f["anticheat"].masking_authority_sha256 = digest
    _rebind_preexecution_roots(f, masking_authority_sha256=digest)

    with pytest.raises(ValueError, match="current masking policy schema"):
        call(f)


def test_current_closure_source_names_successor_schemas_explicitly() -> None:
    source = (ROOT / "src" / "sea_ad_jepa" / "v5" / "current_authority_closure_v1.py").read_text(
        encoding="utf-8"
    )
    assert "CurrentTargetAddressProviderAuthorityV1" in source
    assert "CurrentMaskingPolicyAuthorityV2" in source
