from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def short_label(label: str) -> str:
    replacements = {
        "percent ": "",
        " positive area_Grey matter": "",
        "number of ": "n ",
        " positive objects per area_Grey matter": " obj/area",
        " positive cells per area_Grey matter": " cells/area",
        " activated Iba1 positive cells_Grey matter": "activated Iba1 cells",
        "_Grey matter": "",
    }
    out = label
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot SEA-AD donor-level pathology target summaries.")
    parser.add_argument(
        "--targets",
        default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv",
        help="Joined donor/pathology target CSV.",
    )
    parser.add_argument(
        "--target-columns",
        default="data/processed/metadata/pathology_target_columns.csv",
        help="CSV containing target_column values.",
    )
    parser.add_argument("--out-dir", default="results/figures/metadata", help="Output figure directory.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.targets)
    target_cols = pd.read_csv(args.target_columns)["target_column"].tolist()
    numeric = df[target_cols].apply(pd.to_numeric, errors="coerce")

    corr = numeric.corr(method="spearman")
    labels = [short_label(col) for col in corr.columns]

    fig, ax = plt.subplots(figsize=(11, 9))
    image = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(range(len(labels)), labels=labels, rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels=labels, fontsize=8)
    ax.set_title("SEA-AD MTG Pathology Target Spearman Correlation")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_dir / "pathology_target_spearman_corr.png", dpi=200)
    plt.close(fig)

    selected = [
        "percent 6e10 positive area_Grey matter",
        "percent AT8 positive area_Grey matter",
        "percent GFAP positive area_Grey matter",
        "percent Iba1 positive area_Grey matter",
        "percent NeuN positive area_Grey matter",
    ]
    selected = [col for col in selected if col in numeric.columns]

    fig, axes = plt.subplots(len(selected), 1, figsize=(8, 2.2 * len(selected)), sharex=False)
    if len(selected) == 1:
        axes = [axes]
    for ax, col in zip(axes, selected):
        ax.hist(numeric[col].dropna(), bins=18, color="#4c78a8", alpha=0.85)
        ax.set_title(short_label(col), fontsize=10)
        ax.set_ylabel("donors")
    axes[-1].set_xlabel("target value")
    fig.tight_layout()
    fig.savefig(out_dir / "key_pathology_target_histograms.png", dpi=200)
    plt.close(fig)

    print(f"Wrote figures to {out_dir}")


if __name__ == "__main__":
    main()

