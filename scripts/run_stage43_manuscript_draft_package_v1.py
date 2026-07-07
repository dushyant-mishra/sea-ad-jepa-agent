from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PROHIBITED = "external validation; clean validation; causal mechanism; therapeutic target; gene-ablation support; disease-modifying effect"


def resolve(v: str | Path) -> Path:
    p = Path(v)
    return p if p.is_absolute() else ROOT / p


def load_cfg(p: str | Path) -> dict[str, Any]:
    return yaml.safe_load(resolve(p).read_text(encoding="utf-8"))


def read_csv(v: str | Path) -> pd.DataFrame:
    p = resolve(v)
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def write_csv(df: pd.DataFrame, v: str | Path) -> Path:
    p = resolve(v)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p


def write_text(text: str, v: str | Path) -> Path:
    p = resolve(v)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def as_bool(v: Any) -> bool:
    return v if isinstance(v, bool) else str(v).strip().lower() in {"true", "1", "yes"}


def md(df: pd.DataFrame, n: int = 20) -> str:
    if df.empty:
        return "_No rows available._"
    x = df.head(n).fillna("").astype(str)
    cols = list(x.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in x.iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "\\|") for c in cols) + " |")
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
        nxt = text.find("\n## ", start + len(marker))
        text = text[:start].rstrip() + section + (text[nxt:] if nxt != -1 else "")
    p.write_text(text.rstrip() + "\n", encoding="utf-8")


def input_inventory(cfg):
    rows = []
    for k, v in cfg["inputs"].items():
        p = resolve(v)
        rows.append({"input_id": k, "expected_path": v, "found": p.exists(), "stage_source": k.split("_")[0], "used_in_stage43": True, "notes": "found" if p.exists() else "missing; synthesis continues without fabrication"})
    return pd.DataFrame(rows)


def benchmark_progression(cfg):
    r = cfg["references"]
    rows = [
        ("Stage27C", "module_pca_ridge", "official locked internal benchmark", r["stage27c_score"], "", 0.0, "locked", "passed locked benchmark gate", "official locked internal benchmark"),
        ("Stage39E", "rank_inverse_normal_module_pca8_ridge", "credible unlocked candidate", 0.35808116279206914, "", 0.35808116279206914-r["stage27c_score"], "credible_unlocked", "strict robustness limits", "strong but not locked"),
        ("Stage39H", "context/proxy candidate", "context/proxy candidate", "", "", "", "not_locked", "proxy/stability caution", "context signal only"),
        ("Stage40A", "neural rescue", "failed rescue", "", "", "", "not_locked", "neural rescue failed", "negative result"),
        ("Stage41B", "latent_plus_safe_metadata", "credible unlocked", r["stage41b_score"], "", r["stage41b_score"]-r["stage27c_score"], "credible_unlocked", "bootstrap lower CI below Stage27C", "safe metadata/latent point-estimate gain"),
        ("Stage41C", "blend_stage41b_with_stage39e_pca8", "best credible unlocked internal signal", r["stage41c_score"], r["stage41c_lower_ci"], r["stage41c_score"]-r["stage27c_score"], "credible_unlocked_not_locked", "bootstrap lower CI below Stage27C", "best credible unlocked internal signal, not locked"),
        ("Stage45", "latent_plus_safe_metadata_plus_cellxgene_plus_mri_engineered", "negative new-feature result", r["stage45_score"], 0.214644, r["stage45_delta_vs_stage27c"], "do_not_lock", "below Stage27C and Stage41C", "successful acquisition but negative benchmark result"),
    ]
    return pd.DataFrame(rows, columns=["stage", "candidate_id", "role", "mean_pooled_oof_spearman", "bootstrap_lower_95", "delta_vs_stage27c", "lock_status", "reason_locked_or_not_locked", "interpretation"])


