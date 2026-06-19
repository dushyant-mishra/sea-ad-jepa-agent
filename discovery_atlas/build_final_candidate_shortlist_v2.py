from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


TIER1 = "scorecard_supported_isolated_hypothesis"
PRIOR = "biological_anchor_prior_candidate"
BROAD = "broad_state_caution"
UNSUPPORTED = "unsupported_or_deprioritized"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build final candidate shortlist v2 with targeted manifold QC."
    )
    parser.add_argument(
        "--shortlist-v1",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v1.csv"),
    )
    parser.add_argument(
        "--manifold-audit",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_results_v1.csv"
        ),
    )
    parser.add_argument(
        "--audit-gene-list",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_gene_list_v1.csv"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v2.csv"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_final_candidate_shortlist_v2.md"),
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def classify_manifold_status(value: float) -> str:
    if pd.isna(value):
        return "not_audited"
    if value <= 0.05:
        return "manifold_safe"
    if value <= 0.10:
        return "borderline_manifold_shift"
    return "manifold_violation_warning"


def manifold_interpretation(row: pd.Series) -> str:
    status = str(row["manifold_qc_status"])
    if status == "manifold_safe":
        return "targeted_perturbation_remained_within_sampled_latent_support"
    if status == "borderline_manifold_shift":
        return "targeted_perturbation_has_borderline_latent_support_shift"
    if status == "manifold_violation_warning":
        return "targeted_perturbation_exceeded_latent_support_threshold"
    return "not_selected_for_targeted_manifold_audit_v1"


def evidence_tier(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    status = str(row["manifold_qc_status"])
    if tier == TIER1:
        if status == "manifold_safe":
            return "scorecard_supported_manifold_safe_isolated_hypothesis"
        if status == "borderline_manifold_shift":
            return "scorecard_supported_but_manifold_borderline"
        if status == "manifold_violation_warning":
            return "demoted_manifold_warning"
        return "scorecard_supported_pending_targeted_manifold_qc"
    if tier == PRIOR:
        if status == "manifold_safe":
            return "prior_anchor_manifold_safe"
        if status == "borderline_manifold_shift":
            return "prior_anchor_manifold_borderline"
        if status == "manifold_violation_warning":
            return "prior_anchor_manifold_warning"
        return "prior_anchor_not_targeted_manifold_audited"
    if tier == BROAD:
        if status == "manifold_safe":
            return "manifold_safe_caution_control"
        if status == "borderline_manifold_shift":
            return "broad_state_caution_manifold_borderline"
        if status == "manifold_violation_warning":
            return "broad_state_caution_manifold_warning"
        return "broad_state_caution"
    if status == "manifold_safe":
        return "manifold_safe_but_not_scorecard_promoted"
    if status == "borderline_manifold_shift":
        return "unpromoted_manifold_borderline"
    if status == "manifold_violation_warning":
        return "unpromoted_manifold_warning"
    return "unsupported_or_deprioritized_not_targeted_audited"


def promotion_or_demotion(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    status = str(row["manifold_qc_status"])
    if status == "not_audited":
        return "not_audited_no_change"
    if status == "manifold_violation_warning":
        return "demoted_or_flagged_by_manifold_warning"
    if status == "borderline_manifold_shift":
        return "flagged_by_borderline_manifold_shift"
    if tier == TIER1:
        return "manifold_qc_pass_support_retained"
    if tier == PRIOR:
        return "manifold_qc_pass_anchor_retained"
    if tier == BROAD:
        return "manifold_qc_pass_caution_retained_not_promoted"
    return "manifold_qc_pass_but_not_promoted"


def candidate_status(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    status = str(row["manifold_qc_status"])
    if tier == TIER1 and status == "manifold_safe":
        return "promoted_model_hypothesis_manifold_qc_pass"
    if tier == TIER1 and status == "not_audited":
        return "scorecard_supported_pending_manifold_qc"
    if tier == TIER1:
        return "scorecard_supported_manifold_flag"
    if tier == PRIOR and status == "manifold_safe":
        return "biological_anchor_manifold_qc_pass"
    if tier == PRIOR:
        return "biological_anchor_not_scorecard_promoted"
    if tier == BROAD:
        return "caution_control_not_promoted"
    if status == "manifold_safe":
        return "not_promoted_despite_manifold_qc_pass"
    return "not_promoted_under_conservative_rules"


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame.loc[:, columns].copy()
    if data.empty:
        return ["_No candidates._"]
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
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in data.itertuples(index=False, name=None)
    )
    return lines


def validate(shortlist: pd.DataFrame, audit: pd.DataFrame) -> None:
    if not shortlist["gene"].is_unique:
        raise ValueError("Shortlist v2 contains duplicate genes")
    if int(shortlist["targeted_manifold_audited"].sum()) != len(audit):
        raise ValueError("Audited-gene count does not match targeted audit")
    audited = shortlist[shortlist["targeted_manifold_audited"]]
    if audited["manifold_qc_status"].eq("not_audited").any():
        raise ValueError("Audited genes cannot have not_audited manifold status")
    if shortlist.loc[
        ~shortlist["targeted_manifold_audited"], "manifold_violation_fraction"
    ].notna().any():
        raise ValueError("Unaudited genes cannot have manifold violation values")
    broad_promoted = shortlist[
        shortlist["final_tier"].eq(BROAD)
        & shortlist["final_candidate_status_v2"].str.startswith("promoted")
    ]
    if not broad_promoted.empty:
        raise ValueError("Broad-state caution genes must not be promoted")
    unsupported_promoted = shortlist[
        shortlist["final_tier"].eq(UNSUPPORTED)
        & shortlist["final_candidate_status_v2"].str.startswith("promoted")
    ]
    if not unsupported_promoted.empty:
        raise ValueError("Unsupported/deprioritized genes must not be promoted")


def write_report(shortlist: pd.DataFrame, args: argparse.Namespace) -> None:
    columns = [
        "gene",
        "final_tier",
        "therapeutic_like_score_percentile",
        "manifold_qc_status",
        "manifold_violation_fraction",
        "final_evidence_tier_v2",
        "final_candidate_status_v2",
    ]
    promoted = shortlist[
        shortlist["final_candidate_status_v2"].eq(
            "promoted_model_hypothesis_manifold_qc_pass"
        )
    ].sort_values("therapeutic_like_score_percentile", ascending=False)
    pending = shortlist[
        shortlist["final_candidate_status_v2"].eq(
            "scorecard_supported_pending_manifold_qc"
        )
    ].sort_values("therapeutic_like_score_percentile", ascending=False)
    borderline = shortlist[
        shortlist["manifold_qc_status"].eq("borderline_manifold_shift")
    ]
    warnings = shortlist[
        shortlist["manifold_qc_status"].eq("manifold_violation_warning")
    ]
    anchors = shortlist[shortlist["final_tier"].eq(PRIOR)].sort_values(
        "therapeutic_like_score_percentile", ascending=False
    )
    cautions = shortlist[shortlist["final_tier"].eq(BROAD)].sort_values(
        "therapeutic_like_score_percentile", ascending=False
    )

    lines = [
        "# Discovery Final Candidate Shortlist v2",
        "",
        "## Summary",
        "",
        f"- Total genes retained from v1: {len(shortlist)}",
        f"- Targeted manifold-audited genes: {int(shortlist['targeted_manifold_audited'].sum())}",
        f"- Manifold-safe targeted genes: {int(shortlist['manifold_qc_status'].eq('manifold_safe').sum())}",
        f"- Borderline targeted genes: {len(borderline)}",
        f"- Manifold-warning targeted genes: {len(warnings)}",
        f"- Tier-1 hypotheses with targeted manifold-QC pass: {len(promoted)}",
        f"- Tier-1 hypotheses still pending targeted manifold QC: {len(pending)}",
        "",
        "Manifold safety is a QC gate, not a positive biological ranking signal. It clears the missing-manifold flag for audited candidates but does not rescue broad-state cautions or unsupported genes.",
        "",
        "## Manifold status counts",
        "",
        *[
            f"- `{status}`: {count}"
            for status, count in shortlist["manifold_qc_status"].value_counts().items()
        ],
        "",
        "## Final promoted model hypotheses",
        "",
        *markdown_table(promoted, columns),
        "",
        "## Tier-1 hypotheses pending targeted manifold QC",
        "",
        *markdown_table(pending, columns),
        "",
        "## Borderline candidates",
        "",
        *markdown_table(borderline, columns),
        "",
        "## Demoted or warning candidates",
        "",
        *markdown_table(warnings, columns),
        "",
        "## Prior biological anchors",
        "",
        *markdown_table(anchors, columns),
        "",
        "## Broad-state caution examples",
        "",
        *markdown_table(cautions, columns),
        "",
        "## Interpretation boundaries",
        "",
        "- No candidates have FDR-supported coherent cleaner 1-hop graph neighborhoods; graph-neighborhood evidence remains penalty/context only.",
        "- Manifold QC checks whether targeted perturbations remain close to the learned sampled-cell latent manifold.",
        "- A manifold-QC pass does not prove biological relevance, causal mechanism, druggability, spatial plaque proximity, intervention safety, or therapeutic efficacy.",
        "- The full feature-wide graph-connected screen remains the official pathology-delta ranking.",
        "- Candidate status remains model-implied and requires donor, subtype, external, and experimental validation.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    shortlist = read_csv(args.shortlist_v1)
    audit = read_csv(args.manifold_audit)
    audit_gene_list = read_csv(args.audit_gene_list)

    if set(audit["gene"]) != set(audit_gene_list["gene"]):
        raise ValueError("Targeted audit and pre-specified audit gene list differ")

    audit_columns = [
        "gene",
        "manifold_violation_fraction",
        "mean_nearest_real_cell_distance",
        "p95_nearest_real_cell_distance",
        "baseline_nn_p95_threshold",
        "mean_latent_shift",
        "median_latent_shift",
        "manifold_nn_backend",
    ]
    result = shortlist.merge(
        audit[audit_columns],
        on="gene",
        how="left",
        validate="one_to_one",
    )
    result["targeted_manifold_audited"] = result["gene"].isin(audit["gene"])
    result["manifold_qc_status"] = result["manifold_violation_fraction"].map(
        classify_manifold_status
    )
    result["manifold_qc_interpretation"] = result.apply(
        manifold_interpretation, axis=1
    )
    result["promotion_or_demotion_after_manifold"] = result.apply(
        promotion_or_demotion, axis=1
    )
    result["final_evidence_tier_v2"] = result.apply(evidence_tier, axis=1)
    result["final_candidate_status_v2"] = result.apply(candidate_status, axis=1)

    validate(result, audit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out, index=False)
    write_report(result, args)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print(result["final_evidence_tier_v2"].value_counts().to_string())


if __name__ == "__main__":
    main()
