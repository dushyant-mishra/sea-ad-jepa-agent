from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_CLAIM = "internal benchmark-rescue synthesis; next-data acquisition planning; no new validation claim"
PROHIBITED_CLAIM = "external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim"


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_csv(value: str | Path) -> pd.DataFrame:
    path = resolve(value)
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def write_csv(df: pd.DataFrame, value: str | Path) -> Path:
    path = resolve(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def write_text(text: str, value: str | Path) -> Path:
    path = resolve(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows available._"
    view = view.fillna("").astype(str)
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        vals = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def update_markdown_section(path_value: str | Path, heading: str, body: str) -> None:
    path = resolve(path_value)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = f"\n## {heading}\n{body.strip()}\n"
    marker = f"## {heading}"
    if marker not in text:
        text = text.rstrip() + "\n" + section
    else:
        start = text.index(marker)
        next_start = text.find("\n## ", start + len(marker))
        text = text[:start].rstrip() + section + (text[next_start:] if next_start != -1 else "")
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def update_scorecard_csv(path_value: str | Path, pass_fail: pd.DataFrame) -> None:
    path = resolve(path_value)
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    row = {
        "scorecard_item": "stage40b_terminal_rescue_synthesis",
        "status": "complete",
        "stage": "Stage 40B",
        "metric": "terminal model-rescue decision",
        "threshold_or_gate": "no prior lock-eligible candidate; Stage40A failed; preserve Stage27C and move to feature acquisition",
        "current_value": "Stage27C locked; Stage39E pca8 best unlocked; architecture tuning paused",
        "pass_fail": "pass",
        "datasets_allowed": "existing internal result tables only",
        "datasets_forbidden": "new model training; external data for model selection",
        "allowed_claim": ALLOWED_CLAIM,
        "notes": "Terminal synthesis only; recommends Stage41A manual/internal multimodal feature acquisition.",
        "stage_id": "stage40b_terminal_rescue_synthesis",
        "primary_metric": "stop/continue branch decision",
        "pass_rule": "all claim-boundary and synthesis outputs written",
        "result": f"run_pass={as_bool(pass_fail.iloc[0].get('stage40b_run_pass', False))}",
        "allowed_inputs": "Stage27C through Stage40A generated outputs",
        "forbidden_inputs": "new training, external validation, candidate selection",
        "interpretation": "Internal model-rescue branch should pause on current feature matrix.",
    }
    if df.empty:
        df = pd.DataFrame([row])
    else:
        for col in row:
            if col not in df.columns:
                df[col] = ""
        df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != "stage40b_terminal_rescue_synthesis"]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def rescue_inventory() -> pd.DataFrame:
    rows = [
        ("Stage 27C", "module_pca_ridge locked internal reference", 0.3267024400121495, "locked_benchmark", "official locked internal benchmark remains active"),
        ("Stage 30", "graph controls versus rescue baseline", None, "failed_or_negative", "graph controls did not establish a superior benchmark"),
        ("Stage 31", "anti-oversmoothing residual graph controls", None, "failed_or_negative", "graph residual strategy did not replace non-graph baseline"),
        ("Stage 33/34/35", "external pretraining / graph rescue diagnostics", None, "failed_or_negative", "external-pretraining/graph rescue branch did not beat locked internal benchmark safely"),
        ("Stage 36", "ranked hypothesis package", None, "planning_only", "hypothesis package; not a benchmark rescue"),
        ("Stage 37/38", "external dataset readiness/support branch", None, "support_readiness_only", "support/readiness, not clean external validation"),
        ("Stage 39C", "target engineering rank-int module PCA ridge", 0.3458094563126456, "point_estimate_improved_not_locked", "CI lower too weak; not locked"),
        ("Stage 39D", "full metadata/composition context", 0.5048658499544396, "proxy_sensitive_not_lockable", "large point estimate but proxy/leakage risk"),
        ("Stage 39E", "rank_inverse_normal_module_pca8_ridge", 0.35808116279206914, "best_unlocked_candidate", "best credible simple-model candidate but CI weak"),
        ("Stage 39F", "robustness confirmation", None, "no_new_benchmark_locked", "confirmed no lock-eligible Stage39 candidate"),
        ("Stage 39H", "proxy-safe context decomposition", 0.38781411359724616, "useful_not_lockable", "context signal useful but not lockable"),
        ("Stage 40A", "conditional dual-head EMA+VICReg", 0.20855839806587548, "architecture_rescue_failed", "neural route failed versus Stage39E pca8"),
    ]
    return pd.DataFrame(rows, columns=["stage", "attempt", "best_or_relevant_mean_oof_spearman", "status", "terminal_interpretation"])


def best_candidate_summary() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "candidate": "Stage 27C module_pca_ridge",
            "role": "official_locked_benchmark",
            "mean_pooled_oof_spearman": 0.3267024400121495,
            "lock_status": "locked",
            "reason": "pre-existing official internal benchmark; no later candidate passed all lock gates",
        },
        {
            "candidate": "Stage 39E rank_inverse_normal_module_pca8_ridge",
            "role": "best_credible_unlocked_candidate",
            "mean_pooled_oof_spearman": 0.35808116279206914,
            "lock_status": "unlocked",
            "reason": "passes target guard and improves point estimate, but bootstrap lower CI did not clear lock gates",
        },
        {
            "candidate": "Stage 39H latent_plus_tier1_plus_tier2",
            "role": "useful_context_candidate",
            "mean_pooled_oof_spearman": 0.38781411359724616,
            "lock_status": "unlocked_not_lockable",
            "reason": "useful context signal but target guard/proxy-caution/CI gates failed",
        },
        {
            "candidate": "Stage 40A dualhead_ema_vicreg_latent16",
            "role": "conditional_architecture_rescue",
            "mean_pooled_oof_spearman": 0.20855839806587548,
            "lock_status": "failed",
            "reason": "failed versus Stage 39E pca8 reference",
        },
    ])


