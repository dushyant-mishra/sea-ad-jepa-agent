from __future__ import annotations

import argparse
import importlib
import re
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr
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

s25 = importlib.import_module("run_v3_primary_baseline_benchmark_suite_v1")


TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

PASS_FAIL_OUT = TABLE_DIR / "stage36a_pass_fail_v1.csv"
MODEL_AUDIT_OUT = TABLE_DIR / "stage36a_model_selection_audit_v1.csv"
MODULE_SCORES_OUT = TABLE_DIR / "stage36a_module_counterfactual_scores_v1.csv"
TARGET_SUMMARY_OUT = TABLE_DIR / "stage36a_target_summary_v1.csv"
GENE_SCORES_OUT = TABLE_DIR / "stage36a_gene_hypothesis_scores_v1.csv"
KG_AUDIT_OUT = TABLE_DIR / "stage36a_knowledge_grounding_audit_v1.csv"
RANKED_OUT = TABLE_DIR / "stage36a_agent_ranked_hypotheses_v1.csv"
SAFETY_OUT = TABLE_DIR / "stage36a_safety_language_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage36a_module_counterfactual_agent_report_v1.md"
READABLE_OUT = REPORT_DIR / "stage36a_agent_readable_hypotheses_v1.md"

FORBIDDEN = [
    "causal regulator",
    "therapeutic target",
    "validated mechanism",
    "drug target",
    "external validation succeeded",
    "experimentally confirmed",
    "graph topology is validated",
    "graph-jepa proves causality",
    "in silico ablation is validated",
    "therapeutic targets were discovered",
]


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


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 3 or np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return 0.0
    value = spearmanr(y_true, y_pred).statistic
    return 0.0 if pd.isna(value) else float(value)


def load_context():
    folds, targets, _, metadata = s25.load_inputs()
    donors = folds["donor_id"].astype(str).tolist()
    expr = s25.load_expression_matrix(donors)
    target_matrix = s25.build_target_matrix(metadata, targets, donors)
    shared = sorted(set(donors) & set(expr.index) & set(target_matrix.index))
    folds = folds[folds["donor_id"].astype(str).isin(shared)].copy()
    expr = expr.loc[shared]
    target_matrix = target_matrix.loc[shared]
    modules = s25.build_predefined_module_features(expr).matrix
    return folds, targets, expr, target_matrix, modules


def fit_fold_model(modules: pd.DataFrame, y: pd.Series, train: list[str], cfg: dict[str, Any]) -> Pipeline:
    n_components = min(int(cfg["model"]["module_pca_components"]), modules.shape[1], len(train) - 1)
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=n_components, random_state=int(cfg["random_seed"]))),
            (
                "ridge",
                RidgeCV(
                    alphas=np.asarray(cfg["model"]["ridge_alphas"], dtype=float),
                    cv=min(3, max(2, len(train) // 10)),
                ),
            ),
        ]
    )
    model.fit(modules.loc[train].to_numpy(dtype=float), np.log1p(y.loc[train].to_numpy(dtype=float)))
    return model


def predict_with_component_ablation(model: Pipeline, x: np.ndarray, component_idx: int) -> np.ndarray:
    scaler = model.named_steps["scale"]
    pca = model.named_steps["pca"]
    ridge = model.named_steps["ridge"]
    z = pca.transform(scaler.transform(x))
    z[:, component_idx] = 0.0
    return ridge.predict(z)


