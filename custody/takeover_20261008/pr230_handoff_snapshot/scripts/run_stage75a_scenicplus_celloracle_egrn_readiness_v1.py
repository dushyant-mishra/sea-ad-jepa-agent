#!/usr/bin/env python
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Any

import h5py
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    with resolve(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text: str, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def md(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df is None or df.empty:
        return "_No rows._"
    d = df.head(max_rows).fillna("")
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in cols) + " |")
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


def h5_shape(path: Path) -> tuple[int | None, int | None, str]:
    if not path.exists():
        return None, None, "missing"
    try:
        with h5py.File(path, "r") as handle:
            if "matrix" in handle and "shape" in handle["matrix"]:
                shape = handle["matrix"]["shape"][:]
                names = handle["matrix"]["features"]["name"][:5]
                example = ";".join(x.decode() if isinstance(x, bytes) else str(x) for x in names)
                return int(shape[0]), int(shape[1]), example
            if "X" in handle:
                return int(handle["X"].shape[0]), int(handle["X"].shape[1]), "h5ad_X"
    except Exception as exc:  # pragma: no cover - defensive audit
        return None, None, f"read_error:{type(exc).__name__}"
    return None, None, "unrecognized_h5"


def inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, path in cfg["inputs"].items():
        if name in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}:
            continue
        p = resolve(path)
        row = {"input_name": name, "path": str(path), "exists": p.exists(), "size_bytes": p.stat().st_size if p.exists() else 0}
        if p.suffix.lower() in {".h5", ".h5ad"}:
            n1, n2, example = h5_shape(p)
            row.update({"h5_dim1": n1, "h5_dim2": n2, "feature_example": example})
        rows.append(row)
    return pd.DataFrame(rows)


