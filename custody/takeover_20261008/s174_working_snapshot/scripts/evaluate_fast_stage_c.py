from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.graph_data import load_consensus_edge_index
from sea_ad_jepa.graph_jepa import FastGraphGeneJEPA
from scripts.train_graph_jepa_stage_a_fast import choose_device, normalized_adjacency


def dense_h5ad(path: str) -> tuple[torch.Tensor, list[str], pd.DataFrame]:
    adata = ad.read_h5ad(path)
    x = adata.X
    if sparse.issparse(x):
        x = x.toarray()
    return torch.from_numpy(np.asarray(x, dtype=np.float32)), adata.var_names.astype(str).tolist(), adata.obs.copy()


def infer_fast_model(checkpoint: dict) -> FastGraphGeneJEPA:
    state = checkpoint["model_state"]
    n_genes = int(checkpoint["n_genes"])
    gene_embed_dim = int(state["context_encoder.gene_embedding.weight"].shape[1])
    hidden_dim = int(state["context_encoder.input_proj.0.weight"].shape[0])
    latent_dim = int(state["context_encoder.out.weight"].shape[0])
    n_layers = len([key for key in state if key.startswith("context_encoder.self_linears.") and key.endswith(".weight")])
    model = FastGraphGeneJEPA(
        n_genes=n_genes,
        node_feature_dim=1,
        gene_embed_dim=gene_embed_dim,
        hidden_dim=hidden_dim,
        latent_dim=latent_dim,
        n_layers=n_layers,
        dropout=0.0,
        ema_decay=1.0,
    )
    model.load_state_dict(state)
    return model


