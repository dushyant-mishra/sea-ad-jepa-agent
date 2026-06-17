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
from sklearn.neighbors import NearestNeighbors
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.data import normalize_donor_id
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.graph_data import load_consensus_edge_index
from sea_ad_jepa.graph_jepa import FastGraphGeneJEPA
from scripts.train_graph_jepa_stage_a_fast import choose_device, normalized_adjacency


def dense_h5ad(path: str) -> tuple[torch.Tensor, list[str], pd.DataFrame]:
    adata = ad.read_h5ad(path)
    x = adata.X
    if sparse.issparse(x):
        x = x.toarray()
    return torch.from_numpy(np.asarray(x, dtype=np.float32)), adata.var_names.astype(str).tolist(), adata.obs.copy()


def sample_rows_by_donor(donors: pd.Series, max_cells: int, seed: int) -> np.ndarray:
    if max_cells <= 0 or max_cells >= len(donors):
        return np.arange(len(donors), dtype=np.int64)
    rng = np.random.default_rng(seed)
    per_donor = max(1, int(np.ceil(max_cells / donors.nunique())))
    sampled = []
    for _, idx in donors.groupby(donors).indices.items():
        idx = np.asarray(idx, dtype=np.int64)
        take = min(per_donor, idx.size)
        sampled.extend(rng.choice(idx, size=take, replace=False).tolist())
    sampled = np.asarray(sorted(sampled), dtype=np.int64)
    if sampled.size > max_cells:
        sampled = np.asarray(sorted(rng.choice(sampled, size=max_cells, replace=False)), dtype=np.int64)
    return sampled


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
    for param in model.parameters():
        param.requires_grad = False
    return model


def make_head(payload: dict) -> nn.Module:
    head_kind = str(payload["head_kind"])
    latent_dim = int(payload["latent_dim"])
    n_targets = len(payload["targets"])
    if head_kind == "linear":
        head: nn.Module = nn.Linear(latent_dim, n_targets)
    elif head_kind == "mlp":
        hidden_dim = int(payload["hidden_dim"])
        dropout = float(payload["dropout"])
        head = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, n_targets),
        )
    else:
        raise ValueError(f"Unknown pathology head kind: {head_kind}")
    head.load_state_dict(payload["head_state"])
    head.eval()
    return head


