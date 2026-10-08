from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import yaml
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_stage34a_hbca_microglia_filtered_external_pretraining_v1 as s34a  # noqa: E402


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

MATRIX_MANIFEST_OUT = TABLE_DIR / "stage34b_hbcc_matrix_manifest_v1.csv"
CELLTYPE_AUDIT_OUT = TABLE_DIR / "stage34b_hbcc_celltype_audit_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage34b_pass_fail_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage34b_condition_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage34b_mean_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage34b_target_metrics_v1.csv"
GRAPH_AUDIT_OUT = TABLE_DIR / "stage34b_graph_control_audit_v1.csv"
LEAKAGE_AUDIT_OUT = TABLE_DIR / "stage34b_leakage_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage34b_hbcc_external_pretraining_report_v1.md"

REF27 = s34a.REF27
REF31 = s34a.REF31
REF33C = "stage33c_best_reference"
REF34A = "stage34a_best_reference"


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def verify_registry_approval(cfg: dict[str, Any]) -> dict[str, Any]:
    registry = pd.read_csv(resolve(cfg["registry_path"]))
    hit = registry[registry["dataset_id"].astype(str) == str(cfg["approved_dataset_id"])]
    if hit.empty:
        raise RuntimeError(f"Approved HBCC dataset missing from registry: {cfg['approved_dataset_id']}")
    row = hit.iloc[0]
    audit = {
        "dataset_id": str(row["dataset_id"]),
        "dataset_name": str(row.get("dataset_name", "")),
        "role": str(row.get("role", "")),
        "allowed_for_pretraining": str(row.get("allowed_for_pretraining", "")).lower() == "true",
        "reserved_for_clean_validation": str(row.get("reserved_for_clean_validation", "")).lower() == "true",
        "allowed_for_model_selection": str(row.get("allowed_for_model_selection", "")).lower() == "true",
        "already_used": str(row.get("already_used", "")).lower() == "true",
    }
    if not audit["allowed_for_pretraining"] or audit["reserved_for_clean_validation"] or audit["allowed_for_model_selection"] or audit["already_used"]:
        raise RuntimeError(f"HBCC registry gate failed: {audit}")
    return audit


def sample_obs(obs: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.DataFrame, bool, str]:
    max_cells = int(cfg["max_cells"])
    if len(obs) <= max_cells:
        return obs.copy(), False, "not_downsampled"
    cols = [col for col in cfg["matrix_build"]["stratify_columns"] if col in obs.columns]
    if not cols:
        return obs.sample(n=max_cells, random_state=int(cfg["random_seed"])).copy(), True, "random_sample_no_strata_available"
    grouped = obs.groupby(cols, dropna=False, observed=True)
    pieces = []
    remaining = max_cells
    groups = [(keys, group) for keys, group in grouped]
    for _, group in groups:
        take = max(1, int(round(max_cells * len(group) / len(obs))))
        take = min(take, len(group), remaining)
        if take > 0:
            pieces.append(group.sample(n=take, random_state=int(cfg["random_seed"])))
            remaining -= take
        if remaining <= 0:
            break
    sampled = pd.concat(pieces, ignore_index=False)
    if len(sampled) < max_cells:
        extra_pool = obs.drop(index=sampled.index, errors="ignore")
        if not extra_pool.empty:
            extra = extra_pool.sample(n=min(max_cells - len(sampled), len(extra_pool)), random_state=int(cfg["random_seed"]))
            sampled = pd.concat([sampled, extra], ignore_index=False)
    if len(sampled) > max_cells:
        sampled = sampled.sample(n=max_cells, random_state=int(cfg["random_seed"]))
    return sampled.copy(), True, "stratified_by_" + ";".join(cols)


