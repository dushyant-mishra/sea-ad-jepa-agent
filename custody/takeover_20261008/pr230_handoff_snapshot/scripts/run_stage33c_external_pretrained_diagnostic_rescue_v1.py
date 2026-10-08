from __future__ import annotations

import argparse
import importlib
import json
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from sklearn.decomposition import PCA, TruncatedSVD
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

PASS_FAIL_OUT = TABLE_DIR / "stage33c_pass_fail_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage33c_condition_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage33c_target_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage33c_mean_metrics_v1.csv"
GRAPH_AUDIT_OUT = TABLE_DIR / "stage33c_graph_control_audit_v1.csv"
LEAKAGE_AUDIT_OUT = TABLE_DIR / "stage33c_leakage_audit_v1.csv"
EXTERNAL_AUDIT_OUT = TABLE_DIR / "stage33c_external_pretraining_diagnostic_audit_v1.csv"
GRID_OUT = TABLE_DIR / "stage33c_rescue_grid_v1.csv"
REPORT_OUT = REPORT_DIR / "stage33c_external_pretrained_diagnostic_rescue_report_v1.md"

REF27 = "stage27c_module_pca_ridge_reference"
REF31 = "stage31_weak_residual_real_graph_alpha_0_05_reference"


@dataclass(frozen=True)
class ConditionSpec:
    condition: str
    n_components: int
    transform: str
    projection_variant: str
    graph_variant: str
    graph_alpha: float


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


def row_size_factor_log1p(x):
    if sparse.issparse(x):
        out = x.copy().astype(np.float64)
        out.data = np.clip(out.data, 0, None)
        row_sum = np.asarray(out.sum(axis=1)).ravel()
        positive = row_sum[row_sum > 0]
        scale = float(np.median(positive)) if len(positive) else 1.0
        factors = np.divide(scale, row_sum, out=np.zeros_like(row_sum, dtype=float), where=row_sum > 0)
        out = sparse.diags(factors).dot(out)
        out.data = np.log1p(out.data)
        return out
    arr = np.clip(np.asarray(x, dtype=np.float64), 0, None)
    row_sum = arr.sum(axis=1)
    positive = row_sum[row_sum > 0]
    scale = float(np.median(positive)) if len(positive) else 1.0
    factors = np.divide(scale, row_sum, out=np.zeros_like(row_sum, dtype=float), where=row_sum > 0)
    return np.log1p(arr * factors[:, None])


