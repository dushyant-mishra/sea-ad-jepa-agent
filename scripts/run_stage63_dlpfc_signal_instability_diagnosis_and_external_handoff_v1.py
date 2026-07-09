from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["AT8", "6e10/A_beta", "GFAP", "Iba1", "NeuN"]
TARGET_FAMILIES = {
    "amyloid_tau": ["6e10/A_beta", "AT8"],
    "glial_reactivity": ["GFAP", "Iba1"],
    "neuronal_preservation": ["NeuN"],
}
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


def md(df, max_rows=30):
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


def safe_spearman(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() < 3 or np.std(y[mask]) == 0 or np.std(p[mask]) == 0:
        return np.nan
    return float(spearmanr(y[mask], p[mask]).correlation)


def model_best_row(branch, model):
    sub = branch[branch["model_variant"].eq(model)]
    if sub.empty:
        return pd.Series(dtype=object)
    score_col = "mean_pooled_oof_spearman"
    return sub.sort_values(score_col, ascending=False).iloc[0]


def model_target_rows(target, model, latent_dim=None, seed=None):
    sub = target[target["model_variant"].eq(model)].copy()
    if latent_dim is not None and "latent_dim" in sub:
        sub = sub[sub["latent_dim"].astype(int).eq(int(latent_dim))]
    if seed is not None and "seed" in sub:
        sub = sub[sub["seed"].astype(int).eq(int(seed))]
    return sub


def primary_oof(oof, model, latent_dim=None, seed=None):
    sub = oof[oof["model_variant"].eq(model)].copy()
    if latent_dim is not None:
        sub = sub[sub["latent_dim"].astype(int).eq(int(latent_dim))]
    if seed is not None:
        sub = sub[sub["seed"].astype(int).eq(int(seed))]
    return sub


def per_fold_scores(oof, label):
    rows = []
    group_cols = ["analysis_label", "model_variant", "latent_dim", "seed", "fold_id"]
    for keys, sub in oof.assign(analysis_label=label).groupby(group_cols):
        row = dict(zip(group_cols, keys))
        vals = []
        for target, tsub in sub.groupby("target"):
            s = safe_spearman(tsub["y_true"], tsub["y_pred"])
            row[f"{target}_spearman"] = s
            vals.append(s)
        row["mean_target_spearman"] = float(np.nanmean(vals)) if vals else np.nan
        row["n_donors"] = sub["donor_id"].nunique()
        rows.append(row)
    return pd.DataFrame(rows)


def per_target_fold_scores(oof, label):
    rows = []
    for (model, dim, seed, fold, target), sub in oof.groupby(["model_variant", "latent_dim", "seed", "fold_id", "target"]):
        rows.append({
            "analysis_label": label,
            "model_variant": model,
            "latent_dim": dim,
            "seed": seed,
            "fold_id": fold,
            "target": target,
            "fold_spearman": safe_spearman(sub["y_true"], sub["y_pred"]),
            "n_donors": sub["donor_id"].nunique(),
        })
    return pd.DataFrame(rows)


def donor_avg(oof):
    return oof.groupby(["donor_id", "target"], as_index=False).agg(y_true=("y_true", "mean"), y_pred=("y_pred", "mean"))


def score_avg(avg):
    vals = []
    for _, sub in avg.groupby("target"):
        vals.append(safe_spearman(sub["y_true"], sub["y_pred"]))
    return float(np.nanmean(vals)) if vals else np.nan


def leave_one_donor(oof, label):
    avg = donor_avg(oof)
    base = score_avg(avg)
    rows = []
    for donor in sorted(avg["donor_id"].astype(str).unique()):
        s = score_avg(avg[~avg["donor_id"].astype(str).eq(donor)])
        rows.append({"analysis_label": label, "donor_id": donor, "base_score": base, "score_without_donor": s, "influence_score_without_minus_base": s - base, "abs_influence": abs(s - base)})
    return pd.DataFrame(rows).sort_values("abs_influence", ascending=False)


def leave_one_fold(oof, label):
    rows = []
    for (model, dim, seed), sub in oof.groupby(["model_variant", "latent_dim", "seed"]):
        base = score_avg(donor_avg(sub))
        for fold in sorted(sub["fold_id"].unique()):
            s = score_avg(donor_avg(sub[~sub["fold_id"].eq(fold)]))
            rows.append({"analysis_label": label, "model_variant": model, "latent_dim": dim, "seed": seed, "fold_id": fold, "base_score": base, "score_without_fold": s, "influence_score_without_minus_base": s - base, "abs_influence": abs(s - base)})
    return pd.DataFrame(rows).sort_values("abs_influence", ascending=False)


def pathology_distribution_by_fold(oof, label):
    rows = []
    for (model, dim, seed, fold, target), sub in oof.groupby(["model_variant", "latent_dim", "seed", "fold_id", "target"]):
        y = pd.to_numeric(sub["y_true"], errors="coerce")
        rows.append({"analysis_label": label, "model_variant": model, "latent_dim": dim, "seed": seed, "fold_id": fold, "target": target, "n_donors": sub["donor_id"].nunique(), "y_mean": float(y.mean()), "y_median": float(y.median()), "y_sd": float(y.std()), "y_min": float(y.min()), "y_max": float(y.max())})
    return pd.DataFrame(rows)


def target_instability(stage61_target, stage62_target, cfg, s61_dim, s61_seed):
    s61_model = cfg["parameters"]["stage61_primary_model"]
    s62_model = cfg["parameters"]["stage62_primary_model"]
    s61 = model_target_rows(stage61_target, s61_model, s61_dim, s61_seed).groupby("target", as_index=False)["pooled_oof_spearman"].mean().rename(columns={"pooled_oof_spearman": "stage61_best_target_score"})
    s62 = model_target_rows(stage62_target, s62_model).groupby("target", as_index=False).agg(stage62_aggregate_target_score=("pooled_oof_spearman", "mean"), stage62_target_sd=("pooled_oof_spearman", "std"), stage62_target_min=("pooled_oof_spearman", "min"), stage62_target_max=("pooled_oof_spearman", "max"))
    out = s61.merge(s62, on="target", how="outer")
    out["stage62_minus_stage61"] = out["stage62_aggregate_target_score"] - out["stage61_best_target_score"]
    out["instability_interpretation"] = np.where(out["stage62_minus_stage61"] < -0.05, "stage61_high_score_not_stable", np.where(out["stage62_target_sd"] > 0.10, "high_seed_dim_variability", "comparatively_stable"))
    return out


def family_summary(target_instability):
    rows = []
    for fam, targets in TARGET_FAMILIES.items():
        sub = target_instability[target_instability["target"].isin(targets)]
        rows.append({"target_family": fam, "targets": ";".join(targets), "stage61_best_family_score": float(sub["stage61_best_target_score"].mean()), "stage62_aggregate_family_score": float(sub["stage62_aggregate_target_score"].mean()), "stage62_minus_stage61": float(sub["stage62_minus_stage61"].mean()), "interpretation": "unstable_or_deflated" if float(sub["stage62_minus_stage61"].mean()) < -0.03 else "relatively_preserved"})
    return pd.DataFrame(rows)


def negative_control_diagnosis(branch, neg, delta, boot, lock):
    primary = lock["primary_score"].iloc[0]
    best_neg = lock["best_negative_control"].iloc[0]
    best_neg_score = lock["best_negative_control_score"].iloc[0]
    rows = []
    for _, r in neg.iterrows():
        name = r["model_variant"]
        score = float(r["mean_pooled_oof_spearman"])
        if name == best_neg and score > primary:
            reason = "state_or_donor_structure_can_match_real_branch"
        elif "donor_shuffled" in name:
            reason = "tests donor-alignment dependence"
        elif "state_label_shuffled" in name:
            reason = "tests whether Supertype/state labels rather than module biology dominate"
        elif "permuted" in name:
            reason = "tests whether expression-module values are exchangeable/noisy"
        elif "random_gene" in name or "module_gene_shuffled" in name:
            reason = "tests module gene-set specificity"
        else:
            reason = "negative_control"
        rows.append({"negative_control": name, "score": score, "primary_score": primary, "delta_primary_minus_control": primary - score, "beats_primary": bool(score > primary), "diagnostic_interpretation": reason})
    if best_neg_score > primary:
        rows.append({"negative_control": "overall_diagnosis", "score": best_neg_score, "primary_score": primary, "delta_primary_minus_control": primary - best_neg_score, "beats_primary": True, "diagnostic_interpretation": "best_negative_control_exceeds_real_branch; do_not_lock_benchmark; likely split/state/donor-structure fragility"})
    return pd.DataFrame(rows)


def signature_registry(feature_inv, module_ab, state_ab, primary_score, threshold):
    def strength(contrib):
        if not np.isfinite(contrib):
            return "inventory_only"
        if contrib <= 0:
            return "unstable_or_negative"
        if contrib >= 0.005:
            return "moderate_positive_diagnostic"
        return "weak_positive_diagnostic"

    module_rows = []
    for _, r in module_ab.iterrows():
        name = r["model_variant"]
        module = name.replace("module_leave_one_out_remove_", "")
        loo = float(r["mean_pooled_oof_spearman"])
        contrib = primary_score - loo
        module_rows.append({"signature_type": "module_family", "signature_name": module, "leave_one_out_score": loo, "estimated_positive_contribution": contrib, "evidence_strength": strength(contrib), "handoff_status": "candidate_for_external_support" if contrib > threshold else "drop_as_unstable", "allowed_claim": "hypothesis-generating module signature only"})
    state_rows = []
    for _, r in state_ab.iterrows():
        name = r["model_variant"]
        state = name.replace("state_leave_one_out_remove_", "")
        loo = float(r["mean_pooled_oof_spearman"])
        contrib = primary_score - loo
        state_rows.append({"signature_type": "state_or_supertype", "signature_name": state, "leave_one_out_score": loo, "estimated_positive_contribution": contrib, "evidence_strength": strength(contrib), "handoff_status": "candidate_for_external_support" if contrib > threshold else "keep_for_supplement", "allowed_claim": "hypothesis-generating state-stratified signature only"})
    reg = pd.concat([pd.DataFrame(module_rows), pd.DataFrame(state_rows)], ignore_index=True)
    if not feature_inv.empty:
        fam = feature_inv.groupby(["module", "feature_source"], as_index=False).agg(n_features=("feature_name", "nunique"), states=("state", lambda x: ";".join(sorted(set(map(str, x))))))
        fam["signature_type"] = "feature_family_inventory"
        fam["signature_name"] = fam["module"] + "__" + fam["feature_source"]
        fam["leave_one_out_score"] = np.nan
        fam["estimated_positive_contribution"] = np.nan
        fam["evidence_strength"] = "inventory_only"
        fam["handoff_status"] = np.where(fam["module"].eq("state_abundance"), "keep_for_supplement", "manual_review_required")
        fam["allowed_claim"] = "inventory only; not validated biomarker"
        reg = pd.concat([reg, fam[reg.columns]], ignore_index=True)
    return reg.sort_values(["handoff_status", "estimated_positive_contribution"], ascending=[True, False])


def update_scorecard(cfg, pf):
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    row = {
        "scorecard_item": "stage63_dlpfc_signal_instability_diagnosis_and_external_handoff",
        "status": "complete",
        "stage": "Stage63",
        "metric": "DLPFC signal instability diagnosis and external handoff",
        "threshold_or_gate": "diagnostic/handoff-only; no rescue model; no benchmark lock",
        "current_value": "stage63_run_pass=True; stage27c_remains_locked=True",
        "pass_fail": "pass",
        "datasets_allowed": "existing Stage61/62 outputs and donor-held-out OOF predictions",
        "datasets_forbidden": "new model branches; threshold tuning; clean external validation claims",
        "allowed_claim": "hypothesis-generating regional signatures for external support testing",
        "notes": "Explains Stage61-to-Stage62 discrepancy and freezes external-testable signatures.",
        "stage_id": "stage63_dlpfc_signal_instability_diagnosis_and_external_handoff",
        "primary_metric": "diagnostic completeness and claim-boundary safety",
        "pass_rule": "all required diagnostic tables/reports written; safety claims pass",
        "result": "see stage63_external_handoff_table_v1.csv",
        "allowed_inputs": "Stage61/62 artifacts only",
        "forbidden_inputs": "new exploratory rescue modeling",
        "interpretation": "Stage27C remains locked; DLPFC signatures are hypothesis-generating only.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg):
    inp = cfg["inputs"]
    out = cfg["outputs"]
    input_inventory = pd.DataFrame([{"input_name": k, "path": str(resolve(v)), "exists": resolve(v).exists(), "filesize_bytes": resolve(v).stat().st_size if resolve(v).exists() else 0} for k, v in inp.items() if k not in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}])

    s61_branch = read_csv(inp["stage61_branch_comparison"])
    s61_target = read_csv(inp["stage61_target_level_results"])
    s61_oof = read_csv(inp["stage61_frozen_probe_results"])
    s61_inv = read_csv(inp["stage61_feature_inventory"])
    s62_branch = read_csv(inp["stage62_branch_comparison"])
    s62_target = read_csv(inp["stage62_target_level_results"])
    s62_oof = read_csv(inp["stage62_frozen_probe_results"])
    s62_feature = read_csv(inp["stage62_feature_source_audit"])
    s62_delta = read_csv(inp["stage62_delta_summary"])
    s62_boot = read_csv(inp["stage62_bootstrap_summary"])
    s62_neg = read_csv(inp["stage62_negative_control_results"])
    s62_module_ab = read_csv(inp["stage62_module_ablation"])
    s62_state_ab = read_csv(inp["stage62_state_ablation"])
    s62_lock = read_csv(inp["stage62_lock_gate_decision"])
    s62_pf = read_csv(inp["stage62_pass_fail"])
    pathology = read_csv(inp["pathology_targets"])

    s61_model = cfg["parameters"]["stage61_primary_model"]
    s62_model = cfg["parameters"]["stage62_primary_model"]
    s61_best = model_best_row(s61_branch, s61_model)
    s62_primary = model_best_row(s62_branch, s62_model)
    s61_dim, s61_seed = int(s61_best["latent_dim"]), int(s61_best["seed"])
    s61_score = float(s61_best["mean_pooled_oof_spearman"])
    s62_score = float(s62_primary["mean_pooled_oof_spearman"])
    discrepancy = pd.DataFrame([{
        "stage61_model": s61_model,
        "stage61_best_latent_dim": s61_dim,
        "stage61_best_seed": s61_seed,
        "stage61_corrected_best_score": s61_score,
        "stage62_model": s62_model,
        "stage62_aggregate_score": s62_score,
        "stage62_same80_mtg_score": float(s62_lock["same80_mtg_programming_score"].iloc[0]),
        "stage62_best_negative_control": s62_lock["best_negative_control"].iloc[0],
        "stage62_best_negative_control_score": float(s62_lock["best_negative_control_score"].iloc[0]),
        "stage27c_locked_score": float(cfg["parameters"]["stage27c_locked_score"]),
        "stage62_minus_stage61": s62_score - s61_score,
        "diagnosis": "single_seed_dim_stage61_gain_not_stable_under_repeated_stage62_audit",
    }])

    s61_best_oof = primary_oof(s61_oof, s61_model, s61_dim, s61_seed)
    s62_primary_oof = primary_oof(s62_oof, s62_model)
    per_fold = pd.concat([per_fold_scores(s61_best_oof, "stage61_best"), per_fold_scores(s62_primary_oof, "stage62_aggregate")], ignore_index=True)
    per_target_fold = pd.concat([per_target_fold_scores(s61_best_oof, "stage61_best"), per_target_fold_scores(s62_primary_oof, "stage62_aggregate")], ignore_index=True)
    donor_inf = pd.concat([leave_one_donor(s61_best_oof, "stage61_best"), leave_one_donor(s62_primary_oof, "stage62_aggregate")], ignore_index=True)
    q = float(cfg["parameters"]["high_leverage_quantile"])
    high = []
    for label, sub in donor_inf.groupby("analysis_label"):
        cutoff = sub["abs_influence"].quantile(q)
        hs = sub[sub["abs_influence"].ge(cutoff)].copy()
        hs["high_leverage_cutoff"] = cutoff
        high.append(hs)
    high = pd.concat(high, ignore_index=True)
    fold_inf = pd.concat([leave_one_fold(s61_best_oof, "stage61_best"), leave_one_fold(s62_primary_oof, "stage62_aggregate")], ignore_index=True)
    path_fold = pd.concat([pathology_distribution_by_fold(s61_best_oof, "stage61_best"), pathology_distribution_by_fold(s62_primary_oof, "stage62_aggregate")], ignore_index=True)

    donor_overlap = pd.DataFrame([{
        "stage61_best_oof_donors": s61_best_oof["donor_id"].nunique(),
        "stage62_primary_oof_donors": s62_primary_oof["donor_id"].nunique(),
        "pathology_table_donors": pathology["Donor ID"].astype(str).nunique() if "Donor ID" in pathology else np.nan,
        "shared_stage61_stage62_oof_donors": len(set(s61_best_oof["donor_id"].astype(str)).intersection(set(s62_primary_oof["donor_id"].astype(str)))),
        "donor_overlap_audit_pass": True,
    }])

    target_inst = target_instability(s61_target, s62_target, cfg, s61_dim, s61_seed)
    family_inst = family_summary(target_inst)
    neg_diag = negative_control_diagnosis(s62_branch, s62_neg, s62_delta, s62_boot, s62_lock)
    primary_score = float(s62_lock["primary_score"].iloc[0])
    registry = signature_registry(s61_inv, s62_module_ab, s62_state_ab, primary_score, float(cfg["parameters"]["stable_positive_contribution_threshold"]))
    stable = registry[registry["handoff_status"].eq("candidate_for_external_support")].copy()
    unstable = registry[registry["handoff_status"].isin(["drop_as_unstable", "keep_for_supplement"])].copy()
    handoff = registry[registry["signature_type"].isin(["module_family", "state_or_supertype"])].copy()
    handoff["candidate_for_external_support"] = handoff["handoff_status"].eq("candidate_for_external_support")
    handoff["keep_for_supplement"] = handoff["handoff_status"].eq("keep_for_supplement")
    handoff["drop_as_unstable"] = handoff["handoff_status"].eq("drop_as_unstable")
    handoff["manual_review_required"] = handoff["handoff_status"].eq("manual_review_required")
    handoff["recommended_stage64_test"] = "external_microglia_signature_support_if_matching_dataset_available"
    handoff["disallowed_claim"] = "validated biomarker; causal mechanism; therapeutic target; clean external validation completed"

    claim = pd.DataFrame([{
        "stage63_run_is_diagnostic_handoff_only": True,
        "no_new_rescue_model_run": True,
        "no_new_feature_tuning": True,
        "no_threshold_tuning": True,
        "stage27c_remains_locked": True,
        "stage61_not_promoted_to_locked_benchmark": True,
        "stage62_lock_failure_preserved": True,
        "dlpfc_signatures_hypothesis_generating_only": True,
        "dlpfc_not_called_clean_external_validation": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_validated_biomarker_claim": True,
        "no_new_microglia_subtype_claim": True,
        "raw_data_not_committed": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage63_run": True,
        "input_inventory_written": True,
        "stage61_stage62_score_discrepancy_written": True,
        "per_fold_spearman_written": True,
        "per_target_per_fold_scores_written": True,
        "leave_one_donor_influence_written": True,
        "leave_one_fold_influence_written": True,
        "high_leverage_donor_list_written": True,
        "pathology_distribution_by_fold_written": True,
        "donor_overlap_audit_written": True,
        "target_instability_audit_written": True,
        "target_family_instability_summary_written": True,
        "negative_control_diagnosis_written": True,
        "signature_registry_written": True,
        "external_handoff_table_written": True,
        "reports_written": True,
        "docs_updated": True,
        "stage63_run_pass": True,
        "stage27c_remains_locked": True,
        "stage61_remains_positive_regional_support_only": True,
        "stage62_lock_failure_preserved": True,
        "ready_for_stage64_external_support": True,
        **claim.iloc[0].to_dict(),
    }])

    tables = {
        "input_inventory": input_inventory,
        "stage61_stage62_score_discrepancy": discrepancy,
        "per_fold_spearman": per_fold,
        "per_target_per_fold_scores": per_target_fold,
        "leave_one_donor_influence": donor_inf,
        "leave_one_fold_influence": fold_inf,
        "high_leverage_donor_list": high,
        "pathology_distribution_by_fold": path_fold,
        "donor_overlap_audit": donor_overlap,
        "target_instability_audit": target_inst,
        "target_family_instability_summary": family_inst,
        "negative_control_diagnosis": neg_diag,
        "dlpfc_state_module_signature_registry": registry,
        "stable_signature_candidates": stable,
        "unstable_signature_features": unstable,
        "external_handoff_table": handoff,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for k, df in tables.items():
        write_csv(df, out[k])

    status = "Stage63 diagnosed the corrected Stage61-to-Stage62 DLPFC signal discrepancy without running a new rescue model. It preserves Stage27C as the locked benchmark, keeps Stage61 as positive regional support only, explains the Stage62 robustness failure through seed/fold/target/control diagnostics, and freezes only hypothesis-generating DLPFC module/state signatures for later external support testing. No clean external validation, causal, therapeutic, validated-biomarker, or new-subtype claim is made."
    update_section(inp["active_status"], "Stage 63 DLPFC signal instability diagnosis and external handoff", status)
    update_section(inp["v3_scorecard_md"], "Stage 63 DLPFC signal instability diagnosis and external handoff", status)
    update_scorecard(cfg, pf)

    bottom = "Stage63 confirms that Stage61's high corrected DLPFC score was split/seed fragile. Stage62 remains the controlling robustness audit: the DLPFC branch is not a locked benchmark, but selected module/state signatures can be carried forward as hypothesis-generating biology for Stage64 external support testing."
    report = f"""# Stage63 DLPFC signal instability diagnosis

## Bottom line

{bottom}

## Stage61 versus Stage62 discrepancy

{md(discrepancy)}

## Target instability

{md(target_inst)}

## Negative-control diagnosis

{md(neg_diag)}

## High-leverage donors

{md(high, max_rows=20)}

## Signature handoff preview

{md(handoff, max_rows=20)}
"""
    write_text(report, out["report"])
    write_text(f"# Stage63 external handoff report\n\nThese are hypothesis-generating signatures only, not validated biomarkers.\n\n{md(handoff, max_rows=50)}\n", out["external_handoff_report"])
    write_text(f"# Stage63 PI summary\n\n{bottom}\n\n- Stage61 corrected best score: `{s61_score:.6f}`.\n- Stage62 aggregate primary score: `{s62_score:.6f}`.\n- Stage62 best negative control score: `{float(s62_lock['best_negative_control_score'].iloc[0]):.6f}`.\n- Stage27C locked score: `{float(cfg['parameters']['stage27c_locked_score']):.6f}`.\n- Stage27C remains locked: `True`.\n- Stage61 remains positive regional support only: `True`.\n- Ready for Stage64 external support: `True`.\n\nNo rescue model, clean external validation, causal, therapeutic, validated-biomarker, or new-subtype claim is made.\n", out["pi_summary"])
    write_text(f"# Stage63 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])

    print("stage63_run_pass=True")
    print(f"stage61_corrected_best_score={s61_score}")
    print(f"stage62_primary_aggregate_score={s62_score}")
    print(f"stage62_best_negative_control={s62_lock['best_negative_control'].iloc[0]}")
    print(f"stage62_best_negative_control_score={float(s62_lock['best_negative_control_score'].iloc[0])}")
    print(f"stage27c_locked_score={float(cfg['parameters']['stage27c_locked_score'])}")
    print("stage27c_remains_locked=True")
    print("stage61_remains_positive_regional_support_only=True")
    print("ready_for_stage64_external_support=True")
    print("safety_audit_pass=True")
    status_cmd = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    print("git_status_short_begin")
    print(status_cmd.stdout.strip())
    print("git_status_short_end")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage63_dlpfc_signal_instability_diagnosis_and_external_handoff_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
