from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import pandas as pd


def decode(value) -> str:
    if isinstance(value, bytes):
        return value.decode()
    return str(value)


def categorical_counts(handle: h5py.File, column: str) -> pd.DataFrame:
    ds = handle["obs"][column]
    category_ref = ds.attrs.get("categories")
    if not category_ref:
        values = pd.Series(ds[:]).map(decode)
        return values.value_counts(dropna=False).rename_axis(column).reset_index(name="n")

    categories = [decode(value) for value in handle[category_ref][:]]
    codes = pd.Series(ds[:])
    counts = codes.value_counts().sort_index()
    rows = []
    for code, n in counts.items():
        label = categories[int(code)] if int(code) >= 0 else "NA"
        rows.append({column: label, "n": int(n)})
    return pd.DataFrame(rows).sort_values("n", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast H5AD obs categorical summary using h5py.")
    parser.add_argument("--h5ad", required=True)
    parser.add_argument("--columns", nargs="+", default=["Brain Region", "Class", "Subclass", "Supertype", "Donor ID"])
    parser.add_argument("--out-dir", default="results/inspection")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with h5py.File(args.h5ad, "r") as handle:
        shape = handle["X"].attrs.get("shape")
        print(f"X shape: {shape[0]:,} cells x {shape[1]:,} genes")
        print("obs columns:")
        obs_columns = list(handle["obs"].keys())
        pd.DataFrame({"obs_column": obs_columns}).to_csv(out_dir / "obs_columns_fast.csv", index=False)
        for column in args.columns:
            if column not in handle["obs"]:
                print(f"Missing column: {column}")
                continue
            counts = categorical_counts(handle, column)
            safe_name = column.replace("/", "_").replace(" ", "_")
            counts.to_csv(out_dir / f"{safe_name}_counts.csv", index=False)
            print(f"\n{column}")
            print(counts.head(30).to_string(index=False))


if __name__ == "__main__":
    main()

