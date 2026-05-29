from __future__ import annotations

import argparse

import pandas as pd

from sea_ad_jepa.interpretation import write_hypothesis_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a first hypothesis report from microglia baseline results.")
    parser.add_argument("--baseline-results", required=True)
    parser.add_argument("--out", default="results/reports/microglia_pvm_hypothesis_report.md")
    args = parser.parse_args()

    results = pd.read_csv(args.baseline_results)
    write_hypothesis_report(results, args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

