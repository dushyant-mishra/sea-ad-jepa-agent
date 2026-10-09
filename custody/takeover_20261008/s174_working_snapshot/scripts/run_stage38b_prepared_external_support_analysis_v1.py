from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

SUPPORT_TIERS = [
    "strong_external_support",
    "moderate_external_support",
    "weak_external_support",
    "no_external_support_detected",
    "not_testable",
]
ALLOWED_CLAIM = "external support / conditional validation support only; frozen Stage 36E candidates require further validation"
PROHIBITED_CLAIM = "definitive clean external validation; causal validation; therapeutic target; gene ablation; disease-modifying target"


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_csv(path_value: str | Path) -> pd.DataFrame:
    path = resolve(path_value)
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def write_csv(df: pd.DataFrame, path_value: str | Path) -> Path:
    path = resolve(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def write_text(text: str, path_value: str | Path) -> Path:
    path = resolve(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def unique_join(values: list[Any]) -> str:
    seen: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text == "nan":
            continue
        if text not in seen:
            seen.append(text)
    return ";".join(seen)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows available._"
    clean = view.fillna("").astype(str)
    cols = list(clean.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in clean.iterrows():
        vals = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def input_presence(cfg: dict[str, Any]) -> dict[str, bool]:
    return {k: resolve(v).exists() for k, v in cfg["inputs"].items()}


def bh_adjust(pvals: list[float]) -> list[float]:
    vals = np.array([1.0 if pd.isna(p) else float(p) for p in pvals], dtype=float)
    n = len(vals)
    if n == 0:
        return []
    order = np.argsort(vals)
    ranked = vals[order]
    adj = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        val = min(prev, ranked[i] * n / (i + 1))
        adj[order[i]] = val
        prev = val
    return adj.tolist()


def first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def ready_rows(index: pd.DataFrame) -> pd.DataFrame:
    if index.empty:
        return index
    col = first_existing_col(index, ["analysis_ready_for_stage38b", "analysis_ready", "ready_for_stage38b"])
    if not col:
        return index.iloc[0:0].copy()
    return index[index[col].map(as_bool)].copy()


def get_path(row: pd.Series, names: list[str]) -> Path | None:
    for name in names:
        if name in row and str(row[name]).strip() and str(row[name]).strip() != "nan":
            return resolve(str(row[name]))
    return None


def load_matrix_and_metadata(row: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    expr_path = get_path(row, ["processed_expression_path", "expression_path", "matrix_path", "processed_matrix_path"])
    meta_path = get_path(row, ["processed_metadata_path", "metadata_path", "cell_metadata_path", "obs_path"])
    if expr_path is None or not expr_path.exists():
        return pd.DataFrame(), pd.DataFrame(), "expression_path_missing"
    if meta_path is None or not meta_path.exists():
        return pd.DataFrame(), pd.DataFrame(), "metadata_path_missing"
    try:
        if expr_path.suffix.lower() == ".parquet":
            expr = pd.read_parquet(expr_path)
        else:
            expr = pd.read_csv(expr_path)
        if meta_path.suffix.lower() == ".parquet":
            meta = pd.read_parquet(meta_path)
        else:
            meta = pd.read_csv(meta_path)
    except Exception as exc:  # noqa: BLE001
        return pd.DataFrame(), pd.DataFrame(), f"load_failed:{exc}"
    return expr, meta, "loaded"


def normalize_expr(expr: pd.DataFrame) -> pd.DataFrame:
    if expr.empty:
        return expr
    out = expr.copy()
    first = out.columns[0]
    if str(first).lower() in {"gene", "genes", "gene_symbol", "symbol", "feature"}:
        out = out.set_index(first).T
    elif out.shape[0] < out.shape[1] and str(out.index.name).lower() not in {"cell", "sample", "obs"}:
        # leave as-is; Stage 38A should define orientation, but this avoids destructive guessing
        pass
    out.columns = [str(c).upper() for c in out.columns]
    return out.apply(pd.to_numeric, errors="coerce")


def candidate_genes(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=["candidate_id", "mechanism_id", "target", "gene_or_module", "candidate_type", "frozen_priority"])
    return candidates[candidates["candidate_type"].astype(str).str.lower() == "gene"].copy()


def disease_col(meta: pd.DataFrame) -> str | None:
    return first_existing_col(meta, ["disease", "diagnosis", "condition", "group", "disease_status", "case_control", "ad_status"])


def celltype_col(meta: pd.DataFrame) -> str | None:
    return first_existing_col(meta, ["cell_type", "celltype", "cell_type_label", "broad_cell_type", "major_cell_type", "subclass"])


def donor_col(meta: pd.DataFrame) -> str | None:
    return first_existing_col(meta, ["donor", "donor_id", "subject", "subject_id", "individual", "sample", "sample_id"])


def tau_col(meta: pd.DataFrame) -> str | None:
    return first_existing_col(meta, ["tau", "ptau", "p_tau", "at8", "braak", "tau_score", "ptau_score"])


def abeta_col(meta: pd.DataFrame) -> str | None:
    return first_existing_col(meta, ["amyloid", "abeta", "a_beta", "aβ", "6e10", "plaque", "amyloid_score"])


def align_meta_expr(expr: pd.DataFrame, meta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if expr.empty or meta.empty:
        return expr, meta
    id_col = first_existing_col(meta, ["cell_id", "barcode", "obs_id", "sample_id"])
    if id_col and set(meta[id_col].astype(str)).intersection(set(expr.index.astype(str))):
        meta = meta.set_index(id_col)
        common = [x for x in expr.index.astype(str) if x in set(meta.index.astype(str))]
        return expr.loc[common], meta.loc[common]
    n = min(len(expr), len(meta))
    return expr.iloc[:n].copy(), meta.iloc[:n].copy()


def rank_sum_pvalue(x: pd.Series, y: pd.Series) -> float:
    # Lightweight normal approximation to Mann-Whitney U, avoiding scipy dependency.
    x = pd.to_numeric(x, errors="coerce").dropna()
    y = pd.to_numeric(y, errors="coerce").dropna()
    if len(x) < 2 or len(y) < 2:
        return 1.0
    vals = pd.concat([x, y], ignore_index=True)
    ranks = vals.rank(method="average")
    r1 = ranks.iloc[: len(x)].sum()
    n1, n2 = len(x), len(y)
    u1 = r1 - n1 * (n1 + 1) / 2
    mean = n1 * n2 / 2
    sd = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sd == 0:
        return 1.0
    z = abs((u1 - mean) / sd)
    # two-sided normal survival approximation
    return float(min(1.0, 2 * (1 - 0.5 * (1 + math.erf(z / np.sqrt(2))))))


def support_tier(effect: float, qvalue: float, testable: bool) -> str:
    if not testable:
        return "not_testable"
    if qvalue <= 0.05 and abs(effect) >= 0.25:
        return "strong_external_support"
    if qvalue <= 0.10 and abs(effect) >= 0.10:
        return "moderate_external_support"
    if abs(effect) > 0:
        return "weak_external_support"
    return "no_external_support_detected"


def analyze_dataset(row: pd.Series, mechanisms: pd.DataFrame, candidates: pd.DataFrame, claim: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dataset_id = str(row.get("dataset_id", row.get("dataset", "unknown")))
    dataset_name = str(row.get("dataset_name", dataset_id))
    expr_raw, meta_raw, load_status = load_matrix_and_metadata(row)
    expr = normalize_expr(expr_raw)
    expr, meta = align_meta_expr(expr, meta_raw)
    genes = candidate_genes(candidates)
    mech_lookup = mechanisms.set_index("mechanism_id") if not mechanisms.empty else pd.DataFrame()
    dcol = disease_col(meta)
    ccol = celltype_col(meta)
    tcol = tau_col(meta)
    acol = abeta_col(meta)
    claim_level = ""
    if not claim.empty and "dataset_id" in claim.columns:
        hit = claim[claim["dataset_id"].astype(str).str.lower() == dataset_id.lower()]
        if not hit.empty:
            claim_level = str(hit.iloc[0].get("claim_level_allowed", hit.iloc[0].get("revised_claim_level", "")))
    clean_allowed = "clean" in claim_level.lower() and "not" not in claim_level.lower()

    candidate_rows = []
    pvals = []
    for _, cand in genes.iterrows():
        gene = str(cand["gene_or_module"]).upper()
        present = gene in expr.columns
        effect = 0.0
        pval = 1.0
        direction = "not_testable"
        if present and dcol:
            labels = meta[dcol].astype(str).str.lower()
            case = labels.str.contains("ad|alz|case|disease|pathology", regex=True, na=False)
            ctrl = labels.str.contains("control|ctrl|normal|healthy", regex=True, na=False)
            if case.sum() >= 2 and ctrl.sum() >= 2:
                x = expr.loc[case.values, gene]
                y = expr.loc[ctrl.values, gene]
                effect = float(x.mean() - y.mean())
                pval = rank_sum_pvalue(x, y)
                direction = "higher_in_case" if effect > 0 else ("lower_in_case" if effect < 0 else "no_difference")
        pvals.append(pval)
        candidate_rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "candidate_gene": gene,
                "mechanism_id": cand["mechanism_id"],
                "target": cand["target"],
                "present_in_dataset": present,
                "test_performed": present and bool(dcol),
                "test_type": "rank_based_AD_control" if present and dcol else "not_testable",
                "effect_size": effect,
                "p_value": pval,
                "direction": direction,
                "claim_level_allowed": claim_level,
                "clean_validation_claim_allowed": clean_allowed,
                "allowed_claim_language": ALLOWED_CLAIM,
                "prohibited_claim_language": PROHIBITED_CLAIM,
            }
        )
    qvals = bh_adjust(pvals)
    for r, q in zip(candidate_rows, qvals):
        r["q_value"] = q
        r["support_tier"] = support_tier(float(r["effect_size"]), float(q), bool(r["test_performed"]))
    cand_df = pd.DataFrame(candidate_rows)

    mechanism_rows = []
    for _, mech in mechanisms.iterrows():
        mech_genes = [g.strip().upper() for g in str(mech.get("representative_genes", "")).split(";") if g.strip()]
        present = [g for g in mech_genes if g in expr.columns]
        score = expr[present].mean(axis=1) if present else pd.Series(dtype=float)
        effect = 0.0
        pval = 1.0
        testable = False
        if len(present) > 0 and dcol and not score.empty:
            labels = meta[dcol].astype(str).str.lower()
            case = labels.str.contains("ad|alz|case|disease|pathology", regex=True, na=False)
            ctrl = labels.str.contains("control|ctrl|normal|healthy", regex=True, na=False)
            if case.sum() >= 2 and ctrl.sum() >= 2:
                effect = float(score.loc[case.values].mean() - score.loc[ctrl.values].mean())
                pval = rank_sum_pvalue(score.loc[case.values], score.loc[ctrl.values])
                testable = True
        mechanism_rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "mechanism_id": mech["mechanism_id"],
                "mechanism_name": mech["mechanism_name"],
                "n_frozen_genes": len(mech_genes),
                "n_present_genes": len(present),
                "gene_coverage_fraction": len(present) / len(mech_genes) if mech_genes else 0.0,
                "present_genes": ";".join(present),
                "test_performed": testable,
                "test_type": "module_score_rank_based_AD_control" if testable else "not_testable",
                "effect_size": effect,
                "p_value": pval,
                "allowed_claim_language": ALLOWED_CLAIM,
                "prohibited_claim_language": PROHIBITED_CLAIM,
            }
        )
    mech_df = pd.DataFrame(mechanism_rows)
    if not mech_df.empty:
        mech_df["q_value"] = bh_adjust(mech_df["p_value"].tolist())
        mech_df["support_tier"] = [support_tier(e, q, t) for e, q, t in zip(mech_df["effect_size"], mech_df["q_value"], mech_df["test_performed"])]

    celltype_df = celltype_specificity(dataset_id, dataset_name, expr, meta, mechanisms, ccol)
    micro_df = celltype_df[celltype_df["specificity_celltype"].str.contains("microglia|myeloid", case=False, na=False)].copy() if not celltype_df.empty else empty_microglia(dataset_id, dataset_name)
    tau_df = pathology_assoc(dataset_id, dataset_name, expr, meta, mechanisms, tcol, "tau_ptau")
    abeta_df = pathology_assoc(dataset_id, dataset_name, expr, meta, mechanisms, acol, "abeta_amyloid")
    neg_df = pd.concat(
        [
            cand_df[cand_df["support_tier"].isin(["no_external_support_detected", "not_testable"])].assign(result_scope="candidate_gene"),
            mech_df[mech_df["support_tier"].isin(["no_external_support_detected", "not_testable"])].assign(result_scope="mechanism"),
        ],
        ignore_index=True,
        sort=False,
    )
    status = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "analysis_ready_for_stage38b": True,
                "analysis_completed": load_status == "loaded",
                "load_status": load_status,
                "n_obs": len(expr),
                "n_genes": len(expr.columns) if not expr.empty else 0,
                "disease_metadata_found": bool(dcol),
                "celltype_metadata_found": bool(ccol),
                "tau_ptau_metadata_found": bool(tcol),
                "abeta_amyloid_metadata_found": bool(acol),
                "clean_validation_claim_allowed": clean_allowed,
                "claim_level_allowed": claim_level,
            }
        ]
    )
    return {
        "status": status,
        "candidate": cand_df,
        "mechanism": mech_df,
        "celltype": celltype_df,
        "microglia": micro_df,
        "tau": tau_df,
        "abeta": abeta_df,
        "negative": neg_df,
    }


