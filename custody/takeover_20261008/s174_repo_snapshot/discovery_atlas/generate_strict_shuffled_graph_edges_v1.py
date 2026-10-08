from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic degree-preserving shuffled graph with "
            "minimal overlap with the original graph. No training is performed."
        )
    )
    parser.add_argument(
        "--original-edges",
        type=Path,
        default=Path("results/tables/v2_graph_consensus_edges.csv"),
    )
    parser.add_argument(
        "--starting-edges",
        type=Path,
        default=Path(
            "results/tables/ablation_edge_sets/shuffled_graph_edges_v1.csv"
        ),
    )
    parser.add_argument(
        "--node-map",
        type=Path,
        default=Path(
            "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv"
        ),
    )
    parser.add_argument(
        "--edge-out",
        type=Path,
        default=Path(
            "results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv"
        ),
    )
    parser.add_argument(
        "--diagnostics-out",
        type=Path,
        default=Path(
            "results/tables/ablation_edge_sets/"
            "strict_shuffled_graph_edge_diagnostics_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/strict_shuffled_graph_edge_generation_v1.md"
        ),
    )
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument("--max-attempts", type=int, default=5_000_000)
    parser.add_argument("--patience", type=int, default=500_000)
    parser.add_argument("--neutral-probability", type=float, default=0.01)
    return parser.parse_args()


def canonical_pair(source: int, target: int) -> tuple[int, int]:
    return (source, target) if source < target else (target, source)


