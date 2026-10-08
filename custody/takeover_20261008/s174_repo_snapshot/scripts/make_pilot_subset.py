from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import anndata as ad
import scanpy as sc


def parse_values(values: str) -> set[str]:
    return {value.strip() for value in values.split(",") if value.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a manageable SEA-AD pilot AnnData subset.")
    parser.add_argument("--h5ad", required=True, help="Input .h5ad file.")
    parser.add_argument("--out", required=True, help="Output pilot .h5ad file.")
    parser.add_argument("--cell-type-column", default="", help="obs column used for cell-type filtering.")
    parser.add_argument("--cell-type-values", default="", help="Comma-separated values to keep.")
    parser.add_argument("--region-column", default="", help="obs column used for region filtering.")
    parser.add_argument("--region-values", default="", help="Comma-separated region values to keep.")
    parser.add_argument("--max-cells", type=int, default=50000, help="Maximum cells to keep after filtering.")
    parser.add_argument("--n-top-genes", type=int, default=3000, help="Highly variable genes to keep.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for downsampling.")
    args = parser.parse_args()

    in_path = Path(args.h5ad)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Opening {in_path} in backed mode")
    backed = ad.read_h5ad(in_path, backed="r")
    print(f"Initial shape: {backed.n_obs:,} cells x {backed.n_vars:,} genes/features")

    keep_mask = np.ones(backed.n_obs, dtype=bool)

    if args.cell_type_column and args.cell_type_values:
        keep = parse_values(args.cell_type_values)
        if args.cell_type_column not in backed.obs:
            raise KeyError(f"Column not found in obs: {args.cell_type_column}")
        keep_mask &= backed.obs[args.cell_type_column].astype(str).isin(keep).to_numpy()
        print(f"After cell-type filter: {keep_mask.sum():,} cells")

    if args.region_column and args.region_values:
        keep = parse_values(args.region_values)
        if args.region_column not in backed.obs:
            raise KeyError(f"Column not found in obs: {args.region_column}")
        keep_mask &= backed.obs[args.region_column].astype(str).isin(keep).to_numpy()
        print(f"After region filter: {keep_mask.sum():,} cells")

    selected_idx = np.flatnonzero(keep_mask)
    if args.max_cells and selected_idx.size > args.max_cells:
        rng = np.random.default_rng(args.seed)
        selected_idx = np.sort(rng.choice(selected_idx, size=args.max_cells, replace=False))
        print(f"After downsampling: {selected_idx.size:,} cells")

    print("Loading selected cells into memory")
    adata = backed[selected_idx, :].to_memory()
    backed.file.close()
    print(f"Loaded subset: {adata.n_obs:,} cells x {adata.n_vars:,} genes/features")

    if args.n_top_genes and args.n_top_genes < adata.n_vars:
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)
        sc.pp.highly_variable_genes(adata, n_top_genes=args.n_top_genes, flavor="seurat")
        adata = adata[:, adata.var["highly_variable"]].copy()
        print(f"After HVG selection: {adata.n_obs:,} cells x {adata.n_vars:,} genes/features")

    adata.write_h5ad(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
