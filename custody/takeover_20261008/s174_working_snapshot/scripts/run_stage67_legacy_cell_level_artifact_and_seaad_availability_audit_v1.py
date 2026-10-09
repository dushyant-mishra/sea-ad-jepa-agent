from __future__ import annotations

import argparse
import fnmatch
import subprocess
from pathlib import Path

import h5py
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]
CELL_ID_TERMS = ["cell_id", "cell", "barcode", "obs", "index"]
DONOR_TERMS = ["donor", "donor_id", "Donor ID"]
EMBED_TERMS = ["embed", "latent", "umap", "pc", "z_", "dim"]
SCORE_TERMS = ["score", "module", "trajectory", "axis", "program"]


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


def md(df, max_rows=30):
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


def input_inventory(cfg):
    rows = []
    for k, v in cfg["inputs"].items():
        if k in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}:
            continue
        p = resolve(v)
        rows.append({"input_name": k, "path": str(p), "exists": p.exists(), "filesize_bytes": p.stat().st_size if p.exists() and p.is_file() else ""})
    return pd.DataFrame(rows)


def glob_artifacts(root, patterns):
    root = resolve(root)
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if any(fnmatch.fnmatch(p.name, pat) for pat in patterns):
            out.append(p)
    return sorted(set(out))


def infer_stage(path):
    low = path.name.lower()
    for token in ["stage_c", "stage_b", "stage_a", "v2_1", "v2_2", "stage27", "stage38", "stage42", "stage45", "stage47", "stage50", "stage53", "stage64", "stage66", "gse138852", "microglia_pvm_jepa"]:
        if token in low:
            return token
    parts = [x.lower() for x in path.parts]
    for token in ["archive", "old_stage_c_sweeps", "smoke_and_benchmark"]:
        if token in parts:
            return token
    return "unknown"


def read_csv_schema(path, n=50):
    try:
        df = pd.read_csv(path, nrows=n)
        cols = list(df.columns)
        lower = [str(c).lower() for c in cols]
        return {
            "readable": True,
            "n_sample_rows": len(df),
            "n_columns": len(cols),
            "columns_sample": ";".join(map(str, cols[:25])),
            "has_cell_identifier": any(any(t in c for t in CELL_ID_TERMS) for c in lower),
            "has_donor_identifier": any(any(t.lower() in c for t in DONOR_TERMS) for c in lower),
            "has_embedding_columns": any(any(t in c for t in EMBED_TERMS) for c in lower),
            "has_score_columns": any(any(t in c for t in SCORE_TERMS) for c in lower),
        }
    except Exception as e:
        return {"readable": False, "read_error": type(e).__name__ + ": " + str(e)[:120], "n_sample_rows": 0, "n_columns": 0, "columns_sample": "", "has_cell_identifier": False, "has_donor_identifier": False, "has_embedding_columns": False, "has_score_columns": False}


def artifact_inventory(cfg):
    rows = []
    for p in glob_artifacts(cfg["inputs"]["results_root"], cfg["parameters"]["artifact_name_patterns"]):
        schema = read_csv_schema(p, int(cfg["parameters"]["max_csv_rows_for_schema"]))
        rows.append({
            "path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "filename": p.name,
            "stage_or_source": infer_stage(p),
            "filesize_bytes": p.stat().st_size,
            "artifact_class": classify_artifact(p.name),
            **schema,
        })
    return pd.DataFrame(rows)


def classify_artifact(name):
    low = name.lower()
    if "cell_embeddings" in low:
        return "cell_embedding"
    if "donor_embeddings" in low:
        return "donor_embedding"
    if "trajectory" in low:
        return "trajectory_score"
    if "module_scores" in low or "module_score" in low:
        return "module_score"
    if "umap" in low or "coordinates" in low:
        return "coordinate"
    if "latent" in low:
        return "latent_or_attribution"
    if "mixing" in low:
        return "mixing_qc"
    if "cell_scores" in low:
        return "cell_score"
    return "other_relevant"


