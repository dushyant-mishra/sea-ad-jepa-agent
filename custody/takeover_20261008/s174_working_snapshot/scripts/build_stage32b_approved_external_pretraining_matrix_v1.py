from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_stage32_external_pretraining_matrix_v1 as s32  # noqa: E402


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

DOWNLOAD_PLAN_OUT = TABLE_DIR / "stage32b_candidate_download_plan_v1.csv"
INVENTORY_OUT = TABLE_DIR / "stage32b_approved_matrix_inventory_v1.csv"
GENE_OVERLAP_OUT = TABLE_DIR / "stage32b_gene_overlap_audit_v1.csv"
METADATA_SCHEMA_OUT = TABLE_DIR / "stage32b_metadata_schema_audit_v1.csv"
HOLDOUT_AUDIT_OUT = TABLE_DIR / "stage32b_holdout_protection_audit_v1.csv"
MANIFEST_OUT = TABLE_DIR / "stage32b_pretraining_matrix_manifest_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage32b_pass_fail_v1.csv"
REPORT_OUT = REPORT_DIR / "stage32b_approved_external_pretraining_matrix_report_v1.md"

MATRIX_FILE = "stage32b_external_pretraining_matrix.h5ad"
METADATA_FILE = "stage32b_external_pretraining_metadata.csv"
GENE_MAP_FILE = "stage32b_external_pretraining_gene_map.csv"
JSON_MANIFEST_FILE = "stage32b_external_pretraining_manifest.json"


def load_cfg(path: Path) -> dict[str, Any]:
    return s32.load_cfg(path)


def resolve(value: str | Path) -> Path:
    return s32.resolve(value)


def approved_role_audit(registry: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in registry.iterrows():
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row.get("dataset_name", ""),
                "source": row.get("source_type", ""),
                "collection_name": row.get("collection_name", ""),
                "registry_role": row.get("role", ""),
                **s32.normalize_role(row),
            }
        )
    return pd.DataFrame(rows)


def make_download_plan(cfg: dict[str, Any], role_audit: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    approved = role_audit[role_audit["approved_for_pretraining"]].copy()
    priority = {dataset_id: i for i, dataset_id in enumerate(cfg["candidate_priority_order"])}
    approved["priority_rank"] = approved["dataset_id"].map(priority).fillna(999).astype(int)
    rows = []
    for _, row in approved.sort_values(["priority_rank", "dataset_id"]).iterrows():
        inv = inventory[inventory["matched_dataset_id"] == row["dataset_id"]]
        local_found = not inv.empty
        matrix_loaded = bool(inv["matrix_loaded"].any()) if local_found else False
        if local_found and matrix_loaded:
            next_action = "local approved matrix available; run gene/metadata alignment"
            acquisition_mode = "local"
        elif row["source"] == "CELLxGENE":
            next_action = "manual/approved CELLxGENE Census or H5AD download required; record dataset ID, collection ID, version, URL/source, and command"
            acquisition_mode = "manual_or_allow_download_cellxgene"
        elif row["source"] == "GEO":
            next_action = "manual/approved GEO processed matrix build required; only parse recognized documented formats"
            acquisition_mode = "manual_or_allow_download_geo"
        else:
            next_action = "manual approved acquisition required"
            acquisition_mode = "manual"
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "source": row["source"],
                "collection_name": row["collection_name"],
                "priority_rank": int(row["priority_rank"]),
                "approved_for_pretraining": True,
                "local_matrix_found": local_found,
                "local_matrix_loaded": matrix_loaded,
                "download_default_allowed": False,
                "requires_allow_download_flag": True,
                "acquisition_mode": acquisition_mode,
                "exact_next_action": next_action,
                "clean_validation_boundary": "using this dataset for pretraining forfeits clean-validation use",
            }
        )
    return pd.DataFrame(rows)