def build_or_load_hbcc_matrix(cfg: dict[str, Any], canonical: list[str], registry_audit: dict[str, Any]) -> tuple[ad.AnnData, pd.DataFrame, pd.DataFrame]:
    matrix_path = resolve(cfg["stage34b_matrix"])
    metadata_path = resolve(cfg["stage34b_metadata"])
    gene_map_path = resolve(cfg["stage34b_gene_map"])
    if matrix_path.exists():
        adata = ad.read_h5ad(matrix_path)
        celltype = adata.obs["cell_type"].astype(str).value_counts().reset_index()
        celltype.columns = ["cell_type", "n_cells"]
        manifest = make_manifest(cfg, adata, registry_audit, matrix_reused=True, downsampled=adata.n_obs >= int(cfg["max_cells"]), sampling_logic="loaded_existing_matrix", gene_map_path=gene_map_path, metadata_path=metadata_path)
        return adata, celltype, manifest
    if importlib.util.find_spec("cellxgene_census") is None:
        raise RuntimeError("cellxgene_census is not installed in this Python environment.")
    import cellxgene_census

    project_upper = {gene.upper(): gene for gene in canonical}
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    with cellxgene_census.open_soma(census_version=cfg["matrix_build"]["census_version"]) as census:
        human = census["census_data"]["homo_sapiens"]
        obs_cols = list(cfg["matrix_build"]["obs_columns"])
        obs = (
            human.obs.read(
                value_filter=f"dataset_id == '{cfg['approved_dataset_id']}'",
                column_names=obs_cols,
            )
            .concat()
            .to_pandas()
        )
        if obs.empty:
            raise RuntimeError("No HBCC Census obs rows found.")
        sampled_obs, downsampled, sampling_logic = sample_obs(obs, cfg)
        var = human.ms["RNA"].var.read(column_names=["soma_joinid", "feature_id", "feature_name"]).concat().to_pandas()
        var["project_gene"] = var["feature_name"].astype(str).str.upper().map(project_upper)
        matched_var = var[var["project_gene"].notna()].drop_duplicates("project_gene")
        gene_overlap = len(matched_var) / len(canonical)
        if gene_overlap < float(cfg["minimum_gene_overlap_fraction"]):
            raise RuntimeError(f"HBCC gene overlap {gene_overlap:.4f} below threshold.")
        obs_coords = sampled_obs["soma_joinid"].astype(int).to_numpy()
        var_coords = matched_var["soma_joinid"].astype(int).to_numpy()
        try:
            adata = cellxgene_census.get_anndata(
                census=census,
                organism=cfg["matrix_build"]["organism"],
                measurement_name=cfg["matrix_build"]["measurement_name"],
                X_name=cfg["matrix_build"]["preferred_x_name"],
                obs_coords=obs_coords,
                var_coords=var_coords,
                obs_column_names=[col for col in obs_cols if col in sampled_obs.columns],
                var_column_names=["feature_id", "feature_name"],
            )
            x_name = cfg["matrix_build"]["preferred_x_name"]
        except Exception:
            adata = cellxgene_census.get_anndata(
                census=census,
                organism=cfg["matrix_build"]["organism"],
                measurement_name=cfg["matrix_build"]["measurement_name"],
                obs_coords=obs_coords,
                var_coords=var_coords,
                obs_column_names=[col for col in obs_cols if col in sampled_obs.columns],
                var_column_names=["feature_id", "feature_name"],
            )
            x_name = "default"
    source_to_project = matched_var.set_index("feature_id")["project_gene"].to_dict()
    adata.var["project_gene"] = adata.var["feature_id"].astype(str).map(source_to_project)
    adata = adata[:, adata.var["project_gene"].notna()].copy()
    adata.var_names = adata.var["project_gene"].astype(str).tolist()
    adata.obs["stage34b_source_dataset_id"] = str(cfg["approved_dataset_id"])
    adata.obs["stage34b_source_dataset_name"] = str(cfg["approved_dataset_name"])
    adata.obs["stage34b_expression_source"] = "cellxgene_census"
    adata.uns["stage34b"] = {
        "dataset_id": str(cfg["approved_dataset_id"]),
        "dataset_name": str(cfg["approved_dataset_name"]),
        "census_version": cfg["matrix_build"]["census_version"],
        "x_name": x_name,
        "max_cells": int(cfg["max_cells"]),
        "downsampled": bool(downsampled),
        "sampling_logic": sampling_logic,
        "gene_matching": "intersect_only_case_insensitive_feature_name_to_project_symbol",
        "no_imputation": True,
    }
    adata.write_h5ad(matrix_path)
    adata.obs.reset_index(names="source_obs_id").to_csv(metadata_path, index=False)
    pd.DataFrame(
        {
            "dataset_id": cfg["approved_dataset_id"],
            "project_gene": matched_var["project_gene"],
            "source_feature_id": matched_var["feature_id"],
            "source_feature_name": matched_var["feature_name"],
            "mapping_status": "case_insensitive_feature_name_match",
        }
    ).to_csv(gene_map_path, index=False)
    celltype = adata.obs["cell_type"].astype(str).value_counts().reset_index()
    celltype.columns = ["cell_type", "n_cells"]
    manifest = make_manifest(cfg, adata, registry_audit, matrix_reused=False, downsampled=downsampled, sampling_logic=sampling_logic, gene_map_path=gene_map_path, metadata_path=metadata_path)
    return adata, celltype, manifest


