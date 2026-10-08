from __future__ import annotations

import argparse
import gzip
import urllib.request
from collections import defaultdict
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


def download_if_missing(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 0:
        return
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, out_path)


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
    row = edges["source"].map(gene_to_idx).to_numpy()
    col = edges["target"].map(gene_to_idx).to_numpy()
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
    parser = argparse.ArgumentParser(description="Build STRING prior graphs for the SEA-AD JEPA v2 feature space.")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--string-dir", default="data/external/string")
    parser.add_argument("--version", default="12.0")
    parser.add_argument("--taxon", default="9606")
    parser.add_argument("--thresholds", nargs="+", type=int, default=[400, 700, 900])
    parser.add_argument("--out-prefix", default="results/tables/v2_graph_string")
    args = parser.parse_args()

    genes = read_h5ad_var_names(Path(args.local_h5ad))
    gene_set = {gene.upper() for gene in genes}
    gene_to_original = {gene.upper(): gene for gene in genes}
    gene_to_idx = {gene: idx for idx, gene in enumerate(genes)}
    thresholds = sorted(set(args.thresholds))
    min_threshold = min(thresholds)

    string_dir = Path(args.string_dir)
    info_path = string_dir / f"{args.taxon}.protein.info.v{args.version}.txt.gz"
    links_path = string_dir / f"{args.taxon}.protein.links.v{args.version}.txt.gz"
    info_url = f"https://stringdb-downloads.org/download/protein.info.v{args.version}/{args.taxon}.protein.info.v{args.version}.txt.gz"
    links_url = f"https://stringdb-downloads.org/download/protein.links.v{args.version}/{args.taxon}.protein.links.v{args.version}.txt.gz"
    download_if_missing(info_url, info_path)
    download_if_missing(links_url, links_path)

    print("Parsing STRING protein-to-symbol mappings")
    info_header = pd.read_csv(info_path, sep="\t", nrows=0)
    protein_col = "#protein_external_id" if "#protein_external_id" in info_header.columns else "#string_protein_id"
    info = pd.read_csv(info_path, sep="\t", usecols=[protein_col, "preferred_name"])
    protein_to_gene = dict(zip(info[protein_col].astype(str), info["preferred_name"].astype(str)))

    print(f"Streaming STRING links at minimum threshold {min_threshold}")
    edge_best_score: dict[tuple[str, str], int] = {}
    with gzip.open(links_path, "rt", encoding="utf-8") as handle:
        header = handle.readline().strip().split()
        score_idx = header.index("combined_score") if "combined_score" in header else 2
        for line in handle:
            parts = line.strip().split()
            if len(parts) <= score_idx:
                continue
            score = int(parts[score_idx])
            if score < min_threshold:
                continue
            g1 = protein_to_gene.get(parts[0], "").upper()
            g2 = protein_to_gene.get(parts[1], "").upper()
            if g1 not in gene_set or g2 not in gene_set or g1 == g2:
                continue
            source, target = sorted([gene_to_original[g1], gene_to_original[g2]])
            key = (source, target)
            if score > edge_best_score.get(key, -1):
                edge_best_score[key] = score

    all_edges = pd.DataFrame(
        [(source, target, score, gene_to_idx[source], gene_to_idx[target]) for (source, target), score in edge_best_score.items()],
        columns=["source", "target", "score", "source_idx", "target_idx"],
    )
    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    stats_rows = []
    for threshold in thresholds:
        edges = all_edges[all_edges["score"] >= threshold].sort_values(["score", "source", "target"], ascending=[False, True, True])
        edge_path = out_prefix.parent / f"{out_prefix.name}_edges_t{threshold}.csv"
        edge_index_path = out_prefix.parent / f"{out_prefix.name}_edge_index_t{threshold}.csv"
        edges.to_csv(edge_path, index=False)
        edges[["source_idx", "target_idx", "score"]].to_csv(edge_index_path, index=False)
        row = {"graph": "STRING", "threshold": threshold, **graph_stats(edges, genes)}
        stats_rows.append(row)
        print(f"Threshold {threshold}: {row['n_edges']:,} edges, {row['n_connected_genes']:,}/{row['n_genes']:,} connected genes")

    stats = pd.DataFrame(stats_rows)
    stats_path = out_prefix.parent / f"{out_prefix.name}_stats.csv"
    genes_path = out_prefix.parent / f"{out_prefix.name}_genes.csv"
    stats.to_csv(stats_path, index=False)
    pd.DataFrame({"gene_idx": range(len(genes)), "gene": genes}).to_csv(genes_path, index=False)
    print(f"Wrote {stats_path}")
    print(f"Wrote {genes_path}")


if __name__ == "__main__":
    main()
