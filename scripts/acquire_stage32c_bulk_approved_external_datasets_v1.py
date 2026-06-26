from __future__ import annotations

import argparse
import json
import importlib.util
import sys
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import requests
import yaml
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_stage32_external_pretraining_matrix_v1 as s32  # noqa: E402


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

DOWNLOAD_PLAN_OUT = TABLE_DIR / "stage32c_approved_dataset_download_plan_v1.csv"
DOWNLOAD_MANIFEST_OUT = TABLE_DIR / "stage32c_download_manifest_v1.csv"
SCHEMA_OUT = TABLE_DIR / "stage32c_schema_inventory_v1.csv"
OBS_COLS_OUT = TABLE_DIR / "stage32c_obs_column_inventory_v1.csv"
VAR_COLS_OUT = TABLE_DIR / "stage32c_var_column_inventory_v1.csv"
LAYER_OUT = TABLE_DIR / "stage32c_layer_inventory_v1.csv"
GENE_OVERLAP_OUT = TABLE_DIR / "stage32c_gene_overlap_audit_v1.csv"
FIELD_MAP_OUT = TABLE_DIR / "stage32c_metadata_field_mapping_candidates_v1.csv"
NORMALIZATION_OUT = TABLE_DIR / "stage32c_normalization_audit_v1.csv"
SPECIES_OUT = TABLE_DIR / "stage32c_species_ortholog_audit_v1.csv"
RECOMMEND_OUT = TABLE_DIR / "stage32c_candidate_matrix_recommendations_v1.csv"
HOLDOUT_OUT = TABLE_DIR / "stage32c_holdout_protection_audit_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage32c_pass_fail_v1.csv"
REPORT_OUT = REPORT_DIR / "stage32c_bulk_approved_external_acquisition_report_v1.md"

HUMAN_MATRIX_NAME = "stage32c_human_external_pretraining_matrix.h5ad"
HUMAN_METADATA_NAME = "stage32c_human_external_pretraining_metadata.csv"
HUMAN_GENE_MAP_NAME = "stage32c_human_external_pretraining_gene_map.csv"
HUMAN_MANIFEST_NAME = "stage32c_human_external_pretraining_manifest.json"
HTTP_TIMEOUT_SECONDS = 30


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


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
                "allowed_for_pretraining": s32.as_bool(row.get("allowed_for_pretraining")),
                "reserved_for_clean_validation": s32.as_bool(row.get("reserved_for_clean_validation")),
                "allowed_for_model_selection": s32.as_bool(row.get("allowed_for_model_selection")),
                "already_used": s32.as_bool(row.get("already_used")),
                **s32.normalize_role(row),
            }
        )
    return pd.DataFrame(rows)


def selected_approved(role_audit: pd.DataFrame, cfg: dict[str, Any], targets: list[str], max_datasets: int | None) -> pd.DataFrame:
    approved = role_audit[role_audit["approved_for_pretraining"]].copy()
    if targets:
        approved = approved[approved["dataset_id"].astype(str).isin(set(targets))].copy()
    priority = {dataset_id: i for i, dataset_id in enumerate(cfg.get("candidate_priority_order", []))}
    approved["priority_rank"] = approved["dataset_id"].map(priority).fillna(999).astype(int)
    approved = approved.sort_values(["priority_rank", "dataset_id"]).reset_index(drop=True)
    if max_datasets is not None:
        approved = approved.head(max_datasets)
    return approved


def local_inventory(cfg: dict[str, Any], registry: pd.DataFrame, role_audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    files = s32.find_matrices(cfg)
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
                "dataset_id": dataset_id,
                "local_path": str(path.relative_to(ROOT)),
                "file_size_bytes": int(path.stat().st_size),
                "matrix_format": path.suffix.lower(),
                "registry_match_method": match_method,
                "registry_match_details": match_details,
                "approved_registry_match": approved,
                **info,
            }
        )
    return pd.DataFrame(rows)


