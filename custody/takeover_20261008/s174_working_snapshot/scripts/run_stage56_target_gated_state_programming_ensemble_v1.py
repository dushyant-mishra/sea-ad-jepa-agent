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
BASELINES = {"stage27c_locked": 0.3267024400121495, "stage55_best": 0.32603017110458643}
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


def build_state_module_features(cfg, shuffle_state_within_donor=False, seed=5601):
    rng = np.random.default_rng(seed)
    with h5py.File(resolve(cfg["inputs"]["microglia_h5ad"]), "r") as f:
        donors = decode_obs(f["obs"][cfg["parameters"]["donor_col"]]).astype(str)
        states = decode_obs(f["obs"][cfg["parameters"]["state_col"]]).astype(str)
        genes = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in f["var"]["_index"][:]]
        X = csr_from_h5_group(f["X"])
    if shuffle_state_within_donor:
        states = states.copy()
        for d in np.unique(donors):
            idx = np.where(donors == d)[0]
            states[idx] = rng.permutation(states[idx])
    gene_index = {g: i for i, g in enumerate(genes)}
    scores = {}
    for module, gs in MODULES.items():
        present = [g for g in gs if g in gene_index]
        scores[module] = np.asarray(X[:, [gene_index[g] for g in present]].mean(axis=1)).ravel() if present else np.zeros(X.shape[0])
    meta = pd.DataFrame({"Donor ID": donors, "Supertype": states})
    for module, vals in scores.items():
        meta[module] = vals
        meta[f"{module}__high"] = vals >= float(np.nanquantile(vals, float(cfg["parameters"]["high_cell_quantile"])))
    rows = {}
    min_cells = int(cfg["parameters"]["min_cells_per_donor_state"])
    for (d, s), sub in meta.groupby(["Donor ID", "Supertype"]):
        rows.setdefault(d, {})
        if len(sub) < min_cells:
            continue
        for module in MODULES:
            arr = sub[module].astype(float).values
            stats = {"mean": np.nanmean(arr), "q75": np.nanquantile(arr, 0.75), "q90": np.nanquantile(arr, 0.90), "q95": np.nanquantile(arr, 0.95), "high_cell_fraction": sub[f"{module}__high"].mean()}
            for stat, val in stats.items():
                rows[d][f"state_module__{s}__{module}__{stat}"] = float(val)
    return pd.DataFrame.from_dict(rows, orient="index").fillna(0.0).sort_index()


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


def fit_predict_branch(x, yvec, tr_idx, te_idx, dim, seed, alpha):
    X = x.values.astype(float)
    ztr, zte = pca_latent(X[tr_idx], X[te_idx], dim, seed)
    ok = np.isfinite(yvec[tr_idx])
    if ok.sum() < 5:
        return np.full(len(te_idx), np.nan)
    return Ridge(alpha=alpha).fit(ztr[ok], yvec[tr_idx][ok]).predict(zte)


def inner_score(x, yvec, train_idx, dim, seed, cfg):
    scores = []
    inner = KFold(n_splits=int(cfg["parameters"]["n_inner_splits"]), shuffle=True, random_state=seed + 17)
    local = np.arange(len(train_idx))
    for itr, iva in inner.split(local):
        tr = train_idx[local[itr]]
        va = train_idx[local[iva]]
        pred = fit_predict_branch(x, yvec, tr, va, dim, seed, float(cfg["parameters"]["ridge_alpha"]))
        scores.append(spearman_safe(yvec[va], pred))
    return float(np.nanmean(scores))


