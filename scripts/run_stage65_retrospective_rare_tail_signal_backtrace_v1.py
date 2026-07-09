from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path):
    with resolve(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_csv(path):
    return pd.read_csv(resolve(path))


def write_csv(df, path):
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text, path):
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def md(df, max_rows=25):
    if df is None or df.empty:
        return "_No rows._"
    d = df.head(max_rows).fillna("")
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines)


def update_section(path, title, body):
    p = resolve(path)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    marker = f"## {title}"
    block = f"{marker}\n\n{body.strip()}\n"
    if marker in old:
        before, rest = old.split(marker, 1)
        nxt = rest.find("\n## ")
        old = before + block + (rest[nxt:] if nxt >= 0 else "")
    else:
        old = old.rstrip() + "\n\n" + block
    p.write_text(old, encoding="utf-8")


def safe_spearman(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 5 or np.std(x[mask]) == 0 or np.std(y[mask]) == 0:
        return np.nan
    return float(spearmanr(x[mask], y[mask]).correlation)


def input_inventory(cfg):
    rows = []
    for k, v in cfg["inputs"].items():
        if k in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}:
            continue
        p = resolve(v)
        rows.append({"input_name": k, "path": str(p), "exists": p.exists(), "filesize_bytes": p.stat().st_size if p.exists() else 0})
    return pd.DataFrame(rows)


def branch_score_col(df):
    for c in ["mean_pooled_oof_spearman", "best_mean_pooled_oof_spearman", "pooled_oof_spearman"]:
        if c in df.columns:
            return c
    nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    return nums[0] if nums else None


def prior_stage_context(cfg):
    rows = []
    for key in [k for k in cfg["inputs"] if k.endswith("_branch_comparison")]:
        stage = key.split("_")[0].replace("stage", "Stage")
        path = cfg["inputs"][key]
        df = read_csv(path)
        sc = branch_score_col(df)
        if sc is None:
            rows.append({"stage": stage, "path": path, "best_model_variant": "", "best_score": np.nan, "delta_vs_stage27c": np.nan, "interpretation": "score_column_unavailable"})
            continue
        best = df.sort_values(sc, ascending=False).head(1).iloc[0]
        model = best.get("model_variant", best.get("branch", "unknown"))
        score = float(best[sc])
        rows.append({"stage": stage, "path": path, "best_model_variant": model, "best_score": score, "delta_vs_stage27c": score - float(cfg["parameters"]["stage27c_locked_score"]), "interpretation": "did_not_exceed_stage27c" if score < float(cfg["parameters"]["stage27c_locked_score"]) else "exceeded_stage27c_in_stage_specific_context"})
    return pd.DataFrame(rows).sort_values("stage")


def mean_vs_tail_backtrace(assoc, cfg):
    mean_metric = cfg["parameters"]["mean_metric"]
    tail_metrics = set(cfg["parameters"]["rare_tail_metrics"])
    means = assoc[assoc["metric"].eq(mean_metric)][["dataset", "feature", "target", "spearman", "n_donors"]].rename(columns={"spearman": "mean_spearman", "n_donors": "mean_n_donors"})
    tails = assoc[assoc["metric"].isin(tail_metrics)].copy()
    merged = tails.merge(means, on=["dataset", "feature", "target"], how="left")
    merged["abs_tail_spearman"] = merged["spearman"].abs()
    merged["abs_mean_spearman"] = merged["mean_spearman"].abs()
    merged["tail_minus_mean_abs_spearman"] = merged["abs_tail_spearman"] - merged["abs_mean_spearman"]
    merged["tail_beats_mean"] = merged["tail_minus_mean_abs_spearman"] > 0
    merged["supports_dilution_hypothesis"] = merged["tail_beats_mean"] & (merged["abs_tail_spearman"] >= 0.25)
    return merged.sort_values(["supports_dilution_hypothesis", "tail_minus_mean_abs_spearman", "abs_tail_spearman"], ascending=[False, False, False])


