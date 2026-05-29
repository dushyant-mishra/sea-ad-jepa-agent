from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.jepa import GeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed cells with a trained JEPA model and aggregate by donor.")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--cell-out", default="results/tables/jepa_cell_embeddings.csv")
    parser.add_argument("--donor-out", default="results/tables/jepa_donor_embeddings.csv")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    device = choose_device(args.device)
    adata = ad.read_h5ad(args.h5ad)
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model_args = checkpoint.get("args", {})

    model = GeneJEPA(
        input_dim=int(checkpoint["n_genes"]),
        hidden_dim=int(model_args.get("hidden_dim", 512)),
        latent_dim=int(model_args.get("latent_dim", 128)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    x = torch.from_numpy(to_dense_float32(adata.X))
    loader = DataLoader(TensorDataset(x), batch_size=args.batch_size, shuffle=False)

    embeddings = []
    with torch.no_grad():
        for (batch,) in loader:
            z = model.encode(batch.to(device))
            embeddings.append(z.cpu().numpy())
    embeddings_np = np.vstack(embeddings)

    columns = [f"jepa_{i}" for i in range(embeddings_np.shape[1])]
    cell_df = pd.DataFrame(embeddings_np, columns=columns, index=adata.obs_names)
    cell_df.insert(0, args.donor_column, adata.obs[args.donor_column].astype(str).to_numpy())

    cell_out = Path(args.cell_out)
    donor_out = Path(args.donor_out)
    cell_out.parent.mkdir(parents=True, exist_ok=True)
    donor_out.parent.mkdir(parents=True, exist_ok=True)
    cell_df.to_csv(cell_out)

    donor_df = cell_df.groupby(args.donor_column)[columns].mean().reset_index()
    donor_df = donor_df.rename(columns={args.donor_column: "Donor ID"})
    donor_df.to_csv(donor_out, index=False)

    print(f"Wrote cell embeddings: {cell_out} ({cell_df.shape[0]:,} cells x {len(columns):,} dims)")
    print(f"Wrote donor embeddings: {donor_out} ({donor_df.shape[0]:,} donors x {len(columns):,} dims)")


if __name__ == "__main__":
    main()

