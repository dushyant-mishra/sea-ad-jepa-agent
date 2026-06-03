from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import h5py
import numpy as np
import pandas as pd
import torch
from scipy import sparse


DEFAULT_NODE_ANNOTATION_COLS = (
    "is_hpa_fda_drug_target",
    "is_hpa_predicted_secreted",
    "is_hpa_predicted_membrane",
)


def decode_array(values) -> list[str]:
    return [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in values]


def read_h5ad_var_names(path: str | Path) -> list[str]:
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


def load_consensus_edge_index(
    edge_csv: str | Path,
    make_undirected: bool = True,
    add_self_loops: bool = True,
) -> torch.Tensor:
    """Load consensus gene graph edges as a PyTorch Geometric edge_index tensor."""

    edges = pd.read_csv(edge_csv)
    required = {"source_idx", "target_idx"}
    missing = required - set(edges.columns)
    if missing:
        raise KeyError(f"{edge_csv} is missing required columns: {sorted(missing)}")

    source = edges["source_idx"].to_numpy(dtype=np.int64)
    target = edges["target_idx"].to_numpy(dtype=np.int64)
    if make_undirected:
        row = np.concatenate([source, target])
        col = np.concatenate([target, source])
    else:
        row, col = source, target

    if add_self_loops:
        n_nodes = int(max(row.max(initial=0), col.max(initial=0))) + 1
        loops = np.arange(n_nodes, dtype=np.int64)
        row = np.concatenate([row, loops])
        col = np.concatenate([col, loops])

    return torch.as_tensor(np.stack([row, col], axis=0), dtype=torch.long)


def load_node_annotations(
    annotation_csv: str | Path,
    genes: Sequence[str],
    annotation_cols: Sequence[str] = DEFAULT_NODE_ANNOTATION_COLS,
) -> pd.DataFrame:
    """Return annotation table in exact model gene order."""

    annotations = pd.read_csv(annotation_csv)
    if "gene" not in annotations.columns:
        raise KeyError(f"{annotation_csv} must contain a 'gene' column")

    annotations = annotations.copy()
    annotations["gene_upper"] = annotations["gene"].astype(str).str.upper()
    rows = pd.DataFrame({"gene": list(genes)})
    rows["gene_upper"] = rows["gene"].astype(str).str.upper()
    rows = rows.merge(annotations, on="gene_upper", how="left", suffixes=("", "_annotation"))

    for col in annotation_cols:
        if col not in rows:
            rows[col] = 0
        rows[col] = rows[col].fillna(0).astype(np.float32)
    return rows[["gene", *annotation_cols]]


def node_annotation_tensor(
    annotation_csv: str | Path,
    genes: Sequence[str],
    annotation_cols: Sequence[str] = DEFAULT_NODE_ANNOTATION_COLS,
) -> torch.Tensor:
    rows = load_node_annotations(annotation_csv, genes, annotation_cols)
    return torch.as_tensor(rows[list(annotation_cols)].to_numpy(dtype=np.float32), dtype=torch.float32)


@dataclass(frozen=True)
class GraphSample:
    x: torch.Tensor
    edge_index: torch.Tensor
    node_id: torch.Tensor
    obs_index: int


class GraphExpressionDataset:
    """Per-cell gene-graph samples for Graph-JEPA v2.

    Each sample is one cell represented as a graph with fixed gene nodes and fixed
    STRING/WGCNA edges. Node features are:

    [expression_value, optional translational/node annotations]

    Gene identity is intentionally *not* encoded here as a one-hot vector. The
    Graph-JEPA encoder should add a learnable gene embedding using `node_id`, so
    the network knows which gene is sending or receiving a message.
    """

    def __init__(
        self,
        matrix,
        edge_index: torch.Tensor,
        node_annotations: torch.Tensor | None = None,
        mask_fraction: float = 0.35,
        seed: int = 7,
        return_pyg_data: bool = True,
    ):
        if sparse.issparse(matrix):
            matrix = matrix.tocsr()
        else:
            matrix = np.asarray(matrix, dtype=np.float32)
        self.matrix = matrix
        self.edge_index = edge_index
        self.node_annotations = node_annotations
        self.mask_fraction = mask_fraction
        self.rng = np.random.default_rng(seed)
        self.return_pyg_data = return_pyg_data
        self.n_genes = matrix.shape[1]
        self.node_id = torch.arange(self.n_genes, dtype=torch.long)

        if node_annotations is not None and node_annotations.shape[0] != self.n_genes:
            raise ValueError("node_annotations must have one row per gene")

    def __len__(self) -> int:
        return int(self.matrix.shape[0])

    def __getitem__(self, index: int):
        target_expr = self._row(index)
        context_expr = target_expr.copy()
        mask_idx = self._choose_mask()
        context_expr[mask_idx] = 0.0

        context = self._make_sample(context_expr, index)
        target = self._make_sample(target_expr, index)
        return context, target

    def _row(self, index: int) -> np.ndarray:
        if sparse.issparse(self.matrix):
            return self.matrix[index].toarray().ravel().astype(np.float32, copy=True)
        return np.asarray(self.matrix[index], dtype=np.float32).copy()

    def _choose_mask(self) -> np.ndarray:
        n_mask = max(1, int(self.n_genes * self.mask_fraction))
        return self.rng.choice(self.n_genes, size=n_mask, replace=False)

    def _make_sample(self, expression: np.ndarray, index: int):
        expr = torch.as_tensor(expression[:, None], dtype=torch.float32)
        if self.node_annotations is not None:
            x = torch.cat([expr, self.node_annotations], dim=1)
        else:
            x = expr

        if not self.return_pyg_data:
            return GraphSample(x=x, edge_index=self.edge_index, node_id=self.node_id, obs_index=index)

        try:
            from torch_geometric.data import Data
        except ImportError as exc:
            raise ImportError("Install torch-geometric to return PyG Data objects") from exc

        return Data(
            x=x,
            edge_index=self.edge_index,
            node_id=self.node_id,
            obs_index=torch.tensor([index], dtype=torch.long),
        )
