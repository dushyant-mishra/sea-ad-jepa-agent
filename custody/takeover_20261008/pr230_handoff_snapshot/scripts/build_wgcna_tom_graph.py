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


def standardize(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32, copy=True)
    x -= x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    std[std <= 0] = 1.0
    return x / std


def adjacency_to_tom(adjacency: np.ndarray) -> np.ndarray:
    adjacency = adjacency.astype(np.float32, copy=False)
    np.fill_diagonal(adjacency, 0.0)
    degree = adjacency.sum(axis=1)
    shared = adjacency @ adjacency
    numerator = shared + adjacency
    denominator = np.minimum(degree[:, None], degree[None, :]) + 1.0 - adjacency
    denominator[denominator <= 0] = 1.0
    tom = numerator / denominator
    np.fill_diagonal(tom, 0.0)
    return tom.astype(np.float32, copy=False)


def graph_stats(edges: pd.DataFrame, n_genes: int, genes: list[str]) -> dict[str, object]:
    if edges.empty:
        return {
            "n_genes": n_genes,
            "n_edges": 0,
            "n_connected_genes": 0,
            "connected_fraction": 0.0,
            "n_isolated_genes": n_genes,
            "n_components": n_genes,
            "largest_component_size": 1,
            "median_degree": 0.0,
            "max_degree": 0,
            "top_hub_genes": "",
        }
    row = edges["source_idx"].to_numpy(dtype=np.int64)
    col = edges["target_idx"].to_numpy(dtype=np.int64)
    data = np.ones(row.shape[0] * 2, dtype=np.float32)
    adj = sparse.csr_matrix((data, (np.concatenate([row, col]), np.concatenate([col, row]))), shape=(n_genes, n_genes))
    degrees = np.asarray(adj.sum(axis=1)).ravel()
    n_components, labels = connected_components(adj, directed=False)
    component_sizes = np.bincount(labels, minlength=n_components)
    connected = int(np.sum(degrees > 0))
    hubs = sorted(zip(genes, degrees), key=lambda item: item[1], reverse=True)[:15]
    return {
        "n_genes": n_genes,
        "n_edges": int(edges.shape[0]),
        "n_connected_genes": connected,
        "connected_fraction": connected / n_genes,
        "n_isolated_genes": int(n_genes - connected),
        "n_components": int(n_components),
        "largest_component_size": int(component_sizes.max()) if component_sizes.size else 0,
        "median_degree": float(np.median(degrees)),
        "max_degree": int(degrees.max()) if degrees.size else 0,
        "top_hub_genes": "; ".join(f"{gene}:{int(degree)}" for gene, degree in hubs),
    }


def top_edges_from_matrix(matrix: np.ndarray, genes: list[str], top_edges: int, min_weight: float) -> pd.DataFrame:
    n = matrix.shape[0]
    upper = np.triu_indices(n, k=1)
    weights = matrix[upper]
    keep = np.isfinite(weights) & (weights >= min_weight)
    upper_i = upper[0][keep]
    upper_j = upper[1][keep]
    weights = weights[keep]
    if weights.size == 0:
        return pd.DataFrame(columns=["source", "target", "weight", "source_idx", "target_idx"])
    if weights.size > top_edges:
        idx = np.argpartition(weights, -top_edges)[-top_edges:]
        upper_i = upper_i[idx]
        upper_j = upper_j[idx]
        weights = weights[idx]
    order = np.argsort(weights)[::-1]
    upper_i = upper_i[order]
    upper_j = upper_j[order]
    weights = weights[order]
    return pd.DataFrame(
        {
            "source": [genes[i] for i in upper_i],
            "target": [genes[j] for j in upper_j],
            "weight": weights,
            "source_idx": upper_i,
            "target_idx": upper_j,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a WGCNA-style TOM graph over the SEA-AD JEPA feature space.")
    parser.add_argument("--pseudobulk", default="data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--power", type=int, default=6)
    parser.add_argument("--top-edges", type=int, default=100000)
    parser.add_argument("--min-tom", type=float, default=0.0)
    parser.add_argument("--out-prefix", default="results/tables/v2_graph_wgcna")
    args = parser.parse_args()

    genes = read_h5ad_var_names(Path(args.local_h5ad))
    print(f"Loading pseudobulk matrix and subsetting to {len(genes):,} JEPA genes")
    pseudobulk = pd.read_csv(args.pseudobulk, usecols=["Donor ID", *genes])
    x = pseudobulk[genes].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
    keep_genes = np.isfinite(x).all(axis=0) & (x.std(axis=0) > 0)
    if not keep_genes.all():
        dropped = int((~keep_genes).sum())
        print(f"Dropping {dropped} zero-variance or invalid genes before TOM calculation")
    genes_kept = [gene for gene, keep in zip(genes, keep_genes) if keep]
    x = x[:, keep_genes]

    print("Computing signed correlation adjacency")
    z = standardize(x)
    corr = (z.T @ z) / max(1, z.shape[0] - 1)
    corr = np.clip(corr, -1.0, 1.0).astype(np.float32)
    adjacency = ((1.0 + corr) / 2.0) ** args.power
    np.fill_diagonal(adjacency, 0.0)

    print("Computing topological overlap matrix")
    tom = adjacency_to_tom(adjacency)
    edges = top_edges_from_matrix(tom, genes_kept, top_edges=args.top_edges, min_weight=args.min_tom)
    stats = pd.DataFrame(
        [
            {
                "graph": "WGCNA_TOM",
                "power": args.power,
                "top_edges_requested": args.top_edges,
                "min_tom": args.min_tom,
                **graph_stats(edges, len(genes_kept), genes_kept),
            }
        ]
    )

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    edges_path = out_prefix.parent / f"{out_prefix.name}_edges.csv"
    edge_index_path = out_prefix.parent / f"{out_prefix.name}_edge_index.csv"
    stats_path = out_prefix.parent / f"{out_prefix.name}_stats.csv"
    genes_path = out_prefix.parent / f"{out_prefix.name}_genes.csv"
    edges.to_csv(edges_path, index=False)
    edges[["source_idx", "target_idx", "weight"]].to_csv(edge_index_path, index=False)
    stats.to_csv(stats_path, index=False)
    pd.DataFrame({"gene_idx": range(len(genes_kept)), "gene": genes_kept}).to_csv(genes_path, index=False)
    print(f"Wrote {edges_path}")
    print(f"Wrote {stats_path}")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
