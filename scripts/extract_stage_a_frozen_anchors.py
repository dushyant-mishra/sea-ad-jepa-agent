from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from sea_ad_jepa.graph_data import GraphExpressionDataset, load_consensus_edge_index, node_annotation_tensor
from sea_ad_jepa.graph_jepa import GraphGeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract frozen Stage A Graph-JEPA anchor coordinates.")
    parser.add_argument("--checkpoint", default="results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--anchor-type", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    device = choose_device(args.device)
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model_args = checkpoint.get("args", {})

    adata = ad.read_h5ad(args.h5ad)
    gene_names = adata.var_names.astype(str).tolist()
    if int(checkpoint["n_genes"]) != adata.n_vars:
        raise ValueError(f"Checkpoint has {checkpoint['n_genes']} genes, but {args.h5ad} has {adata.n_vars}.")

    use_node_annotations = bool(model_args.get("use_node_annotations", False))
    node_annotations = node_annotation_tensor(args.annotation_csv, gene_names) if use_node_annotations else None
    node_feature_dim = 1 + (int(node_annotations.shape[1]) if node_annotations is not None else 0)
    edge_index = load_consensus_edge_index(args.edge_csv)

    dataset = GraphExpressionDataset(
        adata.X,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=0.0,
        seed=int(model_args.get("seed", 7)),
        return_pyg_data=True,
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)

    model = GraphGeneJEPA(
        n_genes=adata.n_vars,
        node_feature_dim=node_feature_dim,
        gene_embed_dim=int(model_args.get("gene_embed_dim", 32)),
        hidden_dim=int(model_args.get("hidden_dim", 128)),
        latent_dim=int(model_args.get("latent_dim", 128)),
        n_layers=int(model_args.get("n_layers", 2)),
        dropout=float(model_args.get("dropout", 0.1)),
        conv=str(model_args.get("conv", "sage")),
        ema_decay=float(model_args.get("ema_decay", 0.996)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    latents = []
    with torch.no_grad():
        for batch in loader:
            data = batch[1] if isinstance(batch, (list, tuple)) else batch
            data = data.to(device)
            z = model.target_encoder(data)
            latents.append(z.cpu().numpy())
    z_all = np.concatenate(latents, axis=0)

    out = pd.DataFrame(z_all, columns=[f"z_{i}" for i in range(z_all.shape[1])])
    out.insert(0, "cell_id", adata.obs_names.astype(str).to_numpy())
    if "Donor ID" in adata.obs:
        donor = adata.obs["Donor ID"].astype(str).to_numpy()
    elif "donor_id" in adata.obs:
        donor = adata.obs["donor_id"].astype(str).to_numpy()
    else:
        donor = np.repeat("NA", adata.n_obs)
    out.insert(1, "donor_id", donor)
    out.insert(2, "anchor_type", args.anchor_type)

    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    print(f"cells={out.shape[0]:,} latent_dim={z_all.shape[1]} anchor_type={args.anchor_type}")


if __name__ == "__main__":
    main()
