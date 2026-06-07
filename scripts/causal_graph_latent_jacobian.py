from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch.func import jacrev, vmap
from torch.utils.data import DataLoader, TensorDataset
from torch_geometric.loader import DataLoader as GraphDataLoader

from sea_ad_jepa.gene_sets import module_indices
from sea_ad_jepa.graph_data import GraphExpressionDataset, load_consensus_edge_index, node_annotation_tensor
from sea_ad_jepa.graph_jepa import GraphGeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def sample_rows(n_rows: int, max_cells: int, seed: int) -> np.ndarray:
    if max_cells <= 0 or max_cells >= n_rows:
        return np.arange(n_rows, dtype=np.int64)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n_rows, size=max_cells, replace=False))


def load_graph_model(checkpoint_path: str, adata: ad.AnnData, edge_csv: str, annotation_csv: str, device: torch.device):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    args = checkpoint.get("args", {})
    gene_names = adata.var_names.astype(str).tolist()
    use_annotations = bool(args.get("use_node_annotations", False))
    node_annotations = node_annotation_tensor(annotation_csv, gene_names) if use_annotations else None
    node_feature_dim = 1 + (int(node_annotations.shape[1]) if node_annotations is not None else 0)
    model = GraphGeneJEPA(
        n_genes=adata.n_vars,
        node_feature_dim=node_feature_dim,
        gene_embed_dim=int(args.get("gene_embed_dim", 32)),
        hidden_dim=int(args.get("hidden_dim", 128)),
        latent_dim=int(args.get("latent_dim", 128)),
        n_layers=int(args.get("n_layers", 2)),
        dropout=float(args.get("dropout", 0.1)),
        conv=str(args.get("conv", "sage")),
        ema_decay=float(args.get("ema_decay", 0.996)),
        use_projection_head=bool(args.get("use_projection_head", False)),
        projection_hidden_dim=int(args.get("projection_hidden_dim", 0)) or None,
    ).to(device)
    model.load_state_dict(checkpoint["model_state"], strict=False)
    model.eval()
    return model, checkpoint, node_annotations


def compute_latents(
    model: GraphGeneJEPA,
    matrix,
    edge_index: torch.Tensor,
    node_annotations: torch.Tensor | None,
    embedding_space: str,
    device: torch.device,
    batch_size: int,
    seed: int,
) -> np.ndarray:
    dataset = GraphExpressionDataset(
        matrix,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=0.0,
        seed=seed,
        return_pyg_data=True,
    )
    loader = GraphDataLoader(dataset, batch_size=batch_size, shuffle=False)
    chunks = []
    with torch.no_grad():
        for _, target in loader:
            target = target.to(device)
            chunks.append(model.encode_raw(target, space=embedding_space).cpu().numpy())
    return np.vstack(chunks).astype(np.float32)


def compute_mean_jacobian(model: GraphGeneJEPA, z_np: np.ndarray, device: torch.device, batch_size: int) -> np.ndarray:
    def predictor_single(z_single: torch.Tensor) -> torch.Tensor:
        return model.predictor(z_single.unsqueeze(0)).squeeze(0)

    jac_single = jacrev(predictor_single)
    jac_batch = vmap(jac_single)
    loader = DataLoader(TensorDataset(torch.from_numpy(z_np)), batch_size=batch_size, shuffle=False)
    jac_sum = None
    n_seen = 0
    for (batch,) in loader:
        jac = jac_batch(batch.to(device)).detach().cpu().numpy().astype(np.float32)
        batch_sum = jac.sum(axis=0)
        jac_sum = batch_sum if jac_sum is None else jac_sum + batch_sum
        n_seen += jac.shape[0]
    if jac_sum is None or n_seen == 0:
        raise ValueError("No cells available for Jacobian computation.")
    return jac_sum / float(n_seen)


def module_scores(x_np: np.ndarray, modules: dict[str, list[int]]) -> pd.DataFrame:
    scores = {}
    for module_name, idx in modules.items():
        if idx:
            scores[module_name] = x_np[:, idx].mean(axis=1)
    return pd.DataFrame(scores)


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    a_centered = a - float(np.mean(a))
    b_centered = b - float(np.mean(b))
    denom = float(np.sqrt(np.sum(a_centered**2) * np.sum(b_centered**2)))
    if denom == 0:
        return float("nan")
    return float(np.sum(a_centered * b_centered) / denom)


