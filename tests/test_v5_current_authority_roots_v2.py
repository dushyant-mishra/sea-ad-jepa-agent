from __future__ import annotations

from sea_ad_jepa.v5.current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2


def test_v2_root_vocabulary_is_exact_unique_and_explicit() -> None:
    expected = (
        "full104_substrate_sha256",
        "representation_authority_sha256",
        "support_estimability_authority_sha256",
        "canonical_address_registry_authority_sha256",
        "base_training_estimand_sha256",
        "target_address_provider_authority_sha256",
        "target_evidence_budget_authority_sha256",
        "precision_authority_sha256",
        "outer_split_authority_sha256",
        "target_panel_authority_sha256",
        "address_universe_ladder_authority_sha256",
        "masking_rng_replay_authority_sha256",
        "masking_qualification_design_authority_sha256",
        "masking_qualification_execution_authority_sha256",
        "masking_authority_sha256",
        "target_construction_authority_sha256",
        "remaining_rna_necessity_authority_sha256",
        "remaining_rna_execution_authority_sha256",
        "teacher_target_semantics_authority_sha256",
        "schedule_authority_sha256",
        "ema_authority_sha256",
        "measurement_robustness_authority_sha256",
        "target_identity_gate_authority_sha256",
        "anti_cheat_authority_sha256",
        "model_geometry_authority_sha256",
        "geometry_memorization_qualification_authority_sha256",
        "protected_registry_authority_sha256",
        "critical_test_authority_sha256",
        "observation_gradient_firewall_authority_sha256",
        "runtime_source_authority_sha256",
    )
    assert CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2 == expected
    assert len(set(CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2)) == len(expected)


def test_v2_does_not_use_ambiguous_legacy_root_names() -> None:
    forbidden = {
        "target_address_query_authority_sha256",
        "runtime_source_sha256",
        "geometry_sha256",
        "mask_fraction",
    }
    assert forbidden.isdisjoint(CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2)
