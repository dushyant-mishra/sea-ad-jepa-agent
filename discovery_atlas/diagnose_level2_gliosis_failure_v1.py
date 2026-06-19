from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


TIER1 = "scorecard_supported_isolated_hypothesis"
EPSILONS = [0.001, 0.005, 0.01]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose why Tier-1 genes failed the Level-2 gliosis gate."
    )
    parser.add_argument(
        "--shortlist",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v3.csv"),
    )
    parser.add_argument(
        "--robustness",
        type=Path,
        default=Path(
            "results/tables/discovery_internal_robustness_stability_v1.csv"
        ),
    )
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument(
        "--diagnostics-out",
        type=Path,
        default=Path(
            "results/tables/discovery_level2_gliosis_failure_diagnostics_v1.csv"
        ),
    )
    parser.add_argument(
        "--sensitivity-out",
        type=Path,
        default=Path(
            "results/tables/discovery_level2_gliosis_sensitivity_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_level2_gliosis_failure_diagnostics_v1.md"
        ),
    )
    return parser.parse_args()


def discover_donor_files() -> list[Path]:
    return [
        path
        for path in sorted(Path("results").glob("**/*donor*.csv"))
        if "_feature_wide_counterfactual_chunks" in str(path)
        and (
            "discovery_targeted_manifold_audit_v1" in str(path)
            or "discovery_tier1_pending_manifold_audit" in str(path)
        )
    ]


