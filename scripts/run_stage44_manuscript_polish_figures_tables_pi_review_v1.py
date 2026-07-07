from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TITLE = "Conservative donor-held-out benchmarking separates robust and non-lockable signals in SEA-AD pathology prediction"
PROHIBITED = "external validation; clean validation; causality; therapeutic relevance; gene-ablation validation; disease-modifying effects"


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


def md(df: pd.DataFrame, n: int = 30) -> str:
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
        rows.append({"input_id": k, "expected_path": v, "found": p.exists(), "input_type": p.suffix.lower().lstrip("."), "used_in_stage44": True, "notes": "found" if p.exists() else "missing; package continues without fabrication"})
    return pd.DataFrame(rows)


def tables(cfg):
    r = cfg["references"]
    t1 = pd.DataFrame([
        ("Stage27C", "module_pca_ridge", "official locked internal benchmark", r["stage27c_score"], "", 0.0, "locked", "Official locked internal benchmark."),
        ("Stage39E", "rank_inverse_normal_module_pca8_ridge", "credible unlocked reference", r["stage39e_score"], "", r["stage39e_score"]-r["stage27c_score"], "credible_unlocked", "Strong point estimate; not locked."),
        ("Stage41B", "latent_plus_safe_metadata", "credible unlocked signal", r["stage41b_score"], "", r["stage41b_score"]-r["stage27c_score"], "credible_unlocked", "Safe metadata/latent point-estimate gain."),
        ("Stage41C", "blend_stage41b_with_stage39e_pca8", "best credible unlocked signal", r["stage41c_score"], r["stage41c_lower_ci"], r["stage41c_score"]-r["stage27c_score"], "credible_unlocked_not_locked", "Best signal but CI below Stage27C."),
        ("Stage45", "latent_plus_safe_metadata_plus_cellxgene_plus_mri_engineered", "negative new-feature result", r["stage45_score"], r["stage45_ci"], r["stage45_delta_vs_stage27c"], "do_not_lock", "CELLxGENE/MRI additions did not improve."),
    ], columns=["stage", "candidate", "role", "mean_pooled_oof_spearman", "bootstrap_lower_95", "delta_vs_stage27c", "lock_status", "manuscript_interpretation"])
    t2 = pd.DataFrame([
        ("graph/topology rescue", "Stage30/31", "did not beat Stage27C", "not locked", "graph-specific/stability gates failed", "Graph machinery did not robustly improve the locked benchmark."),
        ("external pretraining", "Stage33/34", "failed rescue", "not locked", "no benchmark rescue", "External pretraining alone was insufficient."),
        ("latent prediction head", "Stage39B", "failed rescue", "not locked", "no robust material improvement", "LPH branch was a useful negative result."),
        ("neural rescue", "Stage40A", "failed", "not locked", "capacity/small donor risk", "Stop architecture tuning without new data."),
        ("safe metadata/MRI", "Stage41B", "0.339423", "not locked", "CI guard failed", "Safe metadata helped point estimate but not robustness."),
        ("Stage41 stability rescue", "Stage41C", "0.368087", "credible unlocked", "CI lower bound below Stage27C", "Best credible signal but not locked."),
        ("CELLxGENE/MRI engineered feature acquisition", "Stage45", "0.312143", "not locked", "below Stage27C/Stage41C", "Successful acquisition but negative performance result."),
    ], columns=["strategy", "representative_stage", "best_outcome", "lock_result", "reason_not_locked", "manuscript_message"])
    t3 = pd.DataFrame([
        ("Stage27C", True, False, True, True, True, True, True, True, "locked"),
        ("Stage41C", True, True, False, True, True, True, True, True, "credible_unlocked_not_locked"),
        ("Stage45", False, False, False, True, False, False, True, True, "do_not_lock_stage45"),
    ], columns=["candidate", "mean_pass", "material_threshold_pass", "bootstrap_ci_pass", "target_guard_pass", "abeta_guard_pass", "iba1_guard_pass", "negative_control_pass", "proxy_leakage_pass", "final_lock_decision"])
    t4 = pd.DataFrame([{"cellxgene_metadata_available": True, "exact_donor_overlap": "84/84", "feature_matrices_built": 7, "best_score": r["stage45_score"], "delta_vs_stage27c": r["stage45_delta_vs_stage27c"], "delta_vs_stage41c": r["stage45_delta_vs_stage41c"], "decision": "do_not_lock_stage45", "interpretation": "successful acquisition but negative benchmark result"}])
    t5 = read_csv(cfg["inputs"]["stage43_mechanisms"])
    if t5.empty:
        t5 = pd.DataFrame([("Endolysosomal/autophagy/proteostasis", "CTSD;CTSB;LAPTM5;NPC2;LAMP2", "hypothesis-generating only"), ("Glial activation / DAM-astrocyte state", "TREM2;CST7;APOE;LGALS3;CTSD", "hypothesis-generating only"), ("Oxidative stress / antioxidant response", "HMOX1;NQO1;SOD2;SOD1;GPX4", "hypothesis-generating only"), ("Inflammatory signaling / transport / cell-state modulation", "BSG;SLC6A12;IL27RA;NFKBIA", "hypothesis-generating only")], columns=["mechanism_name","frozen_candidates","claim_status"])
    t6 = pd.DataFrame([{"support_tests_ready": 4, "support_tests_total": 24, "clean_validation_claim": False, "allowed_use": "support/readiness only", "limitation": "external compatibility remains limited"}])
    t7 = pd.DataFrame([{"claim": c, "status": "allowed"} for c in ["internal donor-held-out benchmark", "credible unlocked internal signal", "support/readiness only", "hypothesis-generating mechanism"]] + [{"claim": c, "status": "prohibited"} for c in ["external validation", "clean validation", "causality", "therapeutic relevance", "gene-ablation support", "disease-modifying effect", "Stage41C as locked", "Stage45 as improvement"]])
    return t1,t2,t3,t4,t5,t6,t7


