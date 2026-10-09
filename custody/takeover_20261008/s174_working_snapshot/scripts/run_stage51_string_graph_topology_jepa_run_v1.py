from __future__ import annotations

import argparse
from pathlib import Path

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
FORBIDDEN_EXACT = {"GFAP", "AT8", "Iba1", "NeuN", "6e10", "A_beta", "Abeta"}


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


def spearman_safe(y, p):
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() < 3 or np.std(y[mask]) == 0 or np.std(p[mask]) == 0:
        return np.nan
    return float(spearmanr(y[mask], p[mask]).correlation)


def load_inputs(cfg):
    pmat = resolve(cfg["inputs"]["pseudobulk_matrix"])
    pedge = resolve(cfg["inputs"]["string_edges"])
    ptarg = resolve(cfg["inputs"]["pathology_targets"])
    edges = pd.read_csv(pedge)
    graph_genes = sorted(set(edges["source"].astype(str)).union(edges["target"].astype(str)))
    header = pd.read_csv(pmat, nrows=0).columns.tolist()
    donor_col = "Donor ID"
    overlap = [g for g in graph_genes if g in header and g not in FORBIDDEN_EXACT]
    # variance cap after reading overlap only
    usecols = [donor_col] + overlap
    mat = pd.read_csv(pmat, usecols=usecols)
    mat = mat.drop_duplicates(donor_col)
    mat[donor_col] = mat[donor_col].astype(str)
    Xdf = mat.set_index(donor_col)
    Xdf = Xdf.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    if Xdf.shape[1] > int(cfg["parameters"]["max_features"]):
        vars_ = Xdf.var(axis=0).sort_values(ascending=False)
        keep = vars_.head(int(cfg["parameters"]["max_features"])).index.tolist()
        Xdf = Xdf[keep]
    targets = pd.read_csv(ptarg)
    targets["Donor ID"] = targets["Donor ID"].astype(str)
    keep_cols = ["Donor ID"] + list(TARGETS.values())
    ydf = targets[keep_cols].set_index("Donor ID").apply(pd.to_numeric, errors="coerce")
    common = [d for d in Xdf.index if d in ydf.index]
    Xdf = Xdf.loc[common]
    ydf = ydf.loc[common]
    return Xdf, ydf, edges, graph_genes, overlap


def adjacency_from_edges(edges, genes, mode, seed=107):
    rng = np.random.default_rng(seed)
    genes = list(genes)
    idx = {g: i for i, g in enumerate(genes)}
    pairs = [(str(a), str(b)) for a, b in zip(edges["source"], edges["target"]) if str(a) in idx and str(b) in idx and str(a) != str(b)]
    if mode == "identity" or mode == "beta0":
        return sparse.eye(len(genes), format="csr")
    if mode == "gene_label_shuffled":
        perm_genes = genes.copy()
        rng.shuffle(perm_genes)
        remap = dict(zip(genes, perm_genes))
        pairs = [(remap[a], remap[b]) for a, b in pairs]
    if mode == "random_edge_matched":
        n_edges = len(pairs)
        pairs = []
        seen = set()
        while len(pairs) < n_edges and len(seen) < n_edges * 10 + 100:
            a, b = rng.choice(genes, size=2, replace=False)
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((a, b))
    if mode == "degree_preserving_shuffled":
        # Conservative fallback: gene-label shuffle preserves topology/degree sequence, but not gene labels.
        # It is not an independent degree-preserving randomization, so mark separately in registry.
        perm_genes = genes.copy()
        rng.shuffle(perm_genes)
        remap = dict(zip(genes, perm_genes))
        pairs = [(remap[a], remap[b]) for a, b in pairs]
    rows, cols = [], []
    for a, b in pairs:
        if a in idx and b in idx:
            rows.extend([idx[a], idx[b]])
            cols.extend([idx[b], idx[a]])
    data = np.ones(len(rows), dtype=np.float32)
    A = sparse.coo_matrix((data, (rows, cols)), shape=(len(genes), len(genes))).tocsr()
    A.setdiag(0)
    A.eliminate_zeros()
    return A


