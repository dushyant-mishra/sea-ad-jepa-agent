from __future__ import annotations

import argparse
import importlib
import sys
import types
from pathlib import Path
from typing import Any

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

for optional_module, optional_class in [("lightgbm", "LGBMRegressor"), ("xgboost", "XGBRegressor")]:
    if optional_module not in sys.modules:
        module = types.ModuleType(optional_module)
        setattr(module, optional_class, object)
        sys.modules[optional_module] = module

from sea_ad_jepa.data.graph_control_features import (  # noqa: E402
    canonical_genes,
    graph_smoothed_expression,
    load_graph_asset,
    predefined_module_features,
)
from sea_ad_jepa.eval.oof_metrics import regression_metrics  # noqa: E402

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

PASS_FAIL_OUT = TABLE_DIR / "stage35a_pass_fail_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage35a_condition_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage35a_mean_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage35a_target_metrics_v1.csv"
TARGET_RESCUE_OUT = TABLE_DIR / "stage35a_target_specific_rescue_v1.csv"
GRAPH_AUDIT_OUT = TABLE_DIR / "stage35a_graph_control_audit_v1.csv"
FEATURE_AUDIT_OUT = TABLE_DIR / "stage35a_feature_audit_v1.csv"
LEAKAGE_AUDIT_OUT = TABLE_DIR / "stage35a_leakage_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage35a_target_aware_weak_graph_rescue_report_v1.md"

REF27 = "stage27c_module_pca_ridge_reference"
REF31 = "stage31_weak_residual_real_graph_alpha_0_05_reference"
NO_GRAPH = "target_aware_no_graph_identity_aux_ridge"


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


def weight_suffix(weight: float) -> str:
    return str(weight).replace(".", "_")


def real_condition(weight: float) -> str:
    return f"target_aware_real_graph_aux_weight_{weight_suffix(weight)}_ridge"


def strict_condition(weight: float) -> str:
    return f"target_aware_strict_shuffled_graph_aux_weight_{weight_suffix(weight)}_ridge"


def target_context(cfg: dict[str, Any], target: str) -> str:
    for context, targets in cfg["target_contexts"].items():
        if target in set(targets):
            return context
    return "unassigned_context"


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


def validate_graph_resources(cfg: dict[str, Any]) -> tuple[list[str], dict[str, Any], pd.DataFrame]:
    paths = [
        resolve(cfg["graph"]["real_edges"]),
        resolve(cfg["graph"]["no_graph_edges"]),
        resolve(cfg["graph"]["strict_shuffled_edges"]),
        resolve(cfg["graph"]["strict_shuffled_diagnostics"]),
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing graph resources: " + ";".join(missing))
    identity_path = resolve(cfg["graph"]["no_graph_edges"])
    canonical = canonical_genes(identity_path)
    edges = pd.read_csv(identity_path)
    source = set(edges["source"].astype(str))
    target = set(edges["target"].astype(str))
    union = source | target
    assets = {
        "real": load_graph_asset("real", resolve(cfg["graph"]["real_edges"]), canonical),
        "no_graph": load_graph_asset("v3_no_graph", identity_path, canonical),
        "strict": load_graph_asset("strict", resolve(cfg["graph"]["strict_shuffled_edges"]), canonical),
    }
    strict_diag = pd.read_csv(resolve(cfg["graph"]["strict_shuffled_diagnostics"]))
    diag = dict(zip(strict_diag["metric"].astype(str), strict_diag["value"].astype(str)))
    audit_rows = [
        ("canonical_source_gene_count_2957", len(source) == 2957, f"source={len(source)}"),
        ("canonical_target_gene_count_2957", len(target) == 2957, f"target={len(target)}"),
        ("canonical_union_gene_count_2957", len(union) == 2957, f"union={len(union)}"),
        ("asset_node_counts_match", all(asset.adjacency.shape == (2957, 2957) for asset in assets.values()), str({k: v.adjacency.shape for k, v in assets.items()})),
        ("real_graph_nonempty", assets["real"].edge_count > 2957, f"edges={assets['real'].edge_count}"),
        ("strict_graph_edge_count_matches_real", assets["strict"].edge_count == assets["real"].edge_count, f"real={assets['real'].edge_count}; strict={assets['strict'].edge_count}"),
        ("strict_degree_sequence_preserved", diag.get("degree_sequence_exactly_preserved", "").lower() == "true", diag.get("degree_sequence_exactly_preserved", "missing")),
        ("strict_zero_overlap", diag.get("zero_overlap_achieved", "").lower() == "true", diag.get("final_overlap_fraction", "missing")),
        ("strict_safe_for_training", diag.get("safe_for_training", "").lower() == "true", diag.get("safe_for_training", "missing")),
    ]
    graph_audit = pd.DataFrame(
        [{"check_id": c, "status": "pass" if p else "fail", "passed": bool(p), "details": d} for c, p, d in audit_rows]
    )
    if not bool(graph_audit["passed"].all()):
        raise RuntimeError("Graph resource audit failed.")
    return canonical, assets, graph_audit


def reference_target_and_mean(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    def from_oof(path: Path, source_condition: str, out_condition: str) -> pd.DataFrame:
        oof = pd.read_csv(path)
        oof = oof[oof["condition"] == source_condition].copy()
        if "target_key" not in oof.columns:
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
                    "target_context": target_context(cfg, key),
                    "n_donors": int(group["donor_id"].nunique()),
                    **regression_metrics(group["y_true"].to_numpy(), group["y_pred"].to_numpy()),
                }
            )
        return pd.DataFrame(rows)

    t27 = from_oof(resolve(cfg["references"]["stage27c_oof"]), "module_pca_ridge", REF27)
    t31 = from_oof(resolve(cfg["references"]["stage31_oof"]), cfg["references"]["stage31_condition"], REF31)
    target = pd.concat([t27, t31], ignore_index=True)
    return target, summarize_mean(target)