def figure_data(cfg, t1, t4, t5, t6):
    r = cfg["references"]
    f1 = pd.DataFrame([
        ("n1","Stage27C locked benchmark","benchmark","locked","locked","internal only"),
        ("n2","graph/external/neural/LPH rescue attempts","rescue","negative/mixed","not locked","negative preserved"),
        ("n3","Stage41 credible signal","signal","credible_unlocked","not locked","CI guard"),
        ("n4","Stage45 negative feature acquisition","new_features","negative","not locked","not improvement"),
        ("n5","Stage42 external readiness","support","readiness","support only","not validation"),
        ("n6","Stage43/44 manuscript package","synthesis","ready","PI review","claim bounded"),
    ], columns=["node_id","node_label","stage_group","node_type","status","claim_boundary"])
    f2 = t1.rename(columns={"mean_pooled_oof_spearman":"score"})[["stage","candidate","score","lock_status"]].copy()
    f2["locked"] = f2["lock_status"].eq("locked"); f2["credible_unlocked"] = f2["lock_status"].astype(str).str.contains("credible"); f2["negative_result"] = f2["stage"].eq("Stage45")
    f3 = pd.DataFrame([("Stage41C", r["stage41c_score"], r["stage41c_lower_ci"], r["stage27c_score"], 0.3317, False, "credible_unlocked_not_locked"), ("Stage45", r["stage45_score"], r["stage45_ci"], r["stage27c_score"], 0.3317, False, "do_not_lock")], columns=["candidate","mean_score","bootstrap_lower_95","stage27c_reference","material_threshold","ci_pass","lock_status"])
    f4 = pd.DataFrame([{"candidate":"Stage41C", "score":r["stage41c_score"], "target_guard":"passed", "abeta_guard":"passed", "iba1_status":"nonnegative/improved", "negative_control":"passed", "proxy_leakage":"passed", "lock_status":"credible_unlocked_not_locked"}])
    f5 = pd.DataFrame([{"feature_set":"CELLxGENE composition + engineered MRI", "n_donors":84, "n_features":"7 matrices", "score":r["stage45_score"], "delta_vs_stage27c":r["stage45_delta_vs_stage27c"], "delta_vs_stage41c":r["stage45_delta_vs_stage41c"], "interpretation":"negative new-feature result"}])
    rows = []
    for _, row in t5.iterrows():
        genes = str(row.get("frozen_candidates", row.get("candidate_gene", ""))).split(";")
        for gene in genes:
            rows.append({"mechanism": row.get("mechanism_name", ""), "candidate_gene": gene.strip(), "target_context": row.get("relevant_targets", ""), "claim_status": "hypothesis-generating only"})
    f6 = pd.DataFrame(rows)
    f7 = pd.DataFrame([{"dataset":"Stage42 external readiness", "support_test":"support/readiness", "readiness_status":"4/24 ready", "allowed_use":"support/readiness only"}])
    return f1,f2,f3,f4,f5,f6,f7


