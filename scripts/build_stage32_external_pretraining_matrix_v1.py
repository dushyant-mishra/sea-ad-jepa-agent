from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import yaml
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

ROLE_AUDIT_OUT = TABLE_DIR / "stage32_external_dataset_role_audit_v1.csv"
INVENTORY_OUT = TABLE_DIR / "stage32_external_matrix_inventory_v1.csv"
GENE_OVERLAP_OUT = TABLE_DIR / "stage32_external_gene_overlap_v1.csv"
CELL_SUMMARY_OUT = TABLE_DIR / "stage32_external_cell_sample_summary_v1.csv"
MATRIX_MANIFEST_OUT = TABLE_DIR / "stage32_external_pretraining_matrix_manifest_v1.csv"
HOLDOUT_AUDIT_OUT = TABLE_DIR / "stage32_external_holdout_protection_audit_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage32_external_pretraining_build_pass_fail_v1.csv"
REPORT_OUT = REPORT_DIR / "stage32_external_pretraining_matrix_report_v1.md"

STATUS_SCORECARD = TABLE_DIR / "v3_scorecard_status_v1.csv"

MATRIX_FILE = "stage32_external_pretraining_matrix.h5ad"
METADATA_FILE = "stage32_external_pretraining_matrix_metadata.csv"
GENE_MAP_FILE = "stage32_external_pretraining_gene_map.csv"
JSON_MANIFEST_FILE = "stage32_external_pretraining_manifest.json"
GENERIC_MATCH_TOKENS = {
    "microglia",
    "allcells",
    "fulldataset",
    "whole taxonomy",
    "wholetaxonomy",
    "allnonneuronalcells",
}


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def norm_text(value: Any) -> str:
    return str(value if not pd.isna(value) else "").strip()


def token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", norm_text(value).lower())


def canonical_target_gene_universe(path: Path) -> list[str]:
    edges = pd.read_csv(path)
    required = {"source", "target"}
    if not required.issubset(edges.columns):
        raise ValueError(f"{path} lacks required columns: {sorted(required)}")
    source_genes = set(edges["source"].astype(str))
    target_genes = set(edges["target"].astype(str))
    union_genes = source_genes | target_genes
    if len(source_genes) != 2957 or len(target_genes) != 2957 or len(union_genes) != 2957:
        raise ValueError(
            "Canonical gene universe mismatch: "
            f"source={len(source_genes)}, target={len(target_genes)}, union={len(union_genes)}; expected 2957"
        )
    return edges[["source", "source_idx"]].drop_duplicates("source_idx").sort_values("source_idx")[
        "source"
    ].astype(str).tolist()


def normalize_role(row: pd.Series) -> dict[str, Any]:
    role = norm_text(row.get("role"))
    stage_allowed = norm_text(row.get("stage_allowed"))
    notes = norm_text(row.get("notes"))
    role_text = " ".join([role, stage_allowed, notes]).lower()
    allowed_for_pretraining = as_bool(row.get("allowed_for_pretraining"))
    reserved_holdout = as_bool(row.get("reserved_for_clean_validation"))
    model_selection = as_bool(row.get("allowed_for_model_selection"))
    already_used = as_bool(row.get("already_used"))
    internal = "sea-ad" in norm_text(row.get("source_type")).lower() or role == "main_internal_benchmark"
    stress = "stress" in role_text
    plausibility = "plausibility" in role_text
    clean_holdout = reserved_holdout or "clean_external_holdout" in role_text
    explicitly_approved = allowed_for_pretraining
    excluded = []
    if not explicitly_approved:
        excluded.append("not_allowed_for_pretraining")
    if reserved_holdout or clean_holdout:
        excluded.append("clean_holdout_protected")
    if model_selection:
        excluded.append("model_selection_dataset_excluded")
    if already_used and not explicitly_approved:
        excluded.append("already_used_without_pretraining_approval")
    if stress:
        excluded.append("stress_test_only")
    if plausibility and not explicitly_approved:
        excluded.append("plausibility_only")
    if internal:
        excluded.append("internal_sea_ad_excluded")
    approved = explicitly_approved and not any(
        reason
        in {
            "clean_holdout_protected",
            "model_selection_dataset_excluded",
            "stress_test_only",
            "plausibility_only",
            "internal_sea_ad_excluded",
        }
        for reason in excluded
    )
    normalized_role = (
        "approved_self_supervised_pretraining"
        if approved
        else "protected_clean_holdout"
        if clean_holdout
        else "excluded_stress_test"
        if stress
        else "excluded_plausibility_only"
        if plausibility
        else "excluded_internal"
        if internal
        else "not_approved_for_pretraining"
    )
    return {
        "registry_role": role,
        "normalized_role": normalized_role,
        "approved_for_pretraining": bool(approved),
        "clean_holdout_protected": bool(clean_holdout),
        "stress_test_only": bool(stress),
        "plausibility_only": bool(plausibility and not approved),
        "internal_dataset": bool(internal),
        "model_selection_excluded": bool(model_selection),
        "already_used": bool(already_used),
        "role_exclusion_reason": "; ".join(excluded) if excluded else "none",
    }


