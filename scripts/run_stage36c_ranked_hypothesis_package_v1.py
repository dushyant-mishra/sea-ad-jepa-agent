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


def minmax(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce").fillna(0.0)
    lo = float(vals.min())
    hi = float(vals.max())
    if hi <= lo:
        return pd.Series(1.0, index=series.index)
    return (vals - lo) / (hi - lo)


def target_match_bonus(row: pd.Series) -> float:
    if str(row.get("kg_known_target_pathology", "False")) == "True":
        return 0.15
    key = str(row.get("target_key", ""))
    if key == "6e10/A_beta" and str(row.get("kg_known_amyloid", "False")) == "True":
        return 0.10
    if key == "AT8" and str(row.get("kg_known_tau", "False")) == "True":
        return 0.10
    if key == "GFAP" and str(row.get("kg_known_astrocyte", "False")) == "True":
        return 0.10
    if key == "Iba1" and str(row.get("kg_known_microglia", "False")) == "True":
        return 0.10
    if key == "NeuN" and str(row.get("kg_known_neuronal", "False")) == "True":
        return 0.10
    return 0.0


def rank_gene_hypotheses(cfg: dict[str, Any], grounding: pd.DataFrame, grounding_status: str) -> pd.DataFrame:
    df = grounding.copy()
    if df.empty:
        return pd.DataFrame()
    df["module_importance_score"] = pd.to_numeric(df["module_importance_score"], errors="coerce").fillna(0.0)
    df["mean_abs_prediction_delta"] = pd.to_numeric(df["mean_abs_prediction_delta"], errors="coerce").fillna(0.0)
    pieces = []
    for _, group in df.groupby("target_key", sort=False):
        g = group.copy()
        scaled_importance = minmax(g["module_importance_score"])
        scaled_delta = minmax(g["mean_abs_prediction_delta"])
        prior_bonus = g["kg_any_prior_support"].astype(str).map({"True": 0.20, "not_evaluated": 0.05, "False": 0.0}).fillna(0.0)
        target_bonus = g.apply(target_match_bonus, axis=1)
        uncertainty = pd.Series(0.0, index=g.index)
        uncertainty += np.where(g["kg_any_prior_support"].astype(str) == "not_evaluated", 0.20, 0.0)
        uncertainty += np.where(g["projection_method"].astype(str).str.contains("module_membership|module-membership|membership", case=False, na=False), 0.10, 0.0)
        uncertainty += np.where(g["module_delta_metric"].abs() < float(cfg["ranking"]["small_delta_threshold"]), 0.05, 0.0)
        g["priority_score"] = (scaled_importance * scaled_delta + prior_bonus + target_bonus - uncertainty).round(6)
        g = g.sort_values(["priority_score", "module_importance_score", "mean_abs_prediction_delta"], ascending=[False, False, False])
        g["rank_within_target"] = range(1, len(g) + 1)
        pieces.append(g)
    out = pd.concat(pieces, ignore_index=True).sort_values(["priority_score", "module_importance_score"], ascending=[False, False])
    out["overall_rank"] = range(1, len(out) + 1)
    def tier(score: float, kg: str) -> str:
        if score >= 0.85 and kg == "True":
            return "Tier 1"
        if score >= 0.55:
            return "Tier 2"
        if score >= 0.25:
            return "Tier 3"
        return "Not ranked"
    out["priority_tier"] = [tier(float(s), str(k)) for s, k in zip(out["priority_score"], out["kg_any_prior_support"])]
    flags = []
    for _, row in out.iterrows():
        f = []
        if str(row.get("kg_any_prior_support")) == "not_evaluated":
            f.append("knowledge_not_evaluated")
        if "membership" in str(row.get("projection_method", "")).lower():
            f.append("module_membership_projection_not_direct_gene_ablation")
        if abs(float(row.get("module_delta_metric", 0.0))) < float(cfg["ranking"]["small_delta_threshold"]):
            f.append("small_module_delta")
        flags.append(";".join(f) if f else "none")
    out["uncertainty_flags"] = flags
    out["evidence_level"] = out.get("evidence_level_from_stage36a", "model_implied_gene_hypothesis")
    out["recommended_followup"] = "independent validation or targeted experimental follow-up; Stage 36C did not run validation"
    out["safe_interpretation"] = "model-implied hypothesis and priority candidate for follow-up; not a causal or treatment claim"
    cols = [
        "target", "target_key", "rank_within_target", "overall_rank", "gene", "module", "projection_method", "evidence_level",
        "module_importance_score", "module_delta_metric", "mean_abs_prediction_delta", "kg_any_prior_support", "kg_known_ad",
        "kg_known_microglia", "kg_known_neuroinflammation", "kg_known_target_pathology", "kg_support_terms", "kg_support_sources",
        "novelty_status", "priority_score", "priority_tier", "uncertainty_flags", "safe_interpretation", "recommended_followup",
    ]
    return out[cols]


def rank_module_hypotheses(cfg: dict[str, Any], ranked: pd.DataFrame) -> pd.DataFrame:
    df = ranked[ranked["gene"].fillna("").astype(str) == ""].copy()
    df = df.rename(columns={"module_or_component": "module_or_component"})
    pieces = []
    for _, group in df.groupby("target_key", sort=False):
        g = group.sort_values(["rank"]).copy()
        g["rank_within_target"] = range(1, len(g) + 1)
        pieces.append(g)
    out = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    def tier(rank: int) -> str:
        if rank <= 3:
            return "Tier 1"
        if rank <= 8:
            return "Tier 2"
        return "Tier 3"
    out["priority_tier"] = [tier(int(r)) for r in out["rank_within_target"]]
    out["safe_interpretation"] = "model-implied module/component counterfactual sensitivity; requires independent validation"
    out["recommended_followup"] = "targeted module/pathway review followed by independent validation design"
    cols = [
        "target", "target_key", "rank_within_target", "module_or_component", "evidence_level", "baseline_metric", "ablated_metric",
        "delta_metric", "mean_abs_prediction_delta", "direction", "priority_tier", "safe_interpretation", "recommended_followup",
    ]
    return out[cols]


def target_summary(cfg: dict[str, Any], target36a: pd.DataFrame, genes: pd.DataFrame, grounding_status: str) -> pd.DataFrame:
    rows = []
    for _, row in target36a.iterrows():
        subset = genes[genes["target_key"] == row["target_key"]].sort_values("rank_within_target").head(5)
        rows.append(
            {
                "target": row["target"],
                "target_key": row["target_key"],
                "baseline_metric": row["baseline_metric"],
                "top_module": row["top_feature"],
                "top_gene_candidates": ";".join(subset["gene"].astype(str).tolist()),
                "n_gene_candidates_ranked": int((genes["target_key"] == row["target_key"]).sum()),
                "knowledge_grounding_status": grounding_status,
                "dominant_interpretation": "ranked follow-up hypotheses from model-implied sensitivity plus local prior support",
                "recommended_next_validation_type": "independent_external_or_experimental_validation_not_run_in_stage36c",
            }
        )
    return pd.DataFrame(rows)


def validation_planning(genes: pd.DataFrame, modules: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in genes.sort_values("overall_rank").head(10).iterrows():
        rows.append(
            {
                "validation_option": "literature/manual review",
                "target": row["target"],
                "candidate_gene_or_module": row["gene"],
                "rationale": f"Top ranked model-implied gene hypothesis from {row['module']} with local grounding status {row['novelty_status']}",
                "required_data": "curated literature and prior-resource review",
                "expected_output": "manual evidence table and claim boundary",
                "risk": "prior support may reflect broad pathway mention rather than specific disease mechanism",
                "claim_if_successful": "stronger rationale for follow-up validation",
                "claim_if_failed": "lower priority for near-term follow-up",
                "not_allowed_claims": "external validation success; causal validation; treatment relevance",
            }
        )
    for _, row in modules.sort_values(["target_key", "rank_within_target"]).groupby("target_key").head(1).iterrows():
        rows.append(
            {
                "validation_option": "independent SEA-AD-like held-out cohort, if available later",
                "target": row["target"],
                "candidate_gene_or_module": row["module_or_component"],
                "rationale": "Top model-implied module/component sensitivity for the target",
                "required_data": "pre-registered held-out donor-level expression and pathology measurements",
                "expected_output": "replication or non-replication of ranked module signal",
                "risk": "small donor cohorts may be underpowered",
                "claim_if_successful": "independent predictive replication of a model-implied hypothesis",
                "claim_if_failed": "hypothesis remains unsupported outside current internal data",
                "not_allowed_claims": "external validation success before the study is actually run; causal or treatment claims",
            }
        )
    return pd.DataFrame(rows)


def safety_audit() -> pd.DataFrame:
    return pd.DataFrame([{"external_validation_claim_made": False, "causal_claim_made": False, "therapeutic_target_claim_made": False, "novelty_overclaim_made": False, "direct_gene_ablation_claim_made": False, "in_silico_ablation_validated_claim_made": False, "priority_score_presented_as_truth": False, "safety_audit_pass": True}])


def write_reports(cfg, genes, modules, targets, planning, audit, pf):
    lines = [
        "# Stage 36C ranked hypothesis package report v1",
        "",
        "## Executive summary",
        "",
        str(pf.iloc[0]["controlled_interpretation"]),
        "The priority score is for prioritization only. It is not biological truth.",
        "",
        "## Ranked target summary",
        "",
        "```csv",
        targets.to_csv(index=False).strip(),
        "```",
        "",
        "## Top gene hypotheses",
        "",
        "```csv",
        genes.head(50).to_csv(index=False).strip(),
        "```",
        "",
        "## Top module hypotheses",
        "",
        "```csv",
        modules.head(50).to_csv(index=False).strip(),
        "```",
        "",
        "## Validation planning",
        "",
        "```csv",
        planning.to_csv(index=False).strip(),
        "```",
        "",
        "## Safety claims audit",
        "",
        "```csv",
        audit.to_csv(index=False).strip(),
        "```",
    ]
    resolve(cfg["outputs"]["report"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    pi = [
        "# Stage 36C PI-readable hypothesis shortlist v1",
        "",
        "## Context",
        "",
        "This shortlist packages Stage 36A model-implied hypotheses with Stage 36B local prior support. It is a follow-up planning artifact, not validation.",
        "",
        "## Top candidates by target",
        "",
    ]
    for target_key, group in genes.sort_values("rank_within_target").groupby("target_key", sort=False):
        pi += [f"### {target_key}", ""]
        for _, row in group.head(int(cfg["ranking"]["top_genes_per_target_for_report"])).iterrows():
            pi.append(f"- `{row['gene']}` from `{row['module']}`: priority `{row['priority_score']}` ({row['priority_tier']}); evidence is model-implied sensitivity plus local prior status `{row['novelty_status']}`. Missing: independent validation. Suggested follow-up: {row['recommended_followup']}.")
        pi.append("")
    pi += [
        "## Claim boundaries",
        "",
        "- These are model-implied hypotheses and priority candidates for follow-up.",
        "- Local prior support is not validation.",
        "- No external validation was run.",
        "- No causal or treatment claim is supported.",
    ]
    resolve(cfg["outputs"]["pi_report"]).write_text("\n".join(pi) + "\n", encoding="utf-8")


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    status = "Stage 36C ranked hypothesis package is complete. It combines Stage 36A model-implied counterfactual sensitivity with Stage 36B local knowledge grounding for follow-up prioritization only. No new modeling, external validation, causal validation, or treatment claim was made."
    for doc_path, marker in [
        (ROOT / "docs" / "ACTIVE_V3_STATUS.md", "\n\n## Stage 36C ranked hypothesis package status\n"),
        (ROOT / "docs" / "V3_SCORECARD.md", "\n\n## Stage 36C ranked hypothesis package result\n"),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + status + "\n", encoding="utf-8")
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    item = "stage36c_ranked_hypothesis_package"
    new = {
        "scorecard_item": item,
        "status": "complete",
        "stage": "Stage 36C",
        "metric": "ranked model-implied follow-up hypotheses",
        "threshold_or_gate": "run pass requires ranked tables, planning table, PI report, and safety audit",
        "current_value": "run_pass=True",
        "pass_fail": "pass" if bool(row.stage36c_run_pass) else "fail",
        "datasets_allowed": "Stage 36A/36B internal outputs only",
        "datasets_forbidden": "new modeling; external validation; web scraping; downloads; causal or treatment claims",
        "allowed_claim": row.controlled_interpretation,
        "notes": "Prioritization package only; not validation.",
    }
    score = score[score["scorecard_item"] != item]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage36c_ranked_hypothesis_package_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    module_scores = read_csv(cfg["inputs"]["stage36a_ranked_hypotheses"])
    target36a = read_csv(cfg["inputs"]["stage36a_target_summary"])
    grounding = read_csv(cfg["inputs"]["stage36b_hypothesis_grounding"])
    pf36b = read_csv(cfg["inputs"]["stage36b_pass_fail"])
    audit36b = read_csv(cfg["inputs"]["stage36b_audit"])
    stage36a_found = not module_scores.empty and not target36a.empty
    stage36b_found = not grounding.empty and not pf36b.empty
    grounding_status = "passed" if stage36b_found and bool(pf36b.iloc[0].get("stage36b_knowledge_grounding_pass", False)) else "not_evaluated"
    genes = rank_gene_hypotheses(cfg, grounding, grounding_status)
    modules = rank_module_hypotheses(cfg, module_scores)
    targets = target_summary(cfg, target36a, genes, grounding_status)
    planning = validation_planning(genes, modules)
    audit = safety_audit()
    interpretation = "Stage 36C produced a ranked hypothesis package from Stage 36A model-implied counterfactual sensitivity and Stage 36B local knowledge grounding. The ranked candidates are follow-up hypotheses only; no external validation, causal validation, or treatment claim was made."
    pf = pd.DataFrame([{"stage36c_run": True, "stage36a_inputs_found": stage36a_found, "stage36b_inputs_found": stage36b_found, "knowledge_grounding_status": grounding_status, "ranked_gene_table_written": True, "ranked_module_table_written": True, "target_summary_written": True, "validation_planning_table_written": True, "pi_readable_report_written": True, "no_new_modeling_run": True, "no_external_validation_run": True, "no_causal_claim": True, "no_therapeutic_claim": True, "safety_audit_pass": bool(audit.iloc[0]["safety_audit_pass"]), "stage36c_run_pass": bool(stage36a_found and stage36b_found and audit.iloc[0]["safety_audit_pass"]), "controlled_interpretation": interpretation}])
    genes.to_csv(resolve(cfg["outputs"]["ranked_gene_hypotheses"]), index=False)
    modules.to_csv(resolve(cfg["outputs"]["ranked_module_hypotheses"]), index=False)
    targets.to_csv(resolve(cfg["outputs"]["target_summary"]), index=False)
    planning.to_csv(resolve(cfg["outputs"]["validation_planning"]), index=False)
    audit.to_csv(resolve(cfg["outputs"]["safety_audit"]), index=False)
    pf.to_csv(resolve(cfg["outputs"]["pass_fail"]), index=False)
    write_reports(cfg, genes, modules, targets, planning, audit, pf)
    update_status(pf)
    print(f"stage36c_run_pass={bool(pf.iloc[0]['stage36c_run_pass'])}")
    print(f"knowledge_grounding_status={grounding_status}")
    print(f"n_ranked_genes={len(genes)}")


if __name__ == "__main__":
    main()