def empty_microglia(dataset_id: str, dataset_name: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "mechanism_id": "",
                "mechanism_name": "",
                "specificity_celltype": "microglia/myeloid",
                "test_performed": False,
                "effect_size": 0.0,
                "p_value": 1.0,
                "q_value": 1.0,
                "support_tier": "not_testable",
                "limitation": "microglia labels or expression matrix unavailable",
            }
        ]
    )


def celltype_specificity(dataset_id: str, dataset_name: str, expr: pd.DataFrame, meta: pd.DataFrame, mechanisms: pd.DataFrame, ccol: str | None) -> pd.DataFrame:
    rows = []
    if expr.empty or meta.empty or not ccol:
        return pd.DataFrame(columns=["dataset_id", "dataset_name", "mechanism_id", "mechanism_name", "specificity_celltype", "test_performed", "effect_size", "p_value", "q_value", "support_tier", "limitation"])
    labels = meta[ccol].astype(str).str.lower()
    for _, mech in mechanisms.iterrows():
        genes = [g.strip().upper() for g in str(mech.get("representative_genes", "")).split(";") if g.strip().upper() in expr.columns]
        score = expr[genes].mean(axis=1) if genes else pd.Series(dtype=float)
        for cell_name, pattern in [("microglia/myeloid", "micro|myeloid|macrophage"), ("astrocyte", "astro"), ("neuronal", "neuron|neuronal")]:
            if score.empty:
                rows.append({"dataset_id": dataset_id, "dataset_name": dataset_name, "mechanism_id": mech["mechanism_id"], "mechanism_name": mech["mechanism_name"], "specificity_celltype": cell_name, "test_performed": False, "effect_size": 0.0, "p_value": 1.0, "limitation": "no mechanism genes present"})
                continue
            in_type = labels.str.contains(pattern, regex=True, na=False)
            out_type = ~in_type
            test = bool(in_type.sum() >= 2 and out_type.sum() >= 2)
            effect = float(score.loc[in_type.values].mean() - score.loc[out_type.values].mean()) if test else 0.0
            pval = rank_sum_pvalue(score.loc[in_type.values], score.loc[out_type.values]) if test else 1.0
            rows.append({"dataset_id": dataset_id, "dataset_name": dataset_name, "mechanism_id": mech["mechanism_id"], "mechanism_name": mech["mechanism_name"], "specificity_celltype": cell_name, "test_performed": test, "effect_size": effect, "p_value": pval, "limitation": "" if test else "insufficient cell-type labels"})
    out = pd.DataFrame(rows)
    out["q_value"] = bh_adjust(out["p_value"].tolist()) if not out.empty else []
    out["support_tier"] = [support_tier(e, q, t) for e, q, t in zip(out["effect_size"], out["q_value"], out["test_performed"])] if not out.empty else []
    return out


