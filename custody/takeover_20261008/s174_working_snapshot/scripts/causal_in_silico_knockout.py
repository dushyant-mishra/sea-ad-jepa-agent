from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from sea_ad_jepa.data import normalize_donor_id
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES
from sea_ad_jepa.jepa import GeneJEPA


class PathologyRegressor(nn.Module):
    def __init__(self, latent_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z).squeeze(-1)


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def load_model(checkpoint_path: str, device: torch.device) -> tuple[GeneJEPA, PathologyRegressor, dict]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_args = checkpoint.get("args", {})
    latent_dim = int(model_args.get("latent_dim", 128))
    model = GeneJEPA(
        input_dim=int(checkpoint["n_genes"]),
        hidden_dim=int(model_args.get("hidden_dim", 512)),
        latent_dim=latent_dim,
        ema_decay=float(model_args.get("ema_decay", 0.996)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])

    head = PathologyRegressor(
        latent_dim=latent_dim,
        hidden_dim=int(model_args.get("head_hidden_dim", 128)),
        dropout=0.0,
    ).to(device)
    head.load_state_dict(checkpoint["head_state"])
    model.eval()
    head.eval()
    return model, head, checkpoint


def predict_cells(
    x_np: np.ndarray,
    model: GeneJEPA,
    head: PathologyRegressor,
    checkpoint: dict,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    loader = DataLoader(TensorDataset(torch.from_numpy(x_np)), batch_size=batch_size, shuffle=False)
    preds = []
    with torch.no_grad():
        for (batch,) in loader:
            z = model.context_encoder(batch.to(device))
            preds.append(head(z).cpu().numpy())
    pred_z = np.concatenate(preds).astype(np.float32)
    train_mean = float(checkpoint.get("train_mean", 0.0))
    train_std = float(checkpoint.get("train_std", 1.0)) or 1.0
    return pred_z * train_std + train_mean


def bootstrap_ci(values: np.ndarray, n_bootstrap: int, seed: int, ci: float) -> tuple[float, float]:
    clean = np.asarray(values, dtype=np.float32)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boot = np.empty(n_bootstrap, dtype=np.float32)
    for i in range(n_bootstrap):
        sample = rng.choice(clean, size=clean.size, replace=True)
        boot[i] = float(np.mean(sample))
    alpha = (100.0 - ci) / 2.0
    return float(np.percentile(boot, alpha)), float(np.percentile(boot, 100.0 - alpha))


def build_perturbation_sets(
    gene_names: list[str],
    mode: str,
    modules: list[str] | None,
    min_genes: int,
) -> list[tuple[str, str, list[str], list[int]]]:
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    selected_modules = modules or sorted(MICROGLIA_GENE_MODULES)
    perturbations = []
    for module_name in selected_modules:
        if module_name not in MICROGLIA_GENE_MODULES:
            raise KeyError(f"Unknown module: {module_name}")
        present_genes = sorted(gene for gene in MICROGLIA_GENE_MODULES[module_name] if gene.upper() in gene_to_idx)
        if mode == "module":
            idx = [gene_to_idx[gene.upper()] for gene in present_genes]
            if len(idx) >= min_genes:
                perturbations.append((module_name, module_name, present_genes, idx))
        else:
            for gene in present_genes:
                perturbations.append((module_name, gene, [gene], [gene_to_idx[gene.upper()]]))
    return perturbations


def apply_intervention(
    x_base: np.ndarray,
    target_idx: list[int],
    intervention: str,
    donors: pd.Series,
    global_means: np.ndarray,
) -> np.ndarray:
    x_perturbed = x_base.copy()
    if intervention == "zero":
        x_perturbed[:, target_idx] = 0.0
    elif intervention == "global_mean":
        x_perturbed[:, target_idx] = global_means[target_idx]
    elif intervention == "donor_mean":
        for donor_id, row_idx in donors.groupby(donors).indices.items():
            rows = np.asarray(row_idx, dtype=np.int64)
            donor_mean = x_base[rows][:, target_idx].mean(axis=0)
            x_perturbed[np.ix_(rows, target_idx)] = donor_mean
    else:
        raise ValueError(f"Unknown intervention: {intervention}")
    return x_perturbed


def summarize_delta(
    baseline_pred: np.ndarray,
    perturbed_pred: np.ndarray,
    donors: pd.Series,
    module: str,
    perturbation: str,
    genes: list[str],
    intervention: str,
    n_bootstrap: int,
    seed: int,
    ci: float,
) -> tuple[dict[str, object], pd.DataFrame]:
    cell_delta = perturbed_pred - baseline_pred
    donor_df = pd.DataFrame(
        {
            "Donor ID": donors.to_numpy(),
            "baseline_prediction": baseline_pred,
            "perturbed_prediction": perturbed_pred,
            "delta": cell_delta,
        }
    ).groupby("Donor ID", as_index=False).mean()
    donor_delta = donor_df["delta"].to_numpy(dtype=np.float32)
    ci_low, ci_high = bootstrap_ci(donor_delta, n_bootstrap=n_bootstrap, seed=seed, ci=ci)
    summary = {
        "module": module,
        "perturbation": perturbation,
        "intervention": intervention,
        "n_genes_perturbed": len(genes),
        "genes": ";".join(genes),
        "mean_baseline_prediction": float(np.mean(baseline_pred)),
        "mean_perturbed_prediction": float(np.mean(perturbed_pred)),
        "mean_cell_delta": float(np.mean(cell_delta)),
        "mean_donor_delta": float(np.mean(donor_delta)),
        "median_donor_delta": float(np.median(donor_delta)),
        "abs_mean_donor_delta": float(abs(np.mean(donor_delta))),
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
        "n_donors": int(donor_df.shape[0]),
        "n_cells": int(cell_delta.size),
    }
    donor_df.insert(0, "module", module)
    donor_df.insert(1, "perturbation", perturbation)
    donor_df.insert(2, "intervention", intervention)
    return summary, donor_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Run in-silico module or gene knockouts on a trained JEPA pathology model.")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--mode", choices=["module", "gene"], default="module")
    parser.add_argument("--modules", nargs="*", default=None)
    parser.add_argument("--intervention", choices=["global_mean", "donor_mean", "zero"], default="global_mean")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--min-genes", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--ci", type=float, default=95.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", default="results/tables/causal_module_knockouts.csv")
    parser.add_argument("--donor-out", default="results/tables/causal_module_knockouts_by_donor.csv")
    args = parser.parse_args()

    device = choose_device(args.device)
    adata = ad.read_h5ad(args.h5ad)
    if args.donor_column not in adata.obs:
        raise KeyError(f"Donor column not found in AnnData obs: {args.donor_column}")
    donors = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)
    gene_names = adata.var_names.astype(str).tolist()

    x_base = to_dense_float32(adata.X)
    model, head, checkpoint = load_model(args.checkpoint, device)
    if int(checkpoint["n_genes"]) != x_base.shape[1]:
        raise ValueError(f"Checkpoint expects {checkpoint['n_genes']} genes but AnnData has {x_base.shape[1]} genes.")

    perturbations = build_perturbation_sets(
        gene_names=gene_names,
        mode=args.mode,
        modules=args.modules,
        min_genes=args.min_genes,
    )
    print(f"Loaded {x_base.shape[0]:,} cells x {x_base.shape[1]:,} genes")
    print(f"Perturbations to run: {len(perturbations):,}")
    print(f"Intervention: {args.intervention}")

    baseline_pred = predict_cells(x_base, model, head, checkpoint, device, args.batch_size)
    global_means = x_base.mean(axis=0)
    summary_rows = []
    donor_rows = []
    for module, perturbation, genes, idx in perturbations:
        x_perturbed = apply_intervention(
            x_base=x_base,
            target_idx=idx,
            intervention=args.intervention,
            donors=donors,
            global_means=global_means,
        )
        perturbed_pred = predict_cells(x_perturbed, model, head, checkpoint, device, args.batch_size)
        summary, donor_df = summarize_delta(
            baseline_pred=baseline_pred,
            perturbed_pred=perturbed_pred,
            donors=donors,
            module=module,
            perturbation=perturbation,
            genes=genes,
            intervention=args.intervention,
            n_bootstrap=args.n_bootstrap,
            seed=args.seed,
            ci=args.ci,
        )
        summary_rows.append(summary)
        donor_rows.append(donor_df)
        print(
            f"{perturbation:<30} "
            f"mean_donor_delta={summary['mean_donor_delta']:+.6f} "
            f"CI=({summary['bootstrap_ci_low']:+.6f}, {summary['bootstrap_ci_high']:+.6f})"
        )

    summary_df = pd.DataFrame(summary_rows).sort_values("abs_mean_donor_delta", ascending=False)
    donor_df = pd.concat(donor_rows, ignore_index=True) if donor_rows else pd.DataFrame()
    out_path = Path(args.out)
    donor_out_path = Path(args.donor_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    donor_out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_path, index=False)
    donor_df.to_csv(donor_out_path, index=False)
    print(f"Wrote {out_path}")
    print(f"Wrote {donor_out_path}")


if __name__ == "__main__":
    main()