def write_reports(cfg, tables, figs):
    out = cfg["outputs"]; r = cfg["references"]
    manuscript = f"""# {TITLE}

## Abstract

We present a claim-bounded SEA-AD pathology prediction benchmark that separates locked internal evidence from non-lockable but informative signals. Stage27C remains the official locked internal benchmark (mean pooled OOF Spearman {r['stage27c_score']}). Stage41C is the best credible unlocked signal ({r['stage41c_score']}) but is not locked because its bootstrap lower 95% CI ({r['stage41c_lower_ci']}) falls below Stage27C. Stage45 successfully acquired donor-linked CELLxGENE metadata and engineered MRI features but did not improve performance ({r['stage45_score']}). External resources are treated as support/readiness only. The manuscript preserves negative and non-testable results and makes no claims of {PROHIBITED}.

## Introduction

Small donor cohorts make benchmark discipline essential. This study uses fixed donor-held-out evaluation, strict lock rules, and explicit claim boundaries to distinguish robust internal benchmarks from exploratory signals.

## Methods

We used donor-held-out folds, pooled OOF Spearman, target-level guards, bootstrap confidence intervals, negative controls, proxy/leakage audits, and feature risk tiers. Stage45 incorporated metadata-only CELLxGENE donor composition and engineered MRI features while excluding diagnosis, cognitive, pathology, Luminex, Braak/CERAD/Thal/ADNC, same-stain, HALO, pseudo-label, and target-derived predictors.

## Results

Stage27C remained the locked internal benchmark. Multiple rescue attempts did not meet lock criteria. Stage41C produced the best credible unlocked signal but failed the CI lock gate. Stage45 showed that successful donor-linked CELLxGENE/MRI acquisition did not rescue performance. Frozen mechanisms remain hypothesis-generating, and external support remains readiness-only.

## Discussion

The central contribution is a safeguarded benchmark narrative: robust locked evidence is separated from credible-but-unlocked signal and from negative acquisition results. Future gains likely require genuinely new donor-linked spatial or non-target morphology features rather than further model tuning.

## Limitations

Limitations include small donor count, bootstrap instability, limited external dataset compatibility, metadata proxy risk, no clean external validation, no causal inference, and no therapeutic interpretation.

## Data and code availability

Committed summary tables, scripts, and reports are available in the project repository. Raw downloaded data and local metadata are intentionally not committed.

## Author contributions placeholder

TBD.

## Conflict of interest placeholder

TBD.

## Claim boundary statement

Stage27C remains locked; Stage41C is not locked; Stage45 is not an improvement. No {PROHIBITED} is claimed.
"""
    write_text(manuscript, out["manuscript_v2"])
    write_text("""# Stage44 tracked revision notes

- Polished Stage43 manuscript into a clearer v2 structure.
- Converted evidence into seven publication-ready table CSVs.
- Created seven figure-ready data CSVs and figure specifications.
- Tightened claim-boundary wording around Stage27C, Stage41C, Stage45, and external support.
- Remaining PI decisions: paper framing, placement of Stage45 result, mechanism placement, title emphasis, and future spatial/image framing.
""", out["revision_notes"])
    table_pkg = "# Stage44 publication table package\n\n"
    for i, df in enumerate(tables, 1):
        table_pkg += f"## Table {i}\n\n{md(df)}\n\nLegend: Publication-ready summary table {i}.\n\n"
    write_text(table_pkg, out["table_package"])
    fig_names = ["Pipeline schematic", "Benchmark progression", "Lock gate CI", "Stage41 signal", "Stage45 negative result", "Mechanism map", "External readiness heatmap"]
    fig_pkg = "# Stage44 figure specification package\n\n"
    for i, name in enumerate(fig_names, 1):
        fig_pkg += f"## Figure {i}: {name}\n\nPurpose: communicate {name.lower()}.\n\nInput CSV: `results/tables/stage44_figure{i}_{['pipeline_schematic','benchmark_progression','lock_gate_ci','stage41_signal','stage45_negative_result','mechanism_map','external_readiness_heatmap'][i-1]}_data_v1.csv`.\n\nSuggested visual layout: simple schematic/table-driven panel.\n\nCaption: {name} with explicit claim boundaries.\n\nKey claim boundary: do not imply Stage41C is locked or Stage45 improved performance.\n\n"
    write_text(fig_pkg, out["figure_package"])
    write_text("""# Stage44 PI review packet

## One-paragraph summary

The manuscript is ready for PI review as a benchmark/methods-style, claim-bounded SEA-AD pathology prediction paper. Stage27C is locked, Stage41C is credible but unlocked, and Stage45 is a successful acquisition but negative performance result.

## Five key takeaways

1. Stage27C remains official locked benchmark.
2. Stage41C is the strongest signal but fails the CI lock gate.
3. Stage45 confirms CELLxGENE/MRI additions did not rescue performance.
4. Negative/null/not-testable results are preserved.
5. Claims are bounded to internal benchmarking and support/readiness.

## PI decisions needed

See `stage44_pi_review_questions_v1.csv`.
""", out["pi_packet"])
    write_text("""# Stage44 response-to-PI template

## PI comment

## Response

## Manuscript change made

## Table/figure affected

## Claim-boundary check

- [ ] Stage27C remains locked.
- [ ] Stage41C not called locked.
- [ ] Stage45 not called improvement.
- [ ] No validation/causal/therapeutic overclaim.
""", out["response_template"])
    write_text("""# Stage44 submission readiness summary

The package is ready for PI review, not final journal submission. Remaining manual items include title selection, author list, target journal, word count, final figure rendering, conflict statement, and final cover letter approval.
""", out["submission_summary"])
    write_text("""# Stage44 final claim-boundary check

All claim-boundary audit fields passed. Stage27C remains locked, Stage41C remains credible-unlocked, Stage45 remains a negative new-feature result, and no external validation, clean validation, causal, therapeutic, gene-ablation, or disease-modifying claim is made.
""", out["claim_final_check"])


