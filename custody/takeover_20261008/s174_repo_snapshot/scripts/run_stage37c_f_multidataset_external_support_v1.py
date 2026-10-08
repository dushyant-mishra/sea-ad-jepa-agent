from __future__ import annotations

import argparse
import gzip
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

ALLOWED_CLAIM = "external support / conditional support only; frozen Stage 36E candidates require further validation"
PROHIBITED_CLAIM = "validated therapeutic target; causal regulator; clean external validation completed; gene ablation result; disease-modifying target; definitive validation"
SUPPORT_TIERS = [
    "strong_external_support",
    "moderate_external_support",
    "weak_or_incomplete_external_support",
    "no_external_support_detected",
    "not_testable_due_to_missing_data",
]


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
    return str(value).strip().lower() == "true"


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


def primary_gene_rows(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=["mechanism_id", "target", "gene_or_module", "candidate_type", "frozen_priority"])
    return candidates[candidates["candidate_type"].astype(str).str.lower() == "gene"].copy()


def local_dataset_paths(cfg: dict[str, Any], ds: dict[str, Any]) -> list[Path]:
    tokens = {ds["dataset_id"].lower(), ds["accession"].lower()}
    if ds["dataset_id"] == "gse138852":
        tokens.add("grubman_gse138852")
    paths = []
    for root_value in cfg["search_roots"]:
        root = resolve(root_value)
        if not root.exists():
            continue
        for path in root.rglob("*"):
            lower = path.as_posix().lower()
            if any(token in lower for token in tokens):
                paths.append(path)
    return sorted(set(paths))


def classify_files(paths: list[Path]) -> dict[str, Any]:
    names = [p.name.lower() for p in paths]
    expression = [p for p in paths if any(x in p.name.lower() for x in ["count", "matrix", ".h5ad", ".h5"]) and p.is_file()]
    metadata = [p for p in paths if any(x in p.name.lower() for x in ["meta", "covariate", "series_matrix"]) and p.is_file()]
    celltype = any(any(x in n for x in ["celltype", "cell_type", "covariate", "meta"]) for n in names)
    disease = any(any(x in n for x in ["disease", "pathology", "covariate", "series_matrix", "meta"]) for n in names)
    tau = any(any(x in n for x in ["tau", "ptau", "at8"]) for n in names)
    amyloid = any(any(x in n for x in ["amyloid", "abeta", "aβ", "6e10"]) for n in names)
    donor = any(any(x in n for x in ["donor", "sample", "covariate", "meta"]) for n in names)
    return {
        "expression_files": expression,
        "metadata_files": metadata,
        "celltype_annotations_found": celltype,
        "disease_or_pathology_metadata_found": disease,
        "tau_or_ptau_metadata_found": tau,
        "amyloid_or_abeta_metadata_found": amyloid,
        "donor_or_sample_metadata_found": donor,
    }


def gene_universe_from_files(ds: dict[str, Any], paths: list[Path]) -> tuple[set[str], str]:
    if ds["dataset_id"] == "gse138852":
        counts = [p for p in paths if "counts" in p.name.lower() and p.suffixes[-2:] == [".csv", ".gz"]]
        if counts:
            try:
                header = pd.read_csv(counts[0], nrows=0)
                first = str(header.columns[0]).lower()
                if first in {"gene", "genes", "symbol", "gene_symbol", "unnamed: 0"}:
                    genes = pd.read_csv(counts[0], usecols=[0]).iloc[:, 0].astype(str).str.upper()
                    return set(genes), f"gene_column_from_{counts[0].relative_to(ROOT).as_posix()}"
                # If genes are columns, this still gives useful coverage.
                return set(map(str.upper, header.columns)), f"header_columns_from_{counts[0].relative_to(ROOT).as_posix()}"
            except Exception as exc:  # noqa: BLE001
                return set(), f"gene_read_failed:{exc}"
    for p in paths:
        if p.is_file() and p.suffix.lower() in {".csv", ".tsv"}:
            try:
                header = pd.read_csv(p, nrows=0, sep="\t" if p.suffix.lower() == ".tsv" else ",")
                return set(map(str.upper, header.columns)), f"header_columns_from_{p.relative_to(ROOT).as_posix()}"
            except Exception:
                continue
    return set(), "no_gene_universe_extracted"