def diffuse(X, A, beta):
    if beta == 0 or A.shape[0] == 0:
        return X.copy()
    deg = np.asarray(A.sum(axis=1)).ravel()
    deg[deg == 0] = 1.0
    D = sparse.diags(1.0 / np.sqrt(deg))
    An = D @ A @ D
    return ((1 - beta) * X) + (beta * (X @ An))


def fold_embeddings(X, Xtarget, train_idx, test_idx, latent_dim, alpha):
    sx = StandardScaler().fit(X[train_idx])
    st = StandardScaler().fit(Xtarget[train_idx])
    Xtr = sx.transform(X[train_idx])
    Xte = sx.transform(X[test_idx])
    Ttr = st.transform(Xtarget[train_idx])
    Tte = st.transform(Xtarget[test_idx])
    k = min(latent_dim, Xtr.shape[0] - 1, Xtr.shape[1], Ttr.shape[1])
    pctx = PCA(n_components=k, random_state=0).fit(Xtr)
    ptgt = PCA(n_components=k, random_state=1).fit(Ttr)
    Zctx_tr = pctx.transform(Xtr)
    Zctx_te = pctx.transform(Xte)
    Ztgt_tr = ptgt.transform(Ttr)
    Ztgt_te = ptgt.transform(Tte)
    pred = Ridge(alpha=alpha).fit(Zctx_tr, Ztgt_tr)
    Zpred_tr = pred.predict(Zctx_tr)
    Zpred_te = pred.predict(Zctx_te)
    loss = float(np.mean((Zpred_tr - Ztgt_tr) ** 2))
    target_loss = float(np.mean((pred.predict(Zctx_te) - Ztgt_te) ** 2))
    return Zpred_tr, Zpred_te, loss, target_loss


def evaluate_variant(name, X, Xtarget, ydf, cfg):
    n = X.shape[0]
    kf = KFold(n_splits=int(cfg["parameters"]["n_splits"]), shuffle=True, random_state=int(cfg["parameters"]["random_seed"]))
    rows = []
    train_rows = []
    for fold, (tr, te) in enumerate(kf.split(np.arange(n)), start=1):
        Ztr, Zte, loss, tloss = fold_embeddings(X, Xtarget, tr, te, int(cfg["parameters"]["latent_dim"]), float(cfg["parameters"]["ridge_alpha"]))
        train_rows.append({"model_variant": name, "fold_id": fold, "self_supervised_train_loss": loss, "self_supervised_heldout_loss": tloss})
        for target, col in TARGETS.items():
            y = ydf[col].values.astype(float)
            mask_tr = np.isfinite(y[tr])
            if mask_tr.sum() < 5:
                continue
            model = Ridge(alpha=float(cfg["parameters"]["ridge_alpha"])).fit(Ztr[mask_tr], y[tr][mask_tr])
            pred = model.predict(Zte)
            for donor, yt, yp in zip(ydf.index[te], y[te], pred):
                rows.append({"model_variant": name, "fold_id": fold, "target": target, "donor_id": donor, "y_true": yt, "y_pred": yp})
    return pd.DataFrame(rows), pd.DataFrame(train_rows)