def canonical_edges(frame: pd.DataFrame) -> list[tuple[int, int]]:
    required = {"source_idx", "target_idx"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing edge columns: {sorted(missing)}")
    return [
        canonical_pair(int(source), int(target))
        for source, target in frame[["source_idx", "target_idx"]].itertuples(
            index=False, name=None
        )
    ]


def degree_sequence(edges: list[tuple[int, int]], n_nodes: int) -> np.ndarray:
    degree = np.zeros(n_nodes, dtype=np.int64)
    for source, target in edges:
        degree[source] += 1
        degree[target] += 1
    return degree


def gene_index_mapping(frames: list[pd.DataFrame], n_nodes: int) -> list[str]:
    mapping: dict[int, str] = {}
    for frame in frames:
        if not {"source", "target", "source_idx", "target_idx"}.issubset(frame.columns):
            continue
        for source, target, source_idx, target_idx in frame[
            ["source", "target", "source_idx", "target_idx"]
        ].itertuples(index=False, name=None):
            mapping[int(source_idx)] = str(source)
            mapping[int(target_idx)] = str(target)
    missing = [index for index in range(n_nodes) if index not in mapping]
    if missing:
        raise ValueError(f"Missing gene labels for node indices: {missing[:10]}")
    return [mapping[index] for index in range(n_nodes)]


def replace_overlap_position(
    overlap_positions: list[int],
    overlap_position_index: dict[int, int],
    position: int,
    is_overlap: bool,
) -> None:
    currently_overlap = position in overlap_position_index
    if currently_overlap == is_overlap:
        return
    if is_overlap:
        overlap_position_index[position] = len(overlap_positions)
        overlap_positions.append(position)
        return
    list_index = overlap_position_index.pop(position)
    last_position = overlap_positions.pop()
    if list_index < len(overlap_positions):
        overlap_positions[list_index] = last_position
        overlap_position_index[last_position] = list_index


def valid_rewire(
    new_first: tuple[int, int],
    new_second: tuple[int, int],
    edge_set: set[tuple[int, int]],
    old_first: tuple[int, int],
    old_second: tuple[int, int],
) -> bool:
    if new_first[0] == new_first[1] or new_second[0] == new_second[1]:
        return False
    if new_first == new_second:
        return False
    remaining = edge_set - {old_first, old_second}
    return new_first not in remaining and new_second not in remaining


def main() -> None:
    args = parse_args()
    if (
        not args.original_edges.exists()
        or not args.starting_edges.exists()
        or not args.node_map.exists()
    ):
        raise FileNotFoundError(
            "Original edges, starting edges, and the full node map are required"
        )

    original_frame = pd.read_csv(args.original_edges)
    starting_frame = pd.read_csv(args.starting_edges)
    node_map_frame = pd.read_csv(args.node_map)
    original_list = canonical_edges(original_frame)
    edges = canonical_edges(starting_frame)
    original_set = set(original_list)
    edge_set = set(edges)
    if len(original_list) != len(original_set):
        raise ValueError("Original graph has duplicate undirected edges")
    if len(edges) != len(edge_set):
        raise ValueError("Starting shuffled graph has duplicate undirected edges")
    if any(source == target for source, target in original_list + edges):
        raise ValueError("Input graph contains self-loops")
    if len(edges) != len(original_list):
        raise ValueError("Starting graph edge count differs from original graph")

    max_index = max(max(source, target) for source, target in original_list + edges)
    n_nodes = max_index + 1
    genes = gene_index_mapping(
        [node_map_frame, original_frame, starting_frame], n_nodes
    )
    original_degree = degree_sequence(original_list, n_nodes)
    starting_degree = degree_sequence(edges, n_nodes)
    if not np.array_equal(original_degree, starting_degree):
        raise ValueError("Starting shuffled graph does not preserve degree sequence")

    overlap_positions = [
        position for position, edge in enumerate(edges) if edge in original_set
    ]
    overlap_position_index = {
        position: list_index
        for list_index, position in enumerate(overlap_positions)
    }
    starting_overlap = len(overlap_positions)
    rng = np.random.default_rng(args.seed)
    attempts = 0
    accepted = 0
    improving_accepted = 0
    neutral_accepted = 0
    attempts_without_improvement = 0

    while (
        overlap_positions
        and attempts < args.max_attempts
        and attempts_without_improvement < args.patience
    ):
        attempts += 1
        first_position = overlap_positions[
            int(rng.integers(0, len(overlap_positions)))
        ]
        second_position = int(rng.integers(0, len(edges)))
        if first_position == second_position:
            continue
        old_first = edges[first_position]
        old_second = edges[second_position]
        a, b = old_first
        c, d = old_second
        candidates = [
            (canonical_pair(a, c), canonical_pair(b, d)),
            (canonical_pair(a, d), canonical_pair(b, c)),
        ]
        rng.shuffle(candidates)
        old_overlap = int(old_first in original_set) + int(old_second in original_set)
        selected: tuple[tuple[int, int], tuple[int, int]] | None = None
        selected_overlap = old_overlap
        for new_first, new_second in candidates:
            if not valid_rewire(
                new_first, new_second, edge_set, old_first, old_second
            ):
                continue
            new_overlap = int(new_first in original_set) + int(
                new_second in original_set
            )
            if new_overlap < selected_overlap:
                selected = (new_first, new_second)
                selected_overlap = new_overlap
            elif (
                selected is None
                and new_overlap == old_overlap
                and attempts_without_improvement > args.patience // 10
                and rng.random() < args.neutral_probability
            ):
                selected = (new_first, new_second)
                selected_overlap = new_overlap
        if selected is None:
            attempts_without_improvement += 1
            continue

        new_first, new_second = selected
        edge_set.remove(old_first)
        edge_set.remove(old_second)
        edge_set.add(new_first)
        edge_set.add(new_second)
        edges[first_position] = new_first
        edges[second_position] = new_second
        replace_overlap_position(
            overlap_positions,
            overlap_position_index,
            first_position,
            new_first in original_set,
        )
        replace_overlap_position(
            overlap_positions,
            overlap_position_index,
            second_position,
            new_second in original_set,
        )
        accepted += 1
        if selected_overlap < old_overlap:
            improving_accepted += 1
            attempts_without_improvement = 0
        else:
            neutral_accepted += 1
            attempts_without_improvement += 1

    final_edges = sorted(edge_set)
    final_degree = degree_sequence(final_edges, n_nodes)
    final_overlap = len(original_set & edge_set)
    final_overlap_fraction = final_overlap / len(original_set)
    degree_preserved = bool(np.array_equal(original_degree, final_degree))
    zero_overlap = final_overlap == 0
    no_duplicates = len(final_edges) == len(set(final_edges))
    no_self_loops = not any(source == target for source, target in final_edges)
    safe_for_training = (
        len(final_edges) == len(original_set)
        and degree_preserved
        and no_duplicates
        and no_self_loops
        and final_overlap < starting_overlap
    )

    output = pd.DataFrame(final_edges, columns=["source_idx", "target_idx"])
    output.insert(0, "target", [genes[index] for index in output["target_idx"]])
    output.insert(0, "source", [genes[index] for index in output["source_idx"]])
    output["support"] = "strict_degree_preserving_overlap_reducing_swap"
    output["string_score"] = np.nan
    output["wgcna_tom"] = np.nan
    args.edge_out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.edge_out, index=False)

    diagnostics = pd.DataFrame(
        [
            ("seed", args.seed, "Fixed deterministic generation seed."),
            ("n_nodes_indexed", n_nodes, "Node indices span the model feature space."),
            ("original_edge_count", len(original_set), "Simple undirected edges."),
            ("starting_edge_count", len(edges), "Current shuffled graph edge count."),
            ("final_edge_count", len(final_edges), "Strict shuffled graph edge count."),
            (
                "starting_overlap_count",
                starting_overlap,
                "Current shuffled edges also present in the original graph.",
            ),
            (
                "starting_overlap_fraction",
                starting_overlap / len(original_set),
                "Starting overlap divided by original edge count.",
            ),
            (
                "final_overlap_count",
                final_overlap,
                "Strict shuffled edges also present in the original graph.",
            ),
            (
                "final_overlap_fraction",
                final_overlap_fraction,
                "Final overlap divided by original edge count.",
            ),
            ("swaps_attempted", attempts, "Candidate double-edge swaps examined."),
            ("swaps_accepted", accepted, "Valid accepted double-edge swaps."),
            (
                "improving_swaps_accepted",
                improving_accepted,
                "Accepted swaps that reduced original-edge overlap.",
            ),
            (
                "neutral_swaps_accepted",
                neutral_accepted,
                "Accepted neutral swaps used only after a stall.",
            ),
            (
                "degree_sequence_exactly_preserved",
                degree_preserved,
                "Compared node-by-node with the original graph.",
            ),
            ("zero_overlap_achieved", zero_overlap, "Final overlap count equals zero."),
            ("no_self_loops", no_self_loops, "Required simple-graph invariant."),
            (
                "no_duplicate_undirected_edges",
                no_duplicates,
                "Required simple-graph invariant.",
            ),
            (
                "safe_for_training",
                safe_for_training,
                "Structural invariants pass and overlap improved.",
            ),
        ],
        columns=["metric", "value", "notes"],
    )
    diagnostics.to_csv(args.diagnostics_out, index=False)

    recommendation = (
        "Use the strict shuffled graph for future approval-gated training."
        if safe_for_training
        else (
            "Keep the existing shuffled graph and label it conservative; the strict "
            "generation did not satisfy all training-readiness conditions."
        )
    )
    overlap_label = (
        "Zero original-edge overlap was achieved."
        if zero_overlap
        else (
            f"Zero overlap was not reached. The result is a low-overlap graph with "
            f"{final_overlap} retained original edges "
            f"({final_overlap_fraction:.4%})."
        )
    )
    lines = [
        "# Strict Shuffled Graph Edge Generation v1",
        "",
        "## Original graph summary",
        "",
        f"- Source: `{args.original_edges}`",
        f"- Indexed nodes: {n_nodes}",
        f"- Undirected edges: {len(original_set):,}",
        "- Self-loops: 0",
        "- Duplicate undirected edges: 0",
        "",
        "## Current shuffled graph summary",
        "",
        f"- Source: `{args.starting_edges}`",
        f"- Edges: {len(edges):,}",
        f"- Starting original-edge overlap: {starting_overlap:,} "
        f"({starting_overlap / len(original_set):.4%})",
        "- Degree sequence matches the original graph exactly.",
        "",
        "## Strict shuffled generation method",
        "",
        "- Graphs were treated as simple undirected graphs using canonical sorted edge pairs.",
        "- Each move was a degree-preserving double-edge swap.",
        "- Self-loops and duplicate edges were rejected.",
        "- Overlap-increasing swaps were rejected.",
        "- Overlap-reducing swaps were preferred; occasional neutral swaps were available after stalls.",
        f"- Fixed seed: `{args.seed}`",
        f"- Swap attempts: {attempts:,}",
        f"- Accepted swaps: {accepted:,}",
        "",
        "## Degree preservation result",
        "",
        f"- Exact node-wise degree preservation: `{degree_preserved}`",
        f"- Final edge count: {len(final_edges):,}",
        f"- Self-loops: {0 if no_self_loops else 'present'}",
        f"- Duplicate undirected edges: {0 if no_duplicates else 'present'}",
        "",
        "## Original-edge overlap before and after",
        "",
        f"- Before: {starting_overlap:,} "
        f"({starting_overlap / len(original_set):.4%})",
        f"- After: {final_overlap:,} ({final_overlap_fraction:.4%})",
        "",
        "## Zero-overlap result",
        "",
        overlap_label,
        "",
        "## Recommendation",
        "",
        recommendation,
        "",
        f"- Training readiness: `{safe_for_training}`",
        f"- Output: `{args.edge_out}`",
        "",
        "## Boundary",
        "",
        "- The existing `shuffled_graph_edges_v1.csv` was not overwritten.",
        "- This generation script ran no model training.",
        "- A previously approved Stage A attempt was stopped before producing a completed checkpoint or history CSV; its partial log remains untouched.",
        "- No external validation was run.",
        "- Evidence levels and the strict Level-2 gliosis criterion are unchanged.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")

    print(diagnostics.to_string(index=False))
    print(f"Wrote {args.edge_out}")
    print(f"Wrote {args.diagnostics_out}")
    print(f"Wrote {args.report}")
    if not safe_for_training:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