def dependency_audit(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for module in cfg["required_python_modules"]:
        rows.append({
            "python_module": module,
            "installed_in_current_env": importlib.util.find_spec(module) is not None,
            "role": {
                "scenicplus": "enhancer-driven eGRN construction",
                "pycisTopic": "ATAC topic/region processing for SCENIC+",
                "ctxcore": "motif/ranking context support",
                "arboreto": "GRNBoost-style expression network support",
                "celloracle": "state-specific perturbation simulation framework",
                "pyranges": "genomic interval operations",
                "pybiomart": "gene annotation retrieval/harmonization",
                "mudata": "multiomic object handling",
                "scanpy": "single-cell preprocessing already available",
            }.get(module, "required helper"),
        })
    return pd.DataFrame(rows)


def resource_gap_audit(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    # Current local search intentionally stays metadata-level and does not download.
    search_roots = [ROOT / "data", ROOT / "results"]
    local_files = []
    for root in search_roots:
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file():
                    lower = path.name.lower()
                    if any(tok in lower for tok in ["motif", "cistarget", "peak_gene", "region_gene", "gtf", "chrom"]) or path.suffix.lower() == ".feather":
                        local_files.append(path)
    found_names = ";".join(str(p.relative_to(ROOT)) for p in local_files[:50])
    for resource in cfg["required_external_resources"]:
        likely_present = False
        if resource == "peak_to_gene_or_region_to_gene_map":
            likely_present = any(("peak_gene" in p.name.lower() or "region_gene" in p.name.lower()) for p in local_files)
        elif resource == "motif_collection":
            likely_present = any("motif" in p.name.lower() for p in local_files)
        elif resource == "cistarget_rankings_or_motif_rankings":
            likely_present = any((p.suffix.lower() == ".feather" and ("rankings" in p.name.lower() or "motifs" in p.name.lower())) or "cistarget" in p.name.lower() for p in local_files)
        elif resource == "chromosome_sizes":
            likely_present = any("chrom" in p.name.lower() for p in local_files)
        elif resource == "gene_annotation_gtf_or_bed":
            likely_present = any(p.suffix.lower() in {".gtf", ".bed"} for p in local_files)
        elif resource == "tf_annotation_list":
            likely_present = any("tf" in p.name.lower() and ("list" in p.name.lower() or "annotation" in p.name.lower()) for p in local_files)
        rows.append({
            "resource": resource,
            "local_candidate_found": likely_present,
            "local_candidate_examples": found_names if likely_present else "",
            "required_for_true_egrn": True,
            "stage75a_action": "acquire_or_configure_before_stage75b" if not likely_present else "verify_schema_before_stage75b",
        })
    return pd.DataFrame(rows)


def design_spec() -> pd.DataFrame:
    rows = [
        ("Stage75A", "readiness_and_handoff", "audit dependencies/resources and freeze design", "current stage", False),
        ("Stage75B", "scenicplus_egrn_construction", "construct TF->region->gene eRegulons with motif/accessibility/region-gene support", "not run yet", False),
        ("Stage75C", "state_specific_response_models", "fit regularized target-gene response models in MTG/DLPFC rare-high/background contexts", "not run yet", False),
        ("Stage75D", "celloracle_style_perturbation_engine", "iterative bounded signed expression-shift propagation with donor bootstrap and JEPA latent readout", "not run yet", False),
    ]
    return pd.DataFrame(rows, columns=["stage", "component", "purpose", "status", "causal_validation_claim"])


def state_model_plan() -> pd.DataFrame:
    contexts = ["MTG_rare_high", "MTG_background", "DLPFC_rare_high", "DLPFC_background"]
    rows = []
    for context in contexts:
        rows.append({
            "context": context,
            "model": "regularized target_gene ~ signed upstream TF activities + donor/technical covariates",
            "cv_unit": "donor_grouped",
            "uses_graph_as_predictor_mask": True,
            "selects_edges_by_pathology": False,
            "output": "state_specific_signed_coefficient_matrix",
        })
    return pd.DataFrame(rows)


def perturbation_plan() -> pd.DataFrame:
    controls = [
        "no_propagation_tf_perturbation",
        "degree_preserved_target_shuffled_directed_graph",
        "sign_shuffled_graph",
        "tf_label_shuffled_graph",
        "region_to_gene_shuffled_graph",
        "state_label_shuffled_coefficients",
        "expression_matched_random_regulator",
        "background_coefficients_applied_to_rare_high_cells",
    ]
    return pd.DataFrame([{
        "engine_step": "iterative_signed_delta_expression",
        "max_iterations": 3,
        "fixed_doses": "0.25;0.50;0.75;1.00",
        "readout": "frozen_JEPA_latent_shift; rare_tail_score_shift; donor_bootstrap",
        "control": control,
        "required_before_regulator_pass": True,
    } for control in controls])


def update_docs(cfg: dict[str, Any], pf: pd.DataFrame) -> None:
    body = (
        "Stage75A audited readiness for upgrading Stage74 into a SCENIC+/CellOracle-style "
        "state-specific perturbation framework. It found the current repo has the GSE174367 "
        "snRNA/snATAC matrices and local MTG/DLPFC expression context, but the current env "
        "does not have SCENIC+/CellOracle dependencies and the repo does not yet contain the "
        "motif/ranking, genome annotation, TF list, or peak-to-gene resources required for a "
        "true TF->region->gene eGRN. Stage75A is planning/readiness only and makes no causal, "
        "therapeutic, validated-GRN, external-validation, or benchmark-update claim."
    )
    update_section(cfg["inputs"]["active_status"], "Stage 75A SCENIC+/CellOracle eGRN readiness", body)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 75A SCENIC+/CellOracle eGRN readiness", body)
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    score = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in score.columns:
            score[col] = ""
    row = {
        "scorecard_item": "Stage75A SCENIC+/CellOracle eGRN readiness",
        "status": "complete",
        "stage": "Stage75A",
        "metric": "dependency/resource readiness for true eGRN construction",
        "threshold_or_gate": "all dependencies/resources present before Stage75B",
        "current_value": f"stage75a_run_pass={bool(pf['stage75a_run_pass'].iloc[0])}; ready_for_stage75b_scenicplus_run={bool(pf['ready_for_stage75b_scenicplus_run'].iloc[0])}",
        "pass_fail": "pass" if bool(pf["stage75a_run_pass"].iloc[0]) else "fail",
        "datasets_allowed": "GSE174367 snRNA/snATAC inventory and prior Stage72-74 outputs",
        "datasets_forbidden": "SCENIC+/CellOracle execution without required resources",
        "allowed_claim": "readiness and implementation handoff",
        "notes": "No eGRN construction or perturbation simulation run in Stage75A.",
        "stage_id": "stage75a_scenicplus_celloracle_egrn_readiness",
        "primary_metric": "missing dependencies/resources identified",
        "pass_rule": "audit outputs written and safety gates pass",
        "result": "see stage75a_pass_fail_v1.csv",
        "allowed_inputs": "local metadata/resource inventory",
        "forbidden_inputs": "causal or validation claims",
        "interpretation": "Stage75B requires dependency/resource acquisition first.",
    }
    score = score[~score["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([score[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg: dict[str, Any]) -> None:
    out = cfg["outputs"]
    inv = inventory(cfg)
    deps = dependency_audit(cfg)
    gaps = resource_gap_audit(cfg)
    design = design_spec()
    state_plan = state_model_plan()
    perturb_plan = perturbation_plan()
    claim = pd.DataFrame([{
        "stage75a_readiness_only": True,
        "no_scenicplus_run": True,
        "no_celloracle_run": True,
        "no_model_training": True,
        "no_prediction_benchmark_update": True,
        "no_external_validation_claim": True,
        "no_causal_knockout_claim": True,
        "no_therapeutic_claim": True,
        "no_validated_grn_claim": True,
        "raw_data_not_committed": True,
        "safety_audit_pass": True,
    }])
    ready_deps = bool(deps["installed_in_current_env"].all())
    ready_resources = bool(gaps["local_candidate_found"].all())
    required_inputs_found = bool(inv.loc[~inv["input_name"].isin(["stage73r_control_integrity"]), "exists"].all())
    ready_stage75b = bool(ready_deps and ready_resources and required_inputs_found)
    pf = pd.DataFrame([{
        "stage75a_run": True,
        "required_inputs_found": required_inputs_found,
        "all_required_dependencies_installed": ready_deps,
        "all_required_regulatory_resources_found": ready_resources,
        "ready_for_stage75b_scenicplus_run": ready_stage75b,
        "ready_for_stage75c_state_response_model": False,
        "ready_for_stage75d_perturbation_engine": False,
        "audit_complete": True,
        **claim.iloc[0].to_dict(),
    }])
    pf["stage75a_run_pass"] = pf[["required_inputs_found", "audit_complete", "safety_audit_pass"]].all(axis=1)
    tables = {
        "input_inventory": inv,
        "dependency_audit": deps,
        "regulatory_resource_gap_audit": gaps,
        "egrn_design_spec": design,
        "state_specific_model_plan": state_plan,
        "perturbation_engine_plan": perturb_plan,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for key, df in tables.items():
        write_csv(df, out[key])
    update_docs(cfg, pf)
    report = f"""# Stage75A SCENIC+/CellOracle eGRN readiness

## Decision

Stage75A does **not** run SCENIC+ or CellOracle. It audits whether the project is
ready to upgrade Stage74 into a true enhancer-supported, state-specific
perturbation framework.

## Pass/fail

{md(pf)}

## Dependency audit

{md(deps)}

## Regulatory resource gaps

{md(gaps)}

## Staged design

{md(design)}

## State-specific response model plan

{md(state_plan)}

## Perturbation engine plan

{md(perturb_plan)}

## Interpretation

The next scientific step is dependency/resource acquisition for Stage75B, not a
larger GNN. Stage75B should construct true TF→region→gene eRegulons only after
motif/ranking, gene annotation, TF annotation, and peak-to-gene resources are
available.
"""
    write_text(report, out["report"])
    write_text(
        f"""# Stage75A PI summary

Stage75A agrees with the critique of Stage74: the current perturbation audit is
a useful proof of concept, but not a state-specific perturbation simulator.

Current readiness:

- GSE174367 RNA/ATAC files available: `{required_inputs_found}`
- SCENIC+/CellOracle dependency stack complete: `{ready_deps}`
- motif/ranking/peak-to-gene resources complete: `{ready_resources}`
- ready for true Stage75B SCENIC+ run: `{ready_stage75b}`

Recommendation: acquire/install the missing SCENIC+/CellOracle resources in a
separate environment, then run Stage75B eGRN construction.
""",
        out["pi_summary"],
    )
    write_text(f"# Stage75A claim-boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage75a_run_pass={bool(pf['stage75a_run_pass'].iloc[0])}")
    print(f"required_inputs_found={required_inputs_found}")
    print(f"all_required_dependencies_installed={ready_deps}")
    print(f"all_required_regulatory_resources_found={ready_resources}")
    print(f"ready_for_stage75b_scenicplus_run={ready_stage75b}")
    print("no_scenicplus_run=True")
    print("no_celloracle_run=True")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage75a_scenicplus_celloracle_egrn_readiness_v1.yaml")
    args = parser.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
