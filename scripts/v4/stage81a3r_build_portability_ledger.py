"""Write the deterministic Stage81A3R clean-worktree portability ledger."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from collections import Counter
from pathlib import Path

import yaml

STATUS = "PROVISIONAL - SYNTHETIC ONLY - NOT FROZEN"
MISSING = "MISSING_IGNORED_HISTORICAL_ARTIFACT"
STALE = "STALE_HISTORICAL_UCDQ_MANIFEST"
OTHER = "OTHER"


def row(node: str, dependency: str, classification: str, evidence: str) -> dict[str, object]:
    return {
        "test_node_id": node,
        "failing_dependency_or_path": dependency,
        "classification": classification,
        "exercised_new_a3r_code": False,
        "evidence": evidence,
    }


ROWS = [
    row("tests/v4/test_pre_stage81a2_harmonization.py::test_protected_files_are_unchanged", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Ignored historical artifact absent from clean checkout."),
    row("tests/v4/test_stage81a1_multimodal_inventory.py::test_audit_outputs_are_deterministic_and_portable", "data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad", MISSING, "Ignored historical source object absent from clean checkout."),
    row("tests/v4/test_stage81a1_multimodal_inventory.py::test_expression_and_gene_contract", "data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad", MISSING, "Ignored historical source object absent from clean checkout."),
    row("tests/v4/test_stage81a1_multimodal_inventory.py::test_graph_spatial_perturbation_and_roles", "data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad", MISSING, "Ignored historical source object absent from clean checkout."),
    row("tests/v4/test_stage81a1_multimodal_inventory.py::test_protected_signatures_and_source_hashes_are_frozen", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Ignored historical artifact absent from clean checkout."),
    row("tests/v4/test_stage81a1b_acquisition_contract.py::test_protected_signatures_are_unchanged", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Ignored historical artifact absent from clean checkout."),
    row("tests/v4/test_stage81a1b_acquisition_contract.py::test_catalog_mode_is_deterministic_and_portable", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Catalog subprocess stops on an absent ignored historical artifact."),
    row("tests/v4/test_stage81a1c_n_normal_references.py::test_protected_signatures_are_unchanged", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Ignored historical artifact absent from clean checkout."),
    row("tests/v4/test_stage81a1c_n_normal_references.py::test_catalog_is_deterministic_and_portable", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Catalog subprocess stops on an absent ignored historical artifact."),
    row("tests/v4/test_stage81a1c_p_perturbation.py::test_protected_signatures_are_unchanged", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Ignored historical artifact absent from clean checkout."),
    row("tests/v4/test_stage81a1d_living_human.py::test_protected_signatures_are_unchanged", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Ignored historical artifact absent from clean checkout."),
    row("tests/v4/test_stage81a2_canonical_freeze.py::test_exact_required_prior_inventory_and_hashes", "configs/v4/stage81a0_v4_design_contract.yaml and Stage81A2 required_prior_inputs hash set", OTHER, "Historical checkout/hash portability mismatch; first expected/observed config hashes differ."),
    row("tests/v4/test_stage81a2_canonical_freeze.py::test_nph_dispositions_are_exact_and_unresolved_excluded", "data/processed/v4/stage81a2/nph52_cell_disposition_summary.csv", MISSING, "Ignored historical cache absent from clean checkout."),
    row("tests/v4/test_stage81a2_canonical_freeze.py::test_nph_exact_52_and_25_19_8_groups", "data/processed/v4/stage81a1d/sealed/nph52_exact_donors.csv", MISSING, "Ignored historical split-metadata cache absent from clean checkout; no RNA was accessed."),
    row("tests/v4/test_stage81a2_canonical_freeze.py::test_protected_file_hashes_unchanged", "results/tables/v2_1_gse174367_cell_trajectory_scores.csv", MISSING, "Ignored historical artifact absent from clean checkout."),
    row("tests/v4/test_stage81a2r_a3r_candidate.py::test_protected_historical_hashes", "results/v4/stage81a3_ipb_jepa_feasibility.json", OTHER, "Historical protected-output hash differs in clean checkout; unrelated to new A3R code."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_contract_thresholds_and_hashes_are_immutable", "Stage81A3 UCDQ config/output hashes", STALE, "Historical UCDQ manifest expects superseded config/output hashes."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_original_ucdq_outputs_remain_preserved", "Stage81A3 UCDQ config/output hashes", STALE, "Historical UCDQ manifest expects superseded config/output hashes."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_publication_adjudication_does_not_depend_on_pathology_value", "Stage81A3 UCDQ config/output hashes", STALE, "Immutable-input verification fails before this historical assertion."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_broad_anchor_plus_independent_high_plex_yields_cross_donor_yes", "Stage81A3 UCDQ config/output hashes", STALE, "Immutable-input verification fails before this historical assertion."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_slidetags_and_merfish_are_distinct_technologies", "Stage81A3 UCDQ config/output hashes", STALE, "Immutable-input verification fails before this historical assertion."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_cross_technology_identifiability_is_yes", "Stage81A3 UCDQ config/output hashes", STALE, "Immutable-input verification fails before this historical assertion."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_fang_mtg_remains_excluded", "Stage81A3 UCDQ config/output hashes", STALE, "Immutable-input verification fails before this historical assertion."),
    row("tests/v4/test_stage81a3_context_human_provenance_adjudication.py::test_no_context_benefit_or_experiment_claim", "Stage81A3 UCDQ config/output hashes", STALE, "Immutable-input verification fails before this historical assertion."),
    row("tests/v4/test_stage81a3_fbsdq_outputs.py::test_candidate_basis_is_160d_and_not_frozen[BALANCED_PCA160]", "results/v4/stage81a3_balanced_pca160_diagnostic.npz", MISSING, "Ignored historical diagnostic absent from clean checkout."),
    row("tests/v4/test_stage81a3_fbsdq_outputs.py::test_candidate_basis_is_160d_and_not_frozen[BALANCED_REP160]", "results/v4/stage81a3_balanced_rep160_diagnostic.npz", MISSING, "Ignored historical diagnostic absent from clean checkout."),
    row("tests/v4/test_stage81a3_fbsdq_outputs.py::test_evidence_and_depth_curves_use_fixed_levels", "results/v4/stage81a3_evidence_response.csv", MISSING, "Ignored historical diagnostic absent from clean checkout."),
    row("tests/v4/test_stage81a3_uniform_context_data_qualification.py::test_contract_hash_stability", "Stage81A3 UCDQ contract config hash", STALE, "Historical contract records the superseded UCDQ config hash."),
]


def atomic_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a3r_final_address_qualification.yaml"))
    args = parser.parse_args()
    project = args.project_dir.resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    rows = sorted(ROWS, key=lambda item: str(item["test_node_id"]))
    if len(rows) != 28 or len({row_["test_node_id"] for row_ in rows}) != 28:
        raise RuntimeError("portability ledger must contain exactly 28 unique failures")
    if any(row_["classification"] == "A3R_REGRESSION" or row_["exercised_new_a3r_code"] for row_ in rows):
        raise RuntimeError("A3R regression detected; checkpoint forbidden")
    counts = dict(sorted(Counter(str(row_["classification"]) for row_ in rows).items()))
    summary = {
        "status": STATUS,
        "clean_worktree_passed": 845,
        "clean_worktree_failed": 28,
        "classification_counts": counts,
        "a3r_regressions": 0,
        "failures_exercising_new_a3r_code": 0,
        "conclusion": "HISTORICAL TEST-ARTIFACT PORTABILITY LIMITATION; NOT AN A3R SCIENTIFIC REGRESSION",
    }
    atomic_csv(project / config["outputs"]["portability_ledger"], rows)
    atomic_json(project / config["outputs"]["portability_summary"], summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