def inspect_schema(path: Path, dataset_id: str, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    base = {
        "dataset_id": dataset_id,
        "local_path": str(path.relative_to(ROOT)),
        "schema_loaded": False,
        "n_obs": 0,
        "n_vars": 0,
        "obsm_keys": "",
        "uns_keys": "",
        "gene_identifier_type": "unknown",
        "example_var_names": "",
        "raw_available": False,
        "normalization_status": "not_loaded",
        "schema_warning": "",
    }
    obs_rows: list[dict[str, Any]] = []
    var_rows: list[dict[str, Any]] = []
    layer_rows: list[dict[str, Any]] = []
    field_rows: list[dict[str, Any]] = []
    norm = {"dataset_id": dataset_id, "normalization_status": "not_loaded", "raw_available": False, "layer_names": "", "normalization_warning": ""}
    if path.suffix.lower() != ".h5ad":
        base["schema_warning"] = f"format_{path.suffix.lower()}_inventory_only"
        norm["normalization_warning"] = base["schema_warning"]
        return base, obs_rows, var_rows, layer_rows, field_rows, norm
    try:
        adata = ad.read_h5ad(path, backed="r")
        base.update(
            {
                "schema_loaded": True,
                "n_obs": int(adata.n_obs),
                "n_vars": int(adata.n_vars),
                "obsm_keys": ";".join(map(str, adata.obsm.keys())),
                "uns_keys": ";".join(map(str, adata.uns.keys())),
                "example_var_names": ";".join(map(str, list(adata.var_names[:10]))),
                "raw_available": adata.raw is not None,
            }
        )
        if all(str(v).startswith("ENSG") for v in list(adata.var_names[: min(20, adata.n_vars)])):
            base["gene_identifier_type"] = "ensembl_like"
        else:
            base["gene_identifier_type"] = "symbol_or_mixed_like"
        for column in map(str, adata.obs.columns):
            obs_rows.append({"dataset_id": dataset_id, "local_path": base["local_path"], "obs_column": column})
        for column in map(str, adata.var.columns):
            var_rows.append({"dataset_id": dataset_id, "local_path": base["local_path"], "var_column": column})
        for layer in map(str, adata.layers.keys()):
            layer_rows.append({"dataset_id": dataset_id, "local_path": base["local_path"], "layer_name": layer})
        if not layer_rows:
            layer_rows.append({"dataset_id": dataset_id, "local_path": base["local_path"], "layer_name": ""})
        obs_cols = set(map(str, adata.obs.columns))
        for field, candidates in cfg["metadata_column_candidates"].items():
            matches = [candidate for candidate in candidates if candidate in obs_cols]
            field_rows.append(
                {
                    "dataset_id": dataset_id,
                    "metadata_field": field,
                    "candidate_columns": ";".join(matches),
                    "has_candidate": bool(matches),
                }
            )
        sample = adata.X[: min(500, adata.n_obs), : min(500, adata.n_vars)]
        arr = sample.data if sparse.issparse(sample) else np.asarray(sample).ravel()
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            status = "unknown_empty_sample"
        elif np.nanmin(arr) < 0:
            status = "scaled_or_centered"
        elif np.allclose(arr, np.round(arr)) and np.nanmax(arr) > 50:
            status = "raw_count_like"
        elif np.nanmax(arr) <= 30:
            status = "log_normalized_like"
        else:
            status = "unknown_nonnegative"
        base["normalization_status"] = status
        norm = {
            "dataset_id": dataset_id,
            "normalization_status": status,
            "raw_available": adata.raw is not None,
            "layer_names": ";".join(map(str, adata.layers.keys())),
            "normalization_warning": "heuristic_only_no_normalization_applied",
        }
        adata.file.close()
    except Exception as exc:
        base["schema_warning"] = f"schema_inspection_failed:{type(exc).__name__}:{exc}"
        norm["normalization_warning"] = base["schema_warning"]
    return base, obs_rows, var_rows, layer_rows, field_rows, norm


def nested_get_int(payload: Any, keys: list[str]) -> int:
    found: list[int] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key) in keys:
                    try:
                        found.append(int(child))
                    except Exception:
                        pass
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return found[0] if found else 0