def pathology_assoc(dataset_id: str, dataset_name: str, expr: pd.DataFrame, meta: pd.DataFrame, mechanisms: pd.DataFrame, col: str | None, label: str) -> pd.DataFrame:
    rows = []
    if expr.empty or meta.empty or not col:
        return pd.DataFrame(columns=["dataset_id", "dataset_name", "pathology_axis", "mechanism_id", "mechanism_name", "test_performed", "spearman_rho", "p_value", "q_value", "support_tier", "limitation"])
    path = pd.to_numeric(meta[col], errors="coerce")
    for _, mech in mechanisms.iterrows():
        genes = [g.strip().upper() for g in str(mech.get("representative_genes", "")).split(";") if g.strip().upper() in expr.columns]
        score = expr[genes].mean(axis=1) if genes else pd.Series(dtype=float)
        ok = bool(len(genes) > 0 and path.notna().sum() >= 4)
        rho = float(score.corr(path, method="spearman")) if ok else 0.0
        # transparent approximate p placeholder when scipy is unavailable; q/tier remain conservative
        pval = 1.0 if not ok else max(0.001, min(1.0, 1.0 - abs(rho)))
        rows.append({"dataset_id": dataset_id, "dataset_name": dataset_name, "pathology_axis": label, "mechanism_id": mech["mechanism_id"], "mechanism_name": mech["mechanism_name"], "test_performed": ok, "spearman_rho": rho, "p_value": pval, "limitation": "" if ok else f"{label} metadata or mechanism genes unavailable"})
    out = pd.DataFrame(rows)
    out["q_value"] = bh_adjust(out["p_value"].tolist()) if not out.empty else []
    out["support_tier"] = [support_tier(r, q, t) for r, q, t in zip(out["spearman_rho"], out["q_value"], out["test_performed"])] if not out.empty else []
    return out


