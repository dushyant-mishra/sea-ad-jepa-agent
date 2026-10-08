from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.v4.build_pre_stage81a2_harmonization import foundation_row_blockers


PROJECT = Path(__file__).resolve().parents[2]
RESULTS = PROJECT / "results/v4"


def rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_non_rna_modality_classification() -> None:
    modalities = {row["dataset_id"]: row for row in rows("pre_stage81a2_modality_integration_registry.csv")}
    documentation = [row for row in modalities.values() if row["feature_space_class"] == "documentation_or_assignment"]
    assert len(documentation) == 4
    assert all(row["equivalent_to_full_rna_matrix"] == "False" for row in documentation)
    assert all(row["rna_vocabulary_eligibility"] == "not_applicable" for row in documentation)
    assert all(row["integration_path"] == "documentation_or_assignment_support" for row in documentation)

    containers = [row for row in modalities.values() if row["feature_space_class"] == "unresolved_processed_container"]
    assert len(containers) == 11
    assert all(row["equivalent_to_full_rna_matrix"] == "False" for row in containers)
    assert all(row["rna_vocabulary_eligibility"] == "pending_content_harmonization" for row in containers)

    atac = modalities["gse254205_3bc2196b5493"]
    assert atac["feature_space_class"] == "atac_or_regulatory"
    assert atac["rna_vocabulary_eligibility"] == "excluded_non_rna"
    assert atac["measurement_mask_required"] == "False"


def test_spatial_panels_require_masks_and_are_not_full_rna() -> None:
    modalities = {row["dataset_id"]: row for row in rows("pre_stage81a2_modality_integration_registry.csv")}
    spatial_ids = (
        "sea_ad_mtg_merfish_combined_2024", "sea_ad_hip_merscope_combined_2026",
        "sea_ad_mec_merscope_combined_2026", "sea_ad_caudate_xenium_combined_2026",
    )
    for dataset_id in spatial_ids:
        row = modalities[dataset_id]
        assert row["feature_space_class"] == "targeted_spatial_panel"
        assert row["measurement_mask_required"] == "True"
        assert row["equivalent_to_full_rna_matrix"] == "False"
        assert "shared_feature_projection" in row["missing_modality_policy"]


def test_foundation_firewalls_and_stage_specific_gates() -> None:
    foundation = {row["dataset_id"]: row for row in rows("pre_stage81a2_foundation_readiness.csv")}
    siletti = foundation["siletti_hbca_all_non_neuronal"]
    assert siletti["foundation_vocabulary_eligible"] == "False"
    assert siletti["holdout_firewall_status"] == "pass"
    pathology = foundation["gse243292_full_dlpfc_h5ad"]
    assert pathology["foundation_vocabulary_eligible"] == "False"
    assert pathology["pathology_firewall_status"] == "excluded_from_foundation"

    report = json.loads((RESULTS / "pre_stage81a2_readiness_report.json").read_text(encoding="utf-8"))
    assert report["ready_for_stage81a2_foundation_review"] is False
    assert report["ready_for_regulatory_adapter_review"] is True
    assert report["ready_for_spatial_branch_review"] is False
    assert report["ready_for_perturbation_controller_review"] is False
    assert all("spatial" not in item and "perturbation" not in item for item in report["foundation_readiness_blockers"])
    assert report["foundation_readiness_blockers"] == [
        "gse97930_cerebellar_umi:donor_grouping",
        "gse97930_frontal_cortex_umi:donor_grouping",
        "gse97930_visual_cortex_umi:donor_grouping",
    ]


def test_foundation_gate_fails_each_relevant_contract_violation() -> None:
    base = {
        "foundation_integration_role": "foundation_training",
        "source_integrity_verified": True,
        "matrix_semantics_resolved": True,
        "exact_feature_identity_required": True,
        "exact_feature_identity_resolved": True,
        "donor_grouping_required": True,
        "donor_grouping_resolved": True,
        "pathology_firewall_status": "pass",
        "holdout_firewall_status": "not_applicable",
    }
    mutations = {
        "source_integrity": ("source_integrity_verified", False),
        "matrix_semantics": ("matrix_semantics_resolved", False),
        "exact_feature_identity": ("exact_feature_identity_resolved", False),
        "donor_grouping": ("donor_grouping_resolved", False),
        "pathology_firewall": ("pathology_firewall_status", "fail"),
        "holdout_firewall": ("holdout_firewall_status", "fail"),
    }
    for expected, (field, value) in mutations.items():
        candidate = {**base, field: value}
        assert expected in foundation_row_blockers(candidate)


def test_no_training_or_machine_specific_paths() -> None:
    report = json.loads((RESULTS / "pre_stage81a2_readiness_report.json").read_text(encoding="utf-8"))
    for field in (
        "physical_full_matrix_merge_performed", "final_vocabulary_frozen",
        "donor_split_frozen", "model_trained", "fuzzy_gene_aliasing_used",
        "fuzzy_donor_inference_used", "pathology_values_used",
    ):
        assert report[field] is False
    for path in RESULTS.glob("pre_stage81a2_*"):
        text = path.read_text(encoding="utf-8", errors="strict")
        assert "C:\\" not in text
        assert "/mnt/" not in text
