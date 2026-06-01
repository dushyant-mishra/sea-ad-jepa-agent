from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sea_ad_jepa.data import normalize_donor_id


FOCUS_LATENT = "jepa_63"
DEFAULT_TARGETS = [
    "percent AT8 positive area_Grey matter",
    "percent NeuN positive area_Grey matter",
    "percent 6e10 positive area_Grey matter",
    "percent GFAP positive area_Grey matter",
    "percent Iba1 positive area_Grey matter",
]


def pearson_corr(x: np.ndarray, y: np.ndarray) -> float:
    keep = np.isfinite(x) & np.isfinite(y)
    if keep.sum() < 3:
        return float("nan")
    x = x[keep]
    y = y[keep]
    x = x - x.mean()
    y = y - y.mean()
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


def normalize01(values: np.ndarray) -> np.ndarray:
    values = values.astype(float)
    lo = np.nanmin(values)
    hi = np.nanmax(values)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.full(values.shape, 0.5, dtype=float)
    return (values - lo) / (hi - lo)


def color_for_value(value: float) -> str:
    t = float(np.clip(value, 0.0, 1.0))
    # Blue -> pale -> red, chosen to remain legible on a white SVG background.
    if t < 0.5:
        u = t / 0.5
        r = int(47 + u * (238 - 47))
        g = int(107 + u * (242 - 107))
        b = int(183 + u * (247 - 183))
    else:
        u = (t - 0.5) / 0.5
        r = int(238 + u * (196 - 238))
        g = int(242 + u * (55 - 242))
        b = int(247 + u * (59 - 247))
    return f"rgb({r},{g},{b})"


def scale(values: np.ndarray, out_min: float, out_max: float) -> np.ndarray:
    lo = float(np.nanmin(values))
    hi = float(np.nanmax(values))
    if hi <= lo:
        return np.full(values.shape, (out_min + out_max) / 2.0)
    return out_min + (values - lo) * (out_max - out_min) / (hi - lo)


def write_svg(plot_df: pd.DataFrame, out_path: Path, value_col: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    reps = ["expression_pca_umap", "jepa_latent_umap"]
    titles = {
        "expression_pca_umap": "Expression PCA UMAP colored by jepa_63",
        "jepa_latent_umap": "JEPA latent UMAP colored by jepa_63",
    }
    width, height = 1280, 560
    panel_w, panel_h = 500, 360
    lefts = [90, 720]
    top = 105
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f8fb"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172033}.title{font-size:24px;font-weight:700}.label{font-size:15px}.small{font-size:12px;fill:#5f6b7a}</style>',
        '<text x="80" y="48" class="title">Does jepa_63 Explain the UMAP Geometry?</text>',
        '<text x="80" y="74" class="small">Each point is a donor. Color shows donor-level jepa_63 activation from the EMA+variance JEPA embedding.</text>',
    ]
    values01 = normalize01(plot_df[value_col].to_numpy(dtype=float))
    plot_df = plot_df.assign(_value01=values01)
    for left, rep in zip(lefts, reps):
        sub = plot_df[plot_df["representation"].eq(rep)].copy()
        if sub.empty:
            continue
        px = scale(sub["x"].to_numpy(dtype=float), left + 20, left + panel_w - 20)
        py = scale(sub["y"].to_numpy(dtype=float), top + panel_h - 20, top + 20)
        svg.append(f'<rect x="{left}" y="{top}" width="{panel_w}" height="{panel_h}" rx="8" fill="#ffffff" stroke="#d8dee8"/>')
        svg.append(f'<text x="{left}" y="{top - 18}" class="label">{titles[rep]}</text>')
        for x, y, c in zip(px, py, sub["_value01"].to_numpy(dtype=float)):
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.5" fill="{color_for_value(c)}" fill-opacity="0.9" stroke="#ffffff" stroke-width="0.8"/>')
    # Simple legend
    legend_x, legend_y = 515, 500
    for i in range(80):
        c = i / 79
        svg.append(f'<rect x="{legend_x + i * 3}" y="{legend_y}" width="3" height="14" fill="{color_for_value(c)}"/>')
    svg.append(f'<text x="{legend_x}" y="{legend_y + 34}" class="small">low jepa_63</text>')
    svg.append(f'<text x="{legend_x + 170}" y="{legend_y + 34}" class="small">high jepa_63</text>')
    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Quantify whether jepa_63 aligns with donor-level UMAP geometry.")
    parser.add_argument("--umap", default="results/tables/latent_space_umap_coordinates.csv")
    parser.add_argument("--embeddings", default="results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv")
    parser.add_argument("--latent", default=FOCUS_LATENT)
    parser.add_argument("--metrics-out", default="results/tables/jepa63_umap_alignment_metrics.csv")
    parser.add_argument("--plot-data-out", default="results/tables/jepa63_umap_alignment_plot_data.csv")
    parser.add_argument("--figure-out", default="results/figures/jepa63_umap_alignment.svg")
    args = parser.parse_args()

    umap_df = pd.read_csv(args.umap)
    emb = pd.read_csv(args.embeddings)
    if args.latent not in emb:
        raise KeyError(f"{args.latent} was not found in {args.embeddings}")
    for df in (umap_df, emb):
        if "Donor ID" not in df:
            raise KeyError("Expected a Donor ID column.")
        df["Donor ID"] = normalize_donor_id(df["Donor ID"])

    plot_df = umap_df.merge(emb[["Donor ID", args.latent]], on="Donor ID", how="inner")
    rows = []
    for rep, sub in plot_df.groupby("representation"):
        latent = sub[args.latent].to_numpy(dtype=float)
        xy = sub[["x", "y"]].to_numpy(dtype=float)
        rows.append(
            {
                "representation": rep,
                "n_donors": int(sub.shape[0]),
                "latent": args.latent,
                "pearson_x": pearson_corr(sub["x"].to_numpy(dtype=float), latent),
                "pearson_y": pearson_corr(sub["y"].to_numpy(dtype=float), latent),
                "spearman_x": spearman_corr(sub["x"].to_numpy(dtype=float), latent),
                "spearman_y": spearman_corr(sub["y"].to_numpy(dtype=float), latent),
                "linear_xy_to_latent_r2": linear_r2(xy, latent),
            }
        )
        for target in DEFAULT_TARGETS:
            if target in sub:
                y = pd.to_numeric(sub[target], errors="coerce").to_numpy(dtype=float)
                rows.append(
                    {
                        "representation": rep,
                        "n_donors": int(np.isfinite(y).sum()),
                        "latent": target,
                        "pearson_x": pearson_corr(sub["x"].to_numpy(dtype=float), y),
                        "pearson_y": pearson_corr(sub["y"].to_numpy(dtype=float), y),
                        "spearman_x": spearman_corr(sub["x"].to_numpy(dtype=float), y),
                        "spearman_y": spearman_corr(sub["y"].to_numpy(dtype=float), y),
                        "linear_xy_to_latent_r2": linear_r2(xy, y),
                    }
                )

    metrics = pd.DataFrame(rows)
    Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.metrics_out, index=False)
    plot_df.to_csv(args.plot_data_out, index=False)
    write_svg(plot_df, Path(args.figure_out), args.latent)

    print(f"Wrote {args.metrics_out}")
    print(f"Wrote {args.plot_data_out}")
    print(f"Wrote {args.figure_out}")
    print(metrics[metrics["latent"].eq(args.latent)].to_string(index=False))


if __name__ == "__main__":
    main()
