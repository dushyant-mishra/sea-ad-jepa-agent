from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_TARGETS = [
    "percent 6e10 positive area_Grey matter",
    "number of 6e10 positive objects per area_Grey matter",
    "percent AT8 positive area_Grey matter",
    "number of AT8 positive cells per area_Grey matter",
    "percent GFAP positive area_Grey matter",
    "percent Iba1 positive area_Grey matter",
    "number of activated Iba1 positive cells_Grey matter",
    "percent NeuN positive area_Grey matter",
    "number of NeuN positive cells per area_Grey matter",
    "guhcl abeta40_Grey matter",
    "guhcl abeta42_Grey matter",
    "guhcl pTau_Grey matter",
    "guhcl tTau_Grey matter",
    "ripa abeta40_Grey matter",
    "ripa abeta42_Grey matter",
    "ripa pTau_Grey matter",
    "ripa tTau_Grey matter",
]

DEFAULT_DONOR_COLUMNS = [
    "Donor ID",
    "Age at Death",
    "Sex",
    "APOE Genotype",
    "Cognitive Status",
    "Braak",
    "Thal",
    "CERAD score",
    "Overall AD neuropathological Change",
    "CPS",
    "Severely Affected Donor",
]


def existing_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in df.columns]


def main() -> None:
    parser = argparse.ArgumentParser(description="Join SEA-AD donor metadata and MTG neuropathology targets.")
    parser.add_argument(
        "--donor-metadata",
        default="data/raw/metadata/sea-ad_cohort_donor_metadata_072524.xlsx",
        help="SEA-AD donor metadata workbook.",
    )
    parser.add_argument(
        "--neuropathology",
        default="data/raw/metadata/sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv",
        help="SEA-AD MTG quantitative neuropathology CSV.",
    )
    parser.add_argument("--out-dir", default="data/processed/metadata", help="Output directory.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    donor = pd.read_excel(args.donor_metadata)
    neuropath = pd.read_csv(args.neuropathology)

    if "Unnamed: 0" in neuropath.columns:
        neuropath = neuropath.drop(columns=["Unnamed: 0"])

    donor_columns = existing_columns(donor, DEFAULT_DONOR_COLUMNS)
    target_columns = existing_columns(neuropath, DEFAULT_TARGETS)

    missing_targets = sorted(set(DEFAULT_TARGETS) - set(target_columns))
    if missing_targets:
        print("Missing expected target columns:")
        for column in missing_targets:
            print(f"  - {column}")

    joined = donor[donor_columns].merge(
        neuropath[["Donor ID", *target_columns]],
        on="Donor ID",
        how="left",
        validate="one_to_one",
    )

    joined.to_csv(out_dir / "sea_ad_mtg_donor_pathology_targets.csv", index=False)
    pd.DataFrame({"target_column": target_columns}).to_csv(out_dir / "pathology_target_columns.csv", index=False)

    numeric_targets = joined[target_columns].apply(pd.to_numeric, errors="coerce")
    summary = numeric_targets.describe().T
    summary["missing_n"] = numeric_targets.isna().sum()
    summary.to_csv(out_dir / "pathology_target_summary.csv")

    corr_columns = [column for column in target_columns if numeric_targets[column].notna().sum() >= 10]
    if corr_columns:
        numeric_targets[corr_columns].corr(method="spearman").to_csv(out_dir / "pathology_target_spearman_corr.csv")

    print(f"Joined donors: {joined.shape[0]}")
    print(f"Target columns: {len(target_columns)}")
    print(f"Wrote outputs to {out_dir}")


if __name__ == "__main__":
    main()