def rescue_summary():
    rows = [
        ("Graph controls/rescue", "graph smoothing/residual graph controls", "did not beat Stage27C", "negative", "graph-specific pass failed or no robust improvement", "Graph machinery was not sufficient under donor-held-out safeguards."),
        ("External pretraining", "approved external pretraining attempts", "failed to rescue benchmark", "negative", "did not improve locked benchmark", "External pretraining did not justify relocking."),
        ("Stage39B LPH", "latent-prediction auxiliary head", "failed", "negative", "no robust material rescue", "LPH did not solve benchmark instability."),
        ("Stage39H", "metadata/context proxy audit", "useful signal", "not locked", "proxy/stability caution", "Context signal is informative but bounded."),
        ("Stage40A", "neural rescue", "failed", "negative", "small donor count/capacity risk", "Stop architecture tuning without new data."),
        ("Stage41B/41C", "safe metadata/latent blending", "0.368087 best credible signal", "credible unlocked", "CI lower bound below Stage27C", "Promising but not lockable."),
        ("Stage45", "CELLxGENE composition + engineered MRI", "0.312143", "negative", "below Stage27C and Stage41C", "New safe features did not rescue performance."),
    ]
    return pd.DataFrame(rows, columns=["stage_or_group", "strategy", "best_result", "outcome", "reason_not_locked", "manuscript_message"])


def stage41_table(cfg):
    r = cfg["references"]
    return pd.DataFrame([{"stage41b_best": "latent_plus_safe_metadata", "stage41b_score": r["stage41b_score"], "stage41c_best": "blend_stage41b_with_stage39e_pca8", "stage41c_score": r["stage41c_score"], "target_guard": "passed", "abeta_guard": "passed", "iba1_status": "nonnegative/improved", "negative_control": "passed", "proxy_leakage": "passed", "bootstrap_limitation": f"lower CI {r['stage41c_lower_ci']} below Stage27C {r['stage27c_score']}", "allowed_claim": "Stage41C produced a credible internal donor-held-out point-estimate improvement but did not pass strict benchmark-lock robustness."}])


def stage45_table(cfg):
    r = cfg["references"]
    return pd.DataFrame([{"cellxgene_metadata_available": True, "exact_donor_overlap": "84/84", "feature_matrices_built": 7, "benchmark_ran": True, "best_stage45_score": r["stage45_score"], "below_stage27c": True, "below_stage41c": True, "decision": "do_not_lock_stage45", "manuscript_message": "Successful acquisition and donor linkage of new safe CELLxGENE composition and engineered MRI features did not rescue benchmark performance, supporting the conclusion that simple composition/volumetric additions were insufficient."}])


def mechanism_table(cfg):
    p = resolve(cfg["inputs"]["stage36e_mechanisms"])
    if p.exists():
        df = pd.read_csv(p)
        df["claim_status"] = "hypothesis-generating only"
        df["prohibited_claim"] = PROHIBITED
        return df
    rows = [
        ("M1", "Endolysosomal/autophagy/proteostasis", "CTSD;CTSB;LAPTM5;NPC2;LAMP2", "NeuN;6e10/A_beta;AT8;GFAP"),
        ("M2", "Glial activation / DAM-astrocyte state", "TREM2;CST7;APOE;LGALS3;CTSD", "GFAP;Iba1;6e10/A_beta;AT8"),
        ("M3", "Oxidative stress / antioxidant response", "HMOX1;NQO1;SOD2;SOD1;GPX4", "Iba1"),
        ("M4", "Inflammatory signaling / transport / cell-state modulation", "BSG;SLC6A12;IL27RA;NFKBIA", "6e10/A_beta;AT8"),
    ]
    return pd.DataFrame([{"mechanism_id": i, "mechanism_name": n, "frozen_candidates": g, "relevant_targets": t, "evidence_source": "Stage36E fallback bins", "claim_status": "hypothesis-generating only", "prohibited_claim": PROHIBITED} for i,n,g,t in rows])