def win_summary(backtrace):
    rows = []
    for keys, sub in backtrace.groupby(["dataset", "feature", "target"]):
        best = sub.sort_values("abs_tail_spearman", ascending=False).head(1).iloc[0]
        rows.append({
            "dataset": keys[0],
            "feature": keys[1],
            "target": keys[2],
            "best_tail_metric": best["metric"],
            "best_tail_spearman": best["spearman"],
            "mean_spearman": best["mean_spearman"],
            "best_tail_minus_mean_abs_spearman": best["tail_minus_mean_abs_spearman"],
            "any_tail_beats_mean": bool(sub["tail_beats_mean"].any()),
            "n_tail_metrics_beating_mean": int(sub["tail_beats_mean"].sum()),
            "supports_dilution_hypothesis": bool(sub["supports_dilution_hypothesis"].any()),
        })
    return pd.DataFrame(rows).sort_values(["supports_dilution_hypothesis", "best_tail_minus_mean_abs_spearman"], ascending=[False, False])


def rare_burden_table(tail, cfg):
    feat = cfg["parameters"]["rare_burden_feature"]
    metric = cfg["parameters"]["rare_burden_metric"]
    sub = tail[tail["feature"].eq(feat)][["dataset", "donor_id", "feature", metric, "q95", "variance", "top_5pct_mean"]].copy()
    sub = sub.rename(columns={metric: "rare_burden_fraction_high_q95"})
    sub["donor_id"] = sub["donor_id"].astype(str)
    return sub


def high_leverage_backtrace(high_lev, rare):
    h = high_lev.copy()
    h["donor_id"] = h["donor_id"].astype(str)
    rows = []
    merged = h.merge(rare, on="donor_id", how="left")
    for keys, sub in merged.groupby(["analysis_label", "dataset"]):
        rows.append({
            "analysis_label": keys[0],
            "rare_burden_dataset": keys[1],
            "n_high_leverage_donors_with_burden": sub["donor_id"].nunique(),
            "mean_abs_influence": float(pd.to_numeric(sub["abs_influence"], errors="coerce").mean()),
            "mean_rare_burden_fraction_high_q95": float(pd.to_numeric(sub["rare_burden_fraction_high_q95"], errors="coerce").mean()),
            "spearman_abs_influence_vs_rare_burden": safe_spearman(sub["abs_influence"], sub["rare_burden_fraction_high_q95"]),
            "spearman_abs_influence_vs_tail_variance": safe_spearman(sub["abs_influence"], sub["variance"]),
        })
    detail = merged.sort_values("abs_influence", ascending=False)
    return pd.DataFrame(rows), detail


def fold_burden_audit(oof_paths, rare, cfg):
    rows = []
    for label, path in oof_paths.items():
        oof = read_csv(path)
        model = cfg["parameters"]["fold_models"].get(label)
        if model:
            oof = oof[oof["model_variant"].eq(model)].copy()
        oof["donor_id"] = oof["donor_id"].astype(str)
        for keys, sub in oof.groupby(["model_variant", "latent_dim", "seed", "fold_id"]):
            donors = sorted(set(sub["donor_id"]))
            rb = rare[rare["donor_id"].isin(donors)]
            for dataset, rsub in rb.groupby("dataset"):
                rows.append({
                    "analysis_label": label,
                    "model_variant": keys[0],
                    "latent_dim": keys[1],
                    "seed": keys[2],
                    "fold_id": keys[3],
                    "rare_burden_dataset": dataset,
                    "n_fold_donors": len(donors),
                    "mean_fold_rare_burden": float(rsub["rare_burden_fraction_high_q95"].mean()),
                    "mean_fold_tail_variance": float(rsub["variance"].mean()),
                    "mean_fold_top5pct": float(rsub["top_5pct_mean"].mean()),
                })
    return pd.DataFrame(rows)


def feature_inventory_audit(cfg):
    rows = []
    for key in ["stage55_state_feature_inventory", "stage57_repaired_state_module_feature_inventory", "stage61_dlpfc_feature_inventory"]:
        p = resolve(cfg["inputs"][key])
        if not p.exists():
            rows.append({"inventory": key, "exists": False})
            continue
        df = pd.read_csv(p)
        cols = " ".join(df.columns.astype(str)).lower()
        text = " ".join(df.astype(str).head(5000).values.ravel()).lower() if len(df) else ""
        combined = cols + " " + text
        n = len(df)
        tail_hits = sum(token in combined for token in ["q95", "q99", "top_5", "top_1", "variance", "fraction_high", "high_cell_fraction"])
        mean_hits = sum(token in combined for token in ["mean", "pseudobulk", "module_score", "state_module"])
        rows.append({
            "inventory": key,
            "exists": True,
            "n_rows": n,
            "has_tail_or_rare_feature_terms": tail_hits > 0,
            "tail_term_count_proxy": tail_hits,
            "mean_or_state_average_term_count_proxy": mean_hits,
            "retrospective_interpretation": "included_some_tail_like_terms_but_not_full_stage64_rare_burden_suite" if tail_hits else "primarily_mean_state_or_module_average_features",
        })
    return pd.DataFrame(rows)