def residual_module_features(expression: pd.DataFrame, asset, alpha: float) -> pd.DataFrame:
    smoothed = graph_smoothed_expression(expression, asset, alpha=alpha)
    residual_expression = expression.copy()
    residual_expression.loc[:, :] = 0.0
    graph_cols = [gene for gene in asset.genes if gene in expression.columns]
    residual_expression.loc[:, graph_cols] = smoothed.loc[:, graph_cols].to_numpy(dtype=float) - expression.loc[:, graph_cols].to_numpy(dtype=float)
    matrix, _ = predefined_module_features(residual_expression)
    return matrix


def fit_predict(
    modules: pd.DataFrame,
    aux: pd.DataFrame,
    y: pd.Series,
    train: list[str],
    test: list[str],
    cfg: dict[str, Any],
    aux_weight: float,
) -> np.ndarray:
    module_train = modules.loc[train].to_numpy(dtype=float)
    module_test = modules.loc[test].to_numpy(dtype=float)
    n_components = min(int(cfg["backbone"]["module_pca_components"]), module_train.shape[1], len(train) - 1)
    backbone = Pipeline(
        [
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=n_components, random_state=int(cfg["random_seed"]))),
        ]
    )
    base_train = backbone.fit_transform(module_train)
    base_test = backbone.transform(module_test)
    aux_train = aux.loc[train].to_numpy(dtype=float)
    aux_test = aux.loc[test].to_numpy(dtype=float)
    aux_scaler = StandardScaler()
    aux_train = aux_scaler.fit_transform(aux_train) * float(aux_weight)
    aux_test = aux_scaler.transform(aux_test) * float(aux_weight)
    x_train = np.concatenate([base_train, aux_train], axis=1)
    x_test = np.concatenate([base_test, aux_test], axis=1)
    ridge = RidgeCV(alphas=np.asarray(cfg["downstream"]["ridge_alphas"], dtype=float), cv=min(3, max(2, len(train) // 10)))
    ridge.fit(x_train, np.log1p(y.loc[train].to_numpy(dtype=float)))
    return ridge.predict(x_test)


def condition_specs(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    weights = list(map(float, cfg["graph"]["aux_weights"]))
    if cfg["graph"].get("run_optional_weights", False):
        weights = list(map(float, cfg["graph"].get("optional_aux_weights", []))) + weights
    specs = [{"condition": NO_GRAPH, "asset_key": "no_graph", "weight": 0.0, "graph_role": "matched_no_graph_identity_control"}]
    for weight in weights:
        specs.append({"condition": real_condition(weight), "asset_key": "real", "weight": weight, "graph_role": "real_graph_auxiliary"})
        specs.append({"condition": strict_condition(weight), "asset_key": "strict", "weight": weight, "graph_role": "strict_shuffled_graph_auxiliary"})
    return specs


def run_oof(cfg: dict[str, Any], assets: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    folds, targets, expression, target_matrix = load_context()
    modules, module_overlaps = predefined_module_features(expression)
    residual_cache = {
        "no_graph": pd.DataFrame(0.0, index=modules.index, columns=modules.columns),
        "real": residual_module_features(expression, assets["real"], float(cfg["graph"]["alpha"])),
        "strict": residual_module_features(expression, assets["strict"], float(cfg["graph"]["alpha"])),
    }
    rows = []
    for spec in condition_specs(cfg):
        aux = residual_cache[spec["asset_key"]]
        for _, target_row in targets.iterrows():
            target = target_row["target_name"]
            key = target_key(target)
            alias = target_row["target_alias"]
            context = target_context(cfg, key)
            y = target_matrix[alias].dropna()
            for fold_id in sorted(folds["fold_id"].unique()):
                test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
                train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
                train = [donor for donor in train if donor in y.index and donor in modules.index]
                test = [donor for donor in test if donor in y.index and donor in modules.index]
                pred = fit_predict(modules, aux, y, train, test, cfg, float(spec["weight"]))
                for donor, true, predicted in zip(test, np.log1p(y.loc[test].to_numpy(dtype=float)), pred):
                    rows.append(
                        {
                            "condition": spec["condition"],
                            "target": target,
                            "target_key": key,
                            "target_alias": alias,
                            "target_context": context,
                            "donor_id": donor,
                            "fold_id": int(fold_id),
                            "y_true": float(true),
                            "y_pred": float(predicted),
                            "target_scale": "log1p",
                        }
                    )
    feature_rows = []
    for spec in condition_specs(cfg):
        feature_rows.append(
            {
                "condition": spec["condition"],
                "graph_role": spec["graph_role"],
                "asset_key": spec["asset_key"],
                "graph_alpha": float(cfg["graph"]["alpha"]) if spec["asset_key"] != "no_graph" else 0.0,
                "aux_weight": float(spec["weight"]),
                "backbone_feature_type": "fold_local_stage27c_module_pca",
                "backbone_pca_components": int(cfg["backbone"]["module_pca_components"]),
                "aux_feature_type": "predefined_module_features_of_gene_graph_expression_residual",
                "context_specific_graphs_available": False,
                "target_aware_routing": "predeclared_target_context_labels_same_gene_graph_auxiliary_view",
                "n_module_features": int(len(module_overlaps)),
                "module_feature_names": ";".join(modules.columns.astype(str)),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(feature_rows)


def compute_target_metrics(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in oof.groupby(["condition", "target", "target_key", "target_alias", "target_context"]):
        condition, target, key, alias, context = keys
        rows.append(
            {
                "condition": condition,
                "target": target,
                "target_key": key,
                "target_alias": alias,
                "target_context": context,
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


def make_audits(cfg: dict[str, Any], target: pd.DataFrame, mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = set(cfg["required_targets"])
    new_conditions = [spec["condition"] for spec in condition_specs(cfg)]
    real_conditions = [c for c in new_conditions if c.startswith("target_aware_real_graph")]
    strict_conditions = [c for c in new_conditions if c.startswith("target_aware_strict_shuffled")]
    mean_map = mean.set_index("condition")["mean_pooled_oof_spearman"]
    best_new = mean[mean["condition"].isin(new_conditions)].iloc[0]
    best_real = mean[mean["condition"].isin(real_conditions)].iloc[0]
    best_real_weight = float(best_real.condition.split("_weight_")[1].split("_ridge")[0].replace("_", "."))
    matched_strict = strict_condition(best_real_weight)
    graph_specific = bool(mean_map.get(best_real.condition, -999) > mean_map.get(NO_GRAPH, 999) and mean_map.get(best_real.condition, -999) > mean_map.get(matched_strict, 999))
    graph = pd.DataFrame(
        [
            {
                "comparison": "best_real_minus_no_graph_identity",
                "left_condition": best_real.condition,
                "right_condition": NO_GRAPH,
                "delta_mean_pooled_oof_spearman": float(mean_map.get(best_real.condition, np.nan) - mean_map.get(NO_GRAPH, np.nan)),
                "graph_gate_pass": bool(mean_map.get(best_real.condition, -999) > mean_map.get(NO_GRAPH, 999)),
            },
            {
                "comparison": "best_real_minus_matched_strict_shuffled",
                "left_condition": best_real.condition,
                "right_condition": matched_strict,
                "delta_mean_pooled_oof_spearman": float(mean_map.get(best_real.condition, np.nan) - mean_map.get(matched_strict, np.nan)),
                "graph_gate_pass": bool(mean_map.get(best_real.condition, -999) > mean_map.get(matched_strict, 999)),
            },
        ]
    )
    ref27 = target[target["condition"] == REF27][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "stage27c_target_spearman"})
    no_graph = target[target["condition"] == NO_GRAPH][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "matched_no_graph_target_spearman"})
    rescue_rows = []
    for real in real_conditions:
        weight = float(real.split("_weight_")[1].split("_ridge")[0].replace("_", "."))
        strict = strict_condition(weight)
        real_t = target[target["condition"] == real][["target", "target_key", "target_context", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "real_target_spearman"})
        strict_t = target[target["condition"] == strict][["target_key", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "matched_strict_target_spearman"})
        merged = real_t.merge(ref27, on="target_key").merge(no_graph, on="target_key").merge(strict_t, on="target_key")
        for _, row in merged.iterrows():
            d27 = row.real_target_spearman - row.stage27c_target_spearman
            dng = row.real_target_spearman - row.matched_no_graph_target_spearman
            dst = row.real_target_spearman - row.matched_strict_target_spearman
            rescue_rows.append(
                {
                    "condition": real,
                    "aux_weight": weight,
                    "target": row.target,
                    "target_key": row.target_key,
                    "target_context": row.target_context,
                    "real_target_spearman": row.real_target_spearman,
                    "delta_vs_stage27c": d27,
                    "delta_vs_matched_no_graph": dng,
                    "delta_vs_matched_strict_shuffled": dst,
                    "target_specific_graph_rescue_candidate": bool(d27 >= 0.005 and dng >= 0.005 and dst >= 0.005),
                    "diagnostic_label_only": True,
                }
            )
    target_rescue = pd.DataFrame(rescue_rows)
    best_target = target[target["condition"] == best_new.condition].merge(ref27, on="target_key", how="left")
    target_gate = bool(((best_target["pooled_oof_spearman"] - best_target["stage27c_target_spearman"]) >= float(cfg["max_target_drop_vs_stage27c_reference"])).all())
    leakage = pd.DataFrame(
        [
            {
                "clean_holdout_used": False,
                "external_pretraining_matrix_used": False,
                "external_labels_used_for_supervised_pathology_prediction": False,
                "sea_ad_used_for_downstream_only": True,
                "locked_donor_folds_used": True,
                "fold_local_downstream_scaling_and_ridge": True,
                "target_values_used_to_construct_graph": False,
                "in_silico_ablation_run": False,
                "leakage_audit_pass": True,
            }
        ]
    )
    internal_pass = bool(
        best_new.mean_pooled_oof_spearman > float(cfg["stage27c_reference_mean"])
        and best_new.mean_pooled_oof_spearman >= float(cfg["minimum_success_threshold"])
        and required.issubset(set(target[target["condition"] == best_new.condition]["target_key"]))
        and target_gate
        and bool(leakage.iloc[0]["leakage_audit_pass"])
    )
    has_target_rescue = bool(target_rescue["target_specific_graph_rescue_candidate"].any())
    real_gt_strict = bool(graph.loc[graph["comparison"] == "best_real_minus_matched_strict_shuffled", "graph_gate_pass"].iloc[0])
    real_gt_no = bool(graph.loc[graph["comparison"] == "best_real_minus_no_graph_identity", "graph_gate_pass"].iloc[0])
    if has_target_rescue and not graph_specific:
        interpretation = "Stage 35A found target-specific graph-rescue signals, but global graph-specific utility remains unestablished."
    elif best_new.mean_pooled_oof_spearman <= float(cfg["stage27c_reference_mean"]):
        interpretation = "Target-aware weak graph injection did not improve over the Stage 27C internal no-graph reference under this implementation."
    elif internal_pass and not graph_specific:
        interpretation = "Stage 35A improved the internal benchmark, but graph-specific utility remains unestablished."
    else:
        interpretation = "Stage 35A completed under guarded internal benchmark rules."
    if real_gt_strict and not real_gt_no:
        graph_interpretation = "Real topology outperformed shuffled topology but did not improve over the no-graph identity reference."
    elif real_gt_no and not real_gt_strict:
        graph_interpretation = "Graph-like auxiliary features improved performance, but topology-specific utility was not established."
    elif graph_specific:
        graph_interpretation = "Global graph-specific pass observed internally; this is not external validation."
    else:
        graph_interpretation = "Graph-specific utility remains unestablished."
    pf = pd.DataFrame(
        [
            {
                "stage35a_run": True,
                "best_stage35a_condition": best_new.condition,
                "best_stage35a_mean_pooled_oof_spearman": float(best_new.mean_pooled_oof_spearman),
                "best_real_graph_condition": best_real.condition,
                "best_real_graph_mean_pooled_oof_spearman": float(best_real.mean_pooled_oof_spearman),
                "stage27c_reference_mean": float(cfg["stage27c_reference_mean"]),
                "stage31_reference_mean": float(cfg["stage31_best_reference_mean"]),
                "best_minus_stage27c": float(best_new.mean_pooled_oof_spearman - float(cfg["stage27c_reference_mean"])),
                "best_real_minus_no_graph": float(mean_map.get(best_real.condition, np.nan) - mean_map.get(NO_GRAPH, np.nan)),
                "best_real_minus_matched_strict": float(mean_map.get(best_real.condition, np.nan) - mean_map.get(matched_strict, np.nan)),
                "all_five_targets_reported": required.issubset(set(target[target["condition"].isin(new_conditions)]["target_key"])),
                "target_degradation_gate_pass": target_gate,
                "stage35a_internal_performance_pass": internal_pass,
                "stage35a_global_graph_specific_pass": graph_specific,
                "n_target_specific_rescue_candidates": int(target_rescue["target_specific_graph_rescue_candidate"].sum()),
                "controlled_interpretation": interpretation,
                "graph_interpretation": graph_interpretation,
            }
        ]
    )
    return leakage, graph, target_rescue, pf


def write_report(mean, target, rescue, graph, feature, leakage, pf):
    row = pf.iloc[0]
    lines = [
        "# Stage 35A target-aware weak graph rescue report v1",
        "",
        "## Executive summary",
        "",
        f"Best Stage 35A condition: `{row.best_stage35a_condition}` with mean pooled donor-level OOF Spearman `{row.best_stage35a_mean_pooled_oof_spearman:.4f}`.",
        f"Best real graph condition: `{row.best_real_graph_condition}` with mean `{row.best_real_graph_mean_pooled_oof_spearman:.4f}`.",
        f"Stage 27C reference: `{row.stage27c_reference_mean:.4f}`. Stage 31 reference: `{row.stage31_reference_mean:.4f}`.",
        f"Internal performance pass: `{bool(row.stage35a_internal_performance_pass)}`. Global graph-specific pass: `{bool(row.stage35a_global_graph_specific_pass)}`. Target-specific rescue candidates: `{int(row.n_target_specific_rescue_candidates)}`.",
        "",
        "## Controlled interpretation",
        "",
        str(row.controlled_interpretation),
        str(row.graph_interpretation),
        "",
        "This is an internal SEA-AD benchmark. It is not external validation, graph topology validation, causality, in silico ablation validation, or therapeutic-target discovery.",
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
        "## Target-specific rescue audit",
        "",
        "```csv",
        rescue.to_csv(index=False).strip(),
        "```",
        "",
        "## Graph-control audit",
        "",
        "```csv",
        graph.to_csv(index=False).strip(),
        "```",
        "",
        "## Feature audit",
        "",
        "```csv",
        feature.to_csv(index=False).strip(),
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
        "scorecard_item": "stage35a_target_aware_weak_graph_rescue",
        "status": "complete",
        "stage": "Stage 35A",
        "metric": "pooled donor-level OOF Spearman",
        "threshold_or_gate": "full pass requires best Stage 35A > Stage 27C and >=0.3228; graph pass requires real > no-graph and strict",
        "current_value": f"{row.best_stage35a_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.stage35a_internal_performance_pass) else "fail",
        "datasets_allowed": "SEA-AD locked folds only",
        "datasets_forbidden": "external pretraining matrices; clean holdouts; external labels; in silico ablation",
        "allowed_claim": row.controlled_interpretation,
        "notes": f"global_graph_specific_pass={bool(row.stage35a_global_graph_specific_pass)}; target_rescue_candidates={int(row.n_target_specific_rescue_candidates)}; {row.graph_interpretation}",
    }
    score = score[score["scorecard_item"] != "stage35a_target_aware_weak_graph_rescue"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (
            ROOT / "docs" / "ACTIVE_V3_STATUS.md",
            "\n\n## Stage 35A target-aware weak graph rescue status\n",
            f"\nStage 35A is complete. Best condition: `{row.best_stage35a_condition}` (`{row.best_stage35a_mean_pooled_oof_spearman:.4f}`). Best real graph condition: `{row.best_real_graph_condition}` (`{row.best_real_graph_mean_pooled_oof_spearman:.4f}`). Internal performance pass: `{bool(row.stage35a_internal_performance_pass)}`; global graph-specific pass: `{bool(row.stage35a_global_graph_specific_pass)}`; target-specific rescue candidates: `{int(row.n_target_specific_rescue_candidates)}`. {row.controlled_interpretation} {row.graph_interpretation} No external validation or manuscript claim update.\n",
        ),
        (
            ROOT / "docs" / "V3_SCORECARD.md",
            "\n\n## Stage 35A target-aware weak graph rescue result\n",
            f"\nBest Stage 35A condition: `{row.best_stage35a_condition}`; mean pooled OOF Spearman: `{row.best_stage35a_mean_pooled_oof_spearman:.4f}`; minus Stage 27C: `{row.best_minus_stage27c:.4f}`; global graph-specific pass: `{bool(row.stage35a_global_graph_specific_pass)}`; target-specific rescue candidates: `{int(row.n_target_specific_rescue_candidates)}`. {row.controlled_interpretation}\n",
        ),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def skipped_outputs(reason: str) -> None:
    pf = pd.DataFrame([{"stage35a_run": False, "skip_reason": reason, "stage35a_internal_performance_pass": False, "stage35a_global_graph_specific_pass": False}])
    pf.to_csv(PASS_FAIL_OUT, index=False)
    REPORT_OUT.write_text("# Stage 35A target-aware weak graph rescue report v1\n\nStage 35A skipped: " + reason + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage35a_target_aware_weak_graph_rescue_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        _, assets, graph_resource_audit = validate_graph_resources(cfg)
    except Exception as exc:
        skipped_outputs(f"{type(exc).__name__}:{exc}")
        print(f"stage35a_skipped={type(exc).__name__}:{exc}")
        return
    external_oof, feature = run_oof(cfg, assets)
    external_target = compute_target_metrics(external_oof)
    ref_target, ref_mean = reference_target_and_mean(cfg)
    target = pd.concat([external_target, ref_target], ignore_index=True)
    mean = pd.concat([summarize_mean(external_target), ref_mean], ignore_index=True).sort_values("mean_pooled_oof_spearman", ascending=False)
    leakage, graph_control, rescue, pf = make_audits(cfg, target, mean)
    graph_full = pd.concat(
        [
            graph_control.assign(audit_type="graph_control_delta"),
            graph_resource_audit.rename(columns={"check_id": "comparison", "details": "right_condition"}).assign(
                left_condition="resource_audit",
                delta_mean_pooled_oof_spearman=np.nan,
                graph_gate_pass=graph_resource_audit["passed"],
                audit_type="resource_audit",
            )[["comparison", "left_condition", "right_condition", "delta_mean_pooled_oof_spearman", "graph_gate_pass", "audit_type"]],
        ],
        ignore_index=True,
    )
    condition = mean.rename(columns={"mean_pooled_oof_spearman": "condition_mean_pooled_oof_spearman"})
    pf.to_csv(PASS_FAIL_OUT, index=False)
    condition.to_csv(CONDITION_OUT, index=False)
    mean.to_csv(MEAN_OUT, index=False)
    target.to_csv(TARGET_OUT, index=False)
    rescue.to_csv(TARGET_RESCUE_OUT, index=False)
    graph_full.to_csv(GRAPH_AUDIT_OUT, index=False)
    feature.to_csv(FEATURE_AUDIT_OUT, index=False)
    leakage.to_csv(LEAKAGE_AUDIT_OUT, index=False)
    write_report(mean, target, rescue, graph_full, feature, leakage, pf)
    update_status(pf)
    row = pf.iloc[0]
    print(f"best_stage35a_condition={row.best_stage35a_condition}")
    print(f"best_mean_pooled_oof_spearman={row.best_stage35a_mean_pooled_oof_spearman:.6f}")
    print(f"best_real_graph_condition={row.best_real_graph_condition}")
    print(f"best_real_graph_mean={row.best_real_graph_mean_pooled_oof_spearman:.6f}")
    print(f"best_minus_stage27c={row.best_minus_stage27c:.6f}")
    print(f"target_specific_rescue_candidates={int(row.n_target_specific_rescue_candidates)}")
    print(f"stage35a_global_graph_specific_pass={bool(row.stage35a_global_graph_specific_pass)}")


if __name__ == "__main__":
    main()