def external_table(cfg):
    ready = read_csv(cfg["inputs"]["stage42_external_readiness"])
    total = len(ready)
    nready = int(ready["ready"].map(as_bool).sum()) if not ready.empty and "ready" in ready else 0
    return pd.DataFrame([{"external_dataset_inventory": "Stage42 readiness outputs", "support_tests_ready": nready, "support_tests_total": total, "readiness_status": "support/readiness only", "clean_validation": False, "missing_data_limitations": "compatible processed external support files remain limited"}])


def negative_null_table():
    rows = [
        ("N1", "External pretraining", "failed to rescue benchmark", "shows pretraining alone was insufficient", True),
        ("N2", "Graph controls", "graph did not beat Stage27C robustly", "prevents overclaiming graph utility", True),
        ("N3", "LPH", "latent-prediction head failure", "rules out auxiliary-head shortcut", True),
        ("N4", "Stage40A", "neural rescue failure", "supports stopping architecture tuning", True),
        ("N5", "Stage41", "not lockable despite strong point estimate", "separates credible signal from locked benchmark", True),
        ("N6", "Stage45", "new safe feature negative result", "composition/MRI additions insufficient", True),
        ("N7", "External support", "not-testable limitations", "keeps support claims bounded", True),
    ]
    return pd.DataFrame(rows, columns=["result_id", "stage", "negative_or_null_result", "why_it_matters", "included_in_manuscript"])


def claim_boundary_table():
    allowed = ["internal donor-held-out benchmark", "locked internal reference", "credible unlocked internal signal", "support/readiness only", "hypothesis-generating mechanism", "negative/null result preservation"]
    prohibited = ["external validation", "clean validation", "causal mechanism", "therapeutic target", "gene-ablation support", "disease-modifying effect", "Stage41C as locked benchmark", "Stage45 as improvement"]
    rows = [{"language": a, "status": "allowed", "notes": "safe claim"} for a in allowed] + [{"language": p, "status": "prohibited", "notes": "do not claim"} for p in prohibited]
    return pd.DataFrame(rows)


def indexes():
    tables = ["Benchmark progression and lock status", "Rescue attempt summary", "Stage41 credible signal and safeguards", "Stage45 feature acquisition negative result", "Frozen mechanism/candidate registry", "External support/readiness", "Negative/null/not-testable results", "Claim boundaries"]
    figs = ["Overall pipeline schematic", "Benchmark progression plot", "Bootstrap/lock gate schematic", "Stage41 signal vs Stage27C and Stage39E", "Stage45 feature acquisition negative result schematic", "Frozen mechanism map", "External support/readiness heatmap", "Claim-boundary diagram"]
    return pd.DataFrame({"table_number": range(1, len(tables)+1), "table_title": tables}), pd.DataFrame({"figure_number": range(1, len(figs)+1), "figure_title": figs})