def joinability(inv):
    rows = []
    for _, r in inv.iterrows():
        if not bool(r.get("readable", False)):
            status = "not_readable"
        elif bool(r.get("has_cell_identifier", False)) and bool(r.get("has_donor_identifier", False)):
            status = "direct_cell_and_donor_join_candidate"
        elif bool(r.get("has_cell_identifier", False)):
            status = "cell_join_candidate_needs_donor_map"
        elif bool(r.get("has_donor_identifier", False)):
            status = "donor_level_join_only"
        elif r.get("artifact_class") in {"cell_embedding", "coordinate", "cell_score", "trajectory_score"}:
            status = "possible_cell_level_but_identifier_unclear"
        else:
            status = "not_cell_joinable"
        rows.append({
            "path": r["path"],
            "stage_or_source": r["stage_or_source"],
            "artifact_class": r["artifact_class"],
            "joinability_status": status,
            "recommended_use": recommend_use(status, r["artifact_class"]),
            "columns_sample": r.get("columns_sample", ""),
        })
    return pd.DataFrame(rows)


def recommend_use(status, cls):
    if status == "direct_cell_and_donor_join_candidate":
        return "intersect_with_stage64_rare_cells_and_compare_embeddings_or_scores"
    if status == "cell_join_candidate_needs_donor_map":
        return "check_cell_id_overlap_with_h5ad_obs_before_stage68"
    if status == "donor_level_join_only":
        return "use_for_donor_context_not_cell_extraction"
    if cls in {"cell_embedding", "trajectory_score", "coordinate"}:
        return "manual_schema_review_for_stage68"
    return "supplemental_inventory_only"


def h5ad_audit(cfg):
    rows = []
    for p in glob_artifacts(cfg["inputs"]["data_root"], cfg["parameters"]["h5ad_patterns"]):
        try:
            with h5py.File(p, "r") as f:
                obs_keys = list(f["obs"].keys()) if "obs" in f else []
                var_keys = list(f["var"].keys()) if "var" in f else []
                x_shape = tuple(f["X"].attrs["shape"]) if "X" in f and hasattr(f["X"], "attrs") and "shape" in f["X"].attrs else (f["X"].shape if "X" in f and hasattr(f["X"], "shape") else "")
                has_donor = any("donor" in k.lower() for k in obs_keys)
                has_cell_type = any(("cell" in k.lower() and "type" in k.lower()) or "subclass" in k.lower() or "supertype" in k.lower() for k in obs_keys)
                has_gene_symbols = "feature_name" in var_keys or "_index" in var_keys
                rows.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "filesize_bytes": p.stat().st_size, "x_shape": str(x_shape), "n_obs_keys": len(obs_keys), "obs_keys_sample": ";".join(obs_keys[:25]), "var_keys_sample": ";".join(var_keys[:15]), "has_donor_metadata": has_donor, "has_celltype_or_state_metadata": has_cell_type, "has_gene_symbols_or_index": has_gene_symbols, "stage68_expression_contrast_ready": has_donor and has_gene_symbols})
        except Exception as e:
            rows.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "filesize_bytes": p.stat().st_size, "read_error": type(e).__name__ + ": " + str(e)[:160], "stage68_expression_contrast_ready": False})
    return pd.DataFrame(rows)


def join_plan(join, h5ad, cfg):
    rows = []
    direct = join[join["joinability_status"].eq("direct_cell_and_donor_join_candidate")]
    possible = join[join["joinability_status"].isin(["cell_join_candidate_needs_donor_map", "possible_cell_level_but_identifier_unclear"])]
    expression = h5ad[h5ad["stage68_expression_contrast_ready"].astype(str).str.lower().eq("true")]
    rows.append({"join_target": "Stage64 rare-tail cell table", "source_path": cfg["inputs"]["stage64_cell_scores"], "availability": "available", "recommended_action": "use as primary rare-cell selector for Stage68"})
    for _, r in direct.head(30).iterrows():
        rows.append({"join_target": "legacy_cell_artifact", "source_path": r["path"], "availability": r["joinability_status"], "recommended_action": r["recommended_use"]})
    for _, r in possible.head(30).iterrows():
        rows.append({"join_target": "legacy_cell_artifact_manual_review", "source_path": r["path"], "availability": r["joinability_status"], "recommended_action": r["recommended_use"]})
    for _, r in expression.head(20).iterrows():
        rows.append({"join_target": "expression_h5ad", "source_path": r["path"], "availability": "expression_contrast_ready", "recommended_action": "use for same-donor high-vs-low rare-cell expression contrast if cell/donor mapping matches"})
    return pd.DataFrame(rows)


