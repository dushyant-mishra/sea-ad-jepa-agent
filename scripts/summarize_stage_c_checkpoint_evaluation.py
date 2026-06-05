from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_EPOCHS = ["005", "010", "015", "020"]
FOCUS_TARGETS = [
    "percent AT8 positive area_Grey matter",
    "percent NeuN positive area_Grey matter",
    "percent 6e10 positive area_Grey matter",
    "percent GFAP positive area_Grey matter",
    "percent Iba1 positive area_Grey matter",
]


def read_epoch_table(pattern: str, epoch: str) -> pd.DataFrame:
    path = Path(pattern.format(epoch=epoch))
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Stage C epoch checkpoint pathology and geometry evaluations.")
    parser.add_argument("--epochs", nargs="+", default=DEFAULT_EPOCHS)
    parser.add_argument("--ridge-pattern", default="results/tables/stage_c_epoch_{epoch}_donor_embedding_ridge_pathology.csv")
    parser.add_argument("--ridge-epoch20", default="results/tables/stage_c_rehearsal_donor_embedding_ridge_pathology.csv")
    parser.add_argument("--geometry-pattern", default="results/tables/stage_c_epoch_{epoch}_latent_space_evaluation_metrics.csv")
    parser.add_argument("--geometry-epoch20", default="results/tables/stage_c_latent_space_evaluation_metrics.csv")
    parser.add_argument("--out", default="results/tables/stage_c_checkpoint_evaluation_summary.csv")
    args = parser.parse_args()

    rows = []
    for epoch in args.epochs:
        ridge = pd.read_csv(args.ridge_epoch20) if epoch == "020" else read_epoch_table(args.ridge_pattern, epoch)
        geometry = pd.read_csv(args.geometry_epoch20) if epoch == "020" else read_epoch_table(args.geometry_pattern, epoch)
        jepa_geometry = geometry[geometry["representation"].eq("jepa_latent_128")].copy()
        pca_geometry = geometry[geometry["representation"].eq("expression_pca_128")].copy()
        pca_lookup = pca_geometry.set_index("target")["knn_spearman"].to_dict()

        for target in FOCUS_TARGETS:
            ridge_sub = ridge[ridge["target"].eq(target)]
            geom_sub = jepa_geometry[jepa_geometry["target"].eq(target)]
            rows.append(
                {
                    "checkpoint_epoch": epoch,
                    "target": target,
                    "ridge_spearman": float(ridge_sub["spearman"].iloc[0]) if not ridge_sub.empty else float("nan"),
                    "jepa_knn_spearman": float(geom_sub["knn_spearman"].iloc[0]) if not geom_sub.empty else float("nan"),
                    "pca_knn_spearman": float(pca_lookup.get(target, float("nan"))),
                    "jepa_minus_pca_knn_spearman": (
                        float(geom_sub["knn_spearman"].iloc[0]) - float(pca_lookup[target])
                        if (not geom_sub.empty and target in pca_lookup)
                        else float("nan")
                    ),
                }
            )

    out = pd.DataFrame(rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(out.to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
