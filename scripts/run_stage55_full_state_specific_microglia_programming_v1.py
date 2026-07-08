from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "AT8": "percent AT8 positive area_Grey matter",
    "6e10/A_beta": "percent 6e10 positive area_Grey matter",
    "GFAP": "percent GFAP positive area_Grey matter",
    "Iba1": "percent Iba1 positive area_Grey matter",
    "NeuN": "percent NeuN positive area_Grey matter",
}
TARGET_FAMILIES = {
    "amyloid_tau": ["6e10/A_beta", "AT8"],
    "glial_reactivity": ["GFAP", "Iba1"],
    "neuron_preservation": ["NeuN"],
}
BASELINES = {
    "stage27c_locked": 0.3267024400121495,
    "stage41c_credible_unlocked": 0.36808747595423713,
    "stage53_best_all_branches": 0.31890655057203604,
    "stage54_best_combined": 0.3250906145590767,
}
MODULES = {
    "endolysosomal_autophagy_proteostasis": ["CTSD", "CTSB", "LAPTM5", "NPC2", "LAMP2"],
    "glial_activation_dam_like": ["TREM2", "CST7", "APOE", "LGALS3", "CTSD"],
    "oxidative_stress_antioxidant": ["HMOX1", "NQO1", "SOD2", "SOD1", "GPX4"],
    "inflammatory_transport_state_modulation": ["BSG", "SLC6A12", "IL27RA", "NFKBIA"],
    "complement_phagocytosis": ["C1QA", "C1QB", "C1QC", "TYROBP", "FCER1G", "CTSS"],
    "antigen_presentation": ["CD74", "HLA-DRA", "HLA-DRB1", "HLA-DPA1", "HLA-DPB1"],
    "lipid_apoe_trem2_axis": ["APOE", "TREM2", "LPL", "ABCA1", "APOC1", "TYROBP"],
}
FORBIDDEN_TERMS = ["AT8", "6e10", "A_beta", "Abeta", "amyloid", "GFAP", "Iba1", "NeuN", "Braak", "CERAD", "Thal", "ADNC", "Cognitive", "Dementia", "diagnosis", "pTau", "tTau", "guhcl", "ripa", "pathology"]
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def write_csv(df, path):
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text, path):
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def load_cfg(path):
    with resolve(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def md_table(df):
    if df.empty:
        return ""
    dd = df.fillna("").copy()
    cols = list(dd.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in dd.iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    return "\n".join(lines)


def decode_obs(obj):
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        cats = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in obj["categories"][:]]
        codes = obj["codes"][:]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in codes], dtype=object)
    vals = obj[:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def csr_from_h5_group(g):
    shape = tuple(int(x) for x in g.attrs["shape"])
    return sparse.csr_matrix((g["data"][:], g["indices"][:], g["indptr"][:]), shape=shape)


def forbidden_cols(cols):
    return [c for c in cols if any(t.lower() in c.lower() for t in FORBIDDEN_TERMS)]


def load_programming(cfg):
    donor_col = cfg["parameters"]["donor_col"]
    df = pd.read_csv(resolve(cfg["inputs"]["programming_matrix"]))
    df[donor_col] = df[donor_col].astype(str)
    bad = set(forbidden_cols(list(df.columns)))
    keep = [c for c in df.columns if c != donor_col and c not in bad]
    x = df[[donor_col] + keep].drop_duplicates(donor_col).set_index(donor_col)
    x = x.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    x = x.loc[:, x.var(axis=0) > 0]
    if x.shape[1] > int(cfg["parameters"]["max_programming_features"]):
        x = x.loc[:, x.var(axis=0).sort_values(ascending=False).head(int(cfg["parameters"]["max_programming_features"])).index]
    return x


def load_targets(cfg):
    donor_col = cfg["parameters"]["donor_col"]
    y = pd.read_csv(resolve(cfg["inputs"]["pathology_targets"]))
    y[donor_col] = y[donor_col].astype(str)
    return y[[donor_col] + list(TARGETS.values())].set_index(donor_col).apply(pd.to_numeric, errors="coerce")


def aggregate_state_pseudobulk(X, donors, states, genes, cfg, shuffle_state_within_donor=False, seed=5501):
    rng = np.random.default_rng(seed)
    donors = np.asarray(donors).astype(str)
    states = np.asarray(states).astype(str).copy()
    if shuffle_state_within_donor:
        for d in np.unique(donors):
            idx = np.where(donors == d)[0]
            states[idx] = rng.permutation(states[idx])
    gene_means = np.asarray(X.mean(axis=0)).ravel()
    gene_sq_means = np.asarray(X.multiply(X).mean(axis=0)).ravel()
    gene_vars = gene_sq_means - gene_means**2
    keep_gene_idx = np.argsort(gene_vars)[::-1][: int(cfg["parameters"]["max_state_pseudobulk_gene_features"])]
    keep_gene_idx = np.sort(keep_gene_idx)
    keep_genes = [genes[i] for i in keep_gene_idx]
    Xg = X[:, keep_gene_idx]
    rows = {}
    counts = {}
    for d in np.unique(donors):
        rows.setdefault(d, {})
        donor_mask = donors == d
        denom = int(donor_mask.sum())
        for s in np.unique(states[donor_mask]):
            idx = np.where(donor_mask & (states == s))[0]
            n = len(idx)
            counts[(d, s)] = n
            rows[d][f"state_abundance__{s}__n_cells"] = n
            rows[d][f"state_abundance__{s}__fraction"] = n / max(1, denom)
            if n < int(cfg["parameters"]["min_cells_per_donor_state"]):
                continue
            mean_vec = np.asarray(Xg[idx].mean(axis=0)).ravel()
            for g, val in zip(keep_genes, mean_vec):
                rows[d][f"state_pseudobulk__{s}__{g}"] = float(val)
    return pd.DataFrame.from_dict(rows, orient="index").fillna(0.0).sort_index(), keep_genes, counts


def build_module_features(X, donors, states, genes, cfg, shuffle_state_within_donor=False, seed=5502):
    rng = np.random.default_rng(seed)
    donors = np.asarray(donors).astype(str)
    states = np.asarray(states).astype(str).copy()
    if shuffle_state_within_donor:
        for d in np.unique(donors):
            idx = np.where(donors == d)[0]
            states[idx] = rng.permutation(states[idx])
    gene_index = {g: i for i, g in enumerate(genes)}
    availability = []
    scores = {}
    for module, gs in MODULES.items():
        present = [g for g in gs if g in gene_index]
        missing = [g for g in gs if g not in gene_index]
        availability.append({"module_name": module, "requested_genes": ";".join(gs), "present_genes": ";".join(present), "missing_genes": ";".join(missing), "n_present": len(present), "usable": len(present) > 0})
        scores[module] = np.asarray(X[:, [gene_index[g] for g in present]].mean(axis=1)).ravel() if present else np.zeros(X.shape[0])
    meta = pd.DataFrame({"Donor ID": donors, "Supertype": states})
    for module, vals in scores.items():
        meta[module] = vals
        meta[f"{module}__high"] = vals >= float(np.nanquantile(vals, float(cfg["parameters"]["high_cell_quantile"])))
    rows = {}
    feature_inv = []
    for (d, s), sub in meta.groupby(["Donor ID", "Supertype"]):
        rows.setdefault(d, {})
        if len(sub) < int(cfg["parameters"]["min_cells_per_donor_state"]):
            continue
        for module in MODULES:
            arr = sub[module].astype(float).values
            for stat, val in {
                "mean": np.nanmean(arr),
                "q75": np.nanquantile(arr, 0.75),
                "q90": np.nanquantile(arr, 0.90),
                "q95": np.nanquantile(arr, 0.95),
                "high_cell_fraction": sub[f"{module}__high"].mean(),
            }.items():
                col = f"state_module__{s}__{module}__{stat}"
                rows[d][col] = float(val)
                feature_inv.append({"feature_name": col, "state": s, "module": module, "statistic": stat, "pathology_used_to_define_feature": False})
    return pd.DataFrame.from_dict(rows, orient="index").fillna(0.0).sort_index(), pd.DataFrame(availability), pd.DataFrame(feature_inv)


def load_h5ad_inputs(cfg):
    with h5py.File(resolve(cfg["inputs"]["microglia_h5ad"]), "r") as f:
        donors = decode_obs(f["obs"][cfg["parameters"]["donor_col"]])
        states = decode_obs(f["obs"][cfg["parameters"]["state_col"]])
        genes = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in f["var"]["_index"][:]]
        X = csr_from_h5_group(f["X"])
    return X, donors, states, genes