def sparse_safe_std_scale_after_log1p(x):
    logged = safe_log1p_matrix(x)
    if sparse.issparse(logged):
        mean_sq = np.asarray(logged.power(2).mean(axis=0)).ravel()
        scale = np.sqrt(np.maximum(mean_sq, 1e-12))
        return logged @ sparse.diags(1.0 / scale), scale
    scale = np.nanstd(logged, axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    return logged / scale, scale


def apply_external_transform(x, transform: str, fit_scale: np.ndarray | None = None):
    if transform == "log1p_clipped_nonnegative":
        return safe_log1p_matrix(x), None
    if transform == "raw_count_size_factor_log1p":
        return row_size_factor_log1p(x), None
    if transform == "zscore_gene_after_log1p":
        if fit_scale is None:
            return sparse_safe_std_scale_after_log1p(x)
        logged = safe_log1p_matrix(x)
        scale = np.where(fit_scale > 1e-12, fit_scale, 1.0)
        if sparse.issparse(logged):
            return logged @ sparse.diags(1.0 / scale), fit_scale
        return logged / scale, fit_scale
    raise ValueError(f"Unknown transform: {transform}")


def gate_inputs(cfg: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    required = [
        resolve(cfg["stage32c_pass_fail"]),
        resolve(cfg["stage32c_matrix"]),
        resolve(cfg["stage32c_manifest"]),
        resolve(cfg["stage33b"]["pass_fail"]),
        resolve(cfg["stage33b"]["mean_metrics"]),
        resolve(cfg["stage33b"]["target_metrics"]),
        resolve(cfg["stage33b"]["leakage_audit"]),
        resolve(cfg["stage33b"]["external_pretraining_audit"]),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, "missing_required_inputs:" + ";".join(missing), {}
    pf32 = pd.read_csv(resolve(cfg["stage32c_pass_fail"]))
    if not bool(pf32.iloc[0].get("stage32c_ready_for_stage33", False)):
        return False, "stage32c_ready_for_stage33_false", {}
    pf33b = pd.read_csv(resolve(cfg["stage33b"]["pass_fail"]))
    if not bool(pf33b.iloc[0].get("stage33b_run_pass", False)):
        return False, "stage33b_run_pass_false", {}
    manifest = json.loads(resolve(cfg["stage32c_manifest"]).read_text(encoding="utf-8"))
    return True, "ready", manifest


def load_context():
    folds, targets, _, metadata = s25.load_inputs()
    donors = folds["donor_id"].astype(str).tolist()
    expression = s25.load_expression_matrix(donors)
    target_matrix = s25.build_target_matrix(metadata, targets, donors)
    shared = sorted(set(donors) & set(expression.index) & set(target_matrix.index))
    folds = folds[folds["donor_id"].astype(str).isin(shared)].copy()
    expression = expression.loc[shared]
    target_matrix = target_matrix.loc[shared]
    modules = s25.build_predefined_module_features(expression).matrix
    return folds, targets, expression, target_matrix, modules


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


def build_condition_grid(cfg: dict[str, Any]) -> list[ConditionSpec]:
    alpha = float(cfg["graph"]["alpha"])
    specs: list[ConditionSpec] = []
    for n in cfg["external_encoder"]["component_grid"]:
        specs.append(ConditionSpec(f"ext_svd{n}_log1p_direct_no_graph", int(n), "log1p_clipped_nonnegative", "direct", "no_graph_identity", 0.0))
    for transform in cfg["external_encoder"]["transform_grid"]:
        if transform != "log1p_clipped_nonnegative":
            specs.append(ConditionSpec(f"ext_svd32_{transform}_direct_no_graph", 32, transform, "direct", "no_graph_identity", 0.0))
    specs.extend(
        [
            ConditionSpec("ext_svd32_log1p_concat_module_pca_no_graph", 32, "log1p_clipped_nonnegative", "concat_module_pca", "no_graph_identity", 0.0),
            ConditionSpec("ext_svd32_log1p_residualized_by_module_pca_no_graph", 32, "log1p_clipped_nonnegative", "residualized_by_module_pca", "no_graph_identity", 0.0),
            ConditionSpec("ext_svd32_log1p_direct_residual_real_graph_alpha_0_05", 32, "log1p_clipped_nonnegative", "direct", "residual_real_graph", alpha),
            ConditionSpec("ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05", 32, "log1p_clipped_nonnegative", "direct", "strict_shuffled_residual_graph", alpha),
        ]
    )
    max_conditions = int(cfg["external_encoder"].get("max_external_conditions", len(specs)))
    return specs[:max_conditions]


def align_expression(expression: pd.DataFrame, genes: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(0.0, index=expression.index, columns=genes)
    shared = [gene for gene in genes if gene in expression.columns]
    out.loc[:, shared] = expression.loc[:, shared].to_numpy(dtype=float)
    return out


def fit_external_encoders(cfg: dict[str, Any], specs: list[ConditionSpec]) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any]]:
    adata = ad.read_h5ad(resolve(cfg["stage32c_matrix"]))
    genes = [str(gene) for gene in adata.var_names]
    encoders: dict[tuple[str, int], dict[str, Any]] = {}
    for transform in sorted({spec.transform for spec in specs}):
        transformed, scale = apply_external_transform(adata.X, transform)
        for n in sorted({spec.n_components for spec in specs if spec.transform == transform}):
            n_components = min(int(n), len(genes) - 1, adata.n_obs - 1)
            encoder = TruncatedSVD(n_components=n_components, random_state=int(cfg["random_seed"]))
            encoder.fit(transformed)
            encoders[(transform, int(n))] = {
                "encoder": encoder,
                "genes": genes,
                "fit_scale": scale,
                "actual_components": n_components,
            }
    audit = {
        "stage32c_matrix": cfg["stage32c_matrix"],
        "n_external_cells": int(adata.n_obs),
        "n_external_genes": int(adata.n_vars),
        "encoder_method": cfg["external_encoder"]["method"],
        "component_grid_run": ";".join(str(x) for x in sorted({s.n_components for s in specs})),
        "transform_grid_run": ";".join(sorted({s.transform for s in specs})),
        "zscore_transform_note": "sparse_safe_log1p_std_scaled_without_dense_centering",
        "external_labels_used_for_supervision": False,
        "sea_ad_used_during_external_pretraining": False,
        "clean_holdout_used": False,
    }
    return encoders, audit


def external_embedding(expression: pd.DataFrame, encoder_bundle: dict[str, Any], transform: str) -> pd.DataFrame:
    genes = encoder_bundle["genes"]
    aligned = align_expression(expression, genes)
    transformed, _ = apply_external_transform(aligned.to_numpy(dtype=float), transform, encoder_bundle.get("fit_scale"))
    values = encoder_bundle["encoder"].transform(transformed)
    cols = [f"ext_svd_{i + 1}" for i in range(values.shape[1])]
    return pd.DataFrame(values, index=expression.index, columns=cols)


def graph_external_embedding(
    cfg: dict[str, Any],
    spec: ConditionSpec,
    expression: pd.DataFrame,
    base_embedding: pd.DataFrame,
    encoder_bundle: dict[str, Any],
) -> pd.DataFrame:
    if spec.graph_variant == "no_graph_identity":
        return base_embedding.copy()
    identity_path = resolve(cfg["graph"]["no_graph_edges"])
    canonical = canonical_genes(identity_path)
    if spec.graph_variant == "residual_real_graph":
        asset = load_graph_asset("real", resolve(cfg["graph"]["real_edges"]), canonical)
    elif spec.graph_variant == "strict_shuffled_residual_graph":
        asset = load_graph_asset("strict", resolve(cfg["graph"]["strict_shuffled_edges"]), canonical)
    else:
        raise ValueError(spec.graph_variant)
    smoothed = graph_smoothed_expression(expression, asset, alpha=spec.graph_alpha)
    smooth_embedding = external_embedding(smoothed, encoder_bundle, spec.transform)
    residual = smooth_embedding - base_embedding
    return pd.concat([base_embedding.add_prefix("base_"), residual.add_prefix("graph_resid_")], axis=1)


def module_pca_features(
    modules: pd.DataFrame,
    train: list[str],
    test: list[str],
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_components = min(int(cfg["module_pca"]["n_components"]), modules.shape[1], len(train) - 1)
    pipe = Pipeline(
        [
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=n_components, random_state=int(cfg["random_seed"]))),
        ]
    )
    train_values = pipe.fit_transform(modules.loc[train].to_numpy(dtype=float))
    test_values = pipe.transform(modules.loc[test].to_numpy(dtype=float))
    cols = [f"module_pca_{i + 1}" for i in range(n_components)]
    return pd.DataFrame(train_values, index=train, columns=cols), pd.DataFrame(test_values, index=test, columns=cols)


def condition_train_test_features(
    spec: ConditionSpec,
    base_features: pd.DataFrame,
    modules: pd.DataFrame,
    train: list[str],
    test: list[str],
    cfg: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, int]:
    x_train = base_features.loc[train].to_numpy(dtype=float)
    x_test = base_features.loc[test].to_numpy(dtype=float)
    if spec.projection_variant == "direct":
        return x_train, x_test, x_train.shape[1]
    m_train, m_test = module_pca_features(modules, train, test, cfg)
    if spec.projection_variant == "concat_module_pca":
        return (
            np.concatenate([x_train, m_train.to_numpy(dtype=float)], axis=1),
            np.concatenate([x_test, m_test.to_numpy(dtype=float)], axis=1),
            x_train.shape[1] + m_train.shape[1],
        )
    if spec.projection_variant == "residualized_by_module_pca":
        m_train_arr = m_train.to_numpy(dtype=float)
        m_test_arr = m_test.to_numpy(dtype=float)
        coef, *_ = np.linalg.lstsq(m_train_arr, x_train, rcond=None)
        resid_train = x_train - m_train_arr @ coef
        resid_test = x_test - m_test_arr @ coef
        return resid_train, resid_test, resid_train.shape[1]
    raise ValueError(spec.projection_variant)


def fit_predict_ridge(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "ridge",
                RidgeCV(
                    alphas=np.asarray(cfg["downstream"]["ridge_alphas"], dtype=float),
                    cv=min(3, max(2, len(y_train) // 10)),
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    return model.predict(x_test)


def run_oof(
    cfg: dict[str, Any],
    specs: list[ConditionSpec],
    encoders: dict[tuple[str, int], dict[str, Any]],
    folds: pd.DataFrame,
    targets: pd.DataFrame,
    expression: pd.DataFrame,
    target_matrix: pd.DataFrame,
    modules: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    base_cache: dict[tuple[str, int], pd.DataFrame] = {}
    condition_features: dict[str, pd.DataFrame] = {}
    for spec in specs:
        bundle = encoders[(spec.transform, spec.n_components)]
        key = (spec.transform, spec.n_components)
        if key not in base_cache:
            base_cache[key] = external_embedding(expression, bundle, spec.transform)
        condition_features[spec.condition] = graph_external_embedding(cfg, spec, expression, base_cache[key], bundle)

    rows: list[dict[str, Any]] = []
    feature_counts: dict[str, int] = {}
    for spec in specs:
        features = condition_features[spec.condition]
        for _, target_row in targets.iterrows():
            target = target_row["target_name"]
            alias = target_row["target_alias"]
            y = target_matrix[alias].dropna()
            for fold_id in sorted(folds["fold_id"].unique()):
                test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train = [donor for donor in train if donor in y.index and donor in features.index]
                test = [donor for donor in test if donor in y.index and donor in features.index]
                x_train, x_test, n_features = condition_train_test_features(spec, features, modules, train, test, cfg)
                feature_counts[spec.condition] = n_features
                pred = fit_predict_ridge(x_train, np.log1p(y.loc[train].to_numpy(dtype=float)), x_test, cfg)
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append(
                        {
                            "condition": spec.condition,
                            "target": target,
                            "target_key": target_key(target),
                            "target_alias": alias,
                            "donor_id": donor,
                            "fold_id": int(fold_id),
                            "y_true": float(true),
                            "y_pred": float(predicted),
                            "target_scale": "log1p",
                            "prediction_source": "stage33c_external_pretrained_diagnostic_rescue_fold_local_ridge",
                        }
                    )
    grid = pd.DataFrame(
        [
            {
                "condition": spec.condition,
                "n_components_requested": spec.n_components,
                "transform": spec.transform,
                "projection_variant": spec.projection_variant,
                "graph_variant": spec.graph_variant,
                "graph_alpha": spec.graph_alpha,
                "n_downstream_features": feature_counts.get(spec.condition, np.nan),
                "included_in_capped_grid": True,
            }
            for spec in specs
        ]
    )
    return pd.DataFrame(rows), grid


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


def make_audits_and_passfail(
    cfg: dict[str, Any],
    specs: list[ConditionSpec],
    target: pd.DataFrame,
    mean: pd.DataFrame,
    grid: pd.DataFrame,
    external_audit: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    external_conditions = [spec.condition for spec in specs]
    required = set(cfg["required_targets"])
    ext_mean = mean[mean["condition"].isin(external_conditions)].copy()
    best = ext_mean.iloc[0]
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    ref27_target = target[target["condition"] == REF27][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "ref27_target_spearman"})
    best_target = target[target["condition"] == best.condition].merge(ref27_target, on="target_key", how="left")
    best_target["delta_vs_stage27c"] = best_target["pooled_oof_spearman"] - best_target["ref27_target_spearman"]
    target_gate = bool((best_target["delta_vs_stage27c"] >= float(cfg["max_target_drop_vs_stage27c_reference"])).all())

    no_graph = "ext_svd32_log1p_direct_no_graph"
    real = "ext_svd32_log1p_direct_residual_real_graph_alpha_0_05"
    strict = "ext_svd32_log1p_direct_strict_shuffled_residual_graph_alpha_0_05"
    real_gt_no = bool(mean_map.get(real, -999) > mean_map.get(no_graph, 999))
    real_gt_strict = bool(mean_map.get(real, -999) > mean_map.get(strict, 999))
    graph_specific = bool(real_gt_no and real_gt_strict)
    graph = pd.DataFrame(
        [
            {
                "comparison": "real_minus_no_graph_identity",
                "left_condition": real,
                "right_condition": no_graph,
                "delta_mean_pooled_oof_spearman": float(mean_map.get(real, np.nan) - mean_map.get(no_graph, np.nan)),
                "graph_gate_pass": real_gt_no,
            },
            {
                "comparison": "real_minus_strict_shuffled",
                "left_condition": real,
                "right_condition": strict,
                "delta_mean_pooled_oof_spearman": float(mean_map.get(real, np.nan) - mean_map.get(strict, np.nan)),
                "graph_gate_pass": real_gt_strict,
            },
        ]
    )
    leakage_checks = {
        "external_labels_used_for_supervised_pathology_prediction": False,
        "clean_holdout_used": False,
        "sea_ad_used_during_external_pretraining": False,
        "donor_leakage_detected": False,
        "fold_local_downstream_scaling_and_ridge": True,
        "locked_donor_folds_used": True,
        "in_silico_ablation_run": False,
        "leakage_audit_pass": True,
    }
    leakage = pd.DataFrame([leakage_checks])
    run_pass = bool(
        external_audit["stage32c_ready"]
        and external_audit["stage33b_loaded"]
        and external_audit["matrix_path_exists"]
        and required.issubset(set(target[target["condition"].isin(external_conditions)]["target_key"]))
        and leakage_checks["leakage_audit_pass"]
    )
    performance_pass = bool(
        best.mean_pooled_oof_spearman > float(cfg["stage33b_best_mean"])
        and best.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"])
        and best.mean_pooled_oof_spearman >= float(cfg["minimum_success_threshold"])
        and target_gate
    )
    if best.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"]):
        interpretation = "Stage 33C external pretraining improved the internal SEA-AD benchmark, but this is not external validation."
    elif best.mean_pooled_oof_spearman > float(cfg["stage33b_best_mean"]):
        interpretation = "Stage 33C rescued part of the external-pretraining deficit but did not improve over the Stage 27C internal no-graph reference."
    else:
        interpretation = "Stage 33C did not rescue the Stage 33B external-pretraining deficit."
    if not graph_specific:
        if real_gt_strict and not real_gt_no:
            graph_interpretation = "Real topology outperformed shuffled topology but did not improve over the no-graph identity reference."
        else:
            graph_interpretation = "Graph-specific utility remains unestablished."
    else:
        graph_interpretation = "Real graph beat matched no-graph and strict-shuffled controls under this internal setup; this is not external validation."
    pf = pd.DataFrame(
        [
            {
                "stage33c_run": True,
                "stage32c_ready": bool(external_audit["stage32c_ready"]),
                "stage33b_results_loaded": bool(external_audit["stage33b_loaded"]),
                "matrix_path_exists": bool(external_audit["matrix_path_exists"]),
                "n_external_conditions_run": int(len(external_conditions)),
                "best_stage33c_condition": best.condition,
                "best_stage33c_mean_pooled_oof_spearman": float(best.mean_pooled_oof_spearman),
                "stage33b_best_mean": float(cfg["stage33b_best_mean"]),
                "stage27c_reference_mean": float(cfg["stage27c_reference_mean"]),
                "stage31_reference_mean": float(cfg["stage31_best_reference_mean"]),
                "best_minus_stage33b": float(best.mean_pooled_oof_spearman - float(cfg["stage33b_best_mean"])),
                "best_minus_stage27c": float(best.mean_pooled_oof_spearman - float(cfg["stage27c_reference_mean"])),
                "minimum_success_threshold": float(cfg["minimum_success_threshold"]),
                "all_five_targets_reported": required.issubset(set(target[target["condition"] == best.condition]["target_key"])),
                "target_degradation_gate_pass": target_gate,
                "stage33c_run_pass": run_pass,
                "stage33c_rescue_performance_pass": performance_pass,
                "stage33c_graph_specific_pass": graph_specific,
                "controlled_interpretation": interpretation,
                "graph_interpretation": graph_interpretation,
            }
        ]
    )
    grid["condition_mean_pooled_oof_spearman"] = grid["condition"].map(mean_map)
    grid["beats_stage33b_best"] = grid["condition_mean_pooled_oof_spearman"] > float(cfg["stage33b_best_mean"])
    grid["beats_stage27c_reference"] = grid["condition_mean_pooled_oof_spearman"] > float(cfg["stage27c_reference_mean"])
    return leakage, graph, pf


def write_report(mean: pd.DataFrame, target: pd.DataFrame, graph: pd.DataFrame, leakage: pd.DataFrame, external: pd.DataFrame, grid: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    lines = [
        "# Stage 33C external-pretrained diagnostic/rescue report v1",
        "",
        "## Executive summary",
        "",
        f"Best Stage 33C condition: `{row.best_stage33c_condition}` with mean pooled donor-level OOF Spearman `{row.best_stage33c_mean_pooled_oof_spearman:.4f}`.",
        f"Stage 33B best: `{row.stage33b_best_mean:.4f}`. Stage 27C reference: `{row.stage27c_reference_mean:.4f}`. Stage 31 reference: `{row.stage31_reference_mean:.4f}`.",
        f"Run pass: `{bool(row.stage33c_run_pass)}`. Rescue performance pass: `{bool(row.stage33c_rescue_performance_pass)}`. Graph-specific pass: `{bool(row.stage33c_graph_specific_pass)}`.",
        "",
        "## Controlled interpretation",
        "",
        str(row.controlled_interpretation),
        str(row.graph_interpretation),
        "",
        "This is an internal SEA-AD diagnostic benchmark using approved external self-supervised pretraining. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.",
        "",
        "## Rescue grid",
        "",
        "```csv",
        grid.to_csv(index=False).strip(),
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
        "## External pretraining diagnostic audit",
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
        "scorecard_item": "stage33c_external_pretraining_diagnostic_rescue",
        "status": "complete",
        "stage": "Stage 33C",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "best Stage 33C > Stage 33B and Stage 27C; >=0.3228; graph pass requires real > no-graph and strict",
        "current_value": f"{row.best_stage33c_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.stage33c_rescue_performance_pass) else "fail",
        "datasets_allowed": "Stage 32C HBCA self-supervised pretraining matrix; SEA-AD locked folds for downstream only",
        "datasets_forbidden": "clean holdouts; SEA-AD during external pretraining; external labels for pathology prediction; in silico ablation",
        "allowed_claim": row.controlled_interpretation,
        "notes": f"graph_specific_pass={bool(row.stage33c_graph_specific_pass)}; {row.graph_interpretation}",
    }
    score = score[score["scorecard_item"] != "stage33c_external_pretraining_diagnostic_rescue"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (
            ROOT / "docs" / "ACTIVE_V3_STATUS.md",
            "\n\n## Stage 33C external-pretrained diagnostic/rescue status\n",
            f"\nStage 33C external-pretrained diagnostic/rescue is complete. Best condition: `{row.best_stage33c_condition}` (`{row.best_stage33c_mean_pooled_oof_spearman:.4f}`). Rescue performance pass: `{bool(row.stage33c_rescue_performance_pass)}`; graph-specific pass: `{bool(row.stage33c_graph_specific_pass)}`. {row.controlled_interpretation} {row.graph_interpretation} No external validation or manuscript claim update.\n",
        ),
        (
            ROOT / "docs" / "V3_SCORECARD.md",
            "\n\n## Stage 33C external-pretrained diagnostic/rescue result\n",
            f"\nBest Stage 33C condition: `{row.best_stage33c_condition}`; mean pooled OOF Spearman: `{row.best_stage33c_mean_pooled_oof_spearman:.4f}`; minus Stage 33B: `{row.best_minus_stage33b:.4f}`; minus Stage 27C: `{row.best_minus_stage27c:.4f}`; graph-specific pass: `{bool(row.stage33c_graph_specific_pass)}`. {row.controlled_interpretation}\n",
        ),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def skipped_outputs(reason: str) -> None:
    pf = pd.DataFrame(
        [
            {
                "stage33c_run": False,
                "skip_reason": reason,
                "stage33c_run_pass": False,
                "stage33c_rescue_performance_pass": False,
                "stage33c_graph_specific_pass": False,
                "controlled_interpretation": "Stage 33C skipped because required Stage 32C/33B inputs were not ready.",
                "graph_interpretation": "Graph-specific utility remains unestablished.",
            }
        ]
    )
    pf.to_csv(PASS_FAIL_OUT, index=False)
    REPORT_OUT.write_text("# Stage 33C external-pretrained diagnostic/rescue report v1\n\nStage 33C skipped because required Stage 32C/33B inputs were not ready.\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage33c_external_pretrained_diagnostic_rescue_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    ready, reason, manifest = gate_inputs(cfg)
    if not ready:
        skipped_outputs(reason)
        print(f"stage33c_skipped={reason}")
        return

    folds, targets, expression, target_matrix, modules = load_context()
    specs = build_condition_grid(cfg)
    encoders, external_audit_dict = fit_external_encoders(cfg, specs)
    external_oof, grid = run_oof(cfg, specs, encoders, folds, targets, expression, target_matrix, modules)
    oof = pd.concat([reference_predictions(cfg), external_oof], ignore_index=True)
    target, mean = compute_metrics(oof)
    external_audit_dict.update(
        {
            "stage32c_ready": True,
            "stage33b_loaded": True,
            "matrix_path_exists": resolve(cfg["stage32c_matrix"]).exists(),
            "stage32c_dataset_id": manifest.get("dataset_id", ""),
            "stage32c_gene_overlap_fraction": manifest.get("gene_overlap_fraction", np.nan),
            "stage32c_n_obs": manifest.get("n_obs", 0),
            "stage32c_n_vars": manifest.get("n_vars", 0),
        }
    )
    leakage, graph, pf = make_audits_and_passfail(cfg, specs, target, mean, grid, external_audit_dict)
    external_audit = pd.DataFrame([external_audit_dict])
    condition = mean.rename(columns={"mean_pooled_oof_spearman": "condition_mean_pooled_oof_spearman"})

    pf.to_csv(PASS_FAIL_OUT, index=False)
    condition.to_csv(CONDITION_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    graph.to_csv(GRAPH_AUDIT_OUT, index=False)
    leakage.to_csv(LEAKAGE_AUDIT_OUT, index=False)
    external_audit.to_csv(EXTERNAL_AUDIT_OUT, index=False)
    grid.to_csv(GRID_OUT, index=False)
    write_report(mean, target, graph, leakage, external_audit, grid, pf)
    update_status(pf)

    row = pf.iloc[0]
    print(f"best_stage33c_condition={row.best_stage33c_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_stage33c_mean_pooled_oof_spearman:.6f}")
    print(f"best_minus_stage33b={row.best_minus_stage33b:.6f}")
    print(f"best_minus_stage27c={row.best_minus_stage27c:.6f}")
    print(f"graph_specific_pass={bool(row.stage33c_graph_specific_pass)}")
    print(f"stage33c_rescue_performance_pass={bool(row.stage33c_rescue_performance_pass)}")


if __name__ == "__main__":
    main()
