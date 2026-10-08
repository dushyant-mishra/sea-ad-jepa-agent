from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate cell-level JEPA latent coordinates to donor-level embeddings.")
    parser.add_argument("--coordinates", required=True, help="Cell-level coordinate CSV with z_* columns.")
    parser.add_argument("--out", required=True, help="Output donor-level embedding CSV.")
    parser.add_argument("--donor-column", default="donor_id")
    parser.add_argument("--output-donor-column", default="Donor ID")
    args = parser.parse_args()

    df = pd.read_csv(args.coordinates)
    z_cols = [col for col in df.columns if str(col).startswith("z_")]
    if not z_cols:
        raise ValueError(f"No z_* columns found in {args.coordinates}")
    if args.donor_column not in df:
        raise KeyError(f"Missing donor column {args.donor_column!r} in {args.coordinates}")

    donor = (
        df.groupby(args.donor_column, as_index=False)[z_cols]
        .mean()
        .rename(columns={args.donor_column: args.output_donor_column})
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    donor.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    print(f"donors={donor.shape[0]:,} latent_dim={len(z_cols)}")


if __name__ == "__main__":
    main()
