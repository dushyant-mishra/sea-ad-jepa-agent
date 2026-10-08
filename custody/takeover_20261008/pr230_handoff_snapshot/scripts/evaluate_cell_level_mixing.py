from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.model_selection import KFold, StratifiedKFold

from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id


def to_dense_float32(matrix) -> np.ndarray:
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def zscore(x: np.ndarray) -> np.ndarray:
    mean = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    std[std == 0] = 1.0
    return ((x - mean) / std).astype(np.float32)


def torch_pca(x: np.ndarray, n_components: int) -> np.ndarray:
    n_components = max(2, min(n_components, min(x.shape) - 1))
    x_tensor = torch.as_tensor(zscore(x), dtype=torch.float32)
    x_tensor = x_tensor - x_tensor.mean(dim=0, keepdim=True)
    _, _, v = torch.pca_lowrank(x_tensor, q=n_components, center=False, niter=4)
    return (x_tensor @ v[:, :n_components]).cpu().numpy().astype(np.float32)


def pathology_bins(values: pd.Series, n_bins: int) -> pd.Series:
    try:
        return pd.qcut(values, q=n_bins, labels=False, duplicates="drop")
    except ValueError:
        return pd.cut(values, bins=n_bins, labels=False, include_lowest=True)


def balanced_sample_indices(meta: pd.DataFrame, donor_col: str, sample_size: int, seed: int) -> np.ndarray:
    if sample_size <= 0 or sample_size >= meta.shape[0]:
        return np.arange(meta.shape[0], dtype=np.int64)
    rng = np.random.default_rng(seed)
    donor_groups = meta.groupby(donor_col).indices
    per_donor = max(1, int(np.ceil(sample_size / max(1, len(donor_groups)))))
    selected: list[int] = []
    for _, idx in donor_groups.items():
        idx_np = np.asarray(idx, dtype=np.int64)
        take = min(per_donor, idx_np.size)
        selected.extend(rng.choice(idx_np, size=take, replace=False).tolist())
    selected_np = np.asarray(selected, dtype=np.int64)
    if selected_np.size > sample_size:
        selected_np = rng.choice(selected_np, size=sample_size, replace=False)
    return np.sort(selected_np)


def encode_labels(labels: pd.Series | np.ndarray) -> tuple[np.ndarray, list[str]]:
    series = pd.Series(labels).astype(str)
    categories = sorted(series.dropna().unique().tolist())
    mapping = {label: idx for idx, label in enumerate(categories)}
    return series.map(mapping).to_numpy(dtype=np.int64), categories


def chunked_silhouette(
    x: np.ndarray,
    labels: np.ndarray,
    chunk_size: int,
    device: torch.device,
) -> float:
    labels = np.asarray(labels)
    valid = pd.Series(labels).notna().to_numpy()
    x = x[valid]
    labels = labels[valid]
    encoded, categories = encode_labels(labels)
    if len(categories) < 2 or x.shape[0] <= len(categories):
        return float("nan")

    x_tensor = torch.as_tensor(x, dtype=torch.float32, device=device)
    label_masks = [torch.as_tensor(encoded == i, dtype=torch.bool, device=device) for i in range(len(categories))]
    encoded_tensor = torch.as_tensor(encoded, dtype=torch.long, device=device)
    scores = []
    for start in range(0, x.shape[0], chunk_size):
        end = min(start + chunk_size, x.shape[0])
        distances = torch.cdist(x_tensor[start:end], x_tensor)
        chunk_labels = encoded_tensor[start:end]
        for row_idx in range(end - start):
            label = int(chunk_labels[row_idx].item())
            same_mask = label_masks[label].clone()
            same_mask[start + row_idx] = False
            if int(same_mask.sum().item()) == 0:
                continue
            a = distances[row_idx, same_mask].mean()
            b_values = [
                distances[row_idx, mask].mean()
                for other, mask in enumerate(label_masks)
                if other != label and int(mask.sum().item()) > 0
            ]
            if not b_values:
                continue
            b = torch.stack(b_values).min()
            denom = torch.maximum(a, b)
            if float(denom.detach().cpu()) > 0:
                scores.append(float(((b - a) / denom).detach().cpu()))
    return float(np.mean(scores)) if scores else float("nan")


