from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from make_pilot_subset_fast import decode, decode_column, read_var_names


def read_csr_row_range(handle: h5py.File, start_row: int, n_rows: int) -> csr_matrix:
    x = handle["X"]
    shape = tuple(int(v) for v in x.attrs["shape"])
    end_row = min(start_row + n_rows, shape[0])
    indptr = x["indptr"][start_row : end_row + 1]
    data_start = int(indptr[0])
    data_end = int(indptr[-1])
    data = x["data"][data_start:data_end]
    indices = x["indices"][data_start:data_end]
    new_indptr = indptr - data_start
    return csr_matrix((data, indices, new_indptr), shape=(end_row - start_row, shape[1]))


def normalize_log_hvg(adata: ad.AnnData, n_top_genes: int) -> ad.AnnData:
    x = adata.X.tocsr(copy=True)
    row_sums = np.asarray(x.sum(axis=1)).ravel()
    row_sums[row_sums == 0] = 1.0
    scale = 1e4 / row_sums
    x = x.multiply(scale[:, None]).tocsr()
    x.data = np.log1p(x.data)

    mean = np.asarray(x.mean(axis=0)).ravel()
    mean_sq = np.asarray(x.power(2).mean(axis=0)).ravel()
    variance = mean_sq - mean**2
    top_idx = np.argsort(variance)[-n_top_genes:]
    top_idx.sort()

    adata = adata[:, top_idx].copy()
    adata.X = x[:, top_idx].copy()
    adata.var["highly_variable"] = True
    return adata


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a fast contiguous pilot slice from a large SEA-AD H5AD.")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--start-row", type=int, default=316988)
    parser.add_argument("--n-rows", type=int, default=10000)
    parser.add_argument("--n-top-genes", type=int, default=3000)
    parser.add_argument(
        "--obs-columns",
        nargs="+",
        default=[
            "Donor ID",
            "Brain Region",
            "Class",
            "Subclass",
            "Supertype",
            "Continuous Pseudo-progression Score",
            "Cognitive Status",
            "Braak",
            "Thal",
            "Overall AD neuropathological Change",
            "APOE Genotype",
            "Age at Death",
            "Sex",
        ],
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(args.h5ad, "r") as handle:
        x_subset = read_csr_row_range(handle, args.start_row, args.n_rows)
        selected_idx = list(range(args.start_row, args.start_row + x_subset.shape[0]))
        obs = pd.DataFrame(index=[f"cell_{i}" for i in selected_idx])
        for column in args.obs_columns:
            if column in handle["obs"]:
                obs[column] = decode_column(handle, column, selected_idx)

        var_names = read_var_names(handle)
        var = pd.DataFrame(index=var_names)
        if "gene_ids" in handle["var"]:
            var["gene_ids"] = [decode(value) for value in handle["var"]["gene_ids"][:]]

    adata = ad.AnnData(X=x_subset, obs=obs, var=var)
    print(f"Initial slice: {adata.n_obs:,} cells x {adata.n_vars:,} genes")
    print(adata.obs["Subclass"].value_counts().head(10).to_string())

    if args.n_top_genes and args.n_top_genes < adata.n_vars:
        adata = normalize_log_hvg(adata, args.n_top_genes)
        print(f"After HVG selection: {adata.n_obs:,} cells x {adata.n_vars:,} genes")

    adata.write_h5ad(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
