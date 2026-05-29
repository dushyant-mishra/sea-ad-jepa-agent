from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from sea_ad_jepa.data import load_pathology_targets
from sea_ad_jepa.interpretation import score_gene_sets


def pearson_against_target(x: np.ndarray, y: np.ndarray, device: str = "auto") -> np.ndarray:
    x = x.astype(np.float32, copy=False)
    y = y.astype(np.float32, copy=False)
    torch_device = torch.device("cuda" if device == "auto" and torch.cuda.is_available() else "cpu")
    if device != "auto":
        torch_device = torch.device(device)
    xt = torch.as_tensor(x, dtype=torch.float32, device=torch_device)
    yt = torch.as_tensor(y, dtype=torch.float32, device=torch_device)
    xt = xt - xt.mean(dim=0, keepdim=True)
    yt = yt - yt.mean()
    numerator = xt.T @ yt
    denominator = torch.sqrt(torch.sum(xt**2, dim=0) * torch.sum(yt**2))
    corr = numerator / denominator.clamp_min(1e-12)
    return corr.detach().cpu().numpy()


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank pseudobulk genes by association with one pathology target.")
    parser.add_argument("--features", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", default="results/tables/microglia_gene_target_rankings.csv")
    parser.add_argument("--gene-set-out", default="results/tables/microglia_gene_set_scores.csv")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    features = pd.read_csv(args.features)
    targets, _ = load_pathology_targets()
    merged = features.merge(targets[["Donor ID", args.target]], on="Donor ID", how="inner")
    gene_columns = [column for column in features.columns if column != "Donor ID"]

    x = merged[gene_columns].to_numpy(dtype=np.float32)
    y = pd.to_numeric(merged[args.target], errors="coerce").to_numpy(dtype=np.float32)
    keep = np.isfinite(y) & np.isfinite(x).all(axis=1)
    x = np.log1p(x[keep])
    y = y[keep]

    corr = pearson_against_target(x, y, device=args.device)
    rankings = pd.DataFrame({"gene": gene_columns, "score": corr})
    rankings["abs_score"] = rankings["score"].abs()
    rankings = rankings.sort_values("abs_score", ascending=False)

    out_path = Path(args.out)
    gene_set_path = Path(args.gene_set_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gene_set_path.parent.mkdir(parents=True, exist_ok=True)
    rankings.to_csv(out_path, index=False)

    gene_sets = score_gene_sets(rankings, gene_column="gene", score_column="abs_score")
    gene_sets.to_csv(gene_set_path, index=False)

    print(rankings.head(25).to_string(index=False))
    print(f"Wrote rankings: {out_path}")
    print(f"Wrote gene-set scores: {gene_set_path}")


if __name__ == "__main__":
    main()