def knn_predict_labels(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    k: int,
    chunk_size: int,
    device: torch.device,
) -> np.ndarray:
    train = torch.as_tensor(x_train, dtype=torch.float32, device=device)
    test = torch.as_tensor(x_test, dtype=torch.float32, device=device)
    y_train = np.asarray(y_train)
    predictions = []
    for start in range(0, x_test.shape[0], chunk_size):
        end = min(start + chunk_size, x_test.shape[0])
        distances = torch.cdist(test[start:end], train).cpu().numpy()
        neighbor_idx = np.argsort(distances, axis=1)[:, :k]
        for row in neighbor_idx:
            values, counts = np.unique(y_train[row], return_counts=True)
            predictions.append(values[np.argmax(counts)])
    return np.asarray(predictions)


def donor_knn_accuracy(
    x: np.ndarray,
    donor_labels: pd.Series,
    k: int,
    n_splits: int,
    chunk_size: int,
    device: torch.device,
) -> float:
    y, _ = encode_labels(donor_labels)
    counts = np.bincount(y)
    min_class = int(counts[counts > 0].min())
    if min_class >= 2:
        splits = max(2, min(n_splits, min_class))
        split_iter = StratifiedKFold(n_splits=splits, shuffle=True, random_state=7).split(x, y)
    else:
        splits = max(2, min(n_splits, x.shape[0]))
        split_iter = KFold(n_splits=splits, shuffle=True, random_state=7).split(x)
    pred = np.full(y.shape, -1, dtype=np.int64)
    for train_idx, test_idx in split_iter:
        pred[test_idx] = knn_predict_labels(
            x_train=x[train_idx],
            y_train=y[train_idx],
            x_test=x[test_idx],
            k=min(k, train_idx.size),
            chunk_size=chunk_size,
            device=device,
        )
    return float(np.mean(pred == y))


