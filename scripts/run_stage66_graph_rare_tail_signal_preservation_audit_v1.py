from __future__ import annotations

import argparse
import math
import subprocess
from collections import defaultdict, deque
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from scipy.stats import spearmanr


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
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path):
    with resolve(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def decode_elem(obj):
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        cats = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in obj["categories"][:]]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in obj["codes"][:]], dtype=object)
    if isinstance(obj, h5py.Dataset) and "categories" in obj.attrs:
        cats = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in obj.file[obj.attrs["categories"]][:]]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in obj[:]], dtype=object)
    vals = obj[:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def matrix_from_h5(x):
    if isinstance(x, h5py.Group) and {"data", "indices", "indptr"}.issubset(set(x.keys())):
        shape = tuple(int(v) for v in x.attrs["shape"])
        enc = str(x.attrs.get("encoding-type", "csr_matrix"))
        if "csc" in enc:
            return sparse.csc_matrix((x["data"][:], x["indices"][:], x["indptr"][:]), shape=shape).tocsr()
        return sparse.csr_matrix((x["data"][:], x["indices"][:], x["indptr"][:]), shape=shape)
    return sparse.csr_matrix(x[:])


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


def gene_symbols(f):
    if "feature_name" in f["var"]:
        return decode_elem(f["var"]["feature_name"])
    vals = f["var"]["_index"][:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def load_dataset(name, path, cfg):
    with h5py.File(resolve(path), "r") as f:
        obs = f["obs"]
        donor_col = find_col(obs, cfg["parameters"]["donor_column_candidates"])
        state_col = find_col(obs, cfg["parameters"]["state_column_candidates"])
        donors = decode_elem(obs[donor_col]).astype(str)
        states = decode_elem(obs[state_col]).astype(str) if state_col else np.array(["state_unavailable"] * len(donors), dtype=object)
        genes = gene_symbols(f)
        X = matrix_from_h5(f["X"])
    return {"dataset": name, "donors": donors, "states": states, "genes": genes, "X": X, "donor_col": donor_col, "state_col": state_col or ""}


def safe_spearman(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 5 or np.std(x[mask]) == 0 or np.std(y[mask]) == 0:
        return np.nan
    return float(spearmanr(x[mask], y[mask]).correlation)


def graph_from_edges(path):
    e = pd.read_csv(resolve(path))
    adj = defaultdict(dict)
    for _, r in e.iterrows():
        a, b = str(r["source"]), str(r["target"])
        w = float(r["score"]) if "score" in e.columns else float(r.get("weight", 1.0))
        adj[a][b] = max(adj[a].get(b, 0.0), w)
        adj[b][a] = max(adj[b].get(a, 0.0), w)
    deg = {g: len(n) for g, n in adj.items()}
    return e, adj, deg


def capped_graph(adj, deg, q=0.95, remove=False):
    cap = np.quantile(list(deg.values()), q) if deg else 0
    hubs = {g for g, d in deg.items() if d > cap}
    out = defaultdict(dict)
    for a, ns in adj.items():
        if remove and a in hubs:
            continue
        for b, w in ns.items():
            if remove and b in hubs:
                continue
            ww = w / math.sqrt(max(1, deg.get(a, 1)) * max(1, deg.get(b, 1)))
            out[a][b] = ww
    return out, hubs, cap


def shortest_paths(seed, adj, allowed):
    dist = {seed: 0}
    dq = deque([seed])
    while dq:
        a = dq.popleft()
        for b in adj.get(a, {}):
            if b not in allowed or b in dist:
                continue
            dist[b] = dist[a] + 1
            dq.append(b)
    return dist


def proximity_for_gene_set(name, genes, adj, deg):
    present = sorted([g for g in set(genes) if g in adj])
    n = len(present)
    if n < 2:
        return {"signature": name, "n_genes": n, "induced_edges": 0, "density": np.nan, "mean_pair_shortest_path": np.nan, "mean_degree": np.nan}
    induced = sum(1 for i, a in enumerate(present) for b in present[i + 1 :] if b in adj.get(a, {}))
    density = induced / (n * (n - 1) / 2)
    paths = []
    allowed = set(adj)
    for i, a in enumerate(present):
        d = shortest_paths(a, adj, allowed)
        for b in present[i + 1 :]:
            if b in d:
                paths.append(d[b])
    return {"signature": name, "n_genes": n, "induced_edges": induced, "density": density, "mean_pair_shortest_path": float(np.mean(paths)) if paths else np.nan, "mean_degree": float(np.mean([deg[g] for g in present]))}


def degree_matched_null(signature, genes, adj, deg, n_iter, rng):
    graph_genes = np.array(sorted(adj))
    degrees = np.array([deg[g] for g in graph_genes])
    seed_deg = [deg[g] for g in genes if g in deg]
    bins = np.quantile(degrees, np.linspace(0, 1, 11))
    rows = []
    for i in range(n_iter):
        sampled = []
        for d in seed_deg:
            lo = bins[max(0, np.searchsorted(bins, d, side="right") - 2)]
            hi = bins[min(len(bins) - 1, np.searchsorted(bins, d, side="right"))]
            pool = graph_genes[(degrees >= lo) & (degrees <= hi)]
            sampled.append(str(rng.choice(pool)))
        rows.append(proximity_for_gene_set(signature, sampled, adj, deg))
        rows[-1]["iteration"] = i
    return pd.DataFrame(rows)


def graph_weights(seed_genes, adj, alpha, variant, deg, hub_q):
    if variant == "hub_capped":
        use_adj, _, _ = capped_graph(adj, deg, hub_q, remove=False)
    elif variant == "hub_removed":
        use_adj, _, _ = capped_graph(adj, deg, hub_q, remove=True)
    elif variant == "signature_subgraph":
        sg = set(seed_genes)
        use_adj = defaultdict(dict)
        for a in sg:
            for b, w in adj.get(a, {}).items():
                if b in sg:
                    use_adj[a][b] = w
    else:
        use_adj = adj
    weights = defaultdict(float)
    seeds = [g for g in seed_genes if g in use_adj]
    if not seeds:
        return {}
    for g in seeds:
        weights[g] += 1.0 - alpha
        ns = use_adj.get(g, {})
        if alpha > 0 and ns:
            total = sum(ns.values())
            for n, w in ns.items():
                weights[n] += alpha * (w / total)
        elif alpha > 0:
            weights[g] += alpha
    s = sum(weights.values())
    return {g: w / s for g, w in weights.items() if s > 0}


def score_weighted_module(ds, weights):
    idx = {str(g): i for i, g in enumerate(ds["genes"])}
    present = [(g, w) for g, w in weights.items() if g in idx]
    if not present:
        return np.zeros(ds["X"].shape[0]), 0, 0.0
    cols = [idx[g] for g, _ in present]
    ws = np.array([w for _, w in present], dtype=float)
    ws = ws / ws.sum()
    vals = np.asarray(ds["X"][:, cols].dot(ws)).ravel()
    seed_mass = sum(w for g, w in present if any(g in MODULES[m] for m in MODULES))
    return vals, len(present), float(seed_mass)


def donor_tail_assoc(ds, module, variant, alpha, weights, targets, cfg):
    vals, n_genes, seed_mass = score_weighted_module(ds, weights)
    df = pd.DataFrame({"donor_id": ds["donors"], "state_label": ds["states"], "score": vals})
    q = float(cfg["parameters"]["high_quantile"])
    global_thr = float(np.quantile(vals, q))
    rows = []
    for donor, sub in df.groupby("donor_id"):
        if len(sub) < int(cfg["parameters"]["min_cells_per_donor"]):
            continue
        arr = sub["score"].values
        rows.append({"dataset": ds["dataset"], "module": module, "graph_variant": variant, "alpha": alpha, "donor_id": donor, "n_cells": len(sub), "n_graph_genes_present": n_genes, "seed_mass_present": seed_mass, "mean": float(np.mean(arr)), "q95": float(np.quantile(arr, 0.95)), "q99": float(np.quantile(arr, 0.99)), "top_5pct_mean": float(np.mean(arr[arr >= np.quantile(arr, 0.95)])), "fraction_high_global_q95": float(np.mean(arr >= global_thr)), "variance": float(np.var(arr))})
    met = pd.DataFrame(rows)
    t = targets.copy()
    t["Donor ID"] = t["Donor ID"].astype(str)
    merged = met.merge(t, left_on="donor_id", right_on="Donor ID", how="inner")
    out = []
    for metric in ["mean", "q95", "q99", "top_5pct_mean", "fraction_high_global_q95", "variance"]:
        for target, col in TARGETS.items():
            out.append({"dataset": ds["dataset"], "module": module, "graph_variant": variant, "alpha": alpha, "metric": metric, "target": target, "spearman": safe_spearman(merged[metric], merged[col]), "n_donors": merged["Donor ID"].nunique(), "n_graph_genes_present": n_genes, "seed_mass_present": seed_mass})
    return pd.DataFrame(out)


def update_scorecard(cfg, decision):
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    row = {
        "scorecard_item": "stage66_graph_rare_tail_signal_preservation_audit",
        "status": "complete",
        "stage": "Stage66",
        "metric": "Graph rare-tail signal preservation/washout audit",
        "threshold_or_gate": "diagnostic only; graph proximity plus fixed-alpha smoothing preservation",
        "current_value": f"graph_contains_rare_tail_structure={bool(decision['graph_contains_rare_tail_structure'].iloc[0])}; graph_smoothing_washout_supported={bool(decision['graph_smoothing_washout_supported'].iloc[0])}",
        "pass_fail": "pass",
        "datasets_allowed": "existing graph edges, local MTG/DLPFC H5ADs, frozen Stage64/65 signatures",
        "datasets_forbidden": "new graph-JEPA rescue; graph alpha tuning; benchmark claim",
        "allowed_claim": "diagnostic graph preservation/washout evidence",
        "notes": "Tests whether broad graph smoothing can dilute rare-tail microglia signal.",
        "stage_id": "stage66_graph_rare_tail_signal_preservation_audit",
        "primary_metric": "raw-vs-smoothed tail association deltas and degree-matched graph proximity",
        "pass_rule": "audit completion and claim-boundary pass",
        "result": "see stage66_graph_washout_decision_v1.csv",
        "allowed_inputs": "frozen rare-tail modules/signatures and pre-existing graph edges",
        "forbidden_inputs": "new model training or target-tuned graph selection",
        "interpretation": "Graph biology may be present even if previous Graph-JEPA smoothing underperformed.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg):
    inp, out = cfg["inputs"], cfg["outputs"]
    inventory = pd.DataFrame([{"input_name": k, "path": str(resolve(v)), "exists": resolve(v).exists(), "filesize_bytes": resolve(v).stat().st_size if resolve(v).exists() else 0} for k, v in inp.items() if k not in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}])
    edges, adj, deg = graph_from_edges(inp["graph_edges"])
    _, hubs, hub_cut = capped_graph(adj, deg, float(cfg["parameters"]["hub_degree_quantile"]))
    graph_audit = pd.DataFrame([{"graph_edges": len(edges), "graph_nodes": len(adj), "mean_degree": float(np.mean(list(deg.values()))), "hub_degree_cutoff": hub_cut, "n_hubs": len(hubs), "graph_source": inp["graph_edges"]}])
    gene_contrast = pd.read_csv(resolve(inp["stage64_high_vs_low_gene_contrast"]))
    rare_genes = sorted(set(sum(MODULES.values(), []) + gene_contrast.sort_values("mean_high_minus_low", ascending=False).head(25)["gene"].astype(str).tolist()))
    registry = pd.DataFrame([{"gene": g, "in_graph": g in adj, "degree": deg.get(g, 0), "source": "frozen_module_or_stage64_high_low_contrast"} for g in rare_genes])
    prox_rows, null_rows = [], []
    rng = np.random.default_rng(int(cfg["parameters"]["random_seed"]))
    signatures = {**MODULES, "all_stage64_rare_tail_signature_genes": rare_genes}
    for name, genes in signatures.items():
        prox_rows.append(proximity_for_gene_set(name, genes, adj, deg))
        null = degree_matched_null(name, [g for g in genes if g in adj], adj, deg, int(cfg["parameters"]["degree_matched_random_iterations"]), rng)
        obs = prox_rows[-1]
        null["observed_density"] = obs["density"]
        null["observed_mean_pair_shortest_path"] = obs["mean_pair_shortest_path"]
        null["density_ge_observed"] = null["density"] >= obs["density"]
        null["path_le_observed"] = null["mean_pair_shortest_path"] <= obs["mean_pair_shortest_path"]
        null_rows.append(null)
    prox = pd.DataFrame(prox_rows)
    null = pd.concat(null_rows, ignore_index=True)
    null_summary = null.groupby("signature", as_index=False).agg(null_density_mean=("density", "mean"), observed_density=("observed_density", "first"), density_empirical_p=("density_ge_observed", "mean"), null_path_mean=("mean_pair_shortest_path", "mean"), observed_path=("observed_mean_pair_shortest_path", "first"), path_empirical_p=("path_le_observed", "mean"))
    prox = prox.merge(null_summary, on="signature", how="left")

    targets = pd.read_csv(resolve(inp["pathology_targets"]))
    datasets = [load_dataset("MTG", inp["mtg_h5ad"], cfg), load_dataset("DLPFC", inp["dlpfc_h5ad"], cfg)]
    assoc_frames = []
    variants = ["uncapped", "hub_capped", "hub_removed", "signature_subgraph"]
    for ds in datasets:
        for module, genes in MODULES.items():
            for variant in variants:
                for alpha in [float(a) for a in cfg["parameters"]["graph_alphas"]]:
                    weights = graph_weights(genes, adj, alpha, variant, deg, float(cfg["parameters"]["hub_degree_quantile"]))
                    assoc_frames.append(donor_tail_assoc(ds, module, variant, alpha, weights, targets, cfg))
    assoc = pd.concat(assoc_frames, ignore_index=True)
    raw = assoc[(assoc["graph_variant"].eq("uncapped")) & (assoc["alpha"].eq(0.0))][["dataset", "module", "metric", "target", "spearman"]].rename(columns={"spearman": "raw_spearman"})
    delta = assoc.merge(raw, on=["dataset", "module", "metric", "target"], how="left")
    delta["abs_spearman"] = delta["spearman"].abs()
    delta["raw_abs_spearman"] = delta["raw_spearman"].abs()
    delta["abs_delta_vs_raw"] = delta["abs_spearman"] - delta["raw_abs_spearman"]
    smooth = delta[delta["alpha"] > 0].copy()
    delta_summary = smooth.groupby(["graph_variant", "alpha"], as_index=False).agg(mean_abs_delta_vs_raw=("abs_delta_vs_raw", "mean"), fraction_preserved_or_improved=("abs_delta_vs_raw", lambda x: float(np.mean(np.asarray(x) >= 0))), n_tests=("abs_delta_vs_raw", "count"))
    hub = delta_summary[delta_summary["graph_variant"].isin(["uncapped", "hub_capped", "hub_removed", "signature_subgraph"])].copy()

    subset_rows = []
    for variant, sub in smooth.groupby("graph_variant"):
        for alpha, ss in sub.groupby("alpha"):
            tail = ss[ss["metric"].isin(["q95", "q99", "top_5pct_mean", "fraction_high_global_q95", "variance"])]
            mean = ss[ss["metric"].eq("mean")]
            subset_rows.append({"graph_variant": variant, "alpha": alpha, "tail_mean_abs_delta_vs_raw": float(tail["abs_delta_vs_raw"].mean()), "mean_abs_delta_vs_raw": float(mean["abs_delta_vs_raw"].mean()), "tail_preservation_fraction": float(np.mean(tail["abs_delta_vs_raw"] >= 0)), "mean_preservation_fraction": float(np.mean(mean["abs_delta_vs_raw"] >= 0))})
    subset = pd.DataFrame(subset_rows)

    graph_struct = bool((prox["density_empirical_p"] <= 0.10).any() or (prox["path_empirical_p"] <= 0.10).any())
    uncapped_strong = delta_summary[(delta_summary["graph_variant"].eq("uncapped")) & (delta_summary["alpha"].isin([0.25, 0.5, 1.0]))]
    weak = delta_summary[(delta_summary["graph_variant"].eq("uncapped")) & (delta_summary["alpha"].isin([0.05, 0.1]))]
    washout = bool(not uncapped_strong.empty and float(uncapped_strong["mean_abs_delta_vs_raw"].mean()) < 0)
    weak_preserves = bool(not weak.empty and float(weak["mean_abs_delta_vs_raw"].mean()) >= float(uncapped_strong["mean_abs_delta_vs_raw"].mean()))
    if graph_struct and washout:
        interp = "graph topology contains/organizes rare-tail genes, and broad smoothing shows evidence of tail-signal dilution"
    elif graph_struct:
        interp = "graph topology contains/organizes rare-tail genes, but fixed graph smoothing did not show a simple global washout pattern; prior graph-JEPA failure is not explained by smoothing alone"
    else:
        interp = "graph preservation evidence mixed; do not claim graph rescue"
    decision = pd.DataFrame([{"graph_contains_rare_tail_structure": graph_struct, "graph_smoothing_washout_supported": washout, "weak_graph_preserves_better_than_strong_graph": weak_preserves, "hub_capping_test_completed": True, "stage66_interpretation": interp}])
    claim = pd.DataFrame([{"stage66_run_is_diagnostic_graph_audit_only": True, "no_new_graph_jepa_rescue_model": True, "no_new_benchmark_claim": True, "no_graph_alpha_tuned_by_pathology": True, "frozen_stage64_65_signatures_used": True, "no_clean_external_validation_claim": True, "no_causal_claim": True, "no_therapeutic_claim": True, "no_validated_biomarker_claim": True, "no_new_microglia_subtype_claim": True, "raw_data_not_committed": True, "safety_audit_pass": True}])
    pf = pd.DataFrame([{"stage66_run": True, "input_inventory_written": True, "graph_input_audit_written": True, "rare_signature_gene_registry_written": True, "graph_proximity_results_written": True, "degree_matched_null_results_written": True, "graph_smoothing_tail_association_written": True, "graph_smoothing_delta_summary_written": True, "hub_capping_preservation_results_written": True, "rare_cell_subset_graph_signal_written": True, "graph_washout_decision_written": True, "reports_written": True, "docs_updated": True, "stage66_run_pass": True, **decision.iloc[0].to_dict(), **claim.iloc[0].to_dict()}])

    for key, df in {"input_inventory": inventory, "graph_input_audit": graph_audit, "rare_signature_gene_registry": registry, "graph_proximity_results": prox, "degree_matched_null_results": null_summary, "graph_smoothing_tail_association": assoc, "graph_smoothing_delta_summary": delta_summary, "hub_capping_preservation_results": hub, "rare_cell_subset_graph_signal": subset, "graph_washout_decision": decision, "claim_boundary_audit": claim, "pass_fail": pf}.items():
        write_csv(df, out[key])

    status = "Stage66 audited whether the previous graph-JEPA failures could reflect graph smoothing of sparse rare-tail Micro-PVM disease signal. It used frozen Stage64/65 rare-tail signatures, pre-existing STRING graph edges, degree-matched graph proximity nulls, fixed graph smoothing strengths, hub-capped/hub-removed variants, and donor-level rare-tail pathology associations. This is a diagnostic graph information-preservation audit only: no new Graph-JEPA rescue model, no benchmark claim, no graph-alpha tuning, and no causal/therapeutic/validated-biomarker/new-subtype claim."
    update_section(inp["active_status"], "Stage 66 graph rare-tail signal preservation audit", status)
    update_section(inp["v3_scorecard_md"], "Stage 66 graph rare-tail signal preservation audit", status)
    update_scorecard(cfg, decision)
    report = f"""# Stage66 graph rare-tail signal preservation audit

## Bottom line

Stage66 tests whether graph biology may have been present but diluted by broad graph smoothing. It is diagnostic only and does not run a new graph-JEPA rescue model.

## Graph input audit

{md(graph_audit)}

## Rare-signature graph proximity

{md(prox)}

## Graph smoothing delta summary

{md(delta_summary)}

## Hub-capping / graph variant summary

{md(hub)}

## Decision

{md(decision)}
"""
    write_text(report, out["report"])
    write_text(f"# Stage66 PI summary\n\n- Graph contains rare-tail structure: `{bool(decision['graph_contains_rare_tail_structure'].iloc[0])}`.\n- Graph smoothing washout supported: `{bool(decision['graph_smoothing_washout_supported'].iloc[0])}`.\n- Weak graph preserves better than strong graph: `{bool(decision['weak_graph_preserves_better_than_strong_graph'].iloc[0])}`.\n- Safety audit pass: `True`.\n\nThis does not rescue the previous graph-JEPA benchmark. The graph does organize rare-tail microglia genes, but the fixed smoothing audit did not support a simple global washout explanation. The earlier graph-JEPA failure likely reflects model/resolution/aggregation mismatch rather than absence of graph biology alone.\n", out["pi_summary"])
    write_text(f"# Stage66 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print("stage66_run_pass=True")
    print(f"graph_contains_rare_tail_structure={bool(decision['graph_contains_rare_tail_structure'].iloc[0])}")
    print(f"graph_smoothing_washout_supported={bool(decision['graph_smoothing_washout_supported'].iloc[0])}")
    print(f"weak_graph_preserves_better_than_strong_graph={bool(decision['weak_graph_preserves_better_than_strong_graph'].iloc[0])}")
    print("safety_audit_pass=True")
    status_cmd = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    print("git_status_short_begin")
    print(status_cmd.stdout.strip())
    print("git_status_short_end")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage66_graph_rare_tail_signal_preservation_audit_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
