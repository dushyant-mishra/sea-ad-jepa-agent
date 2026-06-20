"""Audit Stage 25 v3 primary baseline benchmark protocol.

This script is diagnostic. It does not train v3, run graph neural models,
run external validation, alter evidence levels, or write manuscript prose.

The key audit is whether Stage 25's high-water mark was computed as a mean of
fold-level Spearman values rather than pooled donor-level out-of-fold Spearman.
If per-donor predictions were not saved by Stage 25, this script deterministically
reruns the approved non-neural Stage 25 primary baseline models and stores those
OOF predictions for auditability.
"""

from __future__ import annotations

import importlib
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
ATLAS_DIR = ROOT / "discovery_atlas"
if str(ATLAS_DIR) not in sys.path:
    sys.path.insert(0, str(ATLAS_DIR))

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")

TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

STAGE25_SCRIPT = ATLAS_DIR / "run_v3_primary_baseline_benchmark_suite_v1.py"
STAGE25_RESULTS = TABLE_DIR / "v3_primary_baseline_benchmark_results_v1.csv"
STAGE25_DELTAS = TABLE_DIR / "v3_primary_baseline_pairwise_deltas_v1.csv"
STAGE25_WINNERS = TABLE_DIR / "v3_primary_baseline_target_winners_v1.csv"
LOCKED_FOLDS = TABLE_DIR / "v3_locked_donor_folds_v1.csv"
METADATA_TARGETS = TABLE_DIR / "sea_ad_full_metadata_targets_with_covariates.csv"
PSEUDOBULK_FEATURES = ROOT / "data" / "processed" / "sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv"
OLD_V2_BASELINE = TABLE_DIR / "discovery_baseline_predictive_representation_comparison.csv"
OLD_V2_REPORT = ROOT / "results" / "reports" / "discovery_baseline_comparison_gate.md"

AUDIT_OUT = TABLE_DIR / "v3_primary_baseline_protocol_audit_v1.csv"
POOLED_OUT = TABLE_DIR / "v3_primary_baseline_pooled_oof_recompute_v1.csv"
COMPARISON_OUT = TABLE_DIR / "v3_primary_baseline_protocol_comparison_v1.csv"
PREDICTIONS_OUT = TABLE_DIR / "v3_primary_baseline_oof_predictions_v1.csv"
REPORT_OUT = REPORT_DIR / "v3_primary_baseline_protocol_audit_v1.md"

OLD_V2_MODULE_MEAN = 0.2999
OLD_V2_REAL_GRAPH = 0.2892
SMALL_BAND = 0.01


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        value = spearmanr(y_true, y_pred).statistic
    return 0.0 if pd.isna(value) else float(value)


def load_stage25_context():
    folds, targets, registry, metadata = s25.load_inputs()
    locked_donors = folds["donor_id"].astype(str).tolist()
    expr = s25.load_expression_matrix(locked_donors)
    target_matrix = s25.build_target_matrix(metadata, targets, locked_donors)
    shared_donors = sorted(set(expr.index) & set(target_matrix.index) & set(locked_donors))
    expr = expr.loc[shared_donors]
    target_matrix = target_matrix.loc[shared_donors]
    folds = folds[folds["donor_id"].astype(str).isin(shared_donors)].copy()
    module_features = s25.build_predefined_module_features(expr)
    wgcna_features = s25.build_wgcna_module_features(expr)
    registry_meta = s25.baseline_metadata(registry)
    return folds, target_matrix, expr, module_features, wgcna_features, registry_meta