@torch.no_grad()
def extract_embeddings(
    model: FastGraphGeneJEPA,
    matrix: torch.Tensor,
    adj: torch.Tensor,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    model.eval()
    embeddings = []
    loader = DataLoader(TensorDataset(matrix), batch_size=batch_size, shuffle=False)
    for (batch,) in loader:
        z = model.context_encoder(batch.to(device), adj, node_annotations=None)
        embeddings.append(z.cpu().numpy())
    return np.concatenate(embeddings, axis=0)


def score_metrics(X: np.ndarray, y: np.ndarray, cv: int = 5) -> tuple[float, float]:
    """Returns (Ridge Spearman, Cosine kNN Spearman) for continuous targets."""
    y_scaled = StandardScaler().fit_transform(y.reshape(-1, 1)).flatten()
    kf = KFold(n_splits=cv, shuffle=True, random_state=42)

    # Linear probe (Ridge)
    ridge = RidgeCV(alphas=np.logspace(-3, 3, 10))
    ridge_preds = cross_val_predict(ridge, X, y_scaled, cv=kf)
    ridge_spearman, _ = spearmanr(y_scaled, ridge_preds)

    # Manifold probe (distance-weighted cosine kNN)
    knn = KNeighborsRegressor(n_neighbors=5, weights="distance", metric="cosine")
    knn_preds = cross_val_predict(knn, X, y_scaled, cv=kf)
    knn_spearman, _ = spearmanr(y_scaled, knn_preds)

    return float(ridge_spearman), float(knn_spearman)


def latent_geometry(embeddings: np.ndarray) -> dict[str, float]:
    """Compute effective dimensions and top singular value ratio."""
    centered = embeddings - embeddings.mean(axis=0, keepdims=True)
    svs = np.linalg.svd(centered, compute_uv=False)
    svs = svs / (svs.sum() + 1e-12)
    entropy = -np.sum(svs * np.log(svs + 1e-12))
    effective_dims = float(np.exp(entropy))
    top_sv_ratio = float(svs[0])
    return {"effective_dims": effective_dims, "top_sv_ratio": top_sv_ratio}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Fast Stage C checkpoint geometry against pathology."
    )
    parser.add_argument("--checkpoint", required=True, help="Path to Fast Stage C checkpoint.")
    parser.add_argument("--label", default=None, help="Human-readable label for this checkpoint in the output table.")
    parser.add_argument(
        "--disease-h5ad",
        default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad",
    )
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument(
        "--pathology-targets-path",
        default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv",
    )
    parser.add_argument(
        "--pathology-target-columns-path",
        default="data/processed/metadata/pathology_target_columns.csv",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=[
            "percent AT8 positive area_Grey matter",
            "percent NeuN positive area_Grey matter",
            "percent GFAP positive area_Grey matter",
            "percent Iba1 positive area_Grey matter",
            "percent 6e10 positive area_Grey matter",
        ],
    )
    parser.add_argument(
        "--out-csv",
        default="results/tables/v2_2_fast_stage_c_evaluation.csv",
    )
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    device = choose_device(args.device)
    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint_label = args.label or Path(args.checkpoint).parent.name

    print(f"Loading checkpoint: {args.checkpoint}")
    print(f"Label: {checkpoint_label}")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = infer_fast_model(checkpoint).to(device)

    print("Loading disease H5AD...")
    disease_x, gene_names, disease_obs = dense_h5ad(args.disease_h5ad)
    edge_index = load_consensus_edge_index(args.edge_csv)
    target_adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)

    print("Extracting cell-level embeddings...")
    cell_embeddings = extract_embeddings(model, disease_x, target_adj, device, args.batch_size)

    # Compute cell-level latent geometry
    geometry = latent_geometry(cell_embeddings)
    print(f"Latent geometry: effective_dims={geometry['effective_dims']:.2f}, top_sv_ratio={geometry['top_sv_ratio']:.4f}")

    # Pool to donor level
    print("Pooling to donor-level coordinates...")
    disease_obs = disease_obs.copy()
    disease_obs["Donor ID"] = normalize_donor_id(disease_obs["Donor ID"])
    donor_df = pd.DataFrame(cell_embeddings)
    donor_df["Donor ID"] = disease_obs["Donor ID"].values
    donor_embeddings_df = donor_df.groupby("Donor ID").mean()
    donors = donor_embeddings_df.index.tolist()
    donor_embeddings = donor_embeddings_df.to_numpy()

    print(f"Donors: {len(donors)}, Embedding dims: {donor_embeddings.shape[1]}")

    print("Loading pathology targets...")
    targets_df, _ = load_pathology_targets(
        args.pathology_targets_path, args.pathology_target_columns_path
    )
    targets_df["Donor ID"] = normalize_donor_id(targets_df["Donor ID"])
    targets_df = targets_df.set_index("Donor ID")

    results = []
    for target in args.targets:
        if target not in targets_df.columns:
            print(f"Warning: Target '{target}' not found in metadata. Skipping.")
            continue

        target_values = targets_df.reindex(donors)[target].values.astype(np.float64)
        valid_mask = ~np.isnan(target_values)

        if valid_mask.sum() < 10:
            print(f"Warning: Not enough valid donors for '{target}' ({valid_mask.sum()}). Skipping.")
            continue

        X_valid = donor_embeddings[valid_mask]
        y_valid = target_values[valid_mask]

        ridge_sp, knn_sp = score_metrics(X_valid, y_valid)

        results.append(
            {
                "checkpoint": checkpoint_label,
                "target": target,
                "ridge_spearman": ridge_sp,
                "cosine_knn_spearman": knn_sp,
                "valid_donors": int(valid_mask.sum()),
                "effective_dims": geometry["effective_dims"],
                "top_sv_ratio": geometry["top_sv_ratio"],
            }
        )

        print(f"  {target}")
        print(f"    Ridge Spearman:      {ridge_sp:.3f}")
        print(f"    Cosine kNN Spearman: {knn_sp:.3f}")

    results_df = pd.DataFrame(results)
    # Append to existing file if it exists, so we can build the comparison table incrementally
    if out_path.exists():
        existing = pd.read_csv(out_path)
        results_df = pd.concat([existing, results_df], ignore_index=True)
    results_df.to_csv(out_path, index=False)
    print(f"\nSaved evaluation metrics to {out_path}")


if __name__ == "__main__":
    main()
