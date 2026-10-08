#!/usr/bin/env python3
"""Prepare resumable Stage75F regulator/target/region batches.

This is a manifest builder only. It streams the Stage75C peak-to-gene scaffold,
selects bounded candidate regions for Stage72B regulator-target edges, and
writes per-batch BED/TF/gene files for later motif-enrichment pilots. It does
not run motif enrichment or claim validated regulation.
"""

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
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return data


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def select_edges(edge_path: Path, cfg: dict[str, Any]) -> pd.DataFrame:
    edges = pd.read_csv(edge_path)
    required = {"source_tf", "target_gene"}
    missing = required - set(edges.columns)
    if missing:
        raise ValueError(f"Missing Stage72B edge columns: {sorted(missing)}")
    if "edge_candidate_pass" in edges.columns:
        edges = edges.loc[as_bool(edges["edge_candidate_pass"])].copy()
    primary = list(cfg["regulators"]["primary_passed_all_stage74_gates"])
    secondary = list(cfg["regulators"].get("descriptive_secondary_hypotheses", []))
    regulators = primary + secondary if cfg["batching"].get("include_secondary_regulators", True) else primary
    edges = edges.loc[edges["source_tf"].isin(regulators)].copy()
    edges["_primary_rank"] = edges["source_tf"].map({tf: 0 for tf in primary} | {tf: 1 for tf in secondary}).fillna(2)
    edges["_sign_stability"] = pd.to_numeric(edges.get("bootstrap_sign_stability", 0), errors="coerce").fillna(0)
    rho = edges["bootstrap_median_rho"] if "bootstrap_median_rho" in edges.columns else edges.get("spearman_rho", pd.Series(0, index=edges.index))
    edges["_abs_rho"] = pd.to_numeric(rho, errors="coerce").abs().fillna(0)
    top_targets = int(cfg["batching"].get("top_targets_per_tf", 50))
    edges = (
        edges.sort_values(["_primary_rank", "source_tf", "_sign_stability", "_abs_rho", "target_gene"], ascending=[True, True, False, False, True])
        .groupby("source_tf", sort=False, as_index=False)
        .head(top_targets)
        .drop(columns=["_primary_rank", "_sign_stability", "_abs_rho"])
        .reset_index(drop=True)
    )
    edges["stage75f_role"] = np.where(edges["source_tf"].isin(primary), "primary_stage74_gate_pass", "descriptive_secondary_hypothesis")
    edges["selection_purpose"] = "stage75f_batching_not_candidate_selection"
    return edges


def stream_select_peaks(peak_path: Path, target_genes: set[str], cfg: dict[str, Any]) -> pd.DataFrame:
    usecols = {"peak_id", "chrom", "start", "end", "nearest_gene", "abs_distance_to_tss", "peak_gene_class"}
    chunks = []
    for chunk in pd.read_csv(peak_path, usecols=lambda c: c in usecols, chunksize=int(cfg["batching"].get("peak_chunksize", 250000))):
        chunk = chunk.loc[chunk["nearest_gene"].astype(str).isin(target_genes)].copy()
        if len(chunk):
            chunks.append(chunk)
    if not chunks:
        return pd.DataFrame(columns=sorted(usecols))
    peaks = pd.concat(chunks, ignore_index=True)
    class_order = {name: rank for rank, name in enumerate(cfg["batching"].get("prefer_peak_classes", []))}
    peaks["_class_rank"] = peaks.get("peak_gene_class", pd.Series("", index=peaks.index)).map(class_order).fillna(len(class_order) + 1)
    peaks["_distance"] = pd.to_numeric(peaks.get("abs_distance_to_tss", np.inf), errors="coerce").fillna(np.inf)
    top_peaks = int(cfg["batching"].get("top_peaks_per_target", 10))
    peaks = (
        peaks.sort_values(["nearest_gene", "_class_rank", "_distance", "peak_id"], ascending=[True, True, True, True])
        .groupby("nearest_gene", sort=False, as_index=False)
        .head(top_peaks)
        .drop(columns=["_class_rank", "_distance"])
        .reset_index(drop=True)
    )
    peaks["selection_purpose"] = "stage75f_proximity_scaffold_not_regulation"
    return peaks


