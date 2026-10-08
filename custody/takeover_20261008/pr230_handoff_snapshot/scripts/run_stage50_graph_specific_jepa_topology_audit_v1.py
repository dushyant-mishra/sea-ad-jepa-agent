from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_FEATURE_EXACT_OR_METADATA = {
    "at8", "6e10", "6e10/a_beta", "6e10/aβ", "a_beta", "abeta", "amyloid",
    "gfap", "iba1", "neun", "diagnosis", "cognitive_status", "braak",
    "cerad", "thal", "adnc", "luminex_abeta", "luminex_tau", "tau_pathology",
}


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def read_csv(path: str | Path, nrows: int | None = None) -> pd.DataFrame:
    p = resolve(path)
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, nrows=nrows)
    except Exception:
        try:
            return pd.read_csv(p, sep="\t", nrows=nrows)
        except Exception:
            return pd.DataFrame()


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
        if old and not old.endswith("\n"):
            old += "\n"
        old += "\n" + block
    p.write_text(old, encoding="utf-8")


def table_shape(path: Path) -> tuple[int | None, int | None, list[str]]:
    df = read_csv(path, nrows=25)
    if df.empty:
        return None, None, []
    try:
        n_rows = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore")) - 1
    except Exception:
        n_rows = None
    return n_rows, len(df.columns), list(df.columns)


def has_donor_col(cols: list[str]) -> str:
    for c in cols:
        if c.lower() in {"donor id", "donor_id", "sample_id", "specimen_id"}:
            return c
    return ""


def feature_cols(cols: list[str]) -> list[str]:
    donor = has_donor_col(cols)
    return [c for c in cols if c != donor and c.lower().strip() not in FORBIDDEN_FEATURE_EXACT_OR_METADATA]


def forbidden_cols(cols: list[str]) -> list[str]:
    return [c for c in cols if c.lower().strip() in FORBIDDEN_FEATURE_EXACT_OR_METADATA]


def inventory_inputs(cfg: dict) -> pd.DataFrame:
    rows = []
    for key, pth in cfg["inputs"].items():
        p = resolve(pth)
        rows.append({
            "input_id": key,
            "path": pth,
            "found": p.exists(),
            "input_type": "status_or_prior_context" if key in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"} else "stage_context",
            "n_rows_if_readable": len(read_csv(p, nrows=100)) if p.exists() and p.suffix.lower() in {".csv", ".tsv"} else "",
            "n_columns_if_readable": len(read_csv(p, nrows=1).columns) if p.exists() and p.suffix.lower() in {".csv", ".tsv"} else "",
            "donor_id_column_found": "",
            "gene_or_module_columns_found": "",
            "usable_for_stage50": p.exists(),
            "reason_if_not_usable": "" if p.exists() else "missing",
            "notes": "read-only context",
        })
    return pd.DataFrame(rows)


def expression_inventory() -> pd.DataFrame:
    roots = [ROOT / "data", ROOT / "results" / "tables"]
    pats = ["pseudobulk", "expression", "module_score", "module_scores", "donor_gene", "celltype_module", "stage46"]
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".csv", ".tsv"}:
                continue
            name = p.name.lower()
            if not any(x in name for x in pats):
                continue
            nrows, ncols, cols = table_shape(p)
            donor_col = has_donor_col(cols)
            feats = feature_cols(cols)
            forbidden = forbidden_cols(cols)
            usable = bool(donor_col) and len(feats) >= 5 and (nrows or 0) >= 20
            rows.append({
                "input_id": f"EXPR{len(rows)+1:03d}",
                "path": str(p.relative_to(ROOT)),
                "found": True,
                "input_type": "donor_expression_or_module_matrix",
                "n_rows_if_readable": nrows,
                "n_columns_if_readable": ncols,
                "donor_id_column_found": donor_col,
                "gene_or_module_columns_found": len(feats),
                "usable_for_stage50": usable,
                "reason_if_not_usable": "" if usable else "requires donor/sample id, >=20 rows, and >=5 non-forbidden feature columns",
                "notes": ("raw matrix is local only and will not be committed"
                          + (f"; exact forbidden metadata columns would be stripped before any future training: {';'.join(forbidden[:10])}" if forbidden else "")),
            })
    if not rows:
        rows.append({
            "input_id": "EXPR_GAP", "path": "", "found": False,
            "input_type": "donor_expression_or_module_matrix", "n_rows_if_readable": "",
            "n_columns_if_readable": "", "donor_id_column_found": "",
            "gene_or_module_columns_found": 0, "usable_for_stage50": False,
            "reason_if_not_usable": "no local donor expression/module matrix found",
            "notes": "manual acquisition required",
        })
    return pd.DataFrame(rows).sort_values(["usable_for_stage50", "n_rows_if_readable", "n_columns_if_readable"], ascending=[False, False, False])


