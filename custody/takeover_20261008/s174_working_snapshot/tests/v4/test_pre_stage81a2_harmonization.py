from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "configs/v4/pre_stage81a2_harmonization_contract.yaml"


def test_contract_is_virtual_and_non_destructive() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    policy = config["policy"]
    assert policy["physical_full_matrix_merge_performed"] is False
    assert policy["final_vocabulary_frozen"] is False
    assert policy["donor_split_frozen"] is False
    assert policy["pathology_values_used"] is False
    assert policy["model_trained"] is False
    assert policy["fuzzy_gene_aliasing_allowed"] is False
    assert policy["no_fixed_storage_cap"] is True
    assert policy["spatial_zero_fill_into_rna_vocabulary_allowed"] is False
    assert policy["atac_features_allowed_in_rna_vocabulary"] is False
    assert policy["holdout_may_influence_model_design"] is False
    assert policy["pathology_context_allowed_in_foundation_supervision"] is False
    assert policy["perturbation_training_requires_complete_asset_audit"] is True


def test_protected_files_are_unchanged() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for name, expected in config["protected_worktree_signatures"].items():
        assert hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() == expected


def test_frozen_outputs_when_present() -> None:
    report_path = PROJECT / "results/v4/pre_stage81a2_harmonization_report.json"
    if not report_path.exists():
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["virtual_harmonization_layer_pass"] is True
    assert report["physical_full_matrix_merge_performed"] is False
    assert report["final_vocabulary_frozen"] is False
    assert report["donor_split_frozen"] is False
    assert report["pathology_values_used"] is False
    assert report["model_trained"] is False
    assert report["fuzzy_gene_aliasing_used"] is False
    assert report["spatial_zero_fill_into_rna_vocabulary_allowed"] is False
    assert report["atac_features_allowed_in_rna_vocabulary"] is False
    assert report["holdout_may_influence_model_design"] is False
    assert report["pathology_context_allowed_in_foundation_supervision"] is False
    assert report["perturbation_training_ready"] is False
    assert report["unresolved_perturbation_shape_asset_count"] == 14
    assert report["ready_for_stage81a2_review_deprecated_alias_for"] == "ready_for_stage81a2_foundation_review"


def test_virtual_manifest_has_required_fields_when_present() -> None:
    path = PROJECT / "results/v4/pre_stage81a2_virtual_concat_manifest.json"
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "dataset_id", "source_hash", "source_path", "shape", "gene_namespace",
        "canonical_mapping_file", "cell_identifier_policy", "donor_field",
        "study_field", "region_field", "assay_field", "matrix_semantics",
        "allowed_role", "forbidden_role", "duplicate_group",
        "future_vocabulary_projection_status", "future_split_grouping_keys",
        "feature_space_class", "integration_path", "missing_modality_policy",
        "measurement_mask_required", "equivalent_to_full_rna_matrix",
    }
    assert manifest["physical_full_matrix_merge_performed"] is False
    assert manifest["datasets"]
    assert all(required <= set(row) for row in manifest["datasets"])


def test_modality_and_perturbation_gates_when_present() -> None:
    modality_path = PROJECT / "results/v4/pre_stage81a2_modality_integration_registry.csv"
    perturbation_path = PROJECT / "results/v4/pre_stage81a2_perturbation_readiness_registry.csv"
    if not modality_path.exists() or not perturbation_path.exists():
        return
    import csv
    with modality_path.open(encoding="utf-8", newline="") as handle:
        modalities = {row["dataset_id"]: row for row in csv.DictReader(handle)}
    for dataset_id in (
        "sea_ad_mtg_merfish_combined_2024", "sea_ad_hip_merscope_combined_2026",
        "sea_ad_mec_merscope_combined_2026", "sea_ad_caudate_xenium_combined_2026",
    ):
        assert modalities[dataset_id]["equivalent_to_full_rna_matrix"] == "False"
        assert modalities[dataset_id]["rna_vocabulary_eligibility"] == "excluded_from_direct_full_rna_vocabulary"
        assert modalities[dataset_id]["measurement_mask_required"] == "True"
    assert modalities["sea_ad_mtg_atac_final_2024"]["rna_vocabulary_eligibility"] == "excluded_non_rna"
    assert modalities["siletti_hbca_all_non_neuronal"]["integration_path"] == "clean_holdout_only"
    with perturbation_path.open(encoding="utf-8", newline="") as handle:
        perturbations = list(csv.DictReader(handle))
    assert len(perturbations) == 16
    assert sum(row["shape"] == "unresolved_source_archive_or_table" for row in perturbations) == 14
    assert all(row["perturbation_training_ready"] == "False" for row in perturbations)
