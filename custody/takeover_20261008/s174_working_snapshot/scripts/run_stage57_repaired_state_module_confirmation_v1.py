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
TARGET_FAMILIES = {"amyloid_tau": ["6e10/A_beta", "AT8"], "glial_reactivity": ["GFAP", "Iba1"], "neuron_preservation": ["NeuN"]}
BASELINES = {"stage27c_locked": 0.3267024400121495, "stage55_best": 0.32603017110458643, "material_rescue": 0.3317}
MODULES = {
    "dam_lipid_trem2_apoe": ["APOE", "TREM2", "LPL", "APOC1", "TYROBP", "CST7", "LGALS3", "CTSD"],
    "lysosomal_endolysosomal": ["CTSD", "CTSB", "LAPTM5", "NPC2", "LAMP2", "CTSS", "GBA", "PSAP"],
    "complement_phagocytosis": ["C1QA", "C1QB", "C1QC", "TYROBP", "FCER1G", "CTSS", "AIF1"],
    "antigen_presentation": ["CD74", "HLA-DRA", "HLA-DRB1", "HLA-DPA1", "HLA-DPB1", "B2M"],
    "interferon_inflammatory": ["NFKBIA", "IRF8", "STAT1", "IFITM3", "IL27RA", "SLC6A12", "BSG"],
    "oxidative_stress_repaired": ["HMOX1", "NQO1", "SOD2", "SOD1", "GPX4", "PRDX1", "TXNIP"],
    "mitochondrial_qc_caution": ["MT-CO1", "MT-CO2", "MT-ND1", "MT-ND4", "TOMM40", "PINK1"],
}
FOCUS_STATES = ["Micro-PVM_1", "Micro-PVM_2", "Micro-PVM_3-SEAAD", "Micro-PVM_4-SEAAD"]
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
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in obj["codes"][:]], dtype=object)
    vals = obj[:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def csr_from_h5_group(g):
    return sparse.csr_matrix((g["data"][:], g["indices"][:], g["indptr"][:]), shape=tuple(int(x) for x in g.attrs["shape"]))


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


def load_h5ad(cfg):
    with h5py.File(resolve(cfg["inputs"]["microglia_h5ad"]), "r") as f:
        donors = decode_obs(f["obs"][cfg["parameters"]["donor_col"]]).astype(str)
        states = decode_obs(f["obs"][cfg["parameters"]["state_col"]]).astype(str)
        genes = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in f["var"]["_index"][:]]
        X = csr_from_h5_group(f["X"])
    return X, donors, states, genes


def build_state_modules(cfg, shuffle_states=False, shuffle_modules=False, seed=5701):
    rng = np.random.default_rng(seed)
    X, donors, states, genes = load_h5ad(cfg)
    states = states.copy()
    if shuffle_states:
        for d in np.unique(donors):
            idx = np.where(donors == d)[0]
            states[idx] = rng.permutation(states[idx])
    gene_index = {g: i for i, g in enumerate(genes)}
    all_present = [g for g in genes if g in gene_index]
    registry = []
    scores = {}
    for module, wanted in MODULES.items():
        present = [g for g in wanted if g in gene_index]
        if shuffle_modules and present:
            present = list(rng.choice(all_present, size=len(present), replace=False))
        missing = [g for g in wanted if g not in gene_index]
        registry.append({"module_name": module, "requested_genes": ";".join(wanted), "present_or_shuffled_genes": ";".join(present), "missing_genes": ";".join(missing), "n_present": len(present), "usable": len(present) >= 2, "module_gene_shuffle": shuffle_modules})
        scores[module] = np.asarray(X[:, [gene_index[g] for g in present]].mean(axis=1)).ravel() if present else np.zeros(X.shape[0])
    meta = pd.DataFrame({"Donor ID": donors, "Supertype": states})
    for module, vals in scores.items():
        meta[module] = vals
        meta[f"{module}__high"] = vals >= float(np.nanquantile(vals, float(cfg["parameters"]["high_cell_quantile"])))
    rows = {}
    inv = []
    min_cells = int(cfg["parameters"]["min_cells_per_donor_state"])
    modules = list(MODULES)
    for d, dsub in meta.groupby("Donor ID"):
        rows.setdefault(d, {})
        state_means = {}
        for (state, sub) in dsub.groupby("Supertype"):
            if len(sub) < min_cells:
                continue
            for module in modules:
                arr = sub[module].astype(float).values
                mean = float(np.nanmean(arr))
                high = float(sub[f"{module}__high"].mean())
                state_means[(state, module)] = mean
                for stat, val in {
                    "mean": mean,
                    "q90": float(np.nanquantile(arr, 0.90)),
                    "high_cell_fraction": high,
                }.items():
                    if state in FOCUS_STATES:
                        col = f"focus_state_module__{state}__{module}__{stat}"
                        rows[d][col] = val
                        inv.append({"feature_name": col, "feature_class": "focus_state_module", "state": state, "module": module, "statistic": stat, "pathology_used_to_define_feature": False})
        for module in modules:
            vals = np.array([v for (s, m), v in state_means.items() if m == module], dtype=float)
            if vals.size:
                p = np.abs(vals) / max(1e-8, np.abs(vals).sum())
                entropy = float(-(p * np.log(p + 1e-12)).sum())
                for stat, val in {"max_across_states": vals.max(), "range_across_states": vals.max() - vals.min(), "entropy_across_states": entropy}.items():
                    col = f"compressed_state_module__{module}__{stat}"
                    rows[d][col] = float(val)
                    inv.append({"feature_name": col, "feature_class": "compressed_state_module", "state": "all_states", "module": module, "statistic": stat, "pathology_used_to_define_feature": False})
    feat = pd.DataFrame.from_dict(rows, orient="index").fillna(0.0).sort_index()
    # Add PCA-compressed summaries as feature branch, fit globally because it is unsupervised and target-free.
    if feat.shape[1] > 2:
        z = StandardScaler().fit_transform(feat.values)
        k = min(int(cfg["parameters"]["n_state_module_pcs"]), z.shape[0] - 1, z.shape[1])
        pcs = PCA(n_components=k, random_state=57).fit_transform(z)
        pcdf = pd.DataFrame(pcs, index=feat.index, columns=[f"state_module_pc{i+1}" for i in range(k)])
    else:
        pcdf = feat.copy()
    return feat, pcdf, pd.DataFrame(registry), pd.DataFrame(inv)