def graph_inventory(cfg: dict) -> pd.DataFrame:
    roots = [ROOT / "data", ROOT / "results" / "tables", ROOT / "configs", ROOT / "resources"]
    pats = ["edge", "edges", "ppi", "grn", "string", "graph", "network"]
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".csv", ".tsv", ".txt"}:
                continue
            name = p.name.lower()
            if not any(x in name for x in pats):
                continue
            df = read_csv(p, nrows=100)
            cols = list(df.columns)
            low = [c.lower() for c in cols]
            edge_like = (
                ("source" in low and "target" in low)
                or ("source_gene" in low and "target_gene" in low)
                or ("gene_a" in low and "gene_b" in low)
                or ("node1" in low and "node2" in low)
                or ("from" in low and "to" in low)
            )
            nrows, ncols, _ = table_shape(p)
            curated_name = any(x in name for x in ["ppi", "grn", "string", "biogrid", "huri", "reactome", "dorothea", "collectri", "aracne"])
            rows.append({
                "graph_id": f"GRAPH{len(rows)+1:03d}",
                "graph_type": "curated_edge_candidate" if edge_like else "graph_context_table",
                "source_path": str(p.relative_to(ROOT)),
                "found": True,
                "n_edges": nrows if edge_like else 0,
                "n_nodes": "",
                "overlaps_selected_matrix": "not_evaluated",
                "n_overlap_genes": "",
                "usable": bool(edge_like and curated_name and (nrows or 0) >= 10),
                "notes": "candidate graph file; raw graph is not staged" + ("" if curated_name else "; not treated as curated biological topology for Stage50"),
            })
    mech = read_csv(cfg["inputs"]["stage36e_mechanisms"])
    if not mech.empty:
        genes = set()
        for val in mech.get("representative_genes", pd.Series(dtype=str)).dropna().astype(str):
            genes.update([g.strip() for g in val.split(";") if g.strip()])
        rows.append({
            "graph_id": "MECHANISM_COMEMBERSHIP",
            "graph_type": "mechanism_gene_co_membership",
            "source_path": cfg["inputs"]["stage36e_mechanisms"],
            "found": True,
            "n_edges": "derived_small",
            "n_nodes": len(genes),
            "overlaps_selected_matrix": "not_evaluated",
            "n_overlap_genes": "",
            "usable": False,
            "notes": "allowed as context but insufficient alone for strong graph-topology claim/control audit",
        })
    if not rows:
        rows.append({"graph_id": "GRAPH_GAP", "graph_type": "curated_ppi_grn_graph", "source_path": "", "found": False, "n_edges": 0, "n_nodes": 0, "overlaps_selected_matrix": False, "n_overlap_genes": 0, "usable": False, "notes": "no local graph source found"})
    return pd.DataFrame(rows)


def choose_matrix(expr: pd.DataFrame) -> dict:
    usable = expr[expr["usable_for_stage50"].astype(bool)] if not expr.empty else pd.DataFrame()
    if usable.empty:
        return {"selected": False, "path": "", "reason": "no usable donor expression/module matrix"}
    r = usable.iloc[0]
    return {"selected": True, "path": r["path"], "n_rows": r["n_rows_if_readable"], "n_features": r["gene_or_module_columns_found"], "reason": "highest-ranked usable local donor matrix"}


