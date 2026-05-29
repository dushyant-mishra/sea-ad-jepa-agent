from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from make_pilot_subset_fast import decode, decode_column, normalize_log_hvg, read_categorical, read_var_names


DEFAULT_OBS_COLUMNS = [
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
]


def choose_cell_indices(selected_idx: np.ndarray, max_cells: int | None, seed: int) -> np.ndarray:
    if max_cells is None or max_cells <= 0 or selected_idx.size <= max_cells:
        return selected_idx
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(selected_idx, size=max_cells, replace=False))


def build_outputs(
    h5ad_path: Path,
    filter_column: str,
    filter_value: str,
    cell_max: int,
    seed: int,
    row_block_size: int,
    n_top_genes: int,
    pilot_out: Path,
    pseudobulk_out: Path,
    counts_out: Path,
    obs_columns: list[str],
) -> None:
    with h5py.File(h5ad_path, "r") as handle:
        x = handle["X"]
        n_cells, n_genes = [int(v) for v in x.attrs["shape"]]
        indptr = x["indptr"][:]

        values, categories = read_categorical(handle, filter_column)
        if categories is None:
            keep_mask = values.astype(str) == filter_value
        else:
            code = categories.index(filter_value)
            keep_mask = values == code

        selected_idx = np.flatnonzero(keep_mask)
        pilot_idx = choose_cell_indices(selected_idx, cell_max, seed)
        pilot_lookup = np.zeros(n_cells, dtype=bool)
        pilot_lookup[pilot_idx] = True

        donor_codes, donor_categories = read_categorical(handle, "Donor ID")
        if donor_categories is None:
            donor_labels = sorted(pd.Series(donor_codes.astype(str)).unique())
            donor_to_row = {donor: i for i, donor in enumerate(donor_labels)}
            donor_row_for_cell = np.asarray([donor_to_row[str(donor)] for donor in donor_codes], dtype=np.int32)
        else:
            donor_labels = donor_categories
            donor_row_for_cell = donor_codes.astype(np.int32)

        sums = np.zeros((len(donor_labels), n_genes), dtype=np.float32)
        cell_counts = np.zeros(len(donor_labels), dtype=np.int64)

        pilot_data_parts = []
        pilot_index_parts = []
        pilot_indptr = [0]
        pilot_rows = []

        print(f"Source shape: {n_cells:,} cells x {n_genes:,} genes")
        print(f"Matched {filter_value}: {selected_idx.size:,} cells")
        print(f"Pilot cells to write: {pilot_idx.size:,}")

        for block_start in range(0, n_cells, row_block_size):
            block_end = min(block_start + row_block_size, n_cells)
            block_selected = np.flatnonzero(keep_mask[block_start:block_end]) + block_start
            if block_selected.size == 0:
                if block_start % (row_block_size * 10) == 0:
                    print(f"Scanned {block_end:,} / {n_cells:,} rows")
                continue

            data_start = int(indptr[block_start])
            data_end = int(indptr[block_end])
            block_data = x["data"][data_start:data_end]
            block_indices = x["indices"][data_start:data_end].astype(np.int32, copy=False)

            for row in block_selected:
                local_start = int(indptr[row] - data_start)
                local_end = int(indptr[row + 1] - data_start)
                row_data = block_data[local_start:local_end]
                row_indices = block_indices[local_start:local_end]
                donor_row = int(donor_row_for_cell[row])

                sums[donor_row, row_indices] += row_data
                cell_counts[donor_row] += 1

                if pilot_lookup[row]:
                    pilot_data_parts.append(row_data.astype(np.float32, copy=True))
                    pilot_index_parts.append(row_indices.astype(np.int32, copy=True))
                    pilot_indptr.append(pilot_indptr[-1] + row_data.size)
                    pilot_rows.append(row)

            if block_start % (row_block_size * 10) == 0:
                print(f"Scanned {block_end:,} / {n_cells:,} rows; collected {len(pilot_rows):,} pilot cells")

        gene_names = read_var_names(handle)
        obs = pd.DataFrame(index=[f"cell_{row}" for row in pilot_rows])
        pilot_rows_np = np.asarray(pilot_rows, dtype=np.int64)
        for column in obs_columns:
            if column in handle["obs"]:
                obs[column] = decode_column(handle, column, pilot_rows_np)

        var = pd.DataFrame(index=gene_names)
        if "gene_ids" in handle["var"]:
            var["gene_ids"] = [decode(value) for value in handle["var"]["gene_ids"][:]]

    nonzero_donors = cell_counts > 0
    means = sums[nonzero_donors] / cell_counts[nonzero_donors, None]
    pseudobulk = pd.DataFrame(means, columns=gene_names)
    pseudobulk.insert(0, "Donor ID", np.asarray(donor_labels)[nonzero_donors])
    pseudobulk_out.parent.mkdir(parents=True, exist_ok=True)
    pseudobulk.to_csv(pseudobulk_out, index=False)

    counts = pd.DataFrame({"Donor ID": donor_labels, "microglia_pvm_n_cells": cell_counts})
    counts = counts[counts["microglia_pvm_n_cells"] > 0].sort_values("microglia_pvm_n_cells", ascending=False)
    counts_out.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(counts_out, index=False)

    pilot_out.parent.mkdir(parents=True, exist_ok=True)
    if pilot_rows:
        pilot_x = csr_matrix(
            (
                np.concatenate(pilot_data_parts).astype(np.float32, copy=False),
                np.concatenate(pilot_index_parts).astype(np.int32, copy=False),
                np.asarray(pilot_indptr, dtype=np.int64),
            ),
            shape=(len(pilot_rows), n_genes),
        )
        adata = ad.AnnData(X=pilot_x, obs=obs, var=var)
        if n_top_genes and n_top_genes < adata.n_vars:
            adata = normalize_log_hvg(adata, n_top_genes)
        adata.write_h5ad(pilot_out)
        print(f"Wrote pilot: {pilot_out} ({adata.n_obs:,} cells x {adata.n_vars:,} genes)")

    print(f"Wrote pseudobulk: {pseudobulk_out} ({pseudobulk.shape[0]:,} donors x {pseudobulk.shape[1] - 1:,} genes)")
    print(f"Wrote counts: {counts_out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sequentially build Microglia-PVM pilot and donor pseudobulk from SEA-AD H5AD.")
    parser.add_argument("--h5ad", default="data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad")
    parser.add_argument("--filter-column", default="Subclass")
    parser.add_argument("--filter-value", default="Microglia-PVM")
    parser.add_argument("--cell-max", type=int, default=10000)
    parser.add_argument("--n-top-genes", type=int, default=3000)
    parser.add_argument("--row-block-size", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--pilot-out", default="data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad")
    parser.add_argument("--pseudobulk-out", default="data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv")
    parser.add_argument("--counts-out", default="data/processed/sea_ad_mtg_microglia_pvm_counts.csv")
    parser.add_argument("--obs-columns", nargs="+", default=DEFAULT_OBS_COLUMNS)
    args = parser.parse_args()

    build_outputs(
        h5ad_path=Path(args.h5ad),
        filter_column=args.filter_column,
        filter_value=args.filter_value,
        cell_max=args.cell_max,
        seed=args.seed,
        row_block_size=args.row_block_size,
        n_top_genes=args.n_top_genes,
        pilot_out=Path(args.pilot_out),
        pseudobulk_out=Path(args.pseudobulk_out),
        counts_out=Path(args.counts_out),
        obs_columns=args.obs_columns,
    )


if __name__ == "__main__":
    main()

