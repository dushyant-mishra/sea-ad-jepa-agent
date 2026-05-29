from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.model_selection import KFold
import torch

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id


def spearman_corr(a: np.ndarray, b: np.ndarray) -> float:
    a_rank = pd.Series(a).rank(method="average").to_numpy(dtype=np.float32)
    b_rank = pd.Series(b).rank(method="average").to_numpy(dtype=np.float32)
    a_rank = a_rank - a_rank.mean()
    b_rank = b_rank - b_rank.mean()
    denom = float(np.sqrt(np.sum(a_rank**2) * np.sum(b_rank**2)))
    if denom == 0:
        return float("nan")
    return float(np.sum(a_rank * b_rank) / denom)


def _matrix_to_dense_mean(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        return np.asarray(matrix.mean(axis=0)).ravel()
    return np.asarray(matrix).mean(axis=0)


def aggregate_mean_expression_by_donor(
    h5ad_path: str | Path,
    donor_column: str,
    max_genes: int | None = None,
) -> pd.DataFrame:
    """Aggregate an AnnData expression matrix into donor-level mean expression features."""
    adata = ad.read_h5ad(h5ad_path)
    if donor_column not in adata.obs:
        raise KeyError(f"Column not found in adata.obs: {donor_column}")

    donors = normalize_donor_id(adata.obs[donor_column])
    gene_names = adata.var_names.astype(str).tolist()

    if max_genes is not None and max_genes < len(gene_names):
        gene_names = gene_names[:max_genes]
        adata = adata[:, gene_names].copy()

    rows = []
    for donor_id, idx in donors.groupby(donors).indices.items():
        mean_expr = _matrix_to_dense_mean(adata.X[list(idx), :])
        rows.append(pd.Series(mean_expr, index=gene_names, name=donor_id))

    features = pd.DataFrame(rows)
    features.index.name = "Donor ID"
    return features.reset_index()


def cross_validated_ridge(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    target_columns: list[str],
    n_splits: int = 5,
    alpha: float = 10.0,
    device: str = "auto",
) -> pd.DataFrame:
    """Run donor-level ridge baselines for each pathology target."""
    merged = features.merge(targets, on="Donor ID", how="inner")
    feature_columns = [col for col in features.columns if col != "Donor ID"]
    x = merged[feature_columns].to_numpy(dtype=np.float32)

    rows = []
    for target in target_columns:
        y = pd.to_numeric(merged[target], errors="coerce").to_numpy(dtype=np.float32)
        keep = np.isfinite(y) & np.isfinite(x).all(axis=1)
        if keep.sum() < n_splits:
            continue

        x_keep = x[keep]
        y_keep = y[keep]
        predictions = np.full_like(y_keep, fill_value=np.nan, dtype=np.float32)
        cv = KFold(n_splits=min(n_splits, keep.sum()), shuffle=True, random_state=7)

        torch_device = torch.device("cuda" if device == "auto" and torch.cuda.is_available() else "cpu")
        if device != "auto":
            torch_device = torch.device(device)

        for train_idx, test_idx in cv.split(x_keep):
            x_train_np = x_keep[train_idx]
            x_test_np = x_keep[test_idx]
            mean = x_train_np.mean(axis=0, keepdims=True)
            std = x_train_np.std(axis=0, keepdims=True)
            std[std == 0] = 1.0

            x_train = torch.as_tensor((x_train_np - mean) / std, dtype=torch.float32, device=torch_device)
            x_test = torch.as_tensor((x_test_np - mean) / std, dtype=torch.float32, device=torch_device)
            y_train = torch.as_tensor(y_keep[train_idx], dtype=torch.float32, device=torch_device)

            ones_train = torch.ones((x_train.shape[0], 1), dtype=torch.float32, device=torch_device)
            ones_test = torch.ones((x_test.shape[0], 1), dtype=torch.float32, device=torch_device)
            x_train = torch.cat([ones_train, x_train], dim=1)
            x_test = torch.cat([ones_test, x_test], dim=1)

            identity = torch.eye(x_train.shape[1], dtype=torch.float32, device=torch_device)
            identity[0, 0] = 0.0
            weights = torch.linalg.solve(x_train.T @ x_train + alpha * identity, x_train.T @ y_train)
            predictions[test_idx] = (x_test @ weights).detach().cpu().numpy()

        residual = y_keep - predictions
        ss_res = float(np.sum(residual**2))
        ss_tot = float(np.sum((y_keep - y_keep.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
        mae = float(np.mean(np.abs(residual)))

        rows.append(
            {
                "target": target,
                "n_donors": int(keep.sum()),
                "r2": r2,
                "mae": mae,
                "spearman": spearman_corr(y_keep, predictions),
            }
        )

    return pd.DataFrame(rows).sort_values("spearman", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run donor-level mean-expression ridge baselines.")
    parser.add_argument("--h5ad", required=True, help="Pilot AnnData file.")
    parser.add_argument("--donor-column", required=True, help="Donor ID column in adata.obs.")
    parser.add_argument("--out", default="results/tables/baseline_ridge_pathology.csv")
    parser.add_argument("--max-genes", type=int, default=None)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    targets, target_columns = load_pathology_targets()
    features = aggregate_mean_expression_by_donor(args.h5ad, donor_column=args.donor_column, max_genes=args.max_genes)
    results = cross_validated_ridge(features, targets, target_columns)
    results.to_csv(out_path, index=False)
    print(results.to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