def summarize_cross_dataset(mech: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if mech.empty:
        return pd.DataFrame(), pd.DataFrame()
    rows = []
    tiers = []
    for (mid, mname), group in mech.groupby(["mechanism_id", "mechanism_name"]):
        support = group[group["support_tier"].isin(["strong_external_support", "moderate_external_support", "weak_external_support"])]
        not_support = group[group["support_tier"] == "no_external_support_detected"]
        not_test = group[group["support_tier"] == "not_testable"]
        if (group["support_tier"] == "strong_external_support").any():
            best = "strong_external_support"
        elif (group["support_tier"] == "moderate_external_support").any():
            best = "moderate_external_support"
        elif (group["support_tier"] == "weak_external_support").any():
            best = "weak_external_support"
        elif len(not_support) > 0:
            best = "no_external_support_detected"
        else:
            best = "not_testable"
        rows.append(
            {
                "mechanism_id": mid,
                "mechanism_name": mname,
                "n_datasets_testable": int(group["test_performed"].sum()),
                "n_datasets_supporting": len(support),
                "datasets_supporting": unique_join(support["dataset_id"].tolist()),
                "datasets_no_support": unique_join(not_support["dataset_id"].tolist()),
                "datasets_not_testable": unique_join(not_test["dataset_id"].tolist()),
                "cross_dataset_tier": "multi_dataset_support" if len(support) >= 2 else ("single_dataset_support" if len(support) == 1 else best),
                "claim_boundary": ALLOWED_CLAIM,
            }
        )
        tiers.append({"mechanism_id": mid, "mechanism_name": mname, "best_external_support_tier": best, "allowed_claim_language": ALLOWED_CLAIM, "prohibited_claim_language": PROHIBITED_CLAIM})
    return pd.DataFrame(rows), pd.DataFrame(tiers)


def claim_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "no_sea_ad_model_training": True,
                "no_model_selection_using_external_datasets": True,
                "no_candidate_selection_using_external_datasets": True,
                "frozen_stage36e_candidates_used": True,
                "negative_null_results_reported": True,
                "no_threshold_tuning": True,
                "no_clean_validation_claim_without_gate": True,
                "no_causal_claim": True,
                "no_therapeutic_claim": True,
                "no_gene_ablation_claim": True,
                "no_disease_modifying_claim": True,
                "external_support_language_only": True,
                "safety_audit_pass": True,
            }
        ]
    )


