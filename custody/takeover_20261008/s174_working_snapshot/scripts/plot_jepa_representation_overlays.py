from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sea_ad_jepa.data import normalize_donor_id


DEFAULT_PANELS = [
    ("jepa_34", "jepa_34: dominant homeostatic / vascular axis"),
    ("jepa_46", "jepa_46: complement / synapse-pruning axis"),
    ("jepa_108", "jepa_108: homeostatic / synapse-pruning axis"),
    ("jepa_63", "jepa_63: AT8-linked complement axis"),
    ("percent AT8 positive area_Grey matter", "AT8 / pTau pathology"),
    ("percent NeuN positive area_Grey matter", "NeuN neuronal marker"),
]


def normalize01(values: np.ndarray) -> np.ndarray:
    values = values.astype(float)
    finite = np.isfinite(values)
    out = np.full(values.shape, np.nan, dtype=float)
    if finite.sum() == 0:
        return np.full(values.shape, 0.5, dtype=float)
    lo = float(np.nanmin(values[finite]))
    hi = float(np.nanmax(values[finite]))
    if hi <= lo:
        out[finite] = 0.5
    else:
        out[finite] = (values[finite] - lo) / (hi - lo)
    return out


def color_for_value(value: float) -> str:
    if not np.isfinite(value):
        return "#c7ced8"
    t = float(np.clip(value, 0.0, 1.0))
    # Blue -> light neutral -> red. This works on a white exported SVG and in dark-theme docs.
    if t < 0.5:
        u = t / 0.5
        r = int(40 + u * (238 - 40))
        g = int(95 + u * (242 - 95))
        b = int(170 + u * (247 - 170))
    else:
        u = (t - 0.5) / 0.5
        r = int(238 + u * (196 - 238))
        g = int(242 + u * (55 - 242))
        b = int(247 + u * (59 - 247))
    return f"rgb({r},{g},{b})"


def scale(values: np.ndarray, out_min: float, out_max: float) -> np.ndarray:
    finite = np.isfinite(values)
    if finite.sum() == 0:
        return np.full(values.shape, (out_min + out_max) / 2.0)
    lo = float(np.nanmin(values[finite]))
    hi = float(np.nanmax(values[finite]))
    if hi <= lo:
        return np.full(values.shape, (out_min + out_max) / 2.0)
    return out_min + (values - lo) * (out_max - out_min) / (hi - lo)


def metric_lookup(metrics: pd.DataFrame, latent: str) -> str:
    sub = metrics[(metrics["representation"].eq("jepa_latent_umap")) & (metrics["latent"].eq(latent))]
    if sub.empty:
        return ""
    row = sub.iloc[0]
    return f"R2={row['linear_xy_to_latent_r2']:.3f}, rho_y={row['spearman_y']:+.3f}"


def rank_lookup(rankings: pd.DataFrame, latent: str) -> str:
    sub = rankings[rankings["representation"].eq("jepa_latent_umap")].copy()
    if sub.empty or latent not in set(sub["latent_factor"]):
        return ""
    sub = sub.sort_values("r2_explained_by_2d", ascending=False).reset_index(drop=True)
    row = sub[sub["latent_factor"].eq(latent)].iloc[0]
    rank = int(sub.index[sub["latent_factor"].eq(latent)][0] + 1)
    return f"rank {rank}/128, R2={row['r2_explained_by_2d']:.3f}"