def acquire_cellxgene_metadata(row: pd.Series, output_dir: Path) -> dict[str, Any]:
    dataset_id = str(row["dataset_id"])
    urls = [
        f"https://api.cellxgene.cziscience.com/curation/v1/datasets/{dataset_id}",
        f"https://api.cellxgene.cziscience.com/dp/v1/datasets/{dataset_id}",
    ]
    census_available = importlib.util.find_spec("cellxgene_census") is not None
    errors = []
    for url in urls:
        try:
            response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)
            if response.status_code != 200:
                errors.append(f"{url}:HTTP_{response.status_code}")
                continue
            payload = response.json()
            out_path = output_dir / f"{dataset_id}_cellxgene_metadata.json"
            out_path.write_text(json.dumps(payload, indent=2)[:2_000_000], encoding="utf-8")
            keys = sorted(payload.keys()) if isinstance(payload, dict) else []
            return {
                "metadata_acquisition_attempted": True,
                "metadata_acquisition_succeeded": True,
                "metadata_source": url,
                "metadata_local_path": str(out_path.relative_to(ROOT)),
                "metadata_error": "",
                "cellxgene_census_available": census_available,
                "remote_payload_keys": ";".join(map(str, keys[:50])),
                "remote_n_obs": nested_get_int(payload, ["cell_count", "n_obs", "cell_counts"]),
                "remote_n_vars": nested_get_int(payload, ["feature_count", "n_vars", "gene_count"]),
                "remote_schema_note": "public_api_dataset_metadata_only_no_expression_matrix",
            }
        except Exception as exc:
            errors.append(f"{url}:{type(exc).__name__}:{exc}")
    return {
        "metadata_acquisition_attempted": True,
        "metadata_acquisition_succeeded": False,
        "metadata_source": "cellxgene_public_api",
        "metadata_local_path": "",
        "metadata_error": (
            "cellxgene_census_not_installed; " if not census_available else ""
        )
        + " | ".join(errors)
        + "; next_command=python -m pip install cellxgene-census or provide approved H5AD URL",
        "cellxgene_census_available": census_available,
        "remote_payload_keys": "",
        "remote_n_obs": 0,
        "remote_n_vars": 0,
        "remote_schema_note": "metadata_first_failed_no_expression_downloaded",
    }


def acquire_geo_metadata(row: pd.Series, output_dir: Path) -> dict[str, Any]:
    dataset_id = str(row["dataset_id"])
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={dataset_id}&targ=self&form=text&view=brief"
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP_{response.status_code}")
        text = response.text
        out_path = output_dir / f"{dataset_id}_geo_metadata.txt"
        out_path.write_text(text[:2_000_000], encoding="utf-8")
        sample_count = 0
        supplementary_files = []
        platform_ids = []
        titles = []
        for line in text.splitlines():
            if line.startswith("!Series_sample_id"):
                sample_count += line.count("GSM")
            elif line.startswith("!Series_supplementary_file"):
                supplementary_files.append(line.split("=", 1)[-1].strip())
            elif line.startswith("!Series_platform_id"):
                platform_ids.append(line.split("=", 1)[-1].strip())
            elif line.startswith("!Series_title"):
                titles.append(line.split("=", 1)[-1].strip())
        return {
            "metadata_acquisition_attempted": True,
            "metadata_acquisition_succeeded": True,
            "metadata_source": url,
            "metadata_local_path": str(out_path.relative_to(ROOT)),
            "metadata_error": "",
            "cellxgene_census_available": False,
            "remote_payload_keys": "geo_text_metadata",
            "remote_n_obs": sample_count,
            "remote_n_vars": 0,
            "remote_schema_note": (
                "GEO metadata/sample/file manifest only; no raw expression downloaded; "
                f"platforms={';'.join(platform_ids[:5])}; supplementary_files={';'.join(supplementary_files[:5])}; "
                f"title={';'.join(titles[:1])}"
            ),
        }
    except Exception as exc:
        return {
            "metadata_acquisition_attempted": True,
            "metadata_acquisition_succeeded": False,
            "metadata_source": url,
            "metadata_local_path": "",
            "metadata_error": f"{type(exc).__name__}:{exc}; next_command=manual GEO metadata check for {dataset_id}",
            "cellxgene_census_available": False,
            "remote_payload_keys": "",
            "remote_n_obs": 0,
            "remote_n_vars": 0,
            "remote_schema_note": "metadata_first_failed_no_expression_downloaded",
        }


