#!/usr/bin/env python3
"""Build a bounded mechanics-only TF/target/peak subset for SCENIC+ smoke tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    paths = cfg["paths"]
    outputs = cfg["outputs"]
    subset_cfg = cfg["smoke_subset"]

    edge_path = project / paths["stage72b_edges"]["path"]
    peak_path = project / paths["stage75c_peak_to_gene"]["path"]

    if not edge_path.exists():
        raise FileNotFoundError(edge_path)
    if not peak_path.exists():
        raise FileNotFoundError(peak_path)

    edges = pd.read_csv(edge_path)
    required_edge_cols = {"source_tf", "target_gene"}
    missing_edge_cols = required_edge_cols - set(edges.columns)
    if missing_edge_cols:
        raise ValueError(f"Missing edge columns: {sorted(missing_edge_cols)}")

    if "edge_candidate_pass" in edges.columns:
        edges = edges.loc[as_bool(edges["edge_candidate_pass"])].copy()

    primary = list(cfg["regulators"]["primary_passed_all_stage74_gates"])
    secondary = list(cfg["regulators"]["descriptive_secondary_hypotheses"])
    regulators = primary + secondary
    edges = edges.loc[edges["source_tf"].isin(regulators)].copy()

    edges["_sign_stability"] = pd.to_numeric(
        edges.get("bootstrap_sign_stability", 0), errors="coerce"
    ).fillna(0)
    rho_source = (
        edges["bootstrap_median_rho"]
        if "bootstrap_median_rho" in edges.columns
        else edges.get("spearman_rho", pd.Series(0, index=edges.index))
    )
    edges["_abs_rho"] = pd.to_numeric(rho_source, errors="coerce").abs().fillna(0)
    edges["_primary_rank"] = edges["source_tf"].map(
        {tf: 0 for tf in primary} | {tf: 1 for tf in secondary}
    ).fillna(2)

    top_targets = int(subset_cfg.get("top_targets_per_tf", 10))
    edges = (
        edges.sort_values(
            ["_primary_rank", "source_tf", "_sign_stability", "_abs_rho", "target_gene"],
            ascending=[True, True, False, False, True],
        )
        .groupby("source_tf", sort=False, as_index=False)
        .head(top_targets)
        .drop(columns=["_sign_stability", "_abs_rho", "_primary_rank"])
        .reset_index(drop=True)
    )
    edges["stage75e_smoke_role"] = np.where(
        edges["source_tf"].isin(primary),
        "primary_stage74_gate_pass",
        "descriptive_secondary_hypothesis",
    )
    edges["selection_purpose"] = "mechanics_only_not_candidate_selection"

    target_genes = sorted(set(edges["target_gene"].dropna().astype(str)))
    usecols = [
        "peak_id", "chrom", "start", "end", "nearest_gene",
        "abs_distance_to_tss", "peak_gene_class"
    ]
    peaks = pd.read_csv(peak_path, usecols=lambda c: c in set(usecols))
    required_peak_cols = {"peak_id", "chrom", "start", "end", "nearest_gene"}
    missing_peak_cols = required_peak_cols - set(peaks.columns)
    if missing_peak_cols:
        raise ValueError(f"Missing peak columns: {sorted(missing_peak_cols)}")

    peaks = peaks.loc[peaks["nearest_gene"].isin(target_genes)].copy()
    class_order = {
        name: rank for rank, name in enumerate(subset_cfg.get("prefer_peak_classes", []))
    }
    peaks["_class_rank"] = peaks.get(
        "peak_gene_class", pd.Series("", index=peaks.index)
    ).map(class_order).fillna(len(class_order) + 1)
    peaks["_distance"] = pd.to_numeric(
        peaks.get("abs_distance_to_tss", np.inf), errors="coerce"
    ).fillna(np.inf)

    top_peaks = int(subset_cfg.get("top_peaks_per_target", 3))
    peaks = (
        peaks.sort_values(
            ["nearest_gene", "_class_rank", "_distance", "peak_id"],
            ascending=[True, True, True, True],
        )
        .groupby("nearest_gene", sort=False, as_index=False)
        .head(top_peaks)
        .drop(columns=["_class_rank", "_distance"])
        .reset_index(drop=True)
    )
    peaks["selection_purpose"] = "mechanics_only_proximity_scaffold_not_regulation"

    edge_out = project / outputs["smoke_edges"]
    peak_out = project / outputs["smoke_peak_gene_links"]
    bed_out = project / outputs["smoke_regions_bed"]
    tf_out = project / outputs["smoke_tf_list"]
    gene_out = project / outputs["smoke_gene_list"]
    manifest_out = project / outputs["smoke_manifest"]
    for path in (edge_out, peak_out, bed_out, tf_out, gene_out, manifest_out):
        path.parent.mkdir(parents=True, exist_ok=True)

    edges.to_csv(edge_out, index=False)
    peaks.to_csv(peak_out, index=False)

    bed = peaks[["chrom", "start", "end", "peak_id", "nearest_gene"]].copy()
    bed["name"] = bed["nearest_gene"].astype(str) + "|" + bed["peak_id"].astype(str)
    bed["score"] = 0
    bed["strand"] = "."
    bed[["chrom", "start", "end", "name", "score", "strand"]].to_csv(
        bed_out, sep="\t", header=False, index=False
    )

    present_tfs = [tf for tf in regulators if tf in set(edges["source_tf"])]
    tf_out.write_text("\n".join(present_tfs) + "\n", encoding="utf-8")
    gene_out.write_text("\n".join(target_genes) + "\n", encoding="utf-8")

    supported_targets = sorted(set(peaks["nearest_gene"].astype(str)))
    manifest = {
        "purpose": "mechanics-only SCENIC+/pycisTarget smoke subset",
        "not_for_candidate_selection": True,
        "not_motif_supported_yet": True,
        "not_validated_regulation": True,
        "primary_regulators": primary,
        "secondary_descriptive_regulators": secondary,
        "n_regulators_present": len(present_tfs),
        "regulators_present": present_tfs,
        "n_tf_target_edges": int(len(edges)),
        "n_target_genes": len(target_genes),
        "n_target_genes_with_proximity_peaks": len(supported_targets),
        "targets_without_selected_proximity_peaks": sorted(set(target_genes) - set(supported_targets)),
        "n_selected_peak_gene_links": int(len(peaks)),
        "outputs": {
            "edges": str(edge_out.relative_to(project)),
            "peak_gene_links": str(peak_out.relative_to(project)),
            "regions_bed": str(bed_out.relative_to(project)),
            "tf_list": str(tf_out.relative_to(project)),
            "gene_list": str(gene_out.relative_to(project)),
        },
        "safety": cfg.get("safety", {}),
    }
    manifest_out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote: {edge_out}")
    print(f"Wrote: {peak_out}")
    print(f"Wrote: {bed_out}")
    print(f"Wrote: {tf_out}")
    print(f"Wrote: {gene_out}")
    print(f"Wrote: {manifest_out}")
    print(json.dumps({
        "n_tf_target_edges": len(edges),
        "n_target_genes": len(target_genes),
        "n_peak_gene_links": len(peaks),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
