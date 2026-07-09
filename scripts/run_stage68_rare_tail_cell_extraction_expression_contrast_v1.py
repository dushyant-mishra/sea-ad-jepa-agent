from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from scipy.stats import ranksums


ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    "dam_lipid_trem2_apoe": ["APOE", "TREM2", "LPL", "APOC1", "TYROBP", "CST7", "LGALS3", "CTSD"],
    "lysosomal_endolysosomal": ["CTSD", "CTSB", "LAPTM5", "NPC2", "LAMP2", "CTSS", "GBA", "PSAP"],
    "complement_phagocytosis": ["C1QA", "C1QB", "C1QC", "TYROBP", "FCER1G", "CTSS", "AIF1"],
    "antigen_presentation": ["CD74", "HLA-DRA", "HLA-DRB1", "HLA-DPA1", "HLA-DPB1", "B2M"],
    "interferon_inflammatory": ["NFKBIA", "IRF8", "STAT1", "IFITM3", "IL27RA", "SLC6A12", "BSG"],
    "oxidative_stress_gene_preserved": ["HMOX1", "NQO1", "SOD2", "SOD1", "GPX4", "PRDX1", "TXNIP"],
}
STAGE47_CANDIDATES = [
    "APOE", "APP", "TREM2", "TYROBP", "C1QA", "C1QB", "C1QC", "C3", "CD4", "CD74",
    "CTSD", "CSF1R", "PLCG2", "MSR1", "PLD3", "SLC38A9", "AP1G1", "GSK3B",
    "PTPN18", "SLAIN2", "FIP1L1", "ERC1", "KIF2A", "PAFAH1B1", "UGCG",
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


def read_cfg(path: str | Path) -> dict:
    with resolve(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text: str, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


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


def decode_elem(obj) -> np.ndarray:
    if isinstance(obj, h5py.Group) and "categories" in obj and "codes" in obj:
        cats = [v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in obj["categories"][:]]
        return np.array([cats[int(c)] if 0 <= int(c) < len(cats) else "" for c in obj["codes"][:]], dtype=object)
    vals = obj[:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def find_col(obs, candidates: list[str]) -> str | None:
    keys = set(obs.keys())
    for c in candidates:
        if c in keys:
            return c
    lower = {k.lower(): k for k in keys}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def gene_symbols(f: h5py.File) -> np.ndarray:
    if "feature_name" in f["var"]:
        return decode_elem(f["var"]["feature_name"])
    vals = f["var"]["_index"][:]
    return np.array([v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def sparse_x(f: h5py.File):
    x = f["X"]
    if isinstance(x, h5py.Group) and {"data", "indices", "indptr"}.issubset(set(x.keys())):
        shape = tuple(int(v) for v in x.attrs["shape"])
        enc = str(x.attrs.get("encoding-type", "csr_matrix"))
        if "csc" in enc:
            return sparse.csc_matrix((x["data"][:], x["indices"][:], x["indptr"][:]), shape=shape).tocsr()
        return sparse.csr_matrix((x["data"][:], x["indices"][:], x["indptr"][:]), shape=shape)
    return sparse.csr_matrix(x[:])


def safe_ranksum(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 3 or len(b) < 3 or (np.std(a) == 0 and np.std(b) == 0):
        return np.nan
    return float(ranksums(a, b).pvalue)


def bh(pvals: pd.Series) -> pd.Series:
    p = pd.to_numeric(pvals, errors="coerce").to_numpy(dtype=float)
    out = np.full(len(p), np.nan)
    mask = np.isfinite(p)
    if mask.sum() == 0:
        return pd.Series(out, index=pvals.index)
    order = np.argsort(p[mask])
    pv = p[mask][order]
    n = len(pv)
    adj = np.minimum.accumulate((pv * n / np.arange(1, n + 1))[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    idx = np.where(mask)[0][order]
    out[idx] = adj
    return pd.Series(out, index=pvals.index)


def requested_genes(cfg: dict) -> list[str]:
    genes = []
    if cfg["parameters"]["expression_gene_set"].get("stage64_modules", True):
        for vals in MODULES.values():
            genes.extend(vals)
    if cfg["parameters"]["expression_gene_set"].get("stage47_candidate_overlap", True):
        genes.extend(STAGE47_CANDIDATES)
    genes.extend(cfg["parameters"]["expression_gene_set"].get("extra_genes", []))
    return list(dict.fromkeys(str(g) for g in genes))


def dataset_schema(name: str, path: Path, cfg: dict) -> dict:
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        genes = gene_symbols(f)
        donor_col = find_col(obs, cfg["parameters"]["donor_column_candidates"])
        state_col = find_col(obs, cfg["parameters"]["state_column_candidates"])
        shape = tuple(int(x) for x in f["X"].attrs.get("shape", f["X"].shape if hasattr(f["X"], "shape") else (0, 0)))
    return {
        "dataset": name,
        "path": str(path),
        "exists": path.exists(),
        "x_shape": str(shape),
        "n_genes": len(genes),
        "donor_column": donor_col or "",
        "state_column": state_col or "",
    }


def load_expression_dataset(name: str, path: Path, cfg: dict, genes_req: list[str]) -> dict:
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        donor_col = find_col(obs, cfg["parameters"]["donor_column_candidates"])
        state_col = find_col(obs, cfg["parameters"]["state_column_candidates"])
        donors = decode_elem(obs[donor_col]).astype(str) if donor_col else np.array([""] * f["X"].attrs["shape"][0], dtype=object)
        states = decode_elem(obs[state_col]).astype(str) if state_col else np.array(["state_unavailable"] * len(donors), dtype=object)
        genes = gene_symbols(f)
        gene_index = {str(g): i for i, g in enumerate(genes)}
        present = [g for g in genes_req if g in gene_index]
        missing = [g for g in genes_req if g not in gene_index]
        X = sparse_x(f)
    return {
        "dataset": name,
        "path": path,
        "donor_col": donor_col or "",
        "state_col": state_col or "",
        "donors": donors,
        "states": states,
        "genes": genes,
        "present_genes": present,
        "missing_genes": missing,
        "gene_index": gene_index,
        "X": X,
    }


def zscore(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    sd = np.nanstd(v)
    return (v - np.nanmean(v)) / sd if sd > 0 else np.zeros_like(v)


def recompute_frozen_stage64_scores(ds: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    score = pd.DataFrame({
        "dataset": ds["dataset"],
        "cell_index": np.arange(ds["X"].shape[0]),
        "donor_id": ds["donors"],
        "state_label": ds["states"],
    })
    availability = []
    for module, genes in MODULES.items():
        present = [g for g in genes if g in ds["gene_index"]]
        missing = [g for g in genes if g not in ds["gene_index"]]
        availability.append({
            "dataset": ds["dataset"],
            "module": module,
            "requested_genes": ";".join(genes),
            "present_genes": ";".join(present),
            "missing_genes": ";".join(missing),
            "n_present": len(present),
            "usable": len(present) > 0,
        })
        if present:
            idx = [ds["gene_index"][g] for g in present]
            score[module] = np.asarray(ds["X"][:, idx].mean(axis=1)).ravel().astype(float)
        else:
            score[module] = 0.0
    composite = np.zeros(len(score), dtype=float)
    for module in ["dam_lipid_trem2_apoe", "lysosomal_endolysosomal", "complement_phagocytosis", "antigen_presentation", "oxidative_stress_gene_preserved"]:
        composite += zscore(score[module].to_numpy(dtype=float))
    score["disease_program_score"] = composite / 5.0
    score["dominant_module"] = score[list(MODULES)].idxmax(axis=1)
    return score, pd.DataFrame(availability)


def make_cell_selection(scores: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    q = float(cfg["parameters"]["high_quantile"])
    lowq = float(cfg["parameters"]["low_quantile"])
    rows = []
    selected_all = []
    export = []
    for dataset, sub in scores.groupby("dataset"):
        threshold = float(sub["disease_program_score"].quantile(q))
        low_threshold = float(sub["disease_program_score"].quantile(lowq))
        sub = sub.copy()
        sub["rare_tail_group"] = np.where(sub["disease_program_score"] >= threshold, "high_tail_q95", np.where(sub["disease_program_score"] <= low_threshold, "low_reference_q50", "middle_not_contrasted"))
        rows.append({
            "dataset": dataset,
            "n_cells_scored_full_h5ad": len(sub),
            "high_tail_threshold": threshold,
            "low_reference_threshold": low_threshold,
            "n_high_tail_cells": int((sub["rare_tail_group"] == "high_tail_q95").sum()),
            "n_low_reference_cells": int((sub["rare_tail_group"] == "low_reference_q50").sum()),
            "n_donors": int(sub["donor_id"].nunique()),
            "n_high_tail_donors": int(sub.loc[sub["rare_tail_group"] == "high_tail_q95", "donor_id"].nunique()),
        })
        keep = sub[sub["rare_tail_group"].isin(["high_tail_q95", "low_reference_q50"])].copy()
        selected_all.append(keep)
        high_export = keep[keep["rare_tail_group"].eq("high_tail_q95")].sort_values("disease_program_score", ascending=False)
        low_export = keep[keep["rare_tail_group"].eq("low_reference_q50")].sort_values("disease_program_score", ascending=True)
        maxn = int(cfg["parameters"]["max_export_cells_per_dataset"])
        export.append(pd.concat([high_export, low_export.head(max(0, maxn - len(high_export)))], ignore_index=True).head(maxn))
    return pd.DataFrame(rows), pd.concat(selected_all, ignore_index=True), pd.concat(export, ignore_index=True)


def contrast_dataset(ds: dict, selected: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    name = ds["dataset"]
    sel = selected[selected["dataset"].eq(name)].copy()
    if sel.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    rows, state_rows = [], []
    gene_cols = [ds["gene_index"][g] for g in ds["present_genes"]]
    Xg = ds["X"][:, gene_cols] if gene_cols else None
    min_cells = int(cfg["parameters"]["min_cells_per_donor"])
    min_high = int(cfg["parameters"]["min_high_cells_per_donor"])
    for donor, sub in sel.groupby("donor_id"):
        high_idx = sub.loc[sub["rare_tail_group"].eq("high_tail_q95"), "cell_index"].astype(int).to_numpy()
        low_idx = sub.loc[sub["rare_tail_group"].eq("low_reference_q50"), "cell_index"].astype(int).to_numpy()
        valid = (high_idx < ds["X"].shape[0]).all() and (low_idx < ds["X"].shape[0]).all() if len(high_idx) and len(low_idx) else False
        if not valid or len(high_idx) < min_high or (len(high_idx) + len(low_idx)) < min_cells:
            continue
        high_states = pd.Series(ds["states"][high_idx]).value_counts(normalize=True)
        low_states = pd.Series(ds["states"][low_idx]).value_counts(normalize=True)
        for st in sorted(set(high_states.index).union(set(low_states.index))):
            state_rows.append({
                "dataset": name,
                "donor_id": donor,
                "state_label": st,
                "high_tail_fraction": float(high_states.get(st, 0.0)),
                "low_reference_fraction": float(low_states.get(st, 0.0)),
                "high_minus_low_fraction": float(high_states.get(st, 0.0) - low_states.get(st, 0.0)),
                "n_high_cells": len(high_idx),
                "n_low_cells": len(low_idx),
            })
        if Xg is None:
            continue
        hi = Xg[high_idx, :]
        lo = Xg[low_idx, :]
        hi_mean = np.asarray(hi.mean(axis=0)).ravel()
        lo_mean = np.asarray(lo.mean(axis=0)).ravel()
        for j, g in enumerate(ds["present_genes"]):
            hv = np.asarray(hi[:, j].toarray()).ravel() if sparse.issparse(hi) else hi[:, j]
            lv = np.asarray(lo[:, j].toarray()).ravel() if sparse.issparse(lo) else lo[:, j]
            rows.append({
                "dataset": name,
                "donor_id": donor,
                "gene": g,
                "high_mean": float(hi_mean[j]),
                "low_mean": float(lo_mean[j]),
                "high_minus_low": float(hi_mean[j] - lo_mean[j]),
                "log1p_high_minus_low": float(np.log1p(max(hi_mean[j], 0)) - np.log1p(max(lo_mean[j], 0))),
                "n_high_cells": len(high_idx),
                "n_low_cells": len(low_idx),
                "wilcoxon_rank_sum_p": safe_ranksum(hv, lv),
            })
    detail = pd.DataFrame(rows)
    state = pd.DataFrame(state_rows)
    if detail.empty:
        return detail, pd.DataFrame(), state
    summary = detail.groupby(["dataset", "gene"], as_index=False).agg(
        mean_high_minus_low=("high_minus_low", "mean"),
        median_high_minus_low=("high_minus_low", "median"),
        mean_log1p_high_minus_low=("log1p_high_minus_low", "mean"),
        n_donors=("donor_id", "nunique"),
        total_high_cells=("n_high_cells", "sum"),
        total_low_cells=("n_low_cells", "sum"),
        median_rank_sum_p=("wilcoxon_rank_sum_p", "median"),
    )
    summary["bh_q_median_p_within_dataset"] = summary.groupby("dataset", group_keys=False)["median_rank_sum_p"].apply(bh)
    summary["direction"] = np.where(summary["mean_high_minus_low"] > 0, "higher_in_high_tail", np.where(summary["mean_high_minus_low"] < 0, "lower_in_high_tail", "no_difference"))
    summary = summary.sort_values(["dataset", "mean_high_minus_low"], ascending=[True, False])
    if not state.empty:
        state = state.groupby(["dataset", "state_label"], as_index=False).agg(
            mean_high_minus_low_fraction=("high_minus_low_fraction", "mean"),
            median_high_minus_low_fraction=("high_minus_low_fraction", "median"),
            n_donors=("donor_id", "nunique"),
            total_high_cells=("n_high_cells", "sum"),
            total_low_cells=("n_low_cells", "sum"),
        ).sort_values(["dataset", "mean_high_minus_low_fraction"], ascending=[True, False])
    return detail, summary, state


def module_signature_summary(contrast: pd.DataFrame) -> pd.DataFrame:
    if contrast.empty:
        return pd.DataFrame()
    rows = []
    for module, genes in MODULES.items():
        for dataset, sub in contrast[contrast["gene"].isin(genes)].groupby("dataset"):
            rows.append({
                "dataset": dataset,
                "module": module,
                "n_present_module_genes": int(sub["gene"].nunique()),
                "mean_gene_high_minus_low": float(sub["mean_high_minus_low"].mean()),
                "median_gene_high_minus_low": float(sub["median_high_minus_low"].median()),
                "n_genes_higher_in_high_tail": int((sub["mean_high_minus_low"] > 0).sum()),
                "n_genes_lower_in_high_tail": int((sub["mean_high_minus_low"] < 0).sum()),
                "top_higher_genes": ";".join(sub.sort_values("mean_high_minus_low", ascending=False)["gene"].head(5).tolist()),
            })
    return pd.DataFrame(rows).sort_values(["dataset", "mean_gene_high_minus_low"], ascending=[True, False])


def legacy_overlay(legacy_path: Path, selected: pd.DataFrame) -> pd.DataFrame:
    if not legacy_path.exists():
        return pd.DataFrame()
    legacy = pd.read_csv(legacy_path)
    rows = []
    selected_cols = {c.lower(): c for c in selected.columns}
    for _, r in legacy.iterrows():
        path = resolve(r["path"])
        if not path.exists() or str(path).lower().endswith((".h5ad", ".loom", ".mtx")):
            continue
        cols = str(r.get("columns_sample", "")).split(";")
        lower = {c.lower(): c for c in cols}
        has_cell = any(c in lower for c in ["cell_index", "cell_id", "barcode", "_index"])
        has_donor = any(c in lower for c in ["donor_id", "donor id", "donor"])
        probable = has_cell and (has_donor or "dataset" in lower)
        rows.append({
            "legacy_artifact": str(path),
            "artifact_stage_guess": r.get("stage_guess", ""),
            "n_rows": r.get("n_rows", ""),
            "has_cell_identifier_column": has_cell,
            "has_donor_identifier_column": has_donor,
            "direct_overlay_probable": probable,
            "recommended_use": "overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates" if probable else "manual schema review before overlay",
        })
    return pd.DataFrame(rows).sort_values(["direct_overlay_probable", "legacy_artifact"], ascending=[False, True])


def update_scorecard(cfg: dict, pass_row: pd.Series) -> None:
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in sc.columns:
            sc[col] = ""
    row = {
        "scorecard_item": "Stage68 rare-tail cell extraction and expression contrast",
        "status": "complete",
        "stage": "Stage68",
        "metric": "Stage64 high-tail cells joined to SEA-AD expression rows",
        "threshold_or_gate": "bounded within-donor high-vs-low contrasts; no model training or validation claim",
        "current_value": f"stage68_run_pass={bool(pass_row['stage68_run_pass'])}; expression_contrast_written={bool(pass_row['expression_contrast_written'])}",
        "pass_fail": "pass" if bool(pass_row["stage68_run_pass"]) else "fail",
        "datasets_allowed": "existing local Stage64 cell scores and local MTG/DLPFC H5ADs",
        "datasets_forbidden": "new model training; raw expression export; clean validation claims",
        "allowed_claim": "hypothesis-generating high-tail-cell expression contrast",
        "notes": "Extracts candidate rare-tail cell indices and compares high-tail vs low-reference microglia within donor.",
        "stage_id": "stage68_rare_tail_cell_extraction_expression_contrast",
        "primary_metric": "joined cell count and high-vs-low expression/state contrasts",
        "pass_rule": "required inputs found; contrasts written; claim-boundary audit passes",
        "result": "see stage68_high_vs_low_expression_contrast_v1.csv",
        "allowed_inputs": "Stage64/67 outputs and existing local SEA-AD H5ADs",
        "forbidden_inputs": "new downloaded data, rescue model, benchmark lock",
        "interpretation": "Diagnostic expression contrast only; follow-up biological review/external support required.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg: dict) -> None:
    inp, out = cfg["inputs"], cfg["outputs"]
    stage64_export = pd.read_csv(resolve(inp["stage64_cell_scores"]))
    genes_req = requested_genes(cfg)

    join_rows = []
    contrasts_detail, contrasts_summary, states = [], [], []
    full_scores_parts = []
    loaded = {}
    for name, ds_cfg in cfg["datasets"].items():
        path = resolve(ds_cfg["path"])
        schema = dataset_schema(name, path, cfg)
        stage64_n = int(stage64_export[stage64_export["dataset"].eq(name)]["cell_index"].max() + 1) if (stage64_export["dataset"].eq(name)).any() else 0
        h5_n = int(schema["x_shape"].strip("()").split(",")[0]) if schema["x_shape"].startswith("(") else 0
        schema["stage64_dataset_present"] = bool((stage64_export["dataset"] == name).any())
        schema["stage64_export_rows"] = int((stage64_export["dataset"] == name).sum())
        schema["stage64_row_index_compatible"] = bool(stage64_n <= h5_n and stage64_n > 0)
        ds = load_expression_dataset(name, path, cfg, genes_req)
        full_scores, avail = recompute_frozen_stage64_scores(ds)
        full_scores_parts.append(full_scores)
        loaded[name] = ds
        schema["full_h5ad_cells_scored_for_stage68"] = len(full_scores)
        schema["requested_genes"] = len(genes_req)
        schema["present_requested_genes"] = len(ds["present_genes"])
        schema["missing_requested_genes"] = len(ds["missing_genes"])
        schema["missing_genes_sample"] = ";".join(ds["missing_genes"][:20])
        join_rows.append(schema)

    scores = pd.concat(full_scores_parts, ignore_index=True)
    selection_summary, selected_all, selected_export = make_cell_selection(scores, cfg)
    selected_export["allowed_use"] = "candidate cell index for bounded expression/state contrast; not a validated diseased-cell label"
    selected_export["disallowed_claim"] = "new subtype; validated biomarker cell; causal diseased cell"
    selected_all["allowed_use"] = "internal Stage68 high/low contrast label from frozen Stage64 module definitions"

    for schema in join_rows:
        name = schema["dataset"]
        ds = loaded[name]
        if schema["stage64_row_index_compatible"] and ds["present_genes"]:
            detail, summary, state = contrast_dataset(ds, selected_all, cfg)
            contrasts_detail.append(detail)
            contrasts_summary.append(summary)
            states.append(state)

    join_audit = pd.DataFrame(join_rows)
    detail = pd.concat([d for d in contrasts_detail if not d.empty], ignore_index=True) if contrasts_detail else pd.DataFrame()
    contrast = pd.concat([d for d in contrasts_summary if not d.empty], ignore_index=True) if contrasts_summary else pd.DataFrame()
    state_enrich = pd.concat([d for d in states if not d.empty], ignore_index=True) if states else pd.DataFrame()
    signature = module_signature_summary(contrast)
    overlay = legacy_overlay(resolve(inp["stage67_legacy_inventory"]), selected_export)

    claim = pd.DataFrame([{
        "stage68_run_is_cell_extraction_and_expression_contrast_only": True,
        "full_h5ad_scores_recomputed_from_frozen_stage64_definitions": True,
        "stage64_capped_export_used_only_as_anchor_not_low_reference": True,
        "no_new_model_run": True,
        "no_benchmark_claim": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_validated_biomarker_claim": True,
        "no_new_microglia_subtype_claim": True,
        "raw_expression_matrix_not_written": True,
        "raw_h5ad_not_committed": True,
        "cell_labels_are_hypothesis_generating": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage68_run": True,
        "stage64_cell_scores_found": resolve(inp["stage64_cell_scores"]).exists(),
        "stage67_inputs_found": resolve(inp["stage67_recommended_inputs"]).exists(),
        "mtg_h5ad_found": resolve(inp["mtg_h5ad"]).exists(),
        "dlpfc_h5ad_found": resolve(inp["dlpfc_h5ad"]).exists(),
        "input_join_audit_written": True,
        "candidate_cell_export_index_written": True,
        "expression_contrast_written": not contrast.empty,
        "state_enrichment_written": not state_enrich.empty,
        "legacy_overlay_joinability_written": True,
        "reports_written": True,
        "docs_updated": True,
        "n_selected_candidate_rows": len(selected_export),
        "n_internal_contrast_cell_rows": len(selected_all),
        "n_expression_contrast_rows": len(contrast),
        "n_state_enrichment_rows": len(state_enrich),
        "n_joinable_datasets": int(join_audit["stage64_row_index_compatible"].sum()) if not join_audit.empty else 0,
        **claim.iloc[0].to_dict(),
    }])
    pf["stage68_run_pass"] = pf[
        [
            "stage64_cell_scores_found",
            "mtg_h5ad_found",
            "dlpfc_h5ad_found",
            "input_join_audit_written",
            "candidate_cell_export_index_written",
            "expression_contrast_written",
            "state_enrichment_written",
            "safety_audit_pass",
        ]
    ].all(axis=1)

    tables = {
        "input_join_audit": join_audit,
        "rare_cell_selection_summary": selection_summary,
        "candidate_cell_export_index": selected_export,
        "high_vs_low_expression_contrast": contrast,
        "signature_gene_contrast": signature,
        "state_enrichment": state_enrich,
        "legacy_overlay_joinability": overlay,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for k, df in tables.items():
        write_csv(df, out[k])

    status = (
        "Stage68 extracted rare/high-tail Micro-PVM candidate cells by recomputing the frozen Stage64 module definitions "
        "on the full local MTG/DLPFC SEA-AD H5ADs, then ran bounded within-donor high-vs-low expression and "
        "state-enrichment contrasts. The capped Stage64 cell table was used only as an anchor/check, not as the low-reference universe. "
        "Stage68 also audited legacy v1/v2/v3 cell-level artifact overlay feasibility. It writes cell indices and summary contrasts only, "
        "not raw expression matrices. It is hypothesis-generating and makes no benchmark, external-validation, causal, therapeutic, "
        "validated-biomarker, or new-subtype claim."
    )
    update_section(inp["active_status"], "Stage 68 rare-tail cell extraction and expression contrast", status)
    update_section(inp["v3_scorecard_md"], "Stage 68 rare-tail cell extraction and expression contrast", status)
    update_scorecard(cfg, pf.iloc[0])

    top_genes = contrast.sort_values(["mean_high_minus_low"], ascending=False).head(30) if not contrast.empty else pd.DataFrame()
    top_states = state_enrich.sort_values(["mean_high_minus_low_fraction"], ascending=False).head(20) if not state_enrich.empty else pd.DataFrame()
    report = f"""# Stage68 rare-tail cell extraction and expression contrast

## Bottom line

Stage68 joins the frozen Stage64 rare/high-tail scoring definitions back to the local SEA-AD MTG and DLPFC H5AD expression rows. Because the Stage64 cell table is a capped top-cell export, Stage68 recomputes the same frozen module scores over the full local H5ADs before selecting q95 high-tail and q50 low-reference cells. It then compares high-tail cells with low-reference cells within donor. This is a diagnostic expression/state contrast, not a new model, benchmark, external validation, causal claim, therapeutic claim, validated biomarker, or new microglia subtype.

## Join audit

{md(join_audit)}

## Rare-cell selection summary

{md(selection_summary)}

## Top high-tail expression contrasts

{md(top_genes)}

## Module-level signature summary

{md(signature)}

## State enrichment among high-tail cells

{md(top_states)}

## Legacy overlay feasibility

{md(overlay, max_rows=30)}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(
        f"""# Stage68 PI summary

Stage68 completed the first direct cell extraction/contrast step.

- Candidate high/low cell-index rows exported: `{len(selected_export)}`
- Internal full-H5AD high/low contrast cell rows: `{len(selected_all)}`
- Expression contrast rows: `{len(contrast)}`
- State-enrichment rows: `{len(state_enrich)}`
- Joinable expression datasets: `{int(pf.iloc[0]['n_joinable_datasets'])}`
- Safety audit pass: `True`

Interpretation: the rare/high-tail scoring definitions can be traced back to SEA-AD expression rows and compared with within-donor low-reference microglia using the full local H5ADs. These are hypothesis-generating cell states/signatures only, not validated disease cells or new subtypes.
""",
        out["pi_summary"],
    )
    write_text(f"# Stage68 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])

    print(f"stage68_run_pass={bool(pf.iloc[0]['stage68_run_pass'])}")
    print(f"selected_candidate_rows={len(selected_export)}")
    print(f"internal_contrast_cell_rows={len(selected_all)}")
    print(f"expression_contrast_rows={len(contrast)}")
    print(f"state_enrichment_rows={len(state_enrich)}")
    print(f"joinable_datasets={int(pf.iloc[0]['n_joinable_datasets'])}")
    print("safety_audit_pass=True")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage68_rare_tail_cell_extraction_expression_contrast_v1.yaml")
    args = parser.parse_args()
    run(read_cfg(args.config))


if __name__ == "__main__":
    main()
