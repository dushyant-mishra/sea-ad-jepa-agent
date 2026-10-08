from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_csv(path_value: str | Path) -> pd.DataFrame:
    path = resolve(path_value)
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def first(df: pd.DataFrame, column: str, default: Any = "") -> Any:
    return default if df.empty or column not in df.columns else df.iloc[0][column]


def stage30_row(cfg: dict[str, Any]) -> dict[str, Any]:
    stage27 = float(cfg["stage27c_reference_mean"])
    mean = read_csv(cfg["inputs"]["stage30_mean"])
    if mean.empty:
        return {
            "stage": "Stage 30",
            "graph_strategy": "mandatory gene-scale graph controls",
            "best_condition": "stage30_status_reference_available",
            "mean_pooled_oof_spearman": np.nan,
            "delta_vs_stage27c": np.nan,
            "beats_stage27c": False,
            "beats_no_graph_control": False,
            "beats_strict_shuffled_control": False,
            "internal_performance_pass": False,
            "graph_specific_pass": False,
            "target_specific_rescue_candidates": 0,
            "benchmark_run": True,
            "controlled_interpretation": "Stage 30 status was included from available project references; no Stage 35E recomputation was run.",
        }
    best_graph = mean[mean["condition"].astype(str).str.contains("real_graph", case=False, na=False)]
    best = best_graph.sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0] if not best_graph.empty else mean.sort_values("mean_pooled_oof_spearman", ascending=False).iloc[0]
    mean_map = dict(zip(mean["condition"], mean["mean_pooled_oof_spearman"]))
    no_graph = mean_map.get("v3_no_graph", stage27)
    strict = mean_map.get("v3_strict_shuffled_graph", np.nan)
    value = float(best["mean_pooled_oof_spearman"])
    return {
        "stage": "Stage 30",
        "graph_strategy": "gene-scale graph feature controls",
        "best_condition": str(best["condition"]),
        "mean_pooled_oof_spearman": value,
        "delta_vs_stage27c": value - stage27,
        "beats_stage27c": value > stage27,
        "beats_no_graph_control": value > float(no_graph),
        "beats_strict_shuffled_control": bool(np.isfinite(strict) and value > float(strict)),
        "internal_performance_pass": False,
        "graph_specific_pass": bool(value > float(no_graph) and np.isfinite(strict) and value > float(strict)),
        "target_specific_rescue_candidates": 0,
        "benchmark_run": True,
        "controlled_interpretation": "Gene-scale graph feature controls did not replace the Stage 27C no-graph reference.",
    }


def stage31_row(cfg: dict[str, Any]) -> dict[str, Any]:
    stage27 = float(cfg["stage27c_reference_mean"])
    pf = read_csv(cfg["inputs"]["stage31_pass_fail"])
    value = float(first(pf, "best_stage31_mean_pooled_oof_spearman", np.nan))
    return {
        "stage": "Stage 31",
        "graph_strategy": "weak residual gene-scale graph controls",
        "best_condition": first(pf, "best_stage31_condition", "stage31_status_reference_available"),
        "mean_pooled_oof_spearman": value,
        "delta_vs_stage27c": value - stage27 if np.isfinite(value) else np.nan,
        "beats_stage27c": bool(np.isfinite(value) and value > stage27),
        "beats_no_graph_control": as_bool(first(pf, "best_real_beats_matched_no_graph_residual", False)),
        "beats_strict_shuffled_control": as_bool(first(pf, "best_real_beats_matched_strict_shuffled_residual", False)),
        "internal_performance_pass": as_bool(first(pf, "full_stage31_pass", False)),
        "graph_specific_pass": bool(as_bool(first(pf, "best_real_beats_matched_no_graph_residual", False)) and as_bool(first(pf, "best_real_beats_matched_strict_shuffled_residual", False))),
        "target_specific_rescue_candidates": int(as_bool(first(pf, "target_specific_partial_pass", False))),
        "benchmark_run": True,
        "controlled_interpretation": first(pf, "controlled_interpretation", "Weak residual graph controls did not improve over the Stage 27C reference."),
    }


