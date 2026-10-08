from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


TIER1 = "scorecard_supported_isolated_hypothesis"
BROAD = "broad_state_caution"
PRIOR = "biological_anchor_prior_candidate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap donor-level counterfactual directions for audited genes."
    )
    parser.add_argument(
        "--shortlist",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v3.csv"),
    )
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_internal_robustness_stability_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_internal_robustness_stability_v1.md"
        ),
    )
    return parser.parse_args()


def discover_donor_files() -> list[Path]:
    root = Path("results")
    candidates = sorted(root.glob("**/*donor*.csv"))
    return [
        path
        for path in candidates
        if (
            "discovery_targeted_manifold_audit_v1" in str(path)
            or "discovery_tier1_pending_manifold_audit" in str(path)
        )
        and "_feature_wide_counterfactual_chunks" in str(path)
    ]


def find_delta_column(columns: list[str], marker: str) -> str:
    matches = [
        column
        for column in columns
        if column.startswith("delta_") and marker.lower() in column.lower()
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one delta column for {marker}, found {matches}")
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


def bootstrap_summary(
    donor: pd.DataFrame, n_bootstrap: int, seed: int
) -> dict[str, float]:
    columns = donor.columns.tolist()
    at8 = find_delta_column(columns, "AT8")
    abeta = find_delta_column(columns, "6e10")
    neun = find_delta_column(columns, "NeuN")
    gfap = find_delta_column(columns, "GFAP")
    iba1 = find_delta_column(columns, "Iba1")
    scores = np.column_stack(
        [
            -donor[at8].to_numpy(dtype=float),
            -donor[abeta].to_numpy(dtype=float),
            donor[neun].to_numpy(dtype=float),
            np.clip(donor[gfap].to_numpy(dtype=float), 0, None)
            + np.clip(donor[iba1].to_numpy(dtype=float), 0, None),
        ]
    )
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(scores), size=(n_bootstrap, len(scores)))
    means = scores[indices].mean(axis=1)
    names = [
        "tau_lowering",
        "amyloid_lowering",
        "neuron_preservation",
        "gliosis_penalty",
    ]
    result: dict[str, float] = {
        "tau_direction_stability": float(np.mean(means[:, 0] > 0)),
        "amyloid_direction_stability": float(np.mean(means[:, 1] > 0)),
        "neuron_direction_stability": float(np.mean(means[:, 2] > 0)),
        "gliosis_noninflating_stability": float(np.mean(means[:, 3] <= 0)),
    }
    for index, name in enumerate(names):
        result[f"{name}_bootstrap_mean"] = float(means[:, index].mean())
        result[f"{name}_ci_low"] = float(np.quantile(means[:, index], 0.025))
        result[f"{name}_ci_high"] = float(np.quantile(means[:, index], 0.975))
    return result


def classify_row(row: pd.Series) -> tuple[str, str, float | None, str]:
    if int(row["n_donors_available"]) == 0:
        return (
            "not_testable_missing_donor_level_deltas",
            "not_testable_missing_donor_level_deltas",
            None,
            "",
        )
    axes = required_axes(str(row["pathology_axis_class"]))
    minimum = min(float(row[axis]) for axis in axes) if axes else None
    axis_text = "|".join(axes)
    if row["final_tier"] == BROAD:
        return (
            "descriptive_caution_control",
            "not_applicable_caution_control",
            minimum,
            axis_text,
        )
    if row["final_tier"] == PRIOR:
        return (
            "descriptive_biological_anchor",
            "not_applicable_biological_anchor",
            minimum,
            axis_text,
        )
    if row["final_tier"] != TIER1:
        return (
            "descriptive_unpromoted_gene",
            "not_applicable_not_promoted",
            minimum,
            axis_text,
        )
    if not axes:
        return (
            "not_testable_no_class_specific_axes",
            "not_testable_no_class_specific_axes",
            None,
            "",
        )
    if minimum >= 0.80:
        return "robust_direction_stable", "pass", minimum, axis_text
    if minimum >= 0.60:
        return "robust_direction_mixed", "mixed", minimum, axis_text
    return "unstable_or_not_supported", "not_passed", minimum, axis_text


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame[columns].copy()
    if data.empty:
        return ["_No rows._"]
    for column in data.columns:
        if pd.api.types.is_numeric_dtype(data[column]):
            data[column] = data[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.5g}"
            )
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in data.itertuples(index=False, name=None)
    )
    return lines


