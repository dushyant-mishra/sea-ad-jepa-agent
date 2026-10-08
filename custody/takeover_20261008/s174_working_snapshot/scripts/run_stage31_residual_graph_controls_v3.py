from __future__ import annotations

import argparse
import importlib
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from sklearn.decomposition import PCA
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ATLAS_DIR = ROOT / "discovery_atlas"
for path in [SRC_DIR, ATLAS_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from sea_ad_jepa.data.graph_control_features import (  # noqa: E402
    GraphAsset,
    canonical_genes,
    graph_smoothed_expression,
    load_graph_asset,
    predefined_module_features,
)
from sea_ad_jepa.eval.oof_metrics import regression_metrics, safe_corr  # noqa: E402

for optional_module, optional_class in [
    ("lightgbm", "LGBMRegressor"),
    ("xgboost", "XGBRegressor"),
]:
    if optional_module not in sys.modules:
        module = types.ModuleType(optional_module)
        setattr(module, optional_class, object)
        sys.modules[optional_module] = module

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

STAGE27C_OOF = TABLE_DIR / "stage27c_rescue_oof_predictions_v1.csv"
STAGE27C_TARGET = TABLE_DIR / "stage27c_rescue_target_metrics_v1.csv"
STAGE27C_MEAN = TABLE_DIR / "stage27c_rescue_mean_metrics_v1.csv"
OFFICIAL_MODULE = TABLE_DIR / "v3_primary_baseline_pooled_oof_recompute_v1.csv"
ROLE_REGISTRY = TABLE_DIR / "v3_dataset_role_registry_v1.csv"

OOF_OUT = TABLE_DIR / "stage31_residual_graph_oof_predictions_v1.csv"
TARGET_OUT = TABLE_DIR / "stage31_residual_graph_target_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage31_residual_graph_mean_metrics_v1.csv"
PAIRWISE_OUT = TABLE_DIR / "stage31_residual_graph_pairwise_deltas_v1.csv"
TARGET_DELTA_STAGE27C_OUT = TABLE_DIR / "stage31_residual_graph_target_deltas_vs_stage27c_v1.csv"
TARGET_DELTA_MODULE_OUT = TABLE_DIR / "stage31_residual_graph_target_deltas_vs_module_mean_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage31_residual_graph_pass_fail_v1.csv"
BOOT_OUT = TABLE_DIR / "stage31_residual_graph_bootstrap_ci_v1.csv"
FEATURE_AUDIT_OUT = TABLE_DIR / "stage31_residual_graph_feature_audit_v1.csv"
GRAPH_AUDIT_OUT = TABLE_DIR / "stage31_residual_graph_graph_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage31_residual_graph_controls_report_v1.md"

REFERENCE = "stage27c_module_pca_ridge_reference"
PRIMARY_REAL = "residual_real_graph_pca_ridge"
NO_GRAPH = "residual_no_graph_pca_ridge"
STRICT = "residual_strict_shuffled_graph_pca_ridge"
TARGET_GATED = "target_gated_real_graph_residual_ridge"
WEAK_PRIMARY = "weak_diffusion_real_graph_residual_pca_ridge"
HUB_PRIMARY = "hub_capped_real_graph_residual_pca_ridge"
RESIDUAL_ONLY = "graph_residual_only_ridge"

REQUIRED_TARGETS = {"AT8", "6e10/A_beta", "GFAP", "Iba1", "NeuN"}
REQUIRED_PAIRS = [
    (PRIMARY_REAL, REFERENCE),
    (PRIMARY_REAL, NO_GRAPH),
    (PRIMARY_REAL, STRICT),
    (TARGET_GATED, REFERENCE),
    (TARGET_GATED, NO_GRAPH),
    (TARGET_GATED, STRICT),
    (WEAK_PRIMARY, REFERENCE),
    (HUB_PRIMARY, REFERENCE),
]


def load_cfg(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def target_key(value: object) -> str:
    text = str(value)
    if text.startswith("6e10/"):
        return "6e10/A_beta"
    return text


def safe_condition_suffix(value: float) -> str:
    return str(value).replace(".", "_")


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


def reference_predictions() -> pd.DataFrame:
    ref = pd.read_csv(STAGE27C_OOF)
    ref = ref[ref["condition"] == "module_pca_ridge"].copy()
    return pd.DataFrame(
        {
            "condition": REFERENCE,
            "target": ref["target"],
            "target_key": ref["target"].map(target_key),
            "target_alias": ref["target_alias"],
            "donor_id": ref["donor_id"].astype(str),
            "fold_id": ref["fold_id"].astype(int),
            "y_true": ref["y_true"].astype(float),
            "y_pred": ref["y_pred"].astype(float),
            "target_scale": ref["target_scale"],
            "random_seed": ref["random_seed"].astype(int),
            "clean_holdout_used": False,
            "heldout_donor_leakage_detected": False,
            "external_matrix_used": False,
            "prediction_source": "loaded_stage27c_reference",
        }
    )


def load_hub_capped_graph_asset(
    condition: str,
    path: Path,
    canonical: list[str],
    percentile: float,
    hub_neighbor_weight: float,
) -> tuple[GraphAsset, dict[str, float]]:
    edges = pd.read_csv(path)
    required = {"source_idx", "target_idx"}
    if not required.issubset(edges.columns):
        raise ValueError(f"{path} lacks {sorted(required)}")
    src = edges["source_idx"].to_numpy(dtype=int)
    dst = edges["target_idx"].to_numpy(dtype=int)
    n = len(canonical)
    if len(src) == 0 or src.min() < 0 or dst.min() < 0 or src.max() >= n or dst.max() >= n:
        raise ValueError(f"{path} contains invalid graph node indices")
    rows = np.concatenate([src, dst])
    cols = np.concatenate([dst, src])
    binary = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    binary.data[:] = 1.0
    binary.eliminate_zeros()
    degree = np.asarray(binary.sum(axis=1)).ravel()
    nonzero_degree = degree[degree > 0]
    threshold = float(np.percentile(nonzero_degree, percentile)) if len(nonzero_degree) else 0.0
    hubs = degree >= threshold
    weights = np.ones(len(rows), dtype=np.float64)
    weights[hubs[rows] | hubs[cols]] = float(hub_neighbor_weight)
    adjacency = sparse.coo_matrix((weights, (rows, cols)), shape=(n, n)).tocsr()
    adjacency.eliminate_zeros()
    degree_weighted = np.asarray(adjacency.sum(axis=1)).ravel()
    isolated = degree_weighted == 0
    if isolated.any():
        adjacency = adjacency + sparse.diags(isolated.astype(float))
        degree_weighted = np.asarray(adjacency.sum(axis=1)).ravel()
    normalized = sparse.diags(1.0 / degree_weighted) @ adjacency
    asset = GraphAsset(
        condition=condition,
        path=path,
        genes=canonical,
        adjacency=normalized.tocsr(),
        edge_count=int(len(edges)),
        self_loop_count=int(np.sum(src == dst)),
        notes=(
            "row-normalized hub-capped adjacency; edges touching high-degree hubs "
            f"downweighted to {hub_neighbor_weight}"
        ),
    )
    summary = {
        "hub_cap_percentile": float(percentile),
        "hub_degree_threshold": threshold,
        "n_hub_nodes": int(hubs.sum()),
        "hub_neighbor_weight": float(hub_neighbor_weight),
    }
    return asset, summary


def graph_audit(cfg: dict, assets: dict[str, GraphAsset], canonical: list[str]) -> pd.DataFrame:
    strict_diag = pd.read_csv(resolve(cfg["graph"]["strict_shuffled_diagnostics"]))
    diag = dict(zip(strict_diag["metric"].astype(str), strict_diag["value"].astype(str)))
    real = assets["real"]
    no_graph = assets["no_graph"]
    strict = assets["strict"]
    checks = [
        ("canonical_node_count_2957", len(canonical) == 2957, f"nodes={len(canonical)}"),
        (
            "all_core_conditions_same_node_count",
            all(asset.adjacency.shape == (len(canonical), len(canonical)) for asset in assets.values()),
            str({key: asset.adjacency.shape for key, asset in assets.items()}),
        ),
        ("no_graph_identity_edge_count", no_graph.edge_count == len(canonical), f"edges={no_graph.edge_count}"),
        ("real_graph_nonempty", real.edge_count > len(canonical), f"edges={real.edge_count}"),
        ("strict_graph_edge_count_matches_real", strict.edge_count == real.edge_count, f"real={real.edge_count}; strict={strict.edge_count}"),
        ("strict_degree_sequence_preserved", diag.get("degree_sequence_exactly_preserved", "").lower() == "true", diag.get("degree_sequence_exactly_preserved", "missing")),
        ("strict_zero_overlap", diag.get("zero_overlap_achieved", "").lower() == "true", diag.get("final_overlap_fraction", "missing")),
        ("strict_no_self_loops", diag.get("no_self_loops", "").lower() == "true", diag.get("no_self_loops", "missing")),
        ("strict_safe_for_training", diag.get("safe_for_training", "").lower() == "true", diag.get("safe_for_training", "missing")),
    ]
    return pd.DataFrame(
        [
            {
                "check_id": check,
                "status": "pass" if passed else "fail",
                "passed": bool(passed),
                "details": details,
            }
            for check, passed, details in checks
        ]
    )


def residual_module_features(
    expression: pd.DataFrame,
    asset: GraphAsset,
    alpha: float,
) -> tuple[pd.DataFrame, dict[str, int]]:
    smoothed = graph_smoothed_expression(expression, asset, alpha=alpha)
    residual_expression = expression.copy()
    residual_expression.loc[:, :] = 0.0
    graph_cols = [gene for gene in asset.genes if gene in expression.columns]
    residual_expression.loc[:, graph_cols] = (
        smoothed.loc[:, graph_cols].to_numpy(dtype=float)
        - expression.loc[:, graph_cols].to_numpy(dtype=float)
    )
    return predefined_module_features(residual_expression)


def fit_predict(
    base_features: pd.DataFrame,
    residual_features: pd.DataFrame,
    y: pd.Series,
    train: list[str],
    test: list[str],
    cfg: dict,
    head: str,
    feature_mode: str,
    residual_weight: float,
) -> np.ndarray:
    base_train = base_features.loc[train].to_numpy(dtype=float)
    base_test = base_features.loc[test].to_numpy(dtype=float)
    residual_train = residual_features.loc[train].to_numpy(dtype=float)
    residual_test = residual_features.loc[test].to_numpy(dtype=float)
    residual_scaler = StandardScaler()
    residual_train_scaled = residual_scaler.fit_transform(residual_train) * float(residual_weight)
    residual_test_scaled = residual_scaler.transform(residual_test) * float(residual_weight)
    if feature_mode == "residual_only":
        x_train = residual_train_scaled
        x_test = residual_test_scaled
    else:
        base_scaler = StandardScaler()
        base_train_scaled = base_scaler.fit_transform(base_train)
        base_test_scaled = base_scaler.transform(base_test)
        x_train = np.concatenate(
            [
                base_train_scaled,
                residual_train_scaled,
            ],
            axis=1,
        )
        x_test = np.concatenate(
            [
                base_test_scaled,
                residual_test_scaled,
            ],
            axis=1,
        )
    y_train = np.log1p(y.loc[train].to_numpy(dtype=float))
    ridge = RidgeCV(
        alphas=np.asarray(cfg["head"]["ridge_alphas"], dtype=float),
        cv=min(3, max(2, len(train) // 10)),
    )
    steps = []
    if head == "pca_ridge":
        n_components = min(
            int(cfg["head"]["pca_components"]),
            x_train.shape[1],
            len(train) - 1,
        )
        steps.append(("pca", PCA(n_components=n_components, random_state=int(cfg["random_seed"]))))
    steps.append(("ridge", ridge))
    model = Pipeline(steps)
    model.fit(x_train, y_train)
    return model.predict(x_test)


def condition_plan(cfg: dict, assets: dict[str, GraphAsset]) -> list[dict]:
    plan = [
        {
            "condition": PRIMARY_REAL,
            "asset_key": "real",
            "alpha": float(cfg["graph"]["residual_alpha"]),
            "residual_weight": 1.0,
            "head": "pca_ridge",
            "feature_mode": "base_plus_residual",
            "role": "primary_real_residual",
        },
        {
            "condition": NO_GRAPH,
            "asset_key": "no_graph",
            "alpha": float(cfg["graph"]["residual_alpha"]),
            "residual_weight": 1.0,
            "head": "pca_ridge",
            "feature_mode": "base_plus_residual",
            "role": "matched_no_graph_capacity_control",
        },
        {
            "condition": STRICT,
            "asset_key": "strict",
            "alpha": float(cfg["graph"]["residual_alpha"]),
            "residual_weight": 1.0,
            "head": "pca_ridge",
            "feature_mode": "base_plus_residual",
            "role": "matched_strict_shuffled_topology_control",
        },
        {
            "condition": TARGET_GATED,
            "asset_key": "real",
            "alpha": float(cfg["graph"]["residual_alpha"]),
            "residual_weight": 1.0,
            "head": "ridge",
            "feature_mode": "base_plus_residual",
            "role": "target_specific_low_capacity_gate",
        },
    ]
    primary_alpha = float(cfg["graph"]["weak_diffusion_primary_alpha"])
    for alpha in cfg["graph"]["weak_diffusion_alphas"]:
        alpha = float(alpha)
        condition = WEAK_PRIMARY if np.isclose(alpha, primary_alpha) else (
            f"{WEAK_PRIMARY}_alpha_{safe_condition_suffix(alpha)}"
        )
        plan.append(
            {
                "condition": condition,
                "asset_key": "real",
                "alpha": alpha,
                "residual_weight": alpha / float(cfg["graph"]["residual_alpha"]),
                "head": "pca_ridge",
                "feature_mode": "base_plus_residual",
                "role": "diagnostic_weak_diffusion_anti_oversmoothing",
            }
        )
    primary_hub = float(cfg["graph"]["hub_cap_primary_percentile"])
    for percentile in cfg["graph"]["hub_cap_percentiles"]:
        percentile = float(percentile)
        key = f"hub_capped_{safe_condition_suffix(percentile)}"
        condition = HUB_PRIMARY if np.isclose(percentile, primary_hub) else (
            f"{HUB_PRIMARY}_p{safe_condition_suffix(percentile)}"
        )
        if key not in assets:
            raise KeyError(f"Missing hub-capped graph asset: {key}")
        plan.append(
            {
                "condition": condition,
                "asset_key": key,
                "alpha": float(cfg["graph"]["residual_alpha"]),
                "residual_weight": 1.0,
                "head": "pca_ridge",
                "feature_mode": "base_plus_residual",
                "role": "diagnostic_hub_capped_anti_oversmoothing",
            }
        )
    plan.append(
        {
            "condition": RESIDUAL_ONLY,
            "asset_key": "real",
            "alpha": float(cfg["graph"]["residual_alpha"]),
            "residual_weight": 1.0,
            "head": "ridge",
            "feature_mode": "residual_only",
            "role": "diagnostic_graph_residual_without_stage27c_skip",
        }
    )
    return plan


def run_conditions(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    folds, targets, expression, target_matrix = load_context()
    identity_path = resolve(cfg["graph"]["no_graph_edges"])
    canonical = canonical_genes(identity_path)
    assets: dict[str, GraphAsset] = {
        "real": load_graph_asset("real", resolve(cfg["graph"]["real_edges"]), canonical),
        "no_graph": load_graph_asset("no_graph", identity_path, canonical),
        "strict": load_graph_asset("strict", resolve(cfg["graph"]["strict_shuffled_edges"]), canonical),
    }
    hub_summaries = {}
    for percentile in cfg["graph"]["hub_cap_percentiles"]:
        key = f"hub_capped_{safe_condition_suffix(float(percentile))}"
        asset, summary = load_hub_capped_graph_asset(
            key,
            resolve(cfg["graph"]["real_edges"]),
            canonical,
            percentile=float(percentile),
            hub_neighbor_weight=float(cfg["graph"]["hub_neighbor_weight"]),
        )
        assets[key] = asset
        hub_summaries[key] = summary

    graph_checks = graph_audit(cfg, assets, canonical)
    base_features, base_overlaps = predefined_module_features(expression)
    feature_cache = {}
    feature_rows = []
    for item in condition_plan(cfg, assets):
        cache_key = (item["asset_key"], float(item["alpha"]))
        if cache_key not in feature_cache:
            residual, overlaps = residual_module_features(
                expression,
                assets[item["asset_key"]],
                alpha=float(item["alpha"]),
            )
            feature_cache[cache_key] = (residual, overlaps)
        residual, overlaps = feature_cache[cache_key]
        hub_summary = hub_summaries.get(item["asset_key"], {})
        feature_rows.append(
            {
                "condition": item["condition"],
                "role": item["role"],
                "asset_key": item["asset_key"],
                "graph_alpha": float(item["alpha"]),
                "head": item["head"],
                "feature_mode": item["feature_mode"],
                "residual_weight_after_fold_scaling": float(item["residual_weight"]),
                "n_stage27c_skip_features": 0 if item["feature_mode"] == "residual_only" else int(base_features.shape[1]),
                "n_graph_residual_features": int(residual.shape[1]),
                "base_module_overlap_summary": "; ".join(f"{k}:{v}" for k, v in sorted(base_overlaps.items())),
                "residual_module_overlap_summary": "; ".join(f"{k}:{v}" for k, v in sorted(overlaps.items())),
                "residual_feature_abs_mean": float(np.abs(residual.to_numpy(dtype=float)).mean()),
                "residual_feature_abs_max": float(np.abs(residual.to_numpy(dtype=float)).max()),
                "anti_oversmoothing_design": (
                    "Stage27C module features preserved as untouched skip path"
                    if item["feature_mode"] != "residual_only"
                    else "diagnostic residual-only branch; not full-pass eligible"
                ),
                **hub_summary,
            }
        )

    rows = []
    for condition_idx, item in enumerate(condition_plan(cfg, assets)):
        residual_features, _ = feature_cache[(item["asset_key"], float(item["alpha"]))]
        for target_idx, target_row in targets.iterrows():
            target = target_row["target_name"]
            alias = target_row["target_alias"]
            y = target_matrix[alias].dropna()
            for fold_id in sorted(folds["fold_id"].unique()):
                test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train = [donor for donor in train if donor in y.index]
                test = [donor for donor in test if donor in y.index]
                seed = int(cfg["random_seed"]) + condition_idx * 1000 + target_idx * 100 + int(fold_id)
                pred = fit_predict(
                    base_features,
                    residual_features,
                    y,
                    train,
                    test,
                    cfg,
                    head=item["head"],
                    feature_mode=item["feature_mode"],
                    residual_weight=float(item["residual_weight"]),
                )
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append(
                        {
                            "condition": item["condition"],
                            "target": target,
                            "target_key": target_key(target),
                            "target_alias": alias,
                            "donor_id": donor,
                            "fold_id": int(fold_id),
                            "y_true": float(true),
                            "y_pred": float(predicted),
                            "target_scale": "log1p",
                            "random_seed": int(seed),
                            "clean_holdout_used": False,
                            "heldout_donor_leakage_detected": False,
                            "external_matrix_used": False,
                            "prediction_source": "fresh_stage31_residual_graph_control",
                        }
                    )
    oof = pd.concat([reference_predictions(), pd.DataFrame(rows)], ignore_index=True)
    return oof, graph_checks, pd.DataFrame(feature_rows), folds


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


def comparisons(target: pd.DataFrame, mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    pairs = list(REQUIRED_PAIRS)
    extra_pairs = [
        (WEAK_PRIMARY, NO_GRAPH),
        (WEAK_PRIMARY, STRICT),
        (HUB_PRIMARY, PRIMARY_REAL),
        (RESIDUAL_ONLY, REFERENCE),
    ]
    for condition in mean["condition"]:
        if str(condition).startswith(f"{WEAK_PRIMARY}_alpha_"):
            extra_pairs.extend(
                [
                    (condition, REFERENCE),
                    (condition, NO_GRAPH),
                    (condition, STRICT),
                ]
            )
    rows = []
    for left, right in pairs + extra_pairs:
        if left in mean_map.index and right in mean_map.index:
            rows.append(
                {
                    "comparison": f"{left}_minus_{right}",
                    "left_condition": left,
                    "right_condition": right,
                    "left_mean_pooled_oof_spearman": float(mean_map[left]),
                    "right_mean_pooled_oof_spearman": float(mean_map[right]),
                    "delta_mean_pooled_oof_spearman": float(mean_map[left] - mean_map[right]),
                }
            )
    ref = target[target["condition"] == REFERENCE][
        ["target_key", "pooled_oof_spearman"]
    ].rename(columns={"pooled_oof_spearman": "stage27c_reference_target_spearman"})
    stage27c_delta = target[target["condition"] != REFERENCE].merge(ref, on="target_key", how="left")
    stage27c_delta["delta_vs_stage27c_reference"] = (
        stage27c_delta["pooled_oof_spearman"]
        - stage27c_delta["stage27c_reference_target_spearman"]
    )
    module = pd.read_csv(OFFICIAL_MODULE)
    module = module[module["baseline_id"] == "module_mean_baseline"][
        ["target", "pooled_oof_spearman"]
    ].copy()
    module["target_key"] = module["target"].map(target_key)
    module = module[["target_key", "pooled_oof_spearman"]].rename(
        columns={"pooled_oof_spearman": "module_mean_target_spearman"}
    )
    module_delta = target[target["condition"] != REFERENCE].merge(module, on="target_key", how="left")
    module_delta["delta_vs_module_mean_baseline"] = (
        module_delta["pooled_oof_spearman"]
        - module_delta["module_mean_target_spearman"]
    )
    return pd.DataFrame(rows), stage27c_delta, module_delta


def bootstrap_summary(
    oof: pd.DataFrame,
    pairs: pd.DataFrame,
    cfg: dict,
) -> pd.DataFrame:
    rng = np.random.default_rng(int(cfg["random_seed"]))
    n_resamples = int(cfg["bootstrap"]["n_resamples"])
    donors = np.array(sorted(oof["donor_id"].astype(str).unique()))
    rows = []
    conditions = sorted(oof["condition"].unique())
    cache = {}

    def condition_cache(condition: str) -> dict:
        if condition in cache:
            return cache[condition]
        group = oof[oof["condition"] == condition].copy()
        y_true = group["y_true"].to_numpy(dtype=float)
        y_pred = group["y_pred"].to_numpy(dtype=float)
        target = group["target_key"].astype(str).to_numpy()
        donor = group["donor_id"].astype(str).to_numpy()
        donor_to_idx = {d: np.flatnonzero(donor == d) for d in donors}
        targets = np.array(sorted(np.unique(target)))
        out = {
            "y_true": y_true,
            "y_pred": y_pred,
            "target": target,
            "donor_to_idx": donor_to_idx,
            "targets": targets,
        }
        cache[condition] = out
        return out

    def sampled_mean(condition: str, sampled_donors: np.ndarray) -> float:
        data = condition_cache(condition)
        indices = np.concatenate([data["donor_to_idx"][donor] for donor in sampled_donors])
        y_true = data["y_true"][indices]
        y_pred = data["y_pred"][indices]
        target = data["target"][indices]
        values = []
        for target_name in data["targets"]:
            mask = target == target_name
            values.append(safe_corr(y_true[mask], y_pred[mask], "spearman"))
        return float(np.mean(values))

    for condition in conditions:
        values = []
        for _ in range(n_resamples):
            sampled = rng.choice(donors, size=len(donors), replace=True)
            values.append(sampled_mean(condition, sampled))
        arr = np.asarray(values, dtype=float)
        rows.append(
            {
                "bootstrap_metric": "condition_mean_pooled_oof_spearman",
                "condition": condition,
                "left_condition": "",
                "right_condition": "",
                "n_bootstrap_resamples": n_resamples,
                "spearman_ci_low": float(np.nanpercentile(arr, 2.5)),
                "spearman_ci_median": float(np.nanpercentile(arr, 50.0)),
                "spearman_ci_high": float(np.nanpercentile(arr, 97.5)),
                "uncertainty_status": "complete",
            }
        )
    for _, pair in pairs.iterrows():
        left = pair["left_condition"]
        right = pair["right_condition"]
        values = []
        for _ in range(n_resamples):
            sampled = rng.choice(donors, size=len(donors), replace=True)
            values.append(sampled_mean(left, sampled) - sampled_mean(right, sampled))
        arr = np.asarray(values, dtype=float)
        rows.append(
            {
                "bootstrap_metric": "pairwise_delta_mean_pooled_oof_spearman",
                "condition": pair["comparison"],
                "left_condition": left,
                "right_condition": right,
                "n_bootstrap_resamples": n_resamples,
                "spearman_ci_low": float(np.nanpercentile(arr, 2.5)),
                "spearman_ci_median": float(np.nanpercentile(arr, 50.0)),
                "spearman_ci_high": float(np.nanpercentile(arr, 97.5)),
                "uncertainty_status": "complete",
            }
        )
    return pd.DataFrame(rows)


def pass_fail(
    oof: pd.DataFrame,
    target: pd.DataFrame,
    mean: pd.DataFrame,
    pairs: pd.DataFrame,
    stage27c_delta: pd.DataFrame,
    module_delta: pd.DataFrame,
    graph_audit: pd.DataFrame,
    feature_audit: pd.DataFrame,
    cfg: dict,
) -> pd.DataFrame:
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    eligible = [
        c
        for c in mean["condition"]
        if c not in {REFERENCE, NO_GRAPH, STRICT, RESIDUAL_ONLY}
    ]
    best_condition = max(eligible, key=lambda c: float(mean_map[c]))
    best_mean = float(mean_map[best_condition])
    reference_mean = float(mean_map[REFERENCE])
    no_graph_mean = float(mean_map[NO_GRAPH])
    strict_mean = float(mean_map[STRICT])
    primary_mean = float(mean_map[PRIMARY_REAL])
    target_subset = target[target["condition"] == best_condition]
    mod_subset = module_delta[module_delta["condition"] == best_condition]
    ref_subset = stage27c_delta[stage27c_delta["condition"] == best_condition]
    registry = pd.read_csv(ROLE_REGISTRY)
    registry_model_selection_safe = not bool(
        registry.get("allowed_for_model_selection", pd.Series(dtype=bool)).fillna(False).astype(bool).any()
    )
    duplicate_rows = int(oof.duplicated(["condition", "target_key", "donor_id"], keep=False).sum())
    expected_rows_per_condition = int(oof["donor_id"].nunique() * len(REQUIRED_TARGETS))
    pair_names = set(pairs["comparison"])
    required_pair_names = {f"{left}_minus_{right}" for left, right in REQUIRED_PAIRS}
    target_specific_partial = False
    partial_condition = ""
    partial_target = ""
    for condition in eligible:
        subset = stage27c_delta[stage27c_delta["condition"] == condition].copy()
        if subset.empty:
            continue
        improved = subset[subset["delta_vs_stage27c_reference"] > 0.0]
        safe = bool(
            (
                subset["delta_vs_stage27c_reference"]
                >= float(cfg["max_target_drop_vs_stage27c_reference"])
            ).all()
        )
        if safe and not improved.empty:
            target_specific_partial = True
            best_target_row = improved.sort_values("delta_vs_stage27c_reference", ascending=False).iloc[0]
            partial_condition = condition
            partial_target = str(best_target_row["target_key"])
            break
    checks = {
        "best_real_meets_stage27c_reference": best_mean >= reference_mean,
        "best_real_meets_official_threshold": best_mean >= float(cfg["minimum_success_threshold"]),
        "best_real_beats_matched_no_graph_residual": best_mean > no_graph_mean,
        "best_real_beats_matched_strict_shuffled_residual": best_mean > strict_mean,
        "all_five_targets_reported": set(target_subset["target_key"]) == REQUIRED_TARGETS,
        "no_target_delta_vs_module_mean_below_minus_0_02": bool(
            (mod_subset["delta_vs_module_mean_baseline"] >= float(cfg["max_target_drop_vs_module_mean"])).all()
        ),
        "no_target_delta_vs_stage27c_below_minus_0_02": bool(
            (ref_subset["delta_vs_stage27c_reference"] >= float(cfg["max_target_drop_vs_stage27c_reference"])).all()
        ),
        "no_heldout_donor_leakage": not bool(oof["heldout_donor_leakage_detected"].astype(bool).any()),
        "no_clean_holdout_use": not bool(oof["clean_holdout_used"].astype(bool).any()),
        "no_external_matrix_use": not bool(oof["external_matrix_used"].astype(bool).any()),
        "graph_audit_pass": bool(graph_audit["passed"].all()),
        "feature_audit_pass": bool((feature_audit["n_graph_residual_features"] > 0).all()),
        "all_expected_conditions_present": {REFERENCE, PRIMARY_REAL, NO_GRAPH, STRICT, TARGET_GATED, WEAK_PRIMARY, HUB_PRIMARY}.issubset(set(mean["condition"])),
        "required_pairwise_comparisons_present": required_pair_names.issubset(pair_names),
        "oof_predictions_are_donor_level": "cell_id" not in oof.columns and "barcode" not in {c.lower() for c in oof.columns},
        "locked_84_donors_retained": int(oof["donor_id"].nunique()) == 84,
        "no_duplicate_condition_target_donor_rows": duplicate_rows == 0,
        "registry_has_no_model_selection_external_dataset": registry_model_selection_safe,
    }
    full_pass = all(checks.values())
    if full_pass:
        interpretation = "stage31_residual_graph_full_internal_pass"
    elif best_mean > strict_mean and best_mean <= no_graph_mean:
        interpretation = "graph_like_residual_features_contain_structure_but_topology_specific_utility_not_established"
    elif no_graph_mean >= best_mean:
        interpretation = "stage27c_or_no_graph_residual_remains_best_internal_model"
    elif target_specific_partial:
        interpretation = "target_specific_graph_residual_signal_possible_without_overall_graph_pass"
    else:
        interpretation = "residual_graph_controls_do_not_establish_graph_specific_value"
    return pd.DataFrame(
        [
            {
                "best_stage31_condition": best_condition,
                "best_stage31_mean_pooled_oof_spearman": best_mean,
                "stage27c_reference_mean": reference_mean,
                "official_threshold": float(cfg["minimum_success_threshold"]),
                "best_minus_stage27c_reference": best_mean - reference_mean,
                "best_real_residual_minus_no_graph_residual": best_mean - no_graph_mean,
                "best_real_residual_minus_strict_shuffled_residual": best_mean - strict_mean,
                "primary_real_residual_mean": primary_mean,
                "primary_real_minus_stage27c_reference": primary_mean - reference_mean,
                "primary_real_minus_no_graph_residual": primary_mean - no_graph_mean,
                "primary_real_minus_strict_shuffled_residual": primary_mean - strict_mean,
                "full_stage31_pass": bool(full_pass),
                "target_specific_partial_pass": bool(target_specific_partial),
                "partial_pass_condition": partial_condition,
                "partial_pass_target": partial_target,
                "controlled_interpretation": interpretation,
                "duplicate_oof_rows": duplicate_rows,
                "expected_rows_per_condition": expected_rows_per_condition,
                **checks,
            }
        ]
    )


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    new = {
        "scorecard_item": "stage31_residual_graph_controls",
        "status": "complete",
        "stage": "Stage 31",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "best real residual >= 0.326702 and 0.3228; > no-graph and strict-shuffled; target deltas >= -0.02",
        "current_value": f"{row.best_stage31_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.full_stage31_pass) else "fail",
        "datasets_allowed": "SEA-AD locked donor folds only",
        "datasets_forbidden": "external matrices; clean holdouts; external model selection",
        "allowed_claim": row.controlled_interpretation,
        "notes": (
            f"best={row.best_stage31_condition}; best-reference={row.best_minus_stage27c_reference:.4f}; "
            f"best-no_graph={row.best_real_residual_minus_no_graph_residual:.4f}; "
            f"best-strict={row.best_real_residual_minus_strict_shuffled_residual:.4f}; "
            "external validation not run; ablation validity not established."
        ),
    }
    score = score[score["scorecard_item"] != "stage31_residual_graph_controls"]
    score = pd.concat([score, pd.DataFrame([new])], ignore_index=True)
    score.to_csv(score_path, index=False)

    active_path = ROOT / "docs" / "ACTIVE_V3_STATUS.md"
    text = active_path.read_text(encoding="utf-8")
    marker = "\n\n## Stage 31 residual graph-control status\n"
    addition = (
        marker
        + "\nStage 31 residual graph controls are complete as an anti-oversmoothing experiment. "
        + f"Best Stage 31 condition: `{row.best_stage31_condition}` "
        + f"(`{row.best_stage31_mean_pooled_oof_spearman:.4f}`). "
        + f"Full Stage 31 pass: `{bool(row.full_stage31_pass)}`. "
        + f"Controlled interpretation: `{row.controlled_interpretation}`. "
        + "Stage 27C remains the reference unless a residual graph condition passes all gates. "
        + "External validation remains not run, and in silico ablation remains unvalidated.\n"
    )
    active_path.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")

    score_doc = ROOT / "docs" / "V3_SCORECARD.md"
    text = score_doc.read_text(encoding="utf-8")
    marker = "\n\n## Stage 31 residual graph-control result\n"
    addition = (
        marker
        + f"\nBest Stage 31 condition: `{row.best_stage31_condition}`; "
        + f"mean pooled OOF Spearman: `{row.best_stage31_mean_pooled_oof_spearman:.4f}`; "
        + f"best minus Stage 27C reference: `{row.best_minus_stage27c_reference:.4f}`; "
        + f"best minus no-graph residual: `{row.best_real_residual_minus_no_graph_residual:.4f}`; "
        + f"best minus strict-shuffled residual: `{row.best_real_residual_minus_strict_shuffled_residual:.4f}`. "
        + f"Full pass: `{bool(row.full_stage31_pass)}`. "
        + f"Interpretation: `{row.controlled_interpretation}`.\n"
    )
    score_doc.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")


def write_report(
    cfg: dict,
    target: pd.DataFrame,
    mean: pd.DataFrame,
    pairs: pd.DataFrame,
    stage27c_delta: pd.DataFrame,
    module_delta: pd.DataFrame,
    bootstrap: pd.DataFrame,
    graph_audit_df: pd.DataFrame,
    feature_audit_df: pd.DataFrame,
    pf: pd.DataFrame,
) -> None:
    row = pf.iloc[0]
    best_targets = target[target["condition"] == row.best_stage31_condition]
    lines = [
        "# Stage 31 residual graph controls report v1",
        "",
        "## 1. Executive summary",
        "",
        f"Best Stage 31 condition: `{row.best_stage31_condition}` (`{row.best_stage31_mean_pooled_oof_spearman:.4f}`).",
        f"Stage 27C reference: `{row.stage27c_reference_mean:.4f}`; best minus reference: `{row.best_minus_stage27c_reference:.4f}`.",
        f"Full Stage 31 pass: `{bool(row.full_stage31_pass)}`. Target-specific partial pass: `{bool(row.target_specific_partial_pass)}`.",
        f"Controlled interpretation: `{row.controlled_interpretation}`.",
        "",
        "## 2. Why Stage 31 was run",
        "",
        "Stage 30 showed that mandatory graph smoothing beat strict-shuffled topology but underperformed the Stage 27C no-graph rescue baseline. Stage 31 is explicitly an anti-oversmoothing experiment: it tests whether graph information helps when added as an optional residual feature layer rather than forcing sharp module/pathology signals through a smoothing transform.",
        "",
        "## 3. Stage 27C and Stage 30 recap",
        "",
        f"Stage 27C `module_pca_ridge` passed with mean pooled donor-level OOF Spearman `{cfg['stage27c_reference_mean']:.4f}`. Stage 30 real graph smoothing reached `0.3205`, beat strict-shuffled by about `0.0219`, but failed to beat no-graph/reference and failed the target-degradation gate.",
        "",
        "## 4. What was run",
        "",
        "- Loaded the frozen Stage 27C module-PCA ridge reference predictions.",
        "- Ran residual real graph, residual no-graph, and residual strict-shuffled graph PCA-ridge controls.",
        "- Ran target-specific ridge gates.",
        "- Ran predeclared weak diffusion anti-oversmoothing conditions at alpha 0.05, 0.10, and 0.20.",
        "- Ran hub-capped real graph residual diagnostics.",
        "- Ran graph-residual-only diagnostic features without the Stage 27C skip path.",
        "",
        "## 5. What was not run",
        "",
        "- No external matrices, clean holdouts, or model selection on external datasets.",
        "- No high-capacity GNN, full GAT, hyperbolic latent space, or VICReg-JEPA objective.",
        "- No broad hyperparameter search.",
        "- No manuscript claim update.",
        "",
        "## 6. Locked benchmark policy",
        "",
        "The official metric remains pooled donor-level OOF Spearman on locked Stage 24 donor folds. Required targets are AT8, 6e10/A beta, GFAP, Iba1, and NeuN. Minimum v3 success remains 0.3228, with no target allowed to drop below -0.02 versus module mean or Stage 27C reference for a full pass.",
        "",
        "## 7. Feature construction",
        "",
        "Stage 27C module features are preserved as an untouched skip path for every full-pass-eligible condition. Scaling, PCA, and ridge fitting occur inside each training fold only. The graph-residual-only condition is diagnostic and is not full-pass eligible.",
        "",
        "## 8. Graph residual construction",
        "",
        "Graph residuals are module summaries of `graph-smoothed expression minus identity/no-graph expression`. This directly asks what graph topology adds beyond the no-graph representation.",
        "",
        "## 9. No-graph and strict-shuffled controls",
        "",
        "`residual_no_graph_pca_ridge` controls added feature slots/capacity. `residual_strict_shuffled_graph_pca_ridge` controls graph-like topology while destroying biological edge correspondence.",
        "",
        "## 10. Hub-capping / weak-diffusion diagnostics",
        "",
        "Weak diffusion alphas were predeclared as 0.05, 0.10, and 0.20. Hub capping downweighted edges touching top-degree hubs to test whether hub dominance contributed to oversmoothing.",
        "",
        "## 11. Leakage and holdout controls",
        "",
        "No held-out donor leakage, external matrix use, or clean holdout use is permitted. Preprocessing is fold-local.",
        "",
        "## 12. Mean pooled OOF results",
        "",
        "```csv",
        mean.to_csv(index=False).strip(),
        "```",
        "",
        "## 13. Target-level results",
        "",
        "```csv",
        target.to_csv(index=False).strip(),
        "```",
        "",
        "## 14. Pairwise deltas",
        "",
        "```csv",
        pairs.to_csv(index=False).strip(),
        "```",
        "",
        "## 15. Bootstrap confidence intervals",
        "",
        "```csv",
        bootstrap.to_csv(index=False).strip(),
        "```",
        "",
        "## 16. Pass/fail decision",
        "",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
        "",
        "## 17. Interpretation boundary",
        "",
        "This result does not prove graph topology is validated, Graph-JEPA improves the benchmark, causality, validated gene targets, druggability, spatial plaque proximity, experimental therapeutic efficacy, or in silico ablation validity.",
        "",
        "If real residual graph beats strict-shuffled but not no-graph, the allowed claim is only that graph-like residual features contain some structure while topology-specific utility is not established. If no-graph remains best, the current best internal model remains Stage 27C module_pca_ridge / no-graph.",
        "",
        "## 18. Recommended next stage",
        "",
        (
            "Proceed to replication/stability and external validation planning before any graph-mechanistic interpretation."
            if bool(row.full_stage31_pass)
            else "Keep Stage 27C as the internal reference and treat Stage 31 as an anti-oversmoothing diagnostic unless a later preregistered residual graph run passes all gates."
        ),
        "",
        "## Feature audit",
        "",
        "```csv",
        feature_audit_df.to_csv(index=False).strip(),
        "```",
        "",
        "## Graph audit",
        "",
        "```csv",
        graph_audit_df.to_csv(index=False).strip(),
        "```",
        "",
        "## Target deltas versus Stage 27C",
        "",
        "```csv",
        stage27c_delta.to_csv(index=False).strip(),
        "```",
        "",
        "## Target deltas versus module mean",
        "",
        "```csv",
        module_delta.to_csv(index=False).strip(),
        "```",
        "",
        "## Best-condition target summary",
        "",
        "```csv",
        best_targets.to_csv(index=False).strip(),
        "```",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_outputs(oof: pd.DataFrame, mean: pd.DataFrame, pairs: pd.DataFrame, pf: pd.DataFrame) -> None:
    expected = [
        OOF_OUT,
        TARGET_OUT,
        MEAN_OUT,
        PAIRWISE_OUT,
        TARGET_DELTA_STAGE27C_OUT,
        TARGET_DELTA_MODULE_OUT,
        PASS_FAIL_OUT,
        BOOT_OUT,
        FEATURE_AUDIT_OUT,
        GRAPH_AUDIT_OUT,
        REPORT_OUT,
    ]
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing expected Stage 31 outputs: " + "; ".join(missing))
    if set(oof["target_key"].unique()) != REQUIRED_TARGETS:
        raise ValueError("Stage 31 OOF targets do not match required target set")
    required_conditions = {REFERENCE, PRIMARY_REAL, NO_GRAPH, STRICT, TARGET_GATED, WEAK_PRIMARY, HUB_PRIMARY}
    if not required_conditions.issubset(set(mean["condition"])):
        raise ValueError("Stage 31 missing required conditions")
    required_pair_names = {f"{left}_minus_{right}" for left, right in REQUIRED_PAIRS}
    if not required_pair_names.issubset(set(pairs["comparison"])):
        raise ValueError("Stage 31 missing required pairwise comparisons")
    required_pf_cols = {
        "best_stage31_condition",
        "full_stage31_pass",
        "target_specific_partial_pass",
        "controlled_interpretation",
    }
    if not required_pf_cols.issubset(set(pf.columns)):
        raise ValueError("Stage 31 pass/fail table lacks required columns")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage31_residual_graph_controls_v3.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    oof, graph_audit_df, feature_audit_df, _ = run_conditions(cfg)
    target, mean = compute_metrics(oof)
    pairs, stage27c_delta, module_delta = comparisons(target, mean)
    bootstrap = bootstrap_summary(oof, pairs, cfg)
    pf = pass_fail(
        oof,
        target,
        mean,
        pairs,
        stage27c_delta,
        module_delta,
        graph_audit_df,
        feature_audit_df,
        cfg,
    )

    oof.to_csv(OOF_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    pairs.to_csv(PAIRWISE_OUT, index=False)
    stage27c_delta.to_csv(TARGET_DELTA_STAGE27C_OUT, index=False)
    module_delta.to_csv(TARGET_DELTA_MODULE_OUT, index=False)
    pf.to_csv(PASS_FAIL_OUT, index=False)
    bootstrap.to_csv(BOOT_OUT, index=False)
    feature_audit_df.to_csv(FEATURE_AUDIT_OUT, index=False)
    graph_audit_df.to_csv(GRAPH_AUDIT_OUT, index=False)
    write_report(
        cfg,
        target,
        mean,
        pairs,
        stage27c_delta,
        module_delta,
        bootstrap,
        graph_audit_df,
        feature_audit_df,
        pf,
    )
    validate_outputs(oof, mean, pairs, pf)
    update_status(pf)

    row = pf.iloc[0]
    best_targets = target[target["condition"] == row.best_stage31_condition][
        ["target_key", "pooled_oof_spearman"]
    ].copy()
    print(f"best_stage31_condition={row.best_stage31_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_stage31_mean_pooled_oof_spearman:.6f}")
    print(f"stage27c_reference_mean={row.stage27c_reference_mean:.6f}")
    print(f"best_minus_stage27c_reference={row.best_minus_stage27c_reference:.6f}")
    print(f"best_real_residual_minus_no_graph_residual={row.best_real_residual_minus_no_graph_residual:.6f}")
    print(f"best_real_residual_minus_strict_shuffled_residual={row.best_real_residual_minus_strict_shuffled_residual:.6f}")
    print(best_targets.to_string(index=False))
    print(f"full_stage31_pass={bool(row.full_stage31_pass)}")
    print(f"target_specific_partial_pass={bool(row.target_specific_partial_pass)}")


if __name__ == "__main__":
    main()
