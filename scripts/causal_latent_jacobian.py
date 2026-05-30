from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch.func import jacrev, vmap
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.gene_sets import module_indices
from sea_ad_jepa.jepa import GeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def load_jepa(checkpoint_path: str, device: torch.device) -> tuple[GeneJEPA, dict]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    args = checkpoint.get("args", {})
    model = GeneJEPA(
        input_dim=int(checkpoint["n_genes"]),
        hidden_dim=int(args.get("hidden_dim", 512)),
        latent_dim=int(args.get("latent_dim", 128)),
        ema_decay=float(args.get("ema_decay", 0.996)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, checkpoint


def sample_rows(n_rows: int, max_cells: int, seed: int) -> np.ndarray:
    if max_cells <= 0 or max_cells >= n_rows:
        return np.arange(n_rows, dtype=np.int64)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n_rows, size=max_cells, replace=False))


def compute_latents(model: GeneJEPA, x_np: np.ndarray, device: torch.device, batch_size: int) -> np.ndarray:
    loader = DataLoader(TensorDataset(torch.from_numpy(x_np)), batch_size=batch_size, shuffle=False)
    chunks = []
    with torch.no_grad():
        for (batch,) in loader:
            z = model.context_encoder(batch.to(device))
            chunks.append(z.cpu().numpy())
    return np.vstack(chunks).astype(np.float32)


def compute_mean_jacobian(model: GeneJEPA, z_np: np.ndarray, device: torch.device, batch_size: int) -> np.ndarray:
    def predictor_single(z_single: torch.Tensor) -> torch.Tensor:
        return model.predictor(z_single.unsqueeze(0)).squeeze(0)

    jac_single = jacrev(predictor_single)
    jac_batch = vmap(jac_single)
    loader = DataLoader(TensorDataset(torch.from_numpy(z_np)), batch_size=batch_size, shuffle=False)
    jac_sum = None
    n_seen = 0
    for (batch,) in loader:
        batch = batch.to(device)
        jac = jac_batch(batch).detach().cpu().numpy().astype(np.float32)
        # jac shape: cells x target_dim x source_dim
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


def annotate_latents(z_np: np.ndarray, score_df: pd.DataFrame, top_k: int) -> pd.DataFrame:
    rows = []
    for latent_idx in range(z_np.shape[1]):
        z = z_np[:, latent_idx]
        for module_name in score_df.columns:
            value = corr(z, score_df[module_name].to_numpy(dtype=np.float32))
            if np.isfinite(value):
                rows.append(
                    {
                        "latent_dim": latent_idx,
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


def edge_table(jac: np.ndarray, latent_annotations: pd.DataFrame, top_edges: int) -> pd.DataFrame:
    best_annotation = {}
    if not latent_annotations.empty:
        ranked = latent_annotations.sort_values(["latent_dim", "abs_correlation"], ascending=[True, False])
        for latent_dim, group in ranked.groupby("latent_dim"):
            row = group.iloc[0]
            best_annotation[int(latent_dim)] = f"{row['module']} ({row['correlation']:+.2f})"

    rows = []
    n_target, n_source = jac.shape
    for target_dim in range(n_target):
        for source_dim in range(n_source):
            if target_dim == source_dim:
                continue
            value = float(jac[target_dim, source_dim])
            rows.append(
                {
                    "source_latent_dim": source_dim,
                    "target_latent_dim": target_dim,
                    "mean_jacobian": value,
                    "abs_mean_jacobian": abs(value),
                    "source_annotation": best_annotation.get(source_dim, ""),
                    "target_annotation": best_annotation.get(target_dim, ""),
                }
            )
    return pd.DataFrame(rows).sort_values("abs_mean_jacobian", ascending=False).head(top_edges)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract directed latent-state sensitivities from the JEPA predictor Jacobian.")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--max-cells", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--jacobian-batch-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--top-edges", type=int, default=500)
    parser.add_argument("--top-module-annotations", type=int, default=3)
    parser.add_argument("--matrix-out", default="results/tables/latent_jacobian_matrix.csv")
    parser.add_argument("--edges-out", default="results/tables/latent_jacobian_top_edges.csv")
    parser.add_argument("--annotations-out", default="results/tables/latent_module_annotations.csv")
    args = parser.parse_args()

    device = choose_device(args.device)
    adata = ad.read_h5ad(args.h5ad)
    rows = sample_rows(adata.n_obs, args.max_cells, args.seed)
    x_np = to_dense_float32(adata.X[rows])
    gene_names = adata.var_names.astype(str).tolist()
    modules = module_indices(gene_names, min_genes=2)

    model, checkpoint = load_jepa(args.checkpoint, device)
    if int(checkpoint["n_genes"]) != x_np.shape[1]:
        raise ValueError(f"Checkpoint expects {checkpoint['n_genes']} genes but AnnData has {x_np.shape[1]} genes.")

    print(f"Sampled {x_np.shape[0]:,} cells x {x_np.shape[1]:,} genes")
    z_np = compute_latents(model, x_np, device, args.batch_size)
    print(f"Computed latents: {z_np.shape[0]:,} cells x {z_np.shape[1]:,} dims")
    jac = compute_mean_jacobian(model, z_np, device, args.jacobian_batch_size)
    print(f"Computed mean predictor Jacobian: {jac.shape[0]} x {jac.shape[1]}")

    scores = module_scores(x_np, modules)
    annotations = annotate_latents(z_np, scores, args.top_module_annotations)
    edges = edge_table(jac, annotations, args.top_edges)
    matrix = pd.DataFrame(
        jac,
        index=[f"target_z_{i}" for i in range(jac.shape[0])],
        columns=[f"source_z_{i}" for i in range(jac.shape[1])],
    )

    for path_str, df in [
        (args.matrix_out, matrix),
        (args.edges_out, edges),
        (args.annotations_out, annotations),
    ]:
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=True if df is matrix else False)
        print(f"Wrote {path}")

    if not edges.empty:
        print(edges.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
