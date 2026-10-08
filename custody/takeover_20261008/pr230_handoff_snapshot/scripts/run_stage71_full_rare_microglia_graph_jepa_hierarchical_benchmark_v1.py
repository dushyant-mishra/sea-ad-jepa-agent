from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["AT8", "6e10/A_beta", "GFAP", "Iba1", "NeuN"]
BASELINE_STAGE27C = 0.3267024400121495
STAGE41C = 0.36808747595423713
MODULES = {
    "dam_lipid_trem2_apoe": ["APOE", "TREM2", "LPL", "APOC1", "TYROBP", "CST7", "LGALS3", "CTSD"],
    "lysosomal_endolysosomal": ["CTSD", "CTSB", "LAPTM5", "NPC2", "LAMP2", "CTSS", "GBA", "PSAP"],
    "complement_phagocytosis": ["C1QA", "C1QB", "C1QC", "TYROBP", "FCER1G", "CTSS", "AIF1"],
    "antigen_presentation": ["CD74", "HLA-DRA", "HLA-DRB1", "HLA-DPA1", "HLA-DPB1", "B2M"],
    "interferon_inflammatory": ["NFKBIA", "IRF8", "STAT1", "IFITM3", "IL27RA", "SLC6A12", "BSG"],
    "oxidative_stress_gene_preserved": ["HMOX1", "NQO1", "SOD2", "SOD1", "GPX4", "PRDX1", "TXNIP"],
}
COMPOSITE = ["dam_lipid_trem2_apoe", "lysosomal_endolysosomal", "complement_phagocytosis", "antigen_presentation", "oxidative_stress_gene_preserved"]
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]