def delta_column(columns: list[str], marker: str) -> str:
    matches = [
        column
        for column in columns
        if column.startswith("delta_") and marker.lower() in column.lower()
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one delta column for {marker}: {matches}")
    return matches[0]


def required_axes(pathology_class: str) -> list[str]:
    if pathology_class == "tau_lowering_neuron_preserving":
        return [
            "tau_direction_stability",
            "neuron_direction_stability",
            "gliosis_noninflating_stability",
        ]
    if pathology_class == "dual_pathology_lowering_neuron_preserving":
        return [
            "tau_direction_stability",
            "amyloid_direction_stability",
            "neuron_direction_stability",
            "gliosis_noninflating_stability",
        ]
    if pathology_class == "amyloid_lowering_candidate":
        return [
            "amyloid_direction_stability",
            "gliosis_noninflating_stability",
        ]
    return []


def failure_pattern(failed_axes: list[str]) -> str:
    if not failed_axes:
        return "multi_axis_failure"
    non_gliosis = [
        axis for axis in failed_axes if axis != "gliosis_noninflating_stability"
    ]
    if not non_gliosis:
        return "passes_non_gliosis_axes_fails_gliosis_only"
    if len(non_gliosis) > 1:
        return "multi_axis_failure"
    return {
        "tau_direction_stability": "fails_tau_axis",
        "amyloid_direction_stability": "fails_amyloid_axis",
        "neuron_direction_stability": "fails_neuron_axis",
    }.get(non_gliosis[0], "multi_axis_failure")


def top_donors(donor: pd.DataFrame, gfap: str, iba1: str, n: int = 5) -> str:
    contributions = (
        donor.assign(
            gliosis_contribution=np.clip(donor[gfap].to_numpy(float), 0, None)
            + np.clip(donor[iba1].to_numpy(float), 0, None)
        )
        .nlargest(n, "gliosis_contribution")
        [["Donor ID", "gliosis_contribution"]]
    )
    return ";".join(
        f"{row['Donor ID']}:{row['gliosis_contribution']:.6g}"
        for _, row in contributions.iterrows()
    )


def main() -> None:
    args = parse_args()
    shortlist = pd.read_csv(args.shortlist)
    robustness = pd.read_csv(args.robustness)
    tier1 = shortlist[shortlist["final_tier"].eq(TIER1)].copy()
    if len(tier1) != 41:
        raise ValueError(f"Expected 41 Tier-1 genes, found {len(tier1)}")

    donor_files = discover_donor_files()
    frames = []
    for path in donor_files:
        frame = pd.read_csv(path)
        frame["donor_level_source"] = str(path)
        frames.append(frame)
    donor_data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    merged = tier1.merge(
        robustness[
            [
                "gene",
                "tau_direction_stability",
                "amyloid_direction_stability",
                "neuron_direction_stability",
                "gliosis_noninflating_stability",
                "minimum_required_directional_stability",
                "level_2_evidence_status",
            ]
        ],
        on="gene",
        how="left",
        validate="one_to_one",
    )
    diagnostics = []
    sensitivities = []
    for index, row in merged.iterrows():
        gene = str(row["gene"])
        donor = donor_data[
            donor_data["perturbation"].astype(str).str.upper().eq(gene)
        ].copy()
        axes = required_axes(str(row["pathology_axis_class"]))
        failed = [
            axis
            for axis in axes
            if pd.isna(row[axis]) or float(row[axis]) < 0.80
        ]
        base = {
            "gene": gene,
            "pathology_axis_class": row["pathology_axis_class"],
            "therapeutic_like_score_percentile": row[
                "therapeutic_like_score_percentile"
            ],
            "tau_direction_stability": row["tau_direction_stability"],
            "amyloid_direction_stability": row["amyloid_direction_stability"],
            "neuron_direction_stability": row["neuron_direction_stability"],
            "gliosis_noninflating_stability": row[
                "gliosis_noninflating_stability"
            ],
            "minimum_required_directional_stability": row[
                "minimum_required_directional_stability"
            ],
            "failed_required_axes": "|".join(failed),
        }
        if donor.empty:
            diagnostics.append(
                {
                    **base,
                    "gfap_positive_fraction": np.nan,
                    "iba1_positive_fraction": np.nan,
                    "both_gfap_iba1_positive_fraction": np.nan,
                    "mean_GFAP_delta": np.nan,
                    "mean_Iba1_delta": np.nan,
                    "median_GFAP_delta": np.nan,
                    "median_Iba1_delta": np.nan,
                    "max_GFAP_delta": np.nan,
                    "max_Iba1_delta": np.nan,
                    "donor_count": 0,
                    "top_gliosis_contributing_donors": "",
                    "top_gliosis_donor_share": np.nan,
                    "failure_pattern": "not_testable_missing_donor_level_deltas",
                }
            )
            sensitivities.append(
                {
                    "gene": gene,
                    "official_level2_status": row["level_2_evidence_status"],
                    "strict_gliosis_noninflating_stability": np.nan,
                    "epsilon_0_001_gliosis_stability": np.nan,
                    "epsilon_0_005_gliosis_stability": np.nan,
                    "epsilon_0_01_gliosis_stability": np.nan,
                    "stability_threshold_0_70_status": "not_testable",
                    "stability_threshold_0_75_status": "not_testable",
                    "stability_threshold_0_80_status": "not_testable",
                    "sensitivity_interpretation": "not_testable_missing_donor_level_deltas",
                }
            )
            continue

        columns = donor.columns.tolist()
        gfap = delta_column(columns, "GFAP")
        iba1 = delta_column(columns, "Iba1")
        gfap_values = donor[gfap].to_numpy(float)
        iba1_values = donor[iba1].to_numpy(float)
        gliosis = np.clip(gfap_values, 0, None) + np.clip(iba1_values, 0, None)
        rng = np.random.default_rng(args.seed + index)
        sample_indices = rng.integers(
            0, len(gliosis), size=(args.n_bootstrap, len(gliosis))
        )
        bootstrap_gliosis = gliosis[sample_indices].mean(axis=1)
        epsilon_stability = {
            epsilon: float(np.mean(bootstrap_gliosis <= epsilon))
            for epsilon in EPSILONS
        }
        non_gliosis_axes = [
            axis for axis in axes if axis != "gliosis_noninflating_stability"
        ]
        non_gliosis_min = (
            min(float(row[axis]) for axis in non_gliosis_axes)
            if non_gliosis_axes
            else 1.0
        )
        sensitivity_min = min(
            non_gliosis_min, epsilon_stability[0.005]
        )
        total_positive_gliosis = float(gliosis.sum())
        top_donor_share = (
            float(gliosis.max() / total_positive_gliosis)
            if total_positive_gliosis > 0
            else 0.0
        )
        threshold_status = {
            threshold: (
                "sensitivity_pass"
                if sensitivity_min >= threshold
                else "sensitivity_not_passed"
            )
            for threshold in [0.70, 0.75, 0.80]
        }
        threshold_dependent = (
            epsilon_stability[0.001] < 0.80
            and epsilon_stability[0.01] >= 0.80
        )
        sensitivities.append(
            {
                "gene": gene,
                "official_level2_status": row["level_2_evidence_status"],
                "strict_gliosis_noninflating_stability": float(
                    row["gliosis_noninflating_stability"]
                ),
                "epsilon_0_001_gliosis_stability": epsilon_stability[0.001],
                "epsilon_0_005_gliosis_stability": epsilon_stability[0.005],
                "epsilon_0_01_gliosis_stability": epsilon_stability[0.01],
                "stability_threshold_0_70_status": threshold_status[0.70],
                "stability_threshold_0_75_status": threshold_status[0.75],
                "stability_threshold_0_80_status": threshold_status[0.80],
                "sensitivity_interpretation": (
                    "sensitivity_only_not_evidence_promotion;threshold_dependent"
                    if threshold_dependent
                    else "sensitivity_only_not_evidence_promotion;not_threshold_rescued"
                ),
            }
        )
        diagnostics.append(
            {
                **base,
                "gfap_positive_fraction": float(np.mean(gfap_values > 0)),
                "iba1_positive_fraction": float(np.mean(iba1_values > 0)),
                "both_gfap_iba1_positive_fraction": float(
                    np.mean((gfap_values > 0) & (iba1_values > 0))
                ),
                "mean_GFAP_delta": float(np.mean(gfap_values)),
                "mean_Iba1_delta": float(np.mean(iba1_values)),
                "median_GFAP_delta": float(np.median(gfap_values)),
                "median_Iba1_delta": float(np.median(iba1_values)),
                "max_GFAP_delta": float(np.max(gfap_values)),
                "max_Iba1_delta": float(np.max(iba1_values)),
                "donor_count": int(donor["Donor ID"].nunique()),
                "top_gliosis_contributing_donors": top_donors(
                    donor, gfap, iba1
                ),
                "top_gliosis_donor_share": top_donor_share,
                "failure_pattern": failure_pattern(failed),
            }
        )

    diagnostics_df = pd.DataFrame(diagnostics)
    sensitivity_df = pd.DataFrame(sensitivities)
    if not sensitivity_df["official_level2_status"].eq("not_passed").all():
        raise ValueError("Official Level-2 status changed during diagnostics")
    args.diagnostics_out.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_df.to_csv(args.diagnostics_out, index=False)
    sensitivity_df.to_csv(args.sensitivity_out, index=False)

    gliosis_only = diagnostics_df["failure_pattern"].eq(
        "passes_non_gliosis_axes_fails_gliosis_only"
    )
    mean_gfap_positive = diagnostics_df["gfap_positive_fraction"].mean()
    mean_iba1_positive = diagnostics_df["iba1_positive_fraction"].mean()
    driver = (
        "GFAP"
        if mean_gfap_positive > mean_iba1_positive
        else "Iba1"
        if mean_iba1_positive > mean_gfap_positive
        else "balanced"
    )
    threshold_sensitive = sensitivity_df[
        "sensitivity_interpretation"
    ].str.contains("threshold_dependent").sum()

    # Donor concentration: share of total positive gliosis contribution from top donor.
    outlier_shares = diagnostics_df["top_gliosis_donor_share"].tolist()
    max_top_donor_share = max(outlier_shares)
    outlier_dominated = sum(share >= 0.50 for share in outlier_shares)
    outlier_genes = diagnostics_df.loc[
        diagnostics_df["top_gliosis_donor_share"].ge(0.50), "gene"
    ].tolist()

    recommendation = (
        "Keep the strict rule: failures are broad across donors and are not dominated by a single donor."
        if outlier_dominated == 0 and int(gliosis_only.sum()) > 0
        else "Keep the official strict rule. Any future tolerance must be pre-registered and independently justified."
    )
    lines = [
        "# Level-2 Gliosis Failure Diagnostics v1",
        "",
        "## Summary of why Level 2 failed",
        "",
        f"- Tier-1 genes diagnosed: {len(diagnostics_df)}",
        f"- Failed gliosis only: {int(gliosis_only.sum())}",
        f"- Other or multi-axis failures: {len(diagnostics_df) - int(gliosis_only.sum())}",
        f"- Mean GFAP-positive donor fraction: {mean_gfap_positive:.4f}",
        f"- Mean Iba1-positive donor fraction: {mean_iba1_positive:.4f}",
        f"- Larger positive-fraction contributor: `{driver}`",
        "",
        "## Failure-pattern counts",
        "",
        *[
            f"- `{pattern}`: {count}"
            for pattern, count in diagnostics_df["failure_pattern"].value_counts().items()
        ],
        "",
        "## GFAP versus Iba1 contribution summary",
        "",
        "Positive fractions are descriptive donor-level frequencies. The official gliosis penalty remains `max(GFAP_delta, 0) + max(Iba1_delta, 0)`.",
        "",
        f"- GFAP mean delta across gene-level donor means: {diagnostics_df['mean_GFAP_delta'].mean():.6g}",
        f"- Iba1 mean delta across gene-level donor means: {diagnostics_df['mean_Iba1_delta'].mean():.6g}",
        "",
        "## Donor-outlier summary",
        "",
        f"- Genes where one donor contributes at least 50% of total positive gliosis penalty: {outlier_dominated}",
        f"- Outlier-concentrated genes: {', '.join(outlier_genes) if outlier_genes else 'none'}",
        f"- Maximum top-donor contribution share across genes: {max_top_donor_share:.4f}",
        "",
        "## Sensitivity analysis summary",
        "",
        f"- Genes threshold-dependent between epsilon 0.001 and 0.01: {int(threshold_sensitive)}",
        f"- Genes reaching >=0.80 gliosis stability at epsilon 0.001 / 0.005 / 0.01: "
        f"{int((sensitivity_df['epsilon_0_001_gliosis_stability'] >= 0.80).sum())} / "
        f"{int((sensitivity_df['epsilon_0_005_gliosis_stability'] >= 0.80).sum())} / "
        f"{int((sensitivity_df['epsilon_0_01_gliosis_stability'] >= 0.80).sum())}",
        "- Sensitivity results are labeled `sensitivity_only_not_evidence_promotion`.",
        "- Official Level-2 statuses remain unchanged and not passed.",
        "",
        "## Recommendation",
        "",
        recommendation,
        "",
        "Do not change current evidence levels in this run. A future nonzero tolerance should be pre-registered before examining candidate outcomes and validated independently.",
        "",
        "## Claim boundary",
        "",
        "- Level-1 candidates remain model-implied and manifold-safe.",
        "- Level-2 internal robustness is not established.",
        "- No biological validation, causal mechanism, spatial support, or therapeutic efficacy is implied.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(diagnostics_df["failure_pattern"].value_counts().to_string())
    print(sensitivity_df["sensitivity_interpretation"].value_counts().to_string())
    print(f"Wrote {args.diagnostics_out}")
    print(f"Wrote {args.sensitivity_out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