def find_matrices(cfg: dict[str, Any]) -> list[Path]:
    exts = {str(ext).lower() for ext in cfg["matrix_extensions"]}
    files: list[Path] = []
    for root in cfg["matrix_search_roots"]:
        path = resolve(root)
        if not path.exists():
            continue
        for candidate in path.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in exts:
                files.append(candidate)
    return sorted(files)


def candidate_terms(row: pd.Series) -> list[str]:
    values = [
        row.get("dataset_id"),
        row.get("dataset_name"),
        row.get("collection_name"),
    ]
    out = []
    for value in values:
        raw = norm_text(value)
        if raw:
            out.append(raw)
            out.append(token(raw))
    return [item for item in out if item]


def match_file_to_dataset(path: Path, registry: pd.DataFrame) -> tuple[str, str, str]:
    file_text = token(path.stem + " " + path.parent.name + " " + str(path.relative_to(ROOT)))
    strong_matches = []
    weak_matches = []
    for _, row in registry.iterrows():
        dataset_id = norm_text(row.get("dataset_id"))
        dataset_name = norm_text(row.get("dataset_name"))
        collection = norm_text(row.get("collection_name"))
        id_token = token(dataset_id)
        name_token = token(dataset_name)
        collection_token = token(collection)
        if id_token and id_token in file_text:
            strong_matches.append((dataset_id, "dataset_id_token_match"))
        elif (
            name_token
            and len(name_token) >= 8
            and name_token not in GENERIC_MATCH_TOKENS
            and name_token in file_text
        ):
            strong_matches.append((dataset_id, "dataset_name_token_match"))
        elif (
            collection_token
            and len(collection_token) >= 10
            and collection_token not in GENERIC_MATCH_TOKENS
            and collection_token in file_text
        ):
            weak_matches.append((dataset_id, "collection_name_token_match"))
    matches = strong_matches or weak_matches
    if len(matches) == 1:
        return matches[0][0], matches[0][1], "unique_match"
    if len(matches) > 1:
        return "", "ambiguous_match", ";".join(f"{m[0]}:{m[1]}" for m in matches)
    return "", "no_registry_match", ""


def inspect_h5ad(path: Path, metadata_candidates: dict[str, list[str]]) -> dict[str, Any]:
    info: dict[str, Any] = {
        "matrix_loaded": False,
        "n_cells_or_rows": 0,
        "n_donors_or_samples": 0,
        "n_genes_raw": 0,
        "var_name_example": "",
        "cell_type_column": "",
        "donor_column": "",
        "disease_column": "",
        "tissue_column": "",
        "species_column": "",
        "normalization_status": "not_loaded",
        "warnings": "",
    }
    try:
        adata = ad.read_h5ad(path, backed="r")
        info["matrix_loaded"] = True
        info["n_cells_or_rows"] = int(adata.n_obs)
        info["n_genes_raw"] = int(adata.n_vars)
        info["var_name_example"] = ";".join(map(str, list(adata.var_names[:5])))
        obs_cols = list(map(str, adata.obs.columns))
        for key, out_col in [
            ("cell_type", "cell_type_column"),
            ("donor", "donor_column"),
            ("disease", "disease_column"),
            ("tissue", "tissue_column"),
            ("species", "species_column"),
        ]:
            for candidate in metadata_candidates.get(key, []):
                if candidate in obs_cols:
                    info[out_col] = candidate
                    break
        donor_col = info["donor_column"]
        if donor_col:
            info["n_donors_or_samples"] = int(adata.obs[donor_col].astype(str).nunique())
        x = adata.X
        sample = x[: min(500, adata.n_obs), : min(500, adata.n_vars)]
        if sparse.issparse(sample):
            arr = sample.data
        else:
            arr = np.asarray(sample).ravel()
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            norm = "unknown_empty_sample"
        elif np.nanmin(arr) < 0:
            norm = "scaled_or_centered_contains_negative_values"
        elif np.allclose(arr, np.round(arr)) and np.nanmax(arr) > 50:
            norm = "raw_count_like"
        elif np.nanmax(arr) <= 30:
            norm = "log_normalized_or_transformed_like"
        else:
            norm = "unknown_nonnegative_expression"
        info["normalization_status"] = norm
        adata.file.close()
    except Exception as exc:  # audit must continue
        info["warnings"] = f"failed_to_inspect_h5ad:{type(exc).__name__}:{exc}"
    return info