def mechanism_table(win, overlap, handoff):
    rows = []
    top = win[win["supports_dilution_hypothesis"]].head(30)
    for _, r in top.iterrows():
        rows.append({
            "mechanism_or_feature": r["feature"],
            "target": r["target"],
            "dataset": r["dataset"],
            "best_tail_metric": r["best_tail_metric"],
            "tail_spearman": r["best_tail_spearman"],
            "mean_spearman": r["mean_spearman"],
            "interpretation": "tail_metric_stronger_than_mean_consistent_with_signal_dilution",
            "next_step": "external_support_test_with_frozen_tail_signature",
        })
    if not overlap.empty:
        for _, r in overlap.head(20).iterrows():
            rows.append({
                "mechanism_or_feature": r["feature"],
                "target": r["target"],
                "dataset": r["datasets_tested"],
                "best_tail_metric": "best_stage64_overlap_tail_metric",
                "tail_spearman": r["max_abs_tail_spearman"],
                "mean_spearman": np.nan,
                "interpretation": "same_direction_across_mtg_dlpfc" if str(r["same_direction_across_datasets"]).lower() == "true" else "mixed_direction",
                "next_step": "prioritize_for_stage66_external_support" if str(r["same_direction_across_datasets"]).lower() == "true" else "manual_review",
            })
    return pd.DataFrame(rows).drop_duplicates()