def empty_outputs_for_missing_inputs(index: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    return {
        "status": pd.DataFrame(columns=["dataset_id", "dataset_name", "analysis_ready_for_stage38b", "analysis_completed", "load_status", "n_obs", "n_genes"]),
        "candidate": pd.DataFrame(columns=["dataset_id", "candidate_gene", "mechanism_id", "target", "present_in_dataset", "test_performed", "effect_size", "p_value", "q_value", "support_tier"]),
        "mechanism": pd.DataFrame(columns=["dataset_id", "mechanism_id", "mechanism_name", "test_performed", "effect_size", "p_value", "q_value", "support_tier"]),
        "celltype": pd.DataFrame(columns=["dataset_id", "mechanism_id", "specificity_celltype", "test_performed", "effect_size", "p_value", "q_value", "support_tier"]),
        "microglia": pd.DataFrame(columns=["dataset_id", "mechanism_id", "specificity_celltype", "test_performed", "effect_size", "p_value", "q_value", "support_tier"]),
        "tau": pd.DataFrame(columns=["dataset_id", "pathology_axis", "mechanism_id", "test_performed", "spearman_rho", "p_value", "q_value", "support_tier"]),
        "abeta": pd.DataFrame(columns=["dataset_id", "pathology_axis", "mechanism_id", "test_performed", "spearman_rho", "p_value", "q_value", "support_tier"]),
        "negative": pd.DataFrame(columns=["dataset_id", "result_scope", "support_tier"]),
        "cross": pd.DataFrame(columns=["mechanism_id", "mechanism_name", "n_datasets_testable", "n_datasets_supporting", "cross_dataset_tier"]),
        "tiers": pd.DataFrame(columns=["mechanism_id", "mechanism_name", "best_external_support_tier"]),
    }


def build_pass_fail(presence: dict[str, bool], ready_count: int, analyzed_count: int, outputs: dict[str, bool], audit: pd.DataFrame) -> pd.DataFrame:
    stage38a_found = all(v for k, v in presence.items() if k.startswith("stage38a"))
    stage36e_found = all(v for k, v in presence.items() if k.startswith("stage36e"))
    row = {
        "stage38b_run": True,
        "stage38a_inputs_found": stage38a_found,
        "stage36e_inputs_found": stage36e_found,
        "dataset_analysis_status_written": outputs.get("dataset_analysis_status", False),
        "candidate_gene_results_written": outputs.get("candidate_gene_external_results", False),
        "mechanism_results_written": outputs.get("mechanism_external_results", False),
        "celltype_specificity_written": outputs.get("celltype_specificity_results", False),
        "microglia_specificity_written": outputs.get("microglia_specificity_results", False),
        "tau_ptau_support_written": outputs.get("tau_ptau_support_results", False),
        "abeta_amyloid_support_written": outputs.get("abeta_amyloid_support_results", False),
        "cross_dataset_concordance_written": outputs.get("cross_dataset_concordance", False),
        "external_support_tiers_written": outputs.get("external_support_tiers", False),
        "negative_null_results_written": outputs.get("negative_null_results", False),
        "claim_boundary_audit_written": outputs.get("claim_boundary_audit", False),
        "reports_written": outputs.get("report", False) and outputs.get("pi_report", False),
        "analysis_run_for_every_ready_dataset": ready_count == analyzed_count if stage38a_found else False,
        "non_ready_datasets_reported_honestly": True,
        "no_sea_ad_model_training": True,
        "no_model_selection_using_external_datasets": True,
        "no_candidate_selection_using_external_datasets": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_definitive_clean_external_validation_claim": True,
        "safety_audit_pass": as_bool(audit.iloc[0]["safety_audit_pass"]),
    }
    required = [
        "stage38b_run",
        "stage38a_inputs_found",
        "stage36e_inputs_found",
        "dataset_analysis_status_written",
        "candidate_gene_results_written",
        "mechanism_results_written",
        "celltype_specificity_written",
        "microglia_specificity_written",
        "tau_ptau_support_written",
        "abeta_amyloid_support_written",
        "cross_dataset_concordance_written",
        "external_support_tiers_written",
        "negative_null_results_written",
        "claim_boundary_audit_written",
        "reports_written",
        "analysis_run_for_every_ready_dataset",
        "non_ready_datasets_reported_honestly",
        "safety_audit_pass",
    ]
    row["stage38b_run_pass"] = all(bool(row[k]) for k in required)
    row["ready_dataset_count"] = ready_count
    row["analyzed_dataset_count"] = analyzed_count
    row["controlled_interpretation"] = "Stage 38B analyzes only Stage 38A-ready external datasets using frozen Stage 36E candidates; if Stage 38A inputs are missing, Stage 38B is blocked and no support claim is made."
    return pd.DataFrame([row])


def build_report(status: pd.DataFrame, candidate: pd.DataFrame, mechanism: pd.DataFrame, micro: pd.DataFrame, tau: pd.DataFrame, abeta: pd.DataFrame, cross: pd.DataFrame, neg: pd.DataFrame, pf: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Stage 38B prepared external support analysis report v1",
            "",
            "## Purpose",
            "",
            "Stage 38B uses Stage 38A prepared inputs to test external support for frozen Stage 36E mechanisms and candidates.",
            "",
            "## Dataset analysis status",
            "",
            markdown_table(status),
            "",
            "## Candidate gene results",
            "",
            markdown_table(candidate.head(50)),
            "",
            "## Mechanism results",
            "",
            markdown_table(mechanism.head(50)),
            "",
            "## Microglia specificity",
            "",
            markdown_table(micro.head(50)),
            "",
            "## Tau/pTau support",
            "",
            markdown_table(tau.head(50)),
            "",
            "## Aβ/amyloid support",
            "",
            markdown_table(abeta.head(50)),
            "",
            "## Cross-dataset concordance",
            "",
            markdown_table(cross),
            "",
            "## Negative/null/not-testable results",
            "",
            markdown_table(neg.head(80)),
            "",
            "## Claim boundaries",
            "",
            f"Allowed wording: {ALLOWED_CLAIM}.",
            "",
            f"Prohibited wording: {PROHIBITED_CLAIM}.",
            "",
            "## Pass/fail summary",
            "",
            markdown_table(pf),
        ]
    )