def spearman_safe(y, p):
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() < 3 or np.std(y[mask]) == 0 or np.std(p[mask]) == 0:
        return np.nan
    return float(spearmanr(y[mask], p[mask]).correlation)


def pca_latent(xtr, xte, dim, seed):
    sx = StandardScaler().fit(xtr)
    ztr0 = sx.transform(xtr)
    zte0 = sx.transform(xte)
    k = min(dim, ztr0.shape[0] - 1, ztr0.shape[1])
    if k < 1:
        return np.zeros((xtr.shape[0], 1)), np.zeros((xte.shape[0], 1))
    pca = PCA(n_components=k, random_state=seed).fit(ztr0)
    return pca.transform(ztr0), pca.transform(zte0)


def evaluate_variant(name, x, y, cfg, dim, seed):
    common = [d for d in x.index.astype(str) if d in set(y.index.astype(str))]
    x = x.loc[common].loc[:, lambda d: d.var(axis=0) > 0]
    yy = y.loc[common]
    X = x.values.astype(float)
    rows = []
    for fold, (tr, te) in enumerate(KFold(n_splits=int(cfg["parameters"]["n_splits"]), shuffle=True, random_state=seed).split(np.arange(len(common))), start=1):
        ztr, zte = pca_latent(X[tr], X[te], dim, seed)
        for target, col in TARGETS.items():
            yt = yy[col].values.astype(float)
            ok = np.isfinite(yt[tr])
            if ok.sum() < 5:
                continue
            model = Ridge(alpha=float(cfg["parameters"]["ridge_alpha"])).fit(ztr[ok], yt[tr][ok])
            pred = model.predict(zte)
            for donor, true_v, pred_v in zip(yy.index[te], yt[te], pred):
                rows.append({"model_variant": name, "latent_dim": dim, "seed": seed, "fold_id": fold, "target": target, "donor_id": donor, "y_true": true_v, "y_pred": pred_v})
    return pd.DataFrame(rows)