def write_batch_files(project: Path, batch_dir: Path, edges: pd.DataFrame, peaks: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    batch_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    max_regions = int(cfg["batching"].get("max_regions_per_batch", 5000))
    batch_id = 0
    for tf, tf_edges in edges.groupby("source_tf", sort=False):
        genes = sorted(set(tf_edges["target_gene"].dropna().astype(str)))
        tf_peaks = peaks.loc[peaks["nearest_gene"].astype(str).isin(genes)].copy()
        if tf_peaks.empty:
            region_chunks = [tf_peaks]
        else:
            region_chunks = [tf_peaks.iloc[i:i + max_regions].copy() for i in range(0, len(tf_peaks), max_regions)]
        for chunk_index, peak_chunk in enumerate(region_chunks, start=1):
            batch_id += 1
            stem = f"stage75f_batch_{batch_id:04d}_{tf}"
            bed_path = batch_dir / f"{stem}.regions.bed"
            tf_path = batch_dir / f"{stem}.tf.txt"
            gene_path = batch_dir / f"{stem}.genes.txt"
            meta_path = batch_dir / f"{stem}.manifest.json"
            if len(peak_chunk):
                bed = peak_chunk[["chrom", "start", "end", "peak_id", "nearest_gene"]].copy()
                bed["name"] = bed["nearest_gene"].astype(str) + "|" + bed["peak_id"].astype(str)
                bed["score"] = 0
                bed["strand"] = "."
                bed[["chrom", "start", "end", "name", "score", "strand"]].to_csv(bed_path, sep="\t", header=False, index=False)
            else:
                bed_path.write_text("", encoding="utf-8")
            tf_path.write_text(f"{tf}\n", encoding="utf-8")
            gene_path.write_text("\n".join(genes) + "\n", encoding="utf-8")
            meta = {
                "batch_id": batch_id,
                "tf": tf,
                "chunk_index_for_tf": chunk_index,
                "n_target_genes": len(genes),
                "n_regions": int(len(peak_chunk)),
                "not_motif_enrichment": True,
                "not_validated_regulation": True,
            }
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            rows.append({
                "batch_id": batch_id,
                "tf": tf,
                "chunk_index_for_tf": chunk_index,
                "n_target_genes": len(genes),
                "n_regions": int(len(peak_chunk)),
                "bed_path": str(bed_path.relative_to(project)),
                "tf_path": str(tf_path.relative_to(project)),
                "gene_path": str(gene_path.relative_to(project)),
                "manifest_path": str(meta_path.relative_to(project)),
                "completed": False,
            })
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    inputs = cfg["inputs"]
    outputs = cfg["outputs"]

    edges = select_edges(project / inputs["stage72b_edges"], cfg)
    target_genes = set(edges["target_gene"].dropna().astype(str))
    peaks = stream_select_peaks(project / inputs["stage75c_peak_to_gene"], target_genes, cfg)
    batch_manifest = write_batch_files(project, project / outputs["batch_dir"], edges, peaks, cfg)

    edge_out = project / outputs["candidate_edges"]
    peak_out = project / outputs["candidate_peak_gene_links"]
    batch_out = project / outputs["batch_manifest_csv"]
    manifest_out = project / outputs["manifest_json"]
    for out in [edge_out, peak_out, batch_out, manifest_out]:
        out.parent.mkdir(parents=True, exist_ok=True)
    edges.to_csv(edge_out, index=False)
    peaks.to_csv(peak_out, index=False)
    batch_manifest.to_csv(batch_out, index=False)
    manifest = {
        "stage": "stage75f_out_of_core_batch_manifest_v1",
        "purpose": "resumable regulator/region batch preparation only",
        "n_candidate_edges": int(len(edges)),
        "n_candidate_peak_gene_links": int(len(peaks)),
        "n_batches": int(len(batch_manifest)),
        "not_motif_enrichment": True,
        "not_validated_regulation": True,
        "safety": cfg.get("safety", {}),
    }
    manifest_out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote: {edge_out}")
    print(f"Wrote: {peak_out}")
    print(f"Wrote: {batch_out}")
    print(f"Wrote: {manifest_out}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