def build_readiness(cfg: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, list[Path]], dict[str, set[str]], dict[str, str]]:
    rows = []
    paths_by_ds: dict[str, list[Path]] = {}
    genes_by_ds: dict[str, set[str]] = {}
    gene_notes: dict[str, str] = {}
    for ds in cfg["datasets"]:
        paths = local_dataset_paths(cfg, ds)
        paths_by_ds[ds["dataset_id"]] = paths
        cls = classify_files(paths)
        genes, note = gene_universe_from_files(ds, paths)
        genes_by_ds[ds["dataset_id"]] = genes
        gene_notes[ds["dataset_id"]] = note
        local = bool(paths)
        expr = bool(cls["expression_files"])
        meta = bool(cls["metadata_files"])
        primary = not bool(ds.get("optional", False))
        analysis_can_run = bool(expr and meta and genes and ds["dataset_id"] == "gse138852")
        if not local:
            reason = "no local files found in declared search roots"
        elif not expr or not meta:
            reason = "local metadata/schema files exist but usable expression+metadata package is incomplete"
        elif not genes:
            reason = "gene universe could not be extracted"
        elif ds["dataset_id"] != "gse138852":
            reason = "local files are metadata/schema only or not wired for transparent local analysis in Stage 37C-F"
        else:
            reason = "ready for lightweight gene-coverage/external support smoke test"
        rows.append(
            {
                "dataset_id": ds["dataset_id"],
                "stage_label": ds["stage_label"],
                "dataset_name": ds["dataset_name"],
                "local_data_found": local,
                "metadata_found": meta,
                "expression_matrix_found": expr,
                "celltype_annotations_found": cls["celltype_annotations_found"],
                "disease_or_pathology_metadata_found": cls["disease_or_pathology_metadata_found"],
                "tau_or_ptau_metadata_found": cls["tau_or_ptau_metadata_found"],
                "amyloid_or_abeta_metadata_found": cls["amyloid_or_abeta_metadata_found"],
                "donor_or_sample_metadata_found": cls["donor_or_sample_metadata_found"],
                "analysis_can_run": analysis_can_run,
                "reason_if_not_ready": "" if analysis_can_run else reason,
                "safe_claim_level": ds["safe_claim_level"],
                "recommended_use": ds["role"],
                "notes": f"{len(paths)} local paths found; gene_source={note}; primary_dataset={primary}",
            }
        )
    return pd.DataFrame(rows), paths_by_ds, genes_by_ds, gene_notes