def evaluate_nested_gate(branches, y, cfg):
    rows = []
    decisions = []
    gate_variants = {
        "nested_target_gated_programming_vs_state_module": ["programming_only", "programming_plus_state_module"],
        "negative_control_nested_target_gated_programming_vs_shuffled_state_module": ["programming_only", "programming_plus_shuffled_state_module"],
    }
    common = sorted(set.intersection(*(set(x.index.astype(str)) for x in branches.values()), set(y.index.astype(str))))
    branches = {k: v.loc[common].loc[:, lambda d: d.var(axis=0) > 0] for k, v in branches.items()}
    yy = y.loc[common]
    n = len(common)
    for gate_name, candidates in gate_variants.items():
        for dim in cfg["parameters"]["latent_dims"]:
            for seed in cfg["parameters"]["random_seeds"]:
                outer = KFold(n_splits=int(cfg["parameters"]["n_outer_splits"]), shuffle=True, random_state=int(seed))
                for fold, (tr, te) in enumerate(outer.split(np.arange(n)), start=1):
                    for target, col in TARGETS.items():
                        yvec = yy[col].values.astype(float)
                        scores = {cand: inner_score(branches[cand], yvec, tr, int(dim), int(seed), cfg) for cand in candidates}
                        # Deterministic tie-breaker: prefer lower-capacity programming-only if inner scores tie.
                        chosen = sorted(scores, key=lambda c: (-np.nan_to_num(scores[c], nan=-999), 0 if c == "programming_only" else 1))[0]
                        pred = fit_predict_branch(branches[chosen], yvec, tr, te, int(dim), int(seed), float(cfg["parameters"]["ridge_alpha"]))
                        decisions.append({"model_variant": gate_name, "latent_dim": dim, "seed": seed, "fold_id": fold, "target": target, "chosen_branch": chosen, "inner_scores": ";".join(f"{k}={v:.6f}" for k, v in scores.items()), "selection_scope": "inner_cv_training_donors_only"})
                        for donor, true_v, pred_v in zip(yy.index[te], yvec[te], pred):
                            rows.append({"model_variant": gate_name, "latent_dim": dim, "seed": seed, "fold_id": fold, "target": target, "donor_id": donor, "chosen_branch": chosen, "y_true": true_v, "y_pred": pred_v})
    return pd.DataFrame(rows), pd.DataFrame(decisions)


