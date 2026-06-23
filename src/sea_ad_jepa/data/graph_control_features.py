from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES


@dataclass(frozen=True)
class GraphAsset:
    condition: str
    path: Path
    genes: list[str]
    adjacency: sparse.csr_matrix
    edge_count: int
    self_loop_count: int
    notes: str


def canonical_genes(identity_edges_path: Path) -> list[str]:
    identity = pd.read_csv(identity_edges_path)
    required = {"source", "source_idx"}
    if not required.issubset(identity.columns):
        raise ValueError(f"{identity_edges_path} lacks {sorted(required)}")
    nodes = (
        identity[["source", "source_idx"]]
        .drop_duplicates("source_idx")
        .sort_values("source_idx")
    )
    expected = np.arange(len(nodes))
    if not np.array_equal(nodes["source_idx"].to_numpy(dtype=int), expected):
        raise ValueError("Canonical graph node indices are not contiguous from zero")
    return nodes["source"].astype(str).tolist()


def load_graph_asset(
    condition: str,
    path: Path,
    canonical: list[str],
) -> GraphAsset:
    edges = pd.read_csv(path)
    required = {"source_idx", "target_idx"}
    if not required.issubset(edges.columns):
        raise ValueError(f"{path} lacks {sorted(required)}")
    src = edges["source_idx"].to_numpy(dtype=int)
    dst = edges["target_idx"].to_numpy(dtype=int)
    n = len(canonical)
    if len(src) == 0 or src.min() < 0 or dst.min() < 0 or src.max() >= n or dst.max() >= n:
        raise ValueError(f"{path} contains invalid graph node indices")
    self_loops = int(np.sum(src == dst))
    if condition == "v3_no_graph":
        rows = src
        cols = dst
    else:
        rows = np.concatenate([src, dst])
        cols = np.concatenate([dst, src])
    values = np.ones(len(rows), dtype=np.float64)
    adjacency = sparse.coo_matrix((values, (rows, cols)), shape=(n, n)).tocsr()
    adjacency.data[:] = 1.0
    adjacency.eliminate_zeros()
    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    isolated = degree == 0
    if isolated.any():
        adjacency = adjacency + sparse.diags(isolated.astype(float))
        degree = np.asarray(adjacency.sum(axis=1)).ravel()
    normalized = sparse.diags(1.0 / degree) @ adjacency
    return GraphAsset(
        condition=condition,
        path=path,
        genes=canonical,
        adjacency=normalized.tocsr(),
        edge_count=int(len(edges)),
        self_loop_count=self_loops,
        notes="row-normalized one-hop adjacency; undirected symmetrization except identity control",
    )


def graph_smoothed_expression(
    expression: pd.DataFrame,
    asset: GraphAsset,
    alpha: float,
) -> pd.DataFrame:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    out = expression.copy()
    graph_cols = [gene for gene in asset.genes if gene in expression.columns]
    if len(graph_cols) != len(asset.genes):
        missing = [gene for gene in asset.genes if gene not in expression.columns]
        if missing:
            out = out.copy()
            for gene in missing:
                out[gene] = 0.0
        graph_cols = asset.genes
    x = out.loc[:, graph_cols].to_numpy(dtype=float)
    neighbor = x @ asset.adjacency.T
    smoothed = (1.0 - alpha) * x + alpha * neighbor
    out.loc[:, graph_cols] = np.asarray(smoothed)
    return out


def predefined_module_features(expression: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    gene_to_col = {str(col).upper(): col for col in expression.columns}
    features: dict[str, pd.Series] = {}
    overlaps: dict[str, int] = {}
    for module_name, genes in MICROGLIA_GENE_MODULES.items():
        cols = [gene_to_col[str(gene).upper()] for gene in genes if str(gene).upper() in gene_to_col]
        if len(cols) >= 2:
            features[f"module_{module_name}"] = expression[cols].mean(axis=1)
            overlaps[module_name] = len(cols)
    if not features:
        raise ValueError("No predefined microglia modules overlap expression")
    return pd.DataFrame(features, index=expression.index), overlaps