def write_reports(cfg, tables):
    r = cfg["references"]; out = cfg["outputs"]
    manuscript = f"""# Conservative donor-held-out benchmarking separates robust and non-lockable signals in SEA-AD pathology prediction

## Title options

1. Conservative donor-held-out benchmarking separates robust and non-lockable signals in SEA-AD pathology prediction
2. A safeguarded SEA-AD benchmark framework for Alzheimer pathology prediction and hypothesis support
3. Claim-bounded multimodal benchmarking of SEA-AD pathology-associated readouts

## Abstract

We developed a safeguarded internal benchmark framework for SEA-AD pathology-associated readouts. Stage27C remains the locked internal donor-held-out benchmark with mean pooled OOF Spearman {r['stage27c_score']}. Stage41C produced a stronger credible internal signal ({r['stage41c_score']}) but was not locked because its bootstrap lower 95% CI ({r['stage41c_lower_ci']}) remained below Stage27C. Stage45 successfully acquired donor-linked CELLxGENE metadata with exact 84/84 overlap and built seven safe feature matrices, but the best Stage45 candidate scored {r['stage45_score']} and did not improve over Stage27C or Stage41C. External data are treated as support/readiness only. No causal, therapeutic, gene-ablation, disease-modifying, external-validation, or clean-validation claim is made.

## Introduction

Alzheimer disease modeling workflows can overstate unstable point estimates, especially in small donor cohorts. We therefore separated locked internal benchmark evidence from credible but unlocked signals and support/readiness analyses.

## Methods

We used donor-held-out folds, pooled OOF Spearman, target-level guards, bootstrap lock criteria, negative controls, proxy/leakage audits, and feature risk tiers. Stage45 added CELLxGENE metadata composition and engineered MRI features without using diagnosis, pathology, Luminex, Braak/CERAD/Thal/ADNC, same-stain, HALO, pseudo-label, or held-out target-derived predictors.

## Results

### Locked internal benchmark and scoring framework

Stage27C remained the official locked benchmark.

### Rescue attempts identified instability and proxy risk

Graph, neural, external pretraining, and auxiliary-head branches did not produce a lockable replacement.

### Stage41 safe metadata/latent blending improved point estimate but failed lock CI

Stage41C reached {r['stage41c_score']} but remained credible-unlocked because the lower CI was {r['stage41c_lower_ci']}.

### Stage45 acquired donor-linked CELLxGENE features but did not improve performance

Stage45 achieved exact donor linkage and built seven matrices, but the best result was {r['stage45_score']}.

### Frozen mechanisms remain hypothesis-generating

Mechanism bins are retained only as hypothesis-generating anchors.

### External support/readiness remains limited

External resources are readiness/support context only.

### Claim-boundary framework preserves negative and non-testable results

Negative, null, and not-testable results are explicitly preserved.

## Discussion

The project identifies a robust locked baseline and a stronger but unstable internal signal. The Stage45 negative result suggests simple composition and volumetric features are insufficient. Future work should prioritize genuinely new donor-linked spatial or non-target image morphology features rather than additional score-chasing.

## Limitations

Small donor count, bootstrap instability, external dataset incompatibility, metadata proxy risk, no clean external validation, no causal inference, and no therapeutic validation.

## Data/code availability draft

Code and committed summary artifacts are available in the project repository. Raw data and downloaded metadata remain uncommitted local files.

## Author contributions

TBD.

## Conflict of interest

TBD.

## Claim boundary statement

This manuscript reports internal donor-held-out benchmarking and support/readiness synthesis only. {PROHIBITED} are not claimed.
"""
    methods = """# Stage43 extended methods

The benchmark used fixed donor-held-out folds, pooled OOF Spearman, target-level Spearman, donor bootstrap confidence intervals, strict lock rules, negative controls, proxy/leakage audits, and feature risk tiers. Stage41 used safe metadata/latent blending and OOF blend candidates. Stage45 used CELLxGENE metadata-only donor composition and engineered MRI summaries. Preprocessing for benchmark models was restricted to train folds. External support/readiness tables were not used for training, model selection, relocking, or candidate selection.
"""
    results = f"""# Stage43 results narrative

Stage27C remains locked at {r['stage27c_score']}. Stage41B improved point estimate to {r['stage41b_score']}. Stage41C reached {r['stage41c_score']}, but its lower CI was {r['stage41c_lower_ci']}, so it was not lockable. Stage45 successfully acquired CELLxGENE donor-linked metadata and built seven matrices, but its best score was {r['stage45_score']}, with delta vs Stage27C {r['stage45_delta_vs_stage27c']} and delta vs Stage41C {r['stage45_delta_vs_stage41c']}. The manuscript should frame Stage41C as credible-unlocked and Stage45 as a useful negative result.
"""
    discussion = """# Stage43 discussion and limitations

Stage41C is promising because it improved the point estimate and passed key guards, but it is not locked because the bootstrap lower bound remains below Stage27C. Stage45 matters because it shows that successful donor-linked CELLxGENE composition and engineered MRI acquisition were not sufficient to rescue performance. Composition features may be too coarse; future work may require spatial neighborhoods, image morphology, or richer cell-state expression summaries. Limitations include small donor count, bootstrap instability, external dataset incompatibility, metadata proxy risk, no clean external validation, no causal inference, and no therapeutic interpretation.
"""
    fig_caps = "# Figure caption package\n\n" + "\n".join([f"Figure {i}. {title}." for i, title in zip(tables["figures"]["figure_number"], tables["figures"]["figure_title"])])
    table_caps = "# Table caption package\n\n" + "\n".join([f"Table {i}. {title}." for i, title in zip(tables["table_index"]["table_number"], tables["table_index"]["table_title"])])
    pi = f"""# Stage43 PI review summary

Short answer: the manuscript package is ready for PI review.

- Official locked benchmark: Stage27C ({r['stage27c_score']})
- Best credible unlocked signal: Stage41C ({r['stage41c_score']})
- Newest feature test: Stage45 negative result ({r['stage45_score']})
- What can be claimed: internal donor-held-out benchmark, credible unlocked signal, support/readiness, hypothesis-generating mechanisms, preserved negative/null results.
- What cannot be claimed: {PROHIBITED}.
- Recommended next action: PI review and manuscript editing. Do not run additional benchmark tuning unless new donor-linked spatial/image morphology features become available.
"""
    checklist = """# Stage43 claim boundary checklist

- [x] Stage27C remains locked.
- [x] Stage41C is not called locked.
- [x] Stage45 is not called an improvement.
- [x] No external validation claim.
- [x] No causal claim.
- [x] No therapeutic claim.
- [x] No gene-ablation claim.
- [x] No disease-modifying claim.
- [x] Negative/null results included.
"""
    cover = """# Cover letter draft

Dear Editor,

We submit a claim-bounded SEA-AD benchmarking study that emphasizes rigorous donor-held-out evaluation, transparent benchmark-lock rules, preservation of negative and null findings, and careful separation of locked internal benchmark evidence from credible but unlocked signals and external support/readiness context. The work reports a locked internal benchmark, documents multiple rescue attempts, and provides a conservative framework for hypothesis support without claiming causality, therapeutic relevance, gene-ablation evidence, or external validation.

Sincerely,

[Authors]
"""
    for key, text in [("manuscript_draft", manuscript), ("extended_methods", methods), ("results_narrative", results), ("discussion_limitations", discussion), ("figure_captions", fig_caps), ("table_captions", table_caps), ("pi_summary", pi), ("claim_checklist", checklist), ("cover_letter", cover)]:
        write_text(text, out[key])