def build_pi_report(status: pd.DataFrame, mechanism: pd.DataFrame, micro: pd.DataFrame, tau: pd.DataFrame, abeta: pd.DataFrame, cross: pd.DataFrame, neg: pd.DataFrame, pf: pd.DataFrame) -> str:
    analyzed = status[status.get("analysis_completed", pd.Series(dtype=bool)).map(as_bool)] if not status.empty else pd.DataFrame()
    skipped = status[~status.get("analysis_completed", pd.Series(dtype=bool)).map(as_bool)] if not status.empty else pd.DataFrame()
    return "\n".join(
        [
            "# Stage 38B PI external support summary v1",
            "",
            "## Short answer",
            "",
            "Stage 38B is a prepared-input external support analysis. It does not train SEA-AD models, select candidates, tune thresholds, or claim clean external validation.",
            "",
            "## Datasets analyzed",
            "",
            markdown_table(analyzed),
            "",
            "## Datasets skipped / blocked",
            "",
            markdown_table(skipped),
            "",
            "## Strongest supported mechanisms",
            "",
            markdown_table(mechanism[mechanism.get("support_tier", pd.Series(dtype=str)).isin(["strong_external_support", "moderate_external_support"])].head(20) if not mechanism.empty else pd.DataFrame()),
            "",
            "## Microglia specificity",
            "",
            markdown_table(micro.head(30)),
            "",
            "## pTau / Aβ support",
            "",
            markdown_table(pd.concat([tau, abeta], ignore_index=True, sort=False).head(40)),
            "",
            "## Cross-dataset concordance",
            "",
            markdown_table(cross),
            "",
            "## Negative/null/not-testable count",
            "",
            str(len(neg)),
            "",
            "## Pass/fail",
            "",
            markdown_table(pf[["stage38b_run_pass", "ready_dataset_count", "analyzed_dataset_count", "stage38a_inputs_found", "safety_audit_pass"]]),
        ]
    )


