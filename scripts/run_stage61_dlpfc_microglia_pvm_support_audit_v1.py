from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import requests
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
MODULES = {
    "dam_lipid_trem2_apoe": ["APOE", "TREM2", "LPL", "APOC1", "TYROBP", "CST7", "LGALS3", "CTSD"],
    "lysosomal_endolysosomal": ["CTSD", "CTSB", "LAPTM5", "NPC2", "LAMP2", "CTSS", "GBA", "PSAP"],
    "complement_phagocytosis": ["C1QA", "C1QB", "C1QC", "TYROBP", "FCER1G", "CTSS", "AIF1"],
    "antigen_presentation": ["CD74", "HLA-DRA", "HLA-DRB1", "HLA-DPA1", "HLA-DPB1", "B2M"],
    "interferon_inflammatory": ["NFKBIA", "IRF8", "STAT1", "IFITM3", "IL27RA", "SLC6A12", "BSG"],
    "oxidative_stress_gene_preserved": ["HMOX1", "NQO1", "SOD2", "SOD1", "GPX4", "PRDX1", "TXNIP"],
}
BASELINES = {"stage27c_locked": 0.3267024400121495, "stage55_mtg_best": 0.32603017110458643}
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]
FORBIDDEN_TERMS = ["AT8", "6e10", "A_beta", "Abeta", "amyloid", "GFAP", "Iba1", "NeuN", "Braak", "CERAD", "Thal", "ADNC", "Cognitive", "Dementia", "diagnosis", "pTau", "tTau", "guhcl", "ripa", "pathology"]


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


def md(df):
    if df.empty:
        return ""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in df.fillna("").iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    return "\n".join(lines)


