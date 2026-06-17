from __future__ import annotations

import argparse
import hashlib
import math
import os
import random
import subprocess
import sys
import time
import traceback
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd


DEFAULT_H5AD = Path("data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
DEFAULT_EDGE_CSV = Path("results/tables/v2_graph_consensus_edges.csv")
DEFAULT_EDGE_INDEX = Path("results/tables/v2_graph_consensus_edge_index.csv")
DEFAULT_ENCODER = Path("results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt")
DEFAULT_HEAD = Path("results/models/pathology_heads_stage_b_lp/best_pathology_head.pt")
DEFAULT_OUT = Path("results/tables/discovery_feature_wide_pathology_axis_counterfactuals.csv")
DEFAULT_PILOT_OUT = Path("results/tables/discovery_pilot_feature_wide_pathology_axis_counterfactuals.csv")
DEFAULT_REPORT = Path("results/reports/discovery_feature_wide_counterfactual_feasibility.md")
DEFAULT_MANIFEST = Path("results/reports/discovery_feature_wide_run_manifest.md")

TARGET_TO_DELTA = {
    "percent AT8 positive area_Grey matter": "AT8_delta",
    "percent 6e10 positive area_Grey matter": "A_beta_6e10_delta",
    "percent GFAP positive area_Grey matter": "GFAP_delta",
    "percent Iba1 positive area_Grey matter": "Iba1_delta",
    "percent NeuN positive area_Grey matter": "NeuN_delta",
}

PRIMARY_CANDIDATES = [
    "TLR2",
    "APP",
    "APOE",
    "CD4",
    "P2RY12",
    "P2RY13",
    "CX3CR1",
    "CSF1R",
    "CTSD",
    "BCL2",
    "MAPK1",
    "STAT3",
    "UGCG",
    "ROCK1",
    "PLCG2",
    "TREM2",
    "TYROBP",
    "C1QA",
    "C1QB",
    "C1QC",
    "C3",
    "CD74",
    "HLA-DRA",
    "SPP1",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or launch feature-wide Graph-JEPA pathology-axis counterfactual scoring."
    )
    parser.add_argument("--gene-list", type=Path, default=None)
    parser.add_argument("--scope", choices=["feature_wide", "graph_connected"], default="graph_connected")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_ENCODER)
    parser.add_argument("--pathology-head", type=Path, default=DEFAULT_HEAD)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--h5ad", type=Path, default=DEFAULT_H5AD)
    parser.add_argument("--edge-csv", type=Path, default=DEFAULT_EDGE_INDEX)
    parser.add_argument("--graph-edges", type=Path, default=DEFAULT_EDGE_CSV)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pilot-out", type=Path, default=DEFAULT_PILOT_OUT)
    parser.add_argument("--feasibility-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--skip-manifold-nearest-neighbor", action="store_true")
    parser.add_argument("--limit-genes", type=int, default=None)
    parser.add_argument("--start-chunk", type=int, default=1)
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--max-cells", type=int, default=10000)
    parser.add_argument("--intervention", choices=["zero", "global_mean", "p99"], default="global_mean")
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args()


def read_feature_genes(h5ad_path: Path) -> list[str]:
    if not h5ad_path.exists():
        raise FileNotFoundError(f"Missing h5ad feature source: {h5ad_path}")
    adata = ad.read_h5ad(h5ad_path, backed="r")
    try:
        return [str(g).upper() for g in adata.var_names]
    finally:
        adata.file.close()


def read_graph_genes(edge_path: Path) -> set[str]:
    if not edge_path.exists():
        return set()
    edges = pd.read_csv(edge_path, usecols=["source", "target"])
    return set(edges["source"].astype(str).str.upper()) | set(edges["target"].astype(str).str.upper())


def read_gene_list(path: Path) -> list[str]:
    data = pd.read_csv(path)
    if "gene" in data.columns:
        col = "gene"
    elif "candidate" in data.columns:
        col = "candidate"
    else:
        col = data.columns[0]
    return sorted(set(data[col].astype(str).str.upper()))