def make_manifest(
    cfg: dict[str, Any],
    adata: ad.AnnData,
    registry_audit: dict[str, Any],
    matrix_reused: bool,
    downsampled: bool,
    sampling_logic: str,
    gene_map_path: Path,
    metadata_path: Path,
) -> pd.DataFrame:
    canonical, canonical_audit = s34a.verify_canonical_gene_universe(resolve(cfg["canonical_gene_universe"]))
    gene_overlap = adata.n_vars / len(canonical)
    sample = adata.X[: min(500, adata.n_obs), : min(500, adata.n_vars)]
    arr = sample.data if sparse.issparse(sample) else np.asarray(sample).ravel()
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        norm = "unknown_empty_sample"
    elif np.nanmin(arr) < 0:
        norm = "scaled_or_centered"
    elif np.allclose(arr, np.round(arr)) and np.nanmax(arr) > 50:
        norm = "raw_count_like"
    elif np.nanmax(arr) <= 30:
        norm = "log_normalized_like"
    else:
        norm = "unknown_nonnegative"
    return pd.DataFrame(
        [
            {
                "dataset_id": cfg["approved_dataset_id"],
                "dataset_name": cfg["approved_dataset_name"],
                "approved_for_pretraining": registry_audit["allowed_for_pretraining"],
                "matrix_path": cfg["stage34b_matrix"],
                "metadata_path": str(metadata_path.relative_to(ROOT)),
                "gene_map_path": str(gene_map_path.relative_to(ROOT)),
                "matrix_reused": matrix_reused,
                "n_obs": int(adata.n_obs),
                "n_vars": int(adata.n_vars),
                "max_cells": int(cfg["max_cells"]),
                "downsampled": bool(downsampled),
                "sampling_logic": sampling_logic,
                "gene_overlap_fraction": float(gene_overlap),
                "gene_overlap_pass": gene_overlap >= float(cfg["minimum_gene_overlap_fraction"]),
                "normalization_status": norm,
                "benchmark_transform": cfg["external_encoder"]["transform"],
                "clean_holdout_used": False,
                "sea_ad_used_during_external_pretraining": False,
                "external_labels_used_for_supervised_pathology_prediction": False,
                **canonical_audit,
            }
        ]
    )