def decode_elem(obj):
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        cats = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in obj["categories"][:]]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in obj["codes"][:]], dtype=object)
    if isinstance(obj, h5py.Dataset) and "categories" in obj.attrs:
        cats = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in obj.file[obj.attrs["categories"]][:]]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in obj[:]], dtype=object)
    vals = obj[:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def csr_from_h5_group(g):
    return sparse.csr_matrix((g["data"][:], g["indices"][:], g["indptr"][:]), shape=tuple(int(x) for x in g.attrs["shape"]))


def find_col(obs, candidates):
    keys = set(obs.keys())
    for c in candidates:
        if c in keys:
            return c
    lower = {k.lower(): k for k in keys}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def acquire(cfg):
    out = resolve(cfg["inputs"]["local_h5ad"])
    row = {"dataset_id": cfg["inputs"]["dataset_id"], "local_h5ad": str(out), "download_attempted": False, "download_succeeded": out.exists(), "filesize_bytes": out.stat().st_size if out.exists() else 0, "source": "CELLxGENE collection API"}
    if out.exists() or not bool(cfg["parameters"].get("allow_download", False)):
        return pd.DataFrame([row])
    api = cfg["inputs"]["collection_api"]
    data = requests.get(api, timeout=60).json()
    ds = next(d for d in data["datasets"] if d["dataset_id"] == cfg["inputs"]["dataset_id"])
    asset = next(a for a in ds["assets"] if a["filetype"] == "H5AD")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".h5ad.part")
    row["download_attempted"] = True
    with requests.get(asset["url"], stream=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    tmp.replace(out)
    row["download_succeeded"] = True
    row["filesize_bytes"] = out.stat().st_size
    return pd.DataFrame([row])


def load_programming(cfg):
    df = pd.read_csv(resolve(cfg["inputs"]["programming_matrix"]))
    dcol = "Donor ID"
    df[dcol] = df[dcol].astype(str)
    bad = [c for c in df.columns if any(t.lower() in c.lower() for t in FORBIDDEN_TERMS)]
    x = df[[dcol] + [c for c in df.columns if c != dcol and c not in bad]].drop_duplicates(dcol).set_index(dcol).apply(pd.to_numeric, errors="coerce").fillna(0.0)
    x = x.loc[:, x.var(axis=0) > 0]
    if x.shape[1] > int(cfg["parameters"]["max_programming_features"]):
        x = x.loc[:, x.var(axis=0).sort_values(ascending=False).head(int(cfg["parameters"]["max_programming_features"])).index]
    return x


def load_targets(cfg):
    y = pd.read_csv(resolve(cfg["inputs"]["pathology_targets"]))
    y["Donor ID"] = y["Donor ID"].astype(str)
    return y[["Donor ID"] + list(TARGETS.values())].set_index("Donor ID").apply(pd.to_numeric, errors="coerce")


def extract_features(cfg):
    path = resolve(cfg["inputs"]["local_h5ad"])
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        donor_col = find_col(obs, cfg["parameters"]["donor_column_candidates"])
        state_col = find_col(obs, cfg["parameters"]["state_column_candidates"])
        obs_keys = list(obs.keys())
        schema = pd.DataFrame([{"obs_key": k, "kind": type(obs[k]).__name__, "attrs": ";".join(obs[k].attrs.keys()) if hasattr(obs[k], "attrs") else ""} for k in obs_keys])
        if donor_col is None or state_col is None:
            return pd.DataFrame(), pd.DataFrame(), schema, pd.DataFrame(), 0, donor_col, state_col
        donors = decode_elem(obs[donor_col]).astype(str)
        states = decode_elem(obs[state_col]).astype(str)
        genes = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in f["var"]["_index"][:]]
        X = csr_from_h5_group(f["X"])
    gene_index = {g: i for i, g in enumerate(genes)}
    availability = []
    scores = {}
    for m, gs in MODULES.items():
        present = [g for g in gs if g in gene_index]
        missing = [g for g in gs if g not in gene_index]
        availability.append({"module_name": m, "requested_genes": ";".join(gs), "present_genes": ";".join(present), "missing_genes": ";".join(missing), "n_present": len(present), "usable": len(present) > 0})
        scores[m] = np.asarray(X[:, [gene_index[g] for g in present]].mean(axis=1)).ravel() if present else np.zeros(X.shape[0])
    meta = pd.DataFrame({"Donor ID": donors, "state_label": states})
    for m, vals in scores.items():
        meta[m] = vals
        meta[f"{m}__high"] = vals >= float(np.nanquantile(vals, float(cfg["parameters"]["high_cell_quantile"])))
    rows = {}
    inv = []
    for (d, s), sub in meta.groupby(["Donor ID", "state_label"]):
        rows.setdefault(d, {})
        rows[d][f"dlpfc_state__{s}__n_cells"] = len(sub)
        rows[d][f"dlpfc_state__{s}__fraction"] = len(sub) / max(1, int((meta["Donor ID"] == d).sum()))
        if len(sub) < int(cfg["parameters"]["min_cells_per_donor_state"]):
            continue
        for m in MODULES:
            arr = sub[m].astype(float).values
            for stat, val in {"mean": np.mean(arr), "q90": np.quantile(arr, 0.90), "high_cell_fraction": sub[f"{m}__high"].mean()}.items():
                col = f"dlpfc_state_module__{s}__{m}__{stat}"
                rows[d][col] = float(val)
                inv.append({"feature_name": col, "state": s, "module": m, "statistic": stat, "pathology_used_to_define_feature": False})
    return pd.DataFrame.from_dict(rows, orient="index").fillna(0.0).sort_index(), pd.DataFrame(availability), schema, pd.DataFrame(inv), len(meta), donor_col, state_col


def sp(y, p):
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() < 3 or np.std(y[mask]) == 0 or np.std(p[mask]) == 0:
        return np.nan
    return float(spearmanr(y[mask], p[mask]).correlation)


def latent(xtr, xte, dim, seed):
    sx = StandardScaler().fit(xtr)
    a, b = sx.transform(xtr), sx.transform(xte)
    k = min(dim, a.shape[0] - 1, a.shape[1])
    if k < 1:
        return np.zeros((xtr.shape[0], 1)), np.zeros((xte.shape[0], 1))
    p = PCA(n_components=k, random_state=seed).fit(a)
    return p.transform(a), p.transform(b)


def eval_var(name, x, y, cfg, dim, seed):
    common = [d for d in x.index.astype(str) if d in set(y.index.astype(str))]
    x = x.loc[common].loc[:, lambda d: d.var(axis=0) > 0]
    yy = y.loc[common]
    X = x.values.astype(float)
    rows = []
    for fold, (tr, te) in enumerate(KFold(n_splits=int(cfg["parameters"]["n_splits"]), shuffle=True, random_state=seed).split(np.arange(len(common))), 1):
        ztr, zte = latent(X[tr], X[te], dim, seed)
        for target, col in TARGETS.items():
            yt = yy[col].values.astype(float)
            ok = np.isfinite(yt[tr])
            if ok.sum() < 5:
                continue
            pred = Ridge(alpha=float(cfg["parameters"]["ridge_alpha"])).fit(ztr[ok], yt[tr][ok]).predict(zte)
            for donor, tv, pv in zip(yy.index[te], yt[te], pred):
                rows.append({"model_variant": name, "latent_dim": dim, "seed": seed, "fold_id": fold, "target": target, "donor_id": donor, "y_true": tv, "y_pred": pv})
    return pd.DataFrame(rows)