def inventory_local_matrices(cfg: dict[str, Any], registry: pd.DataFrame, role_audit: pd.DataFrame) -> pd.DataFrame:
    files = s32.find_matrices(cfg)
    rows = []
    metadata_candidates = cfg["metadata_column_candidates"]
    for path in files:
        dataset_id, match_method, match_details = s32.match_file_to_dataset(path, registry)
        role = role_audit[role_audit["dataset_id"] == dataset_id]
        approved = bool(role["approved_for_pretraining"].iloc[0]) if not role.empty else False
        if path.suffix.lower() == ".h5ad" and approved:
            info = s32.inspect_h5ad(path, metadata_candidates)
        elif path.suffix.lower() == ".h5ad":
            info = s32.cheap_skipped_matrix_info(path, "deep_h5ad_inspection_skipped_not_approved_or_ambiguous")
        else:
            info = s32.inspect_generic_matrix(path)
        rows.append(
            {
                "matrix_local_path": str(path.relative_to(ROOT)),
                "file_size_bytes": int(path.stat().st_size),
                "matrix_format": path.suffix.lower(),
                "matched_dataset_id": dataset_id,
                "registry_match_method": match_method,
                "registry_match_details": match_details,
                "approved_registry_match": approved,
                "matrix_found": True,
                **info,
            }
        )
    return pd.DataFrame(rows)


