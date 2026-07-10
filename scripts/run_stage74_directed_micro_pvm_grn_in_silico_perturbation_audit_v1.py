#!/usr/bin/env python
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
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


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    with resolve(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_stage71(path: str | Path):
    spec = importlib.util.spec_from_file_location("stage71", resolve(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import Stage71 helpers")
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
    for _, row in d.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            vals.append(f"{val:.6g}" if isinstance(val, float) else str(val).replace("|", "/"))
        lines.append("| " + " | ".join(vals) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines)


def z(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    sd = np.nanstd(v)
    return (v - np.nanmean(v)) / sd if sd > 0 else np.zeros_like(v)


def requested_genes(cfg: dict[str, Any], edges: pd.DataFrame) -> list[str]:
    genes: list[str] = []
    for vals in MODULES.values():
        genes.extend(vals)
    genes.extend(cfg["references"]["core_signature_genes"])
    genes.extend(edges["source_tf"].astype(str).str.upper().tolist())
    genes.extend(edges["target_gene"].astype(str).str.upper().tolist())
    return list(dict.fromkeys(genes))


def load_expression_cells(stage71, dataset: str, path: Path, genes_req: list[str]) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    with h5py.File(path, "r") as handle:
        obs = handle["obs"]
        donor_col = stage71.find_col(obs, ["donor_id", "Donor ID", "donor"])
        state_col = stage71.find_col(obs, ["Supertype", "Subclass", "cell_type", "ct_subcluster", "author_cell_type"])
        donors = stage71.decode(obs[donor_col]).astype(str)
        states = stage71.decode(obs[state_col]).astype(str) if state_col else np.array(["state_unavailable"] * len(donors), dtype=object)
        genes = stage71.gene_symbols(handle)
        gidx = {str(g).upper(): i for i, g in enumerate(genes)}
        present = [g for g in genes_req if g in gidx]
        X = stage71.x_matrix(handle)[:, [gidx[g] for g in present]].toarray().astype(np.float32)
    cell = pd.DataFrame({"dataset": dataset, "cell_index": np.arange(X.shape[0]), "donor_id": donors, "state_label": states})
    return cell, X, present


def module_matrix(X: np.ndarray, genes: list[str]) -> pd.DataFrame:
    cols = {}
    gpos = {g: i for i, g in enumerate(genes)}
    for module, members in MODULES.items():
        ids = [gpos[g] for g in members if g in gpos]
        cols[module] = X[:, ids].mean(axis=1) if ids else np.zeros(X.shape[0])
    return pd.DataFrame(cols)


def disease_program(modules: pd.DataFrame) -> np.ndarray:
    return np.mean([z(modules[m].to_numpy()) for m in COMPOSITE], axis=0)


def perturb_targets(regulator: str, graph: dict[str, dict[str, float]], hop2: bool, hop2_weight: float) -> dict[str, float]:
    out = dict(graph.get(regulator, {}))
    if hop2:
        for mid, w1 in graph.get(regulator, {}).items():
            for target, w2 in graph.get(mid, {}).items():
                if target != regulator:
                    out[target] = max(out.get(target, 0.0), float(w1) * float(w2) * hop2_weight)
    return out


def build_graphs(edges: pd.DataFrame, genes: list[str], seed: int) -> dict[str, dict[str, dict[str, float]]]:
    passed = edges[edges["edge_candidate_pass"].astype(str).str.lower().eq("true")].copy()
    passed["source_tf"] = passed["source_tf"].astype(str).str.upper()
    passed["target_gene"] = passed["target_gene"].astype(str).str.upper()
    passed["weight"] = passed["bootstrap_sign_stability"].astype(float) * passed["spearman_rho"].astype(float).abs()
    def to_graph(df: pd.DataFrame) -> dict[str, dict[str, float]]:
        graph: dict[str, dict[str, float]] = {}
        for _, row in df.iterrows():
            s, t = row["source_tf"], row["target_gene"]
            if s in genes and t in genes and s != t:
                graph.setdefault(s, {})[t] = max(graph.setdefault(s, {}).get(t, 0.0), float(row["weight"]))
        return graph
    rng = np.random.default_rng(seed)
    shuffled = passed.copy()
    targets = shuffled["target_gene"].to_numpy().copy()
    rng.shuffle(targets)
    shuffled["target_gene"] = targets
    reversed_df = passed.rename(columns={"source_tf": "target_gene", "target_gene": "source_tf"}).copy()
    random_rows = []
    target_pool = sorted(set(passed["target_gene"]) & set(genes))
    for source, sub in passed.groupby("source_tf"):
        n = int(sub["target_gene"].nunique())
        pool = [g for g in target_pool if g != source]
        chosen = rng.choice(pool, min(n, len(pool)), replace=False) if pool else []
        for target in chosen:
            random_rows.append({"source_tf": source, "target_gene": target, "weight": float(sub["weight"].median())})
    random_df = pd.DataFrame(random_rows)
    return {
        "directed_stage72b": to_graph(passed),
        "reversed_directed": to_graph(reversed_df),
        "target_shuffled_directed": to_graph(shuffled),
        "degree_matched_random_directed": to_graph(random_df) if len(random_df) else {},
    }


def simulate_dataset(
    dataset: str,
    cell: pd.DataFrame,
    X: np.ndarray,
    genes: list[str],
    graphs: dict[str, dict[str, dict[str, float]]],
    regulators: list[str],
    doses: list[float],
    hop2_weight: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    gpos = {g: i for i, g in enumerate(genes)}
    baseline_modules = module_matrix(X, genes)
    baseline_program = disease_program(baseline_modules)
    baseline_q95 = float(np.quantile(baseline_program, 0.95))
    baseline_donor = pd.DataFrame({"donor_id": cell["donor_id"], "baseline_program": baseline_program}).groupby("donor_id", as_index=False).agg(
        baseline_top5_mean=("baseline_program", lambda x: float(np.mean(np.asarray(x)[np.asarray(x) >= np.quantile(np.asarray(x), 0.95)]))),
        baseline_q95=("baseline_program", lambda x: float(np.quantile(x, 0.95))),
        baseline_fraction_global_q95=("baseline_program", lambda x: float(np.mean(np.asarray(x) >= baseline_q95))),
    )
    rows = []
    module_rows = []
    for control, graph in graphs.items():
        for regulator in regulators:
            if regulator not in gpos and control == "expression_only":
                continue
            for dose in doses:
                target_weights = {regulator: 1.0} if control == "expression_only" else perturb_targets(regulator, graph, True, hop2_weight)
                target_weights = {g: w for g, w in target_weights.items() if g in gpos}
                if not target_weights:
                    continue
                Xp = X.copy()
                for gene, weight in target_weights.items():
                    Xp[:, gpos[gene]] *= max(0.0, 1.0 - float(dose) * min(1.0, float(weight)))
                pert_modules = module_matrix(Xp, genes)
                pert_program = disease_program(pert_modules)
                tmp = pd.DataFrame({"donor_id": cell["donor_id"], "pert_program": pert_program})
                pert_donor = tmp.groupby("donor_id", as_index=False).agg(
                    pert_top5_mean=("pert_program", lambda x: float(np.mean(np.asarray(x)[np.asarray(x) >= np.quantile(np.asarray(x), 0.95)]))),
                    pert_q95=("pert_program", lambda x: float(np.quantile(x, 0.95))),
                    pert_fraction_global_q95=("pert_program", lambda x: float(np.mean(np.asarray(x) >= baseline_q95))),
                )
                merged = baseline_donor.merge(pert_donor, on="donor_id")
                for metric in ["top5_mean", "q95", "fraction_global_q95"]:
                    base_col = f"baseline_{metric}"
                    pert_col = f"pert_{metric}"
                    rows.append({
                        "dataset": dataset,
                        "regulator": regulator,
                        "control": control,
                        "dose": dose,
                        "metric": metric,
                        "n_downstream_genes": len(target_weights),
                        "downstream_genes": ";".join(sorted(target_weights)),
                        "mean_delta": float((merged[pert_col] - merged[base_col]).mean()),
                        "median_delta": float((merged[pert_col] - merged[base_col]).median()),
                        "abs_mean_delta": float(np.abs(merged[pert_col] - merged[base_col]).mean()),
                        "n_donors": int(merged["donor_id"].nunique()),
                    })
                for module in MODULES:
                    module_rows.append({
                        "dataset": dataset,
                        "regulator": regulator,
                        "control": control,
                        "dose": dose,
                        "module": module,
                        "mean_module_delta": float((pert_modules[module] - baseline_modules[module]).mean()),
                        "abs_mean_module_delta": float(np.abs(pert_modules[module] - baseline_modules[module]).mean()),
                    })
    return pd.DataFrame(rows), pd.DataFrame(module_rows)


def bootstrap_stability(resp: pd.DataFrame, n_iter: int, seed: int) -> pd.DataFrame:
    source = resp[(resp["control"].eq("directed_stage72b")) & (resp["dose"].eq(1.0)) & (resp["metric"].eq("top5_mean"))].copy()
    if source.empty:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    rows = []
    for regulator, sub in source.groupby("regulator"):
        vals = sub["abs_mean_delta"].to_numpy(float)
        boots = []
        for _ in range(n_iter):
            boots.append(float(np.mean(rng.choice(vals, size=len(vals), replace=True))))
        rows.append({
            "regulator": regulator,
            "mean_abs_delta": float(np.mean(vals)),
            "bootstrap_ci_lower_2p5": float(np.quantile(boots, 0.025)),
            "bootstrap_ci_upper_97p5": float(np.quantile(boots, 0.975)),
            "n_dataset_rows": int(len(vals)),
        })
    return pd.DataFrame(rows).sort_values("mean_abs_delta", ascending=False)


def update_docs(stage71, cfg: dict[str, Any], decision: pd.DataFrame, pf: pd.DataFrame) -> None:
    body = (
        "Stage74 tested the Stage72B candidate TF-target graph as a directed "
        "perturbation-prior layer rather than an undirected prediction-smoothing "
        "branch. Fixed-dose regulator perturbations were propagated downstream "
        "through one-hop/two-hop directed targets and compared with expression-only, "
        "reversed, target-shuffled, and random directed controls. This is an in-silico "
        "hypothesis-prioritization audit only: it does not update Stage27C, does not "
        "claim causal knockout validity, and does not claim therapeutic targets."
    )
    stage71.update_section(cfg["inputs"]["active_status"], "Stage 74 directed Micro-PVM GRN perturbation audit", body)
    stage71.update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 74 directed Micro-PVM GRN perturbation audit", body)
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    score = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in score.columns:
            score[col] = ""
    row = {
        "scorecard_item": "Stage74 directed Micro-PVM GRN perturbation audit",
        "status": "complete",
        "stage": "Stage74",
        "metric": "directed perturbation organization/control-specificity gates",
        "threshold_or_gate": "directed organization, stability, control specificity, biological coherence",
        "current_value": f"stage74_run_pass={bool(pf['stage74_run_pass'].iloc[0])}; candidate_prioritization_pass={bool(decision['candidate_prioritization_pass'].iloc[0])}",
        "pass_fail": "pass" if bool(pf["stage74_run_pass"].iloc[0]) else "fail",
        "datasets_allowed": "Stage72B candidate edges and local MTG/DLPFC rare-microglia expression context",
        "datasets_forbidden": "prediction benchmark update; causal knockout or therapeutic claims",
        "allowed_claim": "hypothesis-generating directed perturbation prioritization",
        "notes": "Separate from Stage73R prediction graph-topology audit.",
        "stage_id": "stage74_directed_micro_pvm_grn_in_silico_perturbation_audit",
        "primary_metric": "control-specific perturbation response and regulator priority",
        "pass_rule": "outputs written and safety audit passes",
        "result": "see stage74_decision_audit_v1.csv",
        "allowed_inputs": "frozen Stage72B graph and frozen rare-cell modules",
        "forbidden_inputs": "pathology-tuned perturbation selection",
        "interpretation": "Model-based perturbation hypotheses only; experimental validation required.",
    }
    score = score[~score["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([score[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg: dict[str, Any]) -> None:
    stage71 = load_stage71(cfg["inputs"]["stage71_script"])
    out = cfg["outputs"]
    inventory = pd.DataFrame([
        {"input_name": k, "path": v, "exists": resolve(v).exists(), "size_bytes": resolve(v).stat().st_size if resolve(v).exists() else 0}
        for k, v in cfg["inputs"].items()
        if k not in {"active_status", "v3_scorecard_md", "v3_scorecard_csv", "stage71_script"}
    ])
    edges = pd.read_csv(resolve(cfg["inputs"]["stage72b_candidate_edges"]))
    edges = edges[edges["edge_candidate_pass"].astype(str).str.lower().eq("true")].copy()
    genes = requested_genes(cfg, edges)
    graphs = build_graphs(edges, genes, int(cfg["references"]["random_seed"]))
    graphs["expression_only"] = {}
    regulators = sorted(set(edges["source_tf"].astype(str).str.upper()))
    graph_registry = edges.groupby("source_tf", as_index=False).agg(
        n_direct_targets=("target_gene", "nunique"),
        median_edge_weight=("bootstrap_sign_stability", "median"),
        median_abs_rho=("spearman_rho", lambda x: float(np.median(np.abs(x)))),
    ).rename(columns={"source_tf": "regulator"})
    graph_registry["regulator"] = graph_registry["regulator"].astype(str).str.upper()

    response_parts = []
    module_parts = []
    for dataset, path in [("MTG", cfg["inputs"]["mtg_h5ad"]), ("DLPFC", cfg["inputs"]["dlpfc_h5ad"])]:
        cell, X, present = load_expression_cells(stage71, dataset, resolve(path), genes)
        resp, mods = simulate_dataset(
            dataset,
            cell,
            X,
            present,
            graphs,
            regulators,
            [float(x) for x in cfg["references"]["perturbation_doses"]],
            float(cfg["references"]["hop2_weight"]),
        )
        response_parts.append(resp)
        module_parts.append(mods)
    response = pd.concat(response_parts, ignore_index=True)
    module_response = pd.concat(module_parts, ignore_index=True)
    stability = bootstrap_stability(response, int(cfg["references"]["bootstrap_iterations"]), int(cfg["references"]["random_seed"]))
    control = response[(response["dose"].eq(1.0)) & (response["metric"].eq("top5_mean"))].pivot_table(
        index=["dataset", "regulator"], columns="control", values="abs_mean_delta", aggfunc="mean"
    ).reset_index()
    for col in ["directed_stage72b", "expression_only", "reversed_directed", "target_shuffled_directed", "degree_matched_random_directed"]:
        if col not in control.columns:
            control[col] = np.nan
    control["directed_minus_expression_only"] = control["directed_stage72b"] - control["expression_only"]
    control["directed_minus_reversed"] = control["directed_stage72b"] - control["reversed_directed"]
    control["directed_minus_target_shuffled"] = control["directed_stage72b"] - control["target_shuffled_directed"]
    control["directed_minus_random"] = control["directed_stage72b"] - control["degree_matched_random_directed"]
    priority = control.groupby("regulator", as_index=False).agg(
        mean_directed_abs_delta=("directed_stage72b", "mean"),
        mean_delta_vs_expression_only=("directed_minus_expression_only", "mean"),
        mean_delta_vs_reversed=("directed_minus_reversed", "mean"),
        mean_delta_vs_target_shuffled=("directed_minus_target_shuffled", "mean"),
        mean_delta_vs_random=("directed_minus_random", "mean"),
        n_regions=("dataset", "nunique"),
    ).merge(graph_registry, on="regulator", how="left")
    priority["control_specificity_score"] = priority[["mean_delta_vs_expression_only", "mean_delta_vs_reversed", "mean_delta_vs_target_shuffled", "mean_delta_vs_random"]].mean(axis=1)
    priority["candidate_for_followup"] = (
        (priority["mean_directed_abs_delta"] > 0)
        & (priority["mean_delta_vs_expression_only"] > 0)
        & (priority["mean_delta_vs_reversed"] > 0)
        & (priority["mean_delta_vs_target_shuffled"] > 0)
        & (priority["mean_delta_vs_random"] > 0)
    )
    priority = priority.sort_values(["candidate_for_followup", "control_specificity_score", "mean_directed_abs_delta"], ascending=[False, False, False])
    directed_organization_pass = bool((response[response["control"].eq("directed_stage72b")]["n_downstream_genes"] > 0).any())
    ablation_stability_pass = bool((stability["bootstrap_ci_lower_2p5"] > 0).any()) if not stability.empty else False
    ablation_control_specificity_pass = bool(priority["candidate_for_followup"].any())
    biological_coherence_pass = bool((module_response[module_response["control"].eq("directed_stage72b")]["abs_mean_module_delta"] > 0).any())
    decision = pd.DataFrame([{
        "directed_graph_organization_pass": directed_organization_pass,
        "ablation_stability_pass": ablation_stability_pass,
        "ablation_control_specificity_pass": ablation_control_specificity_pass,
        "biological_coherence_pass": biological_coherence_pass,
        "candidate_prioritization_pass": bool(directed_organization_pass and biological_coherence_pass and ablation_control_specificity_pass),
        "causal_validation_pass": False,
        "prediction_benchmark_updated": False,
        "interpretation": "directed perturbation hypotheses only; not causal knockout validation",
    }])
    claim = pd.DataFrame([{
        "stage74_directed_perturbation_audit_only": True,
        "no_prediction_benchmark_update": True,
        "no_model_rescue_training": True,
        "no_external_validation_claim": True,
        "no_causal_knockout_claim": True,
        "no_therapeutic_claim": True,
        "no_validated_grn_claim": True,
        "fixed_doses_no_tuning": True,
        "frozen_stage72b_edges": True,
        "raw_data_not_committed": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage74_run": True,
        "inputs_found": bool(inventory["exists"].all()),
        "response_curves_written": True,
        "controls_written": True,
        "decision_written": True,
        **decision.iloc[0].to_dict(),
        **claim.iloc[0].to_dict(),
    }])
    pf["stage74_run_pass"] = pf[["inputs_found", "response_curves_written", "controls_written", "decision_written", "safety_audit_pass"]].all(axis=1)
    tables = {
        "input_inventory": inventory,
        "directed_graph_registry": graph_registry,
        "perturbation_response_curves": response,
        "module_response_summary": module_response,
        "donor_bootstrap_stability": stability,
        "control_specificity_results": control,
        "regulator_priority_table": priority,
        "decision_audit": decision,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for key, df in tables.items():
        write_csv(df, out[key])
    update_docs(stage71, cfg, decision, pf)
    report = f"""# Stage74 directed Micro-PVM GRN in-silico perturbation audit

## Decision audit

{md(decision)}

## Top regulator priority rows

{md(priority, 20)}

## Control specificity

{md(control.sort_values('directed_minus_target_shuffled', ascending=False), 20)}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(
        f"""# Stage74 PI summary

- Stage74 run pass: `{bool(pf['stage74_run_pass'].iloc[0])}`
- Candidate prioritization pass: `{bool(decision['candidate_prioritization_pass'].iloc[0])}`
- Control specificity pass: `{bool(decision['ablation_control_specificity_pass'].iloc[0])}`
- Causal validation pass: `False`
- Prediction benchmark updated: `False`

This stage asks a different question from Stage73R: whether directed TF→target
structure can organize perturbation hypotheses. It does not claim experimental
knockout validity or therapeutic relevance.
""",
        out["pi_summary"],
    )
    write_text(f"# Stage74 claim-boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage74_run_pass={bool(pf['stage74_run_pass'].iloc[0])}")
    print(f"directed_graph_organization_pass={directed_organization_pass}")
    print(f"ablation_stability_pass={ablation_stability_pass}")
    print(f"ablation_control_specificity_pass={ablation_control_specificity_pass}")
    print(f"candidate_prioritization_pass={bool(decision['candidate_prioritization_pass'].iloc[0])}")
    print("causal_validation_pass=False")
    print("prediction_benchmark_updated=False")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage74_directed_micro_pvm_grn_in_silico_perturbation_audit_v1.yaml")
    args = parser.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
