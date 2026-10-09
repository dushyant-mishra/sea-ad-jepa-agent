from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.metrics import silhouette_score
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler

from sea_ad_jepa.baselines import spearman_corr
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.evaluation_utils import choose_device, load_jepa, make_strata, to_dense_float32


DEFAULT_TARGETS = [
    "percent AT8 positive area_Grey matter",
    "percent 6e10 positive area_Grey matter",
    "percent GFAP positive area_Grey matter",
    "percent Iba1 positive area_Grey matter",
    "percent NeuN positive area_Grey matter",
]


def sample_cells_balanced_by_donor(donors: pd.Series, max_cells: int, seed: int) -> np.ndarray:
    if max_cells <= 0 or max_cells >= donors.shape[0]:
        return np.arange(donors.shape[0], dtype=np.int64)
    rng = np.random.default_rng(seed)
    donor_groups = donors.groupby(donors).indices
    per_donor = max(1, int(np.ceil(max_cells / max(1, len(donor_groups)))))
    selected = []
    for _, idx in donor_groups.items():
        idx_np = np.asarray(idx, dtype=np.int64)
        take = min(per_donor, idx_np.size)
        selected.extend(rng.choice(idx_np, size=take, replace=False).tolist())
    selected = np.asarray(selected, dtype=np.int64)
    if selected.size > max_cells:
        selected = rng.choice(selected, size=max_cells, replace=False)
    return np.sort(selected)


def compute_pca_features(x, n_components: int, seed: int) -> np.ndarray:
    n_components = min(n_components, min(x.shape) - 1)
    x_np = to_dense_float32(x)
    x_np = StandardScaler(with_mean=True, with_std=True).fit_transform(x_np).astype(np.float32)
    return PCA(n_components=n_components, random_state=seed).fit_transform(x_np).astype(np.float32)


def compute_jepa_features(
    x_np: np.ndarray,
    checkpoint: str,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    model, _ = load_jepa(checkpoint, device)
    model.eval()
    features = []
    for start in range(0, x_np.shape[0], batch_size):
        batch = torch.as_tensor(x_np[start : start + batch_size], dtype=torch.float32, device=device)
        with torch.no_grad():
            features.append(model.context_encoder(batch).cpu().numpy())
    return np.concatenate(features, axis=0).astype(np.float32)


def reduce_2d(features: np.ndarray, reducer: str, seed: int, n_neighbors: int, min_dist: float) -> np.ndarray:
    if reducer == "pca":
        return PCA(n_components=2, random_state=seed).fit_transform(features).astype(np.float32)
    if reducer == "umap":
        try:
            import umap
        except ImportError:
            print("umap-learn is not installed; falling back to PCA-2D.")
            return PCA(n_components=2, random_state=seed).fit_transform(features).astype(np.float32)
        return umap.UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            metric="euclidean",
            random_state=seed,
        ).fit_transform(features).astype(np.float32)
    raise ValueError(f"Unknown reducer: {reducer}")


def donor_mean_features(features: np.ndarray, donors: pd.Series) -> pd.DataFrame:
    feature_df = pd.DataFrame(features, columns=[f"z_{i:03d}" for i in range(features.shape[1])])
    feature_df.insert(0, "Donor ID", donors.to_numpy())
    return feature_df.groupby("Donor ID", as_index=False).mean()


def pathology_bins(values: np.ndarray, n_bins: int) -> np.ndarray:
    try:
        return pd.qcut(values, q=n_bins, labels=False, duplicates="drop").to_numpy(dtype=np.int32)
    except ValueError:
        return pd.cut(values, bins=n_bins, labels=False, include_lowest=True).to_numpy(dtype=np.int32)


