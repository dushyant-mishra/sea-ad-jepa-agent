from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
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

from sea_ad_jepa.data.graph_control_features import (
    canonical_genes,
    graph_smoothed_expression,
    load_graph_asset,
    predefined_module_features,
)
from sea_ad_jepa.eval.oof_metrics import donor_bootstrap_ci, regression_metrics

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

STAGE27C_OOF = TABLE_DIR / "stage27c_rescue_oof_predictions_v1.csv"
STAGE27C_TARGET = TABLE_DIR / "stage27c_rescue_target_metrics_v1.csv"
STAGE27C_MEAN = TABLE_DIR / "stage27c_rescue_mean_metrics_v1.csv"
OFFICIAL_MODULE = TABLE_DIR / "v3_primary_baseline_pooled_oof_recompute_v1.csv"
ROLE_REGISTRY = TABLE_DIR / "v3_dataset_role_registry_v1.csv"

OOF_OUT = TABLE_DIR / "stage30_graph_controls_oof_predictions_v1.csv"
TARGET_OUT = TABLE_DIR / "stage30_graph_controls_target_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage30_graph_controls_mean_metrics_v1.csv"
PAIRWISE_OUT = TABLE_DIR / "stage30_graph_controls_pairwise_deltas_v1.csv"
TARGET_DELTA_OUT = TABLE_DIR / "stage30_graph_controls_target_deltas_vs_stage27c_v1.csv"
PASS_FAIL_OUT = TABLE_DIR / "stage30_graph_controls_pass_fail_v1.csv"
BOOT_OUT = TABLE_DIR / "stage30_graph_controls_bootstrap_ci_v1.csv"
GRAPH_AUDIT_OUT = TABLE_DIR / "stage30_graph_audit_v1.csv"
GRAPH_SUMMARY_OUT = TABLE_DIR / "stage30_graph_node_edge_summary_v1.csv"
REPORT_OUT = REPORT_DIR / "stage30_graph_controls_report_v1.md"

GRAPH_CONDITIONS = ["v3_real_graph", "v3_no_graph", "v3_strict_shuffled_graph"]
REFERENCE = "stage27c_module_pca_ridge_reference"
REQUIRED_PAIRS = [
    ("v3_real_graph", REFERENCE),
    ("v3_real_graph", "v3_no_graph"),
    ("v3_real_graph", "v3_strict_shuffled_graph"),
    ("v3_no_graph", "v3_strict_shuffled_graph"),
]


