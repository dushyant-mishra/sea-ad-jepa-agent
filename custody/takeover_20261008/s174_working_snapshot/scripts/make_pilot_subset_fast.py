from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


def decode(value) -> str:
    if isinstance(value, bytes):
        return value.decode()
    return str(value)


def read_categorical(handle: h5py.File, column: str) -> tuple[np.ndarray, list[str] | None]:
    ds = handle["obs"][column]
    values = ds[:]
    category_ref = ds.attrs.get("categories")
    if not category_ref:
        return np.asarray([decode(value) for value in values]), None
    categories = [decode(value) for value in handle[category_ref][:]]
    return values.astype(np.int64), categories


def decode_column(handle: h5py.File, column: str, selected_idx: np.ndarray) -> list[str]:
    values, categories = read_categorical(handle, column)
    selected = values[selected_idx]
    if categories is None:
        return [decode(value) for value in selected]
    return [categories[int(code)] if int(code) >= 0 else "NA" for code in selected]


def read_var_names(handle: h5py.File) -> list[str]:
    if "_index" in handle["var"]:
        return [decode(value) for value in handle["var"]["_index"][:]]
    if "gene_ids" in handle["var"]:
        return [decode(value) for value in handle["var"]["gene_ids"][:]]
    n_vars = int(handle["X"].attrs["shape"][1])
    return [f"gene_{i}" for i in range(n_vars)]


def subset_csr_rows(handle: h5py.File, row_idx: np.ndarray, row_block_size: int = 20000) -> csr_matrix:
    x = handle["X"]
    shape = tuple(int(v) for v in x.attrs["shape"])
    indptr = x["indptr"][:]
    row_idx = np.asarray(row_idx, dtype=np.int64)

    new_indptr = np.zeros(row_idx.size + 1, dtype=np.int64)
    data_parts = []
    index_parts = []
    cursor = 0

    out_row = 0
    min_row = int(row_idx.min())
    max_row = int(row_idx.max())

    for block_start in range(min_row, max_row + 1, row_block_size):
        block_end = min(block_start + row_block_size, max_row + 1)
        in_block = row_idx[(row_idx >= block_start) & (row_idx < block_end)]
        if in_block.size == 0:
            continue

        data_start = int(indptr[block_start])
        data_end = int(indptr[block_end])
        block_data = x["data"][data_start:data_end]
        block_indices = x["indices"][data_start:data_end].astype(np.int32, copy=False)

        for row in in_block:
            start = int(indptr[row] - data_start)
            end = int(indptr[row + 1] - data_start)
            data_parts.append(block_data[start:end])
            index_parts.append(block_indices[start:end])
            cursor += end - start
            out_row += 1
            new_indptr[out_row] = cursor

    data_concat = np.concatenate(data_parts).astype(np.float32, copy=False)
    indices_concat = np.concatenate(index_parts).astype(np.int32, copy=False)
    return csr_matrix((data_concat, indices_concat, new_indptr), shape=(row_idx.size, shape[1]))


def normalize_log_hvg(adata: ad.AnnData, n_top_genes: int, preserve_genes: set[str] | None = None) -> ad.AnnData:
    x = adata.X.tocsr(copy=True)
    row_sums = np.asarray(x.sum(axis=1)).ravel()
    row_sums[row_sums == 0] = 1.0
    scale = 1e4 / row_sums
    x = x.multiply(scale[:, None]).tocsr()
    x.data = np.log1p(x.data)

    mean = np.asarray(x.mean(axis=0)).ravel()
    mean_sq = np.asarray(x.power(2).mean(axis=0)).ravel()
    variance = mean_sq - mean**2
    preserve_genes = {gene.upper() for gene in (preserve_genes or set())}
    gene_names = [str(gene) for gene in adata.var_names]
    preserve_idx = {idx for idx, gene in enumerate(gene_names) if gene.upper() in preserve_genes}
    n_hvg = max(0, n_top_genes - len(preserve_idx))
    top_idx = set(np.argsort(variance)[-n_hvg:].tolist()) if n_hvg else set()
    top_idx = np.asarray(sorted(top_idx | preserve_idx), dtype=np.int64)

    adata = adata[:, top_idx].copy()
    adata.X = x[:, top_idx].copy()
    adata.var["highly_variable"] = True
    return adata


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast CSR row extraction for SEA-AD H5AD pilot subsets.")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--filter-column", default="Subclass")
    parser.add_argument("--filter-value", default="Microglia-PVM")
    parser.add_argument("--max-cells", type=int, default=10000)
    parser.add_argument("--n-top-genes", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=7)
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
    rng = np.random.default_rng(args.seed)

    with h5py.File(args.h5ad, "r") as handle:
        values, categories = read_categorical(handle, args.filter_column)
        if categories is None:
            keep_mask = values.astype(str) == args.filter_value
        else:
            try:
                code = categories.index(args.filter_value)
            except ValueError as exc:
                raise ValueError(f"{args.filter_value!r} not found in {args.filter_column} categories: {categories}") from exc
            keep_mask = values == code

        selected_idx = np.flatnonzero(keep_mask)
        print(f"Matched cells: {selected_idx.size:,}")
        if args.max_cells and selected_idx.size > args.max_cells:
            selected_idx = np.sort(rng.choice(selected_idx, size=args.max_cells, replace=False))
            print(f"Downsampled cells: {selected_idx.size:,}")

        x_subset = subset_csr_rows(handle, selected_idx)
        obs = pd.DataFrame(index=[f"cell_{i}" for i in selected_idx])
        for column in args.obs_columns:
            if column in handle["obs"]:
                obs[column] = decode_column(handle, column, selected_idx)

        var_names = read_var_names(handle)
        var = pd.DataFrame(index=var_names)
        if "gene_ids" in handle["var"]:
            var["gene_ids"] = [decode(value) for value in handle["var"]["gene_ids"][:]]

    adata = ad.AnnData(X=x_subset, obs=obs, var=var)
    print(f"Initial subset: {adata.n_obs:,} cells x {adata.n_vars:,} genes")

    if args.n_top_genes and args.n_top_genes < adata.n_vars:
        adata = normalize_log_hvg(adata, args.n_top_genes)
        print(f"After HVG selection: {adata.n_obs:,} cells x {adata.n_vars:,} genes")

    adata.write_h5ad(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