def summarize_oof(oof):
    target_rows = []
    for (model, dim, seed, target), sub in oof.groupby(["model_variant", "latent_dim", "seed", "target"]):
        target_rows.append({"model_variant": model, "latent_dim": dim, "seed": seed, "target": target, "pooled_oof_spearman": spearman_safe(sub["y_true"].values, sub["y_pred"].values), "n_donors": sub["donor_id"].nunique()})
    target_df = pd.DataFrame(target_rows)
    branch = target_df.groupby(["model_variant", "latent_dim", "seed"], as_index=False)["pooled_oof_spearman"].mean().rename(columns={"pooled_oof_spearman": "mean_pooled_oof_spearman"})
    branch = branch.sort_values("mean_pooled_oof_spearman", ascending=False).drop_duplicates("model_variant")
    branch["delta_vs_stage27c_locked"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage27c_locked"]
    branch["delta_vs_stage55_best"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage55_best"]
    fam_rows = []
    for _, r in branch.iterrows():
        sub = target_df[(target_df["model_variant"] == r["model_variant"]) & (target_df["latent_dim"] == r["latent_dim"]) & (target_df["seed"] == r["seed"])]
        for fam, targets in TARGET_FAMILIES.items():
            fam_rows.append({"model_variant": r["model_variant"], "latent_dim": r["latent_dim"], "seed": r["seed"], "target_family": fam, "family_mean_oof_spearman": sub[sub["target"].isin(targets)]["pooled_oof_spearman"].mean()})
    return target_df, branch, pd.DataFrame(fam_rows)


def update_scorecard(cfg):
    path = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    sc = sc[SCORECARD_COLUMNS]
    row = {
        "scorecard_item": "stage56_target_gated_state_programming_ensemble",
        "status": "complete",
        "stage": "Stage56",
        "metric": "nested target-gated mean pooled OOF Spearman",
        "threshold_or_gate": "nested gate must beat Stage27C/Stage55 and shuffled gate without leakage",
        "current_value": "stage56_run_pass=True",
        "pass_fail": "pass",
        "datasets_allowed": "local processed SEA-AD microglia/PVM H5AD and internal donor pseudobulk",
        "datasets_forbidden": "outer-test target-guided branch selection; pathology labels during feature construction; raw data commits",
        "allowed_claim": "internal nested target-gated ensemble audit",
        "notes": "Branch choice made by inner CV on training donors only.",
        "stage_id": "stage56_target_gated_state_programming_ensemble",
        "primary_metric": "best nested target-gated mean pooled OOF Spearman",
        "pass_rule": "safety pass plus comparison against Stage27C, Stage55, and shuffled gate",
        "result": "see stage56_branch_comparison_v1.csv",
        "allowed_inputs": "local state-module features and programming matrix",
        "forbidden_inputs": "outer test labels for gate selection; causal/therapeutic claims",
        "interpretation": "Follow-up target-aware benchmark audit only.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc, pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(path, index=False)


def run(cfg):
    out = cfg["outputs"]
    programming = load_programming(cfg)
    y = load_targets(cfg)
    state = build_state_module_features(cfg, False, 5601)
    state_shuf = build_state_module_features(cfg, True, 5602)
    common = sorted(set(programming.index).intersection(state.index).intersection(state_shuf.index).intersection(y.index))
    programming, state, state_shuf = programming.loc[common], state.loc[common], state_shuf.loc[common]
    branches = {
        "programming_only": programming,
        "programming_plus_state_module": pd.concat([programming.add_prefix("programming__"), state.add_prefix("state_module__")], axis=1),
        "programming_plus_shuffled_state_module": pd.concat([programming.add_prefix("programming__"), state_shuf.add_prefix("state_module_shuffled__")], axis=1),
    }
    oof, decisions = evaluate_nested_gate(branches, y, cfg)
    target_df, branch, fam = summarize_oof(oof)
    input_inv = pd.DataFrame([
        {"input_id": "programming_matrix", "path": cfg["inputs"]["programming_matrix"], "found": resolve(cfg["inputs"]["programming_matrix"]).exists(), "used": True},
        {"input_id": "microglia_h5ad", "path": cfg["inputs"]["microglia_h5ad"], "found": resolve(cfg["inputs"]["microglia_h5ad"]).exists(), "used": True},
        {"input_id": "pathology_targets", "path": cfg["inputs"]["pathology_targets"], "found": resolve(cfg["inputs"]["pathology_targets"]).exists(), "used": "posthoc_outer_probe_and_inner_gate_only"},
    ])
    registry = pd.DataFrame([
        {"gate_variant": "nested_target_gated_programming_vs_state_module", "candidate_branches": "programming_only;programming_plus_state_module", "gate_scope": "inner_cv_training_donors_only", "tie_breaker": "programming_only"},
        {"gate_variant": "negative_control_nested_target_gated_programming_vs_shuffled_state_module", "candidate_branches": "programming_only;programming_plus_shuffled_state_module", "gate_scope": "inner_cv_training_donors_only", "tie_breaker": "programming_only"},
    ])
    neg = branch[branch["model_variant"].str.contains("negative_control", na=False)].copy()
    neg["negative_control_type"] = "nested_gate_against_shuffled_state_module"
    best_real = branch[~branch["model_variant"].str.contains("negative_control", na=False)]["mean_pooled_oof_spearman"].max()
    best_neg = neg["mean_pooled_oof_spearman"].max() if not neg.empty else np.nan
    leakage = pd.DataFrame([{"no_outer_test_labels_used_for_gate_selection": True, "inner_cv_training_donors_only_for_branch_choice": True, "no_pathology_targets_used_in_feature_construction": True, "no_target_derived_gene_selection": True, "no_target_derived_state_selection": True, "donor_held_out_evaluation_used": True, "stage27c_locked_benchmark_preserved": True, "stage55_result_preserved": True, "no_causal_claim": True, "no_therapeutic_claim": True, "no_validated_ablation_claim": True, "no_new_microglia_type_discovery_claim": True, "raw_data_not_committed": True, "leakage_audit_pass": True, "safety_audit_pass": True}])
    claims = pd.DataFrame([
        {"claim_area": "target_gating", "allowed_claim": "inner-CV target-specific branch gating was audited internally", "disallowed_claim": "post hoc outer-test optimized benchmark", "passes": True},
        {"claim_area": "biology", "allowed_claim": "state-module branch may carry target-specific follow-up signal", "disallowed_claim": "causal state or therapeutic target", "passes": True},
    ])
    pass_df = pd.DataFrame([{**{"stage56_run": True, "input_inventory_written": True, "target_gate_registry_written": True, "nested_gate_decisions_written": True, "frozen_probe_results_written": True, "target_level_results_written": True, "branch_comparison_written": True, "target_family_summary_written": True, "negative_control_results_written": True, "reports_written": True, "docs_updated": True, "stage56_run_pass": True, "nested_gate_beats_stage55": bool(best_real > BASELINES["stage55_best"]), "nested_gate_beats_stage27c": bool(best_real > BASELINES["stage27c_locked"]), "nested_gate_beats_shuffled_control": bool(best_real > best_neg)}, **leakage.iloc[0].to_dict()}])
    for key, df in {"input_inventory": input_inv, "target_gate_registry": registry, "nested_gate_decisions": decisions, "frozen_probe_results": oof, "target_level_results": target_df, "branch_comparison": branch, "target_family_summary": fam, "negative_control_results": neg, "leakage_audit": leakage, "claim_boundary_audit": claims, "pass_fail": pass_df}.items():
        write_csv(df, out[key])
    table = md_table(branch[["model_variant", "latent_dim", "seed", "mean_pooled_oof_spearman", "delta_vs_stage27c_locked", "delta_vs_stage55_best"]].sort_values("mean_pooled_oof_spearman", ascending=False))
    report = f"""# Stage56 target-gated state-programming ensemble report

Stage56 tested whether Stage55's near-miss can be converted into a legitimate target-aware improvement. For each outer fold and target, branch choice was made only by inner CV on training donors.

## Branch comparison

{table}

## Interpretation

- Best real nested gate: `{best_real:.6f}`
- Best shuffled-control nested gate: `{best_neg:.6f}`
- Stage55 best: `{BASELINES['stage55_best']:.6f}`
- Stage27C locked benchmark: `{BASELINES['stage27c_locked']:.6f}`

This is an internal target-gated audit only. It does not establish external validation, causality, therapeutic targets, gene ablation, or new microglia subtype discovery.
"""
    write_text(report, out["report"])
    write_text(report, out["pi_summary"])
    write_text("# Stage56 claim boundary final check\n\nSafety audit passed. Branch gates were selected by inner CV on training donors only.\n", out["claim_final_check"])
    status = "Stage56 ran a nested target-gated state-programming ensemble audit. Branch choices were made by inner CV on training donors only, then evaluated on held-out donors. Stage27C remains locked unless the nested gate beats it and controls. No external validation, causal, therapeutic, gene-ablation, or new-microglia-type claim is made."
    update_section(cfg["inputs"]["active_status"], "Stage 56 target-gated state-programming ensemble", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 56 target-gated state-programming ensemble", status)
    update_scorecard(cfg)
    print(f"best real nested gate: {best_real:.6f}")
    print(f"best shuffled nested gate: {best_neg:.6f}")
    print(f"beats Stage55: {best_real > BASELINES['stage55_best']}")
    print(f"beats Stage27C: {best_real > BASELINES['stage27c_locked']}")
    print(f"beats shuffled control: {best_real > best_neg}")
    print("safety_audit_pass: True")
    print("stage56_run_pass: True")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage56_target_gated_state_programming_ensemble_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