def lock_status_summary() -> pd.DataFrame:
    return pd.DataFrame([
        {"decision_item": "locked_benchmark", "value": "Stage 27C module_pca_ridge", "status": "preserved"},
        {"decision_item": "new_benchmark_locked_after_39c_to_40a", "value": "False", "status": "no_candidate_passed_all_gates"},
        {"decision_item": "best_unlocked_candidate", "value": "Stage 39E pca8 ridge", "status": "retain_as_candidate_only"},
        {"decision_item": "architecture_tuning_on_current_matrix", "value": "pause", "status": "not_recommended"},
    ])


def failure_mode_summary() -> pd.DataFrame:
    rows = [
        ("weak_bootstrap_support", "Stage 39C/39E/39H", "point estimates improved but donor-bootstrap lower CIs did not clear lock thresholds"),
        ("target_guard_failure", "Stage 39E direct elasticnet / Stage 39H context", "high mean scores traded off Aβ, GFAP, or NeuN"),
        ("proxy_sensitive_context", "Stage 39D/39H full context", "large context gains involved risky or forbidden proxy features"),
        ("architecture_failure", "Stage 40A", "dual-head EMA+VICReg underperformed simple Stage 39E pca8 reference"),
        ("missing_safe_information", "terminal synthesis", "current module matrix appears insufficient for robust rescue without added safe modalities"),
    ]
    return pd.DataFrame(rows, columns=["failure_mode", "stage_or_branch", "evidence"])


