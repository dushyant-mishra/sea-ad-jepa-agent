from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


TIER1 = "scorecard_supported_isolated_hypothesis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Annotate the internal evidence scorecard with diagnostic-only gliosis details."
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=Path(
            "results/tables/discovery_internal_evidence_scorecard_v1.csv"
        ),
    )
    parser.add_argument(
        "--diagnostics",
        type=Path,
        default=Path(
            "results/tables/discovery_level2_gliosis_failure_diagnostics_v1.csv"
        ),
    )
    parser.add_argument(
        "--sensitivity",
        type=Path,
        default=Path(
            "results/tables/discovery_level2_gliosis_sensitivity_v1.csv"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_internal_evidence_scorecard_v1_annotated.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_internal_evidence_scorecard_v1_annotated.md"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = pd.read_csv(args.scorecard)
    diagnostics = pd.read_csv(args.diagnostics)
    sensitivity = pd.read_csv(args.sensitivity)

    if len(diagnostics) != 41 or len(sensitivity) != 41:
        raise ValueError("Expected 41 Tier-1 diagnostic rows")
    if set(diagnostics["gene"]) != set(sensitivity["gene"]):
        raise ValueError("Diagnostic and sensitivity gene sets differ")

    diag_columns = [
        "gene",
        "failure_pattern",
        "failed_required_axes",
        "gfap_positive_fraction",
        "iba1_positive_fraction",
        "mean_GFAP_delta",
        "mean_Iba1_delta",
    ]
    sensitivity_info = sensitivity[
        [
            "gene",
            "strict_gliosis_noninflating_stability",
            "epsilon_0_001_gliosis_stability",
            "epsilon_0_005_gliosis_stability",
            "epsilon_0_01_gliosis_stability",
            "sensitivity_interpretation",
        ]
    ].copy()
    sensitivity_info["epsilon_sensitivity_summary"] = sensitivity_info.apply(
        lambda row: (
            f"strict={row['strict_gliosis_noninflating_stability']:.3f};"
            f"eps0.001={row['epsilon_0_001_gliosis_stability']:.3f};"
            f"eps0.005={row['epsilon_0_005_gliosis_stability']:.3f};"
            f"eps0.01={row['epsilon_0_01_gliosis_stability']:.3f};"
            f"{row['sensitivity_interpretation']}"
        ),
        axis=1,
    )
    diagnostic_info = diagnostics[diag_columns].merge(
        sensitivity_info[["gene", "epsilon_sensitivity_summary"]],
        on="gene",
        validate="one_to_one",
    )
    diagnostic_info = diagnostic_info.rename(
        columns={
            "failure_pattern": "level2_failure_pattern",
            "failed_required_axes": "level2_failed_required_axes",
        }
    )
    diagnostic_info["gliosis_failure_interpretation"] = diagnostic_info.apply(
        lambda row: (
            "strict_positive_part_gliosis_axis_only"
            if row["level2_failure_pattern"]
            == "passes_non_gliosis_axes_fails_gliosis_only"
            else "gliosis_plus_additional_required_axis_failure"
        ),
        axis=1,
    )
    diagnostic_info["diagnostic_only_no_evidence_promotion"] = True

    annotated = base.merge(
        diagnostic_info,
        on="gene",
        how="left",
        validate="one_to_one",
    )
    new_columns = [
        "level2_failure_pattern",
        "level2_failed_required_axes",
        "gliosis_failure_interpretation",
        "gfap_positive_fraction",
        "iba1_positive_fraction",
        "mean_GFAP_delta",
        "mean_Iba1_delta",
        "epsilon_sensitivity_summary",
    ]
    non_tier1 = ~annotated["final_tier"].eq(TIER1)
    for column in new_columns:
        if pd.api.types.is_numeric_dtype(annotated[column]):
            annotated.loc[non_tier1, column] = np.nan
        else:
            annotated.loc[non_tier1, column] = "not_applicable"
    annotated["diagnostic_only_no_evidence_promotion"] = annotated[
        "diagnostic_only_no_evidence_promotion"
    ].eq(True)

    protected = [
        "current_max_evidence_level",
        "internal_robustness_evidence",
        "baseline_comparison_evidence",
        "external_cohort_evidence",
        "cell_state_evidence",
        "spatial_evidence",
        "experimental_evidence",
    ]
    comparison = base[["gene", *protected]].merge(
        annotated[["gene", *protected]],
        on="gene",
        suffixes=("_base", "_annotated"),
        validate="one_to_one",
    )
    for column in protected:
        if not (
            comparison[f"{column}_base"].astype(str)
            == comparison[f"{column}_annotated"].astype(str)
        ).all():
            raise ValueError(f"Protected evidence column changed: {column}")

    tier1 = annotated[annotated["final_tier"].eq(TIER1)]
    if len(tier1) != 41:
        raise ValueError("Expected 41 annotated Tier-1 genes")
    if not tier1["diagnostic_only_no_evidence_promotion"].all():
        raise ValueError("Every Tier-1 diagnostic row must be marked diagnostic-only")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    annotated.to_csv(args.out, index=False)

    counts = tier1["level2_failure_pattern"].value_counts()
    lines = [
        "# Internal Evidence Scorecard v1 — Gliosis Diagnostic Annotation",
        "",
        "## Evidence status",
        "",
        "- Official evidence levels are unchanged.",
        "- All 41 Tier-1 genes remain at Level 1.",
        "- No Level-2 or Level-3 evidence was added.",
        "- Gliosis diagnostics explain the failed robustness gate but do not rescue candidates.",
        "",
        "## Tier-1 failure-pattern counts",
        "",
        *[f"- `{pattern}`: {count}" for pattern, count in counts.items()],
        "",
        "## Sensitivity boundary",
        "",
        "All epsilon analyses are diagnostic sensitivity only and are labeled `diagnostic_only_no_evidence_promotion`. The official strict positive-part gliosis criterion and the original evidence scorecard remain unchanged.",
        "",
        "## Claim boundary",
        "",
        "This annotation adds technical interpretation only. It does not add biological validation, causal evidence, external validation, spatial support, or experimental efficacy.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(counts.to_string())
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