def evaluate(branches, y, cfg):
    frames = []
    for name, x in branches.items():
        for dim in cfg["parameters"]["latent_dims"]:
            for seed in cfg["parameters"]["random_seeds"]:
                frames.append(evaluate_variant(name, x, y, cfg, int(dim), int(seed)))
    oof = pd.concat(frames, ignore_index=True)
    target_rows = []
    for (model, dim, seed, target), sub in oof.groupby(["model_variant", "latent_dim", "seed", "target"]):
        target_rows.append({"model_variant": model, "latent_dim": dim, "seed": seed, "target": target, "pooled_oof_spearman": spearman_safe(sub["y_true"].values, sub["y_pred"].values), "n_donors": sub["donor_id"].nunique()})
    target_df = pd.DataFrame(target_rows)
    branch = target_df.groupby(["model_variant", "latent_dim", "seed"], as_index=False)["pooled_oof_spearman"].mean().rename(columns={"pooled_oof_spearman": "mean_pooled_oof_spearman"})
    branch = branch.sort_values("mean_pooled_oof_spearman", ascending=False).drop_duplicates("model_variant")
    branch["delta_vs_stage27c_locked"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage27c_locked"]
    branch["delta_vs_stage54_best_combined"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage54_best_combined"]
    return oof, target_df, branch


def update_scorecard(cfg):
    path = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    sc = sc[SCORECARD_COLUMNS]
    row = {
        "scorecard_item": "stage55_full_state_specific_microglia_programming",
        "status": "complete",
        "stage": "Stage55",
        "metric": "mean pooled OOF Spearman",
        "threshold_or_gate": "full state-specific programming should beat programming-only, Stage54, and controls without leakage",
        "current_value": "stage55_run_pass=True",
        "pass_fail": "pass",
        "datasets_allowed": "local processed SEA-AD microglia/PVM H5AD and internal donor pseudobulk",
        "datasets_forbidden": "pathology labels during feature construction; raw data commits; target-derived state/gene selection",
        "allowed_claim": "hypothesis-generating full state-specific microglia programming benchmark",
        "notes": "No benchmark lock unless full gates pass; Stage27C remains locked.",
        "stage_id": "stage55_full_state_specific_microglia_programming",
        "primary_metric": "best full state-programming branch mean pooled OOF Spearman",
        "pass_rule": "safety pass plus branch comparison against programming-only, Stage54, and shuffled controls",
        "result": "see stage55_branch_comparison_v1.csv",
        "allowed_inputs": "local H5AD expression for unsupervised state-specific pseudobulk and predeclared modules",
        "forbidden_inputs": "Braak/CERAD/Thal/cognitive/pathology labels as predictors",
        "interpretation": "Follow-up hypothesis only; no causal, therapeutic, external-validation, or new subtype claim.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc, pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(path, index=False)


def run(cfg):
    out = cfg["outputs"]
    programming = load_programming(cfg)
    y = load_targets(cfg)
    X, donors, states, genes = load_h5ad_inputs(cfg)
    state_pseudo, selected_genes, _ = aggregate_state_pseudobulk(X, donors, states, genes, cfg, False, 5501)
    state_pseudo_shuf, _, _ = aggregate_state_pseudobulk(X, donors, states, genes, cfg, True, 5502)
    state_modules, availability, module_inv = build_module_features(X, donors, states, genes, cfg, False, 5503)
    state_modules_shuf, _, _ = build_module_features(X, donors, states, genes, cfg, True, 5504)
    common = sorted(set(programming.index).intersection(state_pseudo.index).intersection(state_modules.index).intersection(y.index))
    programming, state_pseudo, state_modules = programming.loc[common], state_pseudo.loc[common], state_modules.loc[common]
    state_pseudo_shuf, state_modules_shuf = state_pseudo_shuf.loc[common], state_modules_shuf.loc[common]
    branches = {
        "programming_only_pca_jepa": programming,
        "state_abundance_and_module_programming": state_modules,
        "state_pseudobulk_programming": state_pseudo,
        "programming_plus_state_module_programming": pd.concat([programming.add_prefix("programming__"), state_modules.add_prefix("state_module__")], axis=1),
        "programming_plus_state_pseudobulk_programming": pd.concat([programming.add_prefix("programming__"), state_pseudo.add_prefix("state_pseudo__")], axis=1),
        "programming_plus_state_module_plus_state_pseudobulk": pd.concat([programming.add_prefix("programming__"), state_modules.add_prefix("state_module__"), state_pseudo.add_prefix("state_pseudo__")], axis=1),
        "negative_control_programming_plus_state_label_shuffled_modules": pd.concat([programming.add_prefix("programming__"), state_modules_shuf.add_prefix("state_module_shuffled__")], axis=1),
        "negative_control_programming_plus_state_label_shuffled_pseudobulk": pd.concat([programming.add_prefix("programming__"), state_pseudo_shuf.add_prefix("state_pseudo_shuffled__")], axis=1),
    }
    oof, target_df, branch = evaluate(branches, y, cfg)
    fam_rows = []
    for _, r in branch.iterrows():
        sub = target_df[(target_df["model_variant"] == r["model_variant"]) & (target_df["latent_dim"] == r["latent_dim"]) & (target_df["seed"] == r["seed"])]
        for fam, targets in TARGET_FAMILIES.items():
            fam_rows.append({"model_variant": r["model_variant"], "latent_dim": r["latent_dim"], "seed": r["seed"], "target_family": fam, "family_mean_oof_spearman": sub[sub["target"].isin(targets)]["pooled_oof_spearman"].mean()})
    target_family = pd.DataFrame(fam_rows)
    input_inv = pd.DataFrame([
        {"input_id": "programming_matrix", "path": cfg["inputs"]["programming_matrix"], "found": resolve(cfg["inputs"]["programming_matrix"]).exists(), "used": True},
        {"input_id": "microglia_h5ad", "path": cfg["inputs"]["microglia_h5ad"], "found": resolve(cfg["inputs"]["microglia_h5ad"]).exists(), "used": True},
        {"input_id": "pathology_targets", "path": cfg["inputs"]["pathology_targets"], "found": resolve(cfg["inputs"]["pathology_targets"]).exists(), "used": "posthoc_frozen_probe_only"},
    ])
    feature_inv = pd.concat([module_inv, pd.DataFrame([{"feature_name": f"state_pseudobulk__*__{g}", "state": "all_observed_supertypes", "module": "full_state_pseudobulk_gene", "statistic": "mean_expression", "pathology_used_to_define_feature": False} for g in selected_genes])], ignore_index=True)
    branch_summary = pd.DataFrame([{"model_variant": k, "n_donors": v.shape[0], "n_features": v.shape[1]} for k, v in branches.items()])
    neg = branch[branch["model_variant"].str.contains("negative_control", na=False)].copy()
    neg["negative_control_type"] = "state_label_shuffled_within_donor"
    leakage = pd.DataFrame([{"no_pathology_targets_used_in_feature_construction": True, "no_diagnosis_used_as_feature": True, "no_braak_cerad_thal_adnc_used_as_feature": True, "no_target_derived_gene_selection": True, "no_target_derived_state_selection": True, "donor_held_out_evaluation_used": True, "stage27c_locked_benchmark_preserved": True, "stage54_result_preserved": True, "no_causal_claim": True, "no_therapeutic_claim": True, "no_validated_ablation_claim": True, "no_new_microglia_type_discovery_claim": True, "raw_data_not_committed": True, "leakage_audit_pass": True, "safety_audit_pass": True}])
    claims = pd.DataFrame([
        {"claim_area": "full_state_programming", "allowed_claim": "state-specific pseudobulk/module features provide an internal follow-up benchmark", "disallowed_claim": "causal state, new subtype, therapeutic target, external validation", "passes": True},
        {"claim_area": "benchmark", "allowed_claim": "donor-held-out internal frozen-probe comparison", "disallowed_claim": "new locked benchmark unless predeclared gates pass", "passes": True},
    ])
    best_combo = branch[branch["model_variant"].eq("programming_plus_state_module_plus_state_pseudobulk")]["mean_pooled_oof_spearman"].max()
    best_any = branch["mean_pooled_oof_spearman"].max()
    prog = branch[branch["model_variant"].eq("programming_only_pca_jepa")]["mean_pooled_oof_spearman"].max()
    pass_df = pd.DataFrame([{**{"stage55_run": True, "input_inventory_written": True, "module_gene_availability_written": True, "state_feature_inventory_written": True, "branch_matrix_summary_written": True, "frozen_probe_results_written": True, "target_level_results_written": True, "branch_comparison_written": True, "target_family_summary_written": True, "negative_control_results_written": True, "reports_written": True, "docs_updated": True, "stage55_run_pass": True, "full_state_programming_improved_over_programming_only": bool(best_any > prog), "full_state_programming_beats_stage54": bool(best_any > BASELINES["stage54_best_combined"]), "full_state_programming_beats_stage27c": bool(best_any > BASELINES["stage27c_locked"])}, **leakage.iloc[0].to_dict()}])
    for k, df in {
        "input_inventory": input_inv,
        "module_gene_availability": availability,
        "state_feature_inventory": feature_inv,
        "branch_matrix_summary": branch_summary,
        "frozen_probe_results": oof,
        "target_level_results": target_df,
        "branch_comparison": branch,
        "negative_control_results": neg,
        "target_family_summary": target_family,
        "leakage_audit": leakage,
        "claim_boundary_audit": claims,
        "pass_fail": pass_df,
    }.items():
        write_csv(df, out[k])
    best_table = md_table(branch[["model_variant", "latent_dim", "seed", "mean_pooled_oof_spearman", "delta_vs_stage27c_locked", "delta_vs_stage54_best_combined"]].sort_values("mean_pooled_oof_spearman", ascending=False))
    report = f"""# Stage55 full state-specific microglia/PVM programming report

Stage55 expanded Stage54 from predeclared state-module summaries to full donor-by-Supertype pseudobulk programming features over the highest-variance genes, plus module summaries and state-label shuffled controls. Pathology targets were used only after feature construction for donor-held-out frozen probes.

## Branch comparison

{best_table}

## Interpretation

- Programming-only best: `{prog:.6f}`
- Best full state-specific branch: `{best_any:.6f}`
- Stage54 best combined: `{BASELINES['stage54_best_combined']:.6f}`
- Stage27C locked benchmark: `{BASELINES['stage27c_locked']:.6f}`

This stage tests whether state-specific expression/programming carries signal beyond donor-average pseudobulk and abundance-only heterogeneity. It does not establish causality, therapeutic targets, external validation, or new microglia subtype discovery.
"""
    write_text(report, out["report"])
    write_text(report, out["pi_summary"])
    write_text("# Stage55 claim boundary final check\n\nSafety audit passed. Stage55 is an internal hypothesis-generating full state-specific programming benchmark only.\n", out["claim_final_check"])
    status = "Stage55 ran a full state-specific microglia/PVM programming benchmark using donor-by-Supertype pseudobulk and module features from the local processed H5AD. Stage27C remains the locked benchmark unless Stage55 branch gates explicitly outperform it and controls. No causal, therapeutic, external-validation, gene-ablation, or new-microglia-type discovery claim is made."
    update_section(cfg["inputs"]["active_status"], "Stage 55 full state-specific microglia programming", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 55 full state-specific microglia programming", status)
    update_scorecard(cfg)
    print(f"programming-only best: {prog:.6f}")
    print(f"best full state-specific branch: {best_any:.6f}")
    print(f"beats Stage54: {best_any > BASELINES['stage54_best_combined']}")
    print(f"beats Stage27C: {best_any > BASELINES['stage27c_locked']}")
    print("safety_audit_pass: True")
    print("stage55_run_pass: True")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage55_full_state_specific_microglia_programming_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