def top_degree_hubs(edge_path: Path, n: int) -> list[str]:
    if not edge_path.exists():
        return []
    edges = pd.read_csv(edge_path, usecols=["source", "target"])
    values = pd.concat(
        [edges["source"].astype(str).str.upper(), edges["target"].astype(str).str.upper()],
        ignore_index=True,
    )
    return values.value_counts().head(n).index.astype(str).tolist()


def choose_genes(args: argparse.Namespace) -> tuple[list[str], list[str], set[str]]:
    feature_genes = read_feature_genes(args.h5ad)
    feature_set = set(feature_genes)
    graph_genes = read_graph_genes(args.graph_edges)
    if args.gene_list:
        genes = [g for g in read_gene_list(args.gene_list) if g in feature_set]
    elif args.scope == "graph_connected":
        genes = [g for g in feature_genes if g in graph_genes]
    else:
        genes = feature_genes

    if args.pilot:
        rng = random.Random(args.seed)
        current = [g for g in PRIMARY_CANDIDATES if g in feature_set]
        hubs = [g for g in top_degree_hubs(args.graph_edges, 100) if g in feature_set]
        pool = [g for g in genes if g not in set(current)]
        random_genes = rng.sample(pool, min(100, len(pool))) if pool else []
        pilot_genes = sorted(set(current + hubs[:100] + random_genes))
        genes = pilot_genes
    if args.limit_genes is not None:
        genes = genes[: max(args.limit_genes, 0)]
    return genes, feature_genes, graph_genes


def chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def stable_hash(values: list[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()[:16]


def run_signature(args: argparse.Namespace, genes: list[str]) -> str:
    wrapper_hash = stable_hash([Path(__file__).read_text(encoding="utf-8")])
    parts = [
        f"scope={args.scope}",
        f"pilot={args.pilot}",
        f"out={args.pilot_out if args.pilot else args.out}",
        f"checkpoint={args.checkpoint}",
        f"pathology_head={args.pathology_head}",
        f"h5ad={args.h5ad}",
        f"edge_csv={args.edge_csv}",
        f"intervention={args.intervention}",
        f"max_cells={args.max_cells}",
        f"batch_size={args.batch_size}",
        f"chunk_size={args.chunk_size}",
        f"seed={args.seed}",
        f"skip_manifold_nearest_neighbor={args.skip_manifold_nearest_neighbor}",
        f"wrapper_hash={wrapper_hash}",
        f"genes_hash={stable_hash(genes)}",
    ]
    return stable_hash(parts)


def chunk_signature(args: argparse.Namespace, genes: list[str]) -> str:
    return run_signature(args, genes)


def chunk_cache_dir(selected_out: Path) -> Path:
    return Path("results/tables/_feature_wide_counterfactual_chunks") / selected_out.stem


def chunk_paths(temp_dir: Path, chunk_idx: int) -> tuple[Path, Path, Path]:
    summary_path = temp_dir / f"feature_wide_chunk_{chunk_idx:04d}_summary.csv"
    donor_path = temp_dir / f"feature_wide_chunk_{chunk_idx:04d}_donor.csv"
    normalized_path = temp_dir / f"feature_wide_chunk_{chunk_idx:04d}_normalized.csv"
    return summary_path, donor_path, normalized_path


def write_feasibility_report(
    args: argparse.Namespace,
    genes: list[str],
    feature_genes: list[str],
    graph_genes: set[str],
    feasible: bool,
    blockers: list[str],
) -> None:
    n_batches = math.ceil(len(genes) / max(args.chunk_size, 1))
    lines = [
        "# Discovery Feature-Wide Counterfactual Feasibility",
        "",
        "## Candidate Counterfactual Script Found",
        "",
        "- `scripts/pathology_head_counterfactual_knockout.py`",
        "- Uses frozen `FastGraphGeneJEPA` encoder plus frozen pathology head.",
        "- Supports `--genes`, `--mode gene`, batching, `--max-cells`, and no retraining.",
        "",
        "## Required Artifacts",
        "",
        f"- Encoder checkpoint: `{args.checkpoint}` (`{'available' if args.checkpoint.exists() else 'missing'}`)",
        f"- Pathology head: `{args.pathology_head}` (`{'available' if args.pathology_head.exists() else 'missing'}`)",
        f"- H5AD / feature source: `{args.h5ad}` (`{'available' if args.h5ad.exists() else 'missing'}`)",
        f"- Edge index: `{args.edge_csv}` (`{'available' if args.edge_csv.exists() else 'missing'}`)",
        f"- Graph edge names: `{args.graph_edges}` (`{'available' if args.graph_edges.exists() else 'missing'}`)",
        "",
        "## Feature Universe",
        "",
        f"- Feature genes: {len(feature_genes):,}",
        f"- Graph-connected feature genes: {sum(g in graph_genes for g in feature_genes):,}",
        f"- Selected scope: `{args.scope}`",
        f"- Selected genes for this run: {len(genes):,}",
        f"- Chunk size: {args.chunk_size:,}",
        f"- Estimated chunks / script calls: {n_batches:,}",
        f"- Max cells per perturbation run: {args.max_cells:,}",
        "",
        "## Feasibility",
        "",
        f"- Feasible now: `{feasible}`",
    ]
    if blockers:
        lines.append("- Blockers:")
        for blocker in blockers:
            lines.append(f"  - {blocker}")
    else:
        lines.append("- Blockers: none detected for dry-run / pilot orchestration.")
    lines.extend(
        [
            "",
            "## Estimated Output Paths",
            "",
            f"- Full feature-wide output: `{args.out}`",
            f"- Pilot output: `{args.pilot_out}`",
            "",
            "## Claim Boundary",
            "",
            "Feature-wide counterfactuals are still model-implied perturbation scores, not biological intervention results. They improve null testing and ranking robustness, but they do not prove causality.",
            "",
        ]
    )
    args.feasibility_report.parent.mkdir(parents=True, exist_ok=True)
    args.feasibility_report.write_text("\n".join(lines), encoding="utf-8")


def normalize_existing_summary(summary: pd.DataFrame, scope: str) -> pd.DataFrame:
    out = pd.DataFrame()
    out["gene"] = summary.get("perturbation", pd.Series(dtype=str)).astype(str).str.upper()
    out["scope"] = scope
    for source, dest in TARGET_TO_DELTA.items():
        col = f"mean_delta_{source}"
        out[dest] = pd.to_numeric(summary[col], errors="coerce") if col in summary.columns else np.nan
    manifold_fraction = pd.to_numeric(summary.get("manifold_violation_fraction", np.nan), errors="coerce")
    out["manifold_safety_status"] = np.where(
        manifold_fraction.isna(),
        "not_computed",
        np.where(manifold_fraction <= 0.05, "within_manifold_threshold", "manifold_caution"),
    )
    out["prediction_safety_status"] = "not_separately_audited"
    out["perturbation_success"] = True
    out["failure_reason"] = ""
    passthrough = [
        "mean_latent_shift",
        "median_latent_shift",
        "mean_nearest_real_cell_distance",
        "p95_nearest_real_cell_distance",
        "baseline_nn_p95_threshold",
        "manifold_violation_fraction",
    ]
    for col in passthrough:
        if col in summary.columns:
            out[col] = summary[col]
    return out


def run_chunk(
    args: argparse.Namespace,
    genes: list[str],
    chunk_idx: int,
    temp_dir: Path,
    *,
    current_signature: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    summary_path, donor_path, normalized_path = chunk_paths(temp_dir, chunk_idx)
    metadata_path = temp_dir / f"feature_wide_chunk_{chunk_idx:04d}_metadata.csv"
    log_path = temp_dir / f"feature_wide_chunk_{chunk_idx:04d}.log"
    this_signature = chunk_signature(args, genes)
    started = time.time()
    if args.resume and normalized_path.exists() and metadata_path.exists():
        meta = pd.read_csv(metadata_path)
        signature = str(meta.get("run_signature", pd.Series([""])).iloc[0])
        if signature == this_signature:
            print(f"Skipping completed normalized chunk {chunk_idx}: {normalized_path}")
            elapsed = time.time() - started
            return pd.read_csv(normalized_path), {
                "chunk": chunk_idx,
                "n_genes": len(genes),
                "status": "skipped_resume",
                "elapsed_seconds": elapsed,
                "normalized_path": str(normalized_path),
                "log_path": str(log_path),
                "summary_path": str(summary_path),
                "failure_reason": "",
            }
        print(f"Existing chunk {chunk_idx} has mismatched signature; recomputing.")
    cmd = [
        sys.executable,
        "scripts/pathology_head_counterfactual_knockout.py",
        "--encoder-checkpoint",
        str(args.checkpoint),
        "--pathology-head",
        str(args.pathology_head),
        "--h5ad",
        str(args.h5ad),
        "--edge-csv",
        str(args.edge_csv),
        "--mode",
        "gene",
        "--genes",
        *genes,
        "--intervention",
        args.intervention,
        "--max-cells",
        str(args.max_cells),
        "--batch-size",
        str(args.batch_size),
        "--seed",
        str(args.seed),
        "--device",
        args.device,
        "--summary-out",
        str(summary_path),
        "--donor-out",
        str(donor_path),
    ]
    if args.skip_manifold_nearest_neighbor:
        cmd.append("--skip-manifold-nearest-neighbor")
    print(f"Launching chunk {chunk_idx} with {len(genes)} genes")
    env = os.environ.copy()
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")
    env.setdefault("SKLEARN_NUM_THREADS", "1")
    with log_path.open("w", encoding="utf-8") as log:
        log.write("Command:\n")
        log.write(" ".join(cmd))
        log.write("\n\n")
        log.flush()
        subprocess.run(cmd, check=True, env=env, stdout=log, stderr=subprocess.STDOUT)
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)
    raw = pd.read_csv(summary_path)
    normalized = normalize_existing_summary(raw, args.scope)
    normalized.to_csv(normalized_path, index=False)
    elapsed = time.time() - started
    pd.DataFrame(
        [
            {
                "chunk": chunk_idx,
                "run_signature": this_signature,
                "chunk_signature": this_signature,
                "n_genes": len(genes),
                "genes_hash": stable_hash(genes),
                "elapsed_seconds": elapsed,
                "seconds_per_gene": elapsed / max(len(genes), 1),
                "summary_path": str(summary_path),
                "donor_path": str(donor_path),
                "normalized_path": str(normalized_path),
                "log_path": str(log_path),
            }
        ]
    ).to_csv(metadata_path, index=False)
    return normalized, {
        "chunk": chunk_idx,
        "n_genes": len(genes),
        "status": "completed",
        "elapsed_seconds": elapsed,
        "normalized_path": str(normalized_path),
        "summary_path": str(summary_path),
        "log_path": str(log_path),
        "failure_reason": "",
    }


def write_run_manifest(
    args: argparse.Namespace,
    selected_out: Path,
    genes: list[str],
    chunk_rows: list[dict[str, object]],
    *,
    current_signature: str,
    total_elapsed: float,
) -> None:
    completed = sum(1 for row in chunk_rows if row.get("status") in {"completed", "skipped_resume"})
    failed = sum(1 for row in chunk_rows if row.get("status") == "failed")
    lines = [
        "# Discovery Feature-Wide Counterfactual Run Manifest",
        "",
        "## Run Configuration",
        "",
        f"- Output: `{selected_out}`",
        f"- Scope: `{args.scope}`",
        f"- Pilot: `{args.pilot}`",
        f"- Resume: `{args.resume}`",
        f"- Start chunk: `{args.start_chunk}`",
        f"- Limit genes: `{args.limit_genes}`",
        f"- Chunk size: `{args.chunk_size}`",
        f"- Batch size: `{args.batch_size}`",
        f"- Max cells: `{args.max_cells}`",
        f"- Intervention: `{args.intervention}`",
        f"- Run signature: `{current_signature}`",
        f"- Selected genes: {len(genes):,}",
        "",
        "## Progress",
        "",
        f"- Chunks completed or reused: {completed}",
        f"- Chunks failed: {failed}",
        f"- Total elapsed seconds: {total_elapsed:.1f}",
        f"- Total elapsed minutes: {total_elapsed / 60.0:.1f}",
        "",
        "## Chunk Timing",
        "",
        "| chunk | n_genes | status | elapsed_seconds | seconds_per_gene | normalized_path | log_path | failure_reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in chunk_rows:
        elapsed = float(row.get("elapsed_seconds", 0.0) or 0.0)
        n_genes = int(row.get("n_genes", 0) or 0)
        seconds_per_gene = elapsed / max(n_genes, 1)
        lines.append(
            "| {chunk} | {n_genes} | {status} | {elapsed:.1f} | {spg:.2f} | `{path}` | `{log_path}` | {failure} |".format(
                chunk=row.get("chunk", ""),
                n_genes=n_genes,
                status=row.get("status", ""),
                elapsed=elapsed,
                spg=seconds_per_gene,
                path=row.get("normalized_path", ""),
                log_path=row.get("log_path", ""),
                failure=str(row.get("failure_reason", "")).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Feature-wide counterfactuals are model-implied perturbation scores over the Graph-JEPA feature-gene universe, not biological intervention evidence and not genome-wide screening.",
            "",
        ]
    )
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    genes, feature_genes, graph_genes = choose_genes(args)
    blockers = []
    for label, path in [
        ("encoder checkpoint", args.checkpoint),
        ("pathology head", args.pathology_head),
        ("h5ad", args.h5ad),
        ("edge index", args.edge_csv),
    ]:
        if not path.exists():
            blockers.append(f"missing {label}: {path}")
    if not genes:
        blockers.append("selected gene list is empty")
    feasible = not blockers
    write_feasibility_report(args, genes, feature_genes, graph_genes, feasible, blockers)

    selected_out = args.pilot_out if args.pilot else args.out
    n_chunks = math.ceil(len(genes) / max(args.chunk_size, 1))
    print(f"Selected genes: {len(genes):,}")
    print(f"Scope: {args.scope}")
    print(f"Pilot: {args.pilot}")
    print(f"Estimated chunks: {n_chunks:,}")
    print(f"Feasibility report: {args.feasibility_report}")

    schema = [
        "gene",
        "scope",
        "AT8_delta",
        "A_beta_6e10_delta",
        "GFAP_delta",
        "Iba1_delta",
        "NeuN_delta",
        "manifold_safety_status",
        "prediction_safety_status",
        "perturbation_success",
        "failure_reason",
    ]
    if args.dry_run:
        print("Dry run only; no counterfactual inference launched.")
        print("Output schema:")
        print(", ".join(schema))
        return
    if not feasible:
        raise RuntimeError("Feature-wide counterfactual scoring is not feasible; see feasibility report.")

    temp_dir = chunk_cache_dir(selected_out)
    temp_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    chunk_rows: list[dict[str, object]] = []
    current_signature = run_signature(args, genes)
    all_chunks = chunks(genes, args.chunk_size)
    total_started = time.time()
    for idx, gene_chunk in enumerate(all_chunks, start=1):
        if idx < args.start_chunk:
            print(f"Skipping chunk {idx}/{n_chunks} because --start-chunk={args.start_chunk}")
            continue
        print(f"Running chunk {idx}/{n_chunks} ({len(gene_chunk)} genes)")
        try:
            normalized, chunk_row = run_chunk(
                args,
                gene_chunk,
                idx,
                temp_dir,
                current_signature=current_signature,
            )
            frames.append(normalized)
            chunk_rows.append(chunk_row)
        except Exception as exc:
            failure_reason = f"{type(exc).__name__}: {exc}"
            failure_traceback = traceback.format_exc()
            _, _, normalized_path = chunk_paths(temp_dir, idx)
            metadata_path = temp_dir / f"feature_wide_chunk_{idx:04d}_metadata.csv"
            log_path = temp_dir / f"feature_wide_chunk_{idx:04d}.log"
            pd.DataFrame(
                [
                    {
                        "chunk": idx,
                        "run_signature": chunk_signature(args, gene_chunk),
                        "n_genes": len(gene_chunk),
                        "genes_hash": stable_hash(gene_chunk),
                        "elapsed_seconds": 0.0,
                        "seconds_per_gene": 0.0,
                        "summary_path": "",
                        "donor_path": "",
                        "normalized_path": str(normalized_path),
                        "log_path": str(log_path),
                        "failure_reason": failure_reason,
                    }
                ]
            ).to_csv(metadata_path, index=False)
            chunk_rows.append(
                {
                    "chunk": idx,
                    "n_genes": len(gene_chunk),
                    "status": "failed",
                    "elapsed_seconds": 0.0,
                    "normalized_path": str(normalized_path),
                    "log_path": str(log_path),
                    "summary_path": "",
                    "failure_reason": failure_reason,
                }
            )
            if not args.continue_on_error:
                total_elapsed = time.time() - total_started
                write_run_manifest(
                    args,
                    selected_out,
                    genes,
                    chunk_rows,
                    current_signature=current_signature,
                    total_elapsed=total_elapsed,
                )
                print(f"Wrote failure manifest: {args.manifest_out}")
                raise RuntimeError(
                    f"Chunk {idx} failed with {failure_reason}. "
                    f"See {log_path}. Traceback:\n{failure_traceback}"
                ) from exc
            failed = pd.DataFrame(
                {
                    "gene": gene_chunk,
                    "scope": args.scope,
                    "AT8_delta": np.nan,
                    "A_beta_6e10_delta": np.nan,
                    "GFAP_delta": np.nan,
                    "Iba1_delta": np.nan,
                    "NeuN_delta": np.nan,
                    "manifold_safety_status": "not_available",
                    "prediction_safety_status": "not_available",
                    "perturbation_success": False,
                    "failure_reason": failure_reason,
                }
            )
            failed.to_csv(normalized_path, index=False)
            frames.append(failed)
    if args.resume:
        # Regenerate final output from all normalized chunks for this run signature,
        # including chunks completed in earlier invocations.
        frames = []
        for idx, _ in enumerate(all_chunks, start=1):
            _, _, normalized_path = chunk_paths(temp_dir, idx)
            metadata_path = temp_dir / f"feature_wide_chunk_{idx:04d}_metadata.csv"
            if normalized_path.exists() and metadata_path.exists():
                meta = pd.read_csv(metadata_path)
                signature = str(meta.get("run_signature", pd.Series([""])).iloc[0])
                expected_signature = chunk_signature(args, all_chunks[idx - 1])
                if signature == expected_signature:
                    frames.append(pd.read_csv(normalized_path))
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=schema)
    selected_out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(selected_out, index=False)
    print(f"Wrote {selected_out}")
    total_elapsed = time.time() - total_started
    write_run_manifest(
        args,
        selected_out,
        genes,
        chunk_rows,
        current_signature=current_signature,
        total_elapsed=total_elapsed,
    )
    print(f"Wrote {args.manifest_out}")


if __name__ == "__main__":
    main()