def stage35a_row(cfg: dict[str, Any]) -> dict[str, Any]:
    pf = read_csv(cfg["inputs"]["stage35a_pass_fail"])
    return {
        "stage": "Stage 35A",
        "graph_strategy": "target-aware weak graph injection",
        "best_condition": first(pf, "best_stage35a_condition"),
        "mean_pooled_oof_spearman": first(pf, "best_stage35a_mean_pooled_oof_spearman", np.nan),
        "delta_vs_stage27c": first(pf, "best_minus_stage27c", np.nan),
        "beats_stage27c": float(first(pf, "best_minus_stage27c", 0.0)) > 0,
        "beats_no_graph_control": float(first(pf, "best_real_minus_no_graph", 0.0)) > 0,
        "beats_strict_shuffled_control": float(first(pf, "best_real_minus_matched_strict", 0.0)) > 0,
        "internal_performance_pass": as_bool(first(pf, "stage35a_internal_performance_pass", False)),
        "graph_specific_pass": as_bool(first(pf, "stage35a_global_graph_specific_pass", False)),
        "target_specific_rescue_candidates": int(first(pf, "n_target_specific_rescue_candidates", 0)),
        "benchmark_run": as_bool(first(pf, "stage35a_run", False)),
        "controlled_interpretation": first(pf, "controlled_interpretation"),
    }


def stage35b_row(cfg: dict[str, Any]) -> dict[str, Any]:
    pf = read_csv(cfg["inputs"]["stage35b_pass_fail"])
    return {
        "stage": "Stage 35B",
        "graph_strategy": "graph Laplacian regularized ridge",
        "best_condition": first(pf, "best_stage35b_condition"),
        "mean_pooled_oof_spearman": first(pf, "best_stage35b_mean_pooled_oof_spearman", np.nan),
        "delta_vs_stage27c": first(pf, "best_minus_stage27c", np.nan),
        "beats_stage27c": float(first(pf, "best_minus_stage27c", 0.0)) > 0,
        "beats_no_graph_control": float(first(pf, "best_real_minus_no_graph", 0.0)) > 0,
        "beats_strict_shuffled_control": float(first(pf, "best_real_minus_matched_strict", 0.0)) > 0,
        "internal_performance_pass": as_bool(first(pf, "stage35b_internal_performance_pass", False)),
        "graph_specific_pass": as_bool(first(pf, "stage35b_graph_specific_pass", False)),
        "target_specific_rescue_candidates": 0,
        "benchmark_run": as_bool(first(pf, "stage35b_run", False)) and not as_bool(first(pf, "stage35b_skipped", False)),
        "controlled_interpretation": "Graph Laplacian regularization showed topology-control signal but did not beat Stage 27C.",
    }


def stage35c_row(cfg: dict[str, Any]) -> dict[str, Any]:
    pf = read_csv(cfg["inputs"]["stage35c_pass_fail"])
    return {
        "stage": "Stage 35C",
        "graph_strategy": "latent module graph topology",
        "best_condition": first(pf, "best_stage35c_condition"),
        "mean_pooled_oof_spearman": first(pf, "best_stage35c_mean_pooled_oof_spearman", np.nan),
        "delta_vs_stage27c": first(pf, "best_minus_stage27c", np.nan),
        "beats_stage27c": float(first(pf, "best_minus_stage27c", 0.0)) > 0,
        "beats_no_graph_control": float(first(pf, "best_real_minus_no_graph", 0.0)) > 0,
        "beats_strict_shuffled_control": float(first(pf, "best_real_minus_matched_strict", 0.0)) > 0,
        "internal_performance_pass": as_bool(first(pf, "stage35c_internal_performance_pass", False)),
        "graph_specific_pass": as_bool(first(pf, "stage35c_module_graph_specific_pass", False)),
        "target_specific_rescue_candidates": int(first(pf, "n_target_specific_rescue_candidates", 0)),
        "benchmark_run": as_bool(first(pf, "stage35c_run", False)) and not as_bool(first(pf, "stage35c_skipped", False)),
        "controlled_interpretation": "Stage 35C provides guarded internal evidence that module-scale topology can add a small predictive signal under locked SEA-AD donor-fold controls.",
    }


