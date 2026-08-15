"""Focused contracts for the provisional TRAIN-only global-state audit."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from sea_ad_jepa.v4.a3r_global_state import (
    collision_evidence_class,
    input_closure_counts,
    masked_project,
    one_standard_error_prefix,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = yaml.safe_load((ROOT / "configs/v4/stage81a3r_real_train_global_state.yaml").read_text())
FIREWALL = yaml.safe_load((ROOT / "configs/v4/stage81a3r_nph_train_firewall.yaml").read_text())


def test_firewall_has_no_forbidden_input_path() -> None:
    serialized = json.dumps(CONFIG["inputs"]).lower()
    assert all(term not in serialized for term in ("pathology", "diagnosis", "braak", "cerad", "disease"))
    assert CONFIG["governance"]["train_rna_only"] is True
    assert CONFIG["governance"]["development_rna_forbidden"] is True
    assert CONFIG["governance"]["sealed_rna_forbidden"] is True
    assert CONFIG["status"] == "STAGE81A3R_CORRECTED_REAL_TRAIN_GLOBAL_STATE_AUDIT_COMPLETE_NOT_FROZEN"
    assert CONFIG["governance"]["corrected_real_train_runs_authorized"] == 1
    assert CONFIG["governance"]["corrected_real_train_runs_completed"] == 1
    assert CONFIG["governance"]["execution_history_mixed_split_nph_qs_materialized"] is True
    assert CONFIG["governance"]["discarded_mixed_split_cache_used"] is False
    assert CONFIG["governance"]["discarded_mixed_split_cache_retained"] is False


def test_historical_4096_cache_cannot_satisfy_successor_address_contract() -> None:
    expected = {f"address-{index}" for index in range(41_238)}
    actual = {f"address-{index}" for index in range(4_096)}
    result = input_closure_counts(expected, actual)
    assert result == {
        "expected_measured_addresses": 41_238,
        "actual_available_addresses": 4_096,
        "exact_intersection": 4_096,
        "expected_but_missing": 37_142,
        "unexpected_addresses": 0,
    }


def test_physical_splitter_is_preanalytic_and_model_free() -> None:
    path = ROOT / "scripts/v4/stage81a2r_build_nph_physical_split_firewall.R"
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    assert text.count("object <- qread(path)") == 1
    assert "source_donor <- paste0(\"human_\", as.character(coldata(object)$anno_batch))" in lowered
    assert "source_cell_id" in text and "source_donor_id" in text
    assert "sea_ad_jepa" not in lowered
    assert all(term not in lowered for term in ("torch", "tensorflow", "pca(", "svd(", "normalizecounts"))
    assert "assays = list(counts = source_subset)" in text


def test_collision_classification_does_not_infer_aggregation_from_counts() -> None:
    assert collision_evidence_class("current_exact", "EXACT_CURRENT_ENSEMBL") == (
        "INSUFFICIENT_SEMANTICS_FOR_SCALAR_REDUCTION"
    )
    assert collision_evidence_class(
        "current_exact", "EXACT_CURRENT_ENSEMBL|EXACT_HISTORICAL_ENSEMBL_TO_CURRENT"
    ) == "MULTIPLE_HISTORICAL_IDENTITIES_TO_ONE_ADDRESS"
    assert collision_evidence_class("source_native_anchored", "SOURCE_NATIVE_EXACT") == (
        "MULTIPLE_SOURCE_NATIVE_ROWS_TO_ONE_ANCHOR"
    )


def test_successor_a3r_manifest_exposes_only_physical_train_nph() -> None:
    serialized = json.dumps(FIREWALL["analytic_inputs"]).lower()
    assert "nph52_physical_split/train" in serialized.replace("\\\\", "/")
    assert all(term not in serialized for term in ("/dev", "/sealed", "organized_data", "stage81a3_nph_sample"))
    assert FIREWALL["firewall"]["original_mixed_split_nph_qs_accessible_to_a3r"] is False
    assert FIREWALL["firewall"]["development_derivatives_accessible_to_a3r"] is False
    assert FIREWALL["firewall"]["sealed_derivatives_accessible_to_a3r"] is False
    assert FIREWALL["historical_cache"]["classification"] == "HISTORICAL_A2_COMPATIBILITY_ONLY"
    assert FIREWALL["historical_cache"]["satisfies_successor_full_address_contract"] is False
    assert FIREWALL["materialization"]["collision_aggregation_policy_selected"] is False
    assert FIREWALL["materialization"]["downstream_observation_state_contract_accepted"] is True
    assert FIREWALL["materialization"]["corrected_global_basis_permitted"] is True
    assert FIREWALL["materialization"]["corrected_real_train_rerun_permitted"] is True


def test_masked_projection_ignores_structurally_unmeasured_values() -> None:
    basis = np.asarray([[1.0], [2.0], [4.0]])
    measured = np.asarray([True, True, False])
    first = np.asarray([[2.0, 4.0, 0.0]])
    second = np.asarray([[2.0, 4.0, 1e9]])
    assert np.allclose(masked_project(first, basis, measured), masked_project(second, basis, measured))


def test_one_se_rule_selects_smallest_equivalent_prefix() -> None:
    prefixes = np.asarray([16, 32, 48])
    folds = np.asarray([[0.80, 0.82, 0.83], [0.81, 0.83, 0.84], [0.82, 0.84, 0.85]])
    result = one_standard_error_prefix(prefixes, folds)
    assert result["best_prefix"] == 48
    assert result["k_bulk"] in {32, 48}


def test_dimensions_are_audit_granularity_not_fixed_truth() -> None:
    assert CONFIG["basis"]["prefix_step"] == 16
    assert CONFIG["basis"]["group_control_width"] == 32
    assert CONFIG["basis"]["maximum_dimensions"] == 256
    assert CONFIG["governance"]["freeze1_declared"] is False


def test_scalar_observability_contract_is_three_state_and_collision_safe() -> None:
    path = ROOT / "scripts/v4/stage81a3r_close_scalar_observability.py"
    text = path.read_text(encoding="utf-8")
    for state in ("STRUCTURALLY_UNMEASURED", "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED"):
        assert state in text
    assert '"assay_measured": True, "scalar_materializable": False' in text
    assert '"scalar_matrix_input": "MEASURED_SCALAR_ONLY"' in text
    assert '"aggregation_rule_selected": False' in text
    assert '"global_basis_fit_started": False' in text


def test_immune_object_is_phase_b_only_and_cannot_change_phase_a() -> None:
    path = ROOT / "scripts/v4/stage81a3r_audit_sea_ad_immune_phase_b_compatibility.py"
    text = path.read_text(encoding="utf-8")
    assert 'STATUS = "SEA_AD_IMMUNE_PHASE_B_COMPATIBILITY_ONLY"' in text
    assert 'ROLE = "PHASE_B_IMMUNE_MICROGLIA_PVM_CONTINUATION"' in text
    assert '"excluded_from_phase_a_whole_taxonomy_operators": True' in text
    assert '"included_in_a3r_global_basis": False' in text
    assert '"changes_k_bulk": False' in text
    assert '"changes_frozen_address_registry": False' in text
    assert '"aggregation_rule_applied": False' in text


def test_immune_outputs_are_separate_from_foundation_collision_outputs() -> None:
    outputs = CONFIG["outputs"]
    immune = {key: value for key, value in outputs.items() if key.startswith("immune_phase_b_")}
    assert len(immune) == 6
    assert all("sea_ad_immune_phase_b_compatibility" in value for value in immune.values())
    assert all(value not in {
        outputs["collision_ledger"], outputs["collision_address_summary"], outputs["collision_report"]
    } for value in immune.values())


def test_corrected_residual_null_is_predeclared_before_results() -> None:
    null = CONFIG["basis"]["residual_null"]
    assert null["family"] == "WITHIN_OPERATOR_DETERMINISTIC_B_VIEW_CELL_PAIRING_PERMUTATION"
    assert null["permutations"] == 100
    assert null["block_width"] == 16
    assert null["bh_fdr"] == 0.05
    assert null["donor_refit_support_required"] is True
    assert null["contiguous_retention"] is True
    assert null["stop_at_first_unsupported_block"] is True
    assert null["later_support_after_gap"] == "ORDERING_FAILURE"
    assert null["donor_refit_min_median_canonical_correlation"] == 0.50


def test_corrected_nph_materializer_masks_collisions_without_aggregation() -> None:
    text = (ROOT / "scripts/v4/stage81a3r_materialize_corrected_nph_train_sample.R").read_text(encoding="utf-8")
    assert "blocked_rows <- collision_ledger$source_feature_index" in text
    assert "mapping <- mapping[!(mapping$source_feature_index %in% blocked_rows)" in text
    assert "anyDuplicated(mapping$molecular_address_index)" in text
    assert "source_library <- as.numeric(colSums(source_counts" in text
    assert all(term not in text.lower() for term in ("development", "sealed", "pathology", "diagnosis"))


def test_corrected_audit_uses_only_phase_a_and_predeclared_null() -> None:
    text = (ROOT / "scripts/v4/stage81a3r_corrected_real_train_global_state.py").read_text(encoding="utf-8")
    assert "if len(phase_a[phase_a.study_id.eq(\"SEA_AD\")]) != 11" in text
    assert '"immune_phase_b_object_accessed": False' in text
    assert "rng.permutation(len(right))" in text
    assert "null_cfg[\"seed\"]" in text
    assert '"scalar_observable_addresses": 40_949' in text
    assert '"scalar_unobservable_collision_only": 289' in text
    assert '"post_checkpoint_unregistered_collision_pairs": 14' in text
    assert '"freeze1_declared": False' in text


def test_scalar_injectivity_preflight_accepts_only_known_supplemental_contract() -> None:
    text = (ROOT / "scripts/v4/stage81a3r_verify_scalar_mapping_injectivity.py").read_text(encoding="utf-8")
    assert 'EXPECTED_SUPPLEMENTAL_ADDRESSES = {"ENSG00000183889", "ENSG00000281635"}' in text
    assert "observed_pairs == expected_pairs" in text
    assert "frame.unregistered_source_rows.astype(int).eq(2).all()" in text
    assert '"scalar_mapping_injective_after_checkpoint_plus_supplemental_mask"' in text


def test_global_dimension_range_closure_is_bounded_and_conditional() -> None:
    closure = CONFIG["range_closure"]
    assert closure["purpose"] == "RANGE_CLOSURE_CHECK_ONLY"
    assert closure["accepted_prefix_maximum"] == 256
    assert closure["first_extension"] == [272, 288, 304, 320]
    assert closure["conditional_final_extension"] == [336, 352, 368, 384]
    assert closure["conditional_trigger"] == "BEST_TESTED_PREFIX_EQUALS_320"
    assert closure["hard_stop"] == 384
    assert closure["reuse_corrected_train_lineage"] is True
    assert closure["reuse_reproducibility_weights"] is True
    assert closure["reuse_residual_null"] is True
    assert closure["freeze1_declared"] is False


def test_range_closure_preserves_accepted_prefix_and_firewall() -> None:
    text = (ROOT / "scripts/v4/stage81a3r_global_dimension_range_closure.py").read_text(encoding="utf-8")
    assert "combined[:, :existing] - basis" in text
    assert "accepted prefix means did not reproduce" in text
    assert "accepted prefix standard errors did not reproduce" in text
    assert 'conditional_extension_run = int(first_bulk["best_prefix"]) == 320' in text
    assert 'if conditional_extension_run:' in text
    assert '"hard_stop": 384' not in text
    assert '"development_rna_accessed": False' in text
    assert '"sealed_rna_accessed": False' in text
    assert '"pathology_accessed": False' in text
    assert '"immune_phase_b_accessed": False' in text
    assert all(term not in text.lower() for term in ("diagnosis", "braak", "cerad", "amyloid"))


def test_range_closure_reuses_residual_decision_only_when_k_bulk_is_208() -> None:
    text = (ROOT / "scripts/v4/stage81a3r_global_dimension_range_closure.py").read_text(encoding="utf-8")
    assert "if k_bulk == 208:" in text
    assert "stage81a3r_corrected_real_train_residual_tail.csv" in text
    assert 'corrected.keyed_seed(null_cfg["seed"], context["fold"], matrix, permutation)' in text
    assert 'float(null_cfg["bh_fdr"])' in text
    assert 'null_cfg["donor_refit_min_median_canonical_correlation"]' in text