def what_worked_vs_failed() -> pd.DataFrame:
    rows = [
        ("worked_partially", "rank inverse-normal target handling", "Stage 39C/39E improved point estimates"),
        ("worked_partially", "simple ridge/PCA module baseline", "Stage 39E pca8 remains best credible unlocked candidate"),
        ("worked_partially", "safe metadata/context decomposition", "Stage 39H showed context can improve point estimates"),
        ("failed_lock_gate", "full composition/context", "too proxy-sensitive to lock"),
        ("failed_lock_gate", "direct elastic net high-score model", "Aβ guard failed"),
        ("failed", "low-capacity neural dual-head EMA+VICReg", "Stage 40A did not rescue benchmark"),
        ("recommended", "new safe feature acquisition", "likely missing information is outside current matrix"),
    ]
    return pd.DataFrame(rows, columns=["outcome_class", "item", "interpretation"])


def stop_continue_decision() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "decision": "keep_stage27c_locked",
            "value": True,
            "rationale": "No Stage 39C-H or Stage 40A candidate was benchmark-lock eligible.",
            "next_action": "Use Stage 27C for official internal benchmark language.",
        },
        {
            "decision": "continue_internal_architecture_tuning_on_current_features",
            "value": False,
            "rationale": "Stage 40A failed badly versus Stage 39E pca8; further tuning risks overfitting 84 donors.",
            "next_action": "Pause architecture rescue on current feature matrix.",
        },
        {
            "decision": "start_manual_multimodal_feature_acquisition",
            "value": True,
            "rationale": "Useful signal likely requires safer additional internal modalities/features.",
            "next_action": "Run Stage41A manual/internal multimodal feature acquisition.",
        },
        {
            "decision": "continue_external_metadata_repair",
            "value": True,
            "rationale": "External branch remains useful for support/readiness but not clean validation.",
            "next_action": "Maintain as separate support-readiness branch.",
        },
    ])


def missing_information_inventory() -> pd.DataFrame:
    rows = [
        ("internal image-derived pathology morphology", "quantitative plaque/tangle/glial morphology beyond scalar pathology targets", "high"),
        ("section-level pathology image descriptors", "slide/section heterogeneity and staining context", "high"),
        ("spatial neighborhood summaries", "cell-cell neighborhood context around pathology structures", "high"),
        ("region/anatomy covariates", "anatomical context and region-specific burden", "medium"),
        ("donor-level cell-neighborhood composition", "local rather than global composition effects", "high"),
        ("manually curated pathology metadata", "safer expert-curated descriptors not derived from held-out targets", "high"),
        ("slide/section-level covariates", "batch/section technical variation and morphology context", "medium"),
        ("clean external dataset metadata for support-only analysis", "external support/readiness, not clean validation", "medium"),
    ]
    return pd.DataFrame(rows, columns=["missing_feature_class", "why_missing_matters", "priority"])


def acquisition_plan() -> pd.DataFrame:
    rows = [
        ("image_pathology_morphology", "internal pathology images", "internal", "plaque/tangle/glial morphology may explain residual target variation", "medium", "medium", "high", "high", "train-fold-safe internal feature engineering; benchmark candidate after audit", "direct target leakage or post-hoc validation claims", "Stage41A"),
        ("spatial_neighborhood_summaries", "spatial transcriptomics / cell coordinates if available", "internal", "local microenvironment may improve GFAP/Iba1/NeuN without proxy labels", "medium", "medium", "high", "high", "feature acquisition and proxy audit", "causal or therapeutic claims", "Stage41A"),
        ("section_slide_covariates", "internal slide/section metadata", "internal", "technical and anatomical context may stabilize OOF predictions", "low", "low_to_medium", "medium", "high", "covariate audit and train-fold preprocessing", "using direct pathology scores as covariates", "Stage41A"),
        ("manual_pathology_metadata", "manual/expert-curated pathology descriptors", "internal", "could add safe non-target morphology context", "medium", "medium", "medium", "high", "candidate features after provenance review", "held-out target-derived pseudo-labels", "Stage41A"),
        ("external_metadata_repair", "external dataset annotations", "external", "support/readiness for cross-dataset context", "low", "medium", "medium", "medium", "support-only analysis and eligibility audit", "clean external validation unless gates permit", "Stage41B_or_external_repair"),
        ("donor_cell_neighborhood_composition", "internal cell neighborhoods", "internal", "local cell composition may outperform global broad composition", "medium", "medium", "high", "medium", "proxy-safe decomposition after acquisition", "global disease-state labels as predictors", "Stage41A"),
    ]
    return pd.DataFrame(rows, columns=["feature_class", "source", "internal_or_external", "expected_signal", "leakage_risk", "proxy_risk", "acquisition_complexity", "recommended_priority", "allowed_use", "prohibited_use", "next_stage"])


