from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import networkx as nx
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare deterministic graph-ablation edge inputs without training."
    )
    parser.add_argument(
        "--source-graph",
        type=Path,
        default=Path("results/tables/v2_graph_consensus_edges.csv"),
    )
    parser.add_argument(
        "--h5ad",
        type=Path,
        default=Path(
            "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/tables/ablation_edge_sets"),
    )
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument("--swaps-per-edge", type=int, default=5)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/graph_ablation_edge_set_manifest_v1.md"),
    )
    return parser.parse_args()


def canonical_edges(frame: pd.DataFrame) -> set[tuple[int, int]]:
    return {
        (min(int(source), int(target)), max(int(source), int(target)))
        for source, target in frame[["source_idx", "target_idx"]].itertuples(
            index=False, name=None
        )
    }


def main() -> None:
    args = parse_args()
    source = pd.read_csv(args.source_graph)
    required = {"source", "target", "source_idx", "target_idx"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"Source graph missing columns: {sorted(missing)}")

    adata = ad.read_h5ad(args.h5ad, backed="r")
    genes = adata.var_names.astype(str).tolist()
    adata.file.close()
    n_nodes = len(genes)
    if n_nodes != 2957:
        raise ValueError(f"Expected 2,957 model features, found {n_nodes}")
    if source[["source_idx", "target_idx"]].min().min() < 0:
        raise ValueError("Source graph contains negative node indices")
    if source[["source_idx", "target_idx"]].max().max() >= n_nodes:
        raise ValueError("Source graph index exceeds model feature order")
    if source.duplicated(["source_idx", "target_idx"]).any():
        raise ValueError("Source graph contains duplicate directed rows")
    if source["source_idx"].eq(source["target_idx"]).any():
        raise ValueError("Source graph unexpectedly contains self-loops")

    original_edges = canonical_edges(source)
    if len(original_edges) != len(source):
        raise ValueError("Source graph contains duplicate undirected edges")

    # Explicit loops for every model feature are required because the loader infers
    # loop count from the maximum index present in the edge file.
    identity = pd.DataFrame(
        {
            "source": genes,
            "target": genes,
            "source_idx": np.arange(n_nodes, dtype=np.int64),
            "target_idx": np.arange(n_nodes, dtype=np.int64),
            "support": "identity_self_loop",
            "string_score": np.nan,
            "wgcna_tom": np.nan,
        }
    )

    graph = nx.Graph()
    graph.add_nodes_from(range(n_nodes))
    graph.add_edges_from(original_edges)
    original_degree = dict(graph.degree())
    nswap = args.swaps_per_edge * graph.number_of_edges()
    nx.double_edge_swap(
        graph,
        nswap=nswap,
        max_tries=max(nswap * 20, 100),
        seed=args.seed,
    )
    shuffled_edges = sorted(
        (min(int(source_idx), int(target_idx)), max(int(source_idx), int(target_idx)))
        for source_idx, target_idx in graph.edges()
    )
    if len(shuffled_edges) != len(original_edges):
        raise ValueError("Degree-preserving shuffle changed edge count")
    if any(source_idx == target_idx for source_idx, target_idx in shuffled_edges):
        raise ValueError("Degree-preserving shuffle created self-loops")
    if len(shuffled_edges) != len(set(shuffled_edges)):
        raise ValueError("Degree-preserving shuffle created duplicate edges")
    if dict(graph.degree()) != original_degree:
        raise ValueError("Degree-preserving shuffle changed node degrees")

    shuffled = pd.DataFrame(shuffled_edges, columns=["source_idx", "target_idx"])
    shuffled.insert(
        0, "target", [genes[index] for index in shuffled["target_idx"]]
    )
    shuffled.insert(
        0, "source", [genes[index] for index in shuffled["source_idx"]]
    )
    shuffled["support"] = "degree_preserving_double_edge_swap"
    shuffled["string_score"] = np.nan
    shuffled["wgcna_tom"] = np.nan

    overlap = len(original_edges & set(shuffled_edges))
    overlap_fraction = overlap / len(original_edges)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    identity_path = args.out_dir / "no_graph_identity_edges_v1.csv"
    shuffled_path = args.out_dir / "shuffled_graph_edges_v1.csv"
    manifest_path = args.out_dir / "graph_ablation_edge_set_manifest_v1.csv"
    identity.to_csv(identity_path, index=False)
    shuffled.to_csv(shuffled_path, index=False)

    manifest = pd.DataFrame(
        [
            {
                "edge_set_name": "no_graph_identity_edges_v1",
                "path": str(identity_path),
                "n_nodes": n_nodes,
                "n_edges": len(identity),
                "source_graph": str(args.source_graph),
                "shuffle_seed": "",
                "degree_preserving": True,
                "allows_self_loops": True,
                "allows_duplicate_edges": False,
                "directed_or_undirected_assumption": (
                    "one self-loop row per node; loader symmetrizes and adds loops; "
                    "normalized adjacency remains identity"
                ),
                "training_readiness_status": "ready_for_future_approval_gated_training",
                "notes": (
                    "No informative inter-gene edges. Explicit loops preserve all "
                    "2,957 nodes under the current loader's max-index inference."
                ),
            },
            {
                "edge_set_name": "shuffled_graph_edges_v1",
                "path": str(shuffled_path),
                "n_nodes": n_nodes,
                "n_edges": len(shuffled),
                "source_graph": str(args.source_graph),
                "shuffle_seed": args.seed,
                "degree_preserving": True,
                "allows_self_loops": False,
                "allows_duplicate_edges": False,
                "directed_or_undirected_assumption": (
                    "source stores each undirected edge once; loader symmetrizes"
                ),
                "training_readiness_status": "ready_for_future_approval_gated_training",
                "notes": (
                    f"NetworkX double-edge swap; {args.swaps_per_edge} requested "
                    f"swaps per edge; original-edge overlap fraction={overlap_fraction:.6f}."
                ),
            },
        ]
    )
    manifest.to_csv(manifest_path, index=False)

    stage_a_template = (
        "python scripts/train_graph_jepa_stage_a_fast.py "
        "--h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad "
        "--edge-csv {edge_csv} --out-dir {out_dir} --epochs <epochs> "
        "--seed <seed> --history-csv {history_csv} --log-file {log_file}"
    )
    lines = [
        "# Graph Ablation Edge-Set Manifest v1",
        "",
        "## Original graph summary",
        "",
        f"- Source: `{args.source_graph}`",
        f"- Model nodes: {n_nodes}",
        f"- Undirected edges stored once: {len(original_edges)}",
        "- Original self-loops: 0",
        "- Original duplicate undirected edges: 0",
        "",
        "## No-graph / identity definition",
        "",
        f"- Path: `{identity_path}`",
        f"- Rows: {len(identity)} explicit self-loops, one for each model feature.",
        "- Rationale: an empty edge file causes the current loader to infer only one node. Explicit self-loops retain all features while removing informative inter-gene message passing.",
        "- The loader symmetrizes and adds self-loops again, but sparse coalescing and degree normalization still produce identity propagation.",
        "- Readiness: `ready_for_future_approval_gated_training`.",
        "",
        "## Shuffled graph definition",
        "",
        f"- Path: `{shuffled_path}`",
        f"- Seed: {args.seed}",
        "- Method: deterministic NetworkX double-edge swap on a simple undirected graph.",
        "- Degree preserving: yes, exactly for every node.",
        f"- Edge count preserved: {len(shuffled)}",
        "- Self-loops: none.",
        "- Duplicate undirected edges: none.",
        f"- Original-edge overlap fraction after shuffle: {overlap_fraction:.6f}",
        "- Readiness: `ready_for_future_approval_gated_training`.",
        "",
        "## Future training command templates",
        "",
        "No-graph Stage A:",
        "",
        "```text",
        stage_a_template.format(
            edge_csv=identity_path,
            out_dir="results/models/ablation_no_graph_stage_a_v1",
            history_csv="results/tables/ablation_no_graph_stage_a_v1_history.csv",
            log_file="results/logs/ablation_no_graph_stage_a_v1.log",
        ),
        "```",
        "",
        "Shuffled-graph Stage A:",
        "",
        "```text",
        stage_a_template.format(
            edge_csv=shuffled_path,
            out_dir="results/models/ablation_shuffled_graph_stage_a_v1",
            history_csv="results/tables/ablation_shuffled_graph_stage_a_v1_history.csv",
            log_file="results/logs/ablation_shuffled_graph_stage_a_v1.log",
        ),
        "```",
        "",
        "## Boundary",
        "",
        "- No training was run.",
        "- These files are frozen inputs for future approval-gated ablations.",
        "- Preparing edge sets does not change evidence levels or scientific claims.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(manifest.to_string(index=False))
    print(f"Wrote {identity_path}")
    print(f"Wrote {shuffled_path}")
    print(f"Wrote {manifest_path}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