def write_svg(plot_df: pd.DataFrame, metrics: pd.DataFrame, rankings: pd.DataFrame, panels: list[tuple[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1500, 1120
    panel_w, panel_h = 400, 270
    margin_x, margin_y = 70, 145
    gap_x, gap_y = 70, 115
    xs = scale(plot_df["x"].to_numpy(dtype=float), 0, 1)
    ys = scale(plot_df["y"].to_numpy(dtype=float), 1, 0)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f8fb"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172033}.title{font-size:28px;font-weight:700}.subtitle{font-size:15px;fill:#5c6878}.paneltitle{font-size:15px;font-weight:700}.note{font-size:12px;fill:#5c6878}.metric{font-size:12px;fill:#2b3545}</style>',
        '<text x="70" y="52" class="title">JEPA Donor Representation Map</text>',
        '<text x="70" y="80" class="subtitle">One shared JEPA UMAP coordinate system. Color overlays show dominant latent axes, the AT8-linked jepa_63 axis, and observed pathology labels.</text>',
        '<text x="70" y="105" class="subtitle">Interpretation boundary: this visualizes learned representation geometry; it does not prove biological causality.</text>',
    ]

    for i, (column, title) in enumerate(panels):
        col = i % 3
        row = i // 3
        left = margin_x + col * (panel_w + gap_x)
        top = margin_y + row * (panel_h + gap_y)
        values = plot_df[column].to_numpy(dtype=float)
        colors = normalize01(values)
        px = left + 22 + xs * (panel_w - 44)
        py = top + 22 + ys * (panel_h - 44)
        metric = rank_lookup(rankings, column) if column.startswith("jepa_") else metric_lookup(metrics, column)

        svg.append(f'<rect x="{left}" y="{top}" width="{panel_w}" height="{panel_h}" rx="8" fill="#ffffff" stroke="#d8dee8"/>')
        svg.append(f'<text x="{left}" y="{top - 28}" class="paneltitle">{title}</text>')
        if metric:
            svg.append(f'<text x="{left}" y="{top - 10}" class="metric">{metric}</text>')
        for x, y, c in zip(px, py, colors):
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.3" fill="{color_for_value(c)}" fill-opacity="0.92" stroke="#ffffff" stroke-width="0.8"/>')
        # Tiny color strip per panel.
        legend_y = top + panel_h + 15
        for j in range(60):
            c = j / 59
            svg.append(f'<rect x="{left + j * 3}" y="{legend_y}" width="3" height="10" fill="{color_for_value(c)}"/>')
        svg.append(f'<text x="{left}" y="{legend_y + 28}" class="note">low</text>')
        svg.append(f'<text x="{left + 148}" y="{legend_y + 28}" class="note">high</text>')

    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


def write_summary(plot_df: pd.DataFrame, metrics: pd.DataFrame, rankings: pd.DataFrame, panels: list[tuple[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# JEPA Representation Overlay Summary",
        "",
        "This figure maps donor-level JEPA embeddings in one shared 2D UMAP coordinate system and overlays latent dimensions or pathology labels as colors.",
        "",
        "The goal is visualization with guardrails: dominant UMAP axes are not automatically causal axes, and pathology-colored structure is not proof of perturbational causality.",
        "",
        "## Panels",
        "",
        "| Panel | What it shows | Quantitative note |",
        "|---|---|---|",
    ]
    for column, title in panels:
        note = rank_lookup(rankings, column) if column.startswith("jepa_") else metric_lookup(metrics, column)
        lines.append(f"| `{column}` | {title} | {note} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The visible JEPA UMAP is driven mainly by broad microglial state axes such as homeostatic, vascular/barrier, complement, and synapse-pruning programs.",
            "- `jepa_63` is included as an AT8-linked complement/antigen-presentation/synapse-pruning hypothesis axis, but it is not the main UMAP-shaping axis.",
            "- AT8 and NeuN overlays test whether observed pathology labels occupy coherent regions of the learned manifold; they should be interpreted together with the quantitative R2 and Spearman metrics.",
            "",
            f"Donors plotted: {plot_df['Donor ID'].nunique()}",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot JEPA donor UMAP overlays for latent axes and pathology labels.")
    parser.add_argument("--umap", default="results/tables/latent_space_umap_coordinates.csv")
    parser.add_argument("--embeddings", default="results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv")
    parser.add_argument("--metrics", default="results/tables/jepa63_umap_alignment_metrics.csv")
    parser.add_argument("--rankings", default="results/tables/all_jepa_umap_variance_rankings.csv")
    parser.add_argument("--figure-out", default="results/figures/jepa_representation_overlays.svg")
    parser.add_argument("--plot-data-out", default="results/tables/jepa_representation_overlay_plot_data.csv")
    parser.add_argument("--summary-out", default="results/reports/jepa_representation_overlays.md")
    args = parser.parse_args()

    umap_df = pd.read_csv(args.umap)
    embeddings = pd.read_csv(args.embeddings)
    metrics = pd.read_csv(args.metrics)
    rankings = pd.read_csv(args.rankings)
    for df in (umap_df, embeddings):
        if "Donor ID" not in df:
            raise KeyError("Expected a Donor ID column.")
        df["Donor ID"] = normalize_donor_id(df["Donor ID"])

    jepa_umap = umap_df[umap_df["representation"].eq("jepa_latent_umap")].copy()
    needed_latents = [column for column, _ in DEFAULT_PANELS if column.startswith("jepa_")]
    plot_df = jepa_umap.merge(embeddings[["Donor ID", *needed_latents]], on="Donor ID", how="inner")
    missing = [column for column, _ in DEFAULT_PANELS if column not in plot_df]
    if missing:
        raise KeyError(f"Missing columns for overlay plotting: {missing}")

    Path(args.plot_data_out).parent.mkdir(parents=True, exist_ok=True)
    plot_df.to_csv(args.plot_data_out, index=False)
    write_svg(plot_df, metrics, rankings, DEFAULT_PANELS, Path(args.figure_out))
    write_summary(plot_df, metrics, rankings, DEFAULT_PANELS, Path(args.summary_out))

    print(f"Wrote {args.figure_out}")
    print(f"Wrote {args.plot_data_out}")
    print(f"Wrote {args.summary_out}")


if __name__ == "__main__":
    main()