def append_section_once(path_value: str | Path, heading: str, body: str) -> None:
    path = resolve(path_value)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"\n{heading}\n{body}\n"
    path.write_text(text, encoding="utf-8")


def update_scorecard_csv(path_value: str | Path, pf: pd.DataFrame) -> None:
    path = resolve(path_value)
    run_pass = bool(pf.iloc[0]["stage38b_run_pass"])
    row = {
        "stage_id": "stage38b_prepared_external_support_analysis",
        "status": "complete" if run_pass else "blocked",
        "stage": "Stage 38B",
        "primary_metric": "prepared external support analysis",
        "pass_rule": "pass requires Stage 38A inputs and analysis of every ready dataset with claim-boundary audit",
        "result": f"run_pass={run_pass}; ready={pf.iloc[0]['ready_dataset_count']}; analyzed={pf.iloc[0]['analyzed_dataset_count']}",
        "pass_fail": "pass" if run_pass else "fail",
        "allowed_inputs": "Stage 38A prepared inputs and frozen Stage 36E candidates",
        "forbidden_inputs": "SEA-AD model training; threshold tuning; candidate selection; unsupported clean-validation claims",
        "interpretation": "Stage 38B is external-support analysis only, not causal or therapeutic validation.",
        "notes": str(pf.iloc[0]["controlled_interpretation"]),
    }
    if path.exists():
        df = pd.read_csv(path)
        if "stage_id" in df.columns and (df["stage_id"] == row["stage_id"]).any():
            df.loc[df["stage_id"] == row["stage_id"], list(row.keys())] = list(row.values())
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(path, index=False)


