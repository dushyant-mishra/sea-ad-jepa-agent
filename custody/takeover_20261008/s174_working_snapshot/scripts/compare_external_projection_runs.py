from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_CATEGORIES = [
    "sea_ad_disease_trajectory",
    "sea_ad_calibrated_pathology_prediction",
    "module_score",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two external projection summary CSVs.")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--aligned", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--categories", nargs="*", default=DEFAULT_CATEGORIES)
    args = parser.parse_args()

    frames = []
    for label, path in [("baseline", args.baseline), ("aligned", args.aligned)]:
        df = pd.read_csv(path)
        df = df[df["category"].isin(args.categories)].copy()
        df["run"] = label
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    metrics = ["auc_ad_vs_control", "mean_difference_disease_minus_control", "rank_biserial_effect"]
    wide = combined.pivot_table(index=["category", "variable"], columns="run", values=metrics, aggfunc="first")
    wide.columns = [f"{metric}_{run}" for metric, run in wide.columns]
    wide = wide.reset_index()
    for metric in metrics:
        baseline_col = f"{metric}_baseline"
        aligned_col = f"{metric}_aligned"
        if baseline_col in wide and aligned_col in wide:
            wide[f"{metric}_delta_aligned_minus_baseline"] = wide[aligned_col] - wide[baseline_col]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(out, index=False)
    print(wide.sort_values(["category", "auc_ad_vs_control_aligned"], ascending=[True, False]).to_string(index=False))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