def evaluate_donor_knn(
    label: str,
    features: pd.DataFrame,
    targets: pd.DataFrame,
    target_names: list[str],
    n_splits: int,
    n_neighbors: int,
) -> list[dict[str, object]]:
    rows = []
    features = features.copy()
    features["Donor ID"] = normalize_donor_id(features["Donor ID"])
    merged = features.merge(targets, on="Donor ID", how="inner")
    feature_columns = [column for column in features.columns if column != "Donor ID"]
    x = merged[feature_columns].to_numpy(dtype=np.float32)
    donors = merged["Donor ID"].to_numpy()
    for target in target_names:
        if target not in merged:
            continue
        y = pd.to_numeric(merged[target], errors="coerce").to_numpy(dtype=np.float32)
        keep = np.isfinite(y) & np.isfinite(x).all(axis=1)
        if keep.sum() < n_splits:
            continue
        x_keep = x[keep]
        y_keep = y[keep]
        donor_keep = donors[keep]
        groups = donor_keep
        y_split = make_strata(y_keep, min(5, np.unique(y_keep).size))
        splitter = StratifiedGroupKFold(n_splits=min(n_splits, keep.sum()), shuffle=True, random_state=7)
        predictions = np.full(y_keep.shape, np.nan, dtype=np.float32)
        for train_idx, test_idx in splitter.split(x_keep, y_split, groups=groups):
            k = min(n_neighbors, max(1, train_idx.size))
            model = KNeighborsRegressor(n_neighbors=k, weights="distance")
            model.fit(x_keep[train_idx], y_keep[train_idx])
            predictions[test_idx] = model.predict(x_keep[test_idx]).astype(np.float32)
        residual = y_keep - predictions
        rows.append(
            {
                "representation": label,
                "target": target,
                "n_donors": int(keep.sum()),
                "knn_spearman": spearman_corr(y_keep, predictions),
                "knn_mae": float(np.mean(np.abs(residual))),
            }
        )
    return rows


def evaluate_silhouette(
    label: str,
    features: np.ndarray,
    donors: pd.Series,
    targets: pd.DataFrame,
    target_names: list[str],
    n_bins: int,
) -> list[dict[str, object]]:
    rows = []
    donor_features = donor_mean_features(features, donors)
    merged = donor_features.merge(targets, on="Donor ID", how="inner")
    feature_columns = [column for column in donor_features.columns if column != "Donor ID"]
    x = merged[feature_columns].to_numpy(dtype=np.float32)
    if x.shape[0] < 4:
        return rows
    for target in target_names:
        if target not in merged:
            continue
        y = pd.to_numeric(merged[target], errors="coerce").to_numpy(dtype=np.float32)
        keep = np.isfinite(y) & np.isfinite(x).all(axis=1)
        if keep.sum() < 4:
            continue
        labels = pathology_bins(y[keep], n_bins=n_bins)
        if np.unique(labels).size < 2:
            continue
        rows.append(
            {
                "representation": label,
                "target": target,
                "n_donors": int(keep.sum()),
                "pathology_bin_silhouette": float(silhouette_score(x[keep], labels)),
            }
        )
    return rows