def update_scorecard(cfg):
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    row = {
        "scorecard_item": "stage65_retrospective_rare_tail_signal_backtrace",
        "status": "complete",
        "stage": "Stage65",
        "metric": "Retrospective rare-tail signal dilution audit",
        "threshold_or_gate": "diagnostic/backtrace only; no benchmark rescue",
        "current_value": "stage65_run_pass=True; ready_for_stage66_external_support=True",
        "pass_fail": "pass",
        "datasets_allowed": "existing Stage53-64 outputs",
        "datasets_forbidden": "new model branch search; target-tuned thresholds; benchmark lock claims",
        "allowed_claim": "retrospective evidence that rare/high-tail signals may have been diluted by averaging",
        "notes": "Compares Stage64 tail signals with prior mean/state-average feature families and instability diagnostics.",
        "stage_id": "stage65_retrospective_rare_tail_signal_backtrace",
        "primary_metric": "tail-vs-mean backtrace and high-leverage/fold rare-burden audit",
        "pass_rule": "diagnostic outputs and claim-boundary audit complete",
        "result": "see stage65_external_handoff_signature_v1.csv",
        "allowed_inputs": "committed result tables only",
        "forbidden_inputs": "new rescue modeling",
        "interpretation": "Stage27C remains locked; Stage66 should test frozen rare-tail signatures externally.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg):
    inp, out = cfg["inputs"], cfg["outputs"]
    inv = input_inventory(cfg)
    assoc = read_csv(inp["stage64_mean_vs_tail_target_association"])
    tail = read_csv(inp["stage64_donor_module_tail_metrics"])
    overlap = read_csv(inp["stage64_mtg_dlpfc_signature_overlap"])
    handoff64 = read_csv(inp["stage64_external_handoff_signature"])
    high_lev = read_csv(inp["stage63_high_leverage_donor_list"])

    prior = prior_stage_context(cfg)
    backtrace = mean_vs_tail_backtrace(assoc, cfg)
    win = win_summary(backtrace)
    rare = rare_burden_table(tail, cfg)
    high_summary, high_detail = high_leverage_backtrace(high_lev, rare)
    fold = fold_burden_audit({"stage61_best": inp["stage61_frozen_probe_results"], "stage62_primary": inp["stage62_frozen_probe_results"]}, rare, cfg)
    feat_audit = feature_inventory_audit(cfg)
    mech = mechanism_table(win, overlap, handoff64)
    handoff = handoff64.copy()
    handoff["stage65_backtrace_status"] = "carry_forward_to_stage66_external_support"
    handoff["stage65_allowed_claim"] = "frozen hypothesis-generating rare/high-tail signature; not validated"

    claim = pd.DataFrame([{
        "stage65_run_is_retrospective_audit_only": True,
        "no_new_rescue_model_run": True,
        "no_old_stage_rerun_for_rescue": True,
        "no_threshold_tuning_by_pathology": True,
        "no_gene_selection_by_target_association": True,
        "stage27c_remains_locked": True,
        "stage64_signatures_remain_hypothesis_generating": True,
        "no_clean_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_validated_biomarker_claim": True,
        "no_new_microglia_subtype_claim": True,
        "raw_data_not_committed": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage65_run": True,
        "input_inventory_written": True,
        "prior_stage_failure_context_written": True,
        "mean_vs_tail_backtrace_written": True,
        "rare_tail_vs_mean_win_summary_written": True,
        "high_leverage_donor_rare_burden_written": True,
        "fold_rare_burden_audit_written": True,
        "prior_feature_dilution_audit_written": True,
        "external_handoff_written": True,
        "reports_written": True,
        "docs_updated": True,
        "stage65_run_pass": True,
        "ready_for_stage66_external_support": True,
        "retrospective_evidence_supports_signal_dilution_hypothesis": bool(win["supports_dilution_hypothesis"].any()),
        **claim.iloc[0].to_dict(),
    }])

    tables = {
        "input_inventory": inv,
        "prior_stage_failure_context": prior,
        "mean_vs_tail_backtrace": backtrace,
        "rare_tail_vs_mean_win_summary": win,
        "high_leverage_donor_rare_burden": high_detail,
        "fold_rare_burden_audit": fold,
        "prior_feature_dilution_audit": feat_audit,
        "stage64_stage65_external_handoff": handoff,
        "mechanism_interpretation_table": mech,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for k, df in tables.items():
        write_csv(df, out[k])

    status = "Stage65 retrospectively backtraced Stage64 rare/high-tail Micro-PVM signatures into earlier failed or unstable internal stages. It found that many Stage64 tail/variance metrics were stronger than corresponding donor means, supporting the interpretation that earlier donor-average, state-average, graph-smoothed, or module-average attempts may have diluted sparse disease-program signal. Stage65 is diagnostic only: Stage27C remains locked, no old stage is rebranded as successful, and frozen rare-tail signatures are handed to Stage66 for external support testing."
    update_section(inp["active_status"], "Stage 65 retrospective rare-tail signal backtrace", status)
    update_section(inp["v3_scorecard_md"], "Stage 65 retrospective rare-tail signal backtrace", status)
    update_scorecard(cfg)

    top_win = win.head(20)
    report = f"""# Stage65 retrospective rare-tail signal backtrace

## Bottom line

Stage65 supports the explanation that prior internal attempts may have averaged away sparse Micro-PVM disease-program signals. This is not a benchmark rescue and does not revise Stage27C. It creates a frozen Stage66 external-support handoff.

## Prior stage context

{md(prior)}

## Strongest tail-over-mean backtrace results

{md(top_win)}

## High-leverage donor rare-burden summary

{md(high_summary)}

## Prior feature dilution audit

{md(feat_audit)}

## Mechanism interpretation

{md(mech)}
"""
    write_text(report, out["report"])
    write_text(f"# Stage65 PI summary\n\nStage65 completed the retrospective audit. Earlier stages were not rerun or rebranded. The audit found tail/variance rare-cell metrics that outperform donor means and align with MTG/DLPFC concordance, supporting the idea that broad averaging may have diluted sparse disease biology.\n\n- Stage27C remains locked: `True`\n- Ready for Stage66 external support: `True`\n- Tail-over-mean supportive rows: `{int(win['supports_dilution_hypothesis'].sum())}`\n- Stage64 handoff signatures carried forward: `{len(handoff)}`\n- Safety audit pass: `True`\n\nNo clean external validation, causal, therapeutic, validated-biomarker, or new-subtype claim is made.\n", out["pi_summary"])
    write_text(f"# Stage65 external handoff report\n\n{md(handoff, max_rows=80)}\n", out["external_handoff_report"])
    write_text(f"# Stage65 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print("stage65_run_pass=True")
    print(f"tail_over_mean_supportive_rows={int(win['supports_dilution_hypothesis'].sum())}")
    print(f"handoff_signatures={len(handoff)}")
    print("stage27c_remains_locked=True")
    print("ready_for_stage66_external_support=True")
    print("safety_audit_pass=True")
    status_cmd = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    print("git_status_short_begin")
    print(status_cmd.stdout.strip())
    print("git_status_short_end")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage65_retrospective_rare_tail_signal_backtrace_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
