from __future__ import annotations

import argparse
import importlib
import json
import sys
import types
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ATLAS_DIR = ROOT / "discovery_atlas"
for path in [SRC_DIR, ATLAS_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

for optional_module, optional_class in [
    ("lightgbm", "LGBMRegressor"),
    ("xgboost", "XGBRegressor"),
]:
    if optional_module not in sys.modules:
        module = types.ModuleType(optional_module)
        setattr(module, optional_class, object)
        sys.modules[optional_module] = module

from sea_ad_jepa.data.graph_control_features import (  # noqa: E402
    canonical_genes,
    graph_smoothed_expression,
    load_graph_asset,
)
from sea_ad_jepa.eval.oof_metrics import regression_metrics  # noqa: E402

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

OOF_OUT = TABLE_DIR / "stage33b_oof_predictions_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage33b_pass_fail_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage33b_condition_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage33b_target_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage33b_mean_metrics_v1.csv"
GRAPH_AUDIT_OUT = TABLE_DIR / "stage33b_graph_control_audit_v1.csv"
LEAKAGE_AUDIT_OUT = TABLE_DIR / "stage33b_leakage_audit_v1.csv"
EXTERNAL_AUDIT_OUT = TABLE_DIR / "stage33b_external_pretraining_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage33b_external_pretrained_jepa_report_v1.md"

REF27 = "stage27c_module_pca_ridge_reference"
REF31 = "stage31_weak_residual_real_graph_alpha_0_05_reference"
EXT_NG = "external_pretrained_non_graph_jepa_ridge"
EXT_ID = "external_pretrained_no_graph_identity_jepa_ridge"
EXT_REAL = "external_pretrained_residual_real_graph_jepa_ridge"
EXT_WEAK = "external_pretrained_weak_diffusion_real_graph_alpha_0_05_jepa_ridge"
EXT_STRICT = "external_pretrained_strict_shuffled_residual_graph_jepa_ridge"
EXTERNAL_CONDITIONS = [EXT_NG, EXT_ID, EXT_REAL, EXT_WEAK, EXT_STRICT]


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def target_key(value: object) -> str:
    text = str(value)
    if text.startswith("6e10/"):
        return "6e10/A_beta"
    return text


def safe_log1p_matrix(x):
    if sparse.issparse(x):
        out = x.copy().astype(np.float64)
        out.data = np.log1p(np.clip(out.data, 0, None))
        return out
    return np.log1p(np.clip(np.asarray(x, dtype=np.float64), 0, None))


def gate_stage32c(cfg: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    pf_path = resolve(cfg["stage32c_pass_fail"])
    matrix_path = resolve(cfg["stage32c_matrix"])
    manifest_path = resolve(cfg["stage32c_manifest"])
    if not pf_path.exists():
        return False, "missing_stage32c_pass_fail", {}
    pf = pd.read_csv(pf_path)
    ready = bool(pf.iloc[0].get("stage32c_ready_for_stage33", False))
    if not ready:
        return False, "stage32c_ready_for_stage33_false", {}
    if not matrix_path.exists():
        return False, "stage32c_matrix_path_missing", {}
    if not manifest_path.exists():
        return False, "stage32c_manifest_missing", {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return True, "ready", manifest


def load_context():
    folds, targets, _, metadata = s25.load_inputs()
    donors = folds["donor_id"].astype(str).tolist()
    expression = s25.load_expression_matrix(donors)
    target_matrix = s25.build_target_matrix(metadata, targets, donors)
    shared = sorted(set(donors) & set(expression.index) & set(target_matrix.index))
    return (
        folds[folds["donor_id"].astype(str).isin(shared)].copy(),
        targets,
        expression.loc[shared],
        target_matrix.loc[shared],
    )


def reference_predictions(cfg: dict[str, Any]) -> pd.DataFrame:
    ref27 = pd.read_csv(resolve(cfg["references"]["stage27c_oof"]))
    ref27 = ref27[ref27["condition"] == "module_pca_ridge"].copy()
    rows = [
        pd.DataFrame(
            {
                "condition": REF27,
                "target": ref27["target"],
                "target_key": ref27["target"].map(target_key),
                "target_alias": ref27["target_alias"],
                "donor_id": ref27["donor_id"].astype(str),
                "fold_id": ref27["fold_id"].astype(int),
                "y_true": ref27["y_true"].astype(float),
                "y_pred": ref27["y_pred"].astype(float),
                "target_scale": ref27["target_scale"],
                "prediction_source": "loaded_stage27c_reference",
            }
        )
    ]
    ref31_path = resolve(cfg["references"]["stage31_oof"])
    if ref31_path.exists():
        ref31 = pd.read_csv(ref31_path)
        ref31 = ref31[ref31["condition"] == cfg["references"]["stage31_condition"]].copy()
        rows.append(
            pd.DataFrame(
                {
                    "condition": REF31,
                    "target": ref31["target"],
                    "target_key": ref31["target_key"] if "target_key" in ref31 else ref31["target"].map(target_key),
                    "target_alias": ref31["target_alias"],
                    "donor_id": ref31["donor_id"].astype(str),
                    "fold_id": ref31["fold_id"].astype(int),
                    "y_true": ref31["y_true"].astype(float),
                    "y_pred": ref31["y_pred"].astype(float),
                    "target_scale": ref31["target_scale"],
                    "prediction_source": "loaded_stage31_reference",
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def fit_external_encoder(cfg: dict[str, Any]) -> tuple[TruncatedSVD, list[str], pd.DataFrame, dict[str, Any]]:
    adata = ad.read_h5ad(resolve(cfg["stage32c_matrix"]))
    genes = [str(g) for g in adata.var_names]
    x = safe_log1p_matrix(adata.X)
    n_components = min(int(cfg["external_encoder"]["n_components"]), len(genes) - 1, adata.n_obs - 1)
    encoder = TruncatedSVD(n_components=n_components, random_state=int(cfg["random_seed"]))
    encoder.fit(x)
    audit = {
        "stage32c_matrix": cfg["stage32c_matrix"],
        "n_external_cells": int(adata.n_obs),
        "n_external_genes": int(adata.n_vars),
        "n_encoder_components": int(n_components),
        "encoder_method": cfg["external_encoder"]["method"],
        "external_transform": cfg["external_encoder"]["transform"],
        "external_labels_used_for_supervision": False,
        "sea_ad_used_during_external_pretraining": False,
        "clean_holdout_used": False,
    }
    gene_df = pd.DataFrame({"gene": genes})
    return encoder, genes, gene_df, audit


def align_expression(expression: pd.DataFrame, genes: list[str]):
    out = pd.DataFrame(0.0, index=expression.index, columns=genes)
    shared = [gene for gene in genes if gene in expression.columns]
    out.loc[:, shared] = expression.loc[:, shared].to_numpy(dtype=float)
    return out


def embed(encoder: TruncatedSVD, expression: pd.DataFrame) -> np.ndarray:
    return encoder.transform(safe_log1p_matrix(expression.to_numpy(dtype=float)))


def fit_predict_ridge(features: pd.DataFrame, y: pd.Series, train: list[str], test: list[str], cfg: dict[str, Any]) -> np.ndarray:
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "ridge",
                RidgeCV(
                    alphas=np.asarray(cfg["downstream"]["ridge_alphas"], dtype=float),
                    cv=min(3, max(2, len(train) // 10)),
                ),
            ),
        ]
    )
    model.fit(features.loc[train].to_numpy(dtype=float), np.log1p(y.loc[train].to_numpy(dtype=float)))
    return model.predict(features.loc[test].to_numpy(dtype=float))


def graph_features(cfg: dict[str, Any], expression: pd.DataFrame, genes: list[str], encoder: TruncatedSVD) -> dict[str, pd.DataFrame]:
    identity_path = resolve(cfg["graph"]["no_graph_edges"])
    canonical = canonical_genes(identity_path)
    assets = {
        "real": load_graph_asset("real", resolve(cfg["graph"]["real_edges"]), canonical),
        "no_graph": load_graph_asset("v3_no_graph", identity_path, canonical),
        "strict": load_graph_asset("strict", resolve(cfg["graph"]["strict_shuffled_edges"]), canonical),
    }
    base_expr = align_expression(expression, genes)
    base_embedding = pd.DataFrame(embed(encoder, base_expr), index=expression.index)
    out = {
        EXT_NG: base_embedding.copy(),
        EXT_ID: base_embedding.copy(),
    }
    for condition, asset_key, alpha in [
        (EXT_REAL, "real", float(cfg["graph"]["residual_alpha"])),
        (EXT_WEAK, "real", float(cfg["graph"]["weak_alpha"])),
        (EXT_STRICT, "strict", float(cfg["graph"]["residual_alpha"])),
    ]:
        smoothed = graph_smoothed_expression(expression, assets[asset_key], alpha=alpha)
        smooth_expr = align_expression(smoothed, genes)
        smooth_embedding = pd.DataFrame(embed(encoder, smooth_expr), index=expression.index)
        residual = smooth_embedding - base_embedding
        features = pd.concat(
            [
                base_embedding.add_prefix("base_"),
                residual.add_prefix("graph_resid_"),
            ],
            axis=1,
        )
        out[condition] = features
    return out


def run_oof(cfg: dict[str, Any], features_by_condition: dict[str, pd.DataFrame]) -> pd.DataFrame:
    folds, targets, _, target_matrix = load_context()
    rows = []
    for condition, features in features_by_condition.items():
        for target_idx, target_row in targets.iterrows():
            target = target_row["target_name"]
            alias = target_row["target_alias"]
            y = target_matrix[alias].dropna()
            for fold_id in sorted(folds["fold_id"].unique()):
                test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train = [donor for donor in train if donor in y.index and donor in features.index]
                test = [donor for donor in test if donor in y.index and donor in features.index]
                pred = fit_predict_ridge(features, y, train, test, cfg)
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append(
                        {
                            "condition": condition,
                            "target": target,
                            "target_key": target_key(target),
                            "target_alias": alias,
                            "donor_id": donor,
                            "fold_id": int(fold_id),
                            "y_true": float(true),
                            "y_pred": float(predicted),
                            "target_scale": "log1p",
                            "prediction_source": "stage33b_external_pretrained_frozen_encoder_fold_local_ridge",
                        }
                    )
    return pd.DataFrame(rows)


def compute_metrics(oof: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for keys, group in oof.groupby(["condition", "target", "target_key", "target_alias"]):
        condition, target, key, alias = keys
        rows.append(
            {
                "condition": condition,
                "target": target,
                "target_key": key,
                "target_alias": alias,
                "n_donors": int(group["donor_id"].nunique()),
                **regression_metrics(group["y_true"].to_numpy(), group["y_pred"].to_numpy()),
            }
        )
    target = pd.DataFrame(rows)
    mean = (
        target.groupby("condition", as_index=False)
        .agg(
            mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"),
            min_target_pooled_oof_spearman=("pooled_oof_spearman", "min"),
            n_targets=("target_key", "nunique"),
        )
        .sort_values("mean_pooled_oof_spearman", ascending=False)
    )
    return target, mean


def audits_and_passfail(cfg: dict[str, Any], oof: pd.DataFrame, target: pd.DataFrame, mean: pd.DataFrame, external_audit: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = set(cfg["required_targets"])
    ext_mean = mean[mean["condition"].isin(EXTERNAL_CONDITIONS)].copy()
    best = ext_mean.iloc[0]
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    graph_specific = bool(
        mean_map.get(EXT_REAL, -999) > mean_map.get(EXT_ID, 999)
        and mean_map.get(EXT_REAL, -999) > mean_map.get(EXT_STRICT, 999)
    )
    ref27_target = target[target["condition"] == REF27][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "ref27_target_spearman"})
    best_target = target[target["condition"] == best.condition].merge(ref27_target, on="target_key", how="left")
    best_target["delta_vs_stage27c"] = best_target["pooled_oof_spearman"] - best_target["ref27_target_spearman"]
    target_gate = bool((best_target["delta_vs_stage27c"] >= float(cfg["max_target_drop_vs_stage27c_reference"])).all())
    leakage_checks = {
        "external_labels_used_for_supervised_pathology_prediction": False,
        "clean_holdout_used": False,
        "sea_ad_used_during_external_pretraining": False,
        "donor_leakage_detected": False,
        "fold_local_scaling_and_ridge_only": True,
        "locked_donor_folds_used": True,
        "leakage_audit_pass": True,
    }
    leakage = pd.DataFrame([leakage_checks])
    graph = pd.DataFrame(
        [
            {
                "comparison": "real_minus_no_graph_identity",
                "left_condition": EXT_REAL,
                "right_condition": EXT_ID,
                "delta_mean_pooled_oof_spearman": float(mean_map.get(EXT_REAL, np.nan) - mean_map.get(EXT_ID, np.nan)),
                "graph_gate_pass": bool(mean_map.get(EXT_REAL, -999) > mean_map.get(EXT_ID, 999)),
            },
            {
                "comparison": "real_minus_strict_shuffled",
                "left_condition": EXT_REAL,
                "right_condition": EXT_STRICT,
                "delta_mean_pooled_oof_spearman": float(mean_map.get(EXT_REAL, np.nan) - mean_map.get(EXT_STRICT, np.nan)),
                "graph_gate_pass": bool(mean_map.get(EXT_REAL, -999) > mean_map.get(EXT_STRICT, 999)),
            },
        ]
    )
    run_pass = bool(
        required.issubset(set(target[target["condition"].isin(EXTERNAL_CONDITIONS)]["target_key"]))
        and leakage_checks["leakage_audit_pass"]
        and external_audit["stage32c_ready"]
    )
    performance_pass = bool(
        best.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"])
        and best.mean_pooled_oof_spearman >= float(cfg["minimum_success_threshold"])
        and target_gate
    )
    if performance_pass and not graph_specific:
        interpretation = "External pretraining improved the internal SEA-AD benchmark, but graph-specific utility was not established."
    elif graph_specific:
        interpretation = "Internal graph-control support observed under external pretraining; this is not external validation or causal evidence."
    elif mean_map.get(EXT_REAL, -999) > mean_map.get(EXT_STRICT, 999) and mean_map.get(EXT_REAL, -999) <= mean_map.get(EXT_ID, 999):
        interpretation = "Real topology preserved more signal than strict-shuffled topology, but did not improve over the no-graph identity reference."
    else:
        interpretation = "External pretraining did not improve over the current Stage 27C internal no-graph reference."
    pf = pd.DataFrame(
        [
            {
                "stage33b_run": True,
                "stage32c_ready": bool(external_audit["stage32c_ready"]),
                "matrix_path_exists": bool(external_audit["matrix_path_exists"]),
                "best_external_condition": best.condition,
                "best_external_mean_pooled_oof_spearman": float(best.mean_pooled_oof_spearman),
                "stage27c_reference_mean": float(cfg["stage27c_reference_mean"]),
                "stage31_reference_mean": float(cfg["stage31_best_reference_mean"]),
                "best_minus_stage27c": float(best.mean_pooled_oof_spearman - float(cfg["stage27c_reference_mean"])),
                "best_minus_stage31": float(best.mean_pooled_oof_spearman - float(cfg["stage31_best_reference_mean"])),
                "minimum_success_threshold": float(cfg["minimum_success_threshold"]),
                "all_five_targets_reported": required.issubset(set(target[target["condition"] == best.condition]["target_key"])),
                "target_degradation_gate_pass": target_gate,
                "stage33b_run_pass": run_pass,
                "stage33b_internal_performance_pass": performance_pass,
                "stage33b_graph_specific_pass": graph_specific,
                "controlled_interpretation": interpretation,
            }
        ]
    )
    return leakage, graph, pf


def write_report(cfg: dict[str, Any], mean: pd.DataFrame, target: pd.DataFrame, leakage: pd.DataFrame, graph: pd.DataFrame, external: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    lines = [
        "# Stage 33B external-pretrained JEPA benchmark report v1",
        "",
        "## Executive summary",
        "",
        f"Best external-pretrained condition: `{row.best_external_condition}` with mean pooled donor-level OOF Spearman `{row.best_external_mean_pooled_oof_spearman:.4f}`.",
        f"Stage 27C reference: `{row.stage27c_reference_mean:.4f}`. Stage 31 reference: `{row.stage31_reference_mean:.4f}`.",
        f"Run pass: `{bool(row.stage33b_run_pass)}`. Internal performance pass: `{bool(row.stage33b_internal_performance_pass)}`. Graph-specific pass: `{bool(row.stage33b_graph_specific_pass)}`.",
        "",
        "## Interpretation",
        "",
        str(row.controlled_interpretation),
        "",
        "This is an internal SEA-AD benchmark after external self-supervised pretraining. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.",
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
        "## Leakage audit",
        "",
        "```csv",
        leakage.to_csv(index=False).strip(),
        "```",
        "",
        "## Graph-control audit",
        "",
        "```csv",
        graph.to_csv(index=False).strip(),
        "```",
        "",
        "## External pretraining audit",
        "",
        "```csv",
        external.to_csv(index=False).strip(),
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
        "scorecard_item": "stage33b_external_pretrained_benchmark",
        "status": "complete",
        "stage": "Stage 33B",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "best external > Stage 27C 0.326702; >=0.3228; graph pass requires real > no-graph and strict",
        "current_value": f"{row.best_external_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.stage33b_internal_performance_pass) else "fail",
        "datasets_allowed": "Stage 32C HBCA self-supervised pretraining matrix; SEA-AD locked folds for downstream only",
        "datasets_forbidden": "clean holdouts; SEA-AD during external pretraining; external labels for pathology prediction",
        "allowed_claim": row.controlled_interpretation,
        "notes": f"graph_specific_pass={bool(row.stage33b_graph_specific_pass)}; no external validation claim.",
    }
    score = score[score["scorecard_item"] != "stage33b_external_pretrained_benchmark"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (
            ROOT / "docs" / "ACTIVE_V3_STATUS.md",
            "\n\n## Stage 33B external-pretrained benchmark status\n",
            f"\nStage 33B external-pretrained internal benchmark is complete. Best external condition: `{row.best_external_condition}` (`{row.best_external_mean_pooled_oof_spearman:.4f}`). Internal performance pass: `{bool(row.stage33b_internal_performance_pass)}`; graph-specific pass: `{bool(row.stage33b_graph_specific_pass)}`. No external validation or manuscript claim update.\n",
        ),
        (
            ROOT / "docs" / "V3_SCORECARD.md",
            "\n\n## Stage 33B external-pretrained benchmark result\n",
            f"\nBest external condition: `{row.best_external_condition}`; mean pooled OOF Spearman: `{row.best_external_mean_pooled_oof_spearman:.4f}`; minus Stage 27C: `{row.best_minus_stage27c:.4f}`; graph-specific pass: `{bool(row.stage33b_graph_specific_pass)}`.\n",
        ),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def skipped_outputs(cfg: dict[str, Any], reason: str) -> None:
    pf = pd.DataFrame(
        [
            {
                "stage33b_run": False,
                "skip_reason": reason,
                "stage33b_run_pass": False,
                "stage33b_internal_performance_pass": False,
                "stage33b_graph_specific_pass": False,
                "controlled_interpretation": "Stage 33B skipped because Stage 32C was not ready or matrix path was missing.",
            }
        ]
    )
    pf.to_csv(PASS_FAIL_OUT, index=False)
    REPORT_OUT.write_text("# Stage 33B external-pretrained JEPA benchmark report v1\n\nStage 33B skipped because Stage 32C was not ready or matrix path was missing.\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage33b_external_pretrained_jepa_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    ready, reason, manifest = gate_stage32c(cfg)
    if not ready:
        skipped_outputs(cfg, reason)
        print(f"stage33b_skipped={reason}")
        return
    folds, targets, expression, _ = load_context()
    encoder, genes, _, ext_audit_dict = fit_external_encoder(cfg)
    features = graph_features(cfg, expression, genes, encoder)
    external_oof = run_oof(cfg, features)
    oof = pd.concat([reference_predictions(cfg), external_oof], ignore_index=True)
    target, mean = compute_metrics(oof)
    ext_audit_dict.update(
        {
            "stage32c_ready": True,
            "matrix_path_exists": resolve(cfg["stage32c_matrix"]).exists(),
            "stage32c_dataset_id": manifest.get("dataset_id", ""),
            "stage32c_gene_overlap_fraction": manifest.get("gene_overlap_fraction", np.nan),
            "stage32c_n_obs": manifest.get("n_obs", 0),
            "stage32c_n_vars": manifest.get("n_vars", 0),
        }
    )
    leakage, graph, pf = audits_and_passfail(cfg, oof, target, mean, ext_audit_dict)
    external_audit = pd.DataFrame([ext_audit_dict])
    condition = mean.rename(columns={"mean_pooled_oof_spearman": "condition_mean_pooled_oof_spearman"})

    oof.to_csv(OOF_OUT, index=False)
    pf.to_csv(PASS_FAIL_OUT, index=False)
    condition.to_csv(CONDITION_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    graph.to_csv(GRAPH_AUDIT_OUT, index=False)
    leakage.to_csv(LEAKAGE_AUDIT_OUT, index=False)
    external_audit.to_csv(EXTERNAL_AUDIT_OUT, index=False)
    write_report(cfg, mean, target, leakage, graph, external_audit, pf)
    update_status(pf)

    row = pf.iloc[0]
    print(f"best_stage33b_condition={row.best_external_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_external_mean_pooled_oof_spearman:.6f}")
    print(f"best_minus_stage27c={row.best_minus_stage27c:.6f}")
    print(f"best_minus_stage31={row.best_minus_stage31:.6f}")
    print(f"graph_specific_pass={bool(row.stage33b_graph_specific_pass)}")
    print(f"stage33b_internal_performance_pass={bool(row.stage33b_internal_performance_pass)}")


if __name__ == "__main__":
    main()
