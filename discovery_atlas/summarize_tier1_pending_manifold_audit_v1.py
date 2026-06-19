from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize the targeted manifold audit for pending Tier-1 genes."
    )
    parser.add_argument(
        "--gene-list",
        type=Path,
        default=Path(
            "results/tables/discovery_tier1_pending_manifold_audit_gene_list_v1.csv"
        ),
    )
    parser.add_argument(
        "--raw-summary",
        type=Path,
        default=Path(
            "results/tables/discovery_tier1_pending_manifold_audit_v1_summary.csv"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_tier1_pending_manifold_audit_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_tier1_pending_manifold_audit_v1.md"
        ),
    )
    return parser.parse_args()


def classify(value: float) -> str:
    if pd.isna(value):
        return "not_computed"
    if value <= 0.05:
        return "manifold_safe"
    if value <= 0.10:
        return "borderline_manifold_shift"
    return "manifold_violation_warning"


def interpretation(status: str) -> str:
    return {
        "manifold_safe": "targeted_perturbation_remained_within_sampled_latent_support",
        "borderline_manifold_shift": "targeted_perturbation_has_borderline_latent_support_shift",
        "manifold_violation_warning": "targeted_perturbation_exceeded_latent_support_threshold",
        "not_computed": "manifold_qc_not_computed",
    }[status]


def markdown_table(frame: pd.DataFrame) -> list[str]:
    columns = [
        "gene",
        "therapeutic_like_score_percentile",
        "mean_nearest_real_cell_distance",
        "p95_nearest_real_cell_distance",
        "baseline_nn_p95_threshold",
        "manifold_violation_fraction",
        "manifold_qc_status",
    ]
    data = frame[columns].copy()
    for column in data.columns:
        if pd.api.types.is_numeric_dtype(data[column]):
            data[column] = data[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.6g}"
            )
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in data.itertuples(index=False, name=None)
    )
    return lines


def main() -> None:
    args = parse_args()
    genes = pd.read_csv(args.gene_list)
    raw = pd.read_csv(args.raw_summary)
    if len(genes) != 19 or len(raw) != 19:
        raise ValueError(f"Expected 19 rows, found gene_list={len(genes)}, raw={len(raw)}")
    if set(genes["gene"]) != set(raw["gene"]):
        raise ValueError("Pending Tier-1 gene list and raw audit differ")

    merged = genes.merge(raw, on="gene", how="inner", validate="one_to_one")
    merged["manifold_qc_status"] = merged["manifold_violation_fraction"].map(
        classify
    )
    merged["manifold_qc_interpretation"] = merged["manifold_qc_status"].map(
        interpretation
    )
    merged["recommended_shortlist_action"] = merged["manifold_qc_status"].map(
        {
            "manifold_safe": "retain_tier1_scorecard_hypothesis",
            "borderline_manifold_shift": "retain_with_manifold_caution",
            "manifold_violation_warning": "demote_or_flag_after_manifold_qc",
            "not_computed": "keep_pending_manifold_qc",
        }
    )
    merged = merged.sort_values(
        "therapeutic_like_score_percentile", ascending=False
    ).reset_index(drop=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.out, index=False)

    counts = merged["manifold_qc_status"].value_counts()
    lines = [
        "# Pending Tier-1 Targeted Manifold Audit v1",
        "",
        "## Result",
        "",
        f"- Genes audited: {len(merged)}",
        f"- Torch-backend perturbations successful: {int(merged['perturbation_success'].sum())}/{len(merged)}",
        *[f"- `{status}`: {count}" for status, count in counts.items()],
        "",
        *markdown_table(merged),
        "",
        "## Interpretation boundary",
        "",
        "This completes targeted manifold QC for all previously pending Tier-1 candidates if every row is classified as `manifold_safe`, `borderline_manifold_shift`, or `manifold_violation_warning` rather than `not_computed`.",
        "",
        "Manifold QC is technical latent-support QC. It does not prove biological relevance, causal mechanism, druggability, spatial plaque proximity, or therapeutic efficacy.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print(counts.to_string())


if __name__ == "__main__":
    main()
