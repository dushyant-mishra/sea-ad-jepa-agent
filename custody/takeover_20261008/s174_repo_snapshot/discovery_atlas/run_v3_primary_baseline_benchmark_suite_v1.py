"""Run Stage 25 primary leakage-safe v3 baseline benchmark suite.

This script evaluates only the primary non-neural baselines approved in the
Stage 24 harness. It uses locked donor folds, performs all preprocessing inside
training folds, and does not train v3, neural baselines, graph models,
transductive embeddings, or external validation models.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.stats import pearsonr, spearmanr
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES  # noqa: E402


LOCKED_FOLDS = TABLE_DIR / "v3_locked_donor_folds_v1.csv"
TARGET_MANIFEST = TABLE_DIR / "v3_benchmark_target_manifest_v1.csv"
BASELINE_REGISTRY = TABLE_DIR / "v3_benchmark_baseline_registry_v1.csv"
METADATA_TARGETS = TABLE_DIR / "sea_ad_full_metadata_targets_with_covariates.csv"
PSEUDOBULK_FEATURES = ROOT / "data" / "processed" / "sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv"
WGCNA_EDGES = TABLE_DIR / "v2_graph_wgcna_edges.csv"
V2_GRAPH_REFERENCE = TABLE_DIR / "strict_shuffled_graph_ablation_predictive_representation_comparison_v1.csv"

RESULTS_OUT = TABLE_DIR / "v3_primary_baseline_benchmark_results_v1.csv"
DELTAS_OUT = TABLE_DIR / "v3_primary_baseline_pairwise_deltas_v1.csv"
WINNERS_OUT = TABLE_DIR / "v3_primary_baseline_target_winners_v1.csv"
REPORT_OUT = REPORT_DIR / "v3_primary_baseline_benchmark_suite_v1.md"

SEED = 7
SMALL_DIFFERENCE_BAND = 0.01
OLD_V2_MODULE_MEAN = 0.2999
OLD_V2_REAL_GRAPH = 0.2892

PRIMARY_BASELINES = [
    "raw_expression_ridge",
    "raw_expression_elasticnet",
    "pca_ridge",
    "pca_elasticnet",
    "module_mean_baseline",
    "wgcna_module_summary_ridge",
    "wgcna_module_summary_elasticnet",
    "xgboost_raw_expression",
    "lightgbm_raw_expression",
]

TARGET_ALIAS_TO_NAME = {
    "percent AT8 positive area_Grey matter": "AT8",
    "percent 6e10 positive area_Grey matter": "6e10/Aβ",
    "percent GFAP positive area_Grey matter": "GFAP",
    "percent Iba1 positive area_Grey matter": "Iba1",
    "percent NeuN positive area_Grey matter": "NeuN",
}


@dataclass
class FeatureBlock:
    matrix: pd.DataFrame
    source: str
    notes: str


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    for path in [LOCKED_FOLDS, TARGET_MANIFEST, BASELINE_REGISTRY, METADATA_TARGETS, PSEUDOBULK_FEATURES]:
        if not path.exists():
            raise FileNotFoundError(path)
    folds = pd.read_csv(LOCKED_FOLDS)
    targets = pd.read_csv(TARGET_MANIFEST)
    registry = pd.read_csv(BASELINE_REGISTRY)
    metadata = pd.read_csv(METADATA_TARGETS)
    return folds, targets, registry, metadata


def load_expression_matrix(locked_donors: list[str]) -> pd.DataFrame:
    expr = pd.read_csv(PSEUDOBULK_FEATURES)
    if "Donor ID" not in expr.columns:
        raise ValueError(f"{PSEUDOBULK_FEATURES} lacks `Donor ID`")
    expr = expr.drop_duplicates("Donor ID").set_index("Donor ID")
    expr.index = expr.index.astype(str)
    numeric = expr.apply(pd.to_numeric, errors="coerce")
    numeric = numeric.loc[[donor for donor in locked_donors if donor in numeric.index]]
    numeric = numeric.dropna(axis=1, how="all").fillna(0.0)
    return numeric


def build_target_matrix(metadata: pd.DataFrame, targets: pd.DataFrame, locked_donors: list[str]) -> pd.DataFrame:
    metadata = metadata.drop_duplicates("Donor ID").set_index("Donor ID")
    metadata.index = metadata.index.astype(str)
    target_cols = [row["target_alias"] for _, row in targets.iterrows() if bool(row["available"])]
    out = metadata.loc[[donor for donor in locked_donors if donor in metadata.index], target_cols].copy()
    out = out.apply(pd.to_numeric, errors="coerce")
    return out


def select_top_variance_columns(x_train: pd.DataFrame, max_features: int) -> list[str]:
    variances = x_train.var(axis=0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    variances = variances[variances > 0]
    if variances.empty:
        return list(x_train.columns[: min(max_features, x_train.shape[1])])
    return list(variances.sort_values(ascending=False).head(max_features).index)


def build_predefined_module_features(expr: pd.DataFrame) -> FeatureBlock:
    gene_to_col = {col.upper(): col for col in expr.columns}
    features: dict[str, pd.Series] = {}
    used = []
    for module_name, genes in MICROGLIA_GENE_MODULES.items():
        cols = [gene_to_col[g.upper()] for g in genes if g.upper() in gene_to_col]
        if len(cols) >= 2:
            features[f"module_{module_name}"] = expr[cols].mean(axis=1)
            used.append(f"{module_name}:{len(cols)}")
    if not features:
        raise ValueError("No predefined microglia modules overlapped expression features")
    return FeatureBlock(
        matrix=pd.DataFrame(features, index=expr.index),
        source="predefined_microglia_gene_modules",
        notes="Target-independent MICROGLIA_GENE_MODULES means; overlaps=" + "; ".join(used),
    )


def build_wgcna_module_features(expr: pd.DataFrame, max_modules: int = 75) -> FeatureBlock:
    if not WGCNA_EDGES.exists():
        raise FileNotFoundError(WGCNA_EDGES)
    edges = pd.read_csv(WGCNA_EDGES, usecols=["source", "target", "weight"])
    edges["source"] = edges["source"].astype(str)
    edges["target"] = edges["target"].astype(str)
    edges["weight"] = pd.to_numeric(edges["weight"], errors="coerce").fillna(0.0)

    expr_genes = {col.upper(): col for col in expr.columns}
    edges = edges[
        edges["source"].str.upper().isin(expr_genes)
        & edges["target"].str.upper().isin(expr_genes)
    ].copy()
    if edges.empty:
        raise ValueError("No WGCNA edges overlap expression features")

    # Target-independent graph thresholding. Use the strongest WGCNA/TOM edges
    # to avoid one giant component while never consulting pathology labels.
    threshold = float(edges["weight"].quantile(0.99))
    strong = edges[edges["weight"] >= threshold].copy()
    if len(strong) < 100:
        strong = edges.sort_values("weight", ascending=False).head(min(5000, len(edges))).copy()

    graph = nx.Graph()
    graph.add_weighted_edges_from(
        (row.source.upper(), row.target.upper(), float(row.weight)) for row in strong.itertuples()
    )
    communities = [
        sorted(component)
        for component in nx.connected_components(graph)
        if len(component) >= 3
    ]
    communities = sorted(communities, key=len, reverse=True)[:max_modules]
    features: dict[str, pd.Series] = {}
    sizes = []
    for idx, genes in enumerate(communities, start=1):
        cols = [expr_genes[gene] for gene in genes if gene in expr_genes]
        if len(cols) >= 3:
            features[f"wgcna_component_{idx:03d}"] = expr[cols].mean(axis=1)
            sizes.append(len(cols))
    if not features:
        raise ValueError("No WGCNA components with >=3 overlapping genes")
    return FeatureBlock(
        matrix=pd.DataFrame(features, index=expr.index),
        source="wgcna_graph_component_means",
        notes=(
            f"Target-independent WGCNA graph component means from top 1% TOM edges; "
            f"modules={len(features)}; median_genes={float(np.median(sizes)):.1f}"
        ),
    )


def safe_corr(y_true: np.ndarray, y_pred: np.ndarray, method: str) -> float:
    if len(y_true) < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return 0.0
    try:
        value = pearsonr(y_true, y_pred).statistic if method == "pearson" else spearmanr(y_true, y_pred).statistic
        return 0.0 if pd.isna(value) else float(value)
    except Exception:
        return 0.0


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "oof_pearson": safe_corr(y_true, y_pred, "pearson"),
        "oof_spearman": safe_corr(y_true, y_pred, "spearman"),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) >= 2 else float("nan"),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(math.sqrt(mean_squared_error(y_true, y_pred))),
    }


def make_model(baseline_id: str, n_train: int, n_features: int, target_seed: int):
    if baseline_id.endswith("_ridge") or baseline_id == "module_mean_baseline":
        return RidgeCV(alphas=np.array([0.1, 1.0, 10.0, 100.0]), cv=min(3, max(2, n_train // 10)))
    if baseline_id.endswith("_elasticnet"):
        return ElasticNetCV(
            alphas=np.array([0.001, 0.01, 0.1, 1.0]),
            l1_ratio=np.array([0.1, 0.5, 0.9]),
            cv=min(3, max(2, n_train // 10)),
            max_iter=20000,
            random_state=target_seed,
            n_jobs=1,
        )
    if baseline_id == "xgboost_raw_expression":
        return XGBRegressor(
            n_estimators=80,
            max_depth=2,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.7,
            reg_lambda=5.0,
            objective="reg:squarederror",
            random_state=target_seed,
            n_jobs=1,
            verbosity=0,
        )
    if baseline_id == "lightgbm_raw_expression":
        return LGBMRegressor(
            n_estimators=80,
            learning_rate=0.03,
            max_depth=2,
            num_leaves=7,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.7,
            reg_lambda=5.0,
            random_state=target_seed,
            n_jobs=1,
            verbose=-1,
        )
    # Fallback should never be used for the locked list, but keeps the script
    # robust if a package-specific regressor is unavailable.
    return RandomForestRegressor(
        n_estimators=80,
        max_depth=3,
        min_samples_leaf=5,
        random_state=target_seed,
        n_jobs=1,
    )


def fit_predict_baseline(
    baseline_id: str,
    expr: pd.DataFrame,
    module_features: FeatureBlock,
    wgcna_features: FeatureBlock,
    y: pd.Series,
    folds: pd.DataFrame,
    target_seed: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for fold_id in sorted(folds["fold_id"].unique()):
        test_donors = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
        train_donors = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
        train_donors = [d for d in train_donors if d in y.index]
        test_donors = [d for d in test_donors if d in y.index]
        y_train = np.log1p(y.loc[train_donors].astype(float).to_numpy())
        y_test = np.log1p(y.loc[test_donors].astype(float).to_numpy())

        if baseline_id.startswith("raw_expression") or baseline_id in {"pca_ridge", "pca_elasticnet", "xgboost_raw_expression", "lightgbm_raw_expression"}:
            max_features = 500 if baseline_id.startswith(("xgboost", "lightgbm")) else 1000
            selected = select_top_variance_columns(expr.loc[train_donors], max_features)
            x_train = expr.loc[train_donors, selected].to_numpy(dtype=float)
            x_test = expr.loc[test_donors, selected].to_numpy(dtype=float)
            feature_source = "donor_pseudobulk_expression_train_fold_variance_filtered"
            source_notes = f"unsupervised top-variance features selected within training fold; max_features={max_features}"
        elif baseline_id == "module_mean_baseline":
            selected = list(module_features.matrix.columns)
            x_train = module_features.matrix.loc[train_donors, selected].to_numpy(dtype=float)
            x_test = module_features.matrix.loc[test_donors, selected].to_numpy(dtype=float)
            feature_source = module_features.source
            source_notes = module_features.notes
        elif baseline_id.startswith("wgcna_module_summary"):
            selected = list(wgcna_features.matrix.columns)
            x_train = wgcna_features.matrix.loc[train_donors, selected].to_numpy(dtype=float)
            x_test = wgcna_features.matrix.loc[test_donors, selected].to_numpy(dtype=float)
            feature_source = wgcna_features.source
            source_notes = wgcna_features.notes
        else:
            raise ValueError(f"Unexpected primary baseline: {baseline_id}")

        n_features = x_train.shape[1]
        if baseline_id.startswith("pca_"):
            n_components = min(25, x_train.shape[0] - 1, x_train.shape[1])
            estimator = make_model(baseline_id, len(train_donors), n_components, target_seed)
            model = Pipeline(
                [
                    ("scale", StandardScaler()),
                    ("pca", PCA(n_components=n_components, random_state=SEED)),
                    ("model", estimator),
                ]
            )
            pca_note = f"; PCA n_components={n_components} fit on training donors only"
        else:
            estimator = make_model(baseline_id, len(train_donors), n_features, target_seed)
            model = Pipeline([("scale", StandardScaler()), ("model", estimator)])
            pca_note = ""

        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        fold_metrics = metrics(y_test, pred)
        rows.append(
            {
                "baseline_id": baseline_id,
                "target_alias": y.name,
                "fold_id": int(fold_id),
                "n_train_donors": len(train_donors),
                "n_test_donors": len(test_donors),
                "n_features": int(n_features),
                **fold_metrics,
                "feature_source": feature_source,
                "notes": source_notes + pca_note + "; target transformed with log1p inside benchmark",
            }
        )
    return rows


def baseline_metadata(registry: pd.DataFrame) -> dict[str, dict[str, object]]:
    return registry.set_index("baseline_id").to_dict(orient="index")


def run_suite() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    folds, targets, registry, metadata = load_inputs()
    primary_registry = registry[registry["baseline_id"].isin(PRIMARY_BASELINES)].copy()
    missing = sorted(set(PRIMARY_BASELINES) - set(primary_registry["baseline_id"]))
    if missing:
        raise ValueError(f"Missing primary baselines from registry: {missing}")

    locked_donors = folds["donor_id"].astype(str).tolist()
    expr = load_expression_matrix(locked_donors)
    target_matrix = build_target_matrix(metadata, targets, locked_donors)
    shared_donors = sorted(set(expr.index) & set(target_matrix.index) & set(locked_donors))
    expr = expr.loc[shared_donors]
    target_matrix = target_matrix.loc[shared_donors]
    folds = folds[folds["donor_id"].astype(str).isin(shared_donors)].copy()

    module_features = build_predefined_module_features(expr)
    wgcna_features = build_wgcna_module_features(expr)
    meta = baseline_metadata(registry)

    result_rows = []
    for target_idx, target_alias in enumerate(target_matrix.columns):
        y = target_matrix[target_alias].dropna()
        for baseline_id in PRIMARY_BASELINES:
            rows = fit_predict_baseline(
                baseline_id=baseline_id,
                expr=expr,
                module_features=module_features,
                wgcna_features=wgcna_features,
                y=y,
                folds=folds,
                target_seed=SEED + target_idx,
            )
            for row in rows:
                target_name = TARGET_ALIAS_TO_NAME.get(row["target_alias"], str(row["target_alias"]))
                baseline_info = meta[row["baseline_id"]]
                result_rows.append(
                    {
                        "baseline_id": row["baseline_id"],
                        "baseline_name": baseline_info["baseline_name"],
                        "target": target_name,
                        "target_alias": row["target_alias"],
                        "fold_id": row["fold_id"],
                        "n_train_donors": row["n_train_donors"],
                        "n_test_donors": row["n_test_donors"],
                        "n_features": row["n_features"],
                        "oof_pearson": row["oof_pearson"],
                        "oof_spearman": row["oof_spearman"],
                        "r2": row["r2"],
                        "mae": row["mae"],
                        "rmse": row["rmse"],
                        "model_family": baseline_info["baseline_family"],
                        "feature_source": row["feature_source"],
                        "leakage_safe": True,
                        "notes": row["notes"],
                    }
                )

    results = pd.DataFrame(result_rows)
    winners = build_winners(results)
    deltas = build_pairwise_deltas(results, winners)
    context = {
        "n_donors": len(shared_donors),
        "n_folds": int(folds["fold_id"].nunique()),
        "expression_features": int(expr.shape[1]),
        "module_features": int(module_features.matrix.shape[1]),
        "wgcna_features": int(wgcna_features.matrix.shape[1]),
    }
    return results, deltas, winners, context


def target_baseline_summary(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.groupby(["baseline_id", "baseline_name", "target"], as_index=False)
        .agg(
            oof_pearson=("oof_pearson", "mean"),
            oof_spearman=("oof_spearman", "mean"),
            r2=("r2", "mean"),
            mae=("mae", "mean"),
            rmse=("rmse", "mean"),
            n_features=("n_features", "median"),
        )
    )


def build_winners(results: pd.DataFrame) -> pd.DataFrame:
    target_summary = target_baseline_summary(results)
    target_summary["target_specific_rank"] = target_summary.groupby("target")["oof_spearman"].rank(
        method="dense", ascending=False
    ).astype(int)
    target_winners = target_summary.loc[target_summary.groupby("target")["oof_spearman"].idxmax()].copy()
    mean_rank = (
        target_summary.groupby(["baseline_id", "baseline_name"], as_index=False)["oof_spearman"]
        .agg(mean_oof_spearman="mean", median_oof_spearman="median")
        .sort_values("mean_oof_spearman", ascending=False)
    )
    mean_rank["rank"] = np.arange(1, len(mean_rank) + 1)
    rows = []
    for _, row in target_summary.iterrows():
        global_row = mean_rank[mean_rank["baseline_id"] == row["baseline_id"]].iloc[0]
        winner_row = target_winners[target_winners["target"] == row["target"]].iloc[0]
        rows.append(
            {
                "baseline_id": row["baseline_id"],
                "baseline_name": row["baseline_name"],
                "target": row["target"],
                "target_oof_spearman": row["oof_spearman"],
                "target_specific_rank": int(row["target_specific_rank"]),
                "target_specific_winner": winner_row["baseline_id"],
                "mean_oof_spearman_across_targets": global_row["mean_oof_spearman"],
                "median_oof_spearman_across_targets": global_row["median_oof_spearman"],
                "rank": int(global_row["rank"]),
                "is_target_winner": row["baseline_id"] == winner_row["baseline_id"],
            }
        )
    return pd.DataFrame(rows).sort_values(["rank", "target_specific_rank", "target"])


def label_delta(left: str, right: str, delta: float) -> str:
    if abs(delta) <= SMALL_DIFFERENCE_BAND:
        return "difference_within_small_band"
    if left.startswith("wgcna") and right == "module_mean_baseline" and delta > 0:
        return "wgcna_module_features_improve_over_module_mean"
    if left in {"xgboost_raw_expression", "lightgbm_raw_expression"} and delta > 0:
        return "boosting_improves_over_linear_baselines"
    if left.startswith("raw_expression") and delta >= 0:
        return "raw_expression_remains_competitive"
    if right == "module_mean_baseline" and delta < 0:
        return "module_mean_remains_best_primary_baseline"
    if delta > 0:
        return "new_high_watermark_established"
    return "v3_target_updated"


def build_pairwise_deltas(results: pd.DataFrame, winners: pd.DataFrame) -> pd.DataFrame:
    target_summary = target_baseline_summary(results)
    score = {
        (row.baseline_id, row.target): float(row.oof_spearman)
        for row in target_summary.itertuples()
    }
    targets = sorted(target_summary["target"].unique())
    baselines = sorted(target_summary["baseline_id"].unique())
    rows = []

    def add_row(comparison: str, left: str, right: str, target: str, left_score: float, right_score: float) -> None:
        delta = left_score - right_score
        rows.append(
            {
                "comparison": comparison,
                "left_baseline": left,
                "right_baseline": right,
                "target": target,
                "left_oof_spearman": left_score,
                "right_oof_spearman": right_score,
                "delta": delta,
                "small_difference_band": SMALL_DIFFERENCE_BAND,
                "conclusion_label": label_delta(left, right, delta),
            }
        )

    for target in targets:
        for baseline in baselines:
            if baseline != "module_mean_baseline":
                add_row(
                    "baseline_vs_module_mean_baseline",
                    baseline,
                    "module_mean_baseline",
                    target,
                    score[(baseline, target)],
                    score[("module_mean_baseline", target)],
                )
            if baseline != "raw_expression_ridge":
                add_row(
                    "baseline_vs_raw_expression_ridge",
                    baseline,
                    "raw_expression_ridge",
                    target,
                    score[(baseline, target)],
                    score[("raw_expression_ridge", target)],
                )

    if V2_GRAPH_REFERENCE.exists():
        v2 = pd.read_csv(V2_GRAPH_REFERENCE)
        v2 = v2[v2["representation"] == "graph_jepa_real_graph_latent"].copy()
        v2["target_name"] = v2["target"].map(TARGET_ALIAS_TO_NAME).fillna(v2["target"])
        v2_score = dict(zip(v2["target_name"], v2["oof_spearman"]))
        for target in targets:
            if target in v2_score:
                for baseline in baselines:
                    add_row(
                        "baseline_vs_prior_graph_jepa_real_graph_latent",
                        baseline,
                        "graph_jepa_real_graph_latent",
                        target,
                        score[(baseline, target)],
                        float(v2_score[target]),
                    )

    mean_scores = (
        target_summary.groupby("baseline_id")["oof_spearman"]
        .mean()
        .sort_values(ascending=False)
    )
    best = str(mean_scores.index[0])
    best_score = float(mean_scores.iloc[0])
    add_row(
        "best_primary_vs_old_v2_module_mean_target",
        best,
        "old_v2_module_mean_target_0.2999",
        "mean_across_targets",
        best_score,
        OLD_V2_MODULE_MEAN,
    )
    add_row(
        "best_primary_vs_old_v2_real_graph_0.2892",
        best,
        "old_v2_real_graph_0.2892",
        "mean_across_targets",
        best_score,
        OLD_V2_REAL_GRAPH,
    )
    return pd.DataFrame(rows)


def write_report(results: pd.DataFrame, deltas: pd.DataFrame, winners: pd.DataFrame, context: dict[str, object]) -> None:
    target_summary = target_baseline_summary(results)
    ranking = (
        target_summary.groupby(["baseline_id", "baseline_name"], as_index=False)["oof_spearman"]
        .agg(mean_oof_spearman="mean", median_oof_spearman="median")
        .sort_values("mean_oof_spearman", ascending=False)
    )
    ranking["rank"] = np.arange(1, len(ranking) + 1)
    best = ranking.iloc[0]
    best_baseline = str(best["baseline_id"])
    best_score = float(best["mean_oof_spearman"])
    min_v3_target = best_score + SMALL_DIFFERENCE_BAND

    target_winners = winners[winners["is_target_winner"]].sort_values("target")
    module_score = float(ranking.loc[ranking["baseline_id"] == "module_mean_baseline", "mean_oof_spearman"].iloc[0])
    xgb_score = float(ranking.loc[ranking["baseline_id"] == "xgboost_raw_expression", "mean_oof_spearman"].iloc[0])
    lgb_score = float(ranking.loc[ranking["baseline_id"] == "lightgbm_raw_expression", "mean_oof_spearman"].iloc[0])
    wgcna_best = float(
        ranking.loc[
            ranking["baseline_id"].isin(["wgcna_module_summary_ridge", "wgcna_module_summary_elasticnet"]),
            "mean_oof_spearman",
        ].max()
    )

    rank_lines = [
        f"- {int(row.rank)}. `{row.baseline_id}`: mean={row.mean_oof_spearman:.4f}, median={row.median_oof_spearman:.4f}"
        for row in ranking.itertuples()
    ]
    target_lines = [
        f"- {row.target}: `{row.baseline_id}` ({row.target_oof_spearman:.4f})"
        for row in target_winners.itertuples()
    ]
    perf_lines = [
        f"- {row.target} / `{row.baseline_id}`: Spearman={row.oof_spearman:.4f}, R2={row.r2:.4f}, MAE={row.mae:.4f}, RMSE={row.rmse:.4f}"
        for row in target_summary.sort_values(["target", "oof_spearman"], ascending=[True, False]).itertuples()
    ]
    pairwise_lines = [
        f"- {row.comparison}: `{row.left_baseline}` vs `{row.right_baseline}` on {row.target}: Δ={row.delta:.4f} ({row.conclusion_label})"
        for row in deltas.tail(20).itertuples()
    ]

    REPORT_OUT.write_text(
        "\n".join(
            [
                "# v3 primary baseline benchmark suite v1",
                "",
                "## 1. Executive summary",
                "",
                f"Stage 25 evaluated the nine approved primary leakage-safe non-neural baselines using the locked Stage 24 donor folds. The current high-water mark is `{best_baseline}` with mean OOF Spearman `{best_score:.4f}` across the five pathology targets.",
                "",
                "No v3 model, graph neural model, neural/deep baseline, transductive embedding, external validation, evidence-level change, candidate biology card, or manuscript prose was run.",
                "",
                "## 2. Locked donor-fold protocol",
                "",
                f"- Runtime: `sea-ad-jepa-v3`",
                f"- Donors evaluated: `{context['n_donors']}`",
                f"- Folds: `{context['n_folds']}`",
                "- Split unit: donor only; all preprocessing/model fitting happens inside training donors.",
                "- Targets are transformed with `log1p` for regression; Spearman comparisons remain rank-based.",
                "",
                "## 3. Primary baselines evaluated",
                "",
                *[f"- `{baseline}`" for baseline in PRIMARY_BASELINES],
                "",
                "## 4. Leakage-safety protocol",
                "",
                "- Locked donor folds from Stage 24 only.",
                "- No cell-level random splits.",
                "- Scalers, variance feature filters, PCA, ElasticNet inner CV, and models are fit inside each training fold only.",
                "- PCA is fit on training donors and used only to transform held-out donors.",
                "- Module mean features use target-independent predefined microglia modules.",
                "- WGCNA module summaries use target-independent graph components from the WGCNA/TOM edge asset, without pathology labels.",
                "- XGBoost/LightGBM use conservative shallow settings with no test-fold tuning.",
                "",
                "## 5. Target-level performance",
                "",
                *perf_lines,
                "",
                "## 6. Mean OOF Spearman ranking",
                "",
                *rank_lines,
                "",
                "## 7. Pairwise deltas",
                "",
                f"Frozen small-difference band: `{SMALL_DIFFERENCE_BAND}`.",
                "",
                *pairwise_lines,
                "",
                "Full pairwise table: `results/tables/v3_primary_baseline_pairwise_deltas_v1.csv`.",
                "",
                "## 8. New high-water mark",
                "",
                f"- Old target: module_mean_baseline = `{OLD_V2_MODULE_MEAN:.4f}`",
                f"- Old v2 real Graph-JEPA = `{OLD_V2_REAL_GRAPH:.4f}`",
                f"- New target: best primary baseline mean OOF Spearman = `{best_score:.4f}` from `{best_baseline}`",
                f"- Minimum v3 success: best primary baseline + 0.01 = `{min_v3_target:.4f}` mean OOF Spearman",
                "",
                "## 9. Implication for v3 success criterion",
                "",
                "The v3 model should not be judged against the old module-mean target alone. It must exceed the Stage 25 best primary baseline by at least the frozen small-difference band.",
                "",
                "## 10. Deferred baselines",
                "",
                "t-SNE, UMAP, supervised UMAP, PHATE, diffusion maps, scVI/VAE, autoencoder, MLPs, graph-only GNN, v3 real graph, v3 no-graph, v3 strict shuffled graph, and causal estimator layers remain deferred.",
                "",
                "## 11. Overfitting cautions",
                "",
                f"- n_donors is `{context['n_donors']}`, so XGBoost and LightGBM are high-capacity baselines despite conservative settings.",
                "- ElasticNet uses inner training-fold CV only.",
                "- WGCNA summaries are target-independent graph-derived means, not pathology-supervised modules.",
                f"- Raw expression feature count before fold-internal filtering: `{context['expression_features']}`.",
                f"- Predefined module features: `{context['module_features']}`; WGCNA module features: `{context['wgcna_features']}`.",
                "",
                "## 12. Recommended Stage 26 plan",
                "",
                "- Treat this benchmark as the new primary high-water mark.",
                "- Audit whether the winning baseline is robust target-by-target before starting v3 training.",
                "- Only after this benchmark is accepted, implement v3 controls in order: no-graph, strict shuffled graph, then real graph.",
                "- Keep manifold/deep/causal baselines deferred until their leakage-safe protocols are explicitly approved.",
                "",
                "## Target-specific winners",
                "",
                *target_lines,
                "",
                "## Direct questions",
                "",
                f"- XGBoost beats module mean: `{xgb_score > module_score + SMALL_DIFFERENCE_BAND}`.",
                f"- LightGBM beats module mean: `{lgb_score > module_score + SMALL_DIFFERENCE_BAND}`.",
                f"- Best WGCNA module summary beats module mean: `{wgcna_best > module_score + SMALL_DIFFERENCE_BAND}`.",
                f"- Old v2 module mean remains best: `{OLD_V2_MODULE_MEAN > best_score + SMALL_DIFFERENCE_BAND}`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results, deltas, winners, context = run_suite()
    results.to_csv(RESULTS_OUT, index=False)
    deltas.to_csv(DELTAS_OUT, index=False)
    winners.to_csv(WINNERS_OUT, index=False)
    write_report(results, deltas, winners, context)
    print(f"Wrote {RESULTS_OUT}")
    print(f"Wrote {DELTAS_OUT}")
    print(f"Wrote {WINNERS_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