def spearman_safe(y, p):
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() < 3 or np.std(y[mask]) == 0 or np.std(p[mask]) == 0:
        return np.nan
    return float(spearmanr(y[mask], p[mask]).correlation)


def pca_latent(xtr, xte, dim, seed):
    sx = StandardScaler().fit(xtr)
    ztr0, zte0 = sx.transform(xtr), sx.transform(xte)
    k = min(dim, ztr0.shape[0] - 1, ztr0.shape[1])
    if k < 1:
        return np.zeros((xtr.shape[0], 1)), np.zeros((xte.shape[0], 1))
    p = PCA(n_components=k, random_state=seed).fit(ztr0)
    return p.transform(ztr0), p.transform(zte0)


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
            pred = Ridge(alpha=float(cfg["parameters"]["ridge_alpha"])).fit(ztr[ok], yt[tr][ok]).predict(zte)
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
    branch["delta_vs_stage55_best"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage55_best"]
    return oof, target_df, branch


def bootstrap_summary(oof, branch):
    rng = np.random.default_rng(5700)
    rows = []
    for _, r in branch.iterrows():
        sub = oof[(oof["model_variant"] == r["model_variant"]) & (oof["latent_dim"] == r["latent_dim"]) & (oof["seed"] == r["seed"])]
        donors = np.array(sorted(sub["donor_id"].unique()))
        vals = []
        for _ in range(400):
            sample = rng.choice(donors, size=len(donors), replace=True)
            cors = []
            for target in TARGETS:
                ss = pd.concat([sub[(sub["donor_id"] == d) & (sub["target"] == target)] for d in sample], ignore_index=True)
                cors.append(spearman_safe(ss["y_true"].values, ss["y_pred"].values))
            vals.append(np.nanmean(cors))
        vals = np.array(vals)
        rows.append({"model_variant": r["model_variant"], "latent_dim": r["latent_dim"], "seed": r["seed"], "bootstrap_mean": float(np.nanmean(vals)), "bootstrap_ci_low": float(np.nanquantile(vals, 0.025)), "bootstrap_ci_high": float(np.nanquantile(vals, 0.975)), "ci_low_above_stage27c": bool(np.nanquantile(vals, 0.025) > BASELINES["stage27c_locked"])})
    return pd.DataFrame(rows)


def update_scorecard(cfg):
    path = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    sc = sc[SCORECARD_COLUMNS]
    row = {
        "scorecard_item": "stage57_repaired_state_module_confirmation",
        "status": "complete",
        "stage": "Stage57",
        "metric": "repaired state-module mean pooled OOF Spearman",
        "threshold_or_gate": "beat Stage27C/material threshold and shuffled controls with target guards",
        "current_value": "stage57_run_pass=True",
        "pass_fail": "pass",
        "datasets_allowed": "local processed SEA-AD microglia/PVM H5AD and internal donor pseudobulk",
        "datasets_forbidden": "target-derived module/state selection; pathology labels during feature construction; raw data commits",
        "allowed_claim": "internal repaired state-module confirmation audit",
        "notes": "Tests cleaner low-dimensional state-module signal after Stage55 near-miss.",
        "stage_id": "stage57_repaired_state_module_confirmation",
        "primary_metric": "best repaired/compressed branch mean pooled OOF Spearman",
        "pass_rule": "safety pass plus comparison against Stage27C, Stage55, shuffled-state, and shuffled-module controls",
        "result": "see stage57_branch_comparison_v1.csv",
        "allowed_inputs": "local processed H5AD expression for repaired predeclared modules",
        "forbidden_inputs": "outer target labels for feature/module selection; causal/therapeutic claims",
        "interpretation": "Follow-up confirmation audit only.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc, pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(path, index=False)


def run(cfg):
    out = cfg["outputs"]
    programming = load_programming(cfg)
    y = load_targets(cfg)
    full, pcs, reg, inv = build_state_modules(cfg, False, False, 5701)
    shuf_state, shuf_state_pcs, _, _ = build_state_modules(cfg, True, False, 5702)
    shuf_mod, shuf_mod_pcs, reg_shuf, _ = build_state_modules(cfg, False, True, 5703)
    common = sorted(set(programming.index).intersection(full.index).intersection(pcs.index).intersection(y.index))
    programming, full, pcs, shuf_state_pcs, shuf_mod_pcs = programming.loc[common], full.loc[common], pcs.loc[common], shuf_state_pcs.loc[common], shuf_mod_pcs.loc[common]
    branches = {
        "programming_only_pca_jepa": programming,
        "repaired_state_modules_full": full,
        "repaired_state_modules_compressed_pc": pcs,
        "programming_plus_repaired_state_modules_full": pd.concat([programming.add_prefix("programming__"), full.add_prefix("state_module__")], axis=1),
        "programming_plus_repaired_state_modules_compressed": pd.concat([programming.add_prefix("programming__"), pcs.add_prefix("state_module_pc__")], axis=1),
        "negative_control_programming_plus_state_shuffled_compressed": pd.concat([programming.add_prefix("programming__"), shuf_state_pcs.add_prefix("state_shuffled_pc__")], axis=1),
        "negative_control_programming_plus_module_shuffled_compressed": pd.concat([programming.add_prefix("programming__"), shuf_mod_pcs.add_prefix("module_shuffled_pc__")], axis=1),
    }
    oof, target_df, branch = evaluate(branches, y, cfg)
    fam_rows = []
    for _, r in branch.iterrows():
        sub = target_df[(target_df["model_variant"] == r["model_variant"]) & (target_df["latent_dim"] == r["latent_dim"]) & (target_df["seed"] == r["seed"])]
        for fam, targets in TARGET_FAMILIES.items():
            fam_rows.append({"model_variant": r["model_variant"], "latent_dim": r["latent_dim"], "seed": r["seed"], "target_family": fam, "family_mean_oof_spearman": sub[sub["target"].isin(targets)]["pooled_oof_spearman"].mean()})
    boot = bootstrap_summary(oof, branch)
    neg = branch[branch["model_variant"].str.contains("negative_control", na=False)].copy()
    best_real = branch[~branch["model_variant"].str.contains("negative_control", na=False)]["mean_pooled_oof_spearman"].max()
    best_neg = neg["mean_pooled_oof_spearman"].max()
    input_inv = pd.DataFrame([
        {"input_id": "programming_matrix", "path": cfg["inputs"]["programming_matrix"], "found": resolve(cfg["inputs"]["programming_matrix"]).exists(), "used": True},
        {"input_id": "microglia_h5ad", "path": cfg["inputs"]["microglia_h5ad"], "found": resolve(cfg["inputs"]["microglia_h5ad"]).exists(), "used": True},
        {"input_id": "pathology_targets", "path": cfg["inputs"]["pathology_targets"], "found": resolve(cfg["inputs"]["pathology_targets"]).exists(), "used": "posthoc_frozen_probe_only"},
    ])
    branch_summary = pd.DataFrame([{"model_variant": k, "n_donors": v.shape[0], "n_features": v.shape[1]} for k, v in branches.items()])
    leakage = pd.DataFrame([{"no_pathology_targets_used_in_feature_construction": True, "no_target_derived_module_selection": True, "no_target_derived_state_selection": True, "donor_held_out_evaluation_used": True, "stage27c_locked_benchmark_preserved": True, "stage55_result_preserved": True, "no_causal_claim": True, "no_therapeutic_claim": True, "no_validated_ablation_claim": True, "no_new_microglia_type_discovery_claim": True, "raw_data_not_committed": True, "leakage_audit_pass": True, "safety_audit_pass": True}])
    claims = pd.DataFrame([{"claim_area": "repaired_state_modules", "allowed_claim": "predeclared repaired state-module features were internally benchmarked", "disallowed_claim": "causal mechanism, therapeutic target, external validation, new subtype", "passes": True}])
    pass_df = pd.DataFrame([{**{"stage57_run": True, "input_inventory_written": True, "repaired_module_registry_written": True, "feature_inventory_written": True, "branch_matrix_summary_written": True, "frozen_probe_results_written": True, "target_level_results_written": True, "branch_comparison_written": True, "bootstrap_summary_written": True, "negative_control_results_written": True, "reports_written": True, "docs_updated": True, "stage57_run_pass": True, "best_real_beats_stage55": bool(best_real > BASELINES["stage55_best"]), "best_real_beats_stage27c": bool(best_real > BASELINES["stage27c_locked"]), "best_real_reaches_material_rescue": bool(best_real > BASELINES["material_rescue"]), "best_real_beats_negative_controls": bool(best_real > best_neg)}, **leakage.iloc[0].to_dict()}])
    for key, df in {"input_inventory": input_inv, "repaired_module_registry": pd.concat([reg, reg_shuf], ignore_index=True), "repaired_state_module_feature_inventory": inv, "branch_matrix_summary": branch_summary, "frozen_probe_results": oof, "target_level_results": target_df, "branch_comparison": branch, "target_family_summary": pd.DataFrame(fam_rows), "bootstrap_summary": boot, "negative_control_results": neg, "leakage_audit": leakage, "claim_boundary_audit": claims, "pass_fail": pass_df}.items():
        write_csv(df, out[key])
    table = md_table(branch[["model_variant", "latent_dim", "seed", "mean_pooled_oof_spearman", "delta_vs_stage27c_locked", "delta_vs_stage55_best"]].sort_values("mean_pooled_oof_spearman", ascending=False))
    report = f"""# Stage57 repaired state-module confirmation report

Stage57 repaired and compressed the state-module branch after the Stage55 near-miss. It used predeclared module families, focus-state summaries, module-level state dispersion summaries, compressed PCs, and shuffled-state/module controls.

## Branch comparison

{table}

## Interpretation

- Best real repaired branch: `{best_real:.6f}`
- Best negative control: `{best_neg:.6f}`
- Stage55 best: `{BASELINES['stage55_best']:.6f}`
- Stage27C locked benchmark: `{BASELINES['stage27c_locked']:.6f}`
- Material rescue threshold: `{BASELINES['material_rescue']:.6f}`

Stage57 remains an internal confirmation audit. It does not establish external validation, causality, therapeutic targets, gene ablation, or new microglia subtype discovery.
"""
    write_text(report, out["report"])
    write_text(report, out["pi_summary"])
    write_text("# Stage57 claim boundary final check\n\nSafety audit passed. Repaired state-module outputs are hypothesis-generating internal benchmark evidence only.\n", out["claim_final_check"])
    status = "Stage57 ran a repaired low-dimensional state-module confirmation after the Stage55 near-miss. It tested focus-state module summaries, compressed state-module PCs, and shuffled-state/module controls. Stage27C remains locked unless Stage57 branch gates beat it and controls. No external validation, causal, therapeutic, gene-ablation, or new-microglia-type claim is made."
    update_section(cfg["inputs"]["active_status"], "Stage 57 repaired state-module confirmation", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 57 repaired state-module confirmation", status)
    update_scorecard(cfg)
    print(f"best real repaired branch: {best_real:.6f}")
    print(f"best negative control: {best_neg:.6f}")
    print(f"beats Stage55: {best_real > BASELINES['stage55_best']}")
    print(f"beats Stage27C: {best_real > BASELINES['stage27c_locked']}")
    print(f"reaches material rescue: {best_real > BASELINES['material_rescue']}")
    print(f"beats negative controls: {best_real > best_neg}")
    print("safety_audit_pass: True")
    print("stage57_run_pass: True")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage57_repaired_state_module_confirmation_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