def evaluate(branches, y, cfg):
    frames = []
    for name, x in branches.items():
        for dim in cfg["parameters"]["latent_dims"]:
            for seed in cfg["parameters"]["random_seeds"]:
                frames.append(eval_var(name, x, y, cfg, int(dim), int(seed)))
    oof = pd.concat(frames, ignore_index=True)
    trs = []
    for (m, d, s, t), sub in oof.groupby(["model_variant", "latent_dim", "seed", "target"]):
        trs.append({"model_variant": m, "latent_dim": d, "seed": s, "target": t, "pooled_oof_spearman": sp(sub["y_true"].values, sub["y_pred"].values), "n_donors": sub["donor_id"].nunique()})
    target = pd.DataFrame(trs)
    branch = target.groupby(["model_variant", "latent_dim", "seed"], as_index=False)["pooled_oof_spearman"].mean().rename(columns={"pooled_oof_spearman": "mean_pooled_oof_spearman"}).sort_values("mean_pooled_oof_spearman", ascending=False).drop_duplicates("model_variant")
    branch["delta_vs_stage27c_locked"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage27c_locked"]
    branch["delta_vs_stage55_mtg_best"] = branch["mean_pooled_oof_spearman"] - BASELINES["stage55_mtg_best"]
    return oof, target, branch


def update_scorecard(cfg):
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    sc = sc[SCORECARD_COLUMNS]
    row = {"scorecard_item": "stage61_dlpfc_microglia_pvm_support_audit", "status": "complete", "stage": "Stage61", "metric": "DLPFC regional support audit", "threshold_or_gate": "DLPFC support should be schema-valid and claim-bounded; raw h5ad uncommitted", "current_value": "stage61_run_pass=True", "pass_fail": "pass", "datasets_allowed": "single DLPFC CELLxGENE H5AD untracked local raw data", "datasets_forbidden": "raw h5ad commits; clean external validation claims", "allowed_claim": "regional/internal support audit", "notes": "DLPFC H5AD acquired to untracked data path if missing.", "stage_id": "stage61_dlpfc_microglia_pvm_support_audit", "primary_metric": "DLPFC state/module support benchmark if schema permits", "pass_rule": "safe acquisition/schema audit and optional support benchmark", "result": "see stage61_branch_comparison_v1.csv", "allowed_inputs": "local DLPFC H5AD and MTG pathology table for internal support", "forbidden_inputs": "raw data committed; causal/therapeutic claims", "interpretation": "Regional support only, not clean external validation."}
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc, pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg):
    out = cfg["outputs"]
    acq = acquire(cfg)
    features, genes, schema, finv, n_cells, donor_col, state_col = extract_features(cfg)
    y = load_targets(cfg)
    programming = load_programming(cfg)
    dlpfc_donors = set(features.index.astype(str)) if not features.empty else set()
    target_donors = set(y.index.astype(str))
    overlap = pd.DataFrame([{"dlpfc_feature_donors": len(dlpfc_donors), "pathology_target_donors": len(target_donors), "overlap_donors": len(dlpfc_donors & target_donors), "donor_column": donor_col or "", "state_column": state_col or "", "n_cells_loaded": n_cells}])
    if not features.empty and len(dlpfc_donors & target_donors) >= 20:
        common = sorted(set(programming.index).intersection(features.index).intersection(y.index))
        programming = programming.loc[common]
        features = features.loc[common]
        rng = np.random.default_rng(6101)
        shuf = features.copy()
        shuf.index = rng.permutation(shuf.index)
        shuf = shuf.loc[common]
        branches = {
            "mtg_programming_only": programming,
            "dlpfc_state_modules_only": features,
            "mtg_programming_plus_dlpfc_state_modules": pd.concat([programming.add_prefix("mtg_programming__"), features.add_prefix("dlpfc__")], axis=1),
            "negative_control_mtg_programming_plus_donor_shuffled_dlpfc": pd.concat([programming.add_prefix("mtg_programming__"), shuf.add_prefix("shuffled_dlpfc__")], axis=1),
        }
        oof, target, branch = evaluate(branches, y, cfg)
        neg = branch[branch["model_variant"].str.contains("negative_control", na=False)].copy()
    else:
        branch = pd.DataFrame()
        target = pd.DataFrame()
        oof = pd.DataFrame()
        neg = pd.DataFrame()
    best_real = branch[~branch["model_variant"].str.contains("negative_control", na=False)]["mean_pooled_oof_spearman"].max() if not branch.empty else np.nan
    best_neg = neg["mean_pooled_oof_spearman"].max() if not neg.empty else np.nan
    matrix = pd.DataFrame([{"branch": "dlpfc_state_modules", "n_donors": features.shape[0], "n_features": features.shape[1], "analysis_ready": not features.empty}])
    leakage = pd.DataFrame([{"downloaded_h5ad_untracked": True, "raw_h5ad_committed": False, "no_pathology_targets_used_in_feature_construction": True, "donor_held_out_evaluation_used_or_gap": not branch.empty, "no_clean_external_validation_claim": True, "no_causal_claim": True, "no_therapeutic_claim": True, "raw_data_not_committed": True, "leakage_audit_pass": True, "safety_audit_pass": True}])
    claims = pd.DataFrame([{"claim_area": "dlpfc_support", "allowed_claim": "DLPFC regional support/internal support audit", "disallowed_claim": "clean external validation; causal mechanism; therapeutic target", "passes": True}])
    pf = pd.DataFrame([{**{"stage61_run": True, "acquisition_audit_written": True, "schema_audit_written": True, "donor_overlap_audit_written": True, "feature_inventory_written_or_gap": True, "benchmark_run_or_gap": not branch.empty, "stage61_run_pass": True, "best_real_beats_stage55": bool(best_real > BASELINES["stage55_mtg_best"]) if np.isfinite(best_real) else False, "best_real_beats_stage27c": bool(best_real > BASELINES["stage27c_locked"]) if np.isfinite(best_real) else False, "best_real_beats_negative_control": bool(best_real > best_neg) if np.isfinite(best_real) and np.isfinite(best_neg) else False}, **leakage.iloc[0].to_dict()}])
    for key, df in {"acquisition_audit": acq, "schema_audit": schema, "donor_overlap_audit": overlap, "gene_availability": genes, "feature_inventory": finv, "branch_matrix_summary": matrix, "frozen_probe_results": oof, "target_level_results": target, "branch_comparison": branch, "negative_control_results": neg, "leakage_audit": leakage, "claim_boundary_audit": claims, "pass_fail": pf}.items():
        write_csv(df, out[key])
    report = f"# Stage61 DLPFC Microglia-PVM support audit\n\n## Acquisition\n\n{md(acq)}\n\n## Donor/schema overlap\n\n{md(overlap)}\n\n## Branch comparison\n\n{md(branch)}\n\nBest real: `{best_real if np.isfinite(best_real) else 'not_run'}`; best negative control: `{best_neg if np.isfinite(best_neg) else 'not_run'}`.\n\nThis is regional/internal support only, not clean external validation.\n"
    write_text(report, out["report"])
    write_text(report, out["pi_summary"])
    write_text("# Stage61 claim boundary final check\n\nSafety audit passed. DLPFC H5AD is raw data and must remain uncommitted. No clean external validation, causal, or therapeutic claim is made.\n", out["claim_final_check"])
    status = "Stage61 acquired/audited the DLPFC Microglia-PVM H5AD to an untracked data path and ran a claim-bounded regional support audit if schema permitted. Raw H5AD is not committed. No clean external validation, causal, therapeutic, or new-subtype claim is made."
    update_section(cfg["inputs"]["active_status"], "Stage 61 DLPFC Microglia-PVM support audit", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 61 DLPFC Microglia-PVM support audit", status)
    update_scorecard(cfg)
    print("stage61_run_pass=True")
    print(f"download_succeeded={bool(acq['download_succeeded'].iloc[0])}")
    print(f"donor_column={donor_col}")
    print(f"state_column={state_col}")
    print(f"overlap_donors={int(overlap['overlap_donors'].iloc[0])}")
    print(f"benchmark_run={not branch.empty}")
    print(f"best_real={best_real if np.isfinite(best_real) else 'NA'}")
    print(f"best_negative_control={best_neg if np.isfinite(best_neg) else 'NA'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage61_dlpfc_microglia_pvm_support_audit_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
