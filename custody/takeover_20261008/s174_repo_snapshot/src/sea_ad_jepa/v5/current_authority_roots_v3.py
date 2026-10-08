"""Versioned current-V5 root vocabulary V3.

V3 preserves the historical V2 chain and adds three mandatory roots:
biological specificity, q-safety, and provider-backed critical-test execution.
Historical V2 remains unchanged.
"""

CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3 = (
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
    "masking_qualification_parameters_authority_sha256",
    "masking_qualification_run_contract_authority_sha256",
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
    "biological_specificity_authority_sha256",
    "q_safety_authority_sha256",
    "anti_cheat_authority_sha256",
    "model_geometry_authority_sha256",
    "geometry_memorization_qualification_authority_sha256",
    "protected_registry_authority_sha256",
    "critical_test_authority_sha256",
    "critical_test_execution_authority_sha256",
    "observation_gradient_firewall_authority_sha256",
    "runtime_source_authority_sha256",
)

CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V3 = (
    *CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3,
    "preexecution_authority_sha256",
)
