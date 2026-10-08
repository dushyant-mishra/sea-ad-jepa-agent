from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

from sea_ad_jepa.baselines import spearman_corr
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id


DEFAULT_TARGETS = [
    "percent AT8 positive area_Grey matter",
    "percent NeuN positive area_Grey matter",
    "percent 6e10 positive area_Grey matter",
    "percent GFAP positive area_Grey matter",
    "percent Iba1 positive area_Grey matter",
]


def load_feature_table(path: str, label: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Donor ID" not in df:
        raise KeyError(f"{label} feature table must contain a Donor ID column: {path}")
    df["Donor ID"] = normalize_donor_id(df["Donor ID"])
    return df


def numeric_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    feature_columns = [column for column in df.columns if column != "Donor ID"]
    x = df[feature_columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
    keep_cols = np.isfinite(x).all(axis=0) & (np.std(x, axis=0) > 0)
    return x[:, keep_cols], [column for column, keep in zip(feature_columns, keep_cols) if keep]


def pca_representation(features: pd.DataFrame, n_components: int) -> pd.DataFrame:
    x, _ = numeric_feature_matrix(features)
    n_components = max(2, min(n_components, min(x.shape) - 1))
    x_scaled = StandardScaler().fit_transform(x).astype(np.float32)
    z = torch_pca(x_scaled, n_components=n_components)
    out = pd.DataFrame(z, columns=[f"pc_{i:03d}" for i in range(z.shape[1])])
    out.insert(0, "Donor ID", features["Donor ID"].to_numpy())
    return out


def scaled_representation(features: pd.DataFrame, prefix: str) -> pd.DataFrame:
    x, _ = numeric_feature_matrix(features)
    x_scaled = StandardScaler().fit_transform(x).astype(np.float32)
    out = pd.DataFrame(x_scaled, columns=[f"{prefix}_{i:03d}" for i in range(x_scaled.shape[1])])
    out.insert(0, "Donor ID", features["Donor ID"].to_numpy())
    return out


def torch_pca(x: np.ndarray, n_components: int) -> np.ndarray:
    x_tensor = torch.as_tensor(x, dtype=torch.float32)
    x_tensor = x_tensor - x_tensor.mean(dim=0, keepdim=True)
    _, _, v = torch.pca_lowrank(x_tensor, q=n_components, center=False, niter=4)
    return (x_tensor @ v[:, :n_components]).cpu().numpy().astype(np.float32)


def reduce_2d(
    x: np.ndarray,
    reducer: str,
    seed: int,
    n_neighbors: int,
    min_dist: float,
    umap_a: float,
    umap_b: float,
) -> np.ndarray:
    if reducer == "pca":
        return torch_pca(x.astype(np.float32), n_components=2)
    if reducer == "umap":
        try:
            import umap
        except ImportError:
            print("umap-learn is not installed; using PCA-2D fallback.")
            return torch_pca(x.astype(np.float32), n_components=2)
        try:
            return umap.UMAP(
                n_components=2,
                n_neighbors=min(n_neighbors, max(2, x.shape[0] - 1)),
                min_dist=min_dist,
                a=umap_a,
                b=umap_b,
                metric="euclidean",
                init="random",
                random_state=seed,
            ).fit_transform(x).astype(np.float32)
        except Exception as exc:
            print(f"UMAP failed ({exc}); using PCA-2D fallback.")
            return torch_pca(x.astype(np.float32), n_components=2)
    raise ValueError(f"Unknown reducer: {reducer}")


def make_tertiles(y: np.ndarray) -> np.ndarray:
    try:
        return np.asarray(pd.qcut(y, q=3, labels=False, duplicates="drop"), dtype=np.int32)
    except ValueError:
        return np.asarray(pd.cut(y, bins=3, labels=False, include_lowest=True), dtype=np.int32)


def out_of_fold_knn(
    x: np.ndarray,
    y: np.ndarray,
    n_neighbors: int,
    n_splits: int,
    seed: int,
) -> np.ndarray:
    y_bins = make_tertiles(y)
    if np.unique(y_bins).size >= 2 and min(np.bincount(y_bins)) >= 2:
        splitter = StratifiedKFold(n_splits=min(n_splits, min(np.bincount(y_bins))), shuffle=True, random_state=seed)
        splits = splitter.split(x, y_bins)
    else:
        splitter = KFold(n_splits=min(n_splits, x.shape[0]), shuffle=True, random_state=seed)
        splits = splitter.split(x)
    pred = np.full(y.shape, np.nan, dtype=np.float32)
    for train_idx, test_idx in splits:
        k = min(n_neighbors, train_idx.size)
        pred[test_idx] = knn_predict(x[train_idx], y[train_idx], x[test_idx], k)
    return pred


def knn_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, k: int) -> np.ndarray:
    train = torch.as_tensor(x_train, dtype=torch.float32)
    test = torch.as_tensor(x_test, dtype=torch.float32)
    distances = torch.cdist(test, train).cpu().numpy()
    neighbor_idx = np.argsort(distances, axis=1)[:, :k]
    neighbor_distances = np.take_along_axis(distances, neighbor_idx, axis=1)
    weights = 1.0 / np.maximum(neighbor_distances, 1e-6)
    weights = weights / weights.sum(axis=1, keepdims=True)
    return np.sum(y_train[neighbor_idx] * weights, axis=1).astype(np.float32)


def simple_r2(y: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def simple_silhouette(x: np.ndarray, labels: np.ndarray) -> float:
    unique_labels = np.unique(labels)
    if unique_labels.size < 2 or x.shape[0] <= unique_labels.size:
        return float("nan")
    distances = torch.cdist(torch.as_tensor(x, dtype=torch.float32), torch.as_tensor(x, dtype=torch.float32)).cpu().numpy()
    scores = []
    for i, label in enumerate(labels):
        same = labels == label
        same[i] = False
        if same.sum() == 0:
            continue
        a = float(distances[i, same].mean())
        b = min(float(distances[i, labels == other].mean()) for other in unique_labels if other != label)
        denom = max(a, b)
        if denom > 0:
            scores.append((b - a) / denom)
    return float(np.mean(scores)) if scores else float("nan")


def evaluate_representation(
    label: str,
    features: pd.DataFrame,
    targets: pd.DataFrame,
    target_names: list[str],
    n_neighbors: int,
    n_splits: int,
    seed: int,
) -> list[dict[str, object]]:
    merged = features.merge(targets, on="Donor ID", how="inner")
    feature_columns = [column for column in features.columns if column != "Donor ID"]
    x_all = merged[feature_columns].to_numpy(dtype=np.float32)
    rows = []
    for target in target_names:
        if target not in merged:
            continue
        y_all = pd.to_numeric(merged[target], errors="coerce").to_numpy(dtype=np.float32)
        keep = np.isfinite(y_all) & np.isfinite(x_all).all(axis=1)
        if keep.sum() < max(6, n_splits):
            continue
        x = x_all[keep]
        y = y_all[keep]
        y_bins = make_tertiles(y)
        sil = float("nan")
        if np.unique(y_bins).size >= 2:
            sil = simple_silhouette(x, y_bins)
        pred = out_of_fold_knn(x, y, n_neighbors=n_neighbors, n_splits=n_splits, seed=seed)
        rows.append(
            {
                "representation": label,
                "target": target,
                "n_donors": int(keep.sum()),
                "pathology_tertile_silhouette": sil,
                "knn_spearman": spearman_corr(y, pred),
                "knn_r2": simple_r2(y, pred),
                "knn_mae": float(np.mean(np.abs(y - pred))),
            }
        )
    return rows


def build_embedding_table(
    representation_label: str,
    features: pd.DataFrame,
    targets: pd.DataFrame,
    target_names: list[str],
    reducer: str,
    seed: int,
    n_neighbors: int,
    min_dist: float,
    umap_a: float,
    umap_b: float,
) -> pd.DataFrame:
    feature_columns = [column for column in features.columns if column != "Donor ID"]
    x = features[feature_columns].to_numpy(dtype=np.float32)
    xy = reduce_2d(
        x,
        reducer=reducer,
        seed=seed,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        umap_a=umap_a,
        umap_b=umap_b,
    )
    emb = pd.DataFrame(
        {
            "Donor ID": features["Donor ID"].to_numpy(),
            "representation": representation_label,
            "x": xy[:, 0],
            "y": xy[:, 1],
        }
    )
    return emb.merge(targets[["Donor ID", *[target for target in target_names if target in targets]]], on="Donor ID", how="left")


def short_target_name(target: str) -> str:
    replacements = {
        "percent AT8 positive area_Grey matter": "AT8 / pTau",
        "percent NeuN positive area_Grey matter": "NeuN",
        "percent 6e10 positive area_Grey matter": "A beta / 6e10",
        "percent GFAP positive area_Grey matter": "GFAP",
        "percent Iba1 positive area_Grey matter": "Iba1",
    }
    return replacements.get(target, target)


def plot_2x2(embedding_df: pd.DataFrame, target_a: str, target_b: str, out_path: Path) -> None:
    reps = ["expression_pca_umap", "jepa_latent_umap"]
    targets = [target_a, target_b]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1280, 960
    panel_w, panel_h = 520, 340
    lefts = [80, 700]
    tops = [90, 540]
    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f8fb"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172033}.title{font-size:22px;font-weight:700}.label{font-size:15px}.tick{font-size:12px;fill:#526071}</style>',
        '<text x="60" y="42" class="title">PCA Expression Space vs JEPA Disease-State Space</text>',
    ]
    for row_idx, target in enumerate(targets):
        target_values_all = pd.to_numeric(embedding_df[target], errors="coerce").to_numpy(dtype=np.float32)
        vmin = float(np.nanpercentile(target_values_all, 2))
        vmax = float(np.nanpercentile(target_values_all, 98))
        for col_idx, rep in enumerate(reps):
            subset = embedding_df[embedding_df["representation"] == rep].copy()
            x = subset["x"].to_numpy(dtype=np.float32)
            y = subset["y"].to_numpy(dtype=np.float32)
            values = pd.to_numeric(subset[target], errors="coerce").to_numpy(dtype=np.float32)
            left = lefts[col_idx]
            top = tops[row_idx]
            title = f"{rep.replace('_', ' ')} colored by {short_target_name(target)}"
            svg.append(f'<text x="{left}" y="{top - 24}" class="label">{escape_xml(title)}</text>')
            svg.append(f'<rect x="{left}" y="{top}" width="{panel_w}" height="{panel_h}" fill="#ffffff" stroke="#d8dde7"/>')
            x_min, x_max = float(np.nanmin(x)), float(np.nanmax(x))
            y_min, y_max = float(np.nanmin(y)), float(np.nanmax(y))
            x_span = x_max - x_min or 1.0
            y_span = y_max - y_min or 1.0
            order = np.argsort(values)
            for i in order:
                px = left + 24 + ((float(x[i]) - x_min) / x_span) * (panel_w - 48)
                py = top + panel_h - 24 - ((float(y[i]) - y_min) / y_span) * (panel_h - 48)
                color = gradient_color(float(values[i]), vmin, vmax)
                svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5.5" fill="{color}" stroke="#ffffff" stroke-width="0.6" opacity="0.9"/>')
            legend_x = left + panel_w - 110
            legend_y = top + panel_h + 22
            for j in range(80):
                frac = j / 79
                color = gradient_color(vmin + frac * (vmax - vmin), vmin, vmax)
                svg.append(f'<rect x="{legend_x + j}" y="{legend_y}" width="1.2" height="8" fill="{color}"/>')
            svg.append(f'<text x="{legend_x}" y="{legend_y + 24}" class="tick">{vmin:.2g}</text>')
            svg.append(f'<text x="{legend_x + 58}" y="{legend_y + 24}" class="tick">{vmax:.2g}</text>')
    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


def plot_2x2_html(embedding_df: pd.DataFrame, target_a: str, target_b: str, out_path: Path) -> None:
    try:
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
    except ImportError:
        print("Plotly is not installed; skipping interactive HTML figure.")
        return

    reps = ["expression_pca_umap", "jepa_latent_umap"]
    targets = [target_a, target_b]
    titles = [
        f"{rep.replace('_', ' ')}<br>{short_target_name(target)}"
        for target in targets
        for rep in reps
    ]
    fig = make_subplots(rows=2, cols=2, subplot_titles=titles, horizontal_spacing=0.08, vertical_spacing=0.12)
    for row_idx, target in enumerate(targets, start=1):
        all_values = pd.to_numeric(embedding_df[target], errors="coerce").to_numpy(dtype=np.float32)
        cmin = float(np.nanpercentile(all_values, 2))
        cmax = float(np.nanpercentile(all_values, 98))
        for col_idx, rep in enumerate(reps, start=1):
            subset = embedding_df[embedding_df["representation"] == rep]
            fig.add_trace(
                go.Scattergl(
                    x=subset["x"],
                    y=subset["y"],
                    mode="markers",
                    text=subset["Donor ID"],
                    marker={
                        "color": pd.to_numeric(subset[target], errors="coerce"),
                        "colorscale": "Viridis",
                        "cmin": cmin,
                        "cmax": cmax,
                        "size": 9,
                        "line": {"color": "white", "width": 0.5},
                        "colorbar": {"title": short_target_name(target)} if col_idx == 2 else None,
                    },
                    name=f"{rep} {short_target_name(target)}",
                    showlegend=False,
                    hovertemplate="Donor=%{text}<br>x=%{x:.3f}<br>y=%{y:.3f}<br>value=%{marker.color:.3f}<extra></extra>",
                ),
                row=row_idx,
                col=col_idx,
            )
    fig.update_layout(
        title="PCA Expression Space vs JEPA Disease-State Space",
        template="plotly_white",
        width=1200,
        height=900,
    )
    fig.update_xaxes(title_text="UMAP 1")
    fig.update_yaxes(title_text="UMAP 2")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_path, include_plotlyjs="cdn")