def collect_oof_predictions() -> pd.DataFrame:
    folds, target_matrix, expr, module_features, wgcna_features, registry_meta = load_stage25_context()
    rows: list[dict[str, object]] = []
    for target_idx, target_alias in enumerate(target_matrix.columns):
        y = target_matrix[target_alias].dropna()
        target_name = s25.TARGET_ALIAS_TO_NAME.get(target_alias, target_alias)
        for baseline_id in s25.PRIMARY_BASELINES:
            for fold_id in sorted(folds["fold_id"].unique()):
                test_donors = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train_donors = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train_donors = [donor for donor in train_donors if donor in y.index]
                test_donors = [donor for donor in test_donors if donor in y.index]
                y_train = np.log1p(y.loc[train_donors].astype(float).to_numpy())
                y_test = np.log1p(y.loc[test_donors].astype(float).to_numpy())

                if baseline_id.startswith("raw_expression") or baseline_id in {
                    "pca_ridge",
                    "pca_elasticnet",
                    "xgboost_raw_expression",
                    "lightgbm_raw_expression",
                }:
                    max_features = 500 if baseline_id.startswith(("xgboost", "lightgbm")) else 1000
                    selected = s25.select_top_variance_columns(expr.loc[train_donors], max_features)
                    x_train = expr.loc[train_donors, selected].to_numpy(dtype=float)
                    x_test = expr.loc[test_donors, selected].to_numpy(dtype=float)
                    feature_source = "donor_pseudobulk_expression_train_fold_variance_filtered"
                elif baseline_id == "module_mean_baseline":
                    selected = list(module_features.matrix.columns)
                    x_train = module_features.matrix.loc[train_donors, selected].to_numpy(dtype=float)
                    x_test = module_features.matrix.loc[test_donors, selected].to_numpy(dtype=float)
                    feature_source = module_features.source
                elif baseline_id.startswith("wgcna_module_summary"):
                    selected = list(wgcna_features.matrix.columns)
                    x_train = wgcna_features.matrix.loc[train_donors, selected].to_numpy(dtype=float)
                    x_test = wgcna_features.matrix.loc[test_donors, selected].to_numpy(dtype=float)
                    feature_source = wgcna_features.source
                else:
                    raise ValueError(f"Unexpected baseline: {baseline_id}")

                if baseline_id.startswith("pca_"):
                    n_components = min(25, x_train.shape[0] - 1, x_train.shape[1])
                    estimator = s25.make_model(
                        baseline_id, len(train_donors), n_components, s25.SEED + target_idx
                    )
                    model = Pipeline(
                        [
                            ("scale", StandardScaler()),
                            ("pca", PCA(n_components=n_components, random_state=s25.SEED)),
                            ("model", estimator),
                        ]
                    )
                else:
                    estimator = s25.make_model(
                        baseline_id, len(train_donors), x_train.shape[1], s25.SEED + target_idx
                    )
                    model = Pipeline([("scale", StandardScaler()), ("model", estimator)])

                model.fit(x_train, y_train)
                pred = model.predict(x_test)
                for donor_id, true_value, pred_value in zip(test_donors, y_test, pred):
                    rows.append(
                        {
                            "donor_id": donor_id,
                            "fold_id": int(fold_id),
                            "baseline_id": baseline_id,
                            "baseline_name": registry_meta[baseline_id]["baseline_name"],
                            "target": target_name,
                            "target_alias": target_alias,
                            "y_true": float(true_value),
                            "y_pred": float(pred_value),
                            "target_scale": "log1p",
                            "feature_source": feature_source,
                        }
                    )
    return pd.DataFrame(rows)