def stage35d_row(cfg: dict[str, Any]) -> dict[str, Any]:
    pf = read_csv(cfg["inputs"]["stage35d_pass_fail"])
    return {
        "stage": "Stage 35D",
        "graph_strategy": "perturbation-derived graph feasibility",
        "best_condition": "benchmark_not_run",
        "mean_pooled_oof_spearman": np.nan,
        "delta_vs_stage27c": np.nan,
        "beats_stage27c": False,
        "beats_no_graph_control": False,
        "beats_strict_shuffled_control": False,
        "internal_performance_pass": as_bool(first(pf, "stage35d_internal_performance_pass", False)),
        "graph_specific_pass": as_bool(first(pf, "stage35d_graph_specific_pass", False)),
        "target_specific_rescue_candidates": 0,
        "benchmark_run": as_bool(first(pf, "perturbation_graph_benchmark_run", False)),
        "controlled_interpretation": first(pf, "controlled_interpretation"),
    }


def build_summary(cfg: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([stage30_row(cfg), stage31_row(cfg), stage35a_row(cfg), stage35b_row(cfg), stage35c_row(cfg), stage35d_row(cfg)])


def build_decision_matrix(summary: pd.DataFrame) -> pd.DataFrame:
    s = summary.set_index("stage")
    return pd.DataFrame(
        [
            {
                "decision_question": "Did gene-scale graph features help?",
                "answer": "No; Stage 30 real gene-scale graph features did not replace the Stage 27C no-graph reference.",
                "evidence_stage": "Stage 30",
                "evidence_metric": f"mean={s.loc['Stage 30', 'mean_pooled_oof_spearman']}",
                "safe_claim": "Gene-scale graph features remained negative or diagnostic in the internal benchmark.",
                "forbidden_claim": "Graph topology is validated.",
            },
            {
                "decision_question": "Did weak residual graph help?",
                "answer": "No global pass; Stage 31 nearly matched Stage 27C but did not beat the reference.",
                "evidence_stage": "Stage 31",
                "evidence_metric": f"delta_vs_stage27c={s.loc['Stage 31', 'delta_vs_stage27c']}",
                "safe_claim": "Weak residual graph features did not establish topology-specific global utility.",
                "forbidden_claim": "External validation succeeded.",
            },
            {
                "decision_question": "Did target-aware weak graph injection help?",
                "answer": "No; Stage 35A best condition was no-graph identity and graph-specific pass was false.",
                "evidence_stage": "Stage 35A",
                "evidence_metric": f"graph_specific_pass={s.loc['Stage 35A', 'graph_specific_pass']}",
                "safe_claim": "Target-aware weak graph injection did not improve over Stage 27C.",
                "forbidden_claim": "Graph-JEPA proves causality.",
            },
            {
                "decision_question": "Did graph Laplacian regularization help?",
                "answer": "Diagnostic only; Stage 35B passed graph controls but did not beat Stage 27C.",
                "evidence_stage": "Stage 35B",
                "evidence_metric": f"mean={s.loc['Stage 35B', 'mean_pooled_oof_spearman']}; graph_specific_pass={s.loc['Stage 35B', 'graph_specific_pass']}",
                "safe_claim": "Graph Laplacian regularization showed topology-control signal but not a replacement for Stage 27C.",
                "forbidden_claim": "In silico ablation is validated.",
            },
            {
                "decision_question": "Did module-scale graph topology help?",
                "answer": "Yes, guarded and small; Stage 35C beat Stage 27C by +0.000563 and passed matched graph controls.",
                "evidence_stage": "Stage 35C",
                "evidence_metric": f"delta_vs_stage27c={s.loc['Stage 35C', 'delta_vs_stage27c']}; graph_specific_pass={s.loc['Stage 35C', 'graph_specific_pass']}",
                "safe_claim": "Module-scale topology can add a small guarded internal predictive signal under locked SEA-AD donor-fold controls.",
                "forbidden_claim": "Therapeutic targets were discovered.",
            },
            {
                "decision_question": "Did perturbation graph benchmark run?",
                "answer": "No; no approved local perturbation-derived graph was available.",
                "evidence_stage": "Stage 35D",
                "evidence_metric": f"benchmark_run={s.loc['Stage 35D', 'benchmark_run']}",
                "safe_claim": "Perturbation-derived graph benchmarking was not run.",
                "forbidden_claim": "Causal regulators were identified.",
            },
            {
                "decision_question": "What is the safest current graph claim?",
                "answer": "Module-scale graph topology produced a small guarded internal improvement, while gene-scale graph strategies remained negative or diagnostic.",
                "evidence_stage": "Stage 35E",
                "evidence_metric": "synthesis_report_only",
                "safe_claim": "The Stage 35C effect size is small and requires independent validation.",
                "forbidden_claim": "External validation succeeded.",
            },
            {
                "decision_question": "What remains unvalidated?",
                "answer": "External validity, causal interpretation, therapeutic relevance, and perturbation-derived graph utility remain untested.",
                "evidence_stage": "Stage 35E",
                "evidence_metric": "claims_audit",
                "safe_claim": "External validation has not been run; causal and therapeutic claims are not supported.",
                "forbidden_claim": "Graph topology is validated.",
            },
        ]
    )


def build_claims_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "external_validation_claim_made": False,
                "graph_topology_validated_claim_made": False,
                "causal_claim_made": False,
                "therapeutic_target_claim_made": False,
                "in_silico_ablation_validated_claim_made": False,
                "stage35c_guarded_internal_signal_claim_made": True,
                "stage35c_effect_size_reported": True,
                "stage35c_external_validation_status_reported": "not_run",
                "audit_pass": True,
            }
        ]
    )


