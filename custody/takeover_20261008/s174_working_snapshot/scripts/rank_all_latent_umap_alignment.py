from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sea_ad_jepa.data import normalize_donor_id


def pearson_corr(x: np.ndarray, y: np.ndarray) -> float:
    keep = np.isfinite(x) & np.isfinite(y)
    if keep.sum() < 3:
        return float("nan")
    x = x[keep] - np.nanmean(x[keep])
    y = y[keep] - np.nanmean(y[keep])
    denom = float(np.sqrt(np.sum(x * x) * np.sum(y * y)))
    return float(np.sum(x * y) / denom) if denom > 0 else float("nan")


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.shape[0], dtype=float)
    sorted_values = values[order]
    i = 0
    while i < values.shape[0]:
        j = i + 1
        while j < values.shape[0] and sorted_values[j] == sorted_values[i]:
            j += 1
        ranks[order[i:j]] = (i + j - 1) / 2.0
        i = j
    return ranks


def spearman_corr(x: np.ndarray, y: np.ndarray) -> float:
    keep = np.isfinite(x) & np.isfinite(y)
    if keep.sum() < 3:
        return float("nan")
    return pearson_corr(rankdata(x[keep]), rankdata(y[keep]))


def linear_r2(x: np.ndarray, y: np.ndarray) -> float:
    keep = np.isfinite(x).all(axis=1) & np.isfinite(y)
    if keep.sum() < x.shape[1] + 2:
        return float("nan")
    x = x[keep]
    y = y[keep]
    design = np.column_stack([np.ones(x.shape[0]), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    pred = design @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def summarize_annotations(annotations: pd.DataFrame, latent_id: int, top_n: int) -> str:
    if annotations.empty:
        return ""
    sub = annotations[annotations["latent_dim"].eq(latent_id)].sort_values("abs_correlation", ascending=False).head(top_n)
    return "; ".join(f"{row.module} ({row.correlation:+.2f})" for row in sub.itertuples(index=False))


def load_annotations(path: str | None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def rank_latents(
    umap_df: pd.DataFrame,
    embeddings: pd.DataFrame,
    annotations: pd.DataFrame,
    representation: str,
    top_annotations: int,
) -> pd.DataFrame:
    latent_cols = [c for c in embeddings.columns if c.startswith("jepa_")]
    if not latent_cols:
        raise ValueError("No jepa_* columns found in embedding table.")

    sub_umap = umap_df[umap_df["representation"].eq(representation)].copy()
    merged = sub_umap[["Donor ID", "x", "y"]].merge(embeddings[["Donor ID", *latent_cols]], on="Donor ID", how="inner")
    if merged.empty:
        raise ValueError(f"No overlapping donors for representation: {representation}")

    xy = merged[["x", "y"]].to_numpy(dtype=float)
    rows = []
    for col in latent_cols:
        latent_id = int(col.split("_", 1)[1])
        y = merged[col].to_numpy(dtype=float)
        rows.append(
            {
                "representation": representation,
                "latent_factor": col,
                "latent_id": latent_id,
                "n_donors": int(np.isfinite(y).sum()),
                "r2_explained_by_2d": linear_r2(xy, y),
                "spearman_umap_x": spearman_corr(merged["x"].to_numpy(dtype=float), y),
                "spearman_umap_y": spearman_corr(merged["y"].to_numpy(dtype=float), y),
                "pearson_umap_x": pearson_corr(merged["x"].to_numpy(dtype=float), y),
                "pearson_umap_y": pearson_corr(merged["y"].to_numpy(dtype=float), y),
                "top_module_annotations": summarize_annotations(annotations, latent_id, top_annotations),
            }
        )
    return pd.DataFrame(rows).sort_values("r2_explained_by_2d", ascending=False)


def write_summary(rankings: pd.DataFrame, out_path: Path, focus_latent: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# All-Latent UMAP Alignment Summary", ""]
    for rep, sub in rankings.groupby("representation", sort=False):
        ordered = sub.sort_values("r2_explained_by_2d", ascending=False).reset_index(drop=True)
        focus = ordered[ordered["latent_factor"].eq(focus_latent)]
        focus_rank = int(focus.index[0] + 1) if not focus.empty else None
        focus_r2 = float(focus["r2_explained_by_2d"].iloc[0]) if not focus.empty else float("nan")
        lines.append(f"## {rep}")
        lines.append("")
        lines.append(f"- Top latent R2: {ordered['r2_explained_by_2d'].iloc[0]:.3f}")
        lines.append(f"- Median latent R2: {ordered['r2_explained_by_2d'].median():.3f}")
        lines.append(f"- {focus_latent} rank: {focus_rank} of {ordered.shape[0]} latents")
        lines.append(f"- {focus_latent} R2: {focus_r2:.3f}")
        lines.append("")
        lines.append("| Rank | Latent | R2 from 2D UMAP | Spearman x | Spearman y | Top module annotations |")
        lines.append("|---:|---|---:|---:|---:|---|")
        for rank, row in enumerate(ordered.head(12).itertuples(index=False), start=1):
            lines.append(
                f"| {rank} | {row.latent_factor} | {row.r2_explained_by_2d:.3f} | {row.spearman_umap_x:+.3f} | {row.spearman_umap_y:+.3f} | {row.top_module_annotations} |"
            )
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank every JEPA latent dimension by alignment with donor-level UMAP geometry.")
    parser.add_argument("--umap", default="results/tables/latent_space_umap_coordinates.csv")
    parser.add_argument("--embeddings", default="results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv")
    parser.add_argument("--annotations", default="results/tables/latent_jacobian_ema_var_e30_module_annotations.csv")
    parser.add_argument("--representations", nargs="+", default=["jepa_latent_umap", "expression_pca_umap"])
    parser.add_argument("--top-annotations", type=int, default=3)
    parser.add_argument("--focus-latent", default="jepa_63")
    parser.add_argument("--out", default="results/tables/all_jepa_umap_variance_rankings.csv")
    parser.add_argument("--summary-out", default="results/reports/all_jepa_umap_variance_rankings.md")
    args = parser.parse_args()

    umap_df = pd.read_csv(args.umap)
    embeddings = pd.read_csv(args.embeddings)
    annotations = load_annotations(args.annotations)
    for df in (umap_df, embeddings):
        if "Donor ID" not in df:
            raise KeyError("Expected a Donor ID column.")
        df["Donor ID"] = normalize_donor_id(df["Donor ID"])

    rankings = pd.concat(
        [
            rank_latents(
                umap_df=umap_df,
                embeddings=embeddings,
                annotations=annotations,
                representation=representation,
                top_annotations=args.top_annotations,
            )
            for representation in args.representations
        ],
        ignore_index=True,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    rankings.to_csv(args.out, index=False)
    write_summary(rankings, Path(args.summary_out), args.focus_latent)

    print(f"Wrote {args.out}")
    print(f"Wrote {args.summary_out}")
    for representation in args.representations:
        sub = rankings[rankings["representation"].eq(representation)].sort_values("r2_explained_by_2d", ascending=False)
        focus = sub[sub["latent_factor"].eq(args.focus_latent)].reset_index(drop=True)
        focus_rank = int(sub.reset_index(drop=True).index[sub.reset_index(drop=True)["latent_factor"].eq(args.focus_latent)][0] + 1)
        print(f"\n{representation}")
        print(sub.head(8)[["latent_factor", "r2_explained_by_2d", "spearman_umap_x", "spearman_umap_y", "top_module_annotations"]].to_string(index=False))
        if not focus.empty:
            print(f"{args.focus_latent} rank: {focus_rank} / {sub.shape[0]}")


if __name__ == "__main__":
    main()