def plot_embedding(
    embedding_df: pd.DataFrame,
    representation: str,
    target: str,
    out_path: Path,
) -> None:
    subset = embedding_df[embedding_df["representation"] == representation].copy()
    values = pd.to_numeric(subset[target], errors="coerce")
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    sc = ax.scatter(
        subset["x"],
        subset["y"],
        c=values,
        s=7,
        cmap="viridis",
        alpha=0.78,
        linewidths=0,
    )
    ax.set_title(f"{representation}: {target}")
    ax.set_xlabel("dim 1")
    ax.set_ylabel("dim 2")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label(target)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare standard PCA/UMAP geometry with JEPA disease-state geometry."
    )
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument(
        "--checkpoint",
        default="results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt",
    )
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument("--targets", nargs="*", default=DEFAULT_TARGETS)
    parser.add_argument("--max-cells", type=int, default=12000)
    parser.add_argument("--pca-components", type=int, default=128)
    parser.add_argument("--reducer", choices=["umap", "pca"], default="umap")
    parser.add_argument("--umap-neighbors", type=int, default=25)
    parser.add_argument("--umap-min-dist", type=float, default=0.25)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--knn-neighbors", type=int, default=7)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--embedding-out", default="results/tables/representation_geometry_cell_embeddings.csv")
    parser.add_argument("--metrics-out", default="results/tables/representation_geometry_metrics.csv")
    parser.add_argument("--figure-dir", default="results/figures/representation_geometry")
    args = parser.parse_args()

    device = choose_device(args.device)
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])

    adata = ad.read_h5ad(args.h5ad)
    if args.donor_column not in adata.obs:
        raise KeyError(f"Donor column not found in AnnData obs: {args.donor_column}")
    donors_all = normalize_donor_id(adata.obs[args.donor_column]).reset_index(drop=True)
    selected_idx = sample_cells_balanced_by_donor(donors_all, args.max_cells, args.seed)
    donors = donors_all.iloc[selected_idx].reset_index(drop=True)
    x_subset = adata.X[selected_idx]
    x_dense = to_dense_float32(x_subset)

    print(f"Selected {len(selected_idx):,} cells across {donors.nunique():,} donors")
    print("Computing PCA expression representation...")
    pca_features = compute_pca_features(x_subset, args.pca_components, args.seed)
    print("Computing JEPA latent representation...")
    jepa_features = compute_jepa_features(x_dense, args.checkpoint, device, args.batch_size)

    print(f"Reducing representations with {args.reducer}...")
    pca_2d = reduce_2d(pca_features, args.reducer, args.seed, args.umap_neighbors, args.umap_min_dist)
    jepa_2d = reduce_2d(jepa_features, args.reducer, args.seed, args.umap_neighbors, args.umap_min_dist)

    metadata = pd.DataFrame({"cell_index": selected_idx, "Donor ID": donors})
    metadata = metadata.merge(targets[["Donor ID", *[t for t in args.targets if t in targets.columns]]], on="Donor ID", how="left")
    pca_df = metadata.copy()
    pca_df.insert(1, "representation", f"expression_pca_{args.reducer}")
    pca_df["x"] = pca_2d[:, 0]
    pca_df["y"] = pca_2d[:, 1]
    jepa_df = metadata.copy()
    jepa_df.insert(1, "representation", f"jepa_latent_{args.reducer}")
    jepa_df["x"] = jepa_2d[:, 0]
    jepa_df["y"] = jepa_2d[:, 1]
    embedding_df = pd.concat([pca_df, jepa_df], ignore_index=True)

    embedding_out = Path(args.embedding_out)
    embedding_out.parent.mkdir(parents=True, exist_ok=True)
    embedding_df.to_csv(embedding_out, index=False)

    print("Evaluating donor-level pathology predictiveness and pathology-bin separation...")
    metric_rows = []
    pca_donor = donor_mean_features(pca_features, donors)
    jepa_donor = donor_mean_features(jepa_features, donors)
    metric_rows.extend(
        evaluate_donor_knn(
            f"expression_pca_{args.pca_components}",
            pca_donor,
            targets,
            args.targets,
            args.n_splits,
            args.knn_neighbors,
        )
    )
    metric_rows.extend(
        evaluate_donor_knn(
            "jepa_latent_128",
            jepa_donor,
            targets,
            args.targets,
            args.n_splits,
            args.knn_neighbors,
        )
    )
    metric_rows.extend(evaluate_silhouette(f"expression_pca_{args.pca_components}", pca_features, donors, targets, args.targets, 3))
    metric_rows.extend(evaluate_silhouette("jepa_latent_128", jepa_features, donors, targets, args.targets, 3))
    metrics = pd.DataFrame(metric_rows)
    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(metrics_out, index=False)

    figure_dir = Path(args.figure_dir)
    for target in args.targets:
        if target not in embedding_df:
            continue
        plot_embedding(embedding_df, f"expression_pca_{args.reducer}", target, figure_dir / f"expression_pca_{args.reducer}_{target}.png")
        plot_embedding(embedding_df, f"jepa_latent_{args.reducer}", target, figure_dir / f"jepa_latent_{args.reducer}_{target}.png")

    print(metrics.to_string(index=False))
    print(f"Wrote {embedding_out}")
    print(f"Wrote {metrics_out}")
    print(f"Wrote figures to {figure_dir}")


if __name__ == "__main__":
    main()
