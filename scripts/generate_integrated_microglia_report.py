from __future__ import annotations

import argparse

import pandas as pd

from sea_ad_jepa.interpretation import write_integrated_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an integrated Microglia-PVM interpretation report.")
    parser.add_argument("--pseudobulk-results", default="results/tables/microglia_pvm_pseudobulk_ridge_1000genes.csv")
    parser.add_argument("--jepa-results", default="results/tables/microglia_pvm_jepa_embedding_ridge.csv")
    parser.add_argument("--gene-rankings", default="results/tables/microglia_pvm_percent_AT8_gene_rankings.csv")
    parser.add_argument("--gene-set-scores", default="results/tables/microglia_pvm_percent_AT8_gene_set_scores.csv")
    parser.add_argument("--out", default="results/reports/microglia_pvm_integrated_report.md")
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    args = parser.parse_args()

    write_integrated_report(
        pseudobulk_results=pd.read_csv(args.pseudobulk_results),
        jepa_results=pd.read_csv(args.jepa_results),
        gene_rankings=pd.read_csv(args.gene_rankings),
        gene_set_scores=pd.read_csv(args.gene_set_scores),
        out_path=args.out,
        target_name=args.target,
    )
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