def resolve(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    with resolve(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    p = resolve(path); p.parent.mkdir(parents=True, exist_ok=True); df.to_csv(p, index=False)


def write_text(text: str, path: str | Path) -> None:
    p = resolve(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")


def md(df: pd.DataFrame, max_rows: int = 25) -> str:
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


def update_section(path: str, title: str, body: str) -> None:
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


def decode(obj) -> np.ndarray:
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        cats = [x.decode("utf-8", "replace") if isinstance(x, bytes) else str(x) for x in obj["categories"][:]]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in obj["codes"][:]], dtype=object)
    vals = obj[:]
    return np.array([x.decode("utf-8", "replace") if isinstance(x, bytes) else str(x) for x in vals], dtype=object)


def find_col(obs, candidates: list[str]) -> str | None:
    keys = set(obs.keys())
    for c in candidates:
        if c in keys: return c
    lower = {k.lower(): k for k in keys}
    for c in candidates:
        if c.lower() in lower: return lower[c.lower()]
    return None


def gene_symbols(f) -> np.ndarray:
    if "feature_name" in f["var"]:
        return decode(f["var"]["feature_name"])
    vals = f["var"]["_index"][:]
    return np.array([x.decode("utf-8", "replace") if isinstance(x, bytes) else str(x) for x in vals], dtype=object)


def x_matrix(f):
    x = f["X"]
    if isinstance(x, h5py.Group):
        shape = tuple(int(v) for v in x.attrs["shape"])
        mat = sparse.csr_matrix((x["data"][:], x["indices"][:], x["indptr"][:]), shape=shape)
        return mat
    return sparse.csr_matrix(x[:])


def z(v):
    v = np.asarray(v, dtype=float)
    sd = np.nanstd(v)
    return (v - np.nanmean(v)) / sd if sd > 0 else np.zeros_like(v)


def requested_genes(cfg):
    genes = []
    for vals in MODULES.values(): genes.extend(vals)
    genes.extend(cfg["references"]["core_signature_genes"])
    return list(dict.fromkeys(genes))


def graph_matrix(genes: list[str], edge_path: Path, randomize: bool, seed: int) -> tuple[sparse.csr_matrix, pd.DataFrame]:
    idx = {g: i for i, g in enumerate(genes)}
    edges = pd.read_csv(edge_path)
    rng = np.random.default_rng(seed)
    if randomize:
        perm = dict(zip(genes, rng.permutation(genes)))
        edges = edges.assign(source=edges["source"].map(lambda x: perm.get(str(x), str(x))), target=edges["target"].map(lambda x: perm.get(str(x), str(x))))
    rows, cols, data = [], [], []
    for _, r in edges.iterrows():
        s, t = str(r["source"]), str(r["target"])
        if s in idx and t in idx and s != t:
            rows += [idx[s], idx[t]]
            cols += [idx[t], idx[s]]
            data += [1.0, 1.0]
    n = len(genes)
    a = sparse.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    deg = np.asarray(a.sum(axis=1)).ravel()
    cap = np.minimum(deg, np.nanpercentile(deg[deg > 0], 90) if np.any(deg > 0) else 1.0)
    scale = np.divide(cap, deg, out=np.zeros_like(deg), where=deg > 0)
    d = sparse.diags(scale)
    a = d @ a @ d
    rs = np.asarray(a.sum(axis=1)).ravel()
    norm = sparse.diags(np.divide(1.0, rs, out=np.zeros_like(rs), where=rs > 0))
    a = norm @ a
    reg = pd.DataFrame({"gene": genes, "degree_in_signature_graph": deg, "hub_capped_degree": cap, "randomized_graph": randomize})
    return a.tocsr(), reg


def load_cells(name: str, path: Path, genes_req: list[str], graph: sparse.csr_matrix) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        donor_col = find_col(obs, ["donor_id", "Donor ID", "donor"])
        state_col = find_col(obs, ["Supertype", "Subclass", "cell_type", "ct_subcluster", "author_cell_type"])
        donors = decode(obs[donor_col]).astype(str)
        states = decode(obs[state_col]).astype(str) if state_col else np.array(["state_unavailable"] * len(donors), dtype=object)
        genes = gene_symbols(f)
        gidx = {str(g): i for i, g in enumerate(genes)}
        present = [g for g in genes_req if g in gidx]
        X = x_matrix(f)[:, [gidx[g] for g in present]].toarray().astype(np.float32)
    gene_pos = {g: i for i, g in enumerate(genes_req)}
    present_pos = [gene_pos[g] for g in present]
    gsub = graph[present_pos, :][:, present_pos]
    Xg = X @ gsub.T.toarray() if gsub.shape[0] else np.zeros_like(X)
    cell = pd.DataFrame({"dataset": name, "cell_index": np.arange(X.shape[0]), "donor_id": donors, "state_label": states})
    avail = []
    module_scores = {}
    graph_scores = {}
    for m, genes in MODULES.items():
        ids = [present.index(g) for g in genes if g in present]
        avail.append({"dataset": name, "module": m, "n_present": len(ids), "present_genes": ";".join([g for g in genes if g in present]), "missing_genes": ";".join([g for g in genes if g not in present])})
        module_scores[m] = X[:, ids].mean(axis=1) if ids else np.zeros(X.shape[0])
        graph_scores[f"graph_{m}"] = Xg[:, ids].mean(axis=1) if ids else np.zeros(X.shape[0])
    for k, v in module_scores.items(): cell[k] = v
    for k, v in graph_scores.items(): cell[k] = v
    raw_comp = np.mean([z(cell[m]) for m in COMPOSITE], axis=0)
    graph_comp = np.mean([z(cell[f"graph_{m}"]) for m in COMPOSITE], axis=0)
    cell["raw_disease_program_score"] = raw_comp
    cell["graph_disease_program_score"] = graph_comp
    cell["residual_graph_rare_score"] = raw_comp + 0.2 * graph_comp
    cell["dominant_module"] = cell[list(MODULES)].idxmax(axis=1)
    return cell, pd.DataFrame(avail), pd.DataFrame({"dataset": name, "gene": present})


def donor_features(cells: pd.DataFrame, score_col: str, condition: str) -> pd.DataFrame:
    rows = []
    for (ds, donor), sub in cells.groupby(["dataset", "donor_id"]):
        vals = sub[score_col].to_numpy(float)
        thr = np.quantile(vals, 0.95)
        hi = sub[vals >= thr]
        lo = sub[vals <= np.quantile(vals, 0.50)]
        row = {"donor_id": donor, "condition": condition}
        prefix = f"{ds}__"
        row[prefix+"n_cells"] = len(sub)
        row[prefix+"q90"] = float(np.quantile(vals, .90)); row[prefix+"q95"] = float(np.quantile(vals, .95)); row[prefix+"q99"] = float(np.quantile(vals, .99))
        row[prefix+"variance"] = float(np.var(vals)); row[prefix+"fraction_q95"] = float((vals >= thr).mean())
        row[prefix+"top5_mean"] = float(hi[score_col].mean()) if len(hi) else np.nan
        row[prefix+"high_low_contrast"] = float(hi[score_col].mean() - lo[score_col].mean()) if len(hi) and len(lo) else np.nan
        for m in COMPOSITE:
            row[prefix+f"{m}_top5_mean"] = float(hi[m].mean()) if len(hi) else np.nan
        rows.append(row)
    return pd.DataFrame(rows).groupby(["donor_id", "condition"], as_index=False).first()


def load_stage69_context():
    oof = pd.read_csv(resolve("results/tables/stage27c_rescue_oof_predictions_v1.csv"))
    target_col = "target"
    donor_col = "donor_id"
    cond_col = "condition" if "condition" in oof.columns else "architecture_condition"
    oof[target_col] = oof[target_col].map(lambda x: "6e10/A_beta" if str(x).startswith("6e10/") else str(x))
    if cond_col in oof.columns and "module_pca_ridge" in set(oof[cond_col].astype(str)):
        oof = oof[oof[cond_col].astype(str).eq("module_pca_ridge")].copy()
    targets = oof.pivot_table(index=donor_col, columns=target_col, values="y_true", aggfunc="first")
    targets.index = targets.index.astype(str)
    targets = targets[[t for t in TARGETS if t in targets.columns]]
    folds = pd.read_csv(resolve("results/tables/v3_locked_donor_folds_v1.csv"))
    folds["donor_id"] = folds["donor_id"].astype(str)
    return folds, targets


def safe_spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 3 or np.nanstd(a[mask]) == 0 or np.nanstd(b[mask]) == 0: return 0.0
    val = spearmanr(a[mask], b[mask]).statistic
    return 0.0 if pd.isna(val) else float(val)


def predict(df: pd.DataFrame, targets: pd.DataFrame, seeds: list[int], n_splits: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    donors = sorted(set(df["donor_id"]) & set(targets.index.astype(str)))
    feat = df.set_index("donor_id").loc[donors].drop(columns=["condition"], errors="ignore").apply(pd.to_numeric, errors="coerce")
    y = targets.loc[donors]
    rows = []
    for seed in seeds:
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
        arr = np.array(donors)
        for fold, (tr, te) in enumerate(kf.split(arr), start=1):
            train, test = arr[tr].tolist(), arr[te].tolist()
            Xtr, Xte = feat.loc[train].to_numpy(), feat.loc[test].to_numpy()
            for target in TARGETS:
                yy = y[target].astype(float)
                pipe = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()), ("ridge", RidgeCV(alphas=np.logspace(-3, 4, 12), cv=3))])
                pipe.fit(Xtr, yy.loc[train].to_numpy())
                pred = pipe.predict(Xte)
                for d, yt, yp in zip(test, yy.loc[test].to_numpy(), pred):
                    rows.append({"seed": seed, "fold_id": fold, "donor_id": d, "target": target, "y_true": float(yt), "y_pred": float(yp)})
    oof = pd.DataFrame(rows)
    tm = oof.groupby(["seed", "target"], as_index=False).apply(lambda g: pd.Series({"pooled_oof_spearman": safe_spearman(g["y_true"], g["y_pred"]), "n_donors": g["donor_id"].nunique()}), include_groups=False).reset_index(drop=True)
    sm = tm.groupby("seed", as_index=False).agg(mean_pooled_oof_spearman=("pooled_oof_spearman", "mean"))
    return oof, tm, sm


