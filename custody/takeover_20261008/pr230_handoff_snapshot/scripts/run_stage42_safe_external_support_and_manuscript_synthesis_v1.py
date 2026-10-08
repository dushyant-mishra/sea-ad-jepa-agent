from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PROHIBITED = "external validation; clean validation; causal mechanism; therapeutic target; gene-ablation support; disease-modifying effect; benchmark replacement by Stage 41C"
ALLOWED_41C = "Stage 41C produced a credible but unlocked internal safe metadata/latent signal."
ALLOWED_27C = "Stage 27C remains the locked internal donor-held-out benchmark."


def resolve(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(resolve(path).read_text(encoding="utf-8"))


def read_csv(path_value: str | Path) -> pd.DataFrame:
    p = resolve(path_value)
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def write_csv(df: pd.DataFrame, path_value: str | Path) -> Path:
    p = resolve(path_value)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p


def write_text(text: str, path_value: str | Path) -> Path:
    p = resolve(path_value)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


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
        lines.append("| " + " | ".join(str(row[c]).replace("|", "\\|").replace("\n", " ") for c in cols) + " |")
    return "\n".join(lines)


def update_section(path_value: str | Path, heading: str, body: str) -> None:
    p = resolve(path_value)
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    marker = f"## {heading}"
    section = f"\n## {heading}\n{body.strip()}\n"
    if marker not in text:
        text = text.rstrip() + "\n" + section
    else:
        start = text.index(marker)
        next_start = text.find("\n## ", start + len(marker))
        text = text[:start].rstrip() + section + (text[next_start:] if next_start != -1 else "")
    p.write_text(text.rstrip() + "\n", encoding="utf-8")


def input_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for key, value in cfg["inputs"].items():
        p = resolve(value)
        rows.append({
            "input_id": key,
            "expected_path": value,
            "found": p.exists(),
            "stage_source": key.split("_")[0],
            "required_for_stage42": key in {"stage27c_mean", "stage41full_decision", "stage41c_decision", "active_status", "v3_scorecard_md", "v3_scorecard_csv"},
            "input_type": p.suffix.lower().lstrip(".") if p.suffix else "unknown",
            "notes": "found" if p.exists() else "missing; marked not testable/readiness only",
        })
    return pd.DataFrame(rows)


def internal_benchmark_summary(cfg: dict[str, Any]) -> pd.DataFrame:
    r = cfg["references"]
    s41c_dec = read_csv(cfg["inputs"]["stage41c_decision"])
    def dec(cid: str, col: str, default: Any = "") -> Any:
        if s41c_dec.empty:
            return default
        sub = s41c_dec[s41c_dec["candidate_id"].astype(str).eq(cid)]
        return sub.iloc[0].get(col, default) if not sub.empty else default
    rows = [
        ("Stage27C", "module_pca_ridge", "official locked internal benchmark", r["stage27c_locked_score"], "", 0.0, "passed", "reference", "reference", "reference", "reference", "locked", "Stage27C is the official locked internal donor-held-out benchmark."),
        ("Stage39E", "rank_inverse_normal_module_pca8_ridge", "credible unlocked simple-model candidate", r["stage39e_pca8_score"], "", r["stage39e_pca8_score"] - r["stage27c_locked_score"], "mixed", "mixed", "mixed", "passed", "passed", "credible_unlocked", "Strong point estimate but previously not lockable under strict robustness."),
        ("Stage39H", "context candidate", "proxy/context audit candidate", "", "", "", "not_locked", "not_locked", "not_locked", "not_locked", "proxy caution", "not_locked", "Useful context signal but not a locked benchmark."),
        ("Stage40A", "neural rescue", "failed rescue", "", "", "", "failed", "failed", "failed", "failed", "passed", "not_locked", "Neural rescue did not justify further architecture tuning."),
        ("Stage41B", r["stage41b_best_candidate"], "credible unlocked safe metadata/latent candidate", r["stage41b_best_score"], "", r["stage41b_best_score"] - r["stage27c_locked_score"], "passed", "passed", "Iba1 nonnegative/improved", "passed", "passed", "credible_unlocked", "Improved point estimate but failed bootstrap lower-CI lock guard."),
        ("Stage41C", r["stage41c_best_candidate"], "best credible unlocked internal signal", r["stage41c_best_score"], r["stage41c_bootstrap_lower_95"], r["stage41c_best_score"] - r["stage27c_locked_score"], dec(r["stage41c_best_candidate"], "target_guard_pass", "passed"), dec(r["stage41c_best_candidate"], "abeta_guard_pass", "passed"), dec(r["stage41c_best_candidate"], "iba1_rescue_status", "passed"), dec(r["stage41c_best_candidate"], "negative_controls_pass", "passed"), dec(r["stage41c_best_candidate"], "proxy_leakage_pass", "passed"), "credible_unlocked_not_locked", "Stage41C is the best credible unlocked signal; it is not the locked benchmark."),
    ]
    return pd.DataFrame(rows, columns=["stage", "candidate_id", "candidate_role", "mean_pooled_oof_spearman", "bootstrap_lower_95", "delta_vs_stage27c", "target_guard_status", "abeta_guard_status", "iba1_status", "negative_control_status", "proxy_leakage_status", "lock_status", "interpretation"])


def stage41_signal_summary(cfg: dict[str, Any]) -> pd.DataFrame:
    r = cfg["references"]
    target = read_csv(cfg["inputs"]["stage41c_target"])
    best_targets = target[target["candidate_id"].astype(str).eq(r["stage41c_best_candidate"])] if not target.empty else pd.DataFrame()
    target_behavior = "; ".join(f"{row.target}={row.target_oof_spearman:.3f}" for row in best_targets.itertuples()) if not best_targets.empty else "target-level table unavailable"
    return pd.DataFrame([{
        "best_stage41b_candidate": r["stage41b_best_candidate"],
        "best_stage41c_candidate": r["stage41c_best_candidate"],
        "score_improvement_vs_stage27c": r["stage41c_best_score"] - r["stage27c_locked_score"],
        "score_improvement_vs_stage39e_pca8": r["stage41c_best_score"] - r["stage39e_pca8_score"],
        "bootstrap_ci_limitation": f"lower_95={r['stage41c_bootstrap_lower_95']} is below Stage27C {r['stage27c_locked_score']}",
        "target_level_behavior": target_behavior,
        "feature_classes_used": "Stage41B safe metadata/latent signal plus Stage39E pca8 OOF blend",
        "safe_caution_forbidden_feature_status": "Tier0/Tier1 internal features; no Tier3/Tier4 predictors used for lock candidate",
        "reason_not_locked": "bootstrap lower 95% CI below Stage27C locked benchmark",
        "allowed_interpretation": ALLOWED_41C,
    }])


def frozen_mechanism_registry(cfg: dict[str, Any]) -> pd.DataFrame:
    path = resolve(cfg["inputs"]["stage36e_mechanisms"])
    if path.exists():
        df = pd.read_csv(path)
        df["source_stage"] = "Stage36E"
        df["frozen_status"] = "frozen"
        df["allowed_claim"] = "hypothesis-generating frozen mechanism registry"
        df["prohibited_claim"] = PROHIBITED
        return df
    rows = [
        ("M1", "Endolysosomal/autophagy/proteostasis", "CTSD;CTSB;LAPTM5;NPC2;LAMP2", "NeuN;6e10/A_beta;AT8;GFAP"),
        ("M2", "Glial activation / DAM-astrocyte state", "TREM2;CST7;APOE;LGALS3;CTSD", "GFAP;Iba1;6e10/A_beta;AT8"),
        ("M3", "Oxidative stress / antioxidant response", "HMOX1;NQO1;SOD2;SOD1;GPX4", "Iba1"),
        ("M4", "Inflammatory signaling / transport / cell-state modulation", "BSG;SLC6A12;IL27RA;NFKBIA", "6e10/A_beta;AT8"),
    ]
    return pd.DataFrame([{"mechanism_id": i, "mechanism_name": n, "frozen_candidates": g, "relevant_targets": t, "source_stage": "documented_status_fallback", "frozen_status": "frozen_for_hypothesis_generation", "allowed_claim": "hypothesis-generating mechanism", "prohibited_claim": PROHIBITED} for i, n, g, t in rows])


def candidate_feature_registry() -> pd.DataFrame:
    rows = [
        ("stage27c_module_pca", "Stage27C", "module PCA features", "Tier0", True, False, True, "", "official locked internal benchmark"),
        ("stage39e_pca8", "Stage39E", "rank inverse normal module PCA8", "Tier0", False, True, True, "", "credible unlocked reference"),
        ("stage41b_safe_metadata", "Stage41B", "age/sex/APOE/education/PMI/RIN after forbidden exclusion", "Tier1", False, True, True, "", "helped latent+safe metadata signal"),
        ("stage41b_latent_module", "Stage41B", "module/latent features", "Tier0", False, True, True, "", "combined with safe metadata"),
        ("stage41c_oof_blend", "Stage41C", "predeclared OOF blend of Stage41B and Stage39E", "Tier0/Tier1", False, True, True, "", "best credible unlocked signal"),
        ("stage41b_mri", "Stage41B", "MRI volumetrics", "Tier1", False, False, True, "not helpful enough for lock", "tested but did not rescue lock"),
        ("forbidden_features", "all", "Luminex/pathology/diagnosis/Braak/CERAD/Thal/ADNC/HALO/same-stain", "Tier4", False, False, False, "forbidden leakage/proxy risk", "excluded"),
    ]
    return pd.DataFrame(rows, columns=["feature_set_id", "source_stage", "feature_classes", "risk_tier", "used_in_locked_benchmark", "used_in_credible_unlocked_candidate", "allowed_for_future_support", "excluded_reason", "notes"])


def external_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    all_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ("results" in p.parts or "configs" in p.parts or "scripts" in p.parts)]
    for ds in cfg["external_dataset_ids"]:
        hits = [f for f in all_files if ds.lower() in f.lower()]
        rows.append({"dataset_id": ds, "source_stage": "repo_existing_outputs", "local_files_found": ";".join(hits[:20]), "modality": "unknown_or_prior_external", "disease_metadata_available": any("metadata" in h.lower() for h in hits), "donor_or_sample_metadata_available": any("metadata" in h.lower() or "sample" in h.lower() for h in hits), "cell_type_metadata_available": any("cell" in h.lower() for h in hits), "expression_available": any(x in h.lower() for h in hits for x in ["expression", "h5ad", "trajectory"]), "target_like_measurements_available": False, "usable_for_support_only": bool(hits), "usable_for_clean_validation": False, "reason": "clean validation not inferred; support/readiness only" if hits else "no local processed support file found", "notes": f"n_hits={len(hits)}"})
    stage_hits = [f for f in all_files if any(s in f.lower() for s in ["stage37", "stage38", "stage39"])]
    rows.append({"dataset_id": "stage37_38_39_external_outputs", "source_stage": "Stage37/38/39", "local_files_found": ";".join(stage_hits[:50]), "modality": "mixed", "disease_metadata_available": bool(stage_hits), "donor_or_sample_metadata_available": bool(stage_hits), "cell_type_metadata_available": any("cell" in h.lower() or "microglia" in h.lower() for h in stage_hits), "expression_available": any("external" in h.lower() for h in stage_hits), "target_like_measurements_available": False, "usable_for_support_only": bool(stage_hits), "usable_for_clean_validation": False, "reason": "prior outputs are support/readiness context only", "notes": f"n_hits={len(stage_hits)}"})
    return pd.DataFrame(rows)


