from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from sea_ad_jepa.baselines import cross_validated_ridge
from sea_ad_jepa.data import load_pathology_targets


def select_top_variable_genes(features: pd.DataFrame, max_genes: int | None) -> pd.DataFrame:
    if max_genes is None or max_genes <= 0:
        return features
    gene_columns = [column for column in features.columns if column != "Donor ID"]
    if len(gene_columns) <= max_genes:
        return features
    variances = features[gene_columns].var(axis=0).sort_values(ascending=False)
    keep = variances.head(max_genes).index.tolist()
    return features[["Donor ID", *keep]].copy()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run donor-level ridge baselines from pseudobulk CSV features.")
    parser.add_argument("--features", required=True, help="Pseudobulk CSV with Donor ID plus gene columns.")
    parser.add_argument("--out", default="results/tables/microglia_pvm_pseudobulk_ridge.csv")
    parser.add_argument("--max-genes", type=int, default=1000)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    features = pd.read_csv(args.features)
    features = select_top_variable_genes(features, args.max_genes)
    targets, target_columns = load_pathology_targets()
    results = cross_validated_ridge(features, targets, target_columns, device=args.device)
    results.to_csv(out_path, index=False)
    print(results.to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