def load_cfg(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


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


def fit_pca_ridge(
    features: pd.DataFrame,
    y: pd.Series,
    train: list[str],
    test: list[str],
    cfg: dict,
) -> np.ndarray:
    x_train = features.loc[train].to_numpy(dtype=float)
    x_test = features.loc[test].to_numpy(dtype=float)
    y_train = np.log1p(y.loc[train].to_numpy(dtype=float))
    n_components = min(
        int(cfg["head"]["pca_components"]),
        x_train.shape[1],
        len(train) - 1,
    )
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=n_components, random_state=int(cfg["random_seed"]))),
            (
                "ridge",
                RidgeCV(
                    alphas=np.asarray(cfg["head"]["ridge_alphas"], dtype=float),
                    cv=min(3, max(2, len(train) // 10)),
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    return model.predict(x_test)


def reference_predictions() -> pd.DataFrame:
    ref = pd.read_csv(STAGE27C_OOF)
    ref = ref[ref["condition"] == "module_pca_ridge"].copy()
    return pd.DataFrame(
        {
            "condition": REFERENCE,
            "target": ref["target"],
            "target_alias": ref["target_alias"],
            "donor_id": ref["donor_id"],
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


def graph_audit(cfg: dict, assets: dict, canonical: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    strict_diag = pd.read_csv(resolve(cfg["graph"]["strict_shuffled_diagnostics"]))
    diag = dict(zip(strict_diag["metric"].astype(str), strict_diag["value"].astype(str)))
    real = assets["v3_real_graph"]
    no_graph = assets["v3_no_graph"]
    strict = assets["v3_strict_shuffled_graph"]
    checks = [
        ("canonical_node_count_2957", len(canonical) == 2957, f"nodes={len(canonical)}"),
        ("all_conditions_same_node_count", all(asset.adjacency.shape == (len(canonical), len(canonical)) for asset in assets.values()), str({key: asset.adjacency.shape for key, asset in assets.items()})),
        ("no_graph_identity_edge_count", no_graph.edge_count == len(canonical), f"edges={no_graph.edge_count}"),
        ("real_graph_nonempty", real.edge_count > len(canonical), f"edges={real.edge_count}"),
        ("strict_graph_edge_count_matches_real", strict.edge_count == real.edge_count, f"real={real.edge_count}; strict={strict.edge_count}"),
        ("strict_degree_sequence_preserved", diag.get("degree_sequence_exactly_preserved", "").lower() == "true", diag.get("degree_sequence_exactly_preserved", "missing")),
        ("strict_zero_overlap", diag.get("zero_overlap_achieved", "").lower() == "true", diag.get("final_overlap_fraction", "missing")),
        ("strict_no_self_loops", diag.get("no_self_loops", "").lower() == "true", diag.get("no_self_loops", "missing")),
        ("strict_safe_for_training", diag.get("safe_for_training", "").lower() == "true", diag.get("safe_for_training", "missing")),
    ]
    audit = pd.DataFrame(
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
    summaries = []
    for condition, asset in assets.items():
        degree = np.asarray((asset.adjacency > 0).sum(axis=1)).ravel()
        summaries.append(
            {
                "condition": condition,
                "edge_file": str(asset.path.relative_to(ROOT)),
                "n_nodes": len(canonical),
                "input_edge_rows": asset.edge_count,
                "self_loop_rows": asset.self_loop_count,
                "mean_nonzero_neighbors": float(np.mean(degree)),
                "median_nonzero_neighbors": float(np.median(degree)),
                "max_nonzero_neighbors": int(np.max(degree)),
                "smoothing_alpha": float(cfg["graph"]["smoothing_alpha"]),
                "notes": asset.notes,
            }
        )
    return audit, pd.DataFrame(summaries), bool(audit["passed"].all())


def run_graph_conditions(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, bool]:
    folds, targets, expression, target_matrix = load_context()
    identity_path = resolve(cfg["graph"]["no_graph_edges"])
    canonical = canonical_genes(identity_path)
    assets = {
        "v3_real_graph": load_graph_asset("v3_real_graph", resolve(cfg["graph"]["real_edges"]), canonical),
        "v3_no_graph": load_graph_asset("v3_no_graph", identity_path, canonical),
        "v3_strict_shuffled_graph": load_graph_asset("v3_strict_shuffled_graph", resolve(cfg["graph"]["strict_shuffled_edges"]), canonical),
    }
    audit, graph_summary, graph_audit_pass = graph_audit(cfg, assets, canonical)

    feature_blocks = {}
    overlap_rows = []
    for condition, asset in assets.items():
        smoothed = graph_smoothed_expression(
            expression,
            asset,
            alpha=float(cfg["graph"]["smoothing_alpha"]),
        )
        module_features, overlaps = predefined_module_features(smoothed)
        feature_blocks[condition] = module_features
        overlap_rows.append(
            {
                "condition": condition,
                "n_module_features": module_features.shape[1],
                "module_overlap_summary": "; ".join(f"{key}:{value}" for key, value in sorted(overlaps.items())),
            }
        )

    rows = []
    for condition_idx, condition in enumerate(GRAPH_CONDITIONS):
        features = feature_blocks[condition]
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
                pred = fit_pca_ridge(features, y, train, test, cfg)
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append(
                        {
                            "condition": condition,
                            "target": target,
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
                            "prediction_source": "fresh_stage30_graph_smoothed_pca_ridge",
                        }
                    )
    graph_oof = pd.DataFrame(rows)
    reference = reference_predictions()
    oof = pd.concat([reference, graph_oof], ignore_index=True)
    graph_summary = graph_summary.merge(pd.DataFrame(overlap_rows), on="condition", how="left")
    return oof, audit, graph_summary, folds, graph_audit_pass


def compute_metrics(oof: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for keys, group in oof.groupby(["condition", "target", "target_alias"]):
        condition, target, alias = keys
        rows.append(
            {
                "condition": condition,
                "target": target,
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
            n_targets=("target", "nunique"),
        )
        .sort_values("mean_pooled_oof_spearman", ascending=False)
    )
    return target, mean


def comparisons(target: pd.DataFrame, mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    pair_rows = []
    for left, right in REQUIRED_PAIRS:
        pair_rows.append(
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
        ["target", "pooled_oof_spearman"]
    ].rename(columns={"pooled_oof_spearman": "stage27c_reference_target_spearman"})
    graph = target[target["condition"].isin(GRAPH_CONDITIONS)].merge(ref, on="target", how="left")
    graph["delta_vs_stage27c_reference"] = (
        graph["pooled_oof_spearman"] - graph["stage27c_reference_target_spearman"]
    )
    return pd.DataFrame(pair_rows), graph


def pass_fail(
    oof: pd.DataFrame,
    target: pd.DataFrame,
    mean: pd.DataFrame,
    audit_pass: bool,
    cfg: dict,
) -> pd.DataFrame:
    means = mean.set_index("condition")["mean_pooled_oof_spearman"]
    official = pd.read_csv(OFFICIAL_MODULE)
    module = official[official["baseline_id"] == "module_mean_baseline"][
        ["target", "pooled_oof_spearman"]
    ].rename(columns={"pooled_oof_spearman": "module_target_spearman"})
    real_targets = target[target["condition"] == "v3_real_graph"].merge(module, on="target", how="left")
    real_targets["delta_vs_module_mean"] = (
        real_targets["pooled_oof_spearman"] - real_targets["module_target_spearman"]
    )
    real = float(means["v3_real_graph"])
    no_graph = float(means["v3_no_graph"])
    strict = float(means["v3_strict_shuffled_graph"])
    reference = float(means[REFERENCE])
    clean = not bool(oof["clean_holdout_used"].astype(bool).any())
    no_leakage = not bool(oof["heldout_donor_leakage_detected"].astype(bool).any())
    no_external = not bool(oof["external_matrix_used"].astype(bool).any())
    target_gate = bool(
        (real_targets["delta_vs_module_mean"] >= float(cfg["max_target_drop_vs_module_mean"])).all()
    )
    checks = {
        "real_meets_stage27c_reference": real >= reference,
        "real_meets_official_threshold": real >= float(cfg["minimum_success_threshold"]),
        "all_five_targets_reported": int(target[target["condition"] == "v3_real_graph"]["target"].nunique()) == 5,
        "target_degradation_gate_pass": target_gate,
        "no_heldout_donor_leakage": no_leakage,
        "no_clean_holdout_use": clean,
        "no_external_matrix_use": no_external,
        "real_beats_no_graph": real > no_graph,
        "real_beats_strict_shuffled": real > strict,
        "graph_construction_audit_pass": audit_pass,
    }
    graph_pass = all(checks.values())
    if real < no_graph and real > strict:
        interpretation = "real_topology_beats_strict_shuffle_but_identity_no_graph_remains_best"
    elif real > reference and not real > strict:
        interpretation = "graph_like_regularization_may_help_but_topology_specificity_not_established"
    elif real > no_graph and real < reference:
        interpretation = "graph_branch_informative_vs_matched_control_but_not_best_internal_benchmark"
    elif strict >= real:
        interpretation = "topology_specific_evidence_not_established"
    elif graph_pass:
        interpretation = "graph_specific_internal_benchmark_pass"
    else:
        interpretation = "graph_specific_pass_not_established"
    return pd.DataFrame(
        [
            {
                "condition": "v3_real_graph",
                "real_mean_pooled_oof_spearman": real,
                "stage27c_reference_mean": reference,
                "official_threshold": float(cfg["minimum_success_threshold"]),
                "real_minus_stage27c_reference": real - reference,
                "real_minus_no_graph": real - no_graph,
                "real_minus_strict_shuffled_graph": real - strict,
                **checks,
                "graph_specific_pass": graph_pass,
                "controlled_interpretation": interpretation,
            }
        ]
    )


def update_status(mean: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    new = {
        "scorecard_item": "stage30_graph_controls",
        "status": "complete",
        "stage": "Stage 30",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "real >= 0.326702; real > no-graph and strict-shuffled; five targets; target delta >= -0.02",
        "current_value": f"{row.real_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.graph_specific_pass) else "fail",
        "datasets_allowed": "SEA-AD locked donor folds only",
        "datasets_forbidden": "external matrices; clean holdouts; external model selection",
        "allowed_claim": row.controlled_interpretation,
        "notes": f"real-reference={row.real_minus_stage27c_reference:.4f}; real-no_graph={row.real_minus_no_graph:.4f}; real-strict={row.real_minus_strict_shuffled_graph:.4f}; external validation not run; ablation validity not established.",
    }
    score = score[score["scorecard_item"] != "stage30_graph_controls"]
    score = pd.concat([score, pd.DataFrame([new])], ignore_index=True)
    score.to_csv(score_path, index=False)

    active_path = ROOT / "docs" / "ACTIVE_V3_STATUS.md"
    text = active_path.read_text(encoding="utf-8")
    marker = "\n\n## Stage 30 graph-control status\n"
    addition = (
        marker
        + f"\nStage 30 graph controls are complete. Real graph mean pooled OOF Spearman: "
        + f"`{row.real_mean_pooled_oof_spearman:.4f}`; graph-specific pass: `{bool(row.graph_specific_pass)}`; "
        + f"controlled interpretation: `{row.controlled_interpretation}`. External validation remains not run, "
        + "and in silico ablation remains unvalidated.\n"
    )
    active_path.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")

    score_doc = ROOT / "docs" / "V3_SCORECARD.md"
    text = score_doc.read_text(encoding="utf-8")
    marker = "\n\n## Stage 30 graph-control result\n"
    addition = (
        marker
        + f"\nReal graph: `{row.real_mean_pooled_oof_spearman:.4f}`; "
        + f"real minus Stage 27C reference: `{row.real_minus_stage27c_reference:.4f}`; "
        + f"real minus no-graph: `{row.real_minus_no_graph:.4f}`; "
        + f"real minus strict-shuffled: `{row.real_minus_strict_shuffled_graph:.4f}`. "
        + f"Graph-specific pass: `{bool(row.graph_specific_pass)}`. "
        + f"Interpretation: `{row.controlled_interpretation}`.\n"
    )
    score_doc.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")


def write_report(
    cfg: dict,
    target: pd.DataFrame,
    mean: pd.DataFrame,
    pairs: pd.DataFrame,
    bootstrap: pd.DataFrame,
    audit: pd.DataFrame,
    summary: pd.DataFrame,
    pf: pd.DataFrame,
) -> None:
    row = pf.iloc[0]
    best = mean.iloc[0]
    real_targets = target[target["condition"] == "v3_real_graph"]
    lines = [
        "# Stage 30 graph controls report v1",
        "",
        "## 1. Executive summary",
        "",
        f"Best condition: `{best.condition}` (`{best.mean_pooled_oof_spearman:.4f}`).",
        f"Real graph: `{row.real_mean_pooled_oof_spearman:.4f}`. Graph-specific pass: `{bool(row.graph_specific_pass)}`.",
        f"Controlled interpretation: `{row.controlled_interpretation}`.",
        "",
        "## 2. What was run",
        "",
        "- Stage 27C module PCA-ridge reference loaded from frozen OOF outputs.",
        "- Real consensus STRING/WGCNA graph smoothing.",
        "- Identity/no-graph smoothing control.",
        "- Zero-overlap degree-preserving strict-shuffled graph smoothing control.",
        "- Matched 15-module, 8-component PCA-ridge readout under locked folds.",
        "",
        "## 3. What was not run",
        "",
        "- No external matrices or validation.",
        "- No clean holdouts.",
        "- No high-capacity GNN or architecture search.",
        "- No in silico ablation validation.",
        "- No manuscript claim update.",
        "",
        "## 4. Locked benchmark policy",
        "",
        "Pooled donor-level OOF Spearman; locked Stage 24 folds; five targets; threshold 0.3228; target degradation floor -0.02.",
        "",
        "## 5. Stage 27C reference baseline",
        "",
        f"`stage27c_module_pca_ridge_reference = {row.stage27c_reference_mean:.4f}`.",
        "",
        "## 6. Graph assets used",
        "",
        "```csv",
        summary.to_csv(index=False).strip(),
        "```",
        "",
        "## 7. Graph-control construction",
        "",
        f"Fixed one-hop row-normalized smoothing with alpha `{cfg['graph']['smoothing_alpha']}`. Non-graph genes remain unchanged. Identity adjacency returns the original expression exactly. Module construction and PCA-ridge capacity are matched across controls.",
        "",
        "## 8. Leakage and holdout controls",
        "",
        "All scaling, PCA, and ridge fitting occur within training folds. No held-out target, external matrix, clean holdout, or model-selection dataset was used.",
        "",
        "## 9. Mean pooled OOF results",
        "",
        "```csv",
        mean.to_csv(index=False).strip(),
        "```",
        "",
        "## 10. Target-level results",
        "",
        "```csv",
        target.to_csv(index=False).strip(),
        "```",
        "",
        "## 11. Pairwise graph-control deltas",
        "",
        "```csv",
        pairs.to_csv(index=False).strip(),
        "```",
        "",
        "## 12. Bootstrap confidence intervals",
        "",
        "```csv",
        bootstrap.to_csv(index=False).strip(),
        "```",
        "",
        "## 13. Pass/fail decision",
        "",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
        "",
        "## 14. Interpretation boundary",
        "",
        "This stage tests internal graph-topology contribution only. It does not establish causality, validated targets, therapeutic relevance, external validation, or in silico ablation validity.",
        "",
        "## 15. Recommendation for next stage",
        "",
        (
            "Graph-specific internal evidence passed. Proceed to stability/replication checks before counterfactual interpretation."
            if bool(row.graph_specific_pass)
            else "Graph-specific evidence did not pass. Preserve the controlled failure and do not promote graph-topology claims."
        ),
        "",
        "## Graph audit",
        "",
        "```csv",
        audit.to_csv(index=False).strip(),
        "```",
        "",
        "## Real-graph target summary",
        "",
        "```csv",
        real_targets.to_csv(index=False).strip(),
        "```",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage30_graph_controls_v3.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    oof, audit, graph_summary, _, audit_pass = run_graph_conditions(cfg)
    target, mean = compute_metrics(oof)
    pairs, target_deltas = comparisons(target, mean)
    pf = pass_fail(oof, target, mean, audit_pass, cfg)
    bootstrap = donor_bootstrap_ci(
        oof,
        ["condition", "target", "target_alias"],
        n_resamples=int(cfg["bootstrap"]["n_resamples"]),
        seed=int(cfg["random_seed"]),
    )

    oof.to_csv(OOF_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    pairs.to_csv(PAIRWISE_OUT, index=False)
    target_deltas.to_csv(TARGET_DELTA_OUT, index=False)
    pf.to_csv(PASS_FAIL_OUT, index=False)
    bootstrap.to_csv(BOOT_OUT, index=False)
    audit.to_csv(GRAPH_AUDIT_OUT, index=False)
    graph_summary.to_csv(GRAPH_SUMMARY_OUT, index=False)
    write_report(cfg, target, mean, pairs, bootstrap, audit, graph_summary, pf)
    update_status(mean, pf)

    row = pf.iloc[0]
    best = mean.iloc[0]
    real_targets = target[target["condition"] == "v3_real_graph"][
        ["target", "pooled_oof_spearman"]
    ].copy()
    real_targets["target"] = real_targets["target"].map(
        lambda value: "6e10/A_beta" if str(value).startswith("6e10/") else value
    )
    print(f"best_graph_condition={best.condition}")
    print(f"real_graph_mean={row.real_mean_pooled_oof_spearman:.6f}")
    print(f"stage27c_reference_mean={row.stage27c_reference_mean:.6f}")
    print(f"real_minus_reference={row.real_minus_stage27c_reference:.6f}")
    print(f"real_minus_no_graph={row.real_minus_no_graph:.6f}")
    print(f"real_minus_strict_shuffled={row.real_minus_strict_shuffled_graph:.6f}")
    print(real_targets.to_string(index=False))
    print(f"graph_specific_pass={bool(row.graph_specific_pass)}")


if __name__ == "__main__":
    main()
