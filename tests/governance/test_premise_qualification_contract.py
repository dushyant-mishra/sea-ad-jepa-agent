import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_STATE_20261005.json"


def _state() -> dict:
    assert STATE.exists(), "premise qualification state must be published"
    return json.loads(STATE.read_text(encoding="utf-8"))


def test_premise_state_carries_p1_through_p6_and_no_execution_authority() -> None:
    state = _state()
    assert list(state["premise_gates"]) == ["P1", "P2", "P3", "P4", "P5", "P6"]
    assert state["training_authorized"] is False
    assert state["stage_a_execution_authorized"] is False
    assert state["test_open"] is False
    assert state["morabito_open"] is False
    assert state["selected_target"] == "UNSET_REQUIRES_APPROVAL"
    assert state["selected_representation"] == "UNSET_REQUIRES_APPROVAL"
    assert state["selected_estimand"] == "UNSET_REQUIRES_APPROVAL"


def test_stage_a_verdicts_are_exact_and_claim_limited() -> None:
    state = _state()
    assert state["stage_a"]["status"] == "PREFREEZE_EXECUTION_CONTRACT__NOT_EXECUTION_AUTHORITY"
    assert state["stage_a"]["allowed_verdicts"] == [
        "QUALIFIED_FOR_RNA_REPRESENTATION",
        "INFORMATIVE_BUT_NOT_QUALIFIED",
        "FAIL_LEAKAGE",
        "FAIL_SHORTCUT",
        "FAIL_TRANSPORT",
        "NONRECOVERABLE_FROM_VIEW",
        "INDETERMINATE",
    ]
    assert state["stage_a"]["maximum_claim"] == "RNA_REPRESENTATION"


def test_recoverability_semantics_and_transfer_axes_are_not_collapsed() -> None:
    state = _state()
    assert state["recoverability"]["real_rna_quantity"] == "TARGET_OBJECT_RECOVERABILITY"
    assert state["recoverability"]["biological_truth_quantity"] == "BIOLOGICAL_TRUTH_RECOVERABILITY"
    assert state["recoverability"]["real_rna_target_object_is_not_biological_truth"] is True
    assert state["transport"]["axes"] == [
        "DONOR_TRANSFER",
        "OPERATOR_TRANSFER",
        "STUDY_TRANSFER",
        "TECHNOLOGY_TRANSFER",
    ]
    assert state["transport"]["nested_ladder"] is False


def test_diagnostic_readout_firewall_is_prospective() -> None:
    state = _state()
    readout = state["diagnostic_readout"]
    assert readout["fit_partition"] == "INNER_TRAIN_ONLY"
    assert readout["freeze_before"] == "HELD_DONOR_EVALUATION"
    assert readout["may_change_target_definition_from_deciding_outcomes"] is False
    assert readout["fit_on_deciding_units"] is False


def test_synthetic_scale_firewall_blocks_96_feature_production_claim() -> None:
    state = _state()
    scale = state["synthetic_scale_authority"]
    assert scale["world_a_class"] == "REDUCED_MEASUREMENT_AND_METRIC_CONTROL_WORLD"
    assert scale["world_a_feature_count"] == 96
    assert scale["canonical_address_count"] == 41238
    assert scale["world_a_can_qualify_production_pipeline"] is False
    assert scale["production_pipeline_required_universe"] == "CANONICAL_41238_ADDRESS_SYNTHETIC_UNIVERSE"
    assert scale["arbitrary_96_to_41238_mapping_allowed"] is False
    assert scale["independent_noise_padding_satisfies_scale"] is False


def test_v77_bcd_are_already_implemented_at_41k_and_v2_needs_remeasurement() -> None:
    scale = _state()["synthetic_scale_authority"]
    assert scale["bcd_implemented_at_canonical_41238"] is True
    assert scale["bcd_41k_implementation_commit"].startswith("9840cafe")
    assert scale["v2_canonical_observer_commit"].startswith("4e95aac4")
    assert scale["v2_oracle_ceilings_remeasured"] is False
    assert scale["next_required_action"] == "REBUILD_ALL_EXTENDED_WORLDS_ON_V2_AND_REMEASURE_ORACLE_CEILINGS"


def test_synthetic_use_modes_separate_scratch_training_from_real_checkpoint_evaluation() -> None:
    mode = _state()["synthetic_identity_use_modes"]
    assert mode["SCRATCH_SYNTHETIC_TRAINING"]["random_planted_biology_on_real_identity_slots_allowed"] is True
    assert mode["SCRATCH_SYNTHETIC_TRAINING"]["real_gene_semantic_claim_allowed"] is False
    assert mode["REAL_DATA_TRAINED_CHECKPOINT_EVALUATION"]["random_planted_biology_on_real_identity_slots_allowed"] is False
    assert mode["REAL_DATA_TRAINED_CHECKPOINT_EVALUATION"]["status"] == "UNRESOLVED_REQUIRES_PROSPECTIVE_IDENTITY_SEMANTICS"


def test_v77_observer_realism_is_recorded_without_posthoc_rebanding() -> None:
    realism = _state()["synthetic_scale_authority"]["v2_observer_realism"]
    assert realism["abundance_max_median"] == 27514
    assert realism["declared_abundance_band"] == [100, 10000]
    assert realism["abundance_exceeds_declared_band"] is True
    assert realism["top_1pct_count_share"] == 0.324
    assert realism["detect_rate_sd"] == 0.218
    assert realism["addresses_never_detected"] == 11972
    assert realism["measured_state_family_overlap"] == 0.323
    assert realism["measured_regulon_family_overlap"] == 0.367
    assert realism["declared_adjacent_family_overlap"] == 0.45


def test_numeric_margins_and_rare_biology_language_remain_fail_closed() -> None:
    state = _state()
    assert state["numeric_deciding_margins"] == "UNSET_REQUIRES_APPROVAL"
    assert state["rare_novelty"]["rna_structure_is_automatically_biological_novelty"] is False
    assert state["authority_freshness_rule"] == "UPDATE_CANONICAL_SURFACE_WHEN_CURRENT_TASK_CLOSES_OR_NEXT_AUTHORIZED_TASK_CHANGES"
