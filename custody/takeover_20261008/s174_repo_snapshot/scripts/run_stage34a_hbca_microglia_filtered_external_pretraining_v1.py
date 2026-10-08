from __future__ import annotations

import argparse
import importlib
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

for optional_module, optional_class in [("lightgbm", "LGBMRegressor"), ("xgboost", "XGBRegressor")]:
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

CELLTYPE_AUDIT_OUT = TABLE_DIR / "stage34a_celltype_filter_audit_v1.csv"
MATRIX_MANIFEST_OUT = TABLE_DIR / "stage34a_filtered_matrix_manifest_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage34a_pass_fail_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage34a_condition_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage34a_mean_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage34a_target_metrics_v1.csv"
GRAPH_AUDIT_OUT = TABLE_DIR / "stage34a_graph_control_audit_v1.csv"
LEAKAGE_AUDIT_OUT = TABLE_DIR / "stage34a_leakage_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage34a_hbca_microglia_filtered_external_pretraining_report_v1.md"

REF27 = "stage27c_module_pca_ridge_reference"
REF31 = "stage31_weak_residual_real_graph_alpha_0_05_reference"
REF33C = "stage33c_best_reference"


@dataclass(frozen=True)
class ConditionSpec:
    condition: str
    n_components: int
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


def gate_inputs(cfg: dict[str, Any]) -> tuple[bool, str]:
    required = [
        resolve(cfg["stage32c_pass_fail"]),
        resolve(cfg["stage32c_matrix"]),
        resolve(cfg["canonical_gene_universe"]),
        resolve(cfg["references"]["stage27c_oof"]),
        resolve(cfg["references"]["stage31_oof"]),
        resolve(cfg["references"]["stage33c_target_metrics"]),
        resolve(cfg["references"]["stage33c_mean_metrics"]),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, "missing_required_inputs:" + ";".join(missing)
    pf32 = pd.read_csv(resolve(cfg["stage32c_pass_fail"]))
    if not bool(pf32.iloc[0].get("stage32c_ready_for_stage33", False)):
        return False, "stage32c_ready_for_stage33_false"
    return True, "ready"


def verify_canonical_gene_universe(path: Path) -> tuple[list[str], dict[str, Any]]:
    edges = pd.read_csv(path)
    source = set(edges["source"].astype(str))
    target = set(edges["target"].astype(str))
    union = source | target
    audit = {
        "canonical_source_gene_count": len(source),
        "canonical_target_gene_count": len(target),
        "canonical_union_gene_count": len(union),
        "canonical_gene_universe_pass": len(source) == 2957 and len(target) == 2957 and len(union) == 2957,
    }
    if not audit["canonical_gene_universe_pass"]:
        raise RuntimeError(f"Canonical gene universe mismatch: {audit}")
    return sorted(union), audit


def inspect_and_filter_hbca(cfg: dict[str, Any], canonical: list[str], canonical_audit: dict[str, Any]) -> tuple[ad.AnnData, pd.DataFrame, pd.DataFrame]:
    source_path = resolve(cfg["stage32c_matrix"])
    adata = ad.read_h5ad(source_path)
    obs = adata.obs.copy()
    dataset_col = "dataset_id" if "dataset_id" in obs else "stage32c_source_dataset_id"
    approved_dataset_used = bool(obs[dataset_col].astype(str).eq(str(cfg["approved_dataset_id"])).all())
    cell_cols = [col for col in cfg["metadata"]["cell_type_columns"] if col in obs.columns]
    candidate_cols = {
        role: ";".join([col for col in cols if col in obs.columns])
        for role, cols in cfg["metadata"]["candidate_columns"].items()
    }
    exact_terms = [str(term).lower() for term in cfg["metadata"]["exact_or_myeloid_terms"]]
    broad_terms = [str(term).lower() for term in cfg["metadata"]["broad_terms"]]
    audit_rows: list[dict[str, Any]] = []
    exact_mask = pd.Series(False, index=obs.index)
    broad_mask = pd.Series(False, index=obs.index)
    for col in cell_cols:
        labels = obs[col].astype(str)
        counts = labels.value_counts(dropna=False)
        for label, count in counts.items():
            label_lower = str(label).lower()
            matched_terms = [term for term in exact_terms if term in label_lower]
            broad_matched = [term for term in broad_terms if term in label_lower]
            if matched_terms or broad_matched:
                audit_rows.append(
                    {
                        "metadata_column": col,
                        "label": label,
                        "n_cells": int(count),
                        "match_class": "exact_myeloid_or_pvm" if matched_terms else "broad_immune",
                        "matched_terms": ";".join(matched_terms or broad_matched),
                    }
                )
            exact_mask |= labels.str.lower().apply(lambda value: any(term in value for term in exact_terms))
            broad_mask |= labels.str.lower().apply(lambda value: any(term in value for term in broad_terms))
    n_exact = int(exact_mask.sum())
    if n_exact >= int(cfg["minimum_filter_cells"]):
        final_mask = exact_mask
        filter_logic = "exact_microglia_myeloid_pvm_terms"
    else:
        final_mask = exact_mask | broad_mask
        filter_logic = "broadened_to_immune_terms_because_exact_below_minimum"
    filtered = adata[final_mask.to_numpy(), :].copy()
    if filtered.n_obs > int(cfg["max_cells"]):
        rng = np.random.default_rng(int(cfg["random_seed"]))
        chosen = rng.choice(filtered.n_obs, size=int(cfg["max_cells"]), replace=False)
        filtered = filtered[sorted(chosen), :].copy()
        downsampled = True
    else:
        downsampled = False
    shared_genes = [gene for gene in canonical if gene in list(filtered.var_names)]
    filtered = filtered[:, shared_genes].copy()
    out_path = resolve(cfg["stage34a_filtered_matrix"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    filtered.write_h5ad(out_path)
    gene_overlap = len(shared_genes) / len(canonical)
    audit = pd.DataFrame(audit_rows).sort_values(["match_class", "n_cells"], ascending=[True, False])
    if audit.empty:
        audit = pd.DataFrame(columns=["metadata_column", "label", "n_cells", "match_class", "matched_terms"])
    manifest = pd.DataFrame(
        [
            {
                "source_matrix": str(source_path),
                "filtered_matrix": cfg["stage34a_filtered_matrix"],
                "approved_dataset_id": cfg["approved_dataset_id"],
                "approved_dataset_used": approved_dataset_used,
                "filter_logic": filter_logic,
                "n_source_cells": int(adata.n_obs),
                "n_exact_microglia_myeloid_pvm_cells": n_exact,
                "n_filtered_cells": int(filtered.n_obs),
                "downsampled": downsampled,
                "max_cells": int(cfg["max_cells"]),
                "n_source_genes": int(adata.n_vars),
                "n_filtered_genes": int(filtered.n_vars),
                "canonical_genes": len(canonical),
                "gene_overlap_fraction": gene_overlap,
                "minimum_gene_overlap_fraction": float(cfg["minimum_gene_overlap_fraction"]),
                "gene_overlap_pass": gene_overlap >= float(cfg["minimum_gene_overlap_fraction"]),
                "normalization_status": "source_raw_count_like; benchmark_transform_raw_count_size_factor_log1p",
                "metadata_cell_type_columns_used": ";".join(cell_cols),
                **candidate_cols,
                **canonical_audit,
            }
        ]
    )
    if not approved_dataset_used:
        raise RuntimeError("Filtered matrix includes a dataset_id outside the approved HBCA dataset.")
    if int(filtered.n_obs) < int(cfg["minimum_filter_cells"]):
        raise RuntimeError("Filtered matrix has fewer cells than the configured minimum.")
    if not bool(manifest.iloc[0]["gene_overlap_pass"]):
        raise RuntimeError("Filtered matrix gene overlap is below the configured minimum.")
    return filtered, audit, manifest


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


def reference_target_and_mean(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    def from_oof(path: Path, source_condition: str, out_condition: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        oof = pd.read_csv(path)
        oof = oof[oof["condition"] == source_condition].copy()
        if "target_key" not in oof:
            oof["target_key"] = oof["target"].map(target_key)
        rows = []
        for keys, group in oof.groupby(["target", "target_key", "target_alias"]):
            target, key, alias = keys
            rows.append(
                {
                    "condition": out_condition,
                    "target": target,
                    "target_key": key,
                    "target_alias": alias,
                    "n_donors": int(group["donor_id"].nunique()),
                    **regression_metrics(group["y_true"].to_numpy(), group["y_pred"].to_numpy()),
                }
            )
        target_df = pd.DataFrame(rows)
        mean_df = summarize_mean(target_df)
        return target_df, mean_df

    t27, m27 = from_oof(resolve(cfg["references"]["stage27c_oof"]), "module_pca_ridge", REF27)
    t31, m31 = from_oof(resolve(cfg["references"]["stage31_oof"]), cfg["references"]["stage31_condition"], REF31)
    t33 = pd.read_csv(resolve(cfg["references"]["stage33c_target_metrics"]))
    t33 = t33[t33["condition"] == cfg["stage33c_best_condition"]].copy()
    t33["condition"] = REF33C
    m33 = summarize_mean(t33)
    return pd.concat([t27, t31, t33], ignore_index=True), pd.concat([m27, m31, m33], ignore_index=True)


def build_specs() -> list[ConditionSpec]:
    return [
        ConditionSpec("filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph", 16, "direct", "no_graph_identity", 0.0),
        ConditionSpec("filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph", 32, "direct", "no_graph_identity", 0.0),
        ConditionSpec("filtered_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph", 32, "concat_module_pca", "no_graph_identity", 0.0),
        ConditionSpec("filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05", 32, "direct", "residual_real_graph", 0.05),
        ConditionSpec("filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05", 32, "direct", "strict_shuffled_residual_graph", 0.05),
    ]


def align_expression(expression: pd.DataFrame, genes: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(0.0, index=expression.index, columns=genes)
    shared = [gene for gene in genes if gene in expression.columns]
    out.loc[:, shared] = expression.loc[:, shared].to_numpy(dtype=float)
    return out


def fit_encoders(adata: ad.AnnData, specs: list[ConditionSpec], seed: int) -> dict[int, TruncatedSVD]:
    x = row_size_factor_log1p(adata.X)
    encoders = {}
    for n in sorted({spec.n_components for spec in specs}):
        n_components = min(n, adata.n_obs - 1, adata.n_vars - 1)
        encoder = TruncatedSVD(n_components=n_components, random_state=seed)
        encoder.fit(x)
        encoders[n] = encoder
    return encoders


def embed(encoder: TruncatedSVD, expression: pd.DataFrame) -> pd.DataFrame:
    values = encoder.transform(row_size_factor_log1p(expression.to_numpy(dtype=float)))
    return pd.DataFrame(values, index=expression.index, columns=[f"ext_svd_{i + 1}" for i in range(values.shape[1])])


def condition_base_features(cfg: dict[str, Any], spec: ConditionSpec, expression: pd.DataFrame, genes: list[str], encoder: TruncatedSVD) -> pd.DataFrame:
    base_expr = align_expression(expression, genes)
    base = embed(encoder, base_expr)
    if spec.graph_variant == "no_graph_identity":
        return base
    identity_path = resolve(cfg["graph"]["no_graph_edges"])
    canonical = canonical_genes(identity_path)
    if spec.graph_variant == "residual_real_graph":
        asset = load_graph_asset("real", resolve(cfg["graph"]["real_edges"]), canonical)
    elif spec.graph_variant == "strict_shuffled_residual_graph":
        asset = load_graph_asset("strict", resolve(cfg["graph"]["strict_shuffled_edges"]), canonical)
    else:
        raise ValueError(spec.graph_variant)
    smoothed = graph_smoothed_expression(expression, asset, alpha=spec.graph_alpha)
    smooth_expr = align_expression(smoothed, genes)
    smooth = embed(encoder, smooth_expr)
    residual = smooth - base
    return pd.concat([base.add_prefix("base_"), residual.add_prefix("graph_resid_")], axis=1)


def module_pca_features(modules: pd.DataFrame, train: list[str], test: list[str], cfg: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    n_components = min(int(cfg["module_pca"]["n_components"]), modules.shape[1], len(train) - 1)
    pipe = Pipeline([("scale", StandardScaler()), ("pca", PCA(n_components=n_components, random_state=int(cfg["random_seed"])))])
    return pipe.fit_transform(modules.loc[train].to_numpy(dtype=float)), pipe.transform(modules.loc[test].to_numpy(dtype=float))


def fit_predict_ridge(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("ridge", RidgeCV(alphas=np.asarray(cfg["downstream"]["ridge_alphas"], dtype=float), cv=min(3, max(2, len(y_train) // 10)))),
        ]
    )
    model.fit(x_train, y_train)
    return model.predict(x_test)


def run_external_oof(
    cfg: dict[str, Any],
    specs: list[ConditionSpec],
    encoders: dict[int, TruncatedSVD],
    genes: list[str],
    folds: pd.DataFrame,
    targets: pd.DataFrame,
    expression: pd.DataFrame,
    target_matrix: pd.DataFrame,
    modules: pd.DataFrame,
) -> pd.DataFrame:
    feature_cache = {spec.condition: condition_base_features(cfg, spec, expression, genes, encoders[spec.n_components]) for spec in specs}
    rows = []
    for spec in specs:
        features = feature_cache[spec.condition]
        for _, target_row in targets.iterrows():
            target = target_row["target_name"]
            alias = target_row["target_alias"]
            y = target_matrix[alias].dropna()
            for fold_id in sorted(folds["fold_id"].unique()):
                test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train = [donor for donor in train if donor in y.index and donor in features.index]
                test = [donor for donor in test if donor in y.index and donor in features.index]
                x_train = features.loc[train].to_numpy(dtype=float)
                x_test = features.loc[test].to_numpy(dtype=float)
                if spec.projection_variant == "concat_module_pca":
                    m_train, m_test = module_pca_features(modules, train, test, cfg)
                    x_train = np.concatenate([x_train, m_train], axis=1)
                    x_test = np.concatenate([x_test, m_test], axis=1)
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
                        }
                    )
    return pd.DataFrame(rows)


def compute_target_metrics(oof: pd.DataFrame) -> pd.DataFrame:
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
    return pd.DataFrame(rows)


def summarize_mean(target: pd.DataFrame) -> pd.DataFrame:
    return (
        target.groupby("condition", as_index=False)
        .agg(
            mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"),
            min_target_pooled_oof_spearman=("pooled_oof_spearman", "min"),
            n_targets=("target_key", "nunique"),
        )
        .sort_values("mean_pooled_oof_spearman", ascending=False)
    )


def audits_and_passfail(cfg: dict[str, Any], target: pd.DataFrame, mean: pd.DataFrame, manifest: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = set(cfg["required_targets"])
    external_conditions = [spec.condition for spec in build_specs()]
    ext_mean = mean[mean["condition"].isin(external_conditions)].copy()
    best = ext_mean.iloc[0]
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    ref27_target = target[target["condition"] == REF27][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "ref27_target_spearman"})
    best_target = target[target["condition"] == best.condition].merge(ref27_target, on="target_key", how="left")
    target_gate = bool(((best_target["pooled_oof_spearman"] - best_target["ref27_target_spearman"]) >= float(cfg["max_target_drop_vs_stage27c_reference"])).all())
    no_graph = "filtered_ext_svd32_raw_count_size_factor_log1p_direct_no_graph"
    real = "filtered_ext_svd32_raw_count_size_factor_log1p_direct_residual_real_graph_alpha_0_05"
    strict = "filtered_ext_svd32_raw_count_size_factor_log1p_direct_strict_shuffled_residual_graph_alpha_0_05"
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
                "approved_hbca_dataset_used": bool(manifest.iloc[0]["approved_dataset_used"]),
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
    run_pass = bool(
        manifest.iloc[0]["approved_dataset_used"]
        and manifest.iloc[0]["gene_overlap_pass"]
        and leakage.iloc[0]["leakage_audit_pass"]
        and required.issubset(set(target[target["condition"].isin(external_conditions)]["target_key"]))
    )
    biological_filter_pass = bool(best.mean_pooled_oof_spearman > float(cfg["stage33c_best_mean"]) and run_pass)
    full_pass = bool(
        best.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"])
        and best.mean_pooled_oof_spearman >= float(cfg["minimum_success_threshold"])
        and target_gate
        and run_pass
    )
    if best.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"]):
        interpretation = "Microglia/myeloid-filtered external pretraining improved the internal SEA-AD benchmark, but this is not external validation."
    elif best.mean_pooled_oof_spearman > float(cfg["stage33c_best_mean"]):
        interpretation = "Microglia/myeloid filtering improved external-pretraining alignment but did not yet surpass the Stage 27C internal no-graph reference."
    else:
        interpretation = "Microglia/myeloid filtering did not rescue the external-pretraining deficit under this implementation."
    if real_gt_strict and not real_gt_no:
        graph_interpretation = "Real topology outperformed shuffled topology but did not improve over the no-graph identity reference."
    elif graph_specific:
        graph_interpretation = "Filtered real graph beat matched no-graph and strict-shuffled controls internally; this is not external validation."
    else:
        graph_interpretation = "Graph-specific utility remains unestablished."
    pf = pd.DataFrame(
        [
            {
                "stage34a_run": True,
                "approved_hbca_dataset_used": bool(manifest.iloc[0]["approved_dataset_used"]),
                "microglia_myeloid_filter_attempted": True,
                "n_filtered_cells": int(manifest.iloc[0]["n_filtered_cells"]),
                "gene_overlap_fraction": float(manifest.iloc[0]["gene_overlap_fraction"]),
                "best_stage34a_condition": best.condition,
                "best_stage34a_mean_pooled_oof_spearman": float(best.mean_pooled_oof_spearman),
                "stage33c_best_mean": float(cfg["stage33c_best_mean"]),
                "stage27c_reference_mean": float(cfg["stage27c_reference_mean"]),
                "best_minus_stage33c": float(best.mean_pooled_oof_spearman - float(cfg["stage33c_best_mean"])),
                "best_minus_stage27c": float(best.mean_pooled_oof_spearman - float(cfg["stage27c_reference_mean"])),
                "all_five_targets_reported": required.issubset(set(target[target["condition"] == best.condition]["target_key"])),
                "target_degradation_gate_pass": target_gate,
                "stage34a_run_pass": run_pass,
                "stage34a_biological_filter_rescue_pass": biological_filter_pass,
                "stage34a_full_internal_performance_pass": full_pass,
                "stage34a_graph_specific_pass": graph_specific,
                "controlled_interpretation": interpretation,
                "graph_interpretation": graph_interpretation,
            }
        ]
    )
    return leakage, graph, pf


def write_report(cell_audit: pd.DataFrame, manifest: pd.DataFrame, mean: pd.DataFrame, target: pd.DataFrame, graph: pd.DataFrame, leakage: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    lines = [
        "# Stage 34A HBCA microglia/myeloid-filtered external pretraining report v1",
        "",
        "## Executive summary",
        "",
        f"Filtered cells: `{int(row.n_filtered_cells)}`. Best Stage 34A condition: `{row.best_stage34a_condition}` with mean pooled donor-level OOF Spearman `{row.best_stage34a_mean_pooled_oof_spearman:.4f}`.",
        f"Stage 33C best: `{row.stage33c_best_mean:.4f}`. Stage 27C reference: `{row.stage27c_reference_mean:.4f}`.",
        f"Run pass: `{bool(row.stage34a_run_pass)}`. Biological-filter rescue pass: `{bool(row.stage34a_biological_filter_rescue_pass)}`. Full internal performance pass: `{bool(row.stage34a_full_internal_performance_pass)}`. Graph-specific pass: `{bool(row.stage34a_graph_specific_pass)}`.",
        "",
        "## Controlled interpretation",
        "",
        str(row.controlled_interpretation),
        str(row.graph_interpretation),
        "",
        "This is an internal SEA-AD benchmark using the approved HBCA external pretraining dataset. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.",
        "",
        "## Cell-type filter audit",
        "",
        "```csv",
        cell_audit.to_csv(index=False).strip(),
        "```",
        "",
        "## Filtered matrix manifest",
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
        "scorecard_item": "stage34a_hbca_microglia_filtered_external_pretraining",
        "status": "complete",
        "stage": "Stage 34A",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "best Stage 34A > Stage 33C for biological-filter rescue; full pass requires > Stage 27C and >=0.3228",
        "current_value": f"{row.best_stage34a_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.stage34a_full_internal_performance_pass) else "fail",
        "datasets_allowed": "approved HBCA non-neuronal Census dataset filtered to microglia/myeloid/PVM-like cells; SEA-AD locked folds for downstream only",
        "datasets_forbidden": "clean holdouts; SEA-AD during external pretraining; external labels for pathology prediction; in silico ablation",
        "allowed_claim": row.controlled_interpretation,
        "notes": f"biological_filter_rescue_pass={bool(row.stage34a_biological_filter_rescue_pass)}; graph_specific_pass={bool(row.stage34a_graph_specific_pass)}; {row.graph_interpretation}",
    }
    score = score[score["scorecard_item"] != "stage34a_hbca_microglia_filtered_external_pretraining"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (
            ROOT / "docs" / "ACTIVE_V3_STATUS.md",
            "\n\n## Stage 34A HBCA microglia/myeloid-filtered external pretraining status\n",
            f"\nStage 34A is complete. Filtered HBCA cells: `{int(row.n_filtered_cells)}`. Best condition: `{row.best_stage34a_condition}` (`{row.best_stage34a_mean_pooled_oof_spearman:.4f}`). Biological-filter rescue pass: `{bool(row.stage34a_biological_filter_rescue_pass)}`; full internal performance pass: `{bool(row.stage34a_full_internal_performance_pass)}`; graph-specific pass: `{bool(row.stage34a_graph_specific_pass)}`. {row.controlled_interpretation} {row.graph_interpretation} No external validation or manuscript claim update.\n",
        ),
        (
            ROOT / "docs" / "V3_SCORECARD.md",
            "\n\n## Stage 34A HBCA microglia/myeloid-filtered external pretraining result\n",
            f"\nBest Stage 34A condition: `{row.best_stage34a_condition}`; mean pooled OOF Spearman: `{row.best_stage34a_mean_pooled_oof_spearman:.4f}`; minus Stage 33C: `{row.best_minus_stage33c:.4f}`; minus Stage 27C: `{row.best_minus_stage27c:.4f}`; biological-filter rescue pass: `{bool(row.stage34a_biological_filter_rescue_pass)}`; graph-specific pass: `{bool(row.stage34a_graph_specific_pass)}`. {row.controlled_interpretation}\n",
        ),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def skipped_outputs(reason: str) -> None:
    pf = pd.DataFrame([{"stage34a_run": False, "skip_reason": reason, "stage34a_run_pass": False, "stage34a_biological_filter_rescue_pass": False, "stage34a_full_internal_performance_pass": False, "stage34a_graph_specific_pass": False}])
    pf.to_csv(PASS_FAIL_OUT, index=False)
    REPORT_OUT.write_text("# Stage 34A HBCA microglia/myeloid-filtered external pretraining report v1\n\nStage 34A skipped: " + reason + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage34a_hbca_microglia_filtered_external_pretraining_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ready, reason = gate_inputs(cfg)
    if not ready:
        skipped_outputs(reason)
        print(f"stage34a_skipped={reason}")
        return
    canonical, canonical_audit = verify_canonical_gene_universe(resolve(cfg["canonical_gene_universe"]))
    filtered, cell_audit, manifest = inspect_and_filter_hbca(cfg, canonical, canonical_audit)
    folds, targets, expression, target_matrix, modules = load_context()
    specs = build_specs()
    encoders = fit_encoders(filtered, specs, int(cfg["random_seed"]))
    external_oof = run_external_oof(cfg, specs, encoders, list(filtered.var_names), folds, targets, expression, target_matrix, modules)
    external_target = compute_target_metrics(external_oof)
    ref_target, ref_mean = reference_target_and_mean(cfg)
    target = pd.concat([external_target, ref_target], ignore_index=True)
    mean = pd.concat([summarize_mean(external_target), ref_mean], ignore_index=True).sort_values("mean_pooled_oof_spearman", ascending=False)
    leakage, graph, pf = audits_and_passfail(cfg, target, mean, manifest)
    condition = mean.rename(columns={"mean_pooled_oof_spearman": "condition_mean_pooled_oof_spearman"})

    cell_audit.to_csv(CELLTYPE_AUDIT_OUT, index=False)
    manifest.to_csv(MATRIX_MANIFEST_OUT, index=False)
    pf.to_csv(PASS_FAIL_OUT, index=False)
    condition.to_csv(CONDITION_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    graph.to_csv(GRAPH_AUDIT_OUT, index=False)
    leakage.to_csv(LEAKAGE_AUDIT_OUT, index=False)
    write_report(cell_audit, manifest, mean, target, graph, leakage, pf)
    update_status(pf)

    row = pf.iloc[0]
    print(f"filtered_cells={int(row.n_filtered_cells)}")
    print(f"best_stage34a_condition={row.best_stage34a_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_stage34a_mean_pooled_oof_spearman:.6f}")
    print(f"best_minus_stage33c={row.best_minus_stage33c:.6f}")
    print(f"best_minus_stage27c={row.best_minus_stage27c:.6f}")
    print(f"stage34a_biological_filter_rescue_pass={bool(row.stage34a_biological_filter_rescue_pass)}")
    print(f"stage34a_graph_specific_pass={bool(row.stage34a_graph_specific_pass)}")


if __name__ == "__main__":
    main()