def run_counterfactuals(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    folds, targets, _, target_matrix, modules = load_context()
    rows: list[dict[str, Any]] = []
    pred_rows: list[dict[str, Any]] = []
    module_names = list(modules.columns)
    for _, target_row in targets.iterrows():
        target = target_row["target_name"]
        key = target_key(target)
        alias = target_row["target_alias"]
        y = target_matrix[alias].dropna()
        for fold_id in sorted(folds["fold_id"].unique()):
            test = folds.loc[folds["fold_id"] == fold_id, "donor_id"].astype(str).tolist()
            train = folds.loc[folds["fold_id"] != fold_id, "donor_id"].astype(str).tolist()
            train = [donor for donor in train if donor in y.index and donor in modules.index]
            test = [donor for donor in test if donor in y.index and donor in modules.index]
            model = fit_fold_model(modules, y, train, cfg)
            x_test = modules.loc[test].to_numpy(dtype=float)
            baseline = model.predict(x_test)
            true = np.log1p(y.loc[test].to_numpy(dtype=float))
            pca = model.named_steps["pca"]
            ridge = model.named_steps["ridge"]
            module_means = modules.loc[train].mean(axis=0)
            for donor, yt, yp in zip(test, true, baseline):
                pred_rows.append({"target": target, "target_key": key, "target_alias": alias, "donor_id": donor, "fold_id": int(fold_id), "y_true": float(yt), "baseline_pred": float(yp)})
            for module_idx, module_name in enumerate(module_names):
                x_ablate = modules.loc[test].copy()
                x_ablate[module_name] = float(module_means[module_name])
                ablated = model.predict(x_ablate.to_numpy(dtype=float))
                approx_module_coef = float(np.sum(pca.components_[:, module_idx] * ridge.coef_))
                for donor, yt, yp, ya in zip(test, true, baseline, ablated):
                    rows.append(
                        {
                            "target": target,
                            "target_key": key,
                            "target_alias": alias,
                            "fold_id": int(fold_id),
                            "donor_id": donor,
                            "feature_type": "module",
                            "feature_name": module_name,
                            "feature_index": module_idx,
                            "y_true": float(yt),
                            "baseline_pred": float(yp),
                            "ablated_pred": float(ya),
                            "prediction_delta_ablated_minus_baseline": float(ya - yp),
                            "abs_prediction_delta": float(abs(ya - yp)),
                            "coefficient_contribution_available": True,
                            "approx_fold_coefficient_contribution": approx_module_coef,
                        }
                    )
            if cfg["model"].get("include_pca_component_counterfactuals", True):
                n_components = int(pca.n_components_)
                for component_idx in range(n_components):
                    ablated = predict_with_component_ablation(model, x_test, component_idx)
                    coef = float(ridge.coef_[component_idx])
                    for donor, yt, yp, ya in zip(test, true, baseline, ablated):
                        rows.append(
                            {
                                "target": target,
                                "target_key": key,
                                "target_alias": alias,
                                "fold_id": int(fold_id),
                                "donor_id": donor,
                                "feature_type": "pca_component",
                                "feature_name": f"module_pca_component_{component_idx + 1}",
                                "feature_index": component_idx,
                                "y_true": float(yt),
                                "baseline_pred": float(yp),
                                "ablated_pred": float(ya),
                                "prediction_delta_ablated_minus_baseline": float(ya - yp),
                                "abs_prediction_delta": float(abs(ya - yp)),
                                "coefficient_contribution_available": True,
                                "approx_fold_coefficient_contribution": coef,
                            }
                        )
    return pd.DataFrame(rows), pd.DataFrame(pred_rows)


def summarize_counterfactuals(long_df: pd.DataFrame, pred_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_metrics = []
    for keys, group in pred_df.groupby(["target", "target_key", "target_alias"]):
        target, key, alias = keys
        baseline_metrics.append(
            {
                "target": target,
                "target_key": key,
                "target_alias": alias,
                "baseline_metric": safe_spearman(group["y_true"].to_numpy(), group["baseline_pred"].to_numpy()),
                "n_donors": int(group["donor_id"].nunique()),
            }
        )
    baseline = pd.DataFrame(baseline_metrics)
    rows = []
    for keys, group in long_df.groupby(["target", "target_key", "target_alias", "feature_type", "feature_name", "feature_index"]):
        target, key, alias, ftype, fname, findex = keys
        base_metric = safe_spearman(group["y_true"].to_numpy(), group["baseline_pred"].to_numpy())
        ablated_metric = safe_spearman(group["y_true"].to_numpy(), group["ablated_pred"].to_numpy())
        mean_delta = float(group["prediction_delta_ablated_minus_baseline"].mean())
        if mean_delta > 1e-9:
            direction = "ablation_increases_prediction"
        elif mean_delta < -1e-9:
            direction = "ablation_decreases_prediction"
        else:
            direction = "no_mean_direction"
        rows.append(
            {
                "target": target,
                "target_key": key,
                "target_alias": alias,
                "feature_type": ftype,
                "feature_name": fname,
                "feature_index": int(findex),
                "evidence_level": "module_counterfactual_hypothesis" if ftype == "module" else "module_pca_component_counterfactual_hypothesis",
                "baseline_metric": base_metric,
                "ablated_metric": ablated_metric,
                "delta_metric": ablated_metric - base_metric,
                "importance_score": base_metric - ablated_metric,
                "mean_abs_prediction_delta": float(group["abs_prediction_delta"].mean()),
                "mean_prediction_delta_ablated_minus_baseline": mean_delta,
                "direction": direction,
                "mean_abs_coefficient_contribution": float(group["approx_fold_coefficient_contribution"].abs().mean()) if hasattr(group["approx_fold_coefficient_contribution"], "abs") else float(np.abs(group["approx_fold_coefficient_contribution"]).mean()),
                "n_donors": int(group["donor_id"].nunique()),
                "interpretation": "model-implied counterfactual sensitivity; requires independent validation",
                "recommended_validation_type": "independent_experimental_or_external_validation_required",
                "not_experimentally_validated": True,
            }
        )
    scores = pd.DataFrame(rows).sort_values(["target_key", "importance_score", "mean_abs_prediction_delta"], ascending=[True, False, False])
    target_summary = baseline.merge(
        scores.groupby(["target", "target_key"], as_index=False).agg(
            n_counterfactual_features=("feature_name", "nunique"),
            max_importance_score=("importance_score", "max"),
            top_feature=("feature_name", lambda x: list(x)[0]),
        ),
        on=["target", "target_key"],
        how="left",
    )
    return scores, target_summary


def find_local_knowledge(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    if not cfg.get("knowledge_grounding", {}).get("enabled", True):
        return pd.DataFrame(rows)
    patterns = cfg["knowledge_grounding"]["filename_patterns"]
    for root in cfg["knowledge_grounding"]["local_search_roots"]:
        base = resolve(root)
        if not base.exists():
            continue
        for pattern in patterns:
            for path in base.rglob(pattern):
                if path.is_file() and path.suffix.lower() in {".csv", ".md", ".txt", ".tsv"}:
                    rows.append({"path": str(path.relative_to(ROOT)), "size_bytes": int(path.stat().st_size), "used_for_annotation": False})
    return pd.DataFrame(rows).drop_duplicates("path") if rows else pd.DataFrame(rows)


def gene_projection(scores: pd.DataFrame, kg_audit: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    module_gene_map = getattr(s25, "MICROGLIA_GENE_MODULES", {})
    rows = []
    for _, row in scores[scores["feature_type"] == "module"].iterrows():
        feature_name = str(row["feature_name"])
        module_gene_map_key = feature_name
        if module_gene_map_key not in module_gene_map and module_gene_map_key.startswith("module_"):
            module_gene_map_key = module_gene_map_key.removeprefix("module_")
        genes = module_gene_map.get(module_gene_map_key, [])
        for gene in genes:
            rows.append(
                {
                    "target": row["target"],
                    "target_key": row["target_key"],
                    "module": feature_name,
                    "module_gene_map_key": module_gene_map_key,
                    "gene": str(gene).upper(),
                    "projection_method": "exact_predefined_module_membership_projection",
                    "evidence_level": "model_implied_gene_hypothesis",
                    "module_importance_score": row["importance_score"],
                    "module_delta_metric": row["delta_metric"],
                    "mean_abs_prediction_delta": row["mean_abs_prediction_delta"],
                    "kg_known_ad": "not_evaluated",
                    "kg_known_microglia": "not_evaluated",
                    "kg_known_neuroinflammation": "not_evaluated",
                    "kg_known_target_pathology": "not_evaluated",
                    "kg_source": "local_knowledge_resource_missing",
                    "not_experimentally_validated": True,
                }
            )
    gene_df = pd.DataFrame(rows)
    if gene_df.empty:
        gene_df = pd.DataFrame(columns=["target", "target_key", "module", "module_gene_map_key", "gene", "projection_method", "evidence_level"])
    if kg_audit.empty:
        kg = pd.DataFrame(
            [
                {
                    "knowledge_grounding_status": "local_knowledge_resource_missing",
                    "local_resource_count": 0,
                    "knowledge_grounding_pass": False,
                    "non_fatal": True,
                    "notes": "No local static knowledge resource was used for gene known/novel annotation.",
                }
            ]
        )
    else:
        # Resources are inventoried but not schema-stable enough for automatic known-status annotation.
        kg = pd.DataFrame(
            [
                {
                    "knowledge_grounding_status": "local_resources_found_but_not_schema_mapped",
                    "local_resource_count": int(len(kg_audit)),
                    "knowledge_grounding_pass": False,
                    "non_fatal": True,
                    "notes": "Local candidate/prior resources were found, but no stable KG schema was available for automatic annotation.",
                }
            ]
        )
    return gene_df, kg


def ranked_hypotheses(scores: pd.DataFrame, genes: pd.DataFrame, kg: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    top_n = int(cfg["hypotheses"]["top_n_per_target"])
    for target_key, group in scores.groupby("target_key"):
        top = group.sort_values(["importance_score", "mean_abs_prediction_delta"], ascending=[False, False]).head(top_n)
        for rank, (_, row) in enumerate(top.iterrows(), start=1):
            rows.append(
                {
                    "target": row["target"],
                    "target_key": row["target_key"],
                    "rank": rank,
                    "module_or_component": row["feature_name"],
                    "gene": "",
                    "evidence_level": row["evidence_level"],
                    "baseline_metric": row["baseline_metric"],
                    "ablated_metric": row["ablated_metric"],
                    "delta_metric": row["delta_metric"],
                    "mean_abs_prediction_delta": row["mean_abs_prediction_delta"],
                    "direction": row["direction"],
                    "kg_status": kg.iloc[0]["knowledge_grounding_status"],
                    "interpretation": row["interpretation"],
                    "recommended_validation_type": row["recommended_validation_type"],
                }
            )
    if not genes.empty:
        top_gene_n = int(cfg["hypotheses"]["top_gene_n_per_target"])
        for target_key, group in genes.groupby("target_key"):
            top = group.sort_values(["module_importance_score", "mean_abs_prediction_delta"], ascending=[False, False]).head(top_gene_n)
            start = len([r for r in rows if r["target_key"] == target_key]) + 1
            for offset, (_, row) in enumerate(top.iterrows(), start=0):
                rows.append(
                    {
                        "target": row["target"],
                        "target_key": row["target_key"],
                        "rank": start + offset,
                        "module_or_component": row["module"],
                        "gene": row["gene"],
                        "evidence_level": "model_implied_gene_hypothesis",
                        "baseline_metric": np.nan,
                        "ablated_metric": np.nan,
                        "delta_metric": row["module_delta_metric"],
                        "mean_abs_prediction_delta": row["mean_abs_prediction_delta"],
                        "direction": "projected_from_module_counterfactual",
                        "kg_status": row["kg_source"],
                        "interpretation": "module-membership projected model-implied gene hypothesis; requires independent validation",
                        "recommended_validation_type": cfg["hypotheses"]["recommended_validation_type"],
                    }
                )
    return pd.DataFrame(rows)


def safety_audit_texts(*texts: str) -> pd.DataFrame:
    combined = "\n".join(texts).lower()
    rows = []
    for idx, phrase in enumerate(FORBIDDEN, start=1):
        used = phrase in combined
        rows.append({"check_id": f"forbidden_phrase_{idx:02d}", "used": used, "status": "fail" if used else "pass"})
    any_used = any(row["used"] for row in rows)
    rows.append({"check_id": "overall", "used": any_used, "status": "fail" if any_used else "pass"})
    return pd.DataFrame(rows)


def model_selection_audit(cfg: dict[str, Any]) -> pd.DataFrame:
    stage35a_path = resolve(cfg["stage35a_pass_fail"])
    stage35a_used = False
    stage35a_exists = stage35a_path.exists()
    stage35a_pass = False
    if stage35a_exists:
        s35 = pd.read_csv(stage35a_path)
        stage35a_pass = bool(s35.iloc[0].get("stage35a_internal_performance_pass", False))
        stage35a_used = stage35a_pass
    return pd.DataFrame(
        [
            {
                "primary_backbone": "stage27c_module_pca_ridge" if not stage35a_used else "stage35a_best_model",
                "stage27c_reference_mean": float(cfg["stage27c_reference_mean"]),
                "stage35a_pass_fail_exists": stage35a_exists,
                "stage35a_internal_performance_pass": stage35a_pass,
                "stage35a_used_as_primary": stage35a_used,
                "external_pretrained_models_used_as_primary": False,
                "selection_reason": "Stage 35A did not beat Stage 27C; Stage 27C remains primary hypothesis engine." if stage35a_exists and not stage35a_pass else "Stage 27C selected as configured primary backbone.",
            }
        ]
    )


def write_reports(scores, target_summary, genes, kg, ranked, safety, pf):
    row = pf.iloc[0]
    if bool(row.stage36a_gene_level_pass):
        gene_text = "Stage 36A projected module-level counterfactual sensitivity to genes using exact predefined module-membership mappings. These are model-implied hypotheses, not direct gene ablations, causal claims, or experimentally validated targets."
    else:
        gene_text = "Stage 36A produced module-level model-implied counterfactual hypotheses. Gene-level hypotheses were not produced because an exact module-to-gene/loading map was unavailable."
    if str(kg.iloc[0]["knowledge_grounding_status"]).startswith("local_knowledge_resource_missing"):
        kg_text = "Local knowledge grounding was not available, so novelty/known-status was not evaluated."
    else:
        kg_text = "Knowledge grounding annotates prior support only; it does not validate the model-implied hypotheses."
    lines = [
        "# Stage 36A module counterfactual agent report v1",
        "",
        "## Executive summary",
        "",
        f"Stage 36A run pass: `{bool(row.stage36a_run_pass)}`. Gene-level pass: `{bool(row.stage36a_gene_level_pass)}`. Knowledge-grounding pass: `{bool(row.stage36a_knowledge_grounding_pass)}`. Validation pass: `{bool(row.stage36a_validation_pass)}`.",
        "",
        "## Interpretation",
        "",
        gene_text,
        kg_text,
        "",
        "All outputs are model-implied hypotheses and counterfactual sensitivity summaries. They require independent validation and are not causal or experimentally validated target claims.",
        "",
        "## Target summary",
        "",
        "```csv",
        target_summary.to_csv(index=False).strip(),
        "```",
        "",
        "## Top module/component counterfactuals",
        "",
        "```csv",
        scores.head(80).to_csv(index=False).strip(),
        "```",
        "",
        "## Knowledge grounding audit",
        "",
        "```csv",
        kg.to_csv(index=False).strip(),
        "```",
        "",
        "## Safety language audit",
        "",
        "```csv",
        safety.to_csv(index=False).strip(),
        "```",
        "",
        "## Pass/fail",
        "",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
    ]
    report = "\n".join(lines) + "\n"
    REPORT_OUT.write_text(report, encoding="utf-8")

    readable = ["# Stage 36A readable model-implied hypotheses v1", ""]
    for target_key, group in ranked.groupby("target_key"):
        readable.extend([f"## {target_key}", ""])
        for _, row2 in group.head(12).iterrows():
            label = row2["gene"] if str(row2["gene"]) else row2["module_or_component"]
            readable.append(
                f"- Rank {int(row2['rank'])}: `{label}` via `{row2['module_or_component']}`; evidence `{row2['evidence_level']}`; interpretation: {row2['interpretation']}."
            )
        readable.append("")
    READABLE_OUT.write_text("\n".join(readable), encoding="utf-8")
    return report, "\n".join(readable)


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    new = {
        "scorecard_item": "stage36a_module_counterfactual_agent",
        "status": "complete",
        "stage": "Stage 36A",
        "metric": "module-level counterfactual sensitivity on Stage 27C module_pca_ridge",
        "threshold_or_gate": "hypothesis generation only; no validation pass in this stage",
        "current_value": f"run_pass={bool(row.stage36a_run_pass)}",
        "pass_fail": "pass" if bool(row.stage36a_run_pass) else "fail",
        "datasets_allowed": "SEA-AD locked folds through frozen Stage 27C internal benchmark",
        "datasets_forbidden": "clean holdouts; external validation; external labels; therapeutic/causal claims",
        "allowed_claim": "module-level model-implied counterfactual hypotheses requiring independent validation",
        "notes": f"gene_level_pass={bool(row.stage36a_gene_level_pass)}; knowledge_grounding_pass={bool(row.stage36a_knowledge_grounding_pass)}; validation_pass=False.",
    }
    score = score[score["scorecard_item"] != "stage36a_module_counterfactual_agent"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (
            ROOT / "docs" / "ACTIVE_V3_STATUS.md",
            "\n\n## Stage 36A module counterfactual agent status\n",
            f"\nStage 36A is complete. Run pass: `{bool(row.stage36a_run_pass)}`; gene-level pass: `{bool(row.stage36a_gene_level_pass)}`; knowledge-grounding pass: `{bool(row.stage36a_knowledge_grounding_pass)}`; validation pass: `False`. Outputs are model-implied counterfactual hypotheses from the Stage 27C module_pca_ridge backbone and require independent validation. No external validation or therapeutic/causal claim update.\n",
        ),
        (
            ROOT / "docs" / "V3_SCORECARD.md",
            "\n\n## Stage 36A module counterfactual agent result\n",
            f"\nStage 36A produced module-level model-implied counterfactual hypotheses from the Stage 27C module_pca_ridge backbone. Run pass: `{bool(row.stage36a_run_pass)}`; gene-level pass: `{bool(row.stage36a_gene_level_pass)}`; knowledge-grounding pass: `{bool(row.stage36a_knowledge_grounding_pass)}`; validation pass: `False`. These are hypothesis-generation outputs only.\n",
        ),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage36a_module_counterfactual_agent_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    long_df, pred_df = run_counterfactuals(cfg)
    scores, target_summary = summarize_counterfactuals(long_df, pred_df)
    kg_inventory = find_local_knowledge(cfg)
    gene_scores, kg = gene_projection(scores, kg_inventory, cfg)
    ranked = ranked_hypotheses(scores, gene_scores, kg, cfg)
    model_audit = model_selection_audit(cfg)
    placeholder_safety = safety_audit_texts(scores.to_csv(index=False), ranked.to_csv(index=False))
    gene_level_pass = not gene_scores.empty and set(gene_scores["projection_method"].unique()) == {"exact_predefined_module_membership_projection"}
    kg_pass = bool(kg.iloc[0]["knowledge_grounding_pass"])
    run_pass = bool(
        set(cfg["required_targets"]).issubset(set(scores["target_key"]))
        and not scores.empty
        and not target_summary.empty
        and not ranked.empty
        and placeholder_safety.iloc[-1]["status"] == "pass"
    )
    pf = pd.DataFrame(
        [
            {
                "stage36a_run": True,
                "stage27c_model_loaded_or_reproduced": True,
                "locked_donor_folds_used": True,
                "all_five_targets_processed": set(cfg["required_targets"]).issubset(set(scores["target_key"])),
                "module_counterfactual_scores_written": True,
                "target_summary_written": True,
                "ranked_hypothesis_table_written": True,
                "clean_holdout_used": False,
                "external_validation_run": False,
                "external_labels_used_for_supervised_pathology_prediction": False,
                "in_silico_ablation_validated": False,
                "therapeutic_target_language_used": False,
                "causal_validation_claim_used": False,
                "experimentally_validated_targets": False,
                "stage36a_run_pass": run_pass,
                "stage36a_gene_level_pass": gene_level_pass,
                "gene_level_available": gene_level_pass,
                "gene_level_method": "module_membership_projected_gene_sensitivity" if gene_level_pass else "unavailable",
                "stage36a_knowledge_grounding_pass": kg_pass,
                "stage36a_validation_pass": False,
                "controlled_interpretation": "Stage 36A projected module-level counterfactual sensitivity to genes using exact predefined module-membership mappings. These are model-implied hypotheses, not direct gene ablations, causal claims, or experimentally validated targets." if gene_level_pass else "Stage 36A produced module-level model-implied counterfactual hypotheses. Gene-level hypotheses were not produced because an exact module-to-gene/loading map was unavailable.",
            }
        ]
    )
    report_text, readable_text = write_reports(scores, target_summary, gene_scores, kg, ranked, placeholder_safety, pf)
    safety = safety_audit_texts(report_text, readable_text, ranked.to_csv(index=False), pf.to_csv(index=False))
    pf["safety_language_audit_pass"] = safety.iloc[-1]["status"] == "pass"
    pf["stage36a_run_pass"] = pf["stage36a_run_pass"] & pf["safety_language_audit_pass"]
    write_reports(scores, target_summary, gene_scores, kg, ranked, safety, pf)

    pf.to_csv(PASS_FAIL_OUT, index=False)
    model_audit.to_csv(MODEL_AUDIT_OUT, index=False)
    scores.to_csv(MODULE_SCORES_OUT, index=False)
    target_summary.to_csv(TARGET_SUMMARY_OUT, index=False)
    gene_scores.to_csv(GENE_SCORES_OUT, index=False)
    kg.to_csv(KG_AUDIT_OUT, index=False)
    ranked.to_csv(RANKED_OUT, index=False)
    safety.to_csv(SAFETY_OUT, index=False)
    update_status(pf)
    row = pf.iloc[0]
    print(f"stage36a_run_pass={bool(row.stage36a_run_pass)}")
    print(f"stage36a_gene_level_pass={bool(row.stage36a_gene_level_pass)}")
    print(f"stage36a_knowledge_grounding_pass={bool(row.stage36a_knowledge_grounding_pass)}")
    print(f"stage36a_validation_pass={bool(row.stage36a_validation_pass)}")


if __name__ == "__main__":
    main()
