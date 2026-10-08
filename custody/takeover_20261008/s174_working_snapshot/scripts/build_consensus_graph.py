from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import connected_components


def decode_array(values) -> list[str]:
    return [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in values]


def read_h5ad_var_names(path: Path) -> list[str]:
    with h5py.File(path, "r") as h5:
        var = h5["var"]
        index_key = var.attrs.get("_index", None)
        if isinstance(index_key, bytes):
            index_key = index_key.decode("utf-8")
        if index_key and index_key in var:
            return decode_array(var[index_key][()])
        if "_index" in var:
            return decode_array(var["_index"][()])
    raise KeyError(f"Could not read var names from {path}")


def normalize_pair(source: str, target: str) -> tuple[str, str]:
    return tuple(sorted([str(source), str(target)]))


def graph_stats(edges: pd.DataFrame, genes: list[str]) -> dict[str, object]:
    gene_to_idx = {gene: idx for idx, gene in enumerate(genes)}
    n = len(genes)
    if edges.empty:
        return {
            "n_genes": n,
            "n_edges": 0,
            "n_connected_genes": 0,
            "connected_fraction": 0.0,
            "n_isolated_genes": n,
            "n_components": n,
            "largest_component_size": 1,
            "median_degree": 0.0,
            "max_degree": 0,
            "top_hub_genes": "",
        }
    row = edges["source"].map(gene_to_idx).to_numpy(dtype=np.int64)
    col = edges["target"].map(gene_to_idx).to_numpy(dtype=np.int64)
    data = np.ones(row.shape[0] * 2, dtype=np.float32)
    adj = sparse.csr_matrix((data, (np.concatenate([row, col]), np.concatenate([col, row]))), shape=(n, n))
    degrees = np.asarray(adj.sum(axis=1)).ravel()
    n_components, labels = connected_components(adj, directed=False)
    component_sizes = np.bincount(labels, minlength=n_components)
    connected = int(np.sum(degrees > 0))
    hubs = sorted(zip(genes, degrees), key=lambda item: item[1], reverse=True)[:15]
    return {
        "n_genes": n,
        "n_edges": int(edges.shape[0]),
        "n_connected_genes": connected,
        "connected_fraction": connected / n,
        "n_isolated_genes": int(n - connected),
        "n_components": int(n_components),
        "largest_component_size": int(component_sizes.max()) if component_sizes.size else 0,
        "median_degree": float(np.median(degrees)),
        "max_degree": int(degrees.max()) if degrees.size else 0,
        "top_hub_genes": "; ".join(f"{gene}:{int(degree)}" for gene, degree in hubs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge STRING and WGCNA/TOM graphs into a v2 consensus graph.")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--string-edges", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--wgcna-edges", default="results/tables/v2_graph_wgcna_edges.csv")
    parser.add_argument("--out-prefix", default="results/tables/v2_graph_consensus")
    args = parser.parse_args()

    genes = read_h5ad_var_names(Path(args.local_h5ad))
    gene_to_idx = {gene: idx for idx, gene in enumerate(genes)}
    string_edges = pd.read_csv(args.string_edges)
    wgcna_edges = pd.read_csv(args.wgcna_edges)

    string_rows = {}
    for row in string_edges.itertuples(index=False):
        pair = normalize_pair(row.source, row.target)
        string_rows[pair] = float(row.score)

    wgcna_rows = {}
    for row in wgcna_edges.itertuples(index=False):
        pair = normalize_pair(row.source, row.target)
        wgcna_rows[pair] = float(row.weight)

    all_pairs = sorted(set(string_rows) | set(wgcna_rows))
    rows = []
    for source, target in all_pairs:
        in_string = (source, target) in string_rows
        in_wgcna = (source, target) in wgcna_rows
        if source not in gene_to_idx or target not in gene_to_idx:
            continue
        rows.append(
            {
                "source": source,
                "target": target,
                "source_idx": gene_to_idx[source],
                "target_idx": gene_to_idx[target],
                "in_string": in_string,
                "in_wgcna": in_wgcna,
                "string_score": string_rows.get((source, target), np.nan),
                "wgcna_tom": wgcna_rows.get((source, target), np.nan),
                "support": "both" if in_string and in_wgcna else ("string_only" if in_string else "wgcna_only"),
            }
        )

    consensus = pd.DataFrame(rows)
    consensus["support_rank"] = consensus["support"].map({"both": 0, "string_only": 1, "wgcna_only": 2})
    consensus = consensus.sort_values(["support_rank", "wgcna_tom", "string_score"], ascending=[True, False, False]).drop(columns=["support_rank"])
    both = consensus[consensus["support"].eq("both")].copy()
    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    consensus_path = out_prefix.parent / f"{out_prefix.name}_edges.csv"
    both_path = out_prefix.parent / f"{out_prefix.name}_both_edges.csv"
    edge_index_path = out_prefix.parent / f"{out_prefix.name}_edge_index.csv"
    stats_path = out_prefix.parent / f"{out_prefix.name}_stats.csv"

    consensus.to_csv(consensus_path, index=False)
    both.to_csv(both_path, index=False)
    consensus[["source_idx", "target_idx", "support", "string_score", "wgcna_tom"]].to_csv(edge_index_path, index=False)
    stats = pd.DataFrame(
        [
            {"graph": "consensus_union", **graph_stats(consensus, genes)},
            {"graph": "consensus_both", **graph_stats(both, genes)},
            {"graph": "string_only", **graph_stats(consensus[consensus["support"].eq("string_only")], genes)},
            {"graph": "wgcna_only", **graph_stats(consensus[consensus["support"].eq("wgcna_only")], genes)},
        ]
    )
    stats.to_csv(stats_path, index=False)
    print(f"Wrote {consensus_path}")
    print(f"Wrote {both_path}")
    print(f"Wrote {stats_path}")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