def gradient_color(value: float, vmin: float, vmax: float) -> str:
    if not np.isfinite(value):
        return "#b9c0cc"
    frac = (value - vmin) / (vmax - vmin or 1.0)
    frac = max(0.0, min(1.0, frac))
    stops = [(44, 64, 142), (32, 144, 140), (244, 208, 63)]
    if frac < 0.5:
        local = frac / 0.5
        a, b = stops[0], stops[1]
    else:
        local = (frac - 0.5) / 0.5
        a, b = stops[1], stops[2]
    rgb = tuple(int(round(a_i + local * (b_i - a_i))) for a_i, b_i in zip(a, b))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PCA vs JEPA latent spaces for pathology-grounded geometry.")
    parser.add_argument("--pseudobulk", default="data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv")
    parser.add_argument("--jepa", default="results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv")
    parser.add_argument("--targets", nargs="*", default=DEFAULT_TARGETS)
    parser.add_argument("--pca-components", type=int, default=128)
    parser.add_argument("--n-neighbors", type=int, default=5)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--umap-neighbors", type=int, default=12)
    parser.add_argument("--umap-min-dist", type=float, default=0.2)
    parser.add_argument("--umap-a", type=float, default=1.57694346)
    parser.add_argument("--umap-b", type=float, default=0.89506088)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--metrics-out", default="results/tables/latent_space_evaluation_metrics.csv")
    parser.add_argument("--embedding-out", default="results/tables/latent_space_umap_coordinates.csv")
    parser.add_argument("--figure-out", default="results/figures/latent_space_pca_vs_jepa_umap_at8_neun.svg")
    parser.add_argument("--html-out", default="results/figures/latent_space_pca_vs_jepa_umap_at8_neun.html")
    args = parser.parse_args()

    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    pseudobulk = load_feature_table(args.pseudobulk, "pseudobulk")
    jepa = load_feature_table(args.jepa, "jepa")

    expression_pca = pca_representation(pseudobulk, args.pca_components)
    jepa_scaled = scaled_representation(jepa, "jepa")

    metric_rows = []
    metric_rows.extend(
        evaluate_representation(
            "expression_pca_128",
            expression_pca,
            targets,
            args.targets,
            n_neighbors=args.n_neighbors,
            n_splits=args.n_splits,
            seed=args.seed,
        )
    )
    metric_rows.extend(
        evaluate_representation(
            "jepa_latent_128",
            jepa_scaled,
            targets,
            args.targets,
            n_neighbors=args.n_neighbors,
            n_splits=args.n_splits,
            seed=args.seed,
        )
    )
    metrics = pd.DataFrame(metric_rows)
    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(metrics_out, index=False)

    expression_emb = build_embedding_table(
        "expression_pca_umap",
        expression_pca,
        targets,
        args.targets,
        reducer="umap",
        seed=args.seed,
        n_neighbors=args.umap_neighbors,
        min_dist=args.umap_min_dist,
        umap_a=args.umap_a,
        umap_b=args.umap_b,
    )
    jepa_emb = build_embedding_table(
        "jepa_latent_umap",
        jepa_scaled,
        targets,
        args.targets,
        reducer="umap",
        seed=args.seed,
        n_neighbors=args.umap_neighbors,
        min_dist=args.umap_min_dist,
        umap_a=args.umap_a,
        umap_b=args.umap_b,
    )
    embedding_df = pd.concat([expression_emb, jepa_emb], ignore_index=True)
    embedding_out = Path(args.embedding_out)
    embedding_out.parent.mkdir(parents=True, exist_ok=True)
    embedding_df.to_csv(embedding_out, index=False)

    if args.targets[0] in embedding_df and args.targets[1] in embedding_df:
        plot_2x2(embedding_df, args.targets[0], args.targets[1], Path(args.figure_out))
        plot_2x2_html(embedding_df, args.targets[0], args.targets[1], Path(args.html_out))

    print(metrics.to_string(index=False))
    print(f"Wrote {metrics_out}")
    print(f"Wrote {embedding_out}")
    print(f"Wrote {args.figure_out}")
    print(f"Wrote {args.html_out}")


if __name__ == "__main__":
    main()