def inspect_generic_matrix(path: Path) -> dict[str, Any]:
    return {
        "matrix_loaded": False,
        "n_cells_or_rows": 0,
        "n_donors_or_samples": 0,
        "n_genes_raw": 0,
        "var_name_example": "",
        "cell_type_column": "",
        "donor_column": "",
        "disease_column": "",
        "tissue_column": "",
        "species_column": "",
        "normalization_status": "unsupported_for_automatic_stage32_build",
        "warnings": f"format_{path.suffix.lower()}_inventory_only",
    }


def cheap_skipped_matrix_info(path: Path, reason: str) -> dict[str, Any]:
    return {
        "matrix_loaded": False,
        "n_cells_or_rows": 0,
        "n_donors_or_samples": 0,
        "n_genes_raw": 0,
        "var_name_example": "",
        "cell_type_column": "",
        "donor_column": "",
        "disease_column": "",
        "tissue_column": "",
        "species_column": "",
        "normalization_status": "not_inspected_excluded_or_large",
        "warnings": reason,
    }


def gene_overlap_for_h5ad(path: Path, project_genes: list[str]) -> dict[str, Any]:
    result = {
        "n_genes_raw": 0,
        "n_genes_aligned": 0,
        "gene_overlap_fraction": 0.0,
        "gene_overlap_status": "not_loaded",
        "missing_gene_count": len(project_genes),
    }
    try:
        adata = ad.read_h5ad(path, backed="r")
        vars_upper = {str(v).upper(): str(v) for v in adata.var_names}
        project_upper = [gene.upper() for gene in project_genes]
        overlap = [gene for gene in project_upper if gene in vars_upper]
        frac = len(overlap) / len(project_genes)
        if frac >= 0.90:
            status = "good"
        elif frac >= 0.85:
            status = "usable_with_warning"
        else:
            status = "risky_below_0_85"
        result.update(
            {
                "n_genes_raw": int(adata.n_vars),
                "n_genes_aligned": int(len(overlap)),
                "gene_overlap_fraction": float(frac),
                "gene_overlap_status": status,
                "missing_gene_count": int(len(project_genes) - len(overlap)),
            }
        )
        adata.file.close()
    except Exception:
        pass
    return result


