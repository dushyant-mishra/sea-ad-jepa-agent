#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

TRUE_VALUES = {"true", "1", "yes", "y", "t"}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return cfg


def as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(TRUE_VALUES)


def require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = columns - set(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def assert_unique(frame: pd.DataFrame, keys: list[str], label: str) -> None:
    duplicated = frame.duplicated(keys, keep=False)
    if duplicated.any():
        preview = frame.loc[duplicated, keys].head(10).to_dict(orient="records")
        raise RuntimeError(f"{label} is not unique on {keys}: {preview}")


def load_supported_motifs(path: Path) -> pd.DataFrame:
    motifs = pd.read_csv(path)
    require(
        motifs,
        {
            "batch_id", "tf", "MotifID", "NES", "AUC", "enriched",
            "batch_tf_direct_support", "batch_tf_extended_support",
        },
        "F5b enriched motifs",
    )
    for column in [
        "enriched", "batch_tf_direct_support", "batch_tf_extended_support",
        "batch_tf_similarity_support", "batch_tf_orthology_support",
        "batch_tf_similarity_orthology_support",
    ]:
        if column in motifs:
            motifs[column] = as_bool(motifs[column])
    motifs = motifs.loc[
        motifs["enriched"] & motifs["batch_tf_extended_support"]
    ].copy()
    if motifs.empty:
        raise RuntimeError("No enriched motifs are annotated to their batch TF")
    motifs["motif_support_class"] = np.where(
        motifs["batch_tf_direct_support"], "direct", "extended_only"
    )

    def basis(row: pd.Series) -> str:
        labels = []
        for column, label in [
            ("batch_tf_direct_support", "direct"),
            ("batch_tf_similarity_support", "motif_similarity"),
            ("batch_tf_orthology_support", "orthology"),
            ("batch_tf_similarity_orthology_support", "motif_similarity_and_orthology"),
        ]:
            if bool(row.get(column, False)):
                labels.append(label)
        return ";".join(labels) if labels else "unspecified_extended"

    motifs["motif_annotation_basis"] = motifs.apply(basis, axis=1)
    assert_unique(motifs, ["tf", "MotifID"], "Supported motifs")
    return motifs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    f5b = cfg["cistarget_primary_pilot"]
    f5c = cfg["primary_tf_region_gene_evidence"]

    motifs = load_supported_motifs(
        project / f5b["outputs"]["enriched_motifs_csv"]
    )
    hits = pd.read_csv(project / f5b["outputs"]["motif_hits_csv"])
    require(
        hits,
        {
            "batch_id", "tf", "MotifID", "mapped_db_region", "database_rank",
            "Rank_at_max", "query_region", "query_name", "overlap_bp",
            "overlap_fraction_query", "overlap_fraction_db",
        },
        "F5b motif hits",
    )

    motif_columns = [
        "batch_id", "tf", "MotifID", "NES", "AUC", "motif_support_class",
        "motif_annotation_basis", "batch_tf_direct_support",
        "batch_tf_extended_support",
    ]
    for optional in [
        "Direct_annot", "Motif_similarity_annot", "Orthology_annot",
        "Motif_similarity_and_Orthology_annot", "n_motif_hit_db_regions",
    ]:
        if optional in motifs:
            motif_columns.append(optional)
    evidence = hits.merge(
        motifs[motif_columns],
        on=["batch_id", "tf", "MotifID"],
        how="inner",
        validate="many_to_one",
    )
    if evidence.empty:
        raise RuntimeError("No motif hits remain after TF-supported motif filtering")

    peaks = pd.read_csv(project / cfg["outputs"]["candidate_peak_gene_links"])
    require(
        peaks,
        {"peak_id", "chrom", "start", "end", "nearest_gene", "abs_distance_to_tss", "peak_gene_class"},
        "Stage75F peak-gene links",
    )
    peaks["peak_id"] = peaks["peak_id"].astype(str)
    assert_unique(peaks, ["peak_id"], "Stage75F peak-gene links")
    peaks = peaks.rename(
        columns={
            "peak_id": "query_region", "nearest_gene": "target_gene",
            "chrom": "query_peak_chrom", "start": "query_peak_start",
            "end": "query_peak_end",
        }
    )

    evidence = evidence.merge(
        peaks,
        on="query_region",
        how="left",
        validate="many_to_one",
        indicator="_peak_join",
    )
    unmatched_peak_rows = int(evidence["_peak_join"].ne("both").sum())

    edges = pd.read_csv(project / cfg["outputs"]["candidate_edges"])
    require(edges, {"source_tf", "target_gene"}, "Stage75F candidate edges")
    if "edge_candidate_pass" in edges:
        edges = edges.loc[as_bool(edges["edge_candidate_pass"])].copy()
    edges["source_tf"] = edges["source_tf"].astype(str)
    edges["target_gene"] = edges["target_gene"].astype(str)
    assert_unique(edges, ["source_tf", "target_gene"], "Stage75F candidate edges")
    rename = {
        c: f"edge_{c}" for c in edges.columns
        if c not in {"source_tf", "target_gene"}
    }
    edges = edges.rename(columns=rename)

    evidence = evidence.merge(
        edges,
        left_on=["tf", "target_gene"],
        right_on=["source_tf", "target_gene"],
        how="left",
        validate="many_to_one",
        indicator="_edge_join",
    )
    unmatched_edge_rows = int(evidence["_edge_join"].ne("both").sum())

    evidence["tf_region_support_class"] = "cistarget_enriched_motif_leading_edge"
    evidence["region_gene_support_class"] = "proximity_only_nearest_gene"
    evidence["tf_target_support_class"] = "stage72b_candidate_coactivity"
    evidence["combined_evidence_class"] = np.where(
        evidence["motif_support_class"].eq("direct"),
        "direct_motif_plus_coactivity_plus_proximity",
        "extended_motif_plus_coactivity_plus_proximity",
    )
    evidence["evidence_interpretation"] = "candidate_tf_region_gene_evidence_not_validated_regulation"
    evidence["motif_enrichment_completed"] = True
    evidence["validated_regulation"] = False
    evidence["validated_grn_claim"] = False
    evidence["causal_validation_pass"] = False
    evidence["therapeutic_target_claim"] = False

    evidence = (
        evidence.sort_values(
            ["tf", "motif_support_class", "NES", "database_rank"],
            ascending=[True, True, False, True],
        )
        .drop_duplicates(["tf", "MotifID", "mapped_db_region", "query_region", "target_gene"])
        .drop(columns=["_peak_join", "_edge_join", "source_tf"], errors="ignore")
        .reset_index(drop=True)
    )

    target_rows = []
    for (tf, gene), group in evidence.groupby(["tf", "target_gene"], sort=True):
        direct = group.loc[group["motif_support_class"].eq("direct")]
        row = {
            "tf": str(tf),
            "target_gene": str(gene),
            "motif_support_class": "direct" if len(direct) else "extended_only",
            "n_supported_motifs": int(group["MotifID"].nunique()),
            "n_direct_supported_motifs": int(direct["MotifID"].nunique()),
            "n_unique_query_peaks": int(group["query_region"].nunique()),
            "n_unique_screen_regions": int(group["mapped_db_region"].nunique()),
            "n_evidence_rows": int(len(group)),
            "max_motif_NES": float(pd.to_numeric(group["NES"], errors="coerce").max()),
            "max_motif_AUC": float(pd.to_numeric(group["AUC"], errors="coerce").max()),
            "min_abs_distance_to_tss": float(pd.to_numeric(group["abs_distance_to_tss"], errors="coerce").min()),
            "peak_gene_classes": ";".join(sorted(set(group["peak_gene_class"].dropna().astype(str)))),
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
        }
        for column in group.columns:
            if column.startswith("edge_"):
                values = group[column].dropna()
                if len(values):
                    row[column] = values.iloc[0]
        target_rows.append(row)
    target_summary = pd.DataFrame(target_rows).sort_values(
        ["tf", "motif_support_class", "max_motif_NES", "target_gene"],
        ascending=[True, True, False, True],
    )

    tf_rows = []
    for tf, group in evidence.groupby("tf", sort=True):
        direct = group.loc[group["motif_support_class"].eq("direct")]
        tf_rows.append({
            "tf": str(tf),
            "n_supported_motifs": int(group["MotifID"].nunique()),
            "n_direct_supported_motifs": int(direct["MotifID"].nunique()),
            "n_extended_only_supported_motifs": int(group.loc[group["motif_support_class"].eq("extended_only"), "MotifID"].nunique()),
            "n_supported_target_genes": int(group["target_gene"].nunique()),
            "n_supported_query_peaks": int(group["query_region"].nunique()),
            "n_supported_screen_regions": int(group["mapped_db_region"].nunique()),
            "n_evidence_rows": int(len(group)),
            "max_motif_NES": float(pd.to_numeric(group["NES"], errors="coerce").max()),
            "motif_support_interpretation": "direct_and_or_extended" if len(direct) else "extended_only",
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
        })
    tf_summary = pd.DataFrame(tf_rows).sort_values("tf")

    primary_tfs = set(cfg["regulators"]["primary_passed_all_stage74_gates"])
    observed_tfs = set(tf_summary["tf"].astype(str))
    missing_primary_tfs = sorted(primary_tfs - observed_tfs)
    assembly_integrity_pass = bool(
        len(evidence)
        and unmatched_peak_rows == 0
        and unmatched_edge_rows == 0
        and not missing_primary_tfs
    )

    outputs = f5c["outputs"]
    evidence_path = project / outputs["evidence_csv"]
    target_path = project / outputs["target_summary_csv"]
    tf_path = project / outputs["tf_summary_csv"]
    report_path = project / outputs["report_json"]
    for path in [evidence_path, target_path, tf_path, report_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
    evidence.to_csv(evidence_path, index=False)
    target_summary.to_csv(target_path, index=False)
    tf_summary.to_csv(tf_path, index=False)

    report = {
        "stage": "stage75f_primary_tf_region_gene_evidence_v1",
        "purpose": "assemble primary TF-region-gene candidate evidence",
        "assembly_integrity_pass": assembly_integrity_pass,
        "n_supported_motifs": int(evidence[["tf", "MotifID"]].drop_duplicates().shape[0]),
        "n_evidence_rows": int(len(evidence)),
        "n_target_gene_rows": int(len(target_summary)),
        "n_primary_tfs": int(len(tf_summary)),
        "n_unique_target_genes": int(evidence["target_gene"].nunique()),
        "n_unique_query_peaks": int(evidence["query_region"].nunique()),
        "n_unique_screen_regions": int(evidence["mapped_db_region"].nunique()),
        "unmatched_peak_rows": unmatched_peak_rows,
        "unmatched_candidate_edge_rows": unmatched_edge_rows,
        "missing_primary_tfs": missing_primary_tfs,
        "tf_summaries": tf_summary.to_dict(orient="records"),
        "outputs": outputs,
        "claim_boundaries": {
            "motif_enrichment_completed": True,
            "enhancer_informed_candidate_evidence": True,
            "peak_to_gene_support_is_proximity_only": True,
            "tf_target_support_is_candidate_coactivity": True,
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
            "approved_wording": cfg.get("safety", {}).get("approved_wording"),
        },
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote: {evidence_path}")
    print(f"Wrote: {target_path}")
    print(f"Wrote: {tf_path}")
    print(f"Wrote: {report_path}")
    print(json.dumps(report, indent=2))
    return 0 if assembly_integrity_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