def annotate_latents(z_np: np.ndarray, score_df: pd.DataFrame, model_label: str, top_k: int) -> pd.DataFrame:
    rows = []
    for latent_idx in range(z_np.shape[1]):
        z = z_np[:, latent_idx]
        for module_name in score_df.columns:
            value = corr(z, score_df[module_name].to_numpy(dtype=np.float32))
            if np.isfinite(value):
                rows.append(
                    {
                        "model": model_label,
                        "latent_dim": latent_idx,
                        "latent_factor": f"z_{latent_idx}",
                        "module": module_name,
                        "correlation": value,
                        "abs_correlation": abs(value),
                    }
                )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return (
        df.sort_values(["latent_dim", "abs_correlation"], ascending=[True, False])
        .groupby("latent_dim", as_index=False)
        .head(top_k)
        .sort_values(["latent_dim", "abs_correlation"], ascending=[True, False])
    )


def edge_table(jac: np.ndarray, annotations: pd.DataFrame, model_label: str, top_edges: int) -> pd.DataFrame:
    best_annotation = {}
    if not annotations.empty:
        ranked = annotations.sort_values(["latent_dim", "abs_correlation"], ascending=[True, False])
        for latent_dim, group in ranked.groupby("latent_dim"):
            row = group.iloc[0]
            best_annotation[int(latent_dim)] = f"{row['module']} ({row['correlation']:+.2f})"

    rows = []
    for target_dim in range(jac.shape[0]):
        for source_dim in range(jac.shape[1]):
            if target_dim == source_dim:
                continue
            value = float(jac[target_dim, source_dim])
            rows.append(
                {
                    "model": model_label,
                    "source_latent_dim": source_dim,
                    "source_latent_factor": f"z_{source_dim}",
                    "target_latent_dim": target_dim,
                    "target_latent_factor": f"z_{target_dim}",
                    "mean_jacobian": value,
                    "abs_mean_jacobian": abs(value),
                    "source_annotation": best_annotation.get(source_dim, ""),
                    "target_annotation": best_annotation.get(target_dim, ""),
                }
            )
    return pd.DataFrame(rows).sort_values("abs_mean_jacobian", ascending=False).head(top_edges)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Graph-JEPA predictor Jacobian latent sensitivities.")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--embedding-space", choices=["auto", "encoder", "projector"], default="auto")
    parser.add_argument("--max-cells", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--jacobian-batch-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--top-edges", type=int, default=500)
    parser.add_argument("--top-module-annotations", type=int, default=3)
    parser.add_argument("--matrix-out", required=True)
    parser.add_argument("--edges-out", required=True)
    parser.add_argument("--annotations-out", required=True)
    args = parser.parse_args()

    device = choose_device(args.device)
    adata_all = ad.read_h5ad(args.h5ad)
    rows = sample_rows(adata_all.n_obs, args.max_cells, args.seed)
    adata = adata_all[rows].copy()
    gene_names = adata.var_names.astype(str).tolist()
    edge_index = load_consensus_edge_index(args.edge_csv)
    model, checkpoint, node_annotations = load_graph_model(args.checkpoint, adata, args.edge_csv, args.annotation_csv, device)
    model_args = checkpoint.get("args", {})
    embedding_space = args.embedding_space
    if embedding_space == "auto":
        embedding_space = "projector" if bool(model_args.get("use_projection_head", False)) else "encoder"

    x_np = to_dense_float32(adata.X)
    modules = module_indices(gene_names, min_genes=2)
    print(f"Sampled {x_np.shape[0]:,} cells x {x_np.shape[1]:,} genes for {args.model_label}")
    z_np = compute_latents(
        model, adata.X, edge_index, node_annotations, embedding_space, device, args.batch_size, args.seed
    )
    print(f"Computed latents: {z_np.shape[0]:,} x {z_np.shape[1]:,} using {embedding_space}")
    jac = compute_mean_jacobian(model, z_np, device, args.jacobian_batch_size)
    print(f"Computed mean predictor Jacobian: {jac.shape[0]} x {jac.shape[1]}")

    annotations = annotate_latents(z_np, module_scores(x_np, modules), args.model_label, args.top_module_annotations)
    edges = edge_table(jac, annotations, args.model_label, args.top_edges)
    matrix = pd.DataFrame(
        jac,
        index=[f"target_z_{i}" for i in range(jac.shape[0])],
        columns=[f"source_z_{i}" for i in range(jac.shape[1])],
    )
    matrix.insert(0, "model", args.model_label)
    for path_str, df in [
        (args.matrix_out, matrix),
        (args.edges_out, edges),
        (args.annotations_out, annotations),
    ]:
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"Wrote {path}")
    print(edges.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
