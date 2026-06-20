"""Establish v3 generalization and stability gates.

Stage 26 defines robustness gates around the official pooled donor-level OOF
metric from Stage 25B. It does not train v3, run graph neural models, run
external validation, alter evidence levels, create biology cards, or write
manuscript prose.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

POOLED_IN = TABLE_DIR / "v3_primary_baseline_pooled_oof_recompute_v1.csv"
PRED_IN = TABLE_DIR / "v3_primary_baseline_oof_predictions_v1.csv"
AUDIT_IN = TABLE_DIR / "v3_primary_baseline_protocol_audit_v1.csv"
FOLDS_IN = TABLE_DIR / "v3_locked_donor_folds_v1.csv"
TARGETS_IN = TABLE_DIR / "v3_benchmark_target_manifest_v1.csv"
METADATA_IN = TABLE_DIR / "sea_ad_full_metadata_targets_with_covariates.csv"

GATES_OUT = TABLE_DIR / "v3_generalization_gate_definitions_v1.csv"
BOOT_OUT = TABLE_DIR / "v3_primary_baseline_bootstrap_uncertainty_v1.csv"
STRATUM_OUT = TABLE_DIR / "v3_primary_baseline_stratum_stability_v1.csv"
TARGET_STABILITY_OUT = TABLE_DIR / "v3_primary_baseline_target_stability_v1.csv"
REPORT_OUT = REPORT_DIR / "v3_generalization_stability_gates_v1.md"

SEED = 7
N_BOOTSTRAP = 1000
MIN_BOOTSTRAP = 500
MODULE_BASELINE = "module_mean_baseline"
OFFICIAL_MARGIN = 0.01
MAX_TARGET_DEGRADATION = 0.02
MIN_STRATUM_N = 8


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return 0.0
    value = spearmanr(y_true, y_pred).statistic
    return 0.0 if pd.isna(value) else float(value)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    for path in [POOLED_IN, PRED_IN, AUDIT_IN, FOLDS_IN, TARGETS_IN, METADATA_IN]:
        if not path.exists():
            raise FileNotFoundError(path)
    return (
        pd.read_csv(POOLED_IN),
        pd.read_csv(PRED_IN),
        pd.read_csv(AUDIT_IN),
        pd.read_csv(FOLDS_IN),
        pd.read_csv(TARGETS_IN),
        pd.read_csv(METADATA_IN),
    )


def bootstrap_target(pred: pd.DataFrame, rng: np.random.Generator, n_bootstrap: int) -> np.ndarray:
    donors = pred["donor_id"].astype(str).unique()
    by_donor = pred.set_index("donor_id")
    values = []
    for _ in range(n_bootstrap):
        sampled = rng.choice(donors, size=len(donors), replace=True)
        boot = by_donor.loc[sampled]
        values.append(safe_spearman(boot["y_true"].to_numpy(), boot["y_pred"].to_numpy()))
    return np.asarray(values, dtype=float)


def build_bootstrap_uncertainty(pooled: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n_boot = max(MIN_BOOTSTRAP, N_BOOTSTRAP)
    rows: list[dict[str, object]] = []
    target_boot: dict[tuple[str, str], np.ndarray] = {}

    for (baseline_id, target), group in predictions.groupby(["baseline_id", "target"], sort=True):
        vals = bootstrap_target(group, rng, n_boot)
        target_boot[(baseline_id, target)] = vals
        pooled_row = pooled[(pooled["baseline_id"] == baseline_id) & (pooled["target"] == target)].iloc[0]
        rows.append(
            {
                "baseline_id": baseline_id,
                "target": target,
                "pooled_oof_spearman": float(pooled_row["pooled_oof_spearman"]),
                "bootstrap_mean": float(np.mean(vals)),
                "ci_lower": float(np.quantile(vals, 0.025)),
                "ci_upper": float(np.quantile(vals, 0.975)),
                "n_bootstrap": int(n_boot),
                "n_donors": int(group["donor_id"].nunique()),
                "notes": "Donor bootstrap over pooled OOF predictions.",
            }
        )

    for baseline_id in sorted(predictions["baseline_id"].unique()):
        baseline_targets = sorted(predictions.loc[predictions["baseline_id"] == baseline_id, "target"].unique())
        matrix = np.vstack([target_boot[(baseline_id, target)] for target in baseline_targets])
        mean_vals = matrix.mean(axis=0)
        pooled_mean = float(
            pooled.loc[pooled["baseline_id"] == baseline_id, "pooled_oof_spearman"].mean()
        )
        rows.append(
            {
                "baseline_id": baseline_id,
                "target": "mean_across_targets",
                "pooled_oof_spearman": pooled_mean,
                "bootstrap_mean": float(np.mean(mean_vals)),
                "ci_lower": float(np.quantile(mean_vals, 0.025)),
                "ci_upper": float(np.quantile(mean_vals, 0.975)),
                "n_bootstrap": int(n_boot),
                "n_donors": int(predictions.loc[predictions["baseline_id"] == baseline_id, "donor_id"].nunique()),
                "notes": "Mean across target-specific donor bootstrap samples.",
            }
        )
    return pd.DataFrame(rows)


def build_target_stability(pooled: pd.DataFrame) -> pd.DataFrame:
    module = pooled[pooled["baseline_id"] == MODULE_BASELINE].set_index("target")["pooled_oof_spearman"]
    rows = []
    for baseline_id, group in pooled.groupby("baseline_id", sort=True):
        target_group = group[group["target"] != "mean_across_targets"].copy()
        scores = target_group.set_index("target")["pooled_oof_spearman"]
        worst_target = str(scores.idxmin())
        best_target = str(scores.idxmax())
        min_delta_vs_module = min(float(scores[target] - module[target]) for target in scores.index if target in module.index)
        passes = bool(min_delta_vs_module >= -MAX_TARGET_DEGRADATION)
        if baseline_id == MODULE_BASELINE:
            passes = True
        rows.append(
            {
                "baseline_id": baseline_id,
                "mean_pooled_oof_spearman": float(scores.mean()),
                "worst_target": worst_target,
                "worst_target_spearman": float(scores.loc[worst_target]),
                "best_target": best_target,
                "best_target_spearman": float(scores.loc[best_target]),
                "target_spread": float(scores.max() - scores.min()),
                "passes_target_stability_gate": passes,
                "notes": (
                    f"Minimum target delta versus module baseline={min_delta_vs_module:.4f}; "
                    f"future v3 may not degrade any target by more than {MAX_TARGET_DEGRADATION:.2f}."
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("mean_pooled_oof_spearman", ascending=False)


def derive_pathology_stratum(metadata: pd.DataFrame) -> pd.Series:
    if "Overall AD neuropathological Change" in metadata.columns:
        return metadata["Overall AD neuropathological Change"].fillna("unknown").astype(str).replace("", "unknown")
    cols = [c for c in ["Braak", "Thal", "CERAD score"] if c in metadata.columns]
    if cols:
        return metadata[cols].fillna("unknown").astype(str).agg("|".join, axis=1)
    return pd.Series(["unknown"] * len(metadata), index=metadata.index)


def build_stratum_stability(predictions: pd.DataFrame, metadata: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    meta = metadata.drop_duplicates("Donor ID").copy()
    meta["donor_id"] = meta["Donor ID"].astype(str)
    meta["diagnosis"] = meta.get("Cognitive Status", "unknown")
    meta["sex"] = meta.get("Sex", "unknown")
    meta["pathology_stratum"] = derive_pathology_stratum(meta)
    fold_meta = folds[["donor_id", "pathology_stratum"]].rename(columns={"pathology_stratum": "locked_fold_pathology_stratum"})
    meta = meta.merge(fold_meta, on="donor_id", how="left")
    merged = predictions.merge(meta, on="donor_id", how="left")
    rows = []
    stratum_specs = [
        ("diagnosis", "diagnosis"),
        ("sex", "sex"),
        ("pathology_stratum", "pathology_stratum"),
        ("locked_fold_pathology_stratum", "locked_fold_pathology_stratum"),
    ]
    for (baseline_id, target), base_group in merged.groupby(["baseline_id", "target"], sort=True):
        for var, col in stratum_specs:
            if col not in base_group.columns:
                continue
            for value, group in base_group.groupby(col, dropna=False, sort=True):
                n = int(group["donor_id"].nunique())
                underpowered = n < MIN_STRATUM_N
                if underpowered:
                    metric = float(np.mean(np.abs(group["y_true"] - group["y_pred"])))
                    notes = f"Underpowered stratum; reporting MAE on log1p scale because n<{MIN_STRATUM_N}."
                else:
                    metric = safe_spearman(group["y_true"].to_numpy(), group["y_pred"].to_numpy())
                    notes = "Pooled stratum Spearman on log1p OOF predictions."
                rows.append(
                    {
                        "baseline_id": baseline_id,
                        "target": target,
                        "stratum_variable": var,
                        "stratum_value": "missing" if pd.isna(value) else str(value),
                        "n_donors": n,
                        "pooled_spearman_or_error_metric": metric,
                        "underpowered": underpowered,
                        "notes": notes,
                    }
                )
    return pd.DataFrame(rows)


def build_gate_definitions(official_target: float, module_score: float) -> pd.DataFrame:
    gates = [
        {
            "gate_id": "pooled_oof_required",
            "gate_name": "Pooled donor-level OOF metric required",
            "gate_description": "Future v3 comparisons must use pooled donor-level out-of-fold Spearman, not mean fold-level Spearman.",
            "required_for_v3_success": True,
            "threshold": "pooled donor-level OOF Spearman reported for every target",
            "rationale": "Fold-level correlations are noisy with 16-17 donors per fold.",
            "failure_action": "Do not claim v3 improvement; recompute pooled OOF predictions.",
            "notes": "Stage 25B superseded the 0.3425 fold-mean-derived target.",
        },
        {
            "gate_id": "beat_module_mean_by_0p01",
            "gate_name": "Beat module mean by 0.01",
            "gate_description": "v3 must exceed the official module_mean_baseline pooled mean OOF Spearman by at least 0.01.",
            "required_for_v3_success": True,
            "threshold": f">= {official_target:.4f} mean pooled OOF Spearman",
            "rationale": f"Official module baseline is {module_score:.4f}; small-difference band is 0.01.",
            "failure_action": "Treat v3 as not improved over primary module baseline.",
            "notes": "Internal benchmark target only; not external validation.",
        },
        {
            "gate_id": "no_large_target_degradation",
            "gate_name": "No large target degradation",
            "gate_description": "v3 must not degrade more than 0.02 pooled OOF Spearman on any individual target versus module_mean_baseline.",
            "required_for_v3_success": True,
            "threshold": "target_delta_vs_module_mean >= -0.02 for every target",
            "rationale": "Mean improvement can hide target-specific failure.",
            "failure_action": "Report target failure and do not treat v3 as a global improvement.",
            "notes": "All five targets remain required: AT8, 6e10/Aβ, GFAP, Iba1, NeuN.",
        },
        {
            "gate_id": "bootstrap_uncertainty_reported",
            "gate_name": "Bootstrap uncertainty reported",
            "gate_description": "Future v3 results must include donor bootstrap uncertainty for target-level and mean pooled OOF Spearman.",
            "required_for_v3_success": True,
            "threshold": ">=500 donor bootstrap resamples; 1000 preferred",
            "rationale": "n donors = 84 and uncertainty is nontrivial.",
            "failure_action": "Mark result incomplete until uncertainty is reported.",
            "notes": "Improvement should exceed bootstrap uncertainty where possible.",
        },
        {
            "gate_id": "target_specific_performance_required",
            "gate_name": "Target-specific performance required",
            "gate_description": "Future v3 reports must include target-specific performance, worst target, best target, and spread.",
            "required_for_v3_success": True,
            "threshold": "all five target metrics reported",
            "rationale": "No target dropping or mean-only reporting after seeing results.",
            "failure_action": "Reject benchmark summary as incomplete.",
            "notes": "No threshold changes after results.",
        },
        {
            "gate_id": "graph_controls_required",
            "gate_name": "Graph controls required",
            "gate_description": "v3 must pass no-graph and strict-shuffled graph controls before graph-specific benefit is claimed.",
            "required_for_v3_success": True,
            "threshold": "real graph > no-graph and strict-shuffled under pooled OOF gate",
            "rationale": "Graph-specific benefit must survive topology controls.",
            "failure_action": "Do not claim graph-specific improvement.",
            "notes": "Run after minimal non-graph v3 predictor is established.",
        },
        {
            "gate_id": "stratum_reporting_required_if_powered",
            "gate_name": "Stratum reporting if powered",
            "gate_description": "Report diagnosis, sex, and pathology-stratum performance when strata are powered.",
            "required_for_v3_success": True,
            "threshold": f"report strata with n>={MIN_STRATUM_N}; mark smaller strata underpowered",
            "rationale": "Internal donor CV does not guarantee subgroup stability.",
            "failure_action": "Add stratum report or mark underpowered strata explicitly.",
            "notes": "Do not overinterpret small strata.",
        },
        {
            "gate_id": "no_external_generalization_claim_without_external_validation",
            "gate_name": "No external generalization claim without external validation",
            "gate_description": "v3 may not claim broad external generalization from internal SEA-AD donor CV alone.",
            "required_for_v3_success": True,
            "threshold": "external validation required for external-generalization claims",
            "rationale": "Internal donor CV prevents cell leakage but is not an external cohort test.",
            "failure_action": "Limit claims to internal locked-CV performance.",
            "notes": "External validation remains future work.",
        },
        {
            "gate_id": "anti_overfitting_controls",
            "gate_name": "Anti-overfitting controls",
            "gate_description": "Model selection must not use test-fold labels; no target dropping or threshold changes after results.",
            "required_for_v3_success": True,
            "threshold": "predeclared model-selection protocol only",
            "rationale": "n donors = 84 and high-capacity models require stricter controls.",
            "failure_action": "Invalidate affected benchmark and rerun from locked protocol.",
            "notes": "Applies to neural and high-capacity non-neural models.",
        },
    ]
    return pd.DataFrame(gates)


def write_report(
    gates: pd.DataFrame,
    boot: pd.DataFrame,
    stratum: pd.DataFrame,
    target_stability: pd.DataFrame,
    audit: pd.DataFrame,
) -> None:
    module_mean = boot[(boot["baseline_id"] == MODULE_BASELINE) & (boot["target"] == "mean_across_targets")].iloc[0]
    official_target = float(module_mean["pooled_oof_spearman"]) + OFFICIAL_MARGIN
    top_boot = (
        boot[boot["target"] == "mean_across_targets"]
        .sort_values("pooled_oof_spearman", ascending=False)
        .head(5)
    )
    top_lines = [
        f"- `{row.baseline_id}`: pooled={row.pooled_oof_spearman:.4f}, CI=({row.ci_lower:.4f}, {row.ci_upper:.4f})"
        for row in top_boot.itertuples()
    ]
    module_target_lines = [
        f"- {row.target}: pooled={row.pooled_oof_spearman:.4f}, CI=({row.ci_lower:.4f}, {row.ci_upper:.4f})"
        for row in boot[(boot["baseline_id"] == MODULE_BASELINE) & (boot["target"] != "mean_across_targets")]
        .sort_values("target")
        .itertuples()
    ]
    stability_lines = [
        f"- `{row.baseline_id}`: mean={row.mean_pooled_oof_spearman:.4f}, worst={row.worst_target} ({row.worst_target_spearman:.4f}), best={row.best_target} ({row.best_target_spearman:.4f}), spread={row.target_spread:.4f}, passes={row.passes_target_stability_gate}"
        for row in target_stability.head(10).itertuples()
    ]
    underpowered_count = int(stratum["underpowered"].sum())
    powered = stratum[~stratum["underpowered"]]
    stratum_summary = (
        powered.groupby(["baseline_id", "stratum_variable"], as_index=False)["pooled_spearman_or_error_metric"]
        .mean()
        .sort_values(["baseline_id", "stratum_variable"])
    )
    stratum_lines = [
        f"- `{row.baseline_id}` / {row.stratum_variable}: mean powered-stratum metric={row.pooled_spearman_or_error_metric:.4f}"
        for row in stratum_summary.head(20).itertuples()
    ]
    gate_lines = [
        f"- `{row.gate_id}`: {row.threshold}"
        for row in gates.itertuples()
    ]
    audit_lines = [
        f"- {row.audit_item}: {row.status}; risk={row.risk_level}"
        for row in audit.itertuples()
    ]

    REPORT_OUT.write_text(
        "\n".join(
            [
                "# v3 generalization and stability gates v1",
                "",
                "## 1. Executive summary",
                "",
                f"Stage 26 establishes robustness gates around the Stage 25B official pooled donor-level OOF metric. The official internal benchmark remains `module_mean_baseline` at pooled mean OOF Spearman `{module_mean.pooled_oof_spearman:.4f}`; the minimum internal v3 success target is `{official_target:.4f}`.",
                "",
                "No v3 training, graph neural model, external validation, evidence-level change, candidate biology card, or manuscript prose was run.",
                "",
                "## 2. Official v3 benchmark target",
                "",
                f"- Official metric: pooled donor-level OOF Spearman.",
                f"- Module baseline pooled mean OOF Spearman: `{module_mean.pooled_oof_spearman:.4f}`.",
                f"- Required margin: `+{OFFICIAL_MARGIN:.2f}`.",
                f"- Minimum internal v3 success target: `{official_target:.4f}`.",
                "",
                "## 3. Why fold-mean metric was superseded",
                "",
                "Stage 25 used mean fold-level Spearman, which is noisy with approximately 16-17 held-out donors per fold. Stage 25B recomputed per-donor pooled OOF Spearman and superseded the fold-mean-derived 0.3425 target.",
                "",
                "## 4. Bootstrap uncertainty",
                "",
                "Top mean-across-target bootstrap intervals:",
                "",
                *top_lines,
                "",
                "Module baseline target-level bootstrap intervals:",
                "",
                *module_target_lines,
                "",
                "## 5. Target-specific stability",
                "",
                *stability_lines,
                "",
                "Future v3 must report all five targets and must not hide a target-specific degradation behind a higher mean.",
                "",
                "## 6. Stratum stability",
                "",
                f"Stratum rows generated: `{len(stratum)}`; underpowered rows: `{underpowered_count}`. Underpowered strata report log1p-scale MAE rather than Spearman and should not be overinterpreted.",
                "",
                *stratum_lines,
                "",
                "## 7. Generalization gates for future v3",
                "",
                *gate_lines,
                "",
                "## 8. Anti-overfitting rules",
                "",
                "- n donors = 84.",
                "- Internal donor CV is not external validation.",
                "- High-capacity models require stricter gates.",
                "- Model selection must not use test-fold labels.",
                "- No target dropping after results.",
                "- No threshold changes after results.",
                "- No external generalization claim without external validation.",
                "",
                "## 9. Recommended Stage 27 plan",
                "",
                "- Implement a minimal non-graph v3 predictor first: module branch + expression residual branch + target-specific heads.",
                "- Compare it against module_mean_baseline, raw_expression_ridge, and pca_elasticnet.",
                "- Use pooled donor-level OOF only.",
                "- Only after that add typed graph branches and graph controls.",
                "",
                "## Protocol audit carry-forward",
                "",
                *audit_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pooled, predictions, audit, folds, targets, metadata = load_inputs()
    boot = build_bootstrap_uncertainty(pooled, predictions)
    target_stability = build_target_stability(pooled)
    stratum = build_stratum_stability(predictions, metadata, folds)
    module_mean = float(
        boot[(boot["baseline_id"] == MODULE_BASELINE) & (boot["target"] == "mean_across_targets")][
            "pooled_oof_spearman"
        ].iloc[0]
    )
    gates = build_gate_definitions(module_mean + OFFICIAL_MARGIN, module_mean)

    gates.to_csv(GATES_OUT, index=False)
    boot.to_csv(BOOT_OUT, index=False)
    stratum.to_csv(STRATUM_OUT, index=False)
    target_stability.to_csv(TARGET_STABILITY_OUT, index=False)
    write_report(gates, boot, stratum, target_stability, audit)

    print(f"Wrote {GATES_OUT}")
    print(f"Wrote {BOOT_OUT}")
    print(f"Wrote {STRATUM_OUT}")
    print(f"Wrote {TARGET_STABILITY_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
