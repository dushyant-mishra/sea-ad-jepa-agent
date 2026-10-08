from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def load_result(path: str, label: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.insert(0, "model", label)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare pathology prediction result tables.")
    parser.add_argument(
        "--result",
        action="append",
        nargs=2,
        metavar=("LABEL", "CSV"),
        required=True,
        help="Model label and result CSV. Can be passed multiple times.",
    )
    parser.add_argument("--out", default="results/tables/pathology_model_comparison.csv")
    args = parser.parse_args()

    rows = [load_result(path, label) for label, path in args.result]
    combined = pd.concat(rows, ignore_index=True)
    combined = combined.sort_values(["target", "spearman"], ascending=[True, False])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)

    top_by_model = (
        combined.sort_values("spearman", ascending=False)
        .groupby("model", as_index=False)
        .head(5)
        .sort_values(["model", "spearman"], ascending=[True, False])
    )
    print(top_by_model[["model", "target", "spearman", "r2", "mae"]].to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