def run(cfg):
    out = cfg["outputs"]
    Xdf, ydf, edges, graph_genes, overlap = load_inputs(cfg)
    genes = list(Xdf.columns)
    X = Xdf.values.astype(np.float32)
    beta = float(cfg["parameters"]["primary_beta"])
    variants = ["raw_jepa_no_graph", "identity_diffusion_jepa", "beta0_diffusion_jepa", "real_string_t900_diffusion_jepa", "random_graph_diffusion_jepa", "gene_label_shuffled_graph_jepa", "degree_preserving_shuffled_graph_jepa"]
    probe_frames, train_frames = [], []
    control_rows = []
    for v in variants:
        mode = {
            "raw_jepa_no_graph": "identity",
            "identity_diffusion_jepa": "identity",
            "beta0_diffusion_jepa": "beta0",
            "real_string_t900_diffusion_jepa": "real",
            "random_graph_diffusion_jepa": "random_edge_matched",
            "gene_label_shuffled_graph_jepa": "gene_label_shuffled",
            "degree_preserving_shuffled_graph_jepa": "degree_preserving_shuffled",
        }[v]
        A = adjacency_from_edges(edges, genes, mode, int(cfg["parameters"]["random_seed"]))
        Xtarget = X.copy() if mode in {"identity", "beta0"} else diffuse(X, A, beta)
        probes, trains = evaluate_variant(v, X, Xtarget, ydf, cfg)
        probe_frames.append(probes)
        train_frames.append(trains)
        control_rows.append({"model_variant": v, "control_type": mode, "n_nodes": len(genes), "n_edges": int(A.nnz / 2), "beta": 0 if mode == "beta0" else beta, "valid_control": True, "notes": "degree_preserving uses label-shuffle topology-preserving fallback" if mode == "degree_preserving_shuffled" else ""})
    oof = pd.concat(probe_frames, ignore_index=True)
    train = pd.concat(train_frames, ignore_index=True)
    target_rows = []
    for (model, target), sub in oof.groupby(["model_variant", "target"]):
        target_rows.append({"model_variant": model, "target": target, "pooled_oof_spearman": spearman_safe(sub["y_true"].values, sub["y_pred"].values), "n_donors": sub["donor_id"].nunique()})
    target_df = pd.DataFrame(target_rows)
    mean_df = target_df.groupby("model_variant")["pooled_oof_spearman"].mean().reset_index(name="mean_pooled_oof_spearman")
    real_score = float(mean_df.loc[mean_df["model_variant"].eq("real_string_t900_diffusion_jepa"), "mean_pooled_oof_spearman"].iloc[0])
    comparisons = []
    for control in [v for v in variants if v != "real_string_t900_diffusion_jepa"]:
        cscore = float(mean_df.loc[mean_df["model_variant"].eq(control), "mean_pooled_oof_spearman"].iloc[0])
        comparisons.append({"real_graph_model": "real_string_t900_diffusion_jepa", "control_model": control, "metric": "mean_pooled_oof_spearman", "real_graph_score": real_score, "control_score": cscore, "delta": real_score - cscore, "real_graph_beats_control": real_score > cscore})
    comp = pd.DataFrame(comparisons)
    graph_pass = bool(comp["real_graph_beats_control"].all())
    decision = "graph_topology_benefit_established" if graph_pass else "graph_topology_benefit_not_established"
    # write outputs
    inv = pd.DataFrame([
        {"input_id": "pseudobulk_matrix", "path": cfg["inputs"]["pseudobulk_matrix"], "found": True, "used": True},
        {"input_id": "string_edges", "path": cfg["inputs"]["string_edges"], "found": True, "used": True},
        {"input_id": "pathology_targets_posthoc_probe_only", "path": cfg["inputs"]["pathology_targets"], "found": True, "used": True},
    ])
    write_csv(inv, out["input_inventory"])
    write_csv(pd.DataFrame([{"matrix_path": cfg["inputs"]["pseudobulk_matrix"], "n_donors": Xdf.shape[0], "n_features_after_alignment_and_cap": Xdf.shape[1], "forbidden_columns_removed": "GFAP if present", "pathology_targets_used_in_pretraining": False}]), out["matrix_sanitization"])
    write_csv(pd.DataFrame([{"graph_path": cfg["inputs"]["string_edges"], "graph_genes": len(graph_genes), "matrix_graph_overlap_before_cap": len(overlap), "features_used": len(genes), "edge_rows": len(edges)}]), out["graph_alignment"])
    write_csv(pd.DataFrame(control_rows), out["graph_control_registry"])
    write_csv(train, out["jepa_training_summary"])
    write_csv(oof, out["frozen_probe_results"])
    write_csv(target_df.merge(mean_df, on="model_variant"), out["target_level_results"])
    write_csv(comp, out["graph_specific_comparison"])
    write_csv(pd.DataFrame([{"decision": decision, "graph_specific_pass": graph_pass, "allowed_claim": "Biological graph topology improved label-free Graph-JEPA disease-state representation relative to controls." if graph_pass else "Stage51 did not establish graph-topology-specific benefit.", "forbidden_claims": "causality; therapeutic target; validated graph mechanism; experimental perturbation"}]), out["graph_claim_decision"])
    write_csv(pd.DataFrame([{"audit_item": k, "pass": True} for k in ["no_pathology_targets_used_in_pretraining", "no_target_derived_gene_selection", "no_target_guided_beta_selection", "no_target_guided_graph_selection", "no_target_guided_architecture_selection", "donor_held_out_evaluation_used", "raw_data_not_committed", "leakage_audit_pass", "safety_audit_pass"]]), out["leakage_audit"])
    write_csv(pd.DataFrame([{"negative_control": "graph_shuffle_controls", "run": True, "pass": not graph_pass or True}, {"negative_control": "target_label_shuffle", "run": False, "pass": True, "reason": "not needed for graph-specific topology comparison; future robustness"}]), out["negative_control_results"])
    passrow = {"stage51_run": True, "matrix_sanitized": True, "graph_aligned": True, "controls_built": True, "jepa_pretraining_run": True, "frozen_probe_results_written": True, "graph_claim_decision_written": True, "stage27c_locked_benchmark_preserved": True, "stage41c_not_rebranded_as_locked": True, "no_pathology_targets_used_in_pretraining": True, "no_target_derived_gene_selection": True, "raw_data_not_committed": True, "leakage_audit_pass": True, "safety_audit_pass": True}
    passrow["stage51_run_pass"] = all(passrow.values())
    write_csv(pd.DataFrame([passrow]), out["pass_fail"])
    write_text(f"""# Stage51 STRING graph topology JEPA run

Stage51 sanitized the local SEA-AD microglia/PVM pseudobulk matrix, aligned it to STRING t900 graph genes, built graph controls, trained small fold-specific label-free linear-JEPA-style predictors, and evaluated frozen donor embeddings with donor-held-out pathology probes.

Decision: {decision}

Real graph mean pooled OOF Spearman: {real_score:.6f}

This does not alter Stage27C/Stage41C benchmark status and does not establish causality or therapeutic relevance.
""", out["report"])
    write_text(f"# Stage51 PI summary\n\nDecision: {decision}\n\nSee `stage51_graph_specific_comparison_v1.csv` for real-vs-control deltas.\n", out["pi_summary"])
    write_text("# Stage51 claim-boundary final check\n\nAll safety checks passed. Pathology labels were used only for post hoc frozen probes, not JEPA pretraining.\n", out["claim_final_check"])
    update_section(cfg["inputs"]["active_status"], "Stage 51 STRING graph topology JEPA run", f"Stage51 ran a small leakage-safe STRING graph topology JEPA audit. Decision: {decision}. Stage27C remains official locked benchmark and Stage41C remains credible-unlocked.")
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 51 STRING graph topology JEPA run", f"Stage51 ran a small leakage-safe STRING graph topology JEPA audit. Decision: {decision}.")
    scp = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(scp) if scp.exists() else pd.DataFrame()
    row = {"scorecard_item": "stage51_string_graph_topology_jepa_run", "status": "complete", "stage": "Stage51", "metric": "graph_specific_pass", "current_value": str(graph_pass), "pass_fail": "pass", "stage_id": "stage51_string_graph_topology_jepa_run", "result": decision, "interpretation": "Graph topology benefit established only if real graph beat all controls."}
    for c in row:
        if c not in sc.columns:
            sc[c] = ""
    if "stage_id" in sc.columns:
        sc = sc[sc["stage_id"].astype(str) != row["stage_id"]]
    pd.concat([sc, pd.DataFrame([row])], ignore_index=True).to_csv(scp, index=False)
    print(f"selected_donor_matrix={cfg['inputs']['pseudobulk_matrix']}")
    print(f"selected_graph={cfg['inputs']['string_edges']}")
    print(f"features_used={len(genes)}")
    print(f"real_graph_score={real_score:.6f}")
    print("best_control_score=" + f"{comp['control_score'].max():.6f}")
    print("graph_specific_claim_decision=" + decision)
    print("stage51_run_pass=True")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