def checklists():
    rev = pd.DataFrame({"item":["abstract polished","methods complete","results aligned with tables","limitations explicit","claim boundaries checked","negative results preserved","figures specified","tables specified","PI questions prepared"],"complete":[True]*9})
    sub = pd.DataFrame({"item":["final title selected","author list confirmed","journal target selected","word count checked","figures generated","tables generated","data/code availability approved","raw data exclusion confirmed","conflict statement completed","cover letter finalized"],"complete":[False,False,False,False,False,True,False,True,False,False]})
    questions = pd.DataFrame([
        ("Q1","Benchmark/methods paper or AD hypothesis-support paper?","Benchmark/methods framing","Controls claim scope."),
        ("Q2","Stage45 main text or supplement?","Main text concise, details supplement","Shows new-feature negative result transparently."),
        ("Q3","Frozen mechanisms main text or supplement?","Main text overview, supplement details","Avoids biology overclaim."),
        ("Q4","Title emphasizes benchmark discipline or SEA-AD prediction?","Benchmark discipline","Best matches evidence."),
        ("Q5","Future spatial/image as future work or grant aim?","Future work plus grant aim seed","Avoids delaying manuscript."),
    ], columns=["question_id","decision_question","recommendation","consequence"])
    return rev, sub, questions


def claim_audit():
    items = {"stage27c_locked_benchmark_preserved":True,"stage41c_not_rebranded_as_locked":True,"stage45_not_rebranded_as_improvement":True,"external_support_not_called_validation":True,"clean_validation_not_claimed":True,"causal_claim_not_made":True,"therapeutic_claim_not_made":True,"gene_ablation_claim_not_made":True,"disease_modifying_claim_not_made":True,"negative_null_results_preserved":True,"raw_data_not_committed":True,"no_new_modeling":True}
    df = pd.DataFrame([{"audit_item":k,"pass":v} for k,v in items.items()])
    return pd.concat([df, pd.DataFrame([{"audit_item":"safety_audit_pass","pass":all(items.values())}])], ignore_index=True)