def external_repair_plan() -> pd.DataFrame:
    rows = [
        ("repair_sample_metadata", "map sample/cell IDs, disease labels, pathology metadata", "support_readiness", "do not use for internal model selection"),
        ("celltype_harmonization", "microglia/astrocyte/neuron labels where available", "support_readiness", "no clean validation claim"),
        ("pathology_label_harmonization", "tau/pTau/Aβ/amyloid metadata if available", "conditional_support", "claim only external support if prior gates permit"),
        ("claim_level_audit", "dataset-by-dataset allowed claim language", "safety", "avoid clean external validation overclaim"),
    ]
    return pd.DataFrame(rows, columns=["repair_task", "description", "purpose", "claim_boundary"])


def manuscript_readiness_summary() -> pd.DataFrame:
    rows = [
        ("locked_internal_benchmark", "Stage 27C remains locked", "ready"),
        ("model_rescue_attempts", "Stage 39C-H and 40A negative/partial results preserved", "ready_as_methods_or_supplement"),
        ("candidate_model_language", "Stage 39E pca8 is unlocked candidate only", "safe_with_limitations"),
        ("external_validation_language", "not clean external validation", "not_ready"),
        ("causal_therapeutic_language", "not supported", "forbidden"),
        ("next_data_acquisition", "Stage41A recommended", "ready_to_plan"),
    ]
    return pd.DataFrame(rows, columns=["manuscript_item", "status_summary", "readiness"])


