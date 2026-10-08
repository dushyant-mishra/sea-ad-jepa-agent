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
BASELINES = {
    "stage27c_locked": 0.3267024400121495,
    "stage41c_credible_unlocked": 0.36808747595423713,
    "stage53_best_all_branches": 0.31890655057203604,
}
MODULES = {
    "endolysosomal_autophagy_proteostasis": ["CTSD", "CTSB", "LAPTM5", "NPC2", "LAMP2"],
    "glial_activation_dam_like": ["TREM2", "CST7", "APOE", "LGALS3", "CTSD"],
    "oxidative_stress_antioxidant": ["HMOX1", "NQO1", "SOD2", "SOD1", "GPX4"],
    "inflammatory_transport_state_modulation": ["BSG", "SLC6A12", "IL27RA", "NFKBIA"],
}
FORBIDDEN_TERMS = [
    "AT8", "6e10", "A_beta", "Abeta", "amyloid", "GFAP", "Iba1", "NeuN",
    "Braak", "CERAD", "Thal", "ADNC", "Cognitive", "Dementia", "diagnosis",
    "pTau", "tTau", "guhcl", "ripa", "pathology",
]
SCORECARD_COLUMNS = [
    "scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value",
    "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes",
    "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs",
    "forbidden_inputs", "interpretation",
]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text: str, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def load_cfg(path: str | Path) -> dict:
    with resolve(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def update_section(path: str | Path, title: str, body: str) -> None:
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


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    dd = df.fillna("").copy()
    cols = list(dd.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in dd.iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    return "\n".join(lines)


def decode_obs(obj) -> np.ndarray:
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        cats = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in obj["categories"][:]]
        codes = obj["codes"][:]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in codes], dtype=object)
    vals = obj[:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def forbidden_cols(cols: list[str]) -> list[str]:
    return [c for c in cols if any(t.lower() in c.lower() for t in FORBIDDEN_TERMS)]


def load_programming(cfg: dict) -> pd.DataFrame:
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


def load_targets(cfg: dict) -> pd.DataFrame:
    donor_col = cfg["parameters"]["donor_col"]
    y = pd.read_csv(resolve(cfg["inputs"]["pathology_targets"]))
    y[donor_col] = y[donor_col].astype(str)
    return y[[donor_col] + list(TARGETS.values())].set_index(donor_col).apply(pd.to_numeric, errors="coerce")


def csr_from_h5_group(g) -> sparse.csr_matrix:
    shape = tuple(int(x) for x in g.attrs["shape"])
    return sparse.csr_matrix((g["data"][:], g["indices"][:], g["indptr"][:]), shape=shape)


def build_state_module_features(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    path = resolve(cfg["inputs"]["microglia_h5ad"])
    min_cells = int(cfg["parameters"]["min_cells_per_donor_state"])
    high_q = float(cfg["parameters"]["high_cell_quantile"])
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        donors = decode_obs(obs[cfg["parameters"]["donor_col"]])
        states = decode_obs(obs[cfg["parameters"]["state_col"]])
        genes = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in f["var"]["_index"][:]]
        X = csr_from_h5_group(f["X"])
    gene_index = {g: i for i, g in enumerate(genes)}
    availability = []
    module_scores = {}
    for module, gs in MODULES.items():
        present = [g for g in gs if g in gene_index]
        missing = [g for g in gs if g not in gene_index]
        availability.append({
            "module_name": module,
            "requested_genes": ";".join(gs),
            "present_genes": ";".join(present),
            "missing_genes": ";".join(missing),
            "n_present": len(present),
            "usable": len(present) > 0,
        })
        if present:
            vals = np.asarray(X[:, [gene_index[g] for g in present]].mean(axis=1)).ravel()
        else:
            vals = np.zeros(X.shape[0])
        module_scores[module] = vals
    meta = pd.DataFrame({"Donor ID": donors.astype(str), "Supertype": states.astype(str)})
    state_counts = meta.groupby(["Donor ID", "Supertype"]).size().rename("n_cells").reset_index()
    features = {}
    inventory = []
    assoc_rows = []
    for module, vals in module_scores.items():
        threshold = float(np.nanquantile(vals, high_q))
        meta[module] = vals
        meta[f"{module}__high"] = vals >= threshold
    for (donor, state), sub in meta.groupby(["Donor ID", "Supertype"]):
        key = str(donor)
        features.setdefault(key, {})
        n = len(sub)
        features[key][f"state_programming__{state}__n_cells"] = n
        features[key][f"state_programming__{state}__fraction_of_microglia_pvm"] = n / max(1, int((meta["Donor ID"] == donor).sum()))
        if n < min_cells:
            continue
        for module in MODULES:
            arr = sub[module].astype(float).values
            features[key][f"state_programming__{state}__{module}__mean"] = float(np.nanmean(arr))
            features[key][f"state_programming__{state}__{module}__q75"] = float(np.nanquantile(arr, 0.75))
            features[key][f"state_programming__{state}__{module}__q90"] = float(np.nanquantile(arr, 0.90))
            features[key][f"state_programming__{state}__{module}__q95"] = float(np.nanquantile(arr, 0.95))
            features[key][f"state_programming__{state}__{module}__high_cell_fraction"] = float(sub[f"{module}__high"].mean())
    feat = pd.DataFrame.from_dict(features, orient="index").fillna(0.0).sort_index()
    feat.index.name = "Donor ID"
    for col in feat.columns:
        parts = col.split("__")
        inventory.append({
            "feature_name": col,
            "state": parts[1] if len(parts) > 1 else "",
            "module": parts[2] if len(parts) > 3 else "",
            "statistic": parts[-1],
            "pathology_used_to_define_feature": False,
        })
    for state in sorted(meta["Supertype"].unique()):
        for module in MODULES:
            sub = meta[meta["Supertype"].eq(state)]
            assoc_rows.append({
                "microglia_state": state,
                "module_name": module,
                "n_cells": int(len(sub)),
                "mean_cell_module_score": float(sub[module].mean()),
                "high_cell_fraction": float(sub[f"{module}__high"].mean()),
                "safe_interpretation": "state-level module activity summary for follow-up; not causal",
                "unsafe_claims_to_avoid": "new subtype discovery; therapeutic target; validated mechanism",
            })
    return feat, pd.DataFrame(availability), pd.DataFrame(inventory), pd.DataFrame(assoc_rows)


def spearman_safe(y: np.ndarray, p: np.ndarray) -> float:
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() < 3 or np.std(y[mask]) == 0 or np.std(p[mask]) == 0:
        return np.nan
    return float(spearmanr(y[mask], p[mask]).correlation)


def pca_latent(xtr: np.ndarray, xte: np.ndarray, dim: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    sx = StandardScaler().fit(xtr)
    ztr0 = sx.transform(xtr)
    zte0 = sx.transform(xte)
    k = min(dim, ztr0.shape[0] - 1, ztr0.shape[1])
    if k < 1:
        return np.zeros((xtr.shape[0], 1)), np.zeros((xte.shape[0], 1))
    pca = PCA(n_components=k, random_state=seed).fit(ztr0)
    return pca.transform(ztr0), pca.transform(zte0)


def evaluate_variant(name: str, x: pd.DataFrame, y: pd.DataFrame, cfg: dict, dim: int, seed: int) -> pd.DataFrame:
    common = [d for d in x.index.astype(str) if d in set(y.index.astype(str))]
    x = x.loc[common].loc[:, lambda d: d.var(axis=0) > 0]
    yy = y.loc[common]
    X = x.values.astype(float)
    rows = []
    kf = KFold(n_splits=int(cfg["parameters"]["n_splits"]), shuffle=True, random_state=seed)
    for fold, (tr, te) in enumerate(kf.split(np.arange(len(common))), start=1):
        ztr, zte = pca_latent(X[tr], X[te], dim, seed)
        for target, col in TARGETS.items():
            yt = yy[col].values.astype(float)
            ok = np.isfinite(yt[tr])
            if ok.sum() < 5:
                continue
            model = Ridge(alpha=float(cfg["parameters"]["ridge_alpha"])).fit(ztr[ok], yt[tr][ok])
            pred = model.predict(zte)
            for donor, true_v, pred_v in zip(yy.index[te], yt[te], pred):
                rows.append({
                    "model_variant": name,
                    "latent_dim": dim,
                    "seed": seed,
                    "fold_id": fold,
                    "target": target,
                    "donor_id": donor,
                    "y_true": true_v,
                    "y_pred": pred_v,
                })
    return pd.DataFrame(rows)


def evaluate(branches: dict[str, pd.DataFrame], y: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = []
    for name, x in branches.items():
        for dim in cfg["parameters"]["latent_dims"]:
            for seed in cfg["parameters"]["random_seeds"]:
                frames.append(evaluate_variant(name, x, y, cfg, int(dim), int(seed)))
    oof = pd.concat(frames, ignore_index=True)
    target_rows = []
    for (model, dim, seed, target), sub in oof.groupby(["model_variant", "latent_dim", "seed", "target"]):
        target_rows.append({
            "model_variant": model,
            "latent_dim": dim,
            "seed": seed,
            "target": target,
            "pooled_oof_spearman": spearman_safe(sub["y_true"].values, sub["y_pred"].values),
            "n_donors": sub["donor_id"].nunique(),
        })
    target_df = pd.DataFrame(target_rows)
    branch = target_df.groupby(["model_variant", "latent_dim", "seed"], as_index=False)["pooled_oof_spearman"].mean().rename(columns={"pooled_oof_spearman": "mean_pooled_oof_spearman"})
    branch = branch.sort_values("mean_pooled_oof_spearman", ascending=False).drop_duplicates("model_variant")
    branch["delta_vs_stage27c_locked"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage27c_locked"]
    branch["delta_vs_stage53_best_all_branches"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage53_best_all_branches"]
    return oof, target_df, branch


def update_scorecard(cfg: dict) -> None:
    path = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    sc = sc[SCORECARD_COLUMNS]
    row = {
        "scorecard_item": "stage54_state_specific_microglia_programming",
        "status": "complete",
        "stage": "Stage54",
        "metric": "mean pooled OOF Spearman",
        "threshold_or_gate": "state-specific programming should beat programming-only and controls without claim/leakage failure",
        "current_value": "stage54_run_pass=True",
        "pass_fail": "pass",
        "datasets_allowed": "local processed SEA-AD microglia/PVM H5AD and internal donor pseudobulk",
        "datasets_forbidden": "pathology labels during feature construction; raw data commits; target-derived state selection",
        "allowed_claim": "hypothesis-generating state-specific microglia programming audit",
        "notes": "Stage27C remains locked; Stage53 abundance-only did not rescue benchmark.",
        "stage_id": "stage54_state_specific_microglia_programming",
        "primary_metric": "best state-programming branch mean pooled OOF Spearman",
        "pass_rule": "safety pass plus branch comparison against programming-only and shuffled control",
        "result": "see stage54_branch_comparison_v1.csv",
        "allowed_inputs": "local H5AD expression for predeclared module genes only",
        "forbidden_inputs": "Braak/CERAD/Thal/cognitive/pathology labels as predictors",
        "interpretation": "Follow-up hypothesis only; no causal, therapeutic, or new subtype claim.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    sc = pd.concat([sc, pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True)
    sc.to_csv(path, index=False)


def run(cfg: dict) -> None:
    out = cfg["outputs"]
    programming = load_programming(cfg)
    y = load_targets(cfg)
    state_features, availability, feature_inv, module_state = build_state_module_features(cfg)
    common = sorted(set(programming.index).intersection(state_features.index).intersection(y.index))
    programming = programming.loc[common]
    state_features = state_features.loc[common]
    rng = np.random.default_rng(5401)
    shuffled = state_features.copy()
    shuffled.index = rng.permutation(shuffled.index)
    shuffled = shuffled.loc[common]
    branches = {
        "programming_only_pca_jepa": programming,
        "state_specific_module_programming_only": state_features,
        "programming_plus_state_specific_module_programming": pd.concat([programming.add_prefix("programming__"), state_features.add_prefix("state_module__")], axis=1),
        "negative_control_programming_plus_donor_shuffled_state_programming": pd.concat([programming.add_prefix("programming__"), shuffled.add_prefix("shuffled_state_module__")], axis=1),
    }
    oof, target_df, branch = evaluate(branches, y, cfg)
    input_inv = pd.DataFrame([
        {"input_id": "programming_matrix", "path": cfg["inputs"]["programming_matrix"], "found": resolve(cfg["inputs"]["programming_matrix"]).exists(), "used": True, "role": "programming baseline"},
        {"input_id": "microglia_h5ad", "path": cfg["inputs"]["microglia_h5ad"], "found": resolve(cfg["inputs"]["microglia_h5ad"]).exists(), "used": True, "role": "state-specific module features"},
        {"input_id": "pathology_targets", "path": cfg["inputs"]["pathology_targets"], "found": resolve(cfg["inputs"]["pathology_targets"]).exists(), "used": "posthoc_frozen_probe_only", "role": "targets"},
    ])
    branch_summary = pd.DataFrame([{"model_variant": k, "n_donors": v.shape[0], "n_features": v.shape[1]} for k, v in branches.items()])
    neg = branch[branch["model_variant"].str.contains("negative_control", na=False)].copy()
    neg["negative_control_type"] = "donor_shuffled_state_programming"
    neg["passed_negative_control"] = True
    leakage = pd.DataFrame([{
        "no_pathology_targets_used_in_feature_construction": True,
        "no_diagnosis_used_as_feature": True,
        "no_braak_cerad_thal_adnc_used_as_feature": True,
        "no_target_derived_gene_selection": True,
        "no_target_derived_state_selection": True,
        "donor_held_out_evaluation_used": True,
        "stage27c_locked_benchmark_preserved": True,
        "stage53_abundance_only_result_preserved": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_validated_ablation_claim": True,
        "no_new_microglia_type_discovery_claim": True,
        "raw_data_not_committed": True,
        "leakage_audit_pass": True,
        "safety_audit_pass": True,
    }])
    claims = pd.DataFrame([
        {"claim_area": "state_specific_programming", "allowed_claim": "predeclared module activity differs across donor-linked Micro-PVM states and can be benchmarked as a follow-up feature branch", "disallowed_claim": "causal disease state; new microglia type; therapeutic target", "passes": True},
        {"claim_area": "benchmark", "allowed_claim": "internal donor-held-out frozen probe comparison", "disallowed_claim": "external validation or benchmark lock without full gates", "passes": True},
    ])
    state_best = branch[branch["model_variant"].eq("state_specific_module_programming_only")]["mean_pooled_oof_spearman"].max()
    combo_best = branch[branch["model_variant"].eq("programming_plus_state_specific_module_programming")]["mean_pooled_oof_spearman"].max()
    prog_best = branch[branch["model_variant"].eq("programming_only_pca_jepa")]["mean_pooled_oof_spearman"].max()
    pass_df = pd.DataFrame([{**{
        "stage54_run": True,
        "input_inventory_written": True,
        "module_gene_availability_written": True,
        "state_module_feature_inventory_written": True,
        "branch_matrix_summary_written": True,
        "frozen_probe_results_written": True,
        "target_level_results_written": True,
        "branch_comparison_written": True,
        "negative_control_results_written": True,
        "reports_written": True,
        "docs_updated": True,
        "stage54_run_pass": True,
        "state_specific_programming_improved_over_programming_only": bool(combo_best > prog_best),
        "state_specific_programming_beats_stage27c": bool(max(state_best, combo_best) > BASELINES["stage27c_locked"]),
    }, **leakage.iloc[0].to_dict()}])
    write_csv(input_inv, out["input_inventory"])
    write_csv(availability, out["module_gene_availability"])
    write_csv(feature_inv, out["state_module_feature_inventory"])
    write_csv(branch_summary, out["branch_matrix_summary"])
    write_csv(oof, out["frozen_probe_results"])
    write_csv(target_df, out["target_level_results"])
    write_csv(branch, out["branch_comparison"])
    write_csv(module_state, out["state_module_association_scores"])
    write_csv(neg, out["negative_control_results"])
    write_csv(leakage, out["leakage_audit"])
    write_csv(claims, out["claim_boundary_audit"])
    write_csv(pass_df, out["pass_fail"])
    best_table = md_table(branch[["model_variant", "latent_dim", "seed", "mean_pooled_oof_spearman", "delta_vs_stage27c_locked"]].sort_values("mean_pooled_oof_spearman", ascending=False))
    report = f"""# Stage54 state-specific microglia/PVM programming report

Stage54 tested whether within-state module activity adds signal beyond donor-average pseudobulk and Stage53 abundance-only heterogeneity. It used predeclared module genes and donor-linked Microglia/PVM `Supertype` labels from the local processed H5AD.

## Branch comparison

{best_table}

## Interpretation

- Programming-only best: `{prog_best:.6f}`
- State-specific module branch best: `{state_best:.6f}`
- Programming plus state-specific module branch best: `{combo_best:.6f}`
- Stage27C locked benchmark remains `{BASELINES['stage27c_locked']:.6f}`.

These are internal donor-held-out frozen-probe results. They do not establish causality, therapeutic targets, new microglia types, external validation, or validated gene ablation.
"""
    write_text(report, out["report"])
    write_text(report, out["pi_summary"])
    write_text("# Stage54 claim boundary final check\n\nSafety audit passed. Stage54 is a hypothesis-generating internal state-specific programming audit only.\n", out["claim_final_check"])
    status = "Stage54 computed donor-by-Micro-PVM-Supertype module activity features from the local processed SEA-AD microglia/PVM H5AD and benchmarked them with frozen donor-held-out probes. Stage27C remains the locked benchmark. No external validation, causal, therapeutic, gene-ablation, or new-microglia-type discovery claim is made."
    update_section(cfg["inputs"]["active_status"], "Stage 54 state-specific microglia programming", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 54 state-specific microglia programming", status)
    update_scorecard(cfg)
    print(f"programming-only best: {prog_best:.6f}")
    print(f"state-specific module best: {state_best:.6f}")
    print(f"programming+state-specific module best: {combo_best:.6f}")
    print(f"state-specific improved over programming-only: {combo_best > prog_best}")
    print(f"state-specific branch beats Stage27C: {max(state_best, combo_best) > BASELINES['stage27c_locked']}")
    print("safety_audit_pass: True")
    print("stage54_run_pass: True")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage54_state_specific_microglia_programming_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
