from __future__ import annotations

from test_v5_current_stage_a_spillover_firewall_v1 import (
    CURRENT_STAGE_A_SOURCE_PATHS,
    QUARANTINED_V5_MODULES,
)


CURRENT_SUCCESSOR_FILES = {
    "canonical_address_registry_authority_v1.py",
    "current_target_address_provider_authority_v1.py",
    "shared_address_query_provider_v1.py",
    "target_evidence_budget_authority_v1.py",
    "precision_authority_v1.py",
    "outer_split_authority_v1.py",
    "target_panel_authority_v1.py",
    "address_universe_ladder_authority_v1.py",
    "masking_rng_replay_authority_v1.py",
    "masking_qualification_design_authority_v1.py",
    "masking_qualification_execution_authority_v1.py",
    "current_masking_policy_authority_v2.py",
    "target_construction_authority_v1.py",
    "remaining_rna_necessity_v1.py",
    "remaining_rna_execution_authority_v1.py",
    "teacher_target_semantics_authority_v2.py",
    "ema_timescale_authority_v2.py",
    "measurement_robustness_authority_v2.py",
    "target_identity_shortcut_gate_authority_v1.py",
    "anti_cheat_authority_bundle_v2.py",
    "model_geometry_authority_v2.py",
    "geometry_memorization_qualification_authority_v1.py",
    "production_protected_registry_authority_v1.py",
    "critical_test_execution_authority_v1.py",
    "current_runtime_source_authority_v1.py",
    "current_authority_roots_v2.py",
    "current_authority_closure_v2.py",
    "current_trainer_preexecution_contract_v2.py",
    "current_teacher_target_receipt_v2.py",
    "current_training_authority_v1.py",
    "qualified_optimizer_guard_v3.py",
    "current_atomic_checkpoint_guard_v2.py",
}

SUPERSEDED_CURRENT_MODULES = {
    "ema_timescale_authority_v1",
    "measurement_robustness_authority_v1",
    "anti_cheat_authority_bundle_v1",
    "model_geometry_authority_v1",
    "current_authority_roots_v1",
    "current_authority_closure_v1",
    "current_trainer_preexecution_contract_v1",
    "current_teacher_target_receipt_v1",
    "qualified_optimizer_guard_v2",
    "current_atomic_checkpoint_guard_v1",
}


def test_stage_a_inventory_tracks_all_current_successors() -> None:
    assert CURRENT_SUCCESSOR_FILES <= set(CURRENT_STAGE_A_SOURCE_PATHS)


def test_stage_a_inventory_does_not_call_superseded_runtime_schemas_current() -> None:
    current_modules = {name.removesuffix(".py") for name in CURRENT_STAGE_A_SOURCE_PATHS}
    assert current_modules.isdisjoint(SUPERSEDED_CURRENT_MODULES)
    assert SUPERSEDED_CURRENT_MODULES <= QUARANTINED_V5_MODULES