def build_aligned_h5ad(
    included: pd.DataFrame,
    registry: pd.DataFrame,
    project_genes: list[str],
    cfg: dict[str, Any],
    output_dir: Path,
) -> tuple[bool, str]:
    if included.empty:
        return False, ""
    adatas = []
    metadata_frames = []
    gene_map_rows = []
    project_upper = [gene.upper() for gene in project_genes]
    for _, row in included.iterrows():
        path = resolve(row["matrix_local_path"])
        if path.suffix.lower() != ".h5ad":
            continue
        source = ad.read_h5ad(path)
        source_var = {str(v).upper(): str(v) for v in source.var_names}
        aligned_source_genes = [source_var[gene] for gene in project_upper if gene in source_var]
        aligned_project_genes = [project_genes[i] for i, gene in enumerate(project_upper) if gene in source_var]
        if len(aligned_project_genes) / len(project_genes) < float(cfg["main_matrix_min_gene_overlap_fraction"]):
            continue
        subset = source[:, aligned_source_genes].copy()
        subset.var_names = aligned_project_genes
        subset.obs = subset.obs.copy()
        subset.obs["stage32_source_dataset_id"] = row["dataset_id"]
        subset.obs["stage32_source_dataset_name"] = row["dataset_name"]
        subset.obs["stage32_source_matrix_path"] = str(path.relative_to(ROOT))
        adatas.append(subset)
        meta = subset.obs.copy()
        meta.insert(0, "stage32_row_id", [f"{row['dataset_id']}::{idx}" for idx in meta.index.astype(str)])
        metadata_frames.append(meta.reset_index(drop=False).rename(columns={"index": "source_obs_id"}))
        for project_gene, source_gene in zip(aligned_project_genes, aligned_source_genes):
            gene_map_rows.append(
                {
                    "dataset_id": row["dataset_id"],
                    "project_gene": project_gene,
                    "source_gene": source_gene,
                    "mapping_status": "case_insensitive_symbol_match",
                }
            )
    if not adatas:
        return False, ""
    merged = ad.concat(adatas, join="inner", label="stage32_concat_dataset", keys=[str(i) for i in range(len(adatas))])
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = output_dir / MATRIX_FILE
    merged.write_h5ad(matrix_path)
    pd.concat(metadata_frames, ignore_index=True).to_csv(output_dir / METADATA_FILE, index=False)
    pd.DataFrame(gene_map_rows).to_csv(output_dir / GENE_MAP_FILE, index=False)
    manifest = {
        "stage": cfg["stage"],
        "matrix_path": str(matrix_path.relative_to(ROOT)),
        "n_rows": int(merged.n_obs),
        "n_genes": int(merged.n_vars),
        "source_dataset_ids": sorted(set(included["dataset_id"].astype(str))),
        "normalization": cfg["normalization"],
        "validation_boundary": "datasets_used_for_pretraining_are_removed_from_clean_validation_pool",
    }
    (output_dir / JSON_MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return True, str(matrix_path.relative_to(ROOT))


def update_status(pass_fail: pd.DataFrame) -> None:
    row = pass_fail.iloc[0]
    score = pd.read_csv(STATUS_SCORECARD)
    new = {
        "scorecard_item": "stage32_external_pretraining_matrix",
        "status": "complete",
        "stage": "Stage 32",
        "metric": "external pretraining matrix audit/build",
        "threshold_or_gate": "registry loaded; holdouts protected; only approved pretraining datasets included; manifest written",
        "current_value": f"matrix_built={bool(row.matrix_built)}",
        "pass_fail": "pass" if bool(row.stage32_pass) else "fail",
        "datasets_allowed": "registry-approved self-supervised pretraining datasets only",
        "datasets_forbidden": "clean holdouts; model-selection datasets; stress/plausibility-only; internal SEA-AD",
        "allowed_claim": "external pretraining matrix audit/build complete",
        "notes": (
            f"stage33_ready={bool(row.stage32_ready_for_stage33)}; "
            "Stage 27C remains current best internal no-graph benchmark; Stage 30/31 did not establish graph-specific pass; "
            "external validation not run; ablation validity not established."
        ),
    }
    score = score[score["scorecard_item"] != "stage32_external_pretraining_matrix"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(STATUS_SCORECARD, index=False)

    active_path = ROOT / "docs" / "ACTIVE_V3_STATUS.md"
    text = active_path.read_text(encoding="utf-8")
    marker = "\n\n## Stage 32 external pretraining matrix status\n"
    addition = (
        marker
        + "\nStage 32 external pretraining matrix audit/build is complete. "
        + f"Matrix built: `{bool(row.matrix_built)}`; Stage 33 ready: `{bool(row.stage32_ready_for_stage33)}`. "
        + "Stage 27C remains the current best internal no-graph benchmark. Stage 30 mandatory graph controls failed graph-specific pass. "
        + "Stage 31 weak residual graph nearly matched Stage 27C but did not beat it. External validation remains not run, "
        + "and in silico ablation remains unvalidated.\n"
    )
    active_path.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")

    score_doc = ROOT / "docs" / "V3_SCORECARD.md"
    text = score_doc.read_text(encoding="utf-8")
    marker = "\n\n## Stage 32 external pretraining matrix result\n"
    addition = (
        marker
        + f"\nAudit complete: `{bool(row.audit_complete)}`; matrix built: `{bool(row.matrix_built)}`; "
        + f"Stage 33 may proceed: `{bool(row.stage32_ready_for_stage33)}`. "
        + "No model was trained and no benchmark/manuscript claims are updated.\n"
    )
    score_doc.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")


def write_report(
    cfg: dict[str, Any],
    role_audit: pd.DataFrame,
    inventory: pd.DataFrame,
    gene_overlap: pd.DataFrame,
    cell_summary: pd.DataFrame,
    manifest: pd.DataFrame,
    holdout: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    row = pass_fail.iloc[0]
    approved = role_audit[role_audit["approved_for_pretraining"]]
    protected = holdout[holdout["clean_holdout_protected"] | holdout["stress_test_only"] | holdout["plausibility_only"]]
    included = manifest[manifest["included_in_pretraining_matrix"]]
    next_action = (
        "Stage 33 can proceed using the built approved aligned matrix."
        if bool(row.stage32_ready_for_stage33)
        else "Stage 33 should not proceed until an approved registry pretraining dataset has a local processed matrix or download/build approval is granted."
    )
    lines = [
        "# Stage 32 external pretraining matrix report v1",
        "",
        "## 1. Executive summary",
        "",
        f"Registry datasets scanned: `{int(row.n_registry_datasets_scanned)}`. Approved for pretraining: `{int(row.n_approved_for_pretraining)}`. Local matrices found: `{int(row.n_local_matrices_found)}`. Matrices included: `{int(row.n_matrices_included)}`. Matrix built: `{bool(row.matrix_built)}`. Stage 33 ready: `{bool(row.stage32_ready_for_stage33)}`.",
        "",
        "## 2. Why Stage 32 was run",
        "",
        "Stage 31 showed that weak residual graph diffusion nearly matched but did not beat Stage 27C. The next useful step is to build an approved external self-supervised pretraining substrate, not to keep tuning the 84-donor supervised benchmark.",
        "",
        "## 3. Stage 27C / Stage 30 / Stage 31 recap",
        "",
        "Stage 27C remains the current best internal no-graph benchmark at mean pooled OOF Spearman 0.326702. Stage 30 mandatory graph smoothing failed graph-specific pass. Stage 31 weak residual graph reached 0.326370 but did not beat Stage 27C/no-graph.",
        "",
        "## 4. Dataset role policy",
        "",
        "Primary inclusion gate: `allowed_for_pretraining == True`. Always excluded: reserved clean validation, model-selection datasets, stress-test-only datasets, plausibility-only datasets without explicit pretraining approval, already-used datasets without explicit pretraining approval, internal SEA-AD files, and clean AD/dementia holdout candidates.",
        "",
        "## 5. Approved pretraining candidates",
        "",
        "Expected currently approved set from config: `" + ", ".join(cfg["expected_currently_approved_pretraining_dataset_ids"]) + "`.",
        "",
        "```csv",
        approved.to_csv(index=False).strip(),
        "```",
        "",
        "## 6. Protected holdouts",
        "",
        "```csv",
        protected.to_csv(index=False).strip(),
        "```",
        "",
        "## 7. Matrix inventory",
        "",
        "```csv",
        inventory.to_csv(index=False).strip(),
        "```",
        "",
        "## 8. Gene overlap and alignment",
        "",
        "Canonical gene universe source: `results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv`; verified source/target/union gene counts equal 2,957.",
        "",
        "```csv",
        gene_overlap.to_csv(index=False).strip(),
        "```",
        "",
        "## 9. Normalization status",
        "",
        "No arbitrary normalization was applied. Source matrix status was inspected heuristically when H5AD files were readable. Missing gene method: intersect-only, no imputation.",
        "",
        "## 10. Matrix build result",
        "",
        "```csv",
        manifest.to_csv(index=False).strip(),
        "```",
        "",
        "## 11. Holdout protection result",
        "",
        "```csv",
        holdout.to_csv(index=False).strip(),
        "```",
        "",
        "## 12. Pass/fail decision",
        "",
        "```csv",
        pass_fail.to_csv(index=False).strip(),
        "```",
        "",
        "## 13. Whether Stage 33 can proceed",
        "",
        next_action,
        "",
        "## 14. Required next actions",
        "",
        "- If no matrix was built, select/download/build one of the approved pretraining datasets with explicit approval, then rerun Stage 32.",
        "- If a matrix was built, Stage 33 may use it for self-supervised pretraining only; used datasets must not later be claimed as clean validation.",
        "",
        "## 15. Interpretation boundary",
        "",
        "Stage 32 does not train a model. Stage 32 does not update benchmark results. Stage 32 does not create graph-specific evidence. Stage 32 does not validate in silico ablation. Stage 32 does not create clean external validation. Any dataset used for pretraining is removed from the clean-validation pool.",
        "",
        "## Cell/sample summary",
        "",
        "```csv",
        cell_summary.to_csv(index=False).strip(),
        "```",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/data/stage32_external_pretraining_matrix_v1.yaml")
    parser.add_argument("--allow-download", action="store_true")
    args = parser.parse_args()

    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = resolve(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    allow_download = bool(args.allow_download or cfg.get("allow_download", False))
    if allow_download:
        raise NotImplementedError("--allow-download is opt-in but no downloader is implemented in Stage 32 v1")

    project_genes = canonical_target_gene_universe(resolve(cfg["canonical_gene_universe_path"]))
    registry = pd.read_csv(resolve(cfg["registry_path"]))
    role_rows = []
    for _, row in registry.iterrows():
        role_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row.get("dataset_name", ""),
                "source": row.get("source_type", ""),
                "collection_name": row.get("collection_name", ""),
                "registry_role": row.get("role", ""),
                **normalize_role(row),
            }
        )
    role_audit = pd.DataFrame(role_rows)

    files = find_matrices(cfg)
    inventory_rows = []
    metadata_candidates = cfg["metadata_column_candidates"]
    for path in files:
        dataset_id, match_method, match_details = match_file_to_dataset(path, registry)
        role = role_audit[role_audit["dataset_id"] == dataset_id]
        approved = bool(role["approved_for_pretraining"].iloc[0]) if not role.empty else False
        if path.suffix.lower() == ".h5ad" and approved:
            info = inspect_h5ad(path, metadata_candidates)
        elif path.suffix.lower() == ".h5ad":
            info = cheap_skipped_matrix_info(path, "deep_h5ad_inspection_skipped_not_approved_registry_match")
        else:
            info = inspect_generic_matrix(path)
        inventory_rows.append(
            {
                "matrix_local_path": str(path.relative_to(ROOT)),
                "file_size_bytes": int(path.stat().st_size),
                "matrix_format": path.suffix.lower(),
                "matched_dataset_id": dataset_id,
                "registry_match_method": match_method,
                "registry_match_details": match_details,
                "matrix_found": True,
                "approved_registry_match": approved,
                **info,
            }
        )
    inventory = pd.DataFrame(inventory_rows)
    if inventory.empty:
        inventory = pd.DataFrame(
            columns=[
                "matrix_local_path",
                "file_size_bytes",
                "matrix_format",
                "matched_dataset_id",
                "registry_match_method",
                "registry_match_details",
                "matrix_found",
                "approved_registry_match",
                "matrix_loaded",
                "n_cells_or_rows",
                "n_donors_or_samples",
                "n_genes_raw",
                "var_name_example",
                "cell_type_column",
                "donor_column",
                "disease_column",
                "tissue_column",
                "species_column",
                "normalization_status",
                "warnings",
            ]
        )

    role_lookup = role_audit.set_index("dataset_id")
    gene_rows = []
    cell_rows = []
    manifest_rows = []
    for _, inv in inventory.iterrows():
        dataset_id = inv["matched_dataset_id"]
        registry_row = registry[registry["dataset_id"] == dataset_id]
        role_row = role_lookup.loc[dataset_id] if dataset_id in role_lookup.index else None
        path = resolve(inv["matrix_local_path"])
        approved = bool(role_row["approved_for_pretraining"]) if role_row is not None else False
        if path.suffix.lower() == ".h5ad" and approved and bool(inv.get("matrix_loaded")):
            overlap = gene_overlap_for_h5ad(path, project_genes)
        else:
            overlap = {
                "n_genes_raw": int(inv.get("n_genes_raw", 0) or 0),
                "n_genes_aligned": 0,
                "gene_overlap_fraction": 0.0,
                "gene_overlap_status": "not_evaluated_excluded_or_unsupported",
                "missing_gene_count": len(project_genes),
            }
        excluded_reasons = []
        if not dataset_id:
            excluded_reasons.append("no_confident_registry_match")
        if not approved:
            excluded_reasons.append("not_approved_for_pretraining")
        if bool(inv.get("matrix_loaded")) is not True:
            excluded_reasons.append("matrix_not_loaded_or_unsupported")
        if overlap["gene_overlap_fraction"] < float(cfg["main_matrix_min_gene_overlap_fraction"]):
            excluded_reasons.append("gene_overlap_below_0_85")
        included = not excluded_reasons
        dataset_name = registry_row["dataset_name"].iloc[0] if not registry_row.empty else ""
        source = registry_row["source_type"].iloc[0] if not registry_row.empty else ""
        registry_role = registry_row["role"].iloc[0] if not registry_row.empty else ""
        gene_rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "matrix_local_path": inv["matrix_local_path"],
                **overlap,
                "missing_gene_method": cfg["normalization"]["missing_gene_method"],
                "included_in_pretraining_matrix": included,
                "exclusion_reason": "; ".join(excluded_reasons) if excluded_reasons else "none",
            }
        )
        cell_rows.append(
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
                "warnings": inv.get("warnings", ""),
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
                "exclusion_reason": "; ".join(excluded_reasons) if excluded_reasons else "none",
                "used_dataset_removed_from_clean_validation_pool": included,
            }
        )
    gene_overlap = pd.DataFrame(gene_rows)
    cell_summary = pd.DataFrame(cell_rows)
    matrix_manifest = pd.DataFrame(manifest_rows)
    for df, columns in [
        (gene_overlap, ["dataset_id", "dataset_name", "matrix_local_path", "n_genes_raw", "n_genes_aligned", "gene_overlap_fraction", "gene_overlap_status", "missing_gene_count", "missing_gene_method", "included_in_pretraining_matrix", "exclusion_reason"]),
        (cell_summary, ["dataset_id", "dataset_name", "matrix_local_path", "matrix_loaded", "n_cells_or_rows", "n_donors_or_samples", "cell_type_column", "donor_column", "disease_column", "tissue_column", "species_column", "normalization_status", "warnings"]),
        (matrix_manifest, ["dataset_id", "dataset_name", "source", "registry_role", "matrix_local_path", "matrix_found", "matrix_loaded", "n_cells_or_rows", "n_genes_raw", "n_genes_aligned", "gene_overlap_fraction", "included_in_pretraining_matrix", "exclusion_reason", "used_dataset_removed_from_clean_validation_pool"]),
    ]:
        if df.empty:
            for column in columns:
                df[column] = []

    included = matrix_manifest[matrix_manifest["included_in_pretraining_matrix"]].copy()
    matrix_built, matrix_path = (False, "")
    if bool(cfg["build_matrix_if_approved_local_found"]) and not included.empty:
        matrix_built, matrix_path = build_aligned_h5ad(included, registry, project_genes, cfg, output_dir)

    holdout_rows = []
    for _, role in role_audit.iterrows():
        protected = bool(
            role["clean_holdout_protected"]
            or role["stress_test_only"]
            or role["plausibility_only"]
            or role["internal_dataset"]
            or role["model_selection_excluded"]
        )
        inv_match = inventory[inventory["matched_dataset_id"] == role["dataset_id"]]
        man_match = matrix_manifest[matrix_manifest["dataset_id"] == role["dataset_id"]]
        included_any = bool(man_match["included_in_pretraining_matrix"].any()) if not man_match.empty else False
        if protected or included_any:
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
                    "matrix_found": bool(not inv_match.empty),
                    "matrix_loaded": bool(inv_match["matrix_loaded"].any()) if not inv_match.empty else False,
                    "included": included_any,
                    "protection_pass": not (protected and included_any),
                }
            )
    holdout = pd.DataFrame(holdout_rows)

    n_local = int(len(inventory))
    n_included = int(matrix_manifest["included_in_pretraining_matrix"].sum()) if not matrix_manifest.empty else 0
    clean_holdouts_protected = bool(holdout["protection_pass"].all()) if not holdout.empty else True
    role_loaded = not registry.empty
    role_normalized = not role_audit.empty and "normalized_role" in role_audit.columns
    no_bad_inclusions = True
    if n_included:
        included_ids = set(matrix_manifest.loc[matrix_manifest["included_in_pretraining_matrix"], "dataset_id"])
        included_roles = role_audit[role_audit["dataset_id"].isin(included_ids)]
        no_bad_inclusions = bool(included_roles["approved_for_pretraining"].all())
    matrix_manifest_written = True
    audit_complete = all(
        [
            role_loaded,
            role_normalized,
            clean_holdouts_protected,
            no_bad_inclusions,
            not gene_overlap.empty or n_local == 0,
            matrix_manifest_written,
        ]
    )
    stage32_pass = audit_complete
    stage33_ready = bool(matrix_built and n_included > 0)
    pass_fail = pd.DataFrame(
        [
            {
                "registry_loaded": role_loaded,
                "roles_normalized": role_normalized,
                "audit_complete": bool(audit_complete),
                "holdouts_protected": clean_holdouts_protected,
                "no_clean_holdout_included": clean_holdouts_protected,
                "no_stress_test_only_included": no_bad_inclusions,
                "no_plausibility_only_included": no_bad_inclusions,
                "all_included_datasets_explicitly_approved": no_bad_inclusions,
                "gene_overlap_audit_complete": not gene_overlap.empty or n_local == 0,
                "matrix_manifest_written": matrix_manifest_written,
                "matrix_built": bool(matrix_built),
                "stage32_ready_for_stage33": stage33_ready,
                "stage32_pass": bool(stage32_pass),
                "n_registry_datasets_scanned": int(len(registry)),
                "n_approved_for_pretraining": int(role_audit["approved_for_pretraining"].sum()),
                "n_protected_as_clean_holdout": int(role_audit["clean_holdout_protected"].sum()),
                "n_local_matrices_found": n_local,
                "n_matrices_included": n_included,
                "matrix_path": matrix_path,
                "allow_download": allow_download,
            }
        ]
    )

    ROLE_AUDIT_OUT.write_text(role_audit.to_csv(index=False), encoding="utf-8")
    INVENTORY_OUT.write_text(inventory.to_csv(index=False), encoding="utf-8")
    GENE_OVERLAP_OUT.write_text(gene_overlap.to_csv(index=False), encoding="utf-8")
    CELL_SUMMARY_OUT.write_text(cell_summary.to_csv(index=False), encoding="utf-8")
    MATRIX_MANIFEST_OUT.write_text(matrix_manifest.to_csv(index=False), encoding="utf-8")
    HOLDOUT_AUDIT_OUT.write_text(holdout.to_csv(index=False), encoding="utf-8")
    PASS_FAIL_OUT.write_text(pass_fail.to_csv(index=False), encoding="utf-8")
    write_report(cfg, role_audit, inventory, gene_overlap, cell_summary, matrix_manifest, holdout, pass_fail)
    update_status(pass_fail)

    required = [
        ROLE_AUDIT_OUT,
        INVENTORY_OUT,
        GENE_OVERLAP_OUT,
        CELL_SUMMARY_OUT,
        MATRIX_MANIFEST_OUT,
        HOLDOUT_AUDIT_OUT,
        PASS_FAIL_OUT,
        REPORT_OUT,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Stage 32 outputs: " + "; ".join(missing))

    row = pass_fail.iloc[0]
    print(f"registry_datasets_scanned={int(row.n_registry_datasets_scanned)}")
    print(f"approved_for_pretraining={int(row.n_approved_for_pretraining)}")
    print(f"protected_as_clean_holdout={int(row.n_protected_as_clean_holdout)}")
    print(f"local_matrices_found={int(row.n_local_matrices_found)}")
    print(f"matrices_included={int(row.n_matrices_included)}")
    print(f"matrix_built={bool(row.matrix_built)}")
    print(f"matrix_path={row.matrix_path}")
    print(f"stage32_ready_for_stage33={bool(row.stage32_ready_for_stage33)}")


if __name__ == "__main__":
    main()