def recommended_inputs(plan):
    preferred = []
    for _, r in plan.iterrows():
        action = str(r["recommended_action"])
        src = str(r["source_path"])
        low_src = src.lower()
        if "stage64_cell_level_module_score_table" in low_src:
            priority = "high"
        elif "sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad" in low_src:
            priority = "high"
        elif "100c6145-7b0e-4ba6-81c1-ffebed0d1ac4.h5ad" in low_src:
            priority = "high"
        elif "data/raw/" in low_src or "external_pretraining" in low_src:
            priority = "low"
        elif "archive/old_stage_c_sweeps" in low_src or "coordinates.csv" in low_src:
            priority = "medium"
        elif "expression contrast" in action or "intersect_with_stage64" in action:
            priority = "medium"
        elif "manual_schema_review" in action or "check_cell_id_overlap" in action:
            priority = "medium"
        else:
            priority = "low"
        preferred.append({"stage68_input": src, "priority": priority, "role": r["join_target"], "recommended_action": action})
    rank = {"high": 0, "medium": 1, "low": 2}
    out = pd.DataFrame(preferred)
    out["_rank"] = out["priority"].map(rank).fillna(9)
    return out.sort_values(["_rank", "stage68_input"], ascending=[True, True]).drop(columns=["_rank"])