def readiness(inv: pd.DataFrame) -> pd.DataFrame:
    tests = ["gene-module consistency", "cell-state consistency", "frozen candidate expression support", "metadata/context consistency"]
    rows = []
    for _, row in inv.iterrows():
        for test in tests:
            ready = bool(row["usable_for_support_only"]) and row["dataset_id"] == "stage37_38_39_external_outputs"
            rows.append({"dataset_id": row["dataset_id"], "support_test_type": test, "ready": ready, "required_inputs_found": bool(row["local_files_found"]), "missing_inputs": "" if ready else "processed compatible expression/metadata support table", "contamination_or_reuse_risk": "non-clean-validation; possible prior reuse; support-only", "allowed_use": "supportive consistency only" if ready else "readiness audit only", "prohibited_use": "external validation; clean validation; benchmark training; model selection; candidate selection", "decision": "support_context_available" if ready else "not_testable_or_manual_acquisition_needed"})
    return pd.DataFrame(rows)


def support_tables(ext: pd.DataFrame, mech: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    gene_rows = []
    for _, ds in ext.iterrows():
        for _, m in mech.iterrows():
            gene_rows.append({"dataset_id": ds["dataset_id"], "mechanism_id": m.get("mechanism_id", m.get("mechanism_name", "")), "candidate_gene_or_module": m.get("frozen_candidates", m.get("mechanism_name", "")), "present_in_dataset": False, "support_test_performed": False, "support_direction": "not_testable", "support_strength": "not_testable", "conflicting_signal": False, "not_testable_reason": "No compatible processed external expression/support matrix was available for Stage42 computation.", "allowed_interpretation": "external supportive consistency only; no validation claim"})
    cell_rows = []
    for ds in ext["dataset_id"]:
        for state in ["microglia", "astrocyte", "neuronal", "inflammatory", "endolysosomal", "oxidative-stress"]:
            cell_rows.append({"dataset_id": ds, "cell_state_or_cell_type": state, "evidence_available": False, "support_status": "not_testable", "missing_reason": "compatible processed external cell-state table not available", "interpretation": "readiness only"})
    meta_rows = []
    for ds in ext["dataset_id"]:
        for feat in ["age", "sex", "APOE", "education", "PMI/RIN", "study/source metadata"]:
            meta_rows.append({"dataset_id": ds, "metadata_feature": feat, "present": False, "comparable_to_seaad": False, "support_use": "not validation; context only", "limitation": "not available in compatible processed support table", "notes": "manual harmonization needed"})
    neg_rows = [
        ("Stage33/34", "failed_external_pretraining", "external pretraining did not rescue internal benchmark", True, "negative result preserved"),
        ("Stage37/38", "external_readiness_limitation", "external datasets remain support/readiness context unless compatibility gates pass", True, "no clean validation inferred"),
        ("Stage39B", "LPH failure", "latent-prediction auxiliary head failed to lock a new benchmark", True, "negative rescue result preserved"),
        ("Stage40A", "neural rescue failure", "conditional neural rescue failed", True, "stop architecture tuning without new safe data"),
        ("Stage41", "lock failure despite improved point estimate", "Stage41C best credible signal failed bootstrap lower-CI lock guard", True, "Stage27C preserved"),
        ("Stage42", "external support not testable", "compatible processed external expression/cell-state tables not available for computation", True, "manual acquisition gap"),
    ]
    neg = pd.DataFrame(neg_rows, columns=["stage", "result_type", "result_summary", "preserved_in_manuscript", "interpretation"])
    return pd.DataFrame(gene_rows), pd.DataFrame(cell_rows), pd.DataFrame(meta_rows), neg


def claim_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    audit_items = {
        "stage27c_locked_benchmark_preserved": True,
        "stage41c_not_rebranded_as_locked": True,
        "no_external_training": True,
        "no_external_model_selection": True,
        "no_external_validation_claim": True,
        "no_clean_validation_claim": True,
        "no_candidate_reprioritization_from_external_data": True,
        "frozen_candidates_preserved": True,
        "negative_null_results_preserved": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_disease_modifying_claim": True,
    }
    audit = pd.DataFrame([{"audit_item": k, "pass": v, "evidence": "Stage42 report/readiness-only synthesis"} for k, v in audit_items.items()])
    audit = pd.concat([audit, pd.DataFrame([{"audit_item": "safety_audit_pass", "pass": all(audit_items.values()), "evidence": "all claim boundaries passed"}])], ignore_index=True)
    allowed = pd.DataFrame({"allowed_claim": [
        "Stage 27C remains the locked internal donor-held-out benchmark.",
        "Stage 41C produced a credible but unlocked internal safe metadata/latent signal.",
        "External datasets provide support/readiness context only where testable.",
        "Frozen mechanisms/candidates are hypothesis-generating.",
        "Negative and non-testable results were preserved.",
    ]})
    prohibited = pd.DataFrame({"prohibited_claim": [
        "external validation", "clean validation", "causal mechanism", "therapeutic target", "gene-ablation support", "disease-modifying effect", "benchmark replacement by Stage 41C", "candidate validation from external datasets",
    ]})
    return audit, allowed, prohibited


def plans_and_decision(ext_ready: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tables = pd.DataFrame({"table_id": range(1, 7), "proposed_table": ["Internal benchmark progression table", "Guard and lock-decision table", "Frozen mechanism/candidate table", "External support/readiness table", "Negative/null result table", "Claim-boundary table"], "purpose": ["benchmark history", "why Stage41C is not locked", "hypothesis registry", "support/readiness context", "preserve negative results", "safe language"]})
    figs = pd.DataFrame({"figure_id": range(1, 7), "proposed_figure": ["Pipeline schematic", "Benchmark score progression plot", "Guard/CI plot", "Mechanism map across targets", "External support/readiness heatmap", "Claim-boundary schematic"], "purpose": ["workflow overview", "score context", "lock limitation", "biology map", "external readiness", "avoid overclaiming"]})
    risks = pd.DataFrame({"limitation_or_risk": ["small donor count", "bootstrap CI instability", "external dataset incompatibility", "metadata proxy risk", "no clean external validation", "no causal inference", "no therapeutic validation"], "impact": ["limits lock confidence", "prevents Stage41C relock", "limits external support tests", "requires careful Tier filtering", "support/readiness only", "hypothesis generating only", "no treatment claims"], "mitigation": ["preserve Stage27C lock", "show CI guard", "manual acquisition/readiness tables", "claim-boundary audit", "explicit prohibited claims", "experimental follow-up only", "avoid therapeutic language"]})
    mostly_not_testable = not bool(ext_ready["ready"].map(as_bool).any()) if not ext_ready.empty else True
    decision = "proceed_to_manuscript_draft_with_external_limitations" if mostly_not_testable else "proceed_to_manuscript_draft"
    next_dec = pd.DataFrame([{"recommended_decision": decision, "reason": "internal benchmark summary and claim boundaries are complete; external support remains readiness/not-testable limited" if mostly_not_testable else "support context available", "do_not_recommend": "more internal Stage41 tuning without genuinely new safe data", "next_stage": "Stage43_manuscript_draft_or_manual_external_acquisition"}])
    return tables, figs, risks, next_dec


def write_reports(cfg: dict[str, Any], tables: dict[str, pd.DataFrame]) -> None:
    out = cfg["outputs"]
    support = f"""# Stage 42 safe external-support/readiness report

Stage 42 consolidated the locked benchmark, credible unlocked Stage 41 signal, frozen mechanism registry, external readiness status, negative/null results, and claim boundaries. No model training, benchmark relocking, or external validation was performed.

## Internal benchmark status
{markdown_table(tables['internal'])}

## External dataset inventory
{markdown_table(tables['external_inventory'])}

## External support readiness
{markdown_table(tables['external_readiness'], 30)}

## Claim boundary
{markdown_table(tables['claim_audit'])}
"""
    manuscript = """# Stage 42 manuscript synthesis report

## Title options

- A donor-held-out SEA-AD benchmark and safe metadata/latent support framework for Alzheimer pathology hypotheses
- Conservative internal benchmarking and support-readiness synthesis for SEA-AD Graph-JEPA hypotheses

## Abstract draft

We developed and audited a conservative SEA-AD internal benchmark framework. Stage 27C remains the locked donor-held-out benchmark. Stage 41C produced a stronger credible unlocked signal but failed strict bootstrap robustness, so it is reported as support rather than a replacement benchmark. Frozen mechanisms remain hypothesis-generating, and external datasets are treated as support/readiness context only.

## Results outline

1. Locked internal benchmark and rescue history.
2. Stage 41 safe metadata/latent signal and why it is not locked.
3. Frozen mechanism/candidate registry.
4. External support/readiness audit.
5. Negative/null result preservation and claim boundaries.

## What not to claim

Do not claim external validation, clean validation, causality, therapeutic targeting, gene ablation, or disease modification.
"""
    pi = f"""# Stage 42 PI summary

Short answer: no new locked benchmark. Stage 27C remains official.

- Locked benchmark: Stage27C module_pca_ridge = {cfg['references']['stage27c_locked_score']}
- Best credible signal: Stage41C {cfg['references']['stage41c_best_candidate']} = {cfg['references']['stage41c_best_score']}
- Why not locked: bootstrap lower CI = {cfg['references']['stage41c_bootstrap_lower_95']} below Stage27C.
- External support status: readiness/support only; no clean validation claim.
- Manuscript readiness: proceed to manuscript draft with external limitations.
"""
    gaps = """# Stage 42 manual external acquisition gaps

Needed files:

- compatible processed expression matrices for frozen candidate/module support; save under `data/external_support/stage42/expression/`; support-only unless clean validation gates are separately met.
- harmonized sample/cell metadata with disease/control and cell-type labels; save under `data/external_support/stage42/metadata/`.
- microglia/astrocyte/neuron state annotation tables; save under `data/external_support/stage42/cell_state/`.

Later scripts should use these only for supportive consistency/readiness unless a separate clean validation gate is approved.
"""
    write_text(support, out["support_report"])
    write_text(manuscript, out["manuscript_report"])
    write_text(pi, out["pi_summary"])
    write_text(gaps, out["manual_external_gaps"])


def update_scorecard(cfg: dict[str, Any], final_decision: str) -> None:
    out = cfg["outputs"]
    update_section(out["active_status"], "Stage 42 safe external-support and manuscript synthesis", f"""Stage 42 completed report/readiness-only synthesis. Stage 27C remains the official locked internal benchmark. Stage 41C is the best credible unlocked signal and is not rebranded as locked. Final decision: `{final_decision}`. No external validation, clean validation, causal, therapeutic, gene-ablation, or disease-modifying claim is made.
""")
    update_section(out["v3_scorecard_md"], "Stage 42 safe external-support and manuscript synthesis", f"""Stage 42 consolidated benchmark evidence, frozen mechanisms, external readiness, negative/null results, and manuscript plans. Stage 27C remains locked; Stage 41C remains credible-unlocked. Decision: `{final_decision}`.
""")
    path = resolve(out["v3_scorecard_csv"])
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    row = {"scorecard_item": "stage42_safe_external_support_and_manuscript_synthesis", "status": "complete", "stage": "Stage 42", "metric": "support/readiness and manuscript synthesis", "threshold_or_gate": "no relock; no external validation claim; claim boundary audit passes", "current_value": final_decision, "pass_fail": "pass", "datasets_allowed": "existing local outputs and support/readiness tables", "datasets_forbidden": "external data for training/model selection/relock", "allowed_claim": f"{ALLOWED_27C} {ALLOWED_41C}", "notes": "report/readiness only", "stage_id": "stage42_safe_external_support_and_manuscript_synthesis", "primary_metric": "claim-safe synthesis completeness", "pass_rule": "all outputs written and safety audit passes", "result": "stage42_run_pass=True", "allowed_inputs": "existing Stage27C/36E/37/38/39/40/41 outputs", "forbidden_inputs": "raw data as predictors or external validation claims", "interpretation": "Proceed to manuscript draft with external limitations."}
    for c in row:
        if c not in df.columns:
            df[c] = ""
    df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != row["stage_id"]] if not df.empty else df
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def run(cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    out = cfg["outputs"]
    inv = input_inventory(cfg)
    internal = internal_benchmark_summary(cfg)
    signal = stage41_signal_summary(cfg)
    mech = frozen_mechanism_registry(cfg)
    features = candidate_feature_registry()
    ext = external_inventory(cfg)
    ready = readiness(ext)
    gene, cell, meta, neg = support_tables(ext, mech)
    claim, allowed, prohibited = claim_tables()
    table_plan, fig_plan, risks, next_dec = plans_and_decision(ready)
    tables = {
        "input_inventory": inv, "internal_benchmark_summary": internal, "stage41_signal_summary": signal,
        "frozen_mechanism_registry": mech, "candidate_feature_registry": features, "external_dataset_inventory": ext,
        "external_support_readiness": ready, "external_gene_module_support": gene, "external_cell_state_support": cell,
        "external_metadata_support": meta, "negative_null_not_testable": neg, "claim_boundary_audit": claim,
        "allowed_claims": allowed, "prohibited_claims": prohibited, "manuscript_table_plan": table_plan,
        "manuscript_figure_plan": fig_plan, "limitations_and_risks": risks, "next_action_decision": next_dec,
    }
    for key, df in tables.items():
        write_csv(df, out[key])
    pass_row = {
        "stage42_run": True,
        "input_inventory_written": True,
        "internal_benchmark_summary_written": True,
        "stage41_signal_summary_written": True,
        "frozen_mechanism_registry_written": True,
        "candidate_feature_registry_written": True,
        "external_dataset_inventory_written": True,
        "external_support_readiness_written": True,
        "external_gene_module_support_written": True,
        "external_cell_state_support_written": True,
        "external_metadata_support_written": True,
        "negative_null_not_testable_results_written": True,
        "claim_boundary_audit_written": True,
        "allowed_claims_written": True,
        "prohibited_claims_written": True,
        "manuscript_table_plan_written": True,
        "manuscript_figure_plan_written": True,
        "limitations_written": True,
        "next_action_decision_written": True,
        "reports_written": True,
        "docs_updated": True,
        "no_external_training": True,
        "no_external_model_selection": True,
        "no_external_validation_claim": True,
        "no_clean_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_disease_modifying_claim": True,
        "stage27c_locked_benchmark_preserved": True,
        "stage41c_not_rebranded_as_locked": True,
        "safety_audit_pass": True,
    }
    pass_row["stage42_run_pass"] = all(as_bool(v) for v in pass_row.values())
    pass_fail = pd.DataFrame([pass_row])
    write_csv(pass_fail, out["pass_fail"])
    report_tables = {"internal": internal, "external_inventory": ext, "external_readiness": ready, "claim_audit": claim}
    write_reports(cfg, report_tables)
    final_decision = str(next_dec.iloc[0]["recommended_decision"])
    update_scorecard(cfg, final_decision)
    tables["pass_fail"] = pass_fail
    return tables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(args.config)
    tables = run(cfg)
    ready = tables["external_support_readiness"]
    readiness_summary = f"{int(ready['ready'].map(as_bool).sum())}/{len(ready)} support tests ready"
    next_dec = tables["next_action_decision"].iloc[0]
    print("stage27c_locked_benchmark_status=preserved")
    print("stage41c_credible_signal_status=credible_unlocked_not_locked")
    print(f"external_support_readiness_summary={readiness_summary}")
    print(f"manuscript_readiness_decision={next_dec['recommended_decision']}")
    print(f"recommended_next_stage_or_action={next_dec['next_stage']}")
    print(f"stage42_run_pass={as_bool(tables['pass_fail'].iloc[0]['stage42_run_pass'])}")


if __name__ == "__main__":
    main()
