from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DISTANCE_COLUMNS = [
    "mean_nearest_real_cell_distance",
    "p95_nearest_real_cell_distance",
    "baseline_nn_p95_threshold",
    "manifold_violation_fraction",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sanity-check raw distances from the targeted manifold audit."
    )
    parser.add_argument(
        "--raw-audit",
        type=Path,
        default=Path("results/tables/discovery_targeted_manifold_audit_v1.csv"),
    )
    parser.add_argument(
        "--merged-audit",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_results_v1.csv"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_distance_sanity_check.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_targeted_manifold_audit_distance_sanity_check.md"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = pd.read_csv(args.raw_audit)
    merged = pd.read_csv(args.merged_audit)

    missing = [column for column in DISTANCE_COLUMNS if column not in raw.columns]
    if missing:
        raise ValueError(f"Missing raw manifold columns: {missing}")
    for column in DISTANCE_COLUMNS:
        if raw[column].isna().any():
            raise ValueError(f"Null values in {column}")
    if not raw["gene"].is_unique:
        raise ValueError("Raw targeted audit contains duplicate genes")
    if set(raw["gene"]) != set(merged["gene"]):
        raise ValueError("Raw and merged targeted-audit genes differ")
    if raw["baseline_nn_p95_threshold"].max() <= 0:
        raise ValueError("Baseline nearest-neighbor threshold is not positive")
    if raw["p95_nearest_real_cell_distance"].max() <= 0:
        raise ValueError("Perturbed p95 nearest-neighbor distances are all zero")
    if raw["mean_nearest_real_cell_distance"].max() <= 0:
        raise ValueError("Perturbed mean nearest-neighbor distances are all zero")

    backend_column = next(
        (
            column
            for column in ["manifold_neighbor_backend", "manifold_nn_backend"]
            if column in raw.columns
        ),
        None,
    )
    if backend_column is not None and not raw[backend_column].eq("torch").all():
        raise ValueError("Non-torch manifold backend detected")

    safety_column = "manifold_safety_status"
    if safety_column in raw.columns:
        accepted = {"computed", "within_manifold_threshold"}
        if not set(raw[safety_column].dropna().astype(str)).issubset(accepted):
            raise ValueError("Non-computed manifold safety status detected")

    summary_rows = []
    for column in DISTANCE_COLUMNS:
        summary_rows.append(
            {
                "metric": column,
                "minimum": raw[column].min(),
                "median": raw[column].median(),
                "maximum": raw[column].max(),
                "n_non_null": int(raw[column].notna().sum()),
                "all_zero": bool(raw[column].eq(0).all()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out, index=False)

    n_zero_violations = int(raw["manifold_violation_fraction"].eq(0).sum())
    lines = [
        "# Targeted Manifold Audit Raw-Distance Sanity Check",
        "",
        "## Result",
        "",
        f"- Audited genes: {len(raw)}",
        f"- Torch backend confirmed: `{backend_column is not None}`",
        f"- Genes with zero violation fraction: {n_zero_violations}/{len(raw)}",
        f"- Baseline NN p95 threshold: {raw['baseline_nn_p95_threshold'].iloc[0]:.8f}",
        "- Required distance fields: complete and non-null.",
        "- Mean and p95 perturbed nearest-neighbor distances: nonzero.",
        "",
        "| metric | minimum | median | maximum | n_non_null | all_zero |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.metric} | {row.minimum:.8g} | {row.median:.8g} | "
            f"{row.maximum:.8g} | {row.n_non_null} | {row.all_zero} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The zero manifold-violation fractions are a genuine threshold pass rather than a missing-value or all-zero-distance artifact: the underlying distances and positive baseline threshold are populated and nonzero.",
            "",
            "This is technical perturbation QC only. It does not provide biological validation, causal evidence, druggability, spatial context, or therapeutic efficacy.",
            "",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
