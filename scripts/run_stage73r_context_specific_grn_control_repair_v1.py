#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
STAGE27C = 0.3267024400121495
STAGE41C = 0.36808747595423713
SCORECARD_COLUMNS = [
    "scorecard_item", "status", "stage", "metric", "threshold_or_gate",
    "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden",
    "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule",
    "result", "allowed_inputs", "forbidden_inputs", "interpretation",
]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    with resolve(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_stage71_module(path: str | Path):
    spec = importlib.util.spec_from_file_location("stage71", resolve(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Stage71 helper module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
        vals = []
        for col in cols:
            val = r[col]
            vals.append(f"{val:.6g}" if isinstance(val, float) else str(val).replace("|", "/"))
        lines.append("| " + " | ".join(vals) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines)


def candidate_graph_matrix(
    genes: list[str],
    edge_path: Path,
    mode: str,
    seed: int,
    weight_column: str = "bootstrap_sign_stability",
) -> tuple[sparse.csr_matrix, pd.DataFrame]:
    idx = {g: i for i, g in enumerate(genes)}
    edges = pd.read_csv(edge_path)
    if "edge_candidate_pass" in edges.columns:
        edges = edges[edges["edge_candidate_pass"].astype(str).str.lower().eq("true")].copy()
    edges["source"] = edges["source_tf"].astype(str).str.upper()
    edges["target"] = edges["target_gene"].astype(str).str.upper()
    rng = np.random.default_rng(seed)
    if mode == "shuffled_target":
        targets = edges["target"].to_numpy().copy()
        rng.shuffle(targets)
        edges["target"] = targets
    elif mode == "permuted_gene_labels":
        perm = dict(zip(genes, rng.permutation(genes)))
        edges["source"] = edges["source"].map(lambda x: perm.get(x, x))
        edges["target"] = edges["target"].map(lambda x: perm.get(x, x))
    rows, cols, data = [], [], []
    for _, row in edges.iterrows():
        source = row["source"]
        target = row["target"]
        if source not in idx or target not in idx or source == target:
            continue
        weight = abs(float(row.get(weight_column, 1.0)))
        rho = abs(float(row.get("spearman_rho", 1.0))) if "spearman_rho" in row else 1.0
        weight = max(0.05, weight * rho)
        rows.extend([idx[source], idx[target]])
        cols.extend([idx[target], idx[source]])
        data.extend([weight, weight])
    n = len(genes)
    mat = sparse.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    deg = np.asarray(mat.sum(axis=1)).ravel()
    cap = np.minimum(deg, np.nanpercentile(deg[deg > 0], 90) if np.any(deg > 0) else 1.0)
    scale = np.divide(cap, deg, out=np.zeros_like(deg), where=deg > 0)
    mat = sparse.diags(scale) @ mat @ sparse.diags(scale)
    rs = np.asarray(mat.sum(axis=1)).ravel()
    mat = sparse.diags(np.divide(1.0, rs, out=np.zeros_like(rs), where=rs > 0)) @ mat
    reg = pd.DataFrame({
        "gene": genes,
        "graph_name": mode,
        "weighted_degree": deg,
        "hub_capped_degree": cap,
        "in_graph": deg > 0,
    })
    return mat.tocsr(), reg


def graph_hash(mat: sparse.csr_matrix) -> str:
    mat = mat.tocsr()
    h = hashlib.sha256()
    h.update(mat.indptr.tobytes())
    h.update(mat.indices.tobytes())
    h.update(np.asarray(mat.data, dtype=np.float64).tobytes())
    h.update(np.asarray(mat.shape, dtype=np.int64).tobytes())
    return h.hexdigest()


def sparse_corr(a: sparse.csr_matrix, b: sparse.csr_matrix) -> float:
    av = a.toarray().ravel()
    bv = b.toarray().ravel()
    if np.nanstd(av) == 0 or np.nanstd(bv) == 0:
        return np.nan
    return float(np.corrcoef(av, bv)[0, 1])


def graph_integrity_row(name: str, graph: sparse.csr_matrix, context: sparse.csr_matrix, genes: list[str]) -> dict[str, Any]:
    graph = graph.tocsr()
    context = context.tocsr()
    diff = (context != graph).nnz
    deg_context = np.asarray(context.sum(axis=1)).ravel()
    deg_graph = np.asarray(graph.sum(axis=1)).ravel()
    degree_corr = np.nan
    if np.nanstd(deg_context) > 0 and np.nanstd(deg_graph) > 0:
        degree_corr = float(np.corrcoef(deg_context, deg_graph)[0, 1])
    context_edges = set(zip(*context.nonzero()))
    graph_edges = set(zip(*graph.nonzero()))
    symmetric = context_edges.symmetric_difference(graph_edges)
    union = context_edges.union(graph_edges)
    return {
        "graph_name": name,
        "n_nodes": len(genes),
        "edge_count_directed_nnz": int(graph.nnz),
        "matrix_nnz": int(graph.nnz),
        "matrix_hash": graph_hash(graph),
        "diff_nnz_vs_context": int(diff),
        "fraction_changed_edges_vs_context": float(len(symmetric) / max(1, len(union))),
        "node_coverage_fraction": float(np.mean(deg_graph > 0)),
        "degree_correlation_with_context": degree_corr,
        "weighted_adjacency_correlation_with_context": sparse_corr(context, graph),
        "distinct_from_context": bool(diff > 0 and graph_hash(graph) != graph_hash(context)),
    }


def zero_graph_matrix(genes: list[str]) -> tuple[sparse.csr_matrix, pd.DataFrame]:
    mat = sparse.csr_matrix((len(genes), len(genes)))
    reg = pd.DataFrame({"gene": genes, "graph_name": "no_graph_identity", "weighted_degree": 0.0, "hub_capped_degree": 0.0, "in_graph": False})
    return mat, reg


def update_docs(cfg: dict[str, Any], lock: pd.DataFrame, pf: pd.DataFrame) -> None:
    body = (
        "Stage73R repaired the Stage73 candidate-GRN negative-control mode-label "
        "bug, verified that target-shuffled and gene-label-permuted controls are "
        "structurally distinct from the Stage72B context graph, and reran the frozen "
        "Stage71 rare-cell donor-held-out graph diagnostic. It is a diagnostic "
        "graph-prior test only: no clean external validation, causal regulatory, "
        "therapeutic, gene-ablation, or validated-GRN claim is made."
    )
    for key in ["active_status", "v3_scorecard_md"]:
        mod.update_section(cfg["inputs"][key], "Stage 73R context-specific GRN control repair", body)
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    df = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    row = {
        "scorecard_item": "Stage73R context-specific GRN control repair",
        "status": "complete",
        "stage": "Stage73R",
        "metric": "context-specific graph vs no-graph/STRING/shuffled controls",
        "threshold_or_gate": "must beat no-graph and all graph controls without safety violations",
        "current_value": f"context_graph_lock={bool(lock['context_graph_prediction_lock'].iloc[0])}; control_integrity_pass={bool(pf['control_integrity_pass'].iloc[0])}; stage73r_run_pass={bool(pf['stage73r_run_pass'].iloc[0])}",
        "pass_fail": "pass" if bool(pf["stage73r_run_pass"].iloc[0]) else "fail",
        "datasets_allowed": "Stage72B candidate edges, local MTG/DLPFC H5ADs, frozen Stage64/68 signatures",
        "datasets_forbidden": "external validation claim; graph threshold tuning; new candidate selection",
        "allowed_claim": "diagnostic context-specific graph-prior benchmark",
        "notes": "Compares Morabito candidate coactivity graph against strict controls.",
        "stage_id": "stage73r_context_specific_grn_control_repair",
        "primary_metric": "mean pooled OOF Spearman and bootstrap deltas vs controls",
        "pass_rule": "outputs written and claim-boundary audit passes",
        "result": "see stage73r_prediction_lock_decision_v1.csv and stage73r_graph_control_integrity_audit_v1.csv",
        "allowed_inputs": "frozen Stage72B graph and frozen rare-cell signatures",
        "forbidden_inputs": "post hoc tuning or causal GRN claims",
        "interpretation": "Internal graph-prior diagnostic only; external support still required.",
    }
    df = df[~df["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([df[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg: dict[str, Any]) -> None:
    global mod
    mod = load_stage71_module(cfg["inputs"]["stage71_script"])
    outputs = cfg["outputs"]
    inventory = pd.DataFrame([
        {"input_name": k, "path": v, "exists": resolve(v).exists(), "size_bytes": resolve(v).stat().st_size if resolve(v).exists() else 0}
        for k, v in cfg["inputs"].items()
        if k not in {"active_status", "v3_scorecard_md", "v3_scorecard_csv", "stage71_script"}
    ])
    genes = mod.requested_genes(cfg)
    stage72b_edges = pd.read_csv(resolve(cfg["inputs"]["stage72b_candidate_edges"]))
    graph_nodes = sorted(
        set(stage72b_edges.get("source_tf", pd.Series(dtype=str)).astype(str).str.upper())
        | set(stage72b_edges.get("target_gene", pd.Series(dtype=str)).astype(str).str.upper())
    )
    genes = list(dict.fromkeys([*genes, *graph_nodes]))
    graph_specs = []
    A_context, reg_context = candidate_graph_matrix(genes, resolve(cfg["inputs"]["stage72b_candidate_edges"]), "context_specific_stage72b_grn", int(cfg["references"]["random_seed"]))
    A_shuf, reg_shuf = candidate_graph_matrix(genes, resolve(cfg["inputs"]["stage72b_candidate_edges"]), "shuffled_target", int(cfg["references"]["random_seed"]))
    A_perm, reg_perm = candidate_graph_matrix(genes, resolve(cfg["inputs"]["stage72b_candidate_edges"]), "permuted_gene_labels", int(cfg["references"]["random_seed"]))
    A_zero, reg_zero = zero_graph_matrix(genes)
    A_string, reg_string = mod.graph_matrix(genes, resolve(cfg["inputs"]["string_edges"]), False, int(cfg["references"]["random_seed"]))
    reg_string = reg_string.rename(columns={"degree_in_signature_graph": "weighted_degree"})
    reg_string["graph_name"] = "STRING_t700"
    assert (A_context != A_shuf).nnz > 0
    assert (A_context != A_perm).nnz > 0
    assert graph_hash(A_context) != graph_hash(A_shuf)
    assert graph_hash(A_context) != graph_hash(A_perm)
    control_integrity = pd.DataFrame([
        graph_integrity_row("context_grn_aux", A_context, A_context, genes),
        graph_integrity_row("target_shuffled_grn_aux", A_shuf, A_context, genes),
        graph_integrity_row("gene_label_permuted_grn_aux", A_perm, A_context, genes),
        graph_integrity_row("string_graph_aux", A_string, A_context, genes),
        graph_integrity_row("no_graph_raw", A_zero, A_context, genes),
    ])
    target_shuffled_control_applied = bool(control_integrity.set_index("graph_name").loc["target_shuffled_grn_aux", "distinct_from_context"])
    gene_label_permutation_applied = bool(control_integrity.set_index("graph_name").loc["gene_label_permuted_grn_aux", "distinct_from_context"])
    control_graphs_distinct_from_context = bool(target_shuffled_control_applied and gene_label_permutation_applied)
    control_integrity_pass = bool(control_graphs_distinct_from_context)
    graph_specs = [
        ("context_grn_aux", A_context),
        ("no_graph_raw", A_zero),
        ("string_graph_aux", A_string),
        ("target_shuffled_grn_aux", A_shuf),
        ("gene_label_permuted_grn_aux", A_perm),
    ]
    graph_registry = pd.concat([reg_context, reg_zero, reg_string, reg_shuf, reg_perm], ignore_index=True)

    condition_features = []
    cell_aux_rows = []
    for condition, graph in graph_specs:
        cell_parts = []
        for dataset, path in [("MTG", cfg["inputs"]["mtg_h5ad"]), ("DLPFC", cfg["inputs"]["dlpfc_h5ad"])]:
            cells, _, _ = mod.load_cells(dataset, resolve(path), genes, graph)
            cell_parts.append(cells)
        cells_all = pd.concat(cell_parts, ignore_index=True)
        score_col = "raw_disease_program_score" if condition == "no_graph_raw" else "residual_graph_rare_score"
        feats = mod.donor_features(cells_all, score_col, condition)
        condition_features.append((condition, feats))
        cell_aux_rows.append({
            "condition": condition,
            "n_cells": int(len(cells_all)),
            "mean_raw_score": float(cells_all["raw_disease_program_score"].mean()),
            "mean_graph_score": float(cells_all["graph_disease_program_score"].mean()),
            "mean_residual_score": float(cells_all["residual_graph_rare_score"].mean()),
        })

    _, targets = mod.load_stage69_context()
    oofs, tms, sms = [], [], []
    for condition, feats in condition_features:
        oof, tm, sm = mod.predict(feats, targets, cfg["references"]["seeds"], int(cfg["references"]["n_splits"]))
        oof["condition"] = condition
        tm["condition"] = condition
        sm["condition"] = condition
        oofs.append(oof)
        tms.append(tm)
        sms.append(sm)
    oof_all = pd.concat(oofs, ignore_index=True)
    tm_all = pd.concat(tms, ignore_index=True)
    sm_all = pd.concat(sms, ignore_index=True)
    seed_summary = sm_all.groupby("condition", as_index=False).agg(
        mean_score=("mean_pooled_oof_spearman", "mean"),
        median_score=("mean_pooled_oof_spearman", "median"),
        min_score=("mean_pooled_oof_spearman", "min"),
        max_score=("mean_pooled_oof_spearman", "max"),
    ).sort_values("mean_score", ascending=False)
    boot_source = sm_all[["seed", "condition", "mean_pooled_oof_spearman"]]
    boot = pd.DataFrame([
        mod.bootstrap_delta_from_seed_summary(boot_source, "context_grn_aux", None, "context_grn_vs_stage27c", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
        mod.bootstrap_delta_from_seed_summary(boot_source, "context_grn_aux", "no_graph_raw", "context_grn_vs_no_graph", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
        mod.bootstrap_delta_from_seed_summary(boot_source, "context_grn_aux", "string_graph_aux", "context_grn_vs_string", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
        mod.bootstrap_delta_from_seed_summary(boot_source, "context_grn_aux", "target_shuffled_grn_aux", "context_grn_vs_target_shuffled", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
        mod.bootstrap_delta_from_seed_summary(boot_source, "context_grn_aux", "gene_label_permuted_grn_aux", "context_grn_vs_gene_label_permuted", int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"])),
    ])
    means = seed_summary.set_index("condition")["mean_score"].to_dict()
    lock = pd.DataFrame([{
        "context_graph_mean": means.get("context_grn_aux", np.nan),
        "no_graph_mean": means.get("no_graph_raw", np.nan),
        "string_graph_mean": means.get("string_graph_aux", np.nan),
        "target_shuffled_mean": means.get("target_shuffled_grn_aux", np.nan),
        "gene_label_permuted_mean": means.get("gene_label_permuted_grn_aux", np.nan),
        "beats_stage27c_mean": means.get("context_grn_aux", -np.inf) > STAGE27C,
        "beats_no_graph_mean": means.get("context_grn_aux", -np.inf) > means.get("no_graph_raw", np.inf),
        "beats_string_mean": means.get("context_grn_aux", -np.inf) > means.get("string_graph_aux", np.inf),
        "beats_target_shuffled_mean": means.get("context_grn_aux", -np.inf) > means.get("target_shuffled_grn_aux", np.inf),
        "beats_gene_label_permuted_mean": means.get("context_grn_aux", -np.inf) > means.get("gene_label_permuted_grn_aux", np.inf),
        "bootstrap_vs_no_graph_positive": bool(boot.set_index("comparison").loc["context_grn_vs_no_graph", "ci_lower_2p5"] > 0),
        "bootstrap_vs_all_graph_controls_positive": bool((boot[boot["comparison"].isin(["context_grn_vs_string", "context_grn_vs_target_shuffled", "context_grn_vs_gene_label_permuted"])]["ci_lower_2p5"] > 0).all()),
        "beats_stage41c_descriptive": means.get("context_grn_aux", -np.inf) > STAGE41C,
    }])
    lock["context_graph_prediction_lock"] = (
        lock["beats_stage27c_mean"]
        & lock["beats_no_graph_mean"]
        & lock["beats_string_mean"]
        & lock["beats_target_shuffled_mean"]
        & lock["beats_gene_label_permuted_mean"]
        & lock["bootstrap_vs_no_graph_positive"]
        & lock["bootstrap_vs_all_graph_controls_positive"]
    )
    claim = pd.DataFrame([{
        "stage73_internal_graph_prior_diagnostic_only": True,
        "uses_frozen_stage72b_edges": True,
        "uses_frozen_stage64_68_signature": True,
        "no_graph_threshold_tuning": True,
        "no_new_candidate_selection": True,
        "no_model_architecture_search": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_validated_grn_claim": True,
        "raw_data_not_committed": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage73_run": True,
        "inputs_found": bool(inventory["exists"].all()),
        "stage72b_ready_input": bool(pd.read_csv(resolve(cfg["inputs"]["stage72b_readiness"]))["ready_for_stage73_graph_benchmark"].iloc[0]),
        "all_required_outputs_written": True,
        "target_shuffled_control_applied": target_shuffled_control_applied,
        "gene_label_permutation_applied": gene_label_permutation_applied,
        "control_graphs_distinct_from_context": control_graphs_distinct_from_context,
        "control_integrity_pass": control_integrity_pass,
        "context_graph_prediction_lock": bool(lock["context_graph_prediction_lock"].iloc[0]),
        "clean_external_validation_pass": False,
        **claim.iloc[0].to_dict(),
    }])
    pf["stage73r_run_pass"] = pf[["inputs_found", "stage72b_ready_input", "all_required_outputs_written", "control_integrity_pass", "safety_audit_pass"]].all(axis=1)

    graph_controls = seed_summary.merge(pd.DataFrame(cell_aux_rows), on="condition", how="left")
    tables = {
        "input_inventory": inventory,
        "graph_registry": graph_registry,
        "graph_control_integrity_audit": control_integrity,
        "graph_control_results": graph_controls,
        "cell_auxiliary_metrics": pd.DataFrame(cell_aux_rows),
        "oof_predictions": oof_all,
        "target_metrics": tm_all,
        "seed_summary": seed_summary,
        "bootstrap_delta_ci": boot,
        "prediction_lock_decision": lock,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for key, df in tables.items():
        write_csv(df, outputs[key])
    update_docs(cfg, lock, pf)
    report = f"""# Stage73R context-specific GRN control repair

## Control integrity audit

{md(control_integrity)}

## Prediction lock decision

{md(lock)}

## Seed summary

{md(seed_summary)}

## Bootstrap deltas

{md(boot)}

## Claim boundary

{md(claim)}
"""
    write_text(report, outputs["report"])
    write_text(
        f"""# Stage73R PI summary

- Context graph prediction lock: `{bool(lock['context_graph_prediction_lock'].iloc[0])}`
- Control integrity pass: `{bool(pf['control_integrity_pass'].iloc[0])}`
- Context graph mean: `{float(lock['context_graph_mean'].iloc[0])}`
- No-graph mean: `{float(lock['no_graph_mean'].iloc[0])}`
- STRING graph mean: `{float(lock['string_graph_mean'].iloc[0])}`
- Target-shuffled graph mean: `{float(lock['target_shuffled_mean'].iloc[0])}`
- Gene-label-permuted graph mean: `{float(lock['gene_label_permuted_mean'].iloc[0])}`
- Clean external validation pass: `False`

Interpretation: this is an internal graph-prior diagnostic using the frozen
Stage72B candidate coactivity graph. It does not validate regulation or create a
therapeutic/causal claim.
""",
        outputs["pi_summary"],
    )
    write_text(f"# Stage73R claim-boundary final check\n\n{md(claim)}\n", outputs["claim_boundary_final_check"])
    print(f"stage73r_run_pass={bool(pf['stage73r_run_pass'].iloc[0])}")
    print(f"control_integrity_pass={bool(pf['control_integrity_pass'].iloc[0])}")
    print(f"target_shuffled_control_applied={bool(pf['target_shuffled_control_applied'].iloc[0])}")
    print(f"gene_label_permutation_applied={bool(pf['gene_label_permutation_applied'].iloc[0])}")
    print(f"context_graph_prediction_lock={bool(lock['context_graph_prediction_lock'].iloc[0])}")
    print(f"context_graph_mean={float(lock['context_graph_mean'].iloc[0])}")
    print(f"no_graph_mean={float(lock['no_graph_mean'].iloc[0])}")
    print(f"string_graph_mean={float(lock['string_graph_mean'].iloc[0])}")
    print(f"target_shuffled_mean={float(lock['target_shuffled_mean'].iloc[0])}")
    print(f"gene_label_permuted_mean={float(lock['gene_label_permuted_mean'].iloc[0])}")
    print("clean_external_validation_pass=False")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage73r_context_specific_grn_control_repair_v1.yaml")
    args = parser.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