def write_report(
    cfg: dict[str, Any],
    download_plan: pd.DataFrame,
    inventory: pd.DataFrame,
    gene_overlap: pd.DataFrame,
    metadata_schema: pd.DataFrame,
    holdout: pd.DataFrame,
    manifest: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    row = pass_fail.iloc[0]
    lines = [
        "# Stage 32B approved external pretraining acquisition/build report v1",
        "",
        "## Executive summary",
        "",
        f"Registry datasets scanned: `{int(row.n_registry_datasets_scanned)}`. Approved pretraining candidates: `{int(row.n_approved_pretraining_candidates)}`. Local matrices found: `{int(row.n_local_matrices_found)}`. Matrices included: `{int(row.n_matrices_included)}`. Matrix built: `{bool(row.stage32b_matrix_built)}`. Ready for Stage 33A: `{bool(row.stage32b_ready_for_stage33a)}`.",
        "",
        "## Boundary",
        "",
        "Stage 32B is not external validation, does not train a model, does not use external labels for model selection, and does not update manuscript claims. Datasets used for self-supervised pretraining are forfeited as clean validation.",
        "",
        "## Candidate download/build plan",
        "",
        "```csv",
        download_plan.to_csv(index=False).strip(),
        "```",
        "",
        "## Approved matrix inventory",
        "",
        "```csv",
        inventory.to_csv(index=False).strip(),
        "```",
        "",
        "## Gene overlap audit",
        "",
        "```csv",
        gene_overlap.to_csv(index=False).strip(),
        "```",
        "",
        "## Metadata schema audit",
        "",
        "```csv",
        metadata_schema.to_csv(index=False).strip(),
        "```",
        "",
        "## Holdout protection audit",
        "",
        "```csv",
        holdout.to_csv(index=False).strip(),
        "```",
        "",
        "## Matrix manifest",
        "",
        "```csv",
        manifest.to_csv(index=False).strip(),
        "```",
        "",
        "## Pass/fail",
        "",
        "```csv",
        pass_fail.to_csv(index=False).strip(),
        "```",
        "",
        "## Next action",
        "",
        (
            "Stage 33A may run using the built approved external pretraining matrix."
            if bool(row.stage32b_ready_for_stage33a)
            else "Stage 33A must be skipped until one specific approved pretraining candidate is manually approved/downloaded/built or an approved local matrix is provided."
        ),
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(pass_fail: pd.DataFrame) -> None:
    row = pass_fail.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    new = {
        "scorecard_item": "stage32b_external_pretraining_acquisition",
        "status": "complete",
        "stage": "Stage 32B",
        "metric": "approved external matrix acquisition/build audit",
        "threshold_or_gate": "registry-approved pretraining only; no protected holdouts; no ambiguous matches",
        "current_value": f"matrix_built={bool(row.stage32b_matrix_built)}",
        "pass_fail": "pass" if bool(row.stage32b_pass) else "fail",
        "datasets_allowed": "registry-approved self-supervised pretraining candidates only",
        "datasets_forbidden": "clean holdouts; SEA-AD; already-used plausibility-only; stress-test-only; ambiguous registry matches",
        "allowed_claim": "Stage 32B acquisition/build audit complete",
        "notes": f"stage33a_ready={bool(row.stage32b_ready_for_stage33a)}; no external validation or model-selection claim.",
    }
    score = score[score["scorecard_item"] != "stage32b_external_pretraining_acquisition"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)

    active_path = ROOT / "docs" / "ACTIVE_V3_STATUS.md"
    text = active_path.read_text(encoding="utf-8")
    marker = "\n\n## Stage 32B external pretraining acquisition status\n"
    addition = (
        marker
        + f"\nStage 32B acquisition/build audit is complete. Matrix built: `{bool(row.stage32b_matrix_built)}`; "
        + f"Stage 33A ready: `{bool(row.stage32b_ready_for_stage33a)}`. "
        + "If no matrix was built, next action is manual approval/download/build of a specific approved pretraining candidate. "
        + "External validation remains not run and in silico ablation remains unvalidated.\n"
    )
    active_path.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")

    score_doc = ROOT / "docs" / "V3_SCORECARD.md"
    text = score_doc.read_text(encoding="utf-8")
    marker = "\n\n## Stage 32B external pretraining acquisition result\n"
    addition = (
        marker
        + f"\nStage 32B pass: `{bool(row.stage32b_pass)}`; matrix built: `{bool(row.stage32b_matrix_built)}`; "
        + f"Stage 33A ready: `{bool(row.stage32b_ready_for_stage33a)}`.\n"
    )
    score_doc.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/data/stage32b_approved_external_pretraining_acquisition_v1.yaml")
    parser.add_argument("--allow-download", action="store_true")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    if args.allow_download or bool(cfg.get("allow_download", False)):
        raise NotImplementedError("Stage 32B v1 writes exact acquisition plans; automated download is not implemented.")

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = resolve(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    project_genes = s32.canonical_target_gene_universe(resolve(cfg["canonical_gene_universe_path"]))
    registry = pd.read_csv(resolve(cfg["registry_path"]))
    role_audit = approved_role_audit(registry)
    inventory = inventory_local_matrices(cfg, registry, role_audit)
    if inventory.empty:
        inventory = pd.DataFrame(columns=["matrix_local_path", "matched_dataset_id", "approved_registry_match", "matrix_loaded"])
    download_plan = make_download_plan(cfg, role_audit, inventory)

    gene_rows = []
    metadata_rows = []
    manifest_rows = []
    for _, inv in inventory.iterrows():
        dataset_id = str(inv.get("matched_dataset_id", ""))
        role = role_audit[role_audit["dataset_id"] == dataset_id]
        reg = registry[registry["dataset_id"] == dataset_id]
        approved = bool(role["approved_for_pretraining"].iloc[0]) if not role.empty else False
        path = resolve(inv["matrix_local_path"])
        if approved and bool(inv.get("matrix_loaded")) and path.suffix.lower() == ".h5ad":
            overlap = s32.gene_overlap_for_h5ad(path, project_genes)
        else:
            overlap = {
                "n_genes_raw": int(inv.get("n_genes_raw", 0) or 0),
                "n_genes_aligned": 0,
                "gene_overlap_fraction": 0.0,
                "gene_overlap_status": "not_evaluated_excluded_or_unsupported",
                "missing_gene_count": len(project_genes),
            }
        reasons = []
        if not dataset_id:
            reasons.append("no_confident_registry_match")
        if not approved:
            reasons.append("not_approved_for_pretraining")
        if not bool(inv.get("matrix_loaded")):
            reasons.append("matrix_not_loaded_or_unsupported")
        if overlap["gene_overlap_fraction"] < float(cfg["main_matrix_min_gene_overlap_fraction"]):
            reasons.append("gene_overlap_below_0_85")
        included = not reasons
        dataset_name = reg["dataset_name"].iloc[0] if not reg.empty else ""
        source = reg["source_type"].iloc[0] if not reg.empty else ""
        registry_role = reg["role"].iloc[0] if not reg.empty else ""
        gene_rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "matrix_local_path": inv["matrix_local_path"],
                **overlap,
                "gene_alignment_method": "case_insensitive_hgnc_intersect_only",
                "mouse_ortholog_warning": "mouse datasets excluded unless approved ortholog mapping is present" if dataset_id.startswith("mouse") or source == "GEO" and "Mouse" in dataset_name else "",
                "included_in_pretraining_matrix": included,
                "exclusion_reason": "; ".join(reasons) if reasons else "none",
            }
        )
        metadata_rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "matrix_local_path": inv["matrix_local_path"],
                "matrix_loaded": bool(inv.get("matrix_loaded")),
                "n_cells_or_rows": int(inv.get("n_cells_or_rows", 0) or 0),
                "n_donors_or_samples": int(inv.get("n_donors_or_samples", 0) or 0),
                "cell_type_column": inv.get("cell_type_column", ""),
                "donor_column": inv.get("donor_column", ""),
                "disease_column": inv.get("disease_column", ""),
                "tissue_column": inv.get("tissue_column", ""),
                "species_column": inv.get("species_column", ""),
                "normalization_status": inv.get("normalization_status", ""),
                "schema_warning": inv.get("warnings", ""),
            }
        )
        manifest_rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "source": source,
                "registry_role": registry_role,
                "matrix_local_path": inv["matrix_local_path"],
                "matrix_found": True,
                "matrix_loaded": bool(inv.get("matrix_loaded")),
                "n_cells_or_rows": int(inv.get("n_cells_or_rows", 0) or 0),
                "n_genes_raw": int(overlap["n_genes_raw"]),
                "n_genes_aligned": int(overlap["n_genes_aligned"]),
                "gene_overlap_fraction": float(overlap["gene_overlap_fraction"]),
                "included_in_pretraining_matrix": included,
                "exclusion_reason": "; ".join(reasons) if reasons else "none",
                "used_dataset_removed_from_clean_validation_pool": included,
            }
        )

    gene_overlap = pd.DataFrame(gene_rows)
    metadata_schema = pd.DataFrame(metadata_rows)
    manifest = pd.DataFrame(manifest_rows)
    for frame, columns in [
        (gene_overlap, ["dataset_id", "dataset_name", "matrix_local_path", "n_genes_raw", "n_genes_aligned", "gene_overlap_fraction", "gene_overlap_status", "missing_gene_count", "gene_alignment_method", "mouse_ortholog_warning", "included_in_pretraining_matrix", "exclusion_reason"]),
        (metadata_schema, ["dataset_id", "dataset_name", "matrix_local_path", "matrix_loaded", "n_cells_or_rows", "n_donors_or_samples", "cell_type_column", "donor_column", "disease_column", "tissue_column", "species_column", "normalization_status", "schema_warning"]),
        (manifest, ["dataset_id", "dataset_name", "source", "registry_role", "matrix_local_path", "matrix_found", "matrix_loaded", "n_cells_or_rows", "n_genes_raw", "n_genes_aligned", "gene_overlap_fraction", "included_in_pretraining_matrix", "exclusion_reason", "used_dataset_removed_from_clean_validation_pool"]),
    ]:
        if frame.empty:
            for column in columns:
                frame[column] = []

    holdout_rows = []
    for _, role in role_audit.iterrows():
        protected = bool(role["clean_holdout_protected"] or role["stress_test_only"] or role["plausibility_only"] or role["internal_dataset"] or role["model_selection_excluded"])
        inv = inventory[inventory["matched_dataset_id"] == role["dataset_id"]]
        man = manifest[manifest["dataset_id"] == role["dataset_id"]]
        included = bool(man["included_in_pretraining_matrix"].any()) if not man.empty else False
        if protected or included:
            holdout_rows.append(
                {
                    "dataset_id": role["dataset_id"],
                    "dataset_name": role["dataset_name"],
                    "registry_role": role["registry_role"],
                    "normalized_role": role["normalized_role"],
                    "clean_holdout_protected": bool(role["clean_holdout_protected"]),
                    "stress_test_only": bool(role["stress_test_only"]),
                    "plausibility_only": bool(role["plausibility_only"]),
                    "internal_dataset": bool(role["internal_dataset"]),
                    "matrix_found": bool(not inv.empty),
                    "matrix_loaded": bool(inv["matrix_loaded"].any()) if not inv.empty else False,
                    "included": included,
                    "protection_pass": not (protected and included),
                }
            )
    holdout = pd.DataFrame(holdout_rows)

    included = manifest[manifest["included_in_pretraining_matrix"]].copy()
    matrix_built = False
    matrix_path = ""
    if not included.empty:
        # Reuse Stage 32 alignment builder, then rename outputs to Stage 32B names.
        matrix_built, matrix_path = s32.build_aligned_h5ad(included, registry, project_genes, cfg, output_dir)
        if matrix_built:
            old = output_dir / s32.MATRIX_FILE
            if old.exists():
                old.rename(output_dir / MATRIX_FILE)
                matrix_path = str((output_dir / MATRIX_FILE).relative_to(ROOT))
            for old_name, new_name in [
                (s32.METADATA_FILE, METADATA_FILE),
                (s32.GENE_MAP_FILE, GENE_MAP_FILE),
                (s32.JSON_MANIFEST_FILE, JSON_MANIFEST_FILE),
            ]:
                old_path = output_dir / old_name
                if old_path.exists():
                    old_path.rename(output_dir / new_name)

    role_ok = not role_audit.empty
    holdouts_protected = bool(holdout["protection_pass"].all()) if not holdout.empty else True
    no_forbidden = True
    if not included.empty:
        included_roles = role_audit[role_audit["dataset_id"].isin(set(included["dataset_id"]))]
        no_forbidden = bool(included_roles["approved_for_pretraining"].all())
    audit_complete = all([role_ok, holdouts_protected, no_forbidden, not download_plan.empty, not inventory.empty, not gene_overlap.empty, not metadata_schema.empty])
    pass_fail = pd.DataFrame(
        [
            {
                "registry_loaded": True,
                "roles_normalized": role_ok,
                "clean_holdouts_protected": holdouts_protected,
                "no_forbidden_dataset_included": no_forbidden,
                "candidate_download_plan_written": True,
                "matrix_inventory_written": True,
                "gene_overlap_audit_written": True,
                "metadata_schema_audit_written": True,
                "manifest_written": True,
                "stage32b_audit_complete": bool(audit_complete),
                "stage32b_matrix_built": bool(matrix_built),
                "stage32b_ready_for_stage33a": bool(matrix_built and not included.empty),
                "stage32b_pass": bool(audit_complete),
                "n_registry_datasets_scanned": int(len(registry)),
                "n_approved_pretraining_candidates": int(role_audit["approved_for_pretraining"].sum()),
                "n_local_matrices_found": int(len(inventory)),
                "n_matrices_included": int(len(included)),
                "included_dataset_ids": ";".join(sorted(set(included["dataset_id"].astype(str)))) if not included.empty else "",
                "matrix_path": matrix_path,
            }
        ]
    )

    download_plan.to_csv(DOWNLOAD_PLAN_OUT, index=False)
    inventory.to_csv(INVENTORY_OUT, index=False)
    gene_overlap.to_csv(GENE_OVERLAP_OUT, index=False)
    metadata_schema.to_csv(METADATA_SCHEMA_OUT, index=False)
    holdout.to_csv(HOLDOUT_AUDIT_OUT, index=False)
    manifest.to_csv(MANIFEST_OUT, index=False)
    pass_fail.to_csv(PASS_FAIL_OUT, index=False)
    if not matrix_built:
        (output_dir / JSON_MANIFEST_FILE).write_text(
            json.dumps(
                {
                    "stage": cfg["stage"],
                    "matrix_built": False,
                    "source_dataset_ids": [],
                    "reason": "no approved local matrix confidently matched and passing gene-overlap gate",
                    "next_action": "manual approval/download/build of one approved candidate, then rerun Stage 32B",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    write_report(cfg, download_plan, inventory, gene_overlap, metadata_schema, holdout, manifest, pass_fail)
    update_status(pass_fail)

    required = [DOWNLOAD_PLAN_OUT, INVENTORY_OUT, GENE_OVERLAP_OUT, METADATA_SCHEMA_OUT, HOLDOUT_AUDIT_OUT, MANIFEST_OUT, PASS_FAIL_OUT, REPORT_OUT]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Stage 32B outputs: " + "; ".join(missing))

    row = pass_fail.iloc[0]
    print(f"stage32b_registry_datasets_scanned={int(row.n_registry_datasets_scanned)}")
    print(f"approved_pretraining_candidates={int(row.n_approved_pretraining_candidates)}")
    print(f"stage32b_matrix_built={bool(row.stage32b_matrix_built)}")
    print(f"included_datasets={row.included_dataset_ids}")
    print(f"matrix_path={row.matrix_path}")
    print(f"stage32b_ready_for_stage33a={bool(row.stage32b_ready_for_stage33a)}")


if __name__ == "__main__":
    main()