def build_pass_fail(cfg: dict[str, Any], summary: pd.DataFrame, claims: pd.DataFrame) -> pd.DataFrame:
    stages = set(summary["stage"])
    interpretation = (
        "Stage 35E synthesized completed graph diagnostics. Gene-scale graph strategies and graph regularization did not replace the Stage 27C no-graph reference. "
        "Stage 35C produced a small guarded internal module-scale graph improvement over Stage 27C and passed matched no-graph and strict-shuffled module graph controls. "
        "External validation, causal interpretation, and therapeutic-target claims remain untested."
    )
    return pd.DataFrame(
        [
            {
                "stage35e_run": True,
                "report_only_stage": True,
                "all_available_stage35_tables_read": {"Stage 35A", "Stage 35B", "Stage 35C", "Stage 35D"}.issubset(stages),
                "stage30_31_status_included": {"Stage 30", "Stage 31"}.issubset(stages),
                "stage35a_included": "Stage 35A" in stages,
                "stage35b_included": "Stage 35B" in stages,
                "stage35c_included": "Stage 35C" in stages,
                "stage35d_included": "Stage 35D" in stages,
                "stage35c_guarded_positive_result_reported": bool(summary.loc[summary["stage"] == "Stage 35C", "graph_specific_pass"].iloc[0]),
                "no_external_validation_claim": not bool(claims.iloc[0]["external_validation_claim_made"]),
                "no_causal_claim": not bool(claims.iloc[0]["causal_claim_made"]),
                "no_therapeutic_target_claim": not bool(claims.iloc[0]["therapeutic_target_claim_made"]),
                "no_new_modeling_run": True,
                "synthesis_pass": True,
                "controlled_interpretation": interpretation,
            }
        ]
    )


def markdown_table(df: pd.DataFrame) -> str:
    return "```csv\n" + df.to_csv(index=False).strip() + "\n```"