@torch.no_grad()
def encode_matrix(
    model: FastGraphGeneJEPA,
    matrix: torch.Tensor,
    adj: torch.Tensor,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    chunks = []
    loader = DataLoader(TensorDataset(matrix), batch_size=batch_size, shuffle=False)
    for (batch,) in loader:
        z = model.context_encoder(batch.to(device), adj, node_annotations=None)
        chunks.append(z.cpu().numpy())
    return np.concatenate(chunks, axis=0).astype(np.float32)


def aggregate_by_donor(z: np.ndarray, donors: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame(z, columns=[f"z_{i}" for i in range(z.shape[1])])
    df.insert(0, "Donor ID", donors.astype(str).to_numpy())
    return df.groupby("Donor ID", as_index=False).mean()


@torch.no_grad()
def predict_pathology(head: nn.Module, payload: dict, donor_z: pd.DataFrame) -> pd.DataFrame:
    z_cols = [col for col in donor_z.columns if col.startswith("z_")]
    x = donor_z[z_cols].to_numpy(dtype=np.float32)
    x_scaled = (x - np.asarray(payload["x_mean"], dtype=np.float32)) / np.asarray(payload["x_scale"], dtype=np.float32)
    pred_scaled = head(torch.from_numpy(x_scaled)).cpu().numpy()
    pred = pred_scaled * np.asarray(payload["y_scale"], dtype=np.float32) + np.asarray(payload["y_mean"], dtype=np.float32)
    out = donor_z[["Donor ID"]].copy()
    for idx, target in enumerate(payload["targets"]):
        out[f"pred_{target}"] = pred[:, idx]
    return out


def build_perturbations(gene_names: list[str], mode: str, modules: list[str] | None, genes: list[str] | None, min_genes: int):
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    perturbations = []
    if mode in {"module", "both"}:
        selected_modules = modules or sorted(MICROGLIA_GENE_MODULES)
        for module in selected_modules:
            if module not in MICROGLIA_GENE_MODULES:
                raise KeyError(f"Unknown module: {module}")
            present = sorted(gene for gene in MICROGLIA_GENE_MODULES[module] if gene.upper() in gene_to_idx)
            idx = [gene_to_idx[gene.upper()] for gene in present]
            if len(idx) >= min_genes:
                perturbations.append((module, module, present, idx, "module"))
    if mode in {"gene", "both"}:
        selected_genes = genes or sorted({gene for geneset in MICROGLIA_GENE_MODULES.values() for gene in geneset})
        module_lookup = {
            gene.upper(): ";".join(sorted(name for name, geneset in MICROGLIA_GENE_MODULES.items() if gene.upper() in {g.upper() for g in geneset}))
            for gene in selected_genes
        }
        for gene in selected_genes:
            idx = gene_to_idx.get(gene.upper())
            if idx is not None:
                perturbations.append((module_lookup.get(gene.upper()) or "unannotated", gene.upper(), [gene.upper()], [idx], "gene"))
    return perturbations


def apply_intervention(x: np.ndarray, idx: list[int], intervention: str, global_means: np.ndarray) -> np.ndarray:
    perturbed = x.copy()
    if intervention == "zero":
        perturbed[:, idx] = 0.0
    elif intervention == "global_mean":
        perturbed[:, idx] = global_means[idx]
    elif intervention == "p99":
        perturbed[:, idx] = np.percentile(x[:, idx], 99, axis=0).astype(np.float32)
    else:
        raise ValueError("intervention must be zero, global_mean, or p99")
    return perturbed


def main() -> None:
    parser = argparse.ArgumentParser(description="Score graph-mediated digital perturbations with a frozen pathology head.")
    parser.add_argument("--encoder-checkpoint", default="results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt")
    parser.add_argument("--pathology-head", default="results/models/pathology_heads_stage_b_lp/best_pathology_head.pt")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--mode", choices=["module", "gene", "both"], default="module")
    parser.add_argument("--modules", nargs="*", default=None)
    parser.add_argument("--genes", nargs="*", default=None)
    parser.add_argument("--intervention", choices=["zero", "global_mean", "p99"], default="global_mean")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--min-genes", type=int, default=2)
    parser.add_argument("--max-cells", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--skip-manifold-nearest-neighbor", action="store_true")
    parser.add_argument("--summary-out", default="results/tables/pathology_head_module_counterfactual_summary.csv")
    parser.add_argument("--donor-out", default="results/tables/pathology_head_module_counterfactual_donor.csv")
    args = parser.parse_args()

    device = choose_device(args.device)
    print(f"Loading frozen encoder: {args.encoder_checkpoint}")
    encoder_checkpoint = torch.load(args.encoder_checkpoint, map_location="cpu", weights_only=False)
    model = infer_fast_model(encoder_checkpoint).to(device)
    print(f"Loading frozen pathology head: {args.pathology_head}")
    head_payload = torch.load(args.pathology_head, map_location="cpu", weights_only=False)
    head = make_head(head_payload)

    x_tensor, gene_names, obs = dense_h5ad(args.h5ad)
    donors_all = normalize_donor_id(obs[args.donor_column]).reset_index(drop=True)
    rows = sample_rows_by_donor(donors_all, args.max_cells, args.seed)
    x = x_tensor.numpy()[rows].astype(np.float32, copy=True)
    donors = donors_all.iloc[rows].reset_index(drop=True)
    global_means = x.mean(axis=0)
    print(f"Using {x.shape[0]:,} cells across {donors.nunique():,} donors")

    edge_index = load_consensus_edge_index(args.edge_csv)
    adj = normalized_adjacency(edge_index, len(gene_names), 0.0, device)
    perturbations = build_perturbations(gene_names, args.mode, args.modules, args.genes, args.min_genes)
    if not perturbations:
        raise ValueError("No perturbations matched the input gene space.")

    print("Encoding baseline")
    z_base = encode_matrix(model, torch.from_numpy(x), adj, device, args.batch_size)
    donor_base = aggregate_by_donor(z_base, donors)
    baseline_pred = predict_pathology(head, head_payload, donor_base)

    nearest = None
    base_nn_p95 = np.nan
    if args.skip_manifold_nearest_neighbor:
        print("Skipping nearest-neighbor manifold check; manifold fields will be marked not_computed.")
    else:
        nearest = NearestNeighbors(n_neighbors=2, metric="euclidean").fit(z_base)
        base_nn_dist, _ = nearest.kneighbors(z_base)
        base_nn_p95 = float(np.quantile(base_nn_dist[:, 1], 0.95))

    summary_rows = []
    donor_rows = []
    for module, perturbation, genes, idx, perturbation_type in perturbations:
        print(f"Perturbing {perturbation} ({perturbation_type}, {len(idx)} genes)")
        x_perturbed = apply_intervention(x, idx, args.intervention, global_means)
        z_perturbed = encode_matrix(model, torch.from_numpy(x_perturbed), adj, device, args.batch_size)
        donor_perturbed = aggregate_by_donor(z_perturbed, donors)
        perturbed_pred = predict_pathology(head, head_payload, donor_perturbed)

        merged = baseline_pred.merge(perturbed_pred, on="Donor ID", suffixes=("_baseline", "_perturbed"))
        merged.insert(0, "module", module)
        merged.insert(1, "perturbation", perturbation)
        merged.insert(2, "perturbation_type", perturbation_type)
        merged.insert(3, "intervention", args.intervention)
        for target in head_payload["targets"]:
            merged[f"delta_{target}"] = merged[f"pred_{target}_perturbed"] - merged[f"pred_{target}_baseline"]
        donor_rows.append(merged)

        latent_shift = np.linalg.norm(z_perturbed - z_base, axis=1)
        if nearest is None:
            mean_nn_dist = np.nan
            p95_nn_dist = np.nan
            manifold_violation_fraction = np.nan
        else:
            pert_nn_dist, _ = nearest.kneighbors(z_perturbed, n_neighbors=1)
            mean_nn_dist = float(np.mean(pert_nn_dist[:, 0]))
            p95_nn_dist = float(np.quantile(pert_nn_dist[:, 0], 0.95))
            manifold_violation_fraction = float(np.mean(pert_nn_dist[:, 0] > base_nn_p95))
        row = {
            "module": module,
            "perturbation": perturbation,
            "perturbation_type": perturbation_type,
            "intervention": args.intervention,
            "n_genes_perturbed": len(idx),
            "genes": ";".join(genes),
            "mean_latent_shift": float(np.mean(latent_shift)),
            "median_latent_shift": float(np.median(latent_shift)),
            "mean_nearest_real_cell_distance": mean_nn_dist,
            "p95_nearest_real_cell_distance": p95_nn_dist,
            "baseline_nn_p95_threshold": base_nn_p95,
            "manifold_violation_fraction": manifold_violation_fraction,
        }
        for target in head_payload["targets"]:
            delta = merged[f"delta_{target}"].to_numpy(dtype=np.float32)
            row[f"mean_delta_{target}"] = float(np.mean(delta))
            row[f"median_delta_{target}"] = float(np.median(delta))
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)
    donor_df = pd.concat(donor_rows, ignore_index=True)
    summary_path = Path(args.summary_out)
    donor_path = Path(args.donor_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    donor_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_path, index=False)
    donor_df.to_csv(donor_path, index=False)
    print(f"Wrote summary: {summary_path}")
    print(f"Wrote donor table: {donor_path}")


if __name__ == "__main__":
    main()
