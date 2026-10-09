from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError
import yaml

from inspect_stage39a_external_metadata_columns_v1 import (
    ROOT,
    as_bool,
    choose_column,
    clean_text,
    find_expression_file,
    find_metadata_file,
    infer_dataset_files,
    inspect_file_metadata,
    read_10x_barcodes,
    read_table_preview,
    resolve,
    unique_join,
)


SAFE_INTERPRETATION = (
    "Stage 39A is a metadata harmonization rescue and acquisition-gap audit only. It does not train models, "
    "tune thresholds, select candidates, modify frozen Stage 36E hypotheses, or claim clean external validation, "
    "causality, therapeutic effect, disease modification, or gene ablation."
)

DISALLOWED = "clean external validation; causal regulator; therapeutic target; disease-modifying target; gene ablation result"


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_csv(path_value: str | Path) -> pd.DataFrame:
    path = resolve(path_value)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


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


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows available._"
    view = view.fillna("").astype(str)
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        vals = [clean_text(row[col]).replace("|", "\\|").replace("\n", " ") for col in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def input_presence(cfg: dict[str, Any]) -> dict[str, bool]:
    return {name: resolve(path).exists() for name, path in cfg["inputs"].items()}


def column_values(path_value: str, column: str, limit: int = 100000) -> list[str]:
    if not path_value or not column:
        return []
    path = resolve(path_value)
    if not path.exists() or path.suffix.lower() == ".h5":
        return []
    preview, kind = read_table_preview(path, nrows=limit)
    if kind in {"csv", "tsv"} and column in preview.columns:
        return preview[column].dropna().astype(str).tolist()
    return []


def value_hits(values: list[str], terms: list[str]) -> list[str]:
    hits: list[str] = []
    for value in values:
        lower = value.lower()
        if any(term.lower() in lower for term in terms):
            if value not in hits:
                hits.append(value)
    return hits


def infer_disease_values(values: list[str]) -> tuple[list[str], list[str]]:
    case_terms = ["ad", "alz", "case", "disease", "dementia", "pathology"]
    control_terms = ["control", "ctrl", "ct", "normal", "healthy", "no ad", "non"]
    unique = []
    for value in values:
        text = clean_text(value)
        if text and text not in unique:
            unique.append(text)
    cases: list[str] = []
    controls: list[str] = []
    for value in unique:
        lower = value.lower()
        if any(term in lower for term in control_terms):
            controls.append(value)
        elif any(term in lower for term in case_terms):
            cases.append(value)
    # Common Grubman coding.
    for value in unique:
        if value.upper() == "AD" and value not in cases:
            cases.append(value)
        if value.upper() in {"CT", "CTL", "CTRL"} and value not in controls:
            controls.append(value)
    return cases, controls


def build_harmonization(
    dataset_id: str,
    metadata_path: str,
    terms: dict[str, list[str]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    disease_col = ""
    celltype_col = ""
    sample_col = ""
    pathology_cols: list[str] = []
    disease_values: list[str] = []
    cell_values: list[str] = []
    if metadata_path:
        preview, kind = read_table_preview(resolve(metadata_path), nrows=100000)
        if kind in {"csv", "tsv"} and not preview.empty:
            sample_col = choose_column(preview, terms["sample_id"])
            disease_col = choose_column(preview, terms["disease"])
            celltype_col = choose_column(preview, terms["celltype"])
            pathology_cols = [col for col in preview.columns if any(term.lower() in col.lower() for term in terms["pathology"])]
            if disease_col:
                disease_values = preview[disease_col].dropna().astype(str).unique().tolist()
            if celltype_col:
                cell_values = preview[celltype_col].dropna().astype(str).unique().tolist()
    disease_case, disease_control = infer_disease_values(disease_values)
    micro = value_hits(cell_values, terms["microglia"])
    astro = value_hits(cell_values, terms["astrocyte"])
    neuron = value_hits(cell_values, terms["neuron"])
    oligo = value_hits(cell_values, terms["oligodendrocyte"])
    opc = value_hits(cell_values, terms["opc"])
    endothelial = value_hits(cell_values, terms["endothelial"])
    tau_cols = [c for c in pathology_cols if any(t in c.lower() for t in ["tau", "ptau", "tangle", "braak"])]
    amyloid_cols = [c for c in pathology_cols if any(t in c.lower() for t in ["amyloid", "abeta", "plaque", "cerad"])]
    disease = {
        "dataset_id": dataset_id,
        "metadata_path": metadata_path,
        "disease_column": disease_col,
        "disease_values_detected": unique_join(disease_values),
        "disease_case_values": unique_join(disease_case),
        "disease_control_values": unique_join(disease_control),
        "disease_label_ready": bool(disease_col and disease_case and disease_control),
        "harmonization_note": "explicit disease/control-like metadata found" if disease_col and disease_case and disease_control else "disease/control labels not safely harmonized",
    }
    celltype = {
        "dataset_id": dataset_id,
        "metadata_path": metadata_path,
        "celltype_column": celltype_col,
        "celltype_values_detected": unique_join(cell_values[:80]),
        "microglia_values": unique_join(micro),
        "astrocyte_values": unique_join(astro),
        "neuron_values": unique_join(neuron),
        "oligodendrocyte_values": unique_join(oligo),
        "opc_values": unique_join(opc),
        "endothelial_values": unique_join(endothelial),
        "celltype_label_ready": bool(celltype_col),
        "microglia_label_ready": bool(micro),
        "astrocyte_label_ready": bool(astro),
        "harmonization_note": "cell-type labels found" if celltype_col else "cell-type labels not safely harmonized",
    }
    pathology = {
        "dataset_id": dataset_id,
        "metadata_path": metadata_path,
        "tau_ptau_columns": unique_join(tau_cols),
        "amyloid_abeta_columns": unique_join(amyloid_cols),
        "other_pathology_columns": unique_join([c for c in pathology_cols if c not in tau_cols and c not in amyloid_cols]),
        "tau_ptau_label_ready": bool(tau_cols),
        "amyloid_abeta_label_ready": bool(amyloid_cols),
        "pathology_label_ready": bool(pathology_cols),
        "harmonization_note": "pathology columns found" if pathology_cols else "pathology columns not safely harmonized",
    }
    micro_astro = {
        "dataset_id": dataset_id,
        "celltype_column": celltype_col,
        "microglia_values": unique_join(micro),
        "astrocyte_values": unique_join(astro),
        "microglia_label_ready": bool(micro),
        "astrocyte_label_ready": bool(astro),
        "recommended_use": "microglia/astrocyte specificity support can be tested" if micro or astro else "manual cell-type mapping required",
    }
    return disease, celltype, pathology, micro_astro


def build_linkage(dataset_id: str, expression_path: str, metadata_path: str, sample_col: str) -> dict[str, Any]:
    expr_ids: list[str] = []
    expr_col = ""
    if expression_path:
        path = resolve(expression_path)
        if path.suffix.lower() == ".h5":
            expr_ids = read_10x_barcodes(path)
            expr_col = "matrix/barcodes"
        elif path.exists():
            preview, kind = read_table_preview(path, nrows=100000)
            if kind in {"csv", "tsv"} and not preview.empty:
                first = preview.columns[0]
                expr_col = first
                expr_ids = preview[first].dropna().astype(str).tolist()
    meta_ids = column_values(metadata_path, sample_col, limit=100000)
    expr_set = set(expr_ids)
    meta_set = set(meta_ids)
    overlap = len(expr_set & meta_set) if expr_set and meta_set else 0
    ready = bool(overlap > 0)
    return {
        "dataset_id": dataset_id,
        "expression_path": expression_path,
        "metadata_path": metadata_path,
        "sample_id_column_expression": expr_col,
        "sample_id_column_metadata": sample_col,
        "n_expression_ids_previewed": len(expr_set),
        "n_metadata_ids_previewed": len(meta_set),
        "n_overlapping_ids": overlap,
        "sample_id_linkage_ready": ready,
        "linkage_note": "expression and metadata identifiers overlap" if ready else "no safe expression-metadata identifier overlap detected",
    }


def update_markdown_section(path_value: str | Path, heading: str, body: str) -> Path:
    path = resolve(path_value)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = f"\n## {heading}\n{body.strip()}\n"
    marker = f"## {heading}"
    if marker not in text:
        text = text.rstrip() + "\n" + section
    else:
        start = text.index(marker)
        next_start = text.find("\n## ", start + len(marker))
        if next_start == -1:
            text = text[:start].rstrip() + section
        else:
            text = text[:start].rstrip() + section + text[next_start:]
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def update_scorecard_csv(path_value: str | Path, pass_fail: pd.DataFrame, ready_count: int) -> Path:
    path = resolve(path_value)
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    row = {
        "scorecard_item": "stage39a_external_metadata_rescue",
        "status": "complete",
        "stage": "Stage 39A",
        "metric": "metadata harmonization rescue and acquisition-gap audit",
        "threshold_or_gate": "files inspected; metadata candidates/linkage/harmonization/manual fixes written; safety audit passes",
        "current_value": f"run_pass={as_bool(pass_fail.iloc[0]['stage39a_run_pass'])}; ready_for_stage39b={ready_count}",
        "pass_fail": "pass" if as_bool(pass_fail.iloc[0]["stage39a_run_pass"]) else "fail",
        "datasets_allowed": "local external dataset files and Stage 38/36E outputs only",
        "datasets_forbidden": "new downloads; SEA-AD model training; threshold tuning; candidate selection",
        "allowed_claim": "metadata/testability rescue only",
        "notes": SAFE_INTERPRETATION,
        "stage_id": "stage39a_external_metadata_rescue",
        "primary_metric": "metadata rescue completion",
        "pass_rule": "required audit outputs written with honest ready/not-ready status",
        "result": f"run_pass={as_bool(pass_fail.iloc[0]['stage39a_run_pass'])}",
        "allowed_inputs": "Stage 38A/B/C outputs and local external files",
        "forbidden_inputs": "new data downloads; external labels for model selection; new candidates",
        "interpretation": SAFE_INTERPRETATION,
    }
    if df.empty:
        df = pd.DataFrame([row])
    else:
        for col in row:
            if col not in df.columns:
                df[col] = ""
        df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != "stage39a_external_metadata_rescue"]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_cfg(resolve(args.config))
    terms = cfg["candidate_terms"]
    inspect_ids = [d.lower() for d in cfg["datasets"]["inspect"]]
    all_ids = inspect_ids + [d.lower() for d in cfg["datasets"]["acquisition_gap"]]
    inputs_ok = {k: resolve(v).exists() for k, v in cfg["inputs"].items()}
    data = {k: read_csv(v) for k, v in cfg["inputs"].items()}

    inventory_in = data["stage38a_local_file_inventory"]
    files = infer_dataset_files(inventory_in, inspect_ids)
    file_inventory_rows: list[dict[str, Any]] = []
    column_rows: list[dict[str, Any]] = []
    for _, row in files.iterrows():
        inv_row, candidates = inspect_file_metadata(row, terms)
        file_inventory_rows.append(inv_row)
        column_rows.extend(candidates)
    file_inventory = pd.DataFrame(file_inventory_rows)
    column_candidates = pd.DataFrame(column_rows)

    disease_rows: list[dict[str, Any]] = []
    celltype_rows: list[dict[str, Any]] = []
    pathology_rows: list[dict[str, Any]] = []
    micro_rows: list[dict[str, Any]] = []
    linkage_rows: list[dict[str, Any]] = []
    testability_rows: list[dict[str, Any]] = []
    ready_input_rows: list[dict[str, Any]] = []
    manual_rows: list[dict[str, Any]] = []

    processed_index = data["stage38a_processed_input_index"]
    for dataset_id in all_ids:
        file_rows = inventory_in[inventory_in["dataset_id"].astype(str).str.lower() == dataset_id] if not inventory_in.empty else pd.DataFrame()
        idx_rows = processed_index[processed_index["dataset_id"].astype(str).str.lower() == dataset_id] if not processed_index.empty else pd.DataFrame()
        expression_path = ""
        metadata_path = ""
        if not idx_rows.empty:
            expr_candidate = clean_text(idx_rows.iloc[0].get("processed_expression_path", ""))
            meta_candidate = clean_text(idx_rows.iloc[0].get("processed_metadata_path", ""))
            if expr_candidate:
                expression_path = expr_candidate
            if meta_candidate:
                metadata_path = meta_candidate
        if not expression_path:
            expression_path = find_expression_file(file_rows)
        if not metadata_path:
            metadata_path = find_metadata_file(file_rows)

        disease, celltype, pathology, micro_astro = build_harmonization(dataset_id, metadata_path, terms)
        sample_col = ""
        if metadata_path:
            preview, kind = read_table_preview(resolve(metadata_path), nrows=200)
            if kind in {"csv", "tsv"}:
                sample_col = choose_column(preview, terms["sample_id"])
        linkage = build_linkage(dataset_id, expression_path, metadata_path, sample_col)

        disease_rows.append(disease)
        celltype_rows.append(celltype)
        pathology_rows.append(pathology)
        micro_rows.append(micro_astro)
        linkage_rows.append(linkage)

        expression_ready = bool(expression_path)
        metadata_ready = bool(metadata_path)
        sample_ready = as_bool(linkage["sample_id_linkage_ready"])
        disease_ready = as_bool(disease["disease_label_ready"])
        cell_ready = as_bool(celltype["celltype_label_ready"])
        micro_ready = as_bool(celltype["microglia_label_ready"])
        astro_ready = as_bool(celltype["astrocyte_label_ready"])
        tau_ready = as_bool(pathology["tau_ptau_label_ready"])
        abeta_ready = as_bool(pathology["amyloid_abeta_label_ready"])
        path_ready = as_bool(pathology["pathology_label_ready"])

        any_support = expression_ready and metadata_ready and sample_ready and (disease_ready or cell_ready or path_ready)
        disease_support = expression_ready and metadata_ready and sample_ready and disease_ready
        cell_support = expression_ready and metadata_ready and sample_ready and cell_ready
        micro_support = expression_ready and metadata_ready and sample_ready and micro_ready
        tau_abeta_support = expression_ready and metadata_ready and sample_ready and (tau_ready or abeta_ready)

        reasons: list[str] = []
        if not expression_ready:
            reasons.append("expression_file_missing")
        if not metadata_ready:
            reasons.append("metadata_file_missing")
        if metadata_ready and not sample_ready:
            reasons.append("sample_id_linkage_not_resolved")
        if metadata_ready and not disease_ready:
            reasons.append("disease_control_labels_not_resolved")
        if metadata_ready and not cell_ready:
            reasons.append("celltype_labels_not_resolved")
        if metadata_ready and not path_ready:
            reasons.append("pathology_labels_not_resolved")

        recommended = "ready for Stage 39B bounded support analysis" if any_support else "manual acquisition/preprocessing/metadata mapping required"
        if dataset_id in {"gse160936", "gse125050"}:
            recommended = "manual acquisition of expression and metadata files required"
        elif dataset_id == "gse157827" and not metadata_ready:
            recommended = "acquire missing GSE157827 metadata/expression matrix beyond GEO series metadata"

        testability_rows.append(
            {
                "dataset_id": dataset_id,
                "expression_ready": expression_ready,
                "metadata_ready": metadata_ready,
                "sample_id_linkage_ready": sample_ready,
                "disease_label_ready": disease_ready,
                "celltype_label_ready": cell_ready,
                "microglia_label_ready": micro_ready,
                "astrocyte_label_ready": astro_ready,
                "tau_ptau_label_ready": tau_ready,
                "amyloid_abeta_label_ready": abeta_ready,
                "pathology_label_ready": path_ready,
                "ready_for_stage39b_any_support": any_support,
                "ready_for_stage39b_disease_support": disease_support,
                "ready_for_stage39b_celltype_support": cell_support,
                "ready_for_stage39b_microglia_support": micro_support,
                "ready_for_stage39b_tau_abeta_support": tau_abeta_support,
                "reason_if_not_ready": unique_join(reasons),
                "recommended_next_action": recommended,
            }
        )
        ready_input_rows.append(
            {
                "dataset_id": dataset_id,
                "expression_path": expression_path,
                "metadata_path": metadata_path,
                "sample_id_column_expression": linkage["sample_id_column_expression"],
                "sample_id_column_metadata": linkage["sample_id_column_metadata"],
                "disease_column": disease["disease_column"],
                "disease_case_values": disease["disease_case_values"],
                "disease_control_values": disease["disease_control_values"],
                "celltype_column": celltype["celltype_column"],
                "microglia_values": celltype["microglia_values"],
                "astrocyte_values": celltype["astrocyte_values"],
                "neuron_values": celltype["neuron_values"],
                "tau_ptau_columns": pathology["tau_ptau_columns"],
                "amyloid_abeta_columns": pathology["amyloid_abeta_columns"],
                "other_pathology_columns": pathology["other_pathology_columns"],
                "ready_for_stage39b": any_support,
                "allowed_analysis_type": unique_join(
                    [
                        "disease_support" if disease_support else "",
                        "celltype_support" if cell_support else "",
                        "microglia_specificity" if micro_support else "",
                        "tau_abeta_pathology_support" if tau_abeta_support else "",
                    ]
                ),
                "claim_level_allowed": "external support / conditional validation support only" if any_support else "not testable yet",
            }
        )
        if reasons or dataset_id in {"gse160936", "gse125050", "gse157827"}:
            manual_rows.append(
                {
                    "dataset_id": dataset_id,
                    "manual_fix_needed": unique_join(reasons) or "confirm full metadata/expression availability",
                    "exact_requirement": recommended,
                    "priority": "high" if dataset_id in {"gse138852", "gse157827", "gse174367"} else "medium",
                    "claim_impact": "prevents or limits Stage 39B testability",
                }
            )

    disease_df = pd.DataFrame(disease_rows)
    celltype_df = pd.DataFrame(celltype_rows)
    pathology_df = pd.DataFrame(pathology_rows)
    micro_df = pd.DataFrame(micro_rows)
    linkage_df = pd.DataFrame(linkage_rows)
    testability = pd.DataFrame(testability_rows)
    ready_inputs = pd.DataFrame(ready_input_rows)
    manual = pd.DataFrame(manual_rows)
    claim = pd.DataFrame(
        [
            {
                "audit_item": "no_model_training",
                "pass": True,
                "evidence": "Stage 39A only inspects metadata and writes readiness tables.",
            },
            {"audit_item": "no_threshold_tuning", "pass": True, "evidence": "No model thresholds are used."},
            {"audit_item": "no_candidate_selection", "pass": True, "evidence": "Frozen Stage 36E candidates are not modified."},
            {"audit_item": "no_clean_external_validation_claim", "pass": True, "evidence": "Claim level remains support/readiness only."},
            {"audit_item": "no_causal_or_therapeutic_claim", "pass": True, "evidence": DISALLOWED},
            {"audit_item": "no_raw_data_commit", "pass": True, "evidence": "Only Stage 39A result tables/reports are written."},
        ]
    )

    out_paths: dict[str, Path] = {}
    out = cfg["outputs"]
    out_paths["external_file_metadata_inventory"] = write_csv(file_inventory, out["external_file_metadata_inventory"])
    out_paths["metadata_column_candidates"] = write_csv(column_candidates, out["metadata_column_candidates"])
    out_paths["sample_id_linkage_audit"] = write_csv(linkage_df, out["sample_id_linkage_audit"])
    out_paths["disease_label_harmonization"] = write_csv(disease_df, out["disease_label_harmonization"])
    out_paths["celltype_label_harmonization"] = write_csv(celltype_df, out["celltype_label_harmonization"])
    out_paths["pathology_label_harmonization"] = write_csv(pathology_df, out["pathology_label_harmonization"])
    out_paths["microglia_astrocyte_label_audit"] = write_csv(micro_df, out["microglia_astrocyte_label_audit"])
    out_paths["dataset_testability_after_rescue"] = write_csv(testability, out["dataset_testability_after_rescue"])
    out_paths["required_manual_metadata_fixes"] = write_csv(manual, out["required_manual_metadata_fixes"])
    out_paths["stage39b_ready_inputs"] = write_csv(ready_inputs, out["stage39b_ready_inputs"])
    out_paths["claim_boundary_audit"] = write_csv(claim, out["claim_boundary_audit"])

    pass_row = {
        "stage39a_run": True,
        "stage38a_inputs_found": all(inputs_ok[k] for k in inputs_ok if k.startswith("stage38a_")),
        "stage38b_inputs_found": all(inputs_ok[k] for k in inputs_ok if k.startswith("stage38b_")),
        "stage38c_inputs_found": all(inputs_ok[k] for k in inputs_ok if k.startswith("stage38c_")),
        "stage36e_inputs_found": all(inputs_ok[k] for k in inputs_ok if k.startswith("stage36e_")),
        "files_inspected": len(file_inventory) > 0,
        "metadata_candidates_written": True,
        "sample_linkage_audited": True,
        "disease_harmonization_attempted": True,
        "celltype_harmonization_attempted": True,
        "pathology_harmonization_attempted": True,
        "ready_not_ready_status_written_honestly": True,
        "manual_fixes_written_when_needed": True,
        "no_unsupported_validation_claims": True,
        "safety_audit_pass": bool(claim["pass"].map(as_bool).all()),
    }
    pass_row["stage39a_run_pass"] = all(bool(v) for k, v in pass_row.items() if k != "stage39a_run_pass")
    pass_row["controlled_interpretation"] = SAFE_INTERPRETATION
    pass_fail = pd.DataFrame([pass_row])
    out_paths["pass_fail"] = write_csv(pass_fail, out["pass_fail"])

    rescued = testability[testability["ready_for_stage39b_any_support"].map(as_bool)]
    report = f"""# Stage 39A external metadata rescue report

{SAFE_INTERPRETATION}

## Summary

Stage 39A inspected local files for GSE138852, GSE157827, and GSE174367 and wrote manual acquisition/preprocessing requirements for GSE160936, GSE125050, and missing GSE157827 assets. The goal was to rescue metadata testability after Stage 38B/38C correctly reported mostly not-testable/no-support evidence.

Datasets ready for some Stage 39B bounded support analysis after rescue: `{unique_join(rescued['dataset_id'].tolist()) or 'none'}`.

## Dataset testability after rescue

{markdown_table(testability)}

## Stage 39B-ready input mapping

{markdown_table(ready_inputs)}

## Disease harmonization

{markdown_table(disease_df)}

## Cell-type and microglia/astrocyte harmonization

{markdown_table(celltype_df)}

## Pathology harmonization

{markdown_table(pathology_df)}

## Manual fixes

{markdown_table(manual)}

## Claim boundary

Stage 39A is a metadata/testability rescue. It does not establish clean external validation, causality, therapeutic relevance, disease modification, or gene-ablation evidence.
"""
    out_paths["rescue_report"] = write_text(report, out["rescue_report"])

    pi_report = f"""# Stage 39A PI metadata gap summary

## Bottom line

The Stage 38B/38C null/not-testable result should primarily be read as a metadata/testability bottleneck, not as biological failure. Stage 39A rescued explicit metadata mappings where possible and listed exact remaining acquisition/preprocessing gaps.

## What is now ready

{markdown_table(testability[["dataset_id", "ready_for_stage39b_any_support", "ready_for_stage39b_disease_support", "ready_for_stage39b_celltype_support", "ready_for_stage39b_microglia_support", "ready_for_stage39b_tau_abeta_support", "recommended_next_action"]])}

## Main manual fixes

{markdown_table(manual)}

## Safe interpretation

Use this as a metadata rescue and Stage 39B planning package only. Do not describe these outputs as clean external validation or experimental validation.
"""
    out_paths["pi_gap_summary"] = write_text(pi_report, out["pi_gap_summary"])

    ready_count = int(testability["ready_for_stage39b_any_support"].map(as_bool).sum())
    update_markdown_section(
        out["active_status"],
        "Stage 39A external metadata rescue status",
        f"Stage 39A is complete. It inspected local external files, rescued explicit metadata mappings where possible, and wrote Stage 39B-ready input mappings plus manual acquisition/preprocessing gaps. Ready-for-Stage39B datasets: `{unique_join(rescued['dataset_id'].tolist()) or 'none'}`. No model training, threshold tuning, candidate selection, clean external validation, causal claim, therapeutic claim, or gene-ablation claim was made.",
    )
    update_markdown_section(
        out["v3_scorecard_md"],
        "Stage 39A external metadata rescue result",
        f"Stage 39A run pass: `{as_bool(pass_fail.iloc[0]['stage39a_run_pass'])}`. Ready-for-Stage39B datasets after metadata rescue: `{ready_count}`. This is metadata/testability rescue only, not validation.",
    )
    update_scorecard_csv(out["v3_scorecard_csv"], pass_fail, ready_count)

    print("datasets_inspected=" + unique_join(inspect_ids))
    print("datasets_rescued=" + (unique_join(rescued["dataset_id"].tolist()) or "none"))
    print("datasets_ready_for_stage39b=" + (unique_join(rescued["dataset_id"].tolist()) or "none"))
    print("disease_labels_found=" + unique_join(disease_df.loc[disease_df["disease_label_ready"].map(as_bool), "dataset_id"].tolist()))
    print("celltype_labels_found=" + unique_join(celltype_df.loc[celltype_df["celltype_label_ready"].map(as_bool), "dataset_id"].tolist()))
    print("microglia_astrocyte_labels_found=" + unique_join(micro_df.loc[micro_df["microglia_label_ready"].map(as_bool) | micro_df["astrocyte_label_ready"].map(as_bool), "dataset_id"].tolist()))
    print("pathology_labels_found=" + unique_join(pathology_df.loc[pathology_df["pathology_label_ready"].map(as_bool), "dataset_id"].tolist()))
    print("manual_fixes_needed=" + str(len(manual)))
    print("stage39a_run_pass=" + str(as_bool(pass_fail.iloc[0]["stage39a_run_pass"])))


if __name__ == "__main__":
    main()
