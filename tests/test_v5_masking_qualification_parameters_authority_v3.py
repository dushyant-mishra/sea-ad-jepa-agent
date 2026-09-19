from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import (
    PRIMARY_ATTACKER_ID,
    PRIMARY_SCORE_ID,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import (
    BURDEN_SEPARATION_POLICY_ID,
    CONFIRMATION_ROLE_ID,
    FULL104_SUBSTRATE_SHA256,
    HISTORICAL_PROVENANCE_ROLE_ID,
    ORIGIN_POLICY_ID,
    SUPPORT_ESTIMABILITY_AUTHORITY_SHA256,
    TERMINAL_UNIVERSE_ID,
    TERMINAL_UNIVERSE_SIZE,
    MaskingQualificationParametersAuthorityV3,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_FULL104_BOUND_CONFIRMATION_PARAMETERS_AUTHORITY_V3",
        full104_substrate_sha256=FULL104_SUBSTRATE_SHA256,
        support_estimability_authority_sha256=SUPPORT_ESTIMABILITY_AUTHORITY_SHA256,
        terminal_universe_id=TERMINAL_UNIVERSE_ID,
        terminal_universe_size=TERMINAL_UNIVERSE_SIZE,
        primary_attacker_id=PRIMARY_ATTACKER_ID,
        primary_score_id=PRIMARY_SCORE_ID,
        targeted_partner_cap=8,
        ridge_candidate_pool_count=64,
        ridge_score_feature_count=32,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=20,
        prefix_floor_numerator=1,
        prefix_floor_denominator=20,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
        discovery_expanded_validation_report_sha256=h("historical-report"),
        discovery_universe_scale_script_sha256=h("historical-universe"),
        discovery_outside800_unified_script_sha256=h("historical-outside"),
        discovery_provenance_note_sha256=h("historical-provenance"),
        parameter_origin_policy_id=ORIGIN_POLICY_ID,
        confirmation_role_id=CONFIRMATION_ROLE_ID,
        burden_separation_policy_id=BURDEN_SEPARATION_POLICY_ID,
        historical_provenance_role_id=HISTORICAL_PROVENANCE_ROLE_ID,
    )
    values.update(updates)
    return MaskingQualificationParametersAuthorityV3(**values)


def test_v3_confirmation_parameters_are_bound_to_current_full104_roots():
    a = authority()
    a.validate()
    assert a.full104_substrate_sha256 == FULL104_SUBSTRATE_SHA256
    assert a.support_estimability_authority_sha256 == SUPPORT_ESTIMABILITY_AUTHORITY_SHA256
    assert a.terminal_universe_id == "FULL_COMMON_CORE_17186_V1"
    assert a.terminal_universe_size == 17186
    assert a.ridge_score_feature_count == 32
    assert "CONDITIONAL_ON_CURRENT_32_FEATURE_ATTACKER_CLASS" in a.confirmation_role_id


def test_v3_rejects_historical_or_smaller_substrate_as_current_full104():
    with pytest.raises(ValueError, match="different FULL104 substrate"):
        authority(full104_substrate_sha256=h("historical-smaller-run")).validate()


def test_v3_rejects_noncurrent_support_authority():
    with pytest.raises(ValueError, match="different support authority"):
        authority(support_estimability_authority_sha256=h("stale-support")).validate()


def test_v3_historical_roots_cannot_occupy_current_authority_roles():
    with pytest.raises(ValueError, match="cannot occupy current FULL104 authority roles"):
        authority(
            discovery_expanded_validation_report_sha256=FULL104_SUBSTRATE_SHA256
        ).validate()
    with pytest.raises(ValueError, match="cannot occupy current FULL104 authority roles"):
        authority(
            discovery_provenance_note_sha256=SUPPORT_ESTIMABILITY_AUTHORITY_SHA256
        ).validate()


def test_v3_preserves_historical_evidence_as_supporting_only():
    a = authority()
    a.validate()
    assert "SUPPORTING_ONLY" in a.historical_provenance_role_id
    assert a.training_authorized is False
    assert a.protected_outcomes_authorized is False
    assert a.terminal_full104_masking_outcomes_inspected is False


def test_v3_builder_requires_physical_full104_and_current_support_inputs():
    source = Path(
        "scripts/agent/build_full104_masking_parameters_authority_v3_20260919.py"
    ).read_text(encoding="utf-8")
    compile(
        source,
        "scripts/agent/build_full104_masking_parameters_authority_v3_20260919.py",
        "exec",
    )
    assert '--level4-root' in source
    assert '--support-authority' in source
    assert 'PHASE2_EXPRESSION_BLOCK_MANIFEST.csv' in source
    assert FULL104_SUBSTRATE_SHA256 in source
    assert SUPPORT_ESTIMABILITY_AUTHORITY_SHA256 in source
    assert "historical_evidence_role" in source
    assert "capacity_scope_note" in source