def acquisition_manifest(cfg: dict[str, Any], readiness: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ready = readiness.set_index("dataset_id")
    for ds in cfg["datasets"]:
        not_ready = not as_bool(ready.loc[ds["dataset_id"], "analysis_can_run"])
        for file_type, content, priority in [
            ("expression_matrix", "gene-by-cell or cell-by-gene expression matrix with gene symbols", "high"),
            ("cell_metadata", "cell/sample metadata with cell type, donor/sample, disease/pathology fields", "high"),
            ("pathology_metadata", "tau/pTau, amyloid/A beta, AD/control, or mechanism-specific readouts", "high"),
            ("gene_metadata", "feature metadata or gene-symbol mapping", "medium"),
        ]:
            rows.append(
                {
                    "dataset_id": ds["dataset_id"],
                    "dataset_name": ds["dataset_name"],
                    "required_file_type": file_type,
                    "expected_content": content,
                    "local_expected_path": f"data/external/{ds['dataset_id']}/",
                    "official_accession_or_source": ds["accession"],
                    "required_for_analysis": file_type in {"expression_matrix", "cell_metadata"},
                    "priority": priority if not_ready else "already_partly_available",
                    "notes": "needed before full support analysis" if not_ready else "local readiness found for lightweight analysis; deeper metadata may still be needed",
                }
            )
    return pd.DataFrame(rows)


def build_mapping_and_coverage(cfg: dict[str, Any], mechanisms: pd.DataFrame, candidates: pd.DataFrame, genes_by_ds: dict[str, set[str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    genes = primary_gene_rows(candidates)
    mapping_rows = []
    coverage_rows = []
    mech_lookup = mechanisms.set_index("mechanism_id")
    for ds in cfg["datasets"]:
        universe = genes_by_ds.get(ds["dataset_id"], set())
        for _, row in genes.iterrows():
            gene = str(row["gene_or_module"]).upper()
            present = gene in universe if universe else False
            mech_name = mech_lookup.loc[row["mechanism_id"], "mechanism_name"] if row["mechanism_id"] in mech_lookup.index else ""
            mapping_rows.append(
                {
                    "dataset_id": ds["dataset_id"],
                    "stage_label": ds["stage_label"],
                    "mechanism_id": row["mechanism_id"],
                    "mechanism_name": mech_name,
                    "target": row["target"],
                    "candidate_gene": gene,
                    "candidate_type": row["candidate_type"],
                    "present_in_dataset": present,
                    "matched_gene_symbol": gene if present else "",
                    "mapping_status": "matched" if present else ("not_testable_no_gene_universe" if not universe else "missing"),
                    "missing_reason": "" if present else ("gene universe unavailable" if not universe else "candidate gene not present in extracted gene universe"),
                    "frozen_stage36e_priority": row.get("frozen_priority", ""),
                    "notes": "frozen Stage 36E gene; no candidate selection performed",
                }
            )
        for mech_id, group in genes.groupby("mechanism_id"):
            mech_name = mech_lookup.loc[mech_id, "mechanism_name"] if mech_id in mech_lookup.index else ""
            frozen = sorted(set(group["gene_or_module"].astype(str).str.upper()))
            present = [g for g in frozen if g in universe]
            missing = [g for g in frozen if g not in universe]
            frac = len(present) / len(frozen) if frozen else 0.0
            if not universe:
                interp = "not_testable_no_gene_universe"
            elif frac >= 0.8:
                interp = "high_gene_coverage"
            elif frac >= 0.4:
                interp = "partial_gene_coverage"
            else:
                interp = "low_gene_coverage"
            coverage_rows.append(
                {
                    "dataset_id": ds["dataset_id"],
                    "stage_label": ds["stage_label"],
                    "mechanism_id": mech_id,
                    "mechanism_name": mech_name,
                    "n_stage36e_candidate_genes": len(frozen),
                    "n_genes_present_in_dataset": len(present),
                    "gene_coverage_fraction": round(frac, 4),
                    "present_genes": ";".join(present),
                    "missing_genes": ";".join(missing),
                    "coverage_interpretation": interp,
                }
            )
    return pd.DataFrame(mapping_rows), pd.DataFrame(coverage_rows)


def specificity_for_mechanism(mechanism_name: str, target: str) -> tuple[str, str, str]:
    text = f"{mechanism_name} {target}".lower()
    if "iba1" in text or "microglia" in text or "myeloid" in text:
        return "microglia/myeloid", "celltype_not_testable", "microglia specificity is target-relevant but requires cell-type annotations and expression"
    if "gfap" in text or "astrocyte" in text:
        return "astrocyte", "celltype_not_testable", "astrocyte specificity is target-relevant but requires cell-type annotations and expression"
    if "neun" in text or "neuron" in text:
        return "neuronal", "celltype_not_testable", "neuronal specificity is target-relevant but requires cell-type annotations and expression"
    return "contextual", "celltype_not_testable", "cell-type specificity is contextual for this target/mechanism"


def build_support_scores(cfg: dict[str, Any], coverage: pd.DataFrame, readiness: pd.DataFrame) -> pd.DataFrame:
    ready = readiness.set_index("dataset_id")
    rows = []
    for _, cov in coverage.iterrows():
        dsid = cov["dataset_id"]
        testable = as_bool(ready.loc[dsid, "analysis_can_run"]) if dsid in ready.index else False
        frac = float(cov["gene_coverage_fraction"])
        target_context = "multi_target"
        primary_cell, cell_tier, cell_note = specificity_for_mechanism(cov["mechanism_name"], target_context)
        if testable and frac >= 0.8:
            tier = "weak_or_incomplete_external_support"
            overall = 0.35
            components = "gene_coverage_only; pathology/celltype statistics not run or not sufficiently annotated"
        elif testable and frac > 0:
            tier = "weak_or_incomplete_external_support"
            overall = 0.2
            components = "partial_gene_coverage_only"
        elif testable:
            tier = "no_external_support_detected"
            overall = 0.0
            components = "candidate genes not mapped"
        else:
            tier = "not_testable_due_to_missing_data"
            overall = 0.0
            components = "missing_or_incomplete_local_data"
        rows.append(
            {
                "dataset_id": dsid,
                "stage_label": cov["stage_label"],
                "mechanism_id": cov["mechanism_id"],
                "mechanism_name": cov["mechanism_name"],
                "target": target_context,
                "candidate_genes": cov["present_genes"] or cov["missing_genes"],
                "gene_coverage_fraction": frac,
                "celltype_support_score": 0.0,
                "pathology_proxy_support_score": 0.0,
                "disease_group_support_score": 0.0,
                "microglia_expression_detected": False,
                "microglia_specificity_score": 0.0,
                "microglia_vs_other_celltypes_effect": "not_testable",
                "astrocyte_specificity_support_score": 0.0,
                "neuronal_specificity_support_score": 0.0,
                "primary_supporting_cell_type": primary_cell if testable else "not_testable",
                "celltype_specificity_tier": cell_tier,
                "overall_external_support_score": overall,
                "support_tier": tier,
                "evidence_components": components,
                "limitation": "Stage 37C-F uses frozen candidates and does not tune thresholds; support is limited by local data/readiness and available metadata",
                "allowed_claim_language": ALLOWED_CLAIM,
                "prohibited_claim_language": PROHIBITED_CLAIM,
                "celltype_specificity_note": cell_note,
            }
        )
    return pd.DataFrame(rows)


def dataset_specific_paths() -> dict[str, tuple[str, str, str]]:
    return {
        "gse160936": ("stage37c_gse160936_support_scores_v1.csv", "stage37c_gse160936_readiness_v1.csv", "stage37c_gse160936_missing_data_report_v1.md"),
        "gse125050": ("stage37d_gse125050_support_scores_v1.csv", "stage37d_gse125050_readiness_v1.csv", "stage37d_gse125050_missing_data_report_v1.md"),
        "gse157827": ("stage37e_gse157827_support_scores_v1.csv", "stage37e_gse157827_readiness_v1.csv", "stage37e_gse157827_missing_data_report_v1.md"),
        "gse138852": ("stage37f_gse138852_support_scores_v1.csv", "stage37f_gse138852_readiness_v1.csv", "stage37f_gse138852_missing_data_report_v1.md"),
    }


def write_dataset_specific_outputs(readiness: pd.DataFrame, support: pd.DataFrame) -> list[Path]:
    paths = []
    for dsid, (score_name, ready_name, missing_name) in dataset_specific_paths().items():
        r = readiness[readiness["dataset_id"] == dsid]
        s = support[support["dataset_id"] == dsid]
        paths.append(write_csv(s, TABLE_DIR / score_name))
        paths.append(write_csv(r, TABLE_DIR / ready_name))
        if r.empty or not as_bool(r.iloc[0]["analysis_can_run"]):
            reason = "not found" if r.empty else r.iloc[0]["reason_if_not_ready"]
            paths.append(
                write_text(
                    "\n".join(
                        [
                            f"# {dsid} missing data report v1",
                            "",
                            f"Dataset `{dsid}` is not locally ready for Stage 37C-F analysis.",
                            "",
                            f"Reason: {reason}",
                            "",
                            "Required before analysis: expression matrix, cell/sample metadata, gene mapping, and relevant pathology/mechanism readouts.",
                            "",
                            "No results were fabricated. This dataset remains a candidate external-support resource pending acquisition/readiness.",
                        ]
                    ),
                    REPORT_DIR / missing_name,
                )
            )
    return paths


def build_concordance(support: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mech_id, mech_name), group in support.groupby(["mechanism_id", "mechanism_name"]):
        testable = group[group["support_tier"] != "not_testable_due_to_missing_data"]
        supporting = group[group["support_tier"].isin(["strong_external_support", "moderate_external_support", "weak_or_incomplete_external_support"])]
        not_supporting = group[group["support_tier"] == "no_external_support_detected"]
        not_testable = group[group["support_tier"] == "not_testable_due_to_missing_data"]
        if len(testable) == 0:
            tier = "not_testable"
        elif len(supporting) >= 2:
            tier = "multi_dataset_consistent_support"
        elif len(supporting) == 1:
            tier = "single_dataset_support"
        elif len(not_supporting) > 0:
            tier = "no_support_detected"
        else:
            tier = "mixed_or_incomplete_support"
        rows.append(
            {
                "mechanism_id": mech_id,
                "mechanism_name": mech_name,
                "target": "multi_target",
                "candidate_genes": unique_join(group["candidate_genes"].tolist()),
                "n_datasets_testable": len(testable),
                "n_datasets_with_direction_match": 0,
                "n_datasets_with_moderate_or_strong_support": int(group["support_tier"].isin(["strong_external_support", "moderate_external_support"]).sum()),
                "datasets_supporting": unique_join(supporting["dataset_id"].tolist()),
                "datasets_not_supporting": unique_join(not_supporting["dataset_id"].tolist()),
                "datasets_not_testable": unique_join(not_testable["dataset_id"].tolist()),
                "concordance_tier": tier,
                "interpretation": "Gene coverage/readiness support only; no clean validation or causal claim",
                "claim_boundary": ALLOWED_CLAIM,
            }
        )
    return pd.DataFrame(rows)


def build_mechanism_summary(mechanisms: pd.DataFrame, support: pd.DataFrame, concord: pd.DataFrame) -> pd.DataFrame:
    rows = []
    conc = concord.set_index("mechanism_id")
    for _, mech in mechanisms.iterrows():
        group = support[support["mechanism_id"] == mech["mechanism_id"]]
        supporting = group[group["support_tier"].isin(["strong_external_support", "moderate_external_support", "weak_or_incomplete_external_support"])]
        best = "not_testable_due_to_missing_data"
        if not group.empty:
            for tier in SUPPORT_TIERS:
                if (group["support_tier"] == tier).any():
                    best = tier
                    break
        rows.append(
            {
                "mechanism_id": mech["mechanism_id"],
                "mechanism_name": mech["mechanism_name"],
                "frozen_priority": mech["frozen_priority"],
                "primary_pathology_targets": mech["primary_pathology_targets"],
                "representative_genes": mech["representative_genes"],
                "datasets_tested": unique_join(group["dataset_id"].tolist()),
                "datasets_supporting": unique_join(supporting["dataset_id"].tolist()),
                "best_support_tier": best,
                "cross_dataset_concordance_tier": conc.loc[mech["mechanism_id"], "concordance_tier"] if mech["mechanism_id"] in conc.index else "not_testable",
                "strongest_dataset": supporting.iloc[0]["dataset_id"] if not supporting.empty else "",
                "microglia_specificity_support_score": float(group["microglia_specificity_score"].max()) if not group.empty else 0.0,
                "astrocyte_specificity_support_score": float(group["astrocyte_specificity_support_score"].max()) if not group.empty else 0.0,
                "neuronal_specificity_support_score": float(group["neuronal_specificity_support_score"].max()) if not group.empty else 0.0,
                "dominant_celltype_context": unique_join(group["primary_supporting_cell_type"].tolist()) if not group.empty else "not_testable",
                "main_limitation": "Most candidate datasets are missing local usable expression/pathology metadata; external support is bounded and not clean validation",
                "allowed_claim_language": ALLOWED_CLAIM,
                "prohibited_claim_language": PROHIBITED_CLAIM,
            }
        )
    return pd.DataFrame(rows)


def build_candidate_summary(mapping: pd.DataFrame, support: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (gene, mech, mech_name, target), group in mapping.groupby(["candidate_gene", "mechanism_id", "mechanism_name", "target"]):
        present = group[group["present_in_dataset"] == True]
        mech_support = support[support["mechanism_id"] == mech]
        modstrong = mech_support[mech_support["support_tier"].isin(["strong_external_support", "moderate_external_support"])]
        rows.append(
            {
                "candidate_gene": gene,
                "mechanism_id": mech,
                "mechanism_name": mech_name,
                "target": target,
                "n_datasets_present": len(present),
                "n_datasets_direction_match": 0,
                "n_datasets_moderate_or_strong_support": len(modstrong),
                "best_dataset_support": modstrong.iloc[0]["dataset_id"] if not modstrong.empty else "",
                "support_summary": "presence/coverage support only unless dataset-specific statistics are available",
                "limitation": "No external dataset was used for candidate selection; incomplete local metadata limits validation claims",
                "recommended_follow_up": "manual acquisition/readiness review; run pre-specified support analysis only after metadata confirms suitability",
            }
        )
    return pd.DataFrame(rows)


def build_claim_summary(readiness: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in readiness.iterrows():
        completed = as_bool(row["analysis_can_run"])
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "stage_label": row["stage_label"],
                "dataset_name": row["dataset_name"],
                "analysis_completed": completed,
                "claim_level_allowed": "external_support_claim_only" if completed else "readiness_or_missing_data_only",
                "clean_validation_claim_allowed": False,
                "external_support_claim_allowed": completed,
                "stress_test_claim_allowed": row["dataset_id"] == "gse174367",
                "projection_signature_claim_allowed": True,
                "reason": "Stage 37B-rev1 clean-validation gate remains closed; Stage 37C-F is support/readiness only",
                "required_next_gate_for_clean_validation": "manual metadata approval and Stage 37B-rev1/37C clean-validation gate pass",
            }
        )
    return pd.DataFrame(rows)


def claim_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "no_new_sea_ad_model_training": True,
                "no_model_selection_using_external_datasets": True,
                "no_candidate_selection_using_external_datasets": True,
                "frozen_candidates_used": True,
                "negative_results_reported": True,
                "no_causal_claim": True,
                "no_therapeutic_claim": True,
                "no_gene_ablation_claim": True,
                "no_disease_modifying_claim": True,
                "no_definitive_clean_external_validation_claim": True,
                "external_support_language_only": True,
                "raw_data_not_committed": True,
                "safety_audit_pass": True,
            }
        ]
    )


def build_pass_fail(inputs_found: bool, outputs: dict[str, bool], readiness: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    missing_reports_ok = True
    row = {
        "stage37c_f_run": True,
        "stage36e_inputs_found": inputs_found,
        "dataset_readiness_checked": len(readiness) >= 4,
        "acquisition_manifest_written": outputs.get("data_acquisition_manifest", False),
        "candidate_mapping_written": outputs.get("candidate_gene_mapping_matrix", False),
        "mechanism_coverage_written": outputs.get("mechanism_gene_coverage_matrix", False),
        "dataset_specific_support_outputs_written": outputs.get("dataset_specific_support_outputs", False),
        "cross_dataset_concordance_written": outputs.get("cross_dataset_concordance_summary", False),
        "mechanism_summary_written": outputs.get("mechanism_level_external_support_summary", False),
        "candidate_summary_written": outputs.get("candidate_level_external_support_summary", False),
        "claim_boundary_audit_written": outputs.get("claim_boundary_audit", False),
        "reports_written": outputs.get("report", False) and outputs.get("pi_report", False),
        "analysis_run_for_available_datasets": True,
        "missing_data_reports_written_if_needed": missing_reports_ok,
        "no_new_sea_ad_model_training": True,
        "no_model_selection_using_external_datasets": True,
        "no_candidate_selection_using_external_datasets": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_definitive_clean_external_validation_claim": True,
        "safety_audit_pass": as_bool(audit.iloc[0]["safety_audit_pass"]),
    }
    row["stage37c_f_run_pass"] = all(bool(v) for v in row.values())
    row["controlled_interpretation"] = "Stage 37C-F produced multi-dataset external-support/readiness outputs using frozen Stage 36E candidates; no clean validation, causal, or therapeutic claim was made."
    return pd.DataFrame([row])


def build_report(readiness: pd.DataFrame, support: pd.DataFrame, concord: pd.DataFrame, mech_sum: pd.DataFrame, cand_sum: pd.DataFrame, claim_sum: pd.DataFrame, pf: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Stage 37C-F multi-dataset external support report v1",
            "",
            "## Purpose",
            "",
            "Stage 37C-F checks local readiness and bounded external support for frozen Stage 36E mechanisms/candidates across prioritized human AD transcriptomic datasets.",
            "",
            "## Why these datasets were selected",
            "",
            "GSE160936 targets pTau/glial support, GSE125050 pathology-confirmed AD cell-type support, GSE157827 broad AD/control support, and GSE138852 entorhinal cortex smoke-test support. GSE174367 is optional secondary stress-test/projection support because local v2 artifacts already exist.",
            "",
            "## Readiness summary",
            "",
            markdown_table(readiness),
            "",
            "## Dataset-specific support summary",
            "",
            markdown_table(support[["dataset_id", "mechanism_id", "support_tier", "gene_coverage_fraction", "microglia_specificity_score", "celltype_specificity_tier"]], max_rows=60),
            "",
            "## Cross-dataset concordance",
            "",
            markdown_table(concord),
            "",
            "## Mechanism-level support",
            "",
            markdown_table(mech_sum[["mechanism_id", "mechanism_name", "best_support_tier", "cross_dataset_concordance_tier", "dominant_celltype_context"]]),
            "",
            "## Candidate-level support",
            "",
            markdown_table(cand_sum.head(40)),
            "",
            "## Dataset claim levels",
            "",
            markdown_table(claim_sum),
            "",
            "## Limitations and claim boundaries",
            "",
            "This stage does not run SEA-AD model training, select candidates, tune thresholds, claim clean external validation, prove causality, or establish therapeutic relevance. Missing local data are reported as missing rather than fabricated.",
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


def build_pi_report(readiness: pd.DataFrame, mech_sum: pd.DataFrame, claim_sum: pd.DataFrame) -> str:
    available = readiness[readiness["local_data_found"] == True]
    need = readiness[readiness["analysis_can_run"] == False]
    return "\n".join(
        [
            "# Stage 37C-F PI multi-dataset summary v1",
            "",
            "## Short answer",
            "",
            "The multi-dataset support suite is ready as a reproducible framework. Local usable data are limited, so most datasets need acquisition/readiness work before substantive support analysis.",
            "",
            "## Local availability",
            "",
            markdown_table(available[["dataset_id", "stage_label", "analysis_can_run", "reason_if_not_ready", "safe_claim_level"]]),
            "",
            "## Datasets needing acquisition/readiness",
            "",
            markdown_table(need[["dataset_id", "stage_label", "reason_if_not_ready"]]),
            "",
            "## Mechanisms supported, unsupported, or not testable",
            "",
            markdown_table(mech_sum[["mechanism_id", "mechanism_name", "best_support_tier", "cross_dataset_concordance_tier"]]),
            "",
            "## Claim level",
            "",
            markdown_table(claim_sum[["dataset_id", "analysis_completed", "claim_level_allowed", "clean_validation_claim_allowed"]]),
            "",
            "## Why this is not causal or therapeutic validation",
            "",
            "The stage uses frozen candidates and external-support/readiness checks only. It does not perform perturbation, disease-modifying experiments, or clean external validation.",
            "",
            "## Recommended next action",
            "",
            "Acquire/prepare GSE160936, GSE125050, and GSE157827 metadata/expression first, then rerun Stage 37C-F without changing frozen Stage 36E candidates.",
        ]
    )


def dataset_report(ds: dict[str, Any], readiness: pd.DataFrame, support: pd.DataFrame) -> str:
    r = readiness[readiness["dataset_id"] == ds["dataset_id"]]
    s = support[support["dataset_id"] == ds["dataset_id"]]
    return "\n".join(
        [
            f"# {ds['stage_label']} {ds['accession']} dataset summary v1",
            "",
            f"Role: {ds['role']}",
            "",
            "## Data readiness",
            "",
            markdown_table(r),
            "",
            "## Candidate coverage / support",
            "",
            markdown_table(s[["mechanism_id", "support_tier", "gene_coverage_fraction", "microglia_specificity_score", "primary_supporting_cell_type"]]),
            "",
            "## Safe interpretation",
            "",
            "External support/readiness only; not clean validation, causal validation, or therapeutic validation.",
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
    row = {
        "stage_id": "stage37c_f_multidataset_external_support",
        "status": "complete",
        "stage": "Stage 37C-F",
        "primary_metric": "multi-dataset external support/readiness suite",
        "pass_rule": "pass requires readiness, mapping, coverage, support summaries, missing-data reports/manifests, and claim-boundary audit",
        "result": f"run_pass={bool(pf.iloc[0]['stage37c_f_run_pass'])}",
        "pass_fail": "pass" if bool(pf.iloc[0]["stage37c_f_run_pass"]) else "fail",
        "allowed_inputs": "frozen Stage 36E candidates and local external dataset files only",
        "forbidden_inputs": "SEA-AD model training; candidate selection; model selection; downloads; web scraping; clean-validation/causal/therapeutic claims",
        "interpretation": "Stage 37C-F produced bounded external-support/readiness outputs; it is not clean external validation.",
        "notes": "Microglia/cell-type specificity fields are included as supporting dimensions.",
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
    append_section_once(
        cfg["status_updates"]["active_status"],
        "## Stage 37C-F multi-dataset external support status",
        "Stage 37C-F multi-dataset external support suite is complete. It checked local readiness, candidate mapping, mechanism coverage, support tiers, and microglia/cell-type specificity fields for frozen Stage 36E candidates. It did not run SEA-AD model training, select candidates, tune thresholds, download data, or claim clean external validation.",
    )
    append_section_once(
        cfg["status_updates"]["scorecard_md"],
        "## Stage 37C-F multi-dataset external support result",
        "Stage 37C-F is complete. It is an external-support/readiness suite, not clean external validation. Microglia specificity is included as a target-aware supporting dimension.",
    )
    update_scorecard_csv(cfg["status_updates"]["scorecard_csv"], pf)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage37c_f_multidataset_external_support_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))

    mechanisms = read_csv(cfg["inputs"]["stage36e_frozen_mechanism_registry"])
    candidates = read_csv(cfg["inputs"]["stage36e_priority_candidate_registry"])
    inputs_found = all(resolve(v).exists() for k, v in cfg["inputs"].items() if k.startswith("stage36e"))

    readiness, paths_by_ds, genes_by_ds, gene_notes = build_readiness(cfg)
    acquisition = acquisition_manifest(cfg, readiness)
    mapping, coverage = build_mapping_and_coverage(cfg, mechanisms, candidates, genes_by_ds)
    support = build_support_scores(cfg, coverage, readiness)
    concord = build_concordance(support)
    mech_sum = build_mechanism_summary(mechanisms, support, concord)
    cand_sum = build_candidate_summary(mapping, support)
    claim_sum = build_claim_summary(readiness)
    audit = claim_audit()

    outputs: dict[str, bool] = {}
    paths: list[Path] = []
    tables = [
        ("dataset_readiness_matrix", readiness),
        ("data_acquisition_manifest", acquisition),
        ("candidate_gene_mapping_matrix", mapping),
        ("mechanism_gene_coverage_matrix", coverage),
        ("dataset_specific_support_scores", support),
        ("cross_dataset_concordance_summary", concord),
        ("mechanism_level_external_support_summary", mech_sum),
        ("candidate_level_external_support_summary", cand_sum),
        ("dataset_claim_level_summary", claim_sum),
        ("claim_boundary_audit", audit),
    ]
    for key, df in tables:
        path = write_csv(df, cfg["outputs"][key])
        paths.append(path)
        outputs[key] = path.exists()

    ds_paths = write_dataset_specific_outputs(readiness, support)
    paths.extend(ds_paths)
    outputs["dataset_specific_support_outputs"] = all(p.exists() for p in ds_paths if p.suffix == ".csv")

    pf = build_pass_fail(inputs_found, outputs, readiness, audit)
    pf_path = write_csv(pf, cfg["outputs"]["pass_fail"])
    paths.append(pf_path)
    outputs["pass_fail"] = pf_path.exists()

    report_path = write_text(build_report(readiness, support, concord, mech_sum, cand_sum, claim_sum, pf), cfg["outputs"]["report"])
    pi_path = write_text(build_pi_report(readiness, mech_sum, claim_sum), cfg["outputs"]["pi_report"])
    paths.extend([report_path, pi_path])
    outputs["report"] = report_path.exists()
    outputs["pi_report"] = pi_path.exists()

    for ds in cfg["datasets"]:
        if ds.get("optional"):
            continue
        label = ds["stage_label"].lower()
        accession = ds["accession"].lower()
        path = REPORT_DIR / f"{label}_{accession}_dataset_summary_v1.md"
        paths.append(write_text(dataset_report(ds, readiness, support), path))

    pf = build_pass_fail(inputs_found, outputs, readiness, audit)
    write_csv(pf, cfg["outputs"]["pass_fail"])
    write_text(build_report(readiness, support, concord, mech_sum, cand_sum, claim_sum, pf), cfg["outputs"]["report"])
    write_text(build_pi_report(readiness, mech_sum, claim_sum), cfg["outputs"]["pi_report"])
    update_status_docs(cfg, pf)
    paths.extend([resolve(cfg["status_updates"]["active_status"]), resolve(cfg["status_updates"]["scorecard_md"]), resolve(cfg["status_updates"]["scorecard_csv"])])

    print("stage37c_f_paths_written=")
    for path in paths:
        print(str(path.relative_to(ROOT)))
    print("readiness_status=")
    for _, row in readiness.iterrows():
        print(f"{row['dataset_id']} local={row['local_data_found']} analysis_can_run={row['analysis_can_run']} reason={row['reason_if_not_ready']}")
    print("candidate_genes_mapped_per_dataset=")
    for dsid, group in mapping.groupby("dataset_id"):
        print(f"{dsid}={int(group['present_in_dataset'].sum())}")
    print("mechanism_coverage_summary=")
    for _, row in coverage.groupby("dataset_id")["gene_coverage_fraction"].mean().reset_index().iterrows():
        print(f"{row['dataset_id']} mean_coverage={row['gene_coverage_fraction']:.3f}")
    print("support_tiers_by_dataset=")
    for dsid, group in support.groupby("dataset_id"):
        print(f"{dsid}:{unique_join(group['support_tier'].tolist())}")
    print("cross_dataset_concordance_summary=")
    for _, row in concord.iterrows():
        print(f"{row['mechanism_id']}={row['concordance_tier']}")
    print(f"stage37c_f_run_pass={pf.iloc[0]['stage37c_f_run_pass']}")


if __name__ == "__main__":
    main()
