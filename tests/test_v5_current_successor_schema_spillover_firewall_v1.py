from __future__ import annotations

from pathlib import Path


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


def test_current_closure_source_explicitly_rejects_superseded_successor_schemas() -> None:
    source = (ROOT / "src" / "sea_ad_jepa" / "v5" / "current_authority_closure_v1.py").read_text(
        encoding="utf-8"
    )
    # The current closure must identify the successor schemas themselves, not merely
    # accept any internally self-consistent object exposing validate/canonical_digest.
    assert "CurrentTargetAddressProviderAuthorityV1" in source
    assert "CurrentMaskingPolicyAuthorityV2" in source
    assert "current target-address provider schema" in source
    assert "current masking policy schema" in source