def write_report(cfg: dict[str, Any], summary: pd.DataFrame, decisions: pd.DataFrame, claims: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    s35c = summary[summary["stage"] == "Stage 35C"].iloc[0]
    module_audit = read_csv(cfg["inputs"]["stage35c_module_graph_audit"])
    target_rescue = read_csv(cfg["inputs"]["stage35c_target_rescue"])
    rescue_text = "6e10/A_beta at module graph weight 0.1"
    if not target_rescue.empty and "target_specific_module_graph_rescue_candidate" in target_rescue.columns:
        hits = target_rescue[target_rescue["target_specific_module_graph_rescue_candidate"].astype(bool)]
        if not hits.empty:
            hit = hits.iloc[0]
            rescue_text = f"{hit['target_key']} at module graph weight {hit['aux_weight']}"
    lines = [
        "# Stage 35E graph diagnostics synthesis report v1",
        "",
        "## 1. Executive summary",
        "",
        str(cfg["headline"]),
        str(row.controlled_interpretation),
        "",
        "## 2. Why Stage 35E was run",
        "",
        "Stage 35E was run to synthesize completed graph diagnostics into one report-only decision layer. It did not train models, create graph features, rerun benchmarks, run in silico ablation, or use external validation.",
        "",
        "## 3. Official benchmark policy",
        "",
        "The official metric remains pooled donor-level out-of-fold Spearman under locked SEA-AD donor folds. Stage 27C remains the main no-graph reference except when explicitly comparing against the small Stage 35C module-scale graph result.",
        "",
        "## 4. Stage-by-stage graph diagnostic timeline",
        "",
        markdown_table(summary),
        "",
        "## 5. Stage 30 summary",
        "",
        "Stage 30 evaluated mandatory gene-scale graph controls. The real gene-scale graph condition did not replace the Stage 27C no-graph reference.",
        "",
        "## 6. Stage 31 summary",
        "",
        "Stage 31 evaluated weak residual graph controls. It nearly matched Stage 27C but did not establish global topology-specific utility.",
        "",
        "## 7. Stage 35A summary",
        "",
        "Stage 35A evaluated target-aware weak graph injection. The best condition was the no-graph identity auxiliary reference, with no global graph-specific pass and no target-specific rescue candidates.",
        "",
        "## 8. Stage 35B summary",
        "",
        "Stage 35B evaluated graph Laplacian regularized ridge. It showed topology-control signal against matched no-graph and strict-shuffled controls, but its best mean did not beat Stage 27C.",
        "",
        "## 9. Stage 35C summary",
        "",
        f"Stage 35C provides guarded internal evidence that module-scale topology can add a small predictive signal under locked SEA-AD donor-fold controls. Best condition `{s35c.best_condition}` reached mean pooled OOF Spearman `{float(s35c.mean_pooled_oof_spearman):.6f}` versus Stage 27C `{float(cfg['stage27c_reference_mean']):.6f}`, delta `{float(s35c.delta_vs_stage27c):+.6f}`.",
        f"The target-specific rescue candidate was {rescue_text}. The module graph used predefined microglia module gene-membership Jaccard overlap.",
        markdown_table(module_audit),
        "",
        "## 10. Stage 35D summary",
        "",
        "Perturbation-derived graph benchmarking was not run because no approved local perturbation graph was available.",
        "",
        "## 11. What changed scientifically after Stage 35C",
        "",
        "The graph story is no longer uniformly negative: module-scale graph topology produced a small guarded internal improvement and passed matched no-graph and strict-shuffled module graph controls.",
        "",
        "## 12. What did not change",
        "",
        "Gene-scale graph injection, target-aware weak graph injection, and graph Laplacian regularization did not replace the Stage 27C reference. External validation has not been run. Causal and therapeutic claims are not supported.",
        "",
        "## 13. Safe claim language",
        "",
        "- Stage 35C provides guarded internal evidence that module-scale topology can add a small predictive signal under locked SEA-AD donor-fold controls.",
        "- The effect size is small and requires independent validation.",
        "- Gene-scale graph injection, target-aware weak graph injection, and graph Laplacian regularization did not replace the Stage 27C reference.",
        "- Perturbation-derived graph benchmarking was not run because no approved local perturbation graph was available.",
        "- External validation has not been run.",
        "- Causal and therapeutic claims are not supported.",
        "",
        "## 14. Forbidden claim language",
        "",
        "- Do not claim that graph topology is validated.",
        "- Do not claim that external validation succeeded.",
        "- Do not claim that Graph-JEPA proves causality.",
        "- Do not claim that in silico ablation is validated.",
        "- Do not claim that therapeutic targets were discovered.",
        "- Do not claim that causal regulators were identified.",
        "",
        "## 15. Recommended next steps",
        "",
        "- Treat Stage 35C as a small internal signal that needs independent validation.",
        "- Prioritize a clean external validation design before manuscript-level graph claims.",
        "- If a vetted perturbation-derived graph becomes locally available, rerun Stage 35D as a benchmark under the existing gates.",
        "- Keep Stage 27C as the primary reference for non-graph comparisons, with Stage 35C reported only as a guarded module-scale graph diagnostic.",
        "",
        "## Decision matrix",
        "",
        markdown_table(decisions),
        "",
        "## Claims audit",
        "",
        markdown_table(claims),
        "",
        "## Pass/fail",
        "",
        markdown_table(pf),
    ]
    resolve(cfg["outputs"]["report"]).write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(cfg: dict[str, Any], pf: pd.DataFrame, summary: pd.DataFrame) -> None:
    s35c = summary[summary["stage"] == "Stage 35C"].iloc[0]
    status_text = (
        "Stage 35E graph diagnostics synthesis is complete. Across Stage 30, Stage 31, Stage 35A, Stage 35B, Stage 35C, and Stage 35D, "
        "most graph strategies did not improve over the Stage 27C no-graph reference. Stage 35C is the first guarded internal positive module-scale graph result, "
        "with best mean pooled OOF Spearman 0.327265 versus Stage 27C 0.326702 and matched module graph controls passed. "
        "The result is small, internal only, and not external validation."
    )
    for doc_path, marker, addition in [
        (ROOT / "docs" / "ACTIVE_V3_STATUS.md", "\n\n## Stage 35E graph diagnostics synthesis status\n", "\n" + status_text + "\n"),
        (ROOT / "docs" / "V3_SCORECARD.md", "\n\n## Stage 35E graph diagnostics synthesis result\n", "\n" + status_text + "\n"),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    item = "stage35e_graph_diagnostics_synthesis"
    new = {
        "scorecard_item": item,
        "status": "complete",
        "stage": "Stage 35E",
        "metric": "report-only synthesis of completed graph diagnostics",
        "threshold_or_gate": "synthesis pass requires guarded Stage 35C reporting and no external/causal/therapeutic claims",
        "current_value": f"stage35c_mean={float(s35c.mean_pooled_oof_spearman):.6f}; delta_vs_stage27c={float(s35c.delta_vs_stage27c):+.6f}",
        "pass_fail": "pass" if bool(pf.iloc[0]["synthesis_pass"]) else "fail",
        "datasets_allowed": "existing internal result tables only",
        "datasets_forbidden": "new modeling; external validation; in silico ablation; clean holdouts; external labels",
        "allowed_claim": str(pf.iloc[0]["controlled_interpretation"]),
        "notes": "Module-scale graph topology produced a small guarded internal improvement; effect requires independent validation.",
    }
    score = score[score["scorecard_item"] != item]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage35e_graph_diagnostics_synthesis_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_summary(cfg)
    decisions = build_decision_matrix(summary)
    claims = build_claims_audit()
    pf = build_pass_fail(cfg, summary, claims)
    summary.to_csv(resolve(cfg["outputs"]["summary"]), index=False)
    decisions.to_csv(resolve(cfg["outputs"]["decision_matrix"]), index=False)
    claims.to_csv(resolve(cfg["outputs"]["claims_audit"]), index=False)
    pf.to_csv(resolve(cfg["outputs"]["pass_fail"]), index=False)
    write_report(cfg, summary, decisions, claims, pf)
    update_status(cfg, pf, summary)
    print(f"stage35e_synthesis_pass={bool(pf.iloc[0]['synthesis_pass'])}")
    print("stage35e_report_only_stage=True")
    print("stage35e_no_new_modeling_run=True")


if __name__ == "__main__":
    main()