def main() -> None:
    args = parse_args()
    shortlist = pd.read_csv(args.shortlist)
    donor_files = discover_donor_files()
    donor_frames = []
    for path in donor_files:
        frame = pd.read_csv(path)
        frame["donor_level_source"] = str(path)
        donor_frames.append(frame)
    donor_data = (
        pd.concat(donor_frames, ignore_index=True)
        if donor_frames
        else pd.DataFrame(columns=["perturbation", "Donor ID", "donor_level_source"])
    )
    if not donor_data.empty:
        duplicates = donor_data.duplicated(["perturbation", "Donor ID"])
        if duplicates.any():
            raise ValueError("Duplicate gene/donor rows across donor-level sources")

    rows = []
    for index, shortlist_row in shortlist.iterrows():
        gene = str(shortlist_row["gene"])
        donor = donor_data[donor_data["perturbation"].astype(str).str.upper().eq(gene)]
        row = {
            "gene": gene,
            "final_tier": shortlist_row["final_tier"],
            "pathology_axis_class": shortlist_row["pathology_axis_class"],
            "final_candidate_status_v3": shortlist_row["final_candidate_status_v3"],
            "n_donors_available": donor["Donor ID"].nunique() if not donor.empty else 0,
            "n_bootstrap": args.n_bootstrap if not donor.empty else 0,
            "donor_level_source": (
                "|".join(sorted(donor["donor_level_source"].unique()))
                if not donor.empty
                else ""
            ),
        }
        if not donor.empty:
            row.update(
                bootstrap_summary(
                    donor,
                    args.n_bootstrap,
                    args.seed + index,
                )
            )
        else:
            for column in [
                "tau_direction_stability",
                "amyloid_direction_stability",
                "neuron_direction_stability",
                "gliosis_noninflating_stability",
                "tau_lowering_bootstrap_mean",
                "tau_lowering_ci_low",
                "tau_lowering_ci_high",
                "amyloid_lowering_bootstrap_mean",
                "amyloid_lowering_ci_low",
                "amyloid_lowering_ci_high",
                "neuron_preservation_bootstrap_mean",
                "neuron_preservation_ci_low",
                "neuron_preservation_ci_high",
                "gliosis_penalty_bootstrap_mean",
                "gliosis_penalty_ci_low",
                "gliosis_penalty_ci_high",
            ]:
                row[column] = np.nan
        rows.append(row)

    result = pd.DataFrame(rows)
    classifications = result.apply(classify_row, axis=1)
    result["overall_internal_robustness_status"] = [value[0] for value in classifications]
    result["level_2_evidence_status"] = [value[1] for value in classifications]
    result["minimum_required_directional_stability"] = [
        value[2] for value in classifications
    ]
    result["required_axes"] = [value[3] for value in classifications]
    result["notes"] = np.where(
        result["n_donors_available"].eq(0),
        "No donor-level counterfactual delta rows were found for this gene.",
        np.where(
            result["final_tier"].eq(TIER1),
            "Internal donor-bootstrap robustness only; not biological validation.",
            "Descriptive donor-bootstrap profile; not eligible for model-hypothesis Level-2 promotion.",
        ),
    )
    if not result["gene"].is_unique:
        raise ValueError("Robustness output contains duplicate genes")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out, index=False)

    tested = result[result["n_donors_available"].gt(0)]
    not_tested = result[result["n_donors_available"].eq(0)]
    tier1 = result[result["final_tier"].eq(TIER1)]
    cautions = result[result["final_tier"].eq(BROAD)]
    display = [
        "gene",
        "pathology_axis_class",
        "n_donors_available",
        "minimum_required_directional_stability",
        "overall_internal_robustness_status",
        "level_2_evidence_status",
    ]
    lines = [
        "# Discovery Internal Robustness Stability v1",
        "",
        "## Donor-level files discovered and used",
        "",
        *[f"- `{path}`" for path in donor_files],
        "",
        f"- Genes with donor-level deltas: {len(tested)}",
        f"- Genes without donor-level deltas: {len(not_tested)}",
        f"- Bootstrap iterations per testable gene: {args.n_bootstrap}",
        "",
        "## Level-2 evidence status counts",
        "",
        *[
            f"- `{status}`: {count}"
            for status, count in result["level_2_evidence_status"].value_counts().items()
        ],
        "",
        "## Tier-1 robustness summary",
        "",
        *markdown_table(tier1, display),
        "",
        "## Caution-control robustness summary",
        "",
        *markdown_table(cautions[cautions["n_donors_available"].gt(0)], display),
        "",
        "## Claim boundary",
        "",
        "This is internal donor-resampling robustness of model-implied counterfactual directions. It is not external replication, biological validation, causal evidence, spatial evidence, or experimental efficacy.",
        "",
        "The gliosis noninflating criterion follows the pre-specified conservative rule: bootstrap mean `max(GFAP_delta, 0) + max(Iba1_delta, 0) <= 0`.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(result["level_2_evidence_status"].value_counts().to_string())
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
