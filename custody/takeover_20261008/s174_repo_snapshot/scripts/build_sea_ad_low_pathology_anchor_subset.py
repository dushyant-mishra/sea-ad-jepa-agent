from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SEA-AD low-pathology Microglia-PVM anchor H5AD subsets.")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--audit", default="results/tables/sea_ad_low_pathology_anchor_audit_donors.csv")
    parser.add_argument("--anchor-column", default="internal_low_pathology_anchor_relaxed")
    parser.add_argument("--donor-column", default="Donor ID")
    parser.add_argument(
        "--out",
        default="data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad",
    )
    parser.add_argument("--summary-out", default="results/tables/sea_ad_low_pathology_microglia_pvm_relaxed_subset_summary.csv")
    args = parser.parse_args()

    audit = pd.read_csv(args.audit)
    if args.anchor_column not in audit.columns:
        raise KeyError(f"{args.anchor_column} not found in {args.audit}")
    anchor_donors = set(audit.loc[audit[args.anchor_column].fillna(False).astype(bool), "Donor ID"].astype(str))
    if not anchor_donors:
        raise ValueError(f"No donors selected by {args.anchor_column}")

    adata = ad.read_h5ad(args.h5ad)
    if args.donor_column not in adata.obs:
        raise KeyError(f"{args.donor_column} not found in {args.h5ad} obs")

    donor_series = adata.obs[args.donor_column].astype(str)
    mask = donor_series.isin(anchor_donors).to_numpy()
    subset = adata[mask].copy()
    subset.obs["stage_b_anchor_type"] = args.anchor_column

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subset.write_h5ad(out_path)

    summary = (
        subset.obs[args.donor_column]
        .astype(str)
        .value_counts()
        .rename_axis("Donor ID")
        .reset_index(name="n_cells")
        .sort_values("Donor ID")
    )
    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_path, index=False)

    print(f"Wrote {out_path}")
    print(f"Wrote {summary_path}")
    print(f"anchor_column={args.anchor_column} donors={len(anchor_donors)} cells={subset.n_obs:,} genes={subset.n_vars:,}")


if __name__ == "__main__":
    main()