def permutation_pathology_silhouette(
    x: np.ndarray,
    meta: pd.DataFrame,
    donor_col: str,
    path_bin_col: str,
    n_permutations: int,
    chunk_size: int,
    device: torch.device,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    donor_path = meta.groupby(donor_col)[path_bin_col].first().dropna()
    scores = []
    for _ in range(n_permutations):
        shuffled = rng.permutation(donor_path.to_numpy())
        shuffled_map = dict(zip(donor_path.index, shuffled))
        shuffled_labels = meta[donor_col].map(shuffled_map)
        valid = shuffled_labels.notna().to_numpy()
        scores.append(chunked_silhouette(x[valid], shuffled_labels[valid].to_numpy(), chunk_size, device))
    scores_np = np.asarray(scores, dtype=np.float32)
    return float(np.nanmean(scores_np)), float(np.nanstd(scores_np))


def evaluate_representation(
    representation: str,
    x: np.ndarray,
    meta: pd.DataFrame,
    donor_col: str,
    target: str,
    n_bins: int,
    k: int,
    n_splits: int,
    n_permutations: int,
    chunk_size: int,
    device: torch.device,
    seed: int,
) -> dict[str, object]:
    target_values = pd.to_numeric(meta[target], errors="coerce")
    valid_path = target_values.notna()
    path_bins = pathology_bins(target_values[valid_path], n_bins=n_bins)
    meta_eval = meta.copy()
    meta_eval["pathology_bin"] = pd.NA
    meta_eval.loc[valid_path, "pathology_bin"] = path_bins.astype(str).to_numpy()

    donor_sil = chunked_silhouette(x, meta_eval[donor_col].to_numpy(), chunk_size, device)
    path_sil = chunked_silhouette(
        x[valid_path.to_numpy()],
        meta_eval.loc[valid_path, "pathology_bin"].to_numpy(),
        chunk_size,
        device,
    )
    donor_acc = donor_knn_accuracy(
        x=x,
        donor_labels=meta_eval[donor_col],
        k=k,
        n_splits=n_splits,
        chunk_size=chunk_size,
        device=device,
    )
    majority = float(meta_eval[donor_col].value_counts(normalize=True).max())
    perm_mean, perm_std = permutation_pathology_silhouette(
        x=x,
        meta=meta_eval,
        donor_col=donor_col,
        path_bin_col="pathology_bin",
        n_permutations=n_permutations,
        chunk_size=chunk_size,
        device=device,
        seed=seed,
    )
    denom = max(abs(donor_sil), 1e-3)
    return {
        "representation": representation,
        "target": target,
        "n_cells": int(meta_eval.shape[0]),
        "n_donors": int(meta_eval[donor_col].nunique()),
        "donor_silhouette": donor_sil,
        "donor_knn_accuracy": donor_acc,
        "donor_majority_baseline": majority,
        "pathology_silhouette": path_sil,
        "permuted_pathology_silhouette_mean": perm_mean,
        "permuted_pathology_silhouette_std": perm_std,
        "pathology_minus_permuted": path_sil - perm_mean,
        "pathology_to_abs_donor_ratio": path_sil / denom,
    }


def load_jepa_cell_embeddings(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    if "Donor ID" in df:
        df["Donor ID"] = normalize_donor_id(df["Donor ID"])
    feature_cols = [column for column in df.columns if column.startswith("jepa_")]
    if not feature_cols:
        raise ValueError(f"No jepa_* columns found in {path}")
    return df[["Donor ID", *feature_cols]].copy() if "Donor ID" in df else df[feature_cols].copy()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate cell-level donor leakage and pathology mixing in PCA vs JEPA spaces.")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--jepa-cell-embeddings", default="results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_cell_embeddings.csv")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--sample-size", type=int, default=10000)
    parser.add_argument("--pca-components", type=int, default=128)
    parser.add_argument("--pathology-bins", type=int, default=3)
    parser.add_argument("--knn-k", type=int, default=5)
    parser.add_argument("--n-splits", type=int, default=3)
    parser.add_argument("--n-permutations", type=int, default=5)
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", default="results/tables/cell_level_mixing_metrics.csv")
    parser.add_argument("--sample-out", default="results/tables/cell_level_mixing_sample_metadata.csv")
    args = parser.parse_args()

    device = choose_device(args.device)
    print(f"Using device: {device}")
    adata = ad.read_h5ad(args.h5ad)
    if args.donor_column not in adata.obs:
        raise KeyError(f"Donor column not found in AnnData obs: {args.donor_column}")
    if args.target not in load_pathology_targets()[0].columns:
        raise KeyError(f"Target not found in pathology metadata: {args.target}")

    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    target_lookup = targets.set_index("Donor ID")[args.target]
    obs = adata.obs.copy()
    obs[args.donor_column] = normalize_donor_id(obs[args.donor_column])
    obs[args.target] = obs[args.donor_column].map(target_lookup)

    jepa_df = load_jepa_cell_embeddings(args.jepa_cell_embeddings)
    common_cells = obs.index.intersection(jepa_df.index)
    if common_cells.empty:
        raise ValueError("No overlapping cell IDs between AnnData obs and JEPA cell embeddings.")
    obs = obs.loc[common_cells].copy()
    jepa_df = jepa_df.loc[common_cells].copy()

    sample_idx = balanced_sample_indices(obs.reset_index(drop=False), args.donor_column, args.sample_size, args.seed)
    sample_cells = obs.index.to_numpy()[sample_idx]
    meta = obs.loc[sample_cells, [args.donor_column, args.target]].copy().reset_index(names="cell_id")
    meta = meta.rename(columns={args.donor_column: "Donor ID"})

    print(f"Sampled {meta.shape[0]:,} cells from {meta['Donor ID'].nunique():,} donors")
    x_sample = adata[sample_cells].X
    pca_x = torch_pca(to_dense_float32(x_sample), n_components=args.pca_components)
    jepa_cols = [column for column in jepa_df.columns if column.startswith("jepa_")]
    jepa_x = zscore(jepa_df.loc[sample_cells, jepa_cols].to_numpy(dtype=np.float32))

    rows = []
    for label, x in [("expression_pca_128", pca_x), ("jepa_latent_128", jepa_x)]:
        print(f"Evaluating {label}...")
        rows.append(
            evaluate_representation(
                representation=label,
                x=x,
                meta=meta,
                donor_col="Donor ID",
                target=args.target,
                n_bins=args.pathology_bins,
                k=args.knn_k,
                n_splits=args.n_splits,
                n_permutations=args.n_permutations,
                chunk_size=args.chunk_size,
                device=device,
                seed=args.seed,
            )
        )

    result = pd.DataFrame(rows)
    out_path = Path(args.out)
    sample_path = Path(args.sample_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_path, index=False)
    meta.to_csv(sample_path, index=False)
    print(result.to_string(index=False))
    print(f"Wrote {out_path}")
    print(f"Wrote {sample_path}")


if __name__ == "__main__":
    main()