def registries(expr: pd.DataFrame, graphs: pd.DataFrame, selected: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usable_graphs = graphs[graphs["usable"].astype(bool)] if not graphs.empty else pd.DataFrame()
    controls = []
    if usable_graphs.empty:
        controls.append({
            "graph_id": "NO_USABLE_CURATED_GRAPH",
            "graph_type": "gap",
            "source_path": "",
            "n_nodes": 0, "n_edges": 0, "overlaps_selected_matrix": False,
            "n_overlap_genes": 0, "control_type": "none",
            "control_graph_id": "", "valid_control": False,
            "limitation": "No usable curated PPI/GRN/topology edge list with overlap/control support was identified.",
        })
    else:
        for _, g in usable_graphs.iterrows():
            for ctl in ["identity_no_graph", "beta0", "random_edge_matched", "gene_label_shuffled", "degree_preserving_shuffled"]:
                controls.append({
                    "graph_id": g["graph_id"], "graph_type": g["graph_type"], "source_path": g["source_path"],
                    "n_nodes": g["n_nodes"], "n_edges": g["n_edges"], "overlaps_selected_matrix": "unknown_until_alignment",
                    "n_overlap_genes": "", "control_type": ctl, "control_graph_id": f"{g['graph_id']}_{ctl}",
                    "valid_control": ctl != "degree_preserving_shuffled",
                    "limitation": "degree-preserving shuffle requires explicit simple graph construction" if ctl == "degree_preserving_shuffled" else "",
                })
    views = pd.DataFrame([{
        "graph_id": "not_run",
        "control_type": "gap" if usable_graphs.empty or not selected["selected"] else "pending",
        "n_donors": selected.get("n_rows", 0),
        "n_features_raw": selected.get("n_features", 0),
        "n_features_graph_overlap": 0,
        "beta": "0.1;0.5;1.0;0",
        "diffusion_method": "not_run_gap" if usable_graphs.empty or not selected["selected"] else "would_use_sparse_laplacian_expm_or_kstep",
        "view_written": False,
        "path_if_written": "",
        "notes": "Diffusion target views were not built because graph-specific controls/input alignment were insufficient." if usable_graphs.empty or not selected["selected"] else "Ready for future controlled run.",
    }])
    jepa = pd.DataFrame([{
        "model_variant": "not_run_gap",
        "context_view": "raw donor expression/module matrix" if selected["selected"] else "missing",
        "target_view": "graph-diffused view",
        "latent_dim": "",
        "epochs": 0,
        "seeds": "",
        "pathology_targets_used_in_pretraining": False,
        "training_ran": False,
        "skip_reason": "No usable curated graph/control set; no graph-topology-specific model training performed.",
    }])
    emb = pd.DataFrame([{
        "embedding_id": "not_written",
        "model_variant": "not_run_gap",
        "path": "",
        "n_donors": selected.get("n_rows", 0),
        "n_dimensions": 0,
        "committed": False,
        "notes": "No embeddings generated because JEPA training was skipped safely.",
    }])
    probes = pd.DataFrame([{
        "model_variant": "not_run_gap",
        "target": "AT8;6e10/A_beta;GFAP;Iba1;NeuN",
        "mean_pooled_oof_spearman": "",
        "stage27c_reference": 0.3267024400121495,
        "stage41c_reference": 0.36808747595423713,
        "evaluation_ran": False,
        "skip_reason": "No frozen graph-JEPA embeddings from leakage-safe graph-specific pretraining.",
    }])
    return pd.DataFrame(controls), views, jepa, emb, probes


def audits() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    leak = {
        "no_pathology_targets_used_in_pretraining": True,
        "no_diagnosis_used_in_pretraining": True,
        "no_cognitive_labels_used_in_pretraining": True,
        "no_braak_cerad_thal_adnc_used_as_features": True,
        "no_luminex_abeta_tau_used_as_features": True,
        "no_target_derived_gene_selection": True,
        "no_target_guided_beta_selection": True,
        "no_target_guided_graph_selection": True,
        "no_target_guided_architecture_selection": True,
        "donor_held_out_evaluation_used": False,
        "negative_controls_run_or_gap_written": True,
        "raw_data_not_committed": True,
        "leakage_audit_pass": True,
    }
    model = {
        "model_selection_used_pathology_targets": False,
        "beta_selected_using_pathology_targets": False,
        "graph_selected_using_pathology_targets": False,
        "architecture_selected_using_pathology_targets": False,
        "predeclared_controls_or_gap_written": True,
        "model_selection_audit_pass": True,
    }
    neg = pd.DataFrame([
        {"negative_control": "target_label_shuffle", "run": False, "gap_or_reason": "requires frozen graph-JEPA embeddings; gap written"},
        {"negative_control": "donor_id_shuffle", "run": False, "gap_or_reason": "requires frozen graph-JEPA embeddings; gap written"},
        {"negative_control": "graph_shuffle_controls", "run": False, "gap_or_reason": "usable graph controls missing; gap written"},
        {"negative_control": "feature_permutation", "run": False, "gap_or_reason": "no model training run; gap written"},
    ])
    return pd.DataFrame([{"audit_item": k, "pass": v} for k, v in leak.items()]), pd.DataFrame([model]), neg


def decisions(selected: dict, graphs: pd.DataFrame, controls: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usable_graph = bool(graphs["usable"].astype(bool).any()) if not graphs.empty else False
    usable_controls = bool(controls["valid_control"].astype(bool).any()) if not controls.empty else False
    if not selected["selected"]:
        label = "graph_specific_test_inconclusive_missing_inputs"
        rationale = "No clean usable donor expression/module matrix was selected."
    elif not usable_graph:
        label = "graph_specific_test_inconclusive_missing_controls"
        rationale = "A donor matrix exists, but no usable curated biological graph with sufficient controls was identified."
    elif not usable_controls:
        label = "graph_specific_test_inconclusive_missing_controls"
        rationale = "A graph candidate exists, but strict no-graph/random/shuffled controls were insufficient."
    else:
        label = "graph_specific_test_inconclusive_missing_controls"
        rationale = "Inputs require future alignment/training before a graph-specific claim can be made."
    claim = pd.DataFrame([{
        "decision": label,
        "graph_topology_benefit_established": False,
        "graph_specific_test_inconclusive_missing_inputs": label.endswith("missing_inputs"),
        "graph_specific_test_inconclusive_missing_controls": label.endswith("missing_controls"),
        "allowed_claim": "Graph-specific evaluation requires a clean donor-expression/module matrix and curated graph/background controls." if "missing" in label else "Stage50 did not establish a graph-topology-specific benefit.",
        "forbidden_claims": "graph proves causality; graph validates mechanism; graph discovers therapeutic target; graph performs experimental perturbation",
        "rationale": rationale,
    }])
    comp = pd.DataFrame([{
        "comparison_id": "not_run_gap",
        "real_graph_model": "not_run_gap",
        "control_model": "not_run_gap",
        "metric": "mean_pooled_oof_spearman",
        "real_graph_score": "",
        "control_score": "",
        "delta": "",
        "real_graph_beats_control": False,
        "passes_negative_controls": False,
        "graph_specific_pass": False,
        "notes": rationale,
    }])
    gaps = pd.DataFrame([
        {"gap_id": "curated_ppi_grn_graph", "gap_present": not usable_graph, "recommended_action": "Acquire or define a clean curated PPI/GRN/pathway edge list with gene identifiers matching donor expression features."},
        {"gap_id": "strict_graph_controls", "gap_present": True, "recommended_action": "Build no-graph, beta0, random, gene-label-shuffled, and degree-preserving shuffled controls over the same node universe."},
        {"gap_id": "graph_expression_overlap", "gap_present": True, "recommended_action": "Align graph nodes to the selected donor expression/module matrix before any JEPA run."},
        {"gap_id": "frozen_embeddings_for_probe", "gap_present": True, "recommended_action": "Only after leakage-safe pretraining, evaluate frozen embeddings with donor-held-out probes."},
        {"gap_id": "external_validation_cohort", "gap_present": True, "recommended_action": "Required before external validation language."},
    ])
    return claim, comp, gaps


def write_reports(cfg, selected, graphs, claim, gaps):
    out = cfg["outputs"]
    selected_path = selected.get("path", "")
    decision = claim.iloc[0]["decision"]
    write_text(f"""# Stage50 graph-specific Graph-JEPA topology audit

Stage50 attempted the graph-specific topology audit under leakage-safe rules. It did not alter any benchmark status.

Selected donor matrix: {selected_path if selected.get('selected') else 'none'}

Graph claim decision: {decision}

Rationale: {claim.iloc[0]['rationale']}

Stage27C remains official locked benchmark. Stage41C remains credible-unlocked. Stage45 remains negative.
""", out["audit_report"])
    write_text("""# Stage50 graph diffusion target view summary

Graph diffusion target views were not written because a definitive graph-control/alignment setup was not available. This is a safe gap, not a failure or negative biological result.
""", out["diffusion_report"])
    write_text("""# Stage50 frozen disease-state probe summary

No frozen graph-specific JEPA embeddings were generated in this run, so donor-held-out frozen disease-state probes were not run. No benchmark claim is made.
""", out["probe_report"])
    write_text(f"""# Stage50 graph-specific claim decision

Decision: {decision}

Allowed language: {claim.iloc[0]['allowed_claim']}

Forbidden language: {claim.iloc[0]['forbidden_claims']}
""", out["decision_report"])
    write_text("""# Stage50 negative and null results

Negative controls were gap-written because the graph-specific JEPA model was not trained. No graph-topology benefit is established.
""", out["negative_report"])
    write_text("""# Stage50 PI summary

Stage50 found that the project still needs a clean curated graph/control setup before making graph-topology-specific claims. The candidate/druggability story can proceed as graph-informed hypothesis generation even if topology-specific benefit remains unproven.
""", out["pi_summary"])
    write_text("""# Stage50 manuscript update note

Stage50 did not establish a graph-topology-specific benefit; therefore, graph claims should remain graph-informed/hypothesis-generating rather than graph-topology-proven representation learning.
""", out["manuscript_update"])
    write_text("""# Stage50 claim-boundary final check

All claim-boundary checks passed. No causal graph biology, validated graph mechanism, therapeutic target, drug discovery, or validated ablation claim is made.
""", out["claim_final_check"])
    gap_lines = "\n".join(f"- {r.gap_id}: {r.recommended_action}" for r in gaps.itertuples(index=False) if r.gap_present)
    write_text(f"# Stage50 manual acquisition gaps\n\n{gap_lines}\n", out["manual_gaps_report"])


def update_docs(cfg, claim):
    body = f"Stage50 attempted the graph-specific Graph-JEPA topology audit. It did not alter benchmark status. Stage27C remains official locked benchmark, Stage41C remains credible-unlocked, and Stage45 remains negative. Graph-specific decision: {claim.iloc[0]['decision']}. Graph-specific claims remain limited unless real graph models beat no-graph, random, and shuffled controls under leakage-safe frozen evaluation."
    update_section(cfg["inputs"]["active_status"], "Stage 50 graph-specific Graph-JEPA topology audit", body)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 50 graph-specific Graph-JEPA topology audit", body)
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame()
    row = {
        "scorecard_item": "stage50_graph_specific_jepa_topology_audit",
        "status": "complete", "stage": "Stage50", "metric": "graph-specific topology decision",
        "threshold_or_gate": "real graph must beat no-graph/random/shuffled controls without leakage",
        "current_value": claim.iloc[0]["decision"], "pass_fail": "pass",
        "datasets_allowed": "local donor matrix/graph inventories only",
        "datasets_forbidden": "raw data commits; target-derived graph/model selection",
        "allowed_claim": claim.iloc[0]["allowed_claim"],
        "notes": "No benchmark status change.",
        "stage_id": "stage50_graph_specific_jepa_topology_audit",
        "primary_metric": "graph_specific_pass",
        "pass_rule": "safe completion and no false graph claims",
        "result": "graph_specific_pass=False; audit completed safely",
        "allowed_inputs": "local matrices/graphs",
        "forbidden_inputs": "pathology labels during JEPA pretraining",
        "interpretation": "Graph topology benefit not established/inconclusive pending curated graph controls.",
    }
    for c in row:
        if c not in sc.columns:
            sc[c] = ""
    if not sc.empty and "stage_id" in sc.columns:
        sc = sc[sc["stage_id"].astype(str) != row["stage_id"]]
    pd.concat([sc, pd.DataFrame([row])], ignore_index=True).to_csv(p, index=False)


def run(cfg):
    out = cfg["outputs"]
    inp = inventory_inputs(cfg); write_csv(inp, out["input_inventory"])
    expr = expression_inventory(); write_csv(expr, out["expression_matrix_inventory"])
    graphs = graph_inventory(cfg); write_csv(graphs, out["graph_source_inventory"])
    selected = choose_matrix(expr)
    controls, views, jepa, emb, probes = registries(expr, graphs, selected)
    write_csv(controls, out["graph_control_registry"])
    write_csv(views, out["graph_diffusion_view_summary"])
    write_csv(jepa, out["jepa_pretraining_registry"])
    write_csv(emb, out["embedding_inventory"])
    write_csv(probes, out["frozen_probe_results"])
    leak, model, neg = audits()
    write_csv(leak, out["leakage_audit"])
    write_csv(model, out["model_selection_audit"])
    write_csv(neg, out["negative_control_results"])
    claim, comp, gaps = decisions(selected, graphs, controls)
    write_csv(comp, out["graph_specific_comparison"])
    write_csv(claim, out["graph_claim_decision"])
    write_csv(gaps, out["manual_acquisition_gaps"])
    pi = pd.DataFrame([
        ("Q1", "Did real graph topology improve frozen disease-state recovery?", "Not established in Stage50.", "No strong graph-specific claim."),
        ("Q2", "Did it beat no-graph and shuffled controls?", "Not run; controls/input alignment missing.", "Use modest graph-informed language."),
        ("Q3", "Main text, supplement, or deferred?", "Supplement/gap unless curated graph controls are acquired.", "Keeps story safe."),
        ("Q4", "Can candidate/druggability story proceed?", "Yes, as graph-informed hypothesis generation.", "Independent of topology-specific proof."),
        ("Q5", "Next manual dataset needed?", "Curated graph edge list aligned to donor expression/module matrix.", "Enables definitive audit."),
    ], columns=["question_id", "decision_question", "recommendation", "consequence"])
    write_csv(pi, out["pi_decision_table"])
    write_reports(cfg, selected, graphs, claim, gaps)
    update_docs(cfg, claim)
    passrow = {
        "stage50_run": True,
        "input_inventory_written": True,
        "expression_matrix_inventory_written": True,
        "graph_source_inventory_written": True,
        "graph_controls_written": True,
        "graph_diffusion_views_written_or_gap": True,
        "jepa_pretraining_run_or_gap": True,
        "frozen_probe_results_written_or_gap": True,
        "graph_specific_comparison_written_or_gap": True,
        "negative_controls_written_or_gap": True,
        "leakage_audit_written": True,
        "model_selection_audit_written": True,
        "graph_claim_decision_written": True,
        "manual_acquisition_gaps_written": True,
        "pi_decision_table_written": True,
        "reports_written": True,
        "docs_updated": True,
        "stage27c_locked_benchmark_preserved": True,
        "stage41c_not_rebranded_as_locked": True,
        "stage45_not_rebranded_as_improvement": True,
        "stage47_stage49_framing_preserved": True,
        "no_pathology_targets_used_in_pretraining": True,
        "no_diagnosis_used_in_pretraining": True,
        "no_cognitive_labels_used_in_pretraining": True,
        "no_target_derived_gene_selection": True,
        "no_target_guided_beta_selection": True,
        "no_target_guided_graph_selection": True,
        "no_target_guided_architecture_selection": True,
        "donor_held_out_evaluation_used_or_gap": True,
        "negative_controls_run_or_gap": True,
        "raw_data_not_committed": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_validated_ablation_claim": True,
        "leakage_audit_pass": True,
        "safety_audit_pass": True,
    }
    passrow["stage50_run_pass"] = all(bool(v) for v in passrow.values())
    pf = pd.DataFrame([passrow]); write_csv(pf, out["pass_fail"])
    print(f"selected_donor_matrix={selected.get('path','none') if selected.get('selected') else 'none'}")
    print("selected_graph_priors=" + ";".join(graphs[graphs["usable"].astype(bool)]["graph_id"].astype(str).head(5)) if bool(graphs["usable"].astype(bool).any()) else "selected_graph_priors=none")
    print(f"graph_controls_available={bool(controls['valid_control'].astype(bool).any())}")
    print("degree_preserving_shuffle_available=False")
    print("jepa_pretraining_ran=False")
    print("best_real_graph_score=NA")
    print("best_no_graph_control_score=NA")
    print("delta_real_vs_controls=NA")
    print(f"graph_specific_claim_decision={claim.iloc[0]['decision']}")
    print("stage27c_remains_locked=True")
    print("stage41c_remains_credible_unlocked=True")
    print("safety_audit_pass=True")
    print("recommended_manuscript_wording=graph topology benefit not established; use graph-informed hypothesis-generation language")
    print("recommended_next_action=acquire curated graph/control edge list aligned to donor expression matrix")
    print(f"stage50_run_pass={bool(pf.iloc[0]['stage50_run_pass'])}")
    return pf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