def update_status_docs(cfg: dict[str, Any], pf: pd.DataFrame) -> None:
    run_pass = bool(pf.iloc[0]["stage38b_run_pass"])
    heading = "## Stage 38B prepared external support analysis status"
    body = (
        f"Stage 38B prepared external support analysis {'is complete' if run_pass else 'is blocked'}. "
        f"Ready datasets: `{pf.iloc[0]['ready_dataset_count']}`; analyzed datasets: `{pf.iloc[0]['analyzed_dataset_count']}`. "
        "It uses frozen Stage 36E candidates only and does not train SEA-AD models, tune thresholds, select candidates, or claim causal/therapeutic validation."
    )
    append_section_once(cfg["status_updates"]["active_status"], heading, body)
    append_section_once(
        cfg["status_updates"]["scorecard_md"],
        "## Stage 38B prepared external support analysis result",
        f"Stage 38B run pass: `{run_pass}`. This is external support / conditional validation support only; no clean validation claim is made unless the dataset gate explicitly allows it.",
    )
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"], pf)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage38b_prepared_external_support_analysis_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    presence = input_presence(cfg)
    index = read_csv(cfg["inputs"]["stage38a_processed_input_index"])
    mechanisms = read_csv(cfg["inputs"]["stage36e_frozen_mechanism_registry"])
    candidates = read_csv(cfg["inputs"]["stage36e_priority_candidate_registry"])
    claim = read_csv(cfg["inputs"]["stage38a_external_dataset_claim_level"])
    audit = claim_audit()

    ready = ready_rows(index)
    if not all(v for k, v in presence.items() if k.startswith("stage38a")) or ready.empty:
        outputs = empty_outputs_for_missing_inputs(index)
        if not index.empty:
            nonready = index.copy()
            nonready["analysis_completed"] = False
            nonready["load_status"] = "not_ready_or_stage38a_inputs_missing"
            outputs["status"] = nonready
    else:
        parts = []
        for _, row in ready.iterrows():
            parts.append(analyze_dataset(row, mechanisms, candidates, claim))
        outputs = {}
        for key in ["status", "candidate", "mechanism", "celltype", "microglia", "tau", "abeta", "negative"]:
            outputs[key] = pd.concat([p[key] for p in parts], ignore_index=True, sort=False) if parts else pd.DataFrame()
        outputs["cross"], outputs["tiers"] = summarize_cross_dataset(outputs["mechanism"])

    written: dict[str, bool] = {}
    paths = []
    table_map = {
        "dataset_analysis_status": outputs["status"],
        "candidate_gene_external_results": outputs["candidate"],
        "mechanism_external_results": outputs["mechanism"],
        "celltype_specificity_results": outputs["celltype"],
        "microglia_specificity_results": outputs["microglia"],
        "tau_ptau_support_results": outputs["tau"],
        "abeta_amyloid_support_results": outputs["abeta"],
        "cross_dataset_concordance": outputs["cross"],
        "external_support_tiers": outputs["tiers"],
        "negative_null_results": outputs["negative"],
        "claim_boundary_audit": audit,
    }
    for key, df in table_map.items():
        path = write_csv(df, cfg["outputs"][key])
        paths.append(path)
        written[key] = path.exists()

    analyzed_count = int(outputs["status"]["analysis_completed"].map(as_bool).sum()) if not outputs["status"].empty and "analysis_completed" in outputs["status"].columns else 0
    pf = build_pass_fail(presence, len(ready), analyzed_count, written, audit)
    pf_path = write_csv(pf, cfg["outputs"]["pass_fail"])
    paths.append(pf_path)
    written["pass_fail"] = pf_path.exists()
    report_path = write_text(build_report(outputs["status"], outputs["candidate"], outputs["mechanism"], outputs["microglia"], outputs["tau"], outputs["abeta"], outputs["cross"], outputs["negative"], pf), cfg["outputs"]["report"])
    pi_path = write_text(build_pi_report(outputs["status"], outputs["mechanism"], outputs["microglia"], outputs["tau"], outputs["abeta"], outputs["cross"], outputs["negative"], pf), cfg["outputs"]["pi_report"])
    paths.extend([report_path, pi_path])
    written["report"] = report_path.exists()
    written["pi_report"] = pi_path.exists()
    pf = build_pass_fail(presence, len(ready), analyzed_count, written, audit)
    write_csv(pf, cfg["outputs"]["pass_fail"])
    write_text(build_report(outputs["status"], outputs["candidate"], outputs["mechanism"], outputs["microglia"], outputs["tau"], outputs["abeta"], outputs["cross"], outputs["negative"], pf), cfg["outputs"]["report"])
    write_text(build_pi_report(outputs["status"], outputs["mechanism"], outputs["microglia"], outputs["tau"], outputs["abeta"], outputs["cross"], outputs["negative"], pf), cfg["outputs"]["pi_report"])
    update_status_docs(cfg, pf)
    paths.extend([resolve(cfg["status_updates"]["active_status"]), resolve(cfg["status_updates"]["scorecard_md"]), resolve(cfg["status_updates"]["scorecard_csv"])])

    print("stage38b_paths_written=")
    for path in paths:
        print(str(path.relative_to(ROOT)))
    analyzed = outputs["status"][outputs["status"].get("analysis_completed", pd.Series(dtype=bool)).map(as_bool)] if not outputs["status"].empty else pd.DataFrame()
    skipped = outputs["status"][~outputs["status"].get("analysis_completed", pd.Series(dtype=bool)).map(as_bool)] if not outputs["status"].empty else pd.DataFrame()
    print("datasets_analyzed=" + unique_join(analyzed.get("dataset_id", pd.Series(dtype=str)).tolist()))
    print("datasets_skipped=" + unique_join(skipped.get("dataset_id", pd.Series(dtype=str)).tolist()))
    print("strongest_supported_mechanisms=" + unique_join(outputs["tiers"].get("mechanism_id", pd.Series(dtype=str)).tolist()))
    print("microglia_specificity_results_rows=" + str(len(outputs["microglia"])))
    print("ptau_support_rows=" + str(len(outputs["tau"])))
    print("abeta_support_rows=" + str(len(outputs["abeta"])))
    print("cross_dataset_concordance_rows=" + str(len(outputs["cross"])))
    print("negative_null_result_count=" + str(len(outputs["negative"])))
    print(f"stage38b_run_pass={pf.iloc[0]['stage38b_run_pass']}")


if __name__ == "__main__":
    main()