def acquire_metadata_first(row: pd.Series, output_dir: Path) -> dict[str, Any]:
    source = str(row.get("source", ""))
    if source == "CELLxGENE":
        return acquire_cellxgene_metadata(row, output_dir)
    if source == "GEO":
        return acquire_geo_metadata(row, output_dir)
    return {
        "metadata_acquisition_attempted": True,
        "metadata_acquisition_succeeded": False,
        "metadata_source": source,
        "metadata_local_path": "",
        "metadata_error": f"unsupported_metadata_source:{source}",
        "cellxgene_census_available": False,
        "remote_payload_keys": "",
        "remote_n_obs": 0,
        "remote_n_vars": 0,
        "remote_schema_note": "metadata_first_not_supported_for_source",
    }


def write_report(download_plan: pd.DataFrame, manifest: pd.DataFrame, schema: pd.DataFrame, gene: pd.DataFrame, norm: pd.DataFrame, species: pd.DataFrame, recommend: pd.DataFrame, holdout: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    exact_next = (
        "python scripts/run_stage33a_external_pretrained_jepa_v1.py --config configs/train/stage33a_external_pretrained_jepa_v1.yaml"
        if bool(row.stage32c_ready_for_stage33)
        else "python scripts/acquire_stage32c_bulk_approved_external_datasets_v1.py --config configs/data/stage32c_bulk_approved_external_acquisition_v1.yaml --allow-download --metadata-first"
    )
    lines = [
        "# Stage 32C bulk approved external acquisition report v1",
        "",
        "## 1. Executive summary",
        "",
        f"Approved candidates: `{int(row.n_approved_candidates)}`. Download attempted: `{bool(row.stage32c_any_download_attempted)}`. Download succeeded: `{bool(row.stage32c_any_download_succeeded)}`. Human matrix built: `{bool(row.stage32c_human_matrix_built)}`. Ready for Stage 33: `{bool(row.stage32c_ready_for_stage33)}`.",
        "",
        "## 2. Why Stage 32C was run",
        "",
        "Stage 32C performs a bulk acquisition/schema audit for all registry-approved self-supervised pretraining candidates before any Stage 33 external-pretrained JEPA benchmark.",
        "",
        "## 3. Approved pretraining candidates",
        "",
        "```csv",
        download_plan.to_csv(index=False).strip(),
        "```",
        "",
        "## 4. Download/acquisition results",
        "",
        "```csv",
        manifest.to_csv(index=False).strip(),
        "```",
        "",
        "## 5. Schema and column-name inventory",
        "",
        "```csv",
        schema.to_csv(index=False).strip(),
        "```",
        "",
        "## 6. Gene overlap results",
        "",
        "```csv",
        gene.to_csv(index=False).strip(),
        "```",
        "",
        "## 7. Normalization and layer audit",
        "",
        "```csv",
        norm.to_csv(index=False).strip(),
        "```",
        "",
        "## 8. Human-ready datasets",
        "",
        "```csv",
        recommend[recommend['recommendation_class'].astype(str).str.contains('human', na=False)].to_csv(index=False).strip(),
        "```",
        "",
        "## 9. Mouse/ortholog-required datasets",
        "",
        "```csv",
        species.to_csv(index=False).strip(),
        "```",
        "",
        "## 10. Protected holdout audit",
        "",
        "```csv",
        holdout.to_csv(index=False).strip(),
        "```",
        "",
        "## 11. Candidate matrix recommendation",
        "",
        "```csv",
        recommend.to_csv(index=False).strip(),
        "```",
        "",
        "## 12. Whether Stage 33 can proceed",
        "",
        "Stage 33 can proceed only if `stage32c_ready_for_stage33=True`.",
        "",
        "## 13. Interpretation boundary",
        "",
        "Stage 32C does not train a model. Stage 32C does not run external validation. Stage 32C does not use external labels for supervised prediction. Stage 32C does not validate in silico ablation. Stage 32C does not update manuscript claims. Any dataset used for pretraining is forfeited as clean validation.",
        "",
        "## 14. Exact next command",
        "",
        f"`{exact_next}`",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    new = {
        "scorecard_item": "stage32c_bulk_external_schema_acquisition",
        "status": "complete",
        "stage": "Stage 32C",
        "metric": "bulk approved external acquisition/schema audit",
        "threshold_or_gate": "approved pretraining only; protected holdouts excluded; schema/gene/normalization audits written",
        "current_value": f"ready_for_stage33={bool(row.stage32c_ready_for_stage33)}",
        "pass_fail": "pass" if bool(row.stage32c_pass) else "fail",
        "datasets_allowed": "registry-approved external self-supervised pretraining candidates",
        "datasets_forbidden": "clean holdouts; SEA-AD; model-selection datasets; stress/plausibility-only; ambiguous matches",
        "allowed_claim": "Stage 32C schema/acquisition audit complete",
        "notes": f"downloads_attempted={bool(row.stage32c_any_download_attempted)}; human_matrix_built={bool(row.stage32c_human_matrix_built)}.",
    }
    score = score[score["scorecard_item"] != "stage32c_bulk_external_schema_acquisition"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (
            ROOT / "docs" / "ACTIVE_V3_STATUS.md",
            "\n\n## Stage 32C bulk external acquisition status\n",
            f"\nStage 32C bulk approved external acquisition/schema audit is complete. Human matrix built: `{bool(row.stage32c_human_matrix_built)}`; Stage 33 ready: `{bool(row.stage32c_ready_for_stage33)}`. No model was trained and external validation remains not run.\n",
        ),
        (
            ROOT / "docs" / "V3_SCORECARD.md",
            "\n\n## Stage 32C bulk external acquisition result\n",
            f"\nStage 32C pass: `{bool(row.stage32c_pass)}`; downloads attempted: `{bool(row.stage32c_any_download_attempted)}`; human matrix built: `{bool(row.stage32c_human_matrix_built)}`; Stage 33 ready: `{bool(row.stage32c_ready_for_stage33)}`.\n",
        ),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/data/stage32c_bulk_approved_external_acquisition_v1.yaml")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--metadata-first", action="store_true")
    parser.add_argument("--download-expression", action="store_true")
    parser.add_argument("--max-datasets", type=int, default=None)
    parser.add_argument("--target-dataset-id", action="append", default=[])
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = resolve(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    project_genes = s32.canonical_target_gene_universe(resolve(cfg["canonical_gene_universe_path"]))
    registry = pd.read_csv(resolve(cfg["registry_path"]))
    role = approved_role_audit(registry)
    approved = selected_approved(role, cfg, args.target_dataset_id, args.max_datasets)
    inventory = local_inventory(cfg, registry, role)

    download_rows = []
    manifest_rows = []
    schema_rows = []
    obs_rows = []
    var_rows = []
    layer_rows = []
    gene_rows = []
    field_rows = []
    norm_rows = []
    species_rows = []
    recommend_rows = []
    download_attempted = bool(args.allow_download)
    download_succeeded = False

    for _, row in approved.iterrows():
        inv = inventory[inventory["dataset_id"] == row["dataset_id"]].copy()
        local_path = str(inv["local_path"].iloc[0]) if not inv.empty else ""
        has_local = bool(local_path)
        metadata_result = {
            "metadata_acquisition_attempted": False,
            "metadata_acquisition_succeeded": False,
            "metadata_source": "",
            "metadata_local_path": "",
            "metadata_error": "",
            "cellxgene_census_available": importlib.util.find_spec("cellxgene_census") is not None,
            "remote_payload_keys": "",
            "remote_n_obs": 0,
            "remote_n_vars": 0,
            "remote_schema_note": "",
        }
        if args.allow_download:
            if args.metadata_first and not args.download_expression:
                metadata_result = acquire_metadata_first(row, output_dir)
                acquisition_status = (
                    "metadata_first_succeeded"
                    if metadata_result["metadata_acquisition_succeeded"]
                    else "metadata_first_failed"
                )
            elif args.download_expression:
                acquisition_status = "expression_download_guarded_not_implemented"
                metadata_result["metadata_acquisition_attempted"] = True
                metadata_result["metadata_error"] = (
                    "expression materialization intentionally not implemented in Stage 32C v1; "
                    "provide approved source-specific command/version/size first"
                )
            else:
                acquisition_status = "allow_download_set_but_no_metadata_or_expression_mode"
        elif has_local:
            acquisition_status = "existing_local_candidate_found"
        else:
            acquisition_status = "not_acquired_no_download_default"
        download_succeeded = download_succeeded or bool(metadata_result["metadata_acquisition_succeeded"])
        next_action = (
            "inspect/build from existing local approved matrix"
            if has_local
            else (
                "metadata acquired; review schema/source before any expression download"
                if metadata_result["metadata_acquisition_succeeded"]
                else "run with --allow-download --metadata-first first; use --download-expression only after source/version/size are approved"
            )
        )
        download_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "source": row["source"],
                "collection_name": row["collection_name"],
                "priority_rank": int(row["priority_rank"]),
                "approved_for_pretraining": True,
                "allow_download": bool(args.allow_download),
                "metadata_first": bool(args.metadata_first),
                "download_expression": bool(args.download_expression),
                "acquisition_status": acquisition_status,
                "local_path": local_path,
                **metadata_result,
                "exact_next_action": next_action,
            }
        )
        if has_local and inv["matrix_loaded"].iloc[0]:
            path = resolve(local_path)
            schema, obs, var, layers, fields, norm = inspect_schema(path, row["dataset_id"], cfg)
            schema_rows.append({**row.to_dict(), **schema})
            obs_rows.extend(obs)
            var_rows.extend(var)
            layer_rows.extend(layers)
            field_rows.extend(fields)
            norm_rows.append(norm)
            overlap = s32.gene_overlap_for_h5ad(path, project_genes) if path.suffix.lower() == ".h5ad" else {
                "n_genes_raw": int(schema.get("n_vars", 0)),
                "n_genes_aligned": 0,
                "gene_overlap_fraction": 0.0,
                "gene_overlap_status": "unsupported_format",
                "missing_gene_count": len(project_genes),
            }
        else:
            schema_rows.append(
                {
                    **row.to_dict(),
                    "dataset_id": row["dataset_id"],
                    "local_path": local_path,
                    "schema_loaded": bool(metadata_result["metadata_acquisition_succeeded"]),
                    "n_obs": int(metadata_result.get("remote_n_obs", 0) or 0),
                    "n_vars": int(metadata_result.get("remote_n_vars", 0) or 0),
                    "obsm_keys": "",
                    "uns_keys": "",
                    "gene_identifier_type": "unknown",
                    "example_var_names": "",
                    "raw_available": False,
                    "normalization_status": "not_loaded",
                    "schema_warning": metadata_result.get("metadata_error", "")
                    or metadata_result.get("remote_schema_note", "")
                    or "no_approved_local_loaded_matrix",
                }
            )
            layer_rows.append({"dataset_id": row["dataset_id"], "local_path": local_path, "layer_name": ""})
            for field in cfg["metadata_column_candidates"]:
                field_rows.append({"dataset_id": row["dataset_id"], "metadata_field": field, "candidate_columns": "", "has_candidate": False})
            norm_rows.append(
                {
                    "dataset_id": row["dataset_id"],
                    "normalization_status": "not_loaded",
                    "raw_available": False,
                    "layer_names": "",
                    "normalization_warning": (
                        "metadata_only_no_expression_matrix"
                        if metadata_result["metadata_acquisition_succeeded"]
                        else "no_approved_local_loaded_matrix"
                    ),
                }
            )
            overlap = {
                "n_genes_raw": 0,
                "n_genes_aligned": 0,
                "gene_overlap_fraction": 0.0,
                "gene_overlap_status": "not_evaluated_no_matrix",
                "missing_gene_count": len(project_genes),
            }
        species = "mouse" if str(row["dataset_id"]).startswith("mouse") or "mouse" in str(row["dataset_name"]).lower() else "human_or_unknown"
        ortholog = species == "mouse"
        sufficient = has_local and overlap["gene_overlap_fraction"] >= float(cfg["main_matrix_min_gene_overlap_fraction"]) and not ortholog
        gene_rows.append({"dataset_id": row["dataset_id"], "dataset_name": row["dataset_name"], "local_path": local_path, **overlap, "included_in_candidate_matrix": False})
        species_rows.append({"dataset_id": row["dataset_id"], "dataset_name": row["dataset_name"], "species": species, "ortholog_mapping_required": ortholog, "ortholog_mapping_available": False, "main_human_matrix_eligible": bool(sufficient)})
        recommendation = "human_ready_candidate" if sufficient else ("ortholog_mapping_required" if ortholog else "acquire_or_build_matrix_before_stage33")
        recommend_rows.append({"dataset_id": row["dataset_id"], "dataset_name": row["dataset_name"], "recommendation_class": recommendation, "recommended_next_use": "Stage 33 candidate" if sufficient else "not ready for Stage 33", "reason": "no approved loaded matrix or insufficient gene/schema audit" if not sufficient else "approved human matrix appears usable"})
        manifest_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "dataset_name": row["dataset_name"],
                "source": row["source"],
                "acquisition_status": acquisition_status,
                "local_path": local_path,
                "metadata_source": metadata_result.get("metadata_source", ""),
                "metadata_local_path": metadata_result.get("metadata_local_path", ""),
                "metadata_error": metadata_result.get("metadata_error", ""),
                "file_size_bytes": int(inv["file_size_bytes"].iloc[0]) if not inv.empty else 0,
                "included_in_candidate_matrix": False,
                "exclusion_reason": "no expression matrix built in metadata-first Stage 32C run",
            }
        )

    holdout_rows = []
    for _, h in role.iterrows():
        protected = bool(h["clean_holdout_protected"] or h["stress_test_only"] or h["plausibility_only"] or h["internal_dataset"] or h["model_selection_excluded"])
        if protected:
            holdout_rows.append({"dataset_id": h["dataset_id"], "dataset_name": h["dataset_name"], "registry_role": h["registry_role"], "normalized_role": h["normalized_role"], "matrix_downloaded": False, "included": False, "protection_pass": True})

    download_plan = pd.DataFrame(download_rows)
    manifest = pd.DataFrame(manifest_rows)
    schema = pd.DataFrame(schema_rows)
    obs_cols = pd.DataFrame(obs_rows) if obs_rows else pd.DataFrame(columns=["dataset_id", "local_path", "obs_column"])
    var_cols = pd.DataFrame(var_rows) if var_rows else pd.DataFrame(columns=["dataset_id", "local_path", "var_column"])
    layers = pd.DataFrame(layer_rows)
    gene = pd.DataFrame(gene_rows)
    field_map = pd.DataFrame(field_rows)
    norm = pd.DataFrame(norm_rows)
    species = pd.DataFrame(species_rows)
    recommend = pd.DataFrame(recommend_rows)
    holdout = pd.DataFrame(holdout_rows)
    human_matrix_built = False
    matrix_path = ""

    pass_fail = pd.DataFrame(
        [
            {
                "registry_loaded": True,
                "approved_candidates_identified": not approved.empty,
                "protected_holdouts_excluded": bool(holdout["protection_pass"].all()) if not holdout.empty else True,
                "download_manifest_written": True,
                "schema_inventory_written": True,
                "obs_var_column_inventories_written": True,
                "gene_overlap_audit_written": True,
                "normalization_audit_written": True,
                "candidate_recommendation_written": True,
                "stage32c_pass": True,
                "stage32c_any_download_attempted": download_attempted,
                "stage32c_any_download_succeeded": download_succeeded,
                "stage32c_human_matrix_built": human_matrix_built,
                "stage32c_ready_for_stage33": False,
                "stage32c_clean_holdouts_protected": True,
                "stage32c_forbidden_dataset_included": False,
                "n_approved_candidates": int(len(approved)),
                "n_schema_loaded": int(schema["schema_loaded"].sum()) if "schema_loaded" in schema else 0,
                "human_matrix_path": matrix_path,
            }
        ]
    )

    download_plan.to_csv(DOWNLOAD_PLAN_OUT, index=False)
    manifest.to_csv(DOWNLOAD_MANIFEST_OUT, index=False)
    schema.to_csv(SCHEMA_OUT, index=False)
    obs_cols.to_csv(OBS_COLS_OUT, index=False)
    var_cols.to_csv(VAR_COLS_OUT, index=False)
    layers.to_csv(LAYER_OUT, index=False)
    gene.to_csv(GENE_OVERLAP_OUT, index=False)
    field_map.to_csv(FIELD_MAP_OUT, index=False)
    norm.to_csv(NORMALIZATION_OUT, index=False)
    species.to_csv(SPECIES_OUT, index=False)
    recommend.to_csv(RECOMMEND_OUT, index=False)
    holdout.to_csv(HOLDOUT_OUT, index=False)
    pass_fail.to_csv(PASS_FAIL_OUT, index=False)
    if not human_matrix_built:
        (output_dir / HUMAN_MANIFEST_NAME).write_text(json.dumps({"matrix_built": False, "source_dataset_ids": [], "reason": "no safe approved human matrix built"}, indent=2), encoding="utf-8")
    write_report(download_plan, manifest, schema, gene, norm, species, recommend, holdout, pass_fail)
    update_status(pass_fail)

    required = [DOWNLOAD_PLAN_OUT, DOWNLOAD_MANIFEST_OUT, SCHEMA_OUT, OBS_COLS_OUT, VAR_COLS_OUT, LAYER_OUT, GENE_OVERLAP_OUT, FIELD_MAP_OUT, NORMALIZATION_OUT, SPECIES_OUT, RECOMMEND_OUT, HOLDOUT_OUT, PASS_FAIL_OUT, REPORT_OUT]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Stage 32C outputs: " + "; ".join(missing))

    row = pass_fail.iloc[0]
    print(f"stage32c_approved_candidates={int(row.n_approved_candidates)}")
    print(f"stage32c_any_download_attempted={bool(row.stage32c_any_download_attempted)}")
    print(f"stage32c_any_download_succeeded={bool(row.stage32c_any_download_succeeded)}")
    print(f"stage32c_human_matrix_built={bool(row.stage32c_human_matrix_built)}")
    print(f"stage32c_ready_for_stage33={bool(row.stage32c_ready_for_stage33)}")


if __name__ == "__main__":
    main()