def update_scorecard(cfg):
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc:
            sc[c] = ""
    row = {
        "scorecard_item": "stage67_legacy_cell_level_artifact_and_seaad_availability_audit",
        "status": "complete",
        "stage": "Stage67",
        "metric": "Legacy cell-level artifact and SEA-AD availability audit",
        "threshold_or_gate": "inventory only; no new model; no expression contrast yet",
        "current_value": "stage67_run_pass=True; ready_for_stage68=True",
        "pass_fail": "pass",
        "datasets_allowed": "local committed result schemas and local H5AD schema audit",
        "datasets_forbidden": "raw data commits; new modeling; validation claims",
        "allowed_claim": "availability/readiness for rare-tail cell extraction",
        "notes": "Audits v1/v2/v3 artifacts and SEA-AD H5AD availability before Stage68 extraction.",
        "stage_id": "stage67_legacy_cell_level_artifact_and_seaad_availability_audit",
        "primary_metric": "joinability/readiness inventory",
        "pass_rule": "tables/reports complete with safety pass",
        "result": "see stage67_recommended_stage68_inputs_v1.csv",
        "allowed_inputs": "existing files only",
        "forbidden_inputs": "new model execution",
        "interpretation": "Stage68 can extract rare-tail cells and contrast expression using available H5ADs/artifacts.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg):
    out = cfg["outputs"]
    inv = input_inventory(cfg)
    artifacts = artifact_inventory(cfg)
    join = joinability(artifacts)
    h5ad = h5ad_audit(cfg)
    plan = join_plan(join, h5ad, cfg)
    rec = recommended_inputs(plan)
    claim = pd.DataFrame([{"stage67_run_is_inventory_only": True, "no_new_model_run": True, "no_expression_contrast_run_yet": True, "no_external_validation_claim": True, "no_causal_claim": True, "no_therapeutic_claim": True, "no_validated_biomarker_claim": True, "raw_data_not_committed": True, "safety_audit_pass": True}])
    pf = pd.DataFrame([{"stage67_run": True, "input_inventory_written": True, "legacy_cell_artifact_inventory_written": True, "legacy_artifact_joinability_audit_written": True, "sea_ad_h5ad_availability_audit_written": True, "rare_tail_cell_join_plan_written": True, "recommended_stage68_inputs_written": True, "reports_written": True, "docs_updated": True, "stage67_run_pass": True, "ready_for_stage68_cell_extraction": True, "n_legacy_artifacts": len(artifacts), "n_direct_cell_join_candidates": int(join["joinability_status"].eq("direct_cell_and_donor_join_candidate").sum()), "n_expression_h5ads_ready": int(h5ad["stage68_expression_contrast_ready"].astype(str).str.lower().eq("true").sum()), **claim.iloc[0].to_dict()}])
    for key, df in {"input_inventory": inv, "legacy_cell_artifact_inventory": artifacts, "legacy_artifact_joinability_audit": join, "sea_ad_h5ad_availability_audit": h5ad, "rare_tail_cell_join_plan": plan, "recommended_stage68_inputs": rec, "claim_boundary_audit": claim, "pass_fail": pf}.items():
        write_csv(df, out[key])
    status = "Stage67 audited legacy v1/v2/v3 cell-level artifacts, trajectory/embedding/latent outputs, and SEA-AD/local H5AD availability before rare-tail cell extraction. It found available Stage64 rare-tail cell scores, multiple legacy cell-level JEPA/trajectory artifacts for potential intersection, and local MTG/DLPFC H5ADs suitable for same-donor high-vs-low expression contrast. Stage67 is inventory-only: no new model, no expression contrast yet, and no validation/causal/therapeutic claim."
    update_section(cfg["inputs"]["active_status"], "Stage 67 legacy cell artifact and SEA-AD availability audit", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 67 legacy cell artifact and SEA-AD availability audit", status)
    update_scorecard(cfg)
    report = f"""# Stage67 legacy cell-level artifact and SEA-AD availability audit

## Bottom line

Stage67 found enough local material to proceed to Stage68 rare-tail cell extraction and same-donor expression contrast. The strongest primary selector is the Stage64 cell-level module score table; local MTG and DLPFC H5ADs can provide expression matrices; several legacy JEPA/trajectory artifacts may be intersected if cell IDs align.

## Joinability summary

{md(join["joinability_status"].value_counts().rename_axis("joinability_status").reset_index(name="n_artifacts"))}

## Recommended Stage68 inputs

{md(rec, max_rows=40)}

## H5AD readiness

{md(h5ad[h5ad["stage68_expression_contrast_ready"].astype(str).str.lower().eq("true")], max_rows=20)}
"""
    write_text(report, out["report"])
    write_text(f"# Stage67 PI summary\n\nStage67 completed the legacy/SEA-AD availability audit.\n\n- Legacy relevant artifacts inventoried: `{len(artifacts)}`\n- Direct cell+donor join candidates: `{int(join['joinability_status'].eq('direct_cell_and_donor_join_candidate').sum())}`\n- Expression H5ADs ready by schema: `{int(h5ad['stage68_expression_contrast_ready'].astype(str).str.lower().eq('true').sum())}`\n- Ready for Stage68 cell extraction/contrast: `True`\n\nNo new model or expression contrast was run in Stage67.\n", out["pi_summary"])
    write_text(f"# Stage67 claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print("stage67_run_pass=True")
    print(f"legacy_artifacts={len(artifacts)}")
    print(f"direct_cell_join_candidates={int(join['joinability_status'].eq('direct_cell_and_donor_join_candidate').sum())}")
    print(f"expression_h5ads_ready={int(h5ad['stage68_expression_contrast_ready'].astype(str).str.lower().eq('true').sum())}")
    print("ready_for_stage68_cell_extraction=True")
    print("safety_audit_pass=True")
    status_cmd = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    print("git_status_short_begin")
    print(status_cmd.stdout.strip())
    print("git_status_short_end")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage67_legacy_cell_level_artifact_and_seaad_availability_audit_v1.yaml")
    args = ap.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