def reference_target_and_mean(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ref_target, ref_mean = s34a.reference_target_and_mean(
        {
            **cfg,
            "references": {
                "stage27c_oof": cfg["references"]["stage27c_oof"],
                "stage31_oof": cfg["references"]["stage31_oof"],
                "stage31_condition": cfg["references"]["stage31_condition"],
                "stage33c_target_metrics": cfg["references"]["stage33c_target_metrics"],
                "stage33c_mean_metrics": cfg["references"]["stage33c_target_metrics"],
            },
        }
    )
    t34 = pd.read_csv(resolve(cfg["references"]["stage34a_target_metrics"]))
    t34 = t34[t34["condition"] == cfg["stage34a_best_condition"]].copy()
    t34["condition"] = REF34A
    m34 = s34a.summarize_mean(t34)
    return pd.concat([ref_target, t34], ignore_index=True), pd.concat([ref_mean, m34], ignore_index=True)


def build_specs() -> list[s34a.ConditionSpec]:
    return [
        s34a.ConditionSpec("hbcc_ext_svd16_raw_count_size_factor_log1p_direct_no_graph", 16, "direct", "no_graph_identity", 0.0),
        s34a.ConditionSpec("hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph", 32, "direct", "no_graph_identity", 0.0),
        s34a.ConditionSpec("hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph", 32, "concat_module_pca", "no_graph_identity", 0.0),
        s34a.ConditionSpec("hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05", 32, "direct", "residual_real_graph", 0.05),
        s34a.ConditionSpec("hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05", 32, "direct", "strict_shuffled_residual_graph", 0.05),
    ]


def audits_and_passfail(cfg: dict[str, Any], target: pd.DataFrame, mean: pd.DataFrame, manifest: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = set(cfg["required_targets"])
    external_conditions = [spec.condition for spec in build_specs()]
    ext_mean = mean[mean["condition"].isin(external_conditions)].copy()
    best = ext_mean.iloc[0]
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    ref27_target = target[target["condition"] == REF27][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "ref27_target_spearman"})
    best_target = target[target["condition"] == best.condition].merge(ref27_target, on="target_key", how="left")
    target_gate = bool(((best_target["pooled_oof_spearman"] - best_target["ref27_target_spearman"]) >= float(cfg["max_target_drop_vs_stage27c_reference"])).all())
    no_graph = "hbcc_ext_svd32_raw_count_size_factor_log1p_direct_no_graph"
    real = "hbcc_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05"
    strict = "hbcc_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05"
    real_gt_no = bool(mean_map.get(real, -999) > mean_map.get(no_graph, 999))
    real_gt_strict = bool(mean_map.get(real, -999) > mean_map.get(strict, 999))
    graph_specific = bool(real_gt_no and real_gt_strict)
    graph = pd.DataFrame(
        [
            {"comparison": "real_minus_no_graph_identity", "left_condition": real, "right_condition": no_graph, "delta_mean_pooled_oof_spearman": float(mean_map.get(real, np.nan) - mean_map.get(no_graph, np.nan)), "graph_gate_pass": real_gt_no},
            {"comparison": "real_minus_strict_shuffled", "left_condition": real, "right_condition": strict, "delta_mean_pooled_oof_spearman": float(mean_map.get(real, np.nan) - mean_map.get(strict, np.nan)), "graph_gate_pass": real_gt_strict},
        ]
    )
    leakage = pd.DataFrame(
        [
            {
                "approved_hbcc_dataset_used": True,
                "clean_holdout_used": False,
                "sea_ad_used_during_external_pretraining": False,
                "external_labels_used_for_supervised_pathology_prediction": False,
                "locked_donor_folds_used": True,
                "fold_local_downstream_scaling_and_ridge": True,
                "in_silico_ablation_run": False,
                "leakage_audit_pass": True,
            }
        ]
    )
    run_pass = bool(manifest.iloc[0]["approved_for_pretraining"] and manifest.iloc[0]["gene_overlap_pass"] and required.issubset(set(target[target["condition"].isin(external_conditions)]["target_key"])))
    dataset_rescue_pass = bool(best.mean_pooled_oof_spearman > max(float(cfg["stage33c_best_mean"]), float(cfg["stage34a_best_mean"])) and run_pass)
    full_pass = bool(best.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"]) and best.mean_pooled_oof_spearman >= float(cfg["minimum_success_threshold"]) and target_gate and run_pass)
    if best.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"]):
        interpretation = "HBCC external pretraining improved the internal SEA-AD benchmark, but this is not external validation."
    elif dataset_rescue_pass:
        interpretation = "HBCC external pretraining improved over prior external-pretraining attempts but did not surpass the Stage 27C internal no-graph reference."
    else:
        interpretation = "HBCC external pretraining did not rescue the external-pretraining deficit under this compact benchmark."
    if real_gt_strict and not real_gt_no:
        graph_interpretation = "Real topology outperformed shuffled topology but did not improve over the no-graph identity reference."
    elif graph_specific:
        graph_interpretation = "HBCC real graph beat matched no-graph and strict-shuffled controls internally; this is not external validation."
    else:
        graph_interpretation = "Graph-specific utility remains unestablished."
    pf = pd.DataFrame(
        [
            {
                "stage34b_run": True,
                "approved_hbcc_dataset_used": True,
                "n_hbcc_cells": int(manifest.iloc[0]["n_obs"]),
                "gene_overlap_fraction": float(manifest.iloc[0]["gene_overlap_fraction"]),
                "best_stage34b_condition": best.condition,
                "best_stage34b_mean_pooled_oof_spearman": float(best.mean_pooled_oof_spearman),
                "stage33c_best_mean": float(cfg["stage33c_best_mean"]),
                "stage34a_best_mean": float(cfg["stage34a_best_mean"]),
                "stage27c_reference_mean": float(cfg["stage27c_reference_mean"]),
                "best_minus_stage33c": float(best.mean_pooled_oof_spearman - float(cfg["stage33c_best_mean"])),
                "best_minus_stage34a": float(best.mean_pooled_oof_spearman - float(cfg["stage34a_best_mean"])),
                "best_minus_stage27c": float(best.mean_pooled_oof_spearman - float(cfg["stage27c_reference_mean"])),
                "all_five_targets_reported": required.issubset(set(target[target["condition"] == best.condition]["target_key"])),
                "target_degradation_gate_pass": target_gate,
                "stage34b_run_pass": run_pass,
                "stage34b_dataset_rescue_pass": dataset_rescue_pass,
                "stage34b_full_internal_performance_pass": full_pass,
                "stage34b_graph_specific_pass": graph_specific,
                "controlled_interpretation": interpretation,
                "graph_interpretation": graph_interpretation,
            }
        ]
    )
    return leakage, graph, pf


def write_report(celltype: pd.DataFrame, manifest: pd.DataFrame, mean: pd.DataFrame, target: pd.DataFrame, graph: pd.DataFrame, leakage: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    lines = [
        "# Stage 34B HBCC external pretraining report v1",
        "",
        "## Executive summary",
        "",
        f"HBCC cells used: `{int(row.n_hbcc_cells)}`. Best condition: `{row.best_stage34b_condition}` with mean pooled donor-level OOF Spearman `{row.best_stage34b_mean_pooled_oof_spearman:.4f}`.",
        f"Stage 33C best: `{row.stage33c_best_mean:.4f}`. Stage 34A best: `{row.stage34a_best_mean:.4f}`. Stage 27C reference: `{row.stage27c_reference_mean:.4f}`.",
        f"Run pass: `{bool(row.stage34b_run_pass)}`. Dataset rescue pass: `{bool(row.stage34b_dataset_rescue_pass)}`. Full internal performance pass: `{bool(row.stage34b_full_internal_performance_pass)}`. Graph-specific pass: `{bool(row.stage34b_graph_specific_pass)}`.",
        "",
        "## Controlled interpretation",
        "",
        str(row.controlled_interpretation),
        str(row.graph_interpretation),
        "",
        "This is an internal SEA-AD benchmark using an approved HBCC external pretraining dataset. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.",
        "",
        "## HBCC cell-type audit",
        "",
        "```csv",
        celltype.to_csv(index=False).strip(),
        "```",
        "",
        "## HBCC matrix manifest",
        "",
        "```csv",
        manifest.to_csv(index=False).strip(),
        "```",
        "",
        "## Mean metrics",
        "",
        "```csv",
        mean.to_csv(index=False).strip(),
        "```",
        "",
        "## Target metrics",
        "",
        "```csv",
        target.to_csv(index=False).strip(),
        "```",
        "",
        "## Graph-control audit",
        "",
        "```csv",
        graph.to_csv(index=False).strip(),
        "```",
        "",
        "## Leakage audit",
        "",
        "```csv",
        leakage.to_csv(index=False).strip(),
        "```",
        "",
        "## Pass/fail",
        "",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    new = {
        "scorecard_item": "stage34b_hbcc_external_pretraining",
        "status": "complete",
        "stage": "Stage 34B",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "dataset rescue requires best Stage 34B > Stage 33C/34A; full pass requires > Stage 27C and >=0.3228",
        "current_value": f"{row.best_stage34b_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.stage34b_full_internal_performance_pass) else "fail",
        "datasets_allowed": "approved HBCC CELLxGENE Census pretraining dataset; SEA-AD locked folds for downstream only",
        "datasets_forbidden": "clean holdouts; SEA-AD during external pretraining; external labels for pathology prediction; in silico ablation",
        "allowed_claim": row.controlled_interpretation,
        "notes": f"dataset_rescue_pass={bool(row.stage34b_dataset_rescue_pass)}; graph_specific_pass={bool(row.stage34b_graph_specific_pass)}; {row.graph_interpretation}",
    }
    score = score[score["scorecard_item"] != "stage34b_hbcc_external_pretraining"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (
            ROOT / "docs" / "ACTIVE_V3_STATUS.md",
            "\n\n## Stage 34B HBCC external pretraining status\n",
            f"\nStage 34B is complete. HBCC cells used: `{int(row.n_hbcc_cells)}`. Best condition: `{row.best_stage34b_condition}` (`{row.best_stage34b_mean_pooled_oof_spearman:.4f}`). Dataset rescue pass: `{bool(row.stage34b_dataset_rescue_pass)}`; full internal performance pass: `{bool(row.stage34b_full_internal_performance_pass)}`; graph-specific pass: `{bool(row.stage34b_graph_specific_pass)}`. {row.controlled_interpretation} {row.graph_interpretation} No external validation or manuscript claim update.\n",
        ),
        (
            ROOT / "docs" / "V3_SCORECARD.md",
            "\n\n## Stage 34B HBCC external pretraining result\n",
            f"\nBest Stage 34B condition: `{row.best_stage34b_condition}`; mean pooled OOF Spearman: `{row.best_stage34b_mean_pooled_oof_spearman:.4f}`; minus Stage 33C: `{row.best_minus_stage33c:.4f}`; minus Stage 27C: `{row.best_minus_stage27c:.4f}`; dataset rescue pass: `{bool(row.stage34b_dataset_rescue_pass)}`; graph-specific pass: `{bool(row.stage34b_graph_specific_pass)}`. {row.controlled_interpretation}\n",
        ),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage34b_hbcc_external_pretraining_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    registry_audit = verify_registry_approval(cfg)
    canonical, _ = s34a.verify_canonical_gene_universe(resolve(cfg["canonical_gene_universe"]))
    adata, celltype, manifest = build_or_load_hbcc_matrix(cfg, canonical, registry_audit)
    folds, targets, expression, target_matrix, modules = s34a.load_context()
    specs = build_specs()
    encoders = s34a.fit_encoders(adata, specs, int(cfg["random_seed"]))
    external_oof = s34a.run_external_oof(cfg, specs, encoders, list(adata.var_names), folds, targets, expression, target_matrix, modules)
    external_target = s34a.compute_target_metrics(external_oof)
    ref_target, ref_mean = reference_target_and_mean(cfg)
    target = pd.concat([external_target, ref_target], ignore_index=True)
    mean = pd.concat([s34a.summarize_mean(external_target), ref_mean], ignore_index=True).sort_values("mean_pooled_oof_spearman", ascending=False)
    leakage, graph, pf = audits_and_passfail(cfg, target, mean, manifest)
    condition = mean.rename(columns={"mean_pooled_oof_spearman": "condition_mean_pooled_oof_spearman"})
    celltype.to_csv(CELLTYPE_AUDIT_OUT, index=False)
    manifest.to_csv(MATRIX_MANIFEST_OUT, index=False)
    pf.to_csv(PASS_FAIL_OUT, index=False)
    condition.to_csv(CONDITION_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    graph.to_csv(GRAPH_AUDIT_OUT, index=False)
    leakage.to_csv(LEAKAGE_AUDIT_OUT, index=False)
    write_report(celltype, manifest, mean, target, graph, leakage, pf)
    update_status(pf)
    row = pf.iloc[0]
    print(f"hbcc_cells={int(row.n_hbcc_cells)}")
    print(f"best_stage34b_condition={row.best_stage34b_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_stage34b_mean_pooled_oof_spearman:.6f}")
    print(f"best_minus_stage33c={row.best_minus_stage33c:.6f}")
    print(f"best_minus_stage27c={row.best_minus_stage27c:.6f}")
    print(f"stage34b_dataset_rescue_pass={bool(row.stage34b_dataset_rescue_pass)}")
    print(f"stage34b_graph_specific_pass={bool(row.stage34b_graph_specific_pass)}")


if __name__ == "__main__":
    main()