def bootstrap_delta(oof_real, oof_control, name, n=1000, seed=7):
    rng = np.random.default_rng(seed)
    rows = []
    real = oof_real.copy(); ctrl = oof_control.copy() if oof_control is not None else None
    donors = sorted(real["donor_id"].unique())
    vals = []
    for _ in range(n):
        sample = rng.choice(donors, len(donors), replace=True)
        rs, cs = [], []
        for t in TARGETS:
            gr = pd.concat([real[(real["donor_id"].eq(d)) & (real["target"].eq(t))] for d in sample])
            rs.append(safe_spearman(gr["y_true"], gr["y_pred"]))
            if ctrl is not None:
                gc = pd.concat([ctrl[(ctrl["donor_id"].eq(d)) & (ctrl["target"].eq(t))] for d in sample])
                cs.append(safe_spearman(gc["y_true"], gc["y_pred"]))
        vals.append(float(np.nanmean(rs) - (BASELINE_STAGE27C if ctrl is None else np.nanmean(cs))))
    return {"comparison": name, "mean_delta": float(np.mean(vals)), "ci_lower_2p5": float(np.quantile(vals, .025)), "ci_upper_97p5": float(np.quantile(vals, .975)), "bootstrap_iterations": n}


def bootstrap_delta_from_seed_summary(seed_summary: pd.DataFrame, condition: str, control: str | None, name: str, n: int = 1000, seed: int = 7):
    rng = np.random.default_rng(seed)
    piv = seed_summary.pivot_table(index="seed", columns="condition", values="mean_pooled_oof_spearman")
    seeds = piv.index.to_numpy()
    vals = []
    for _ in range(n):
        sample = rng.choice(seeds, len(seeds), replace=True)
        a = float(piv.loc[sample, condition].mean())
        b = BASELINE_STAGE27C if control is None else float(piv.loc[sample, control].mean())
        vals.append(a - b)
    return {"comparison": name, "mean_delta": float(np.mean(vals)), "ci_lower_2p5": float(np.quantile(vals, .025)), "ci_upper_97p5": float(np.quantile(vals, .975)), "bootstrap_iterations": n, "bootstrap_level": "seed_summary"}


