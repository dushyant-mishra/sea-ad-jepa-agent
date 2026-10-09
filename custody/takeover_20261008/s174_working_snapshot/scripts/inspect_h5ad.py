from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a SEA-AD AnnData file without loading the full matrix.")
    parser.add_argument("--h5ad", required=True, help="Path to an .h5ad file.")
    parser.add_argument("--out-dir", default="results/inspection", help="Directory for inspection CSV outputs.")
    args = parser.parse_args()

    h5ad_path = Path(args.h5ad)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(h5ad_path, backed="r")

    print(f"File: {h5ad_path}")
    print(f"Shape: {adata.n_obs:,} cells x {adata.n_vars:,} genes/features")
    print("\nobs columns:")
    for col in adata.obs.columns:
        print(f"  - {col}")

    pd.DataFrame({"obs_column": list(adata.obs.columns)}).to_csv(out_dir / "obs_columns.csv", index=False)
    pd.DataFrame({"var_column": list(adata.var.columns)}).to_csv(out_dir / "var_columns.csv", index=False)
    adata.obs.head(50).to_csv(out_dir / "obs_head.csv")
    adata.var.head(50).to_csv(out_dir / "var_head.csv")

    candidate_terms = ("donor", "subject", "specimen", "region", "cell", "class", "subclass", "type", "braak", "adnc")
    print("\nLikely useful obs columns:")
    for col in adata.obs.columns:
        lowered = col.lower()
        if any(term in lowered for term in candidate_terms):
            print(f"  - {col}")

    print(f"\nWrote inspection files to {out_dir}")
    adata.file.close()


if __name__ == "__main__":
    main()