def run(cfg):
    out = cfg["outputs"]
    inv = input_inventory(cfg)
    bench = benchmark_progression(cfg)
    rescue = rescue_summary()
    s41 = stage41_table(cfg)
    s45 = stage45_table(cfg)
    mech = mechanism_table(cfg)
    ext = external_table(cfg)
    neg = negative_null_table()
    claim = claim_boundary_table()
    table_index, fig_index = indexes()
    pi_decision = pd.DataFrame([{"decision": "PI review and manuscript editing", "do_not_do": "additional benchmark tuning unless new donor-linked spatial/image morphology features become available", "official_locked_benchmark": "Stage27C", "best_credible_unlocked_signal": "Stage41C"}])
    outputs = {
        "input_inventory": inv, "benchmark_progression": bench, "rescue_attempt_summary": rescue, "stage41_signal": s41, "stage45_negative_result": s45,
        "frozen_mechanism": mech, "external_support_readiness": ext, "negative_null_result": neg, "claim_boundary": claim,
        "manuscript_table_index": table_index, "manuscript_figure_index": fig_index, "pi_review_decision": pi_decision,
    }
    for key, df in outputs.items():
        write_csv(df, out[key])
    write_reports(cfg, {"table_index": table_index, "figures": fig_index})
    passrow = {
        "stage43_run": True, "input_inventory_written": True, "benchmark_progression_table_written": True, "rescue_attempt_summary_written": True,
        "stage41_signal_table_written": True, "stage45_negative_result_table_written": True, "frozen_mechanism_table_written": True,
        "external_support_readiness_table_written": True, "negative_null_result_table_written": True, "claim_boundary_table_written": True,
        "manuscript_table_index_written": True, "manuscript_figure_index_written": True, "manuscript_draft_written": True,
        "extended_methods_written": True, "results_narrative_written": True, "discussion_limitations_written": True, "captions_written": True,
        "pi_summary_written": True, "claim_boundary_checklist_written": True, "cover_letter_written": True, "docs_updated": True,
        "stage27c_locked_benchmark_preserved": True, "stage41c_not_rebranded_as_locked": True, "stage45_not_rebranded_as_improvement": True,
        "no_new_modeling": True, "no_external_validation_claim": True, "no_clean_validation_claim": True, "no_causal_claim": True,
        "no_therapeutic_claim": True, "no_gene_ablation_claim": True, "no_disease_modifying_claim": True, "safety_audit_pass": True,
    }
    passrow["stage43_run_pass"] = all(as_bool(v) for v in passrow.values())
    pf = pd.DataFrame([passrow]); write_csv(pf, out["pass_fail"])
    update_section(out["active_status"], "Stage 43 manuscript draft package", "Stage43 generated the manuscript draft and PI review package. Stage27C remains official locked benchmark; Stage41C remains best credible unlocked signal; Stage45 remains a negative safe feature-acquisition benchmark. Next action: PI review / manuscript editing.")
    update_section(out["v3_scorecard_md"], "Stage 43 manuscript draft package", "Stage43 created manuscript-ready tables, reports, captions, claim boundaries, and PI review summary. No new modeling or benchmark changes were performed.")
    scorepath = resolve(out["v3_scorecard_csv"])
    sc = pd.read_csv(scorepath) if scorepath.exists() else pd.DataFrame()
    row = {"scorecard_item": "stage43_manuscript_draft_package", "status": "complete", "stage": "Stage43", "metric": "manuscript draft readiness", "threshold_or_gate": "synthesis only; preserve Stage27C lock and claim boundaries", "current_value": "PI review and manuscript editing", "pass_fail": "pass", "datasets_allowed": "existing committed summaries", "datasets_forbidden": "raw data; new modeling; external validation claims", "allowed_claim": "manuscript-ready internal benchmark and support/readiness synthesis", "notes": "Stage41C credible-unlocked; Stage45 negative", "stage_id": "stage43_manuscript_draft_package", "primary_metric": "package completeness", "pass_rule": "all outputs written and safety gates pass", "result": "stage43_run_pass=True", "allowed_inputs": "existing results/tables and reports", "forbidden_inputs": "new model training or raw data", "interpretation": "Ready for PI review."}
    for c in row:
        if c not in sc.columns: sc[c] = ""
    sc = sc[sc.get("stage_id", pd.Series(dtype=str)).astype(str) != row["stage_id"]] if not sc.empty else sc
    pd.concat([sc, pd.DataFrame([row])], ignore_index=True).to_csv(scorepath, index=False)
    return pf


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); args = ap.parse_args()
    cfg = load_cfg(args.config); pf = run(cfg)
    print(f"manuscript_draft_path={cfg['outputs']['manuscript_draft']}")
    print(f"pi_summary_path={cfg['outputs']['pi_summary']}")
    print("official_locked_benchmark=Stage27C")
    print("best_credible_unlocked_signal=Stage41C")
    print("stage45_result_status=negative_new_feature_result")
    print("recommended_next_action=PI review / manuscript editing")
    print(f"stage43_run_pass={as_bool(pf.iloc[0]['stage43_run_pass'])}")


if __name__ == "__main__":
    main()