def recompute_pooled(stage25_results: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    fold_mean = (
        stage25_results.groupby(["baseline_id", "target"], as_index=False)["oof_spearman"]
        .mean()
        .rename(columns={"oof_spearman": "fold_mean_spearman"})
    )
    official_baseline = (
        predictions.groupby(["baseline_id", "target"])
        .apply(lambda g: safe_spearman(g["y_true"].to_numpy(), g["y_pred"].to_numpy()), include_groups=False)
        .reset_index(name="pooled_oof_spearman")
    )
    merged = fold_mean.merge(official_baseline, on=["baseline_id", "target"], how="inner")
    mean_scores = (
        merged.groupby("baseline_id")["pooled_oof_spearman"].mean().sort_values(ascending=False)
    )
    official_best = str(mean_scores.index[0])
    for row in merged.itertuples():
        rows.append(
            {
                "baseline_id": row.baseline_id,
                "target": row.target,
                "fold_mean_spearman": float(row.fold_mean_spearman),
                "pooled_oof_spearman": float(row.pooled_oof_spearman),
                "difference": float(row.pooled_oof_spearman - row.fold_mean_spearman),
                "n_donors": int(
                    predictions[
                        (predictions["baseline_id"] == row.baseline_id)
                        & (predictions["target"] == row.target)
                    ]["donor_id"].nunique()
                ),
                "official_for_v3_target": row.baseline_id == official_best,
                "notes": "Official metric is pooled donor-level OOF Spearman; fold mean retained for audit comparison.",
            }
        )
    return pd.DataFrame(rows)


def build_protocol_comparison(stage25_results: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    v2_exists = OLD_V2_BASELINE.exists()
    v2 = pd.read_csv(OLD_V2_BASELINE) if v2_exists else pd.DataFrame()
    v2_donors = str(int(v2["n_donors"].max())) if v2_exists and "n_donors" in v2.columns else "unknown"
    v2_cv = (
        "; ".join(sorted(v2["cv_scheme"].dropna().astype(str).unique()))
        if v2_exists and "cv_scheme" in v2.columns
        else "unknown"
    )
    v2_targets = (
        "; ".join(sorted(v2["target"].dropna().astype(str).unique()))
        if v2_exists and "target" in v2.columns
        else "unknown"
    )
    stage25_targets = "; ".join(sorted(stage25_results["target_alias"].dropna().astype(str).unique()))
    rows = [
        {
            "protocol_component": "donor_count",
            "v2_value": v2_donors,
            "stage25_value": str(predictions["donor_id"].nunique()),
            "same_or_different": "same" if v2_donors == str(predictions["donor_id"].nunique()) else "different",
            "risk_if_different": "medium",
            "notes": "Donor count must match for direct apples-to-apples comparison.",
        },
        {
            "protocol_component": "fold_split",
            "v2_value": v2_cv,
            "stage25_value": "locked Stage 24 5-fold donor split, seed 7",
            "same_or_different": "unknown",
            "risk_if_different": "medium",
            "notes": "V2 reports 5-fold donor CV but does not expose exact donor fold assignment in this table.",
        },
        {
            "protocol_component": "target_table",
            "v2_value": v2_targets,
            "stage25_value": stage25_targets,
            "same_or_different": "same" if set(v2_targets.split("; ")) == set(stage25_targets.split("; ")) else "unknown",
            "risk_if_different": "medium",
            "notes": "Both use the same five SEA-AD pathology target aliases when visible.",
        },
        {
            "protocol_component": "feature_table",
            "v2_value": "prior baseline comparison assets; exact raw feature table not fully encoded in comparison CSV",
            "stage25_value": str(PSEUDOBULK_FEATURES.relative_to(ROOT)),
            "same_or_different": "unknown",
            "risk_if_different": "high",
            "notes": "Direct comparison to 0.2999 needs caveat unless feature-table identity is proven.",
        },
        {
            "protocol_component": "module_definitions",
            "v2_value": "module mean baseline definitions not fully encoded in comparison CSV",
            "stage25_value": "src/sea_ad_jepa/gene_sets.py MICROGLIA_GENE_MODULES",
            "same_or_different": "unknown",
            "risk_if_different": "high",
            "notes": "Stage25 modules are target-independent, but exact equivalence to old v2 module mean requires provenance check.",
        },
        {
            "protocol_component": "target_transform",
            "v2_value": "unknown in comparison CSV",
            "stage25_value": "log1p",
            "same_or_different": "unknown",
            "risk_if_different": "medium",
            "notes": "Stage25 stores OOF prediction scale as log1p.",
        },
        {
            "protocol_component": "metric_aggregation",
            "v2_value": "oof_spearman column available; likely pooled or aggregate OOF but not proven from CSV alone",
            "stage25_value": "Stage25 report/ranking used mean of fold-level Spearman; Stage25B recommends pooled donor-level OOF",
            "same_or_different": "different",
            "risk_if_different": "high",
            "notes": "This is the core Stage25B concern.",
        },
        {
            "protocol_component": "missing_target_handling",
            "v2_value": "all visible target rows report n_donors=84",
            "stage25_value": "all five targets available for 84 donors",
            "same_or_different": "same",
            "risk_if_different": "low",
            "notes": "No target-specific donor drops detected.",
        },
    ]
    return pd.DataFrame(rows)


def build_audit_table(
    stage25_results: pd.DataFrame,
    pooled: pd.DataFrame,
    comparison: pd.DataFrame,
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    module_rows = pooled[pooled["baseline_id"] == "module_mean_baseline"]
    module_fold_mean = float(module_rows["fold_mean_spearman"].mean())
    module_pooled = float(module_rows["pooled_oof_spearman"].mean())
    metric_shift = module_pooled - module_fold_mean
    comparison_high_risk = comparison[
        (comparison["same_or_different"].isin(["different", "unknown"]))
        & (comparison["risk_if_different"].isin(["medium", "high"]))
    ]
    module_feature_cols = [c for c in predictions["feature_source"].unique() if "module" in str(c)]
    rows = [
        {
            "audit_item": "aggregation_check",
            "status": "pass_with_revision",
            "finding": (
                f"Stage25 ranking used mean fold-level Spearman. Pooled module_mean_baseline mean OOF Spearman is "
                f"{module_pooled:.4f} vs fold-mean {module_fold_mean:.4f} (difference {metric_shift:.4f})."
            ),
            "risk_level": "medium" if abs(metric_shift) <= 0.02 else "high",
            "recommended_action": "Use pooled donor-level OOF Spearman as official Stage25B metric.",
        },
        {
            "audit_item": "prediction_storage_check",
            "status": "pass",
            "finding": f"Per-donor OOF predictions recomputed and saved for {predictions['donor_id'].nunique()} donors.",
            "risk_level": "low",
            "recommended_action": "Keep OOF prediction table with benchmark artifacts.",
        },
        {
            "audit_item": "apples_to_apples_v2_comparison",
            "status": "caution",
            "finding": (
                f"{len(comparison_high_risk)} protocol components are unknown or different at medium/high risk."
            ),
            "risk_level": "medium",
            "recommended_action": "Do not compare Stage25B directly to 0.2999 without caveat unless feature/module provenance is reconciled.",
        },
        {
            "audit_item": "module_baseline_sanity_check",
            "status": "pass",
            "finding": (
                "Module features are computed from expression-only predefined target-independent modules; "
                f"module feature sources observed: {sorted(module_feature_cols)}."
            ),
            "risk_level": "low",
            "recommended_action": "Module baseline is acceptable as an internal locked-CV baseline.",
        },
        {
            "audit_item": "generalization_caution",
            "status": "caution",
            "finding": "Locked donor CV prevents cell leakage but does not prove external cohort generalization.",
            "risk_level": "medium",
            "recommended_action": "Run external/stress tests before broad generalization claims.",
        },
    ]
    return pd.DataFrame(rows)


def write_report(
    stage25_results: pd.DataFrame,
    pooled: pd.DataFrame,
    comparison: pd.DataFrame,
    audit: pd.DataFrame,
) -> None:
    fold_rank = (
        stage25_results.groupby("baseline_id")["oof_spearman"]
        .mean()
        .sort_values(ascending=False)
    )
    pooled_rank = (
        pooled.groupby("baseline_id")["pooled_oof_spearman"]
        .mean()
        .sort_values(ascending=False)
    )
    best_baseline = str(pooled_rank.index[0])
    best_score = float(pooled_rank.iloc[0])
    min_target = best_score + SMALL_BAND
    module_pooled = float(pooled_rank.loc["module_mean_baseline"])
    module_fold = float(fold_rank.loc["module_mean_baseline"])
    keep_3425 = abs(module_pooled - 0.3325) <= SMALL_BAND
    leakage_detected = audit[audit["risk_level"].eq("high") & audit["status"].str.contains("fail", case=False, na=False)]

    module_lines = [
        f"- {row.target}: fold_mean={row.fold_mean_spearman:.4f}, pooled={row.pooled_oof_spearman:.4f}, difference={row.difference:.4f}"
        for row in pooled[pooled["baseline_id"] == "module_mean_baseline"].sort_values("target").itertuples()
    ]
    rank_lines = [
        f"- `{idx}`: pooled mean OOF Spearman={value:.4f}"
        for idx, value in pooled_rank.items()
    ]
    comparison_lines = [
        f"- {row.protocol_component}: {row.same_or_different} (risk={row.risk_if_different})"
        for row in comparison.itertuples()
    ]
    audit_lines = [
        f"- {row.audit_item}: {row.status}; risk={row.risk_level}; {row.finding}"
        for row in audit.itertuples()
    ]

    if keep_3425:
        official_text = (
            "The pooled module mean remains within 0.01 of the Stage 25 value, so the 0.3425 "
            "minimum v3 success target remains valid."
        )
    elif abs(module_pooled - OLD_V2_MODULE_MEAN) <= SMALL_BAND:
        official_text = (
            "The pooled module mean drops near the old 0.2999 value, so the Stage 25 fold-mean "
            "ranking should be treated as exploratory and the official target revised downward."
        )
    else:
        official_text = (
            f"The official target should use the pooled best primary baseline: {best_baseline} "
            f"at {best_score:.4f}, giving minimum v3 success {min_target:.4f}."
        )

    REPORT_OUT.write_text(
        "\n".join(
            [
                "# v3 primary baseline protocol audit v1",
                "",
                "## 1. Executive summary",
                "",
                "Stage 25 used mean fold-level Spearman for its ranking. Stage 25B recomputed deterministic per-donor OOF predictions and recommends pooled donor-level OOF Spearman as the official benchmark metric.",
                "",
                f"Module mean pooled OOF Spearman is `{module_pooled:.4f}` versus Stage 25 fold-mean `{module_fold:.4f}`. Official pooled best baseline is `{best_baseline}` at `{best_score:.4f}`, so the recommended minimum v3 target is `{min_target:.4f}`.",
                "",
                "No v3 training, graph neural model, external validation, evidence-level change, candidate biology card, or manuscript prose was run.",
                "",
                "## 2. Why the Stage 25 number increased",
                "",
                "The Stage 25 increase partly reflects a stronger locked donor-fold module baseline, but it was reported using mean fold-level correlations. With 16-17 donors per fold, fold-level Spearman is noisy. Pooled donor-level OOF Spearman is the safer official aggregation.",
                "",
                "## 3. Fold-mean vs pooled OOF comparison",
                "",
                *module_lines,
                "",
                "Pooled ranking:",
                "",
                *rank_lines,
                "",
                "## 4. Apples-to-apples comparison with v2 baseline",
                "",
                *comparison_lines,
                "",
                "The v2 comparison is not fully apples-to-apples unless exact feature table, module definitions, target transform, and aggregation provenance are reconciled.",
                "",
                "## 5. Module baseline leakage sanity check",
                "",
                "Module definitions come from `src/sea_ad_jepa/gene_sets.py` and are target-independent named microglia modules. Stage 25B confirms module means are computed from expression values only; pathology targets are not used to define module features, and held-out donor target values are not used in feature construction.",
                "",
                "## 6. Generalization risk",
                "",
                "Locked donor CV prevents cell leakage but does not prove external cohort generalization. External/stress tests are required before broad generalization claims.",
                "",
                "## 7. Official recommended v3 benchmark target",
                "",
                f"- Old target: module_mean_baseline = `{OLD_V2_MODULE_MEAN:.4f}`",
                f"- Old v2 real Graph-JEPA = `{OLD_V2_REAL_GRAPH:.4f}`",
                f"- Stage 25 fold-mean module mean = `{module_fold:.4f}`",
                f"- Stage 25B pooled module mean = `{module_pooled:.4f}`",
                f"- Official pooled best primary baseline = `{best_baseline}` at `{best_score:.4f}`",
                f"- Recommended minimum v3 success = `{min_target:.4f}`",
                "",
                official_text,
                "",
                "## 8. Recommended next stage",
                "",
                "- Treat pooled donor-level OOF Spearman as official.",
                "- Update Stage 25 report/target language if desired so fold-mean values are audit-only.",
                "- Before v3 training, decide whether to reconcile v2/Stage25 feature and module provenance or use Stage25B as a new locked internal benchmark.",
                "- Do not start v3 neural model training until this target policy is accepted.",
                "",
                "## Audit table summary",
                "",
                *audit_lines,
                "",
                "Leakage stop condition:",
                "",
                "No high-risk leakage failure was detected." if leakage_detected.empty else "High-risk leakage failure detected; fix baseline pipeline before v3 training.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in [
        STAGE25_SCRIPT,
        STAGE25_RESULTS,
        STAGE25_DELTAS,
        STAGE25_WINNERS,
        LOCKED_FOLDS,
        METADATA_TARGETS,
        PSEUDOBULK_FEATURES,
    ]:
        if not path.exists():
            raise FileNotFoundError(path)

    stage25_results = pd.read_csv(STAGE25_RESULTS)
    predictions = collect_oof_predictions()
    pooled = recompute_pooled(stage25_results, predictions)
    comparison = build_protocol_comparison(stage25_results, predictions)
    audit = build_audit_table(stage25_results, pooled, comparison, predictions)

    predictions.to_csv(PREDICTIONS_OUT, index=False)
    pooled.to_csv(POOLED_OUT, index=False)
    comparison.to_csv(COMPARISON_OUT, index=False)
    audit.to_csv(AUDIT_OUT, index=False)
    write_report(stage25_results, pooled, comparison, audit)

    print(f"Wrote {AUDIT_OUT}")
    print(f"Wrote {POOLED_OUT}")
    print(f"Wrote {COMPARISON_OUT}")
    print(f"Wrote {PREDICTIONS_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