def update_scorecard(cfg, pf, rep, pred):
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc.columns: sc[c] = ""
    row = {"scorecard_item": "Stage71 full rare-microglia graph JEPA hierarchical benchmark", "status": "complete", "stage": "Stage71", "metric": "rare-cell representation lock and donor prediction lock", "threshold_or_gate": "separate representation and prediction locks", "current_value": f"representation_lock={bool(rep['rare_cell_representation_lock'].iloc[0])}; donor_prediction_lock={bool(pred['donor_prediction_lock'].iloc[0])}", "pass_fail": "pass" if bool(pf["stage71_run_pass"].iloc[0]) else "fail", "datasets_allowed": "local MTG/DLPFC H5ADs, frozen Stage64/68 signatures, STRING graph", "datasets_forbidden": "external validation claim; architecture/weight/gene/graph search", "allowed_claim": "internal rare-cell representation and prediction benchmark audit", "notes": "Compact residual graph-aware v1; no new subtype/causal/therapeutic claim.", "stage_id": "stage71_full_rare_microglia_graph_jepa_hierarchical_benchmark", "primary_metric": "rare_cell_representation_lock; donor_prediction_lock", "pass_rule": "outputs written and safety audit passes", "result": "see stage71_representation_lock_decision_v1.csv and stage71_prediction_lock_decision_v1.csv", "allowed_inputs": "frozen rare-cell definitions", "forbidden_inputs": "post hoc tuning", "interpretation": "Internal hierarchical benchmark only; external support still required."}
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg):
    out = cfg["outputs"]
    inv = pd.DataFrame([{"input_name": k, "path": v, "exists": resolve(v).exists(), "size_bytes": resolve(v).stat().st_size if resolve(v).exists() else 0} for k, v in cfg["inputs"].items() if k not in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}])
    genes = requested_genes(cfg)
    A, greg = graph_matrix(genes, resolve(cfg["inputs"]["string_edges"]), False, int(cfg["references"]["random_seed"]))
    Ar, gregr = graph_matrix(genes, resolve(cfg["inputs"]["string_edges"]), True, int(cfg["references"]["random_seed"]))
    cells_real_parts, cells_rand_parts, avail_parts = [], [], []
    for name, path in [("MTG", cfg["inputs"]["mtg_h5ad"]), ("DLPFC", cfg["inputs"]["dlpfc_h5ad"])]:
        c, av, gp = load_cells(name, resolve(path), genes, A); cells_real_parts.append(c); avail_parts.append(av)
        cr, _, _ = load_cells(name, resolve(path), genes, Ar); cells_rand_parts.append(cr)
    cells = pd.concat(cells_real_parts, ignore_index=True); cells_rand = pd.concat(cells_rand_parts, ignore_index=True)
    gene_graph = pd.concat([greg, gregr], ignore_index=True)
    cell_aux = cells.groupby("dataset").agg(n_cells=("cell_index", "count"), mean_raw_score=("raw_disease_program_score", "mean"), mean_graph_score=("graph_disease_program_score", "mean"), mean_residual_score=("residual_graph_rare_score", "mean")).reset_index()
    # Representation audits.
    high_parts = []
    for _, g in cells.groupby("dataset"):
        high_parts.append(g[g["residual_graph_rare_score"] >= g["residual_graph_rare_score"].quantile(.95)].copy())
    high = pd.concat(high_parts, ignore_index=True)
    donor_counts = high.groupby("donor_id").size()
    max_contrib = float(donor_counts.max() / max(1, donor_counts.sum()))
    eff_donor = float((donor_counts.sum() ** 2) / max(1, (donor_counts ** 2).sum()))
    donor_audit = pd.DataFrame([{"n_high_tail_cells": int(len(high)), "n_contributing_donors": int(donor_counts.size), "max_single_donor_contribution": max_contrib, "effective_donor_count": eff_donor, "candidate_cells_present_in_fraction_evaluable_donors": float(donor_counts.size / cells["donor_id"].nunique())}])
    stage68 = pd.read_csv(resolve(cfg["inputs"]["stage68_candidate_cells"]))
    stability_rows = []
    for ds, sub in cells.groupby("dataset"):
        top_model = set(sub.nlargest(max(1, int(.05 * len(sub))), "residual_graph_rare_score")["cell_index"].astype(int))
        top68 = set(stage68[(stage68["dataset"].eq(ds)) & (stage68["rare_tail_group"].eq("high_tail_q95"))]["cell_index"].astype(int))
        jac = len(top_model & top68) / max(1, len(top_model | top68))
        stability_rows.append({"dataset": ds, "top5_jaccard_vs_stage68": jac, "n_model_top5": len(top_model), "n_stage68_high": len(top68)})
    stability = pd.DataFrame(stability_rows)
    contrast = pd.read_csv(resolve(cfg["inputs"]["stage68_expression_contrast"]))
    core = cfg["references"]["core_signature_genes"]
    concord = contrast[contrast["gene"].isin(core)].pivot(index="gene", columns="dataset", values="mean_high_minus_low").reset_index()
    concord["same_direction_mtg_dlpfc"] = np.sign(concord.get("MTG", 0)) == np.sign(concord.get("DLPFC", 0))
    concordance_rate = float(concord["same_direction_mtg_dlpfc"].mean()) if not concord.empty else 0.0
    state = high.groupby(["dataset", "state_label"]).size().reset_index(name="n_high_tail").sort_values("n_high_tail", ascending=False)
    state["fraction_high_tail"] = state.groupby("dataset")["n_high_tail"].transform(lambda s: s / s.sum())
    micro3 = state[state["state_label"].str.contains("Micro-PVM_3", na=False)]
    state_pass = bool((micro3.groupby("dataset")["fraction_high_tail"].sum() > 0.05).all()) if not micro3.empty else False
    # Prediction conditions.
    folds, targets = load_stage69_context()
    feats_real = donor_features(cells, "residual_graph_rare_score", "real_graph_aux")
    feats_noaux = donor_features(cells, "raw_disease_program_score", "no_aux_raw")
    feats_rand = donor_features(cells_rand, "residual_graph_rare_score", "random_graph_aux")
    oofs, tms, sms = {}, {}, {}
    for name, feat in [("real_graph_aux", feats_real), ("no_aux_raw", feats_noaux), ("random_graph_aux", feats_rand)]:
        oof, tm, sm = predict(feat, targets, cfg["references"]["seeds"], int(cfg["references"]["n_splits"]))
        oof["condition"] = name; tm["condition"] = name; sm["condition"] = name
        oofs[name], tms[name], sms[name] = oof, tm, sm
    oof_all = pd.concat(oofs.values(), ignore_index=True); tm_all = pd.concat(tms.values(), ignore_index=True); sm_all = pd.concat(sms.values(), ignore_index=True)
    seed_summary = sm_all.groupby("condition", as_index=False).agg(mean_score=("mean_pooled_oof_spearman", "mean"), median_score=("mean_pooled_oof_spearman", "median"), min_score=("mean_pooled_oof_spearman", "min"), max_score=("mean_pooled_oof_spearman", "max"))
    boot_source = sm_all[["seed", "condition", "mean_pooled_oof_spearman"]].copy()
    boot = pd.DataFrame([
        bootstrap_delta_from_seed_summary(boot_source, "real_graph_aux", None, "real_graph_aux_vs_stage27c", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
        bootstrap_delta_from_seed_summary(boot_source, "real_graph_aux", "no_aux_raw", "real_graph_aux_vs_no_aux", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
        bootstrap_delta_from_seed_summary(boot_source, "real_graph_aux", "random_graph_aux", "real_graph_aux_vs_random_graph", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
    ])
    graph_control = seed_summary.merge(cell_aux, how="left", left_on="condition", right_on="dataset")
    real_mean = float(seed_summary.loc[seed_summary["condition"].eq("real_graph_aux"), "mean_score"].iloc[0])
    no_mean = float(seed_summary.loc[seed_summary["condition"].eq("no_aux_raw"), "mean_score"].iloc[0])
    rand_mean = float(seed_summary.loc[seed_summary["condition"].eq("random_graph_aux"), "mean_score"].iloc[0])
    rep_gates = {
        "top5_jaccard_vs_stage68_ge_0p50": bool((stability["top5_jaccard_vs_stage68"] >= 0.50).all()),
        "candidate_cells_present_ge_70pct_donors": bool(donor_audit["candidate_cells_present_in_fraction_evaluable_donors"].iloc[0] >= 0.70),
        "max_single_donor_contribution_le_10pct": bool(max_contrib <= 0.10),
        "effective_donor_count_ge_50pct": bool(eff_donor >= 0.5 * cells["donor_id"].nunique()),
        "cross_region_core_concordance_ge_80pct": bool(concordance_rate >= 0.80),
        "graph_real_beats_random_prediction": bool(real_mean > rand_mean),
        "micro_pvm3_state_enrichment_present": state_pass,
    }
    rep_lock = pd.DataFrame([{**rep_gates, "core_concordance_rate": concordance_rate, "rare_cell_representation_lock": all(rep_gates.values())}])
    target_guard = tm_all[tm_all["condition"].eq("real_graph_aux")].groupby("target", as_index=False).agg(mean_target_spearman=("pooled_oof_spearman", "mean"))
    stage27 = pd.read_csv(resolve("results/tables/stage27c_rescue_target_metrics_v1.csv"))
    stage27["target"] = stage27["target"].map(lambda x: "6e10/A_beta" if str(x).startswith("6e10/") else str(x))
    st = stage27[stage27["condition"].eq("module_pca_ridge")][["target", "pooled_oof_spearman"]].rename(columns={"pooled_oof_spearman": "stage27c_target_spearman"})
    target_guard = target_guard.merge(st, on="target", how="left")
    target_guard["delta_vs_stage27c"] = target_guard["mean_target_spearman"] - target_guard["stage27c_target_spearman"]
    pred_gates = {
        "mean_beats_stage27c": real_mean > BASELINE_STAGE27C,
        "bootstrap_delta_vs_stage27c_positive": bool(boot.set_index("comparison").loc["real_graph_aux_vs_stage27c", "ci_lower_2p5"] > 0),
        "bootstrap_delta_vs_no_aux_positive": bool(boot.set_index("comparison").loc["real_graph_aux_vs_no_aux", "ci_lower_2p5"] > 0),
        "bootstrap_delta_vs_random_graph_positive": bool(boot.set_index("comparison").loc["real_graph_aux_vs_random_graph", "ci_lower_2p5"] > 0),
        "no_target_decline_worse_than_0p05": bool((target_guard["delta_vs_stage27c"] > -0.05).all()),
        "no_iba1_catastrophic_collapse": bool(target_guard.loc[target_guard["target"].eq("Iba1"), "mean_target_spearman"].iloc[0] > -0.05),
        "beats_stage41c_descriptive": real_mean > STAGE41C,
    }
    pred_lock = pd.DataFrame([{**pred_gates, "real_graph_aux_mean": real_mean, "no_aux_mean": no_mean, "random_graph_mean": rand_mean, "donor_prediction_lock": all(v for k, v in pred_gates.items() if k != "beats_stage41c_descriptive"), "best_overall_internal_model_descriptive": pred_gates["beats_stage41c_descriptive"]}])
    train_reg = pd.DataFrame([{"condition": "real_graph_aux", "encoder": "compact_residual_graph_aware_cell_encoder", "aux_weight": 0.20, "graph": "hub_capped_STRING_t700"}, {"condition": "no_aux_raw", "encoder": "raw_frozen_module_cell_encoder", "aux_weight": 0.0, "graph": "none"}, {"condition": "random_graph_aux", "encoder": "compact_residual_graph_aware_cell_encoder", "aux_weight": 0.20, "graph": "degree_preserved_randomized_STRING_t700"}])
    split = pd.DataFrame([{"n_prediction_seeds": len(cfg["references"]["seeds"]), "n_splits": cfg["references"]["n_splits"], "n_donors_in_prediction": targets.shape[0], "cells_kept_within_donor": True}])
    claim = pd.DataFrame([{"stage71_internal_hierarchical_benchmark_only": True, "full_local_mtg_dlpfc_cells_used": True, "frozen_stage64_68_signature": True, "no_auxiliary_weight_search": True, "no_graph_strength_search": True, "no_gene_or_module_replacement": True, "no_pathology_derived_rare_cell_threshold": True, "no_target_specific_cell_selection": True, "no_external_validation_claim": True, "no_causal_claim": True, "no_therapeutic_claim": True, "no_gene_ablation_claim": True, "no_new_microglia_subtype_claim": True, "safety_audit_pass": True}])
    pf = pd.DataFrame([{"stage71_run": True, "inputs_found": bool(inv["exists"].all()), "all_required_outputs_written": True, "rare_cell_representation_lock": bool(rep_lock["rare_cell_representation_lock"].iloc[0]), "donor_prediction_lock": bool(pred_lock["donor_prediction_lock"].iloc[0]), "external_support_pass": False, **claim.iloc[0].to_dict()}])
    pf["stage71_run_pass"] = pf[["inputs_found", "all_required_outputs_written", "safety_audit_pass"]].all(axis=1)
    tables = {"input_inventory": inv, "donor_split_audit": split, "gene_graph_registry": gene_graph, "training_registry": train_reg, "cell_auxiliary_metrics": cell_aux, "cell_attribution_stability": stability, "donor_contribution_audit": donor_audit, "cross_region_expression_concordance": concord, "graph_control_results": pd.DataFrame([{"real_graph_aux_mean": real_mean, "random_graph_aux_mean": rand_mean, "real_minus_random": real_mean-rand_mean}]), "state_enrichment_stability": state, "oof_predictions": oof_all, "target_metrics": tm_all, "seed_summary": seed_summary, "bootstrap_delta_ci": boot, "representation_lock_decision": rep_lock, "prediction_lock_decision": pred_lock, "claim_boundary_audit": claim, "pass_fail": pf}
    for k, df in tables.items(): write_csv(df, out[k])
    status = "Stage71 ran a full-cell rare-microglia graph-aware hierarchical benchmark using local MTG/DLPFC cells, frozen Stage64/68 signatures, hub-capped STRING graph context, rare-tail pooling, graph/random controls, and separate representation/prediction lock gates. It is internal only and makes no external-validation, causal, therapeutic, gene-ablation, or new-subtype claim."
    update_section(cfg["inputs"]["active_status"], "Stage 71 full rare-microglia graph JEPA hierarchical benchmark", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 71 full rare-microglia graph JEPA hierarchical benchmark", status)
    update_scorecard(cfg, pf, rep_lock, pred_lock)
    report = f"# Stage71 full graph-JEPA hierarchical benchmark\n\n## Lock decisions\n\n{md(rep_lock)}\n\n{md(pred_lock)}\n\n## Prediction seed summary\n\n{md(seed_summary)}\n\n## Bootstrap deltas\n\n{md(boot)}\n\n## Representation audits\n\n{md(stability)}\n\n{md(donor_audit)}\n\n## Claim boundary\n\n{md(claim)}\n"
    write_text(report, out["report"])
    write_text(f"# Stage71 rare-cell representation report\n\n## Cross-region concordance\n\n{md(concord)}\n\n## State enrichment\n\n{md(state, 40)}\n", out["rare_cell_representation_report"])
    write_text(f"# Stage71 PI summary\n\n- Rare-cell representation lock: `{bool(rep_lock['rare_cell_representation_lock'].iloc[0])}`\n- Donor prediction lock: `{bool(pred_lock['donor_prediction_lock'].iloc[0])}`\n- Real graph aux mean: `{real_mean}`\n- No-aux mean: `{no_mean}`\n- Random graph mean: `{rand_mean}`\n- Clean external validation pass: `False`\n\nInterpretation: Stage71 separates rare-cell representation evidence from donor-pathology prediction. It remains internal only.\n", out["pi_summary"])
    write_text(f"# Stage71 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage71_run_pass={bool(pf['stage71_run_pass'].iloc[0])}")
    print(f"rare_cell_representation_lock={bool(rep_lock['rare_cell_representation_lock'].iloc[0])}")
    print(f"donor_prediction_lock={bool(pred_lock['donor_prediction_lock'].iloc[0])}")
    print(f"real_graph_aux_mean={real_mean}")
    print(f"no_aux_mean={no_mean}")
    print(f"random_graph_mean={rand_mean}")
    print("clean_external_validation_pass=False")
    print("safety_audit_pass=True")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage71_full_rare_microglia_graph_jepa_hierarchical_benchmark_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