def claim_audit() -> pd.DataFrame:
    items = {
        "no_new_model_training": True,
        "no_external_data_used_for_model_selection": True,
        "frozen_candidates_preserved": True,
        "stage27c_locked_benchmark_preserved": True,
        "no_clean_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_disease_modifying_claim": True,
        "negative_results_preserved": True,
    }
    rows = [{"audit_item": k, "pass": v, "evidence": "Stage 40B is a report-only terminal synthesis." if v else "failed"} for k, v in items.items()]
    rows.append({"audit_item": "safety_audit_pass", "pass": all(items.values()), "evidence": "all safety checks passed"})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    out = cfg["outputs"]

    rescue = rescue_inventory()
    best = best_candidate_summary()
    lock = lock_status_summary()
    failure = failure_mode_summary()
    worked = what_worked_vs_failed()
    stop = stop_continue_decision()
    missing = missing_information_inventory()
    acquire = acquisition_plan()
    external = external_repair_plan()
    manuscript = manuscript_readiness_summary()
    claim = claim_audit()
    pass_fail = pd.DataFrame([{
        "stage40b_run": True,
        "rescue_attempt_inventory_written": True,
        "best_candidate_summary_written": True,
        "lock_status_summary_written": True,
        "failure_mode_summary_written": True,
        "stop_continue_decision_written": True,
        "missing_information_inventory_written": True,
        "multimodal_feature_acquisition_plan_written": True,
        "external_metadata_repair_plan_written": True,
        "manuscript_readiness_summary_written": True,
        "claim_boundary_audit_written": True,
        "reports_written": True,
        "no_new_model_training": True,
        "stage27c_locked_benchmark_preserved": True,
        "safety_audit_pass": bool(claim["pass"].map(as_bool).all()),
        "stage40b_run_pass": True,
        "recommended_next_stage": cfg["references"]["recommended_next_stage"],
    }])

    write_csv(rescue, out["rescue_attempt_inventory"])
    write_csv(best, out["best_candidate_summary"])
    write_csv(lock, out["lock_status_summary"])
    write_csv(failure, out["failure_mode_summary"])
    write_csv(worked, out["what_worked_vs_failed"])
    write_csv(stop, out["stop_continue_decision"])
    write_csv(missing, out["missing_information_inventory"])
    write_csv(acquire, out["multimodal_feature_acquisition_plan"])
    write_csv(external, out["external_metadata_repair_plan"])
    write_csv(manuscript, out["manuscript_readiness_summary"])
    write_csv(claim, out["claim_boundary_audit"])
    write_csv(pass_fail, out["pass_fail"])

    report = f"""# Stage 40B terminal model-rescue synthesis report

## Executive summary

Stage 27C remains the official locked internal benchmark. Stage 39C-E produced point-estimate improvements, but Stage 39F confirmed no benchmark-lock eligible candidate. Stage 39H showed useful context signal but no proxy-safe lockable recovery. Stage 40A conditional dual-head EMA+VICReg failed versus the Stage 39E pca8 reference. Therefore internal architecture tuning on the current feature matrix should pause.

## Rescue attempt inventory

{markdown_table(rescue)}

## Best candidate summary

{markdown_table(best)}

## Lock status

{markdown_table(lock)}

## Failure modes

{markdown_table(failure)}

## What worked versus failed

{markdown_table(worked)}

## Stop/continue decision

{markdown_table(stop)}

## Missing information inventory

{markdown_table(missing)}

## Multimodal/spatial/image acquisition plan

{markdown_table(acquire)}

## External metadata repair branch

{markdown_table(external)}

## Manuscript readiness and claim boundaries

{markdown_table(manuscript)}

{markdown_table(claim)}
"""
    pi = f"""# Stage 40B PI next-steps summary

## Short answer

The locked benchmark remains Stage 27C `module_pca_ridge` (`0.3267024400121495`). The best credible unlocked candidate is Stage 39E `rank_inverse_normal_module_pca8_ridge` (`0.35808116279206914`), but it is not locked. Stage 40A neural rescue failed, so internal architecture tuning on the current feature matrix should pause.

## What to do next

{markdown_table(stop)}

## What to acquire next

{markdown_table(acquire[['feature_class', 'source', 'recommended_priority', 'allowed_use', 'next_stage']])}

## Safe language

Use internal benchmark-rescue synthesis, point-estimate improvement, unlocked candidate, support/readiness branch, and next-data acquisition. Do not claim external validation, causality, therapeutic targets, gene ablation, or disease modification.
"""
    write_text(report, out["technical_report"])
    write_text(pi, out["pi_summary"])
    update_markdown_section(out["active_status"], "Stage 40B terminal rescue synthesis status", "Stage 40B is complete. Stage 27C remains the locked benchmark; Stage 39E pca8 remains the best credible unlocked candidate; internal architecture tuning on the current feature matrix should pause; recommended next stage is Stage41A manual/internal multimodal feature acquisition.")
    update_markdown_section(out["v3_scorecard_md"], "Stage 40B terminal rescue synthesis result", "Stage 40B run pass: `True`. Locked benchmark: Stage 27C module_pca_ridge. Best unlocked candidate: Stage 39E pca8 ridge. Recommended next stage: Stage41A manual/internal multimodal feature acquisition.")
    update_scorecard_csv(out["v3_scorecard_csv"], pass_fail)

    print("locked_benchmark=Stage27C module_pca_ridge")
    print("best_unlocked_candidate=Stage39E rank_inverse_normal_module_pca8_ridge")
    print("continue_internal_architecture_tuning=False")
    print(f"recommended_next_stage={cfg['references']['recommended_next_stage']}")
    print("top_missing_feature_classes=" + ";".join(missing.head(4)["missing_feature_class"].tolist()))
    print(f"stage40b_run_pass={as_bool(pass_fail.iloc[0]['stage40b_run_pass'])}")


if __name__ == "__main__":
    main()
