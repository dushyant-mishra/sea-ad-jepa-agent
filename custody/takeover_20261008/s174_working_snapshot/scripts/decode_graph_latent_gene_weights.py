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

from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.graph_data import GraphExpressionDataset, load_consensus_edge_index, node_annotation_tensor
from sea_ad_jepa.graph_jepa import GraphGeneJEPA


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def sample_rows(n_rows: int, max_cells: int, seed: int) -> np.ndarray:
    if max_cells <= 0 or max_cells >= n_rows:
        return np.arange(n_rows, dtype=np.int64)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n_rows, size=max_cells, replace=False))


def module_membership(gene: str) -> str:
    hits = [name for name, genes in MICROGLIA_GENE_MODULES.items() if gene.upper() in {g.upper() for g in genes}]
    return ";".join(sorted(hits))


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
    edge_index = load_consensus_edge_index(edge_csv)
    return model, checkpoint, edge_index, node_annotations


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode Graph-JEPA latent dimensions into gene attribution rankings.")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--latent-dims", nargs="+", type=int, required=True)
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_string_edges_t700.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--embedding-space", choices=["auto", "encoder", "projector"], default="auto")
    parser.add_argument("--max-cells", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    device = choose_device(args.device)
    adata_all = ad.read_h5ad(args.h5ad)
    rows = sample_rows(adata_all.n_obs, args.max_cells, args.seed)
    adata = adata_all[rows].copy()
    gene_names = adata.var_names.astype(str).tolist()
    model, checkpoint, edge_index, node_annotations = load_graph_model(
        args.checkpoint, adata, args.edge_csv, args.annotation_csv, device
    )
    model_args = checkpoint.get("args", {})
    embedding_space = args.embedding_space
    if embedding_space == "auto":
        embedding_space = "projector" if bool(model_args.get("use_projection_head", False)) else "encoder"

    dataset = GraphExpressionDataset(
        adata.X,
        edge_index=edge_index,
        node_annotations=node_annotations,
        mask_fraction=0.0,
        seed=args.seed,
        return_pyg_data=True,
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)
    n_genes = adata.n_vars
    signed = {dim: torch.zeros(n_genes, dtype=torch.float64) for dim in args.latent_dims}
    absolute = {dim: torch.zeros(n_genes, dtype=torch.float64) for dim in args.latent_dims}
    counts = {dim: torch.zeros(n_genes, dtype=torch.float64) for dim in args.latent_dims}

    for _, target in loader:
        target = target.to(device)
        target.x.requires_grad_(True)
        z = model.encode_raw(target, space=embedding_space)
        for dim in args.latent_dims:
            model.zero_grad(set_to_none=True)
            if target.x.grad is not None:
                target.x.grad.zero_()
            score = z[:, dim].sum()
            grad = torch.autograd.grad(score, target.x, retain_graph=True)[0][:, 0].detach().cpu()
            expr = target.x.detach().cpu()[:, 0]
            attribution = grad * expr
            node_id = target.node_id.detach().cpu()
            signed[dim].index_add_(0, node_id, attribution.to(torch.float64))
            absolute[dim].index_add_(0, node_id, attribution.abs().to(torch.float64))
            counts[dim].index_add_(0, node_id, torch.ones_like(attribution, dtype=torch.float64))

    rows_out = []
    annotations = pd.read_csv(args.annotation_csv) if Path(args.annotation_csv).exists() else pd.DataFrame()
    annotation_map = {}
    if "gene" in annotations:
        annotations = annotations.copy()
        annotations["gene_upper"] = annotations["gene"].astype(str).str.upper()
        annotation_map = annotations.drop_duplicates("gene_upper").set_index("gene_upper").to_dict("index")

    for dim in args.latent_dims:
        mean_signed = (signed[dim] / counts[dim].clamp_min(1)).numpy()
        mean_abs = (absolute[dim] / counts[dim].clamp_min(1)).numpy()
        order = np.argsort(-mean_abs)
        for rank, idx in enumerate(order, start=1):
            gene = gene_names[int(idx)]
            ann = annotation_map.get(gene.upper(), {})
            rows_out.append(
                {
                    "model": args.model_label,
                    "latent_dimension": f"z_{dim}",
                    "latent_id": dim,
                    "rank": rank,
                    "gene": gene,
                    "signed_attribution": float(mean_signed[idx]),
                    "abs_attribution": float(mean_abs[idx]),
                    "module_annotations": module_membership(gene),
                    "is_hpa_fda_drug_target": int(ann.get("is_hpa_fda_drug_target", 0) or 0),
                    "is_hpa_predicted_membrane": int(ann.get("is_hpa_predicted_membrane", 0) or 0),
                    "is_hpa_predicted_secreted": int(ann.get("is_hpa_predicted_secreted", 0) or 0),
                }
            )

    out = pd.DataFrame(rows_out)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    print(out.groupby("latent_dimension").head(10).to_string(index=False))


if __name__ == "__main__":
    main()