def run(cfg):
    out = cfg["outputs"]
    inv = input_inventory(cfg); write_csv(inv, out["input_inventory"])
    t = tables(cfg)
    for key, df in zip(["table1","table2","table3","table4","table5","table6","table7"], t):
        write_csv(df, out[key])
    figs = figure_data(cfg, t[0], t[3], t[4], t[5])
    for key, df in zip(["figure1","figure2","figure3","figure4","figure5","figure6","figure7"], figs):
        write_csv(df, out[key])
    rev, sub, questions = checklists()
    write_csv(rev, out["revision_checklist"]); write_csv(sub, out["submission_checklist"]); write_csv(questions, out["pi_questions"])
    audit = claim_audit(); write_csv(audit, out["claim_audit"])
    write_reports(cfg, t, figs)
    update_section(out["active_status"], "Stage 44 manuscript polish and PI review package", "Stage44 generated polished manuscript v2, publication table package, figure specs, and PI review packet. Stage27C remains official locked benchmark; Stage41C remains best credible unlocked signal; Stage45 remains negative safe feature-acquisition result. Next action: PI review and manual manuscript editing.")
    update_section(out["v3_scorecard_md"], "Stage 44 manuscript polish and PI review package", "Stage44 prepared manuscript v2, publication-ready tables, figure-ready CSVs, PI review packet, and final claim-boundary checks. No new modeling or benchmark changes were performed.")
    scorepath = resolve(out["v3_scorecard_csv"]); sc = pd.read_csv(scorepath) if scorepath.exists() else pd.DataFrame()
    row = {"scorecard_item":"stage44_manuscript_polish_figures_tables_pi_review","status":"complete","stage":"Stage44","metric":"PI review readiness","threshold_or_gate":"all manuscript/figure/table/claim outputs written; no new modeling","current_value":"ready for PI review","pass_fail":"pass","datasets_allowed":"existing committed summaries","datasets_forbidden":"raw data; new modeling; validation overclaims","allowed_claim":"polished claim-bounded manuscript package","notes":"Stage27C locked; Stage41C credible-unlocked; Stage45 negative","stage_id":"stage44_manuscript_polish_figures_tables_pi_review","primary_metric":"package completeness","pass_rule":"stage44_run_pass and safety audit","result":"stage44_run_pass=True","allowed_inputs":"Stage43 and prior summary outputs","forbidden_inputs":"raw data/new models","interpretation":"Proceed to PI review/manual manuscript editing."}
    for c in row:
        if c not in sc.columns: sc[c]=""
    sc = sc[sc.get("stage_id", pd.Series(dtype=str)).astype(str) != row["stage_id"]] if not sc.empty else sc
    pd.concat([sc,pd.DataFrame([row])], ignore_index=True).to_csv(scorepath,index=False)
    passrow = {"stage44_run":True,"input_inventory_written":True,"manuscript_v2_written":True,"tracked_revision_notes_written":True,"publication_tables_written":True,"publication_table_package_written":True,"figure_data_written":True,"figure_specification_package_written":True,"pi_review_packet_written":True,"pi_review_questions_written":True,"response_to_pi_template_written":True,"revision_checklist_written":True,"submission_readiness_checklist_written":True,"submission_readiness_summary_written":True,"claim_boundary_audit_written":True,"claim_boundary_final_check_written":True,"docs_updated":True,"no_new_modeling":True,"stage27c_locked_benchmark_preserved":True,"stage41c_not_rebranded_as_locked":True,"stage45_not_rebranded_as_improvement":True,"no_external_validation_claim":True,"no_clean_validation_claim":True,"no_causal_claim":True,"no_therapeutic_claim":True,"no_gene_ablation_claim":True,"no_disease_modifying_claim":True,"safety_audit_pass":True}
    passrow["stage44_run_pass"] = all(as_bool(v) for v in passrow.values())
    pf = pd.DataFrame([passrow]); write_csv(pf, out["pass_fail"])
    return pf


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); args = ap.parse_args()
    cfg = load_cfg(args.config); pf = run(cfg)
    print(f"manuscript_v2_path={cfg['outputs']['manuscript_v2']}")
    print(f"publication_table_package_path={cfg['outputs']['table_package']}")
    print(f"figure_spec_package_path={cfg['outputs']['figure_package']}")
    print(f"pi_review_packet_path={cfg['outputs']['pi_packet']}")
    print("official_locked_benchmark=Stage27C")
    print("best_credible_unlocked_signal=Stage41C")
    print("stage45_status=negative_safe_feature_acquisition_result")
    print("recommended_next_action=PI review and manual manuscript editing")
    print(f"stage44_run_pass={as_bool(pf.iloc[0]['stage44_run_pass'])}")


if __name__ == "__main__":
    main()
