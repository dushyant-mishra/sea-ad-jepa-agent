from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


TIER1 = "scorecard_supported_isolated_hypothesis"
BROAD = "broad_state_caution"
PRIOR = "biological_anchor_prior_candidate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve Tier-1 manifold QC in final candidate shortlist v3."
    )
    parser.add_argument(
        "--shortlist-v2",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v2.csv"),
    )
    parser.add_argument(
        "--original-audit",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_results_v1.csv"
        ),
    )
    parser.add_argument(
        "--pending-tier1-audit",
        type=Path,
        default=Path(
            "results/tables/discovery_tier1_pending_manifold_audit_v1.csv"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v3.csv"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_final_candidate_shortlist_v3.md"),
    )
    return parser.parse_args()


def v3_evidence_tier(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    status = str(row["manifold_qc_status"])
    if tier == TIER1:
        if status == "manifold_safe":
            return "scorecard_supported_manifold_safe_isolated_hypothesis"
        if status == "borderline_manifold_shift":
            return "scorecard_supported_but_manifold_borderline"
        if status == "manifold_violation_warning":
            return "demoted_manifold_warning"
        return "scorecard_supported_manifold_qc_unresolved"
    return str(row["final_evidence_tier_v2"])


def v3_candidate_status(row: pd.Series) -> str:
    tier = str(row["final_tier"])
    status = str(row["manifold_qc_status"])
    if tier == TIER1:
        if status == "manifold_safe":
            return "promoted_model_hypothesis_manifold_qc_pass"
        if status == "borderline_manifold_shift":
            return "promoted_with_manifold_caution"
        if status == "manifold_violation_warning":
            return "demoted_after_manifold_qc"
        return "tier1_manifold_qc_unresolved"
    return str(row["final_candidate_status_v2"])


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame[columns].copy()
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


def main() -> None:
    args = parse_args()
    v2 = pd.read_csv(args.shortlist_v2)
    original = pd.read_csv(args.original_audit)
    pending = pd.read_csv(args.pending_tier1_audit)

    if not v2["gene"].is_unique or not pending["gene"].is_unique:
        raise ValueError("Shortlist and pending audit genes must be unique")
    if set(original["gene"]) & set(pending["gene"]):
        raise ValueError("Original and pending targeted audits overlap")

    result = v2.copy()
    result["manifold_qc_source"] = "not_targeted_audited"
    result.loc[
        result["gene"].isin(original["gene"]), "manifold_qc_source"
    ] = "original_45_gene_targeted_audit_v1"

    pending_columns = [
        "gene",
        "manifold_qc_status",
        "manifold_violation_fraction",
        "manifold_qc_interpretation",
        "mean_nearest_real_cell_distance",
        "p95_nearest_real_cell_distance",
        "baseline_nn_p95_threshold",
        "mean_latent_shift",
        "median_latent_shift",
        "manifold_nn_backend",
    ]
    pending_map = pending[pending_columns].set_index("gene")
    pending_mask = result["gene"].isin(pending_map.index)
    for column in pending_columns[1:]:
        result.loc[pending_mask, column] = result.loc[pending_mask, "gene"].map(
            pending_map[column]
        )
    result.loc[pending_mask, "targeted_manifold_audited"] = True
    result.loc[pending_mask, "manifold_qc_source"] = "pending_tier1_targeted_audit_v1"

    result["tier1_manifold_qc_resolved"] = (
        result["final_tier"].eq(TIER1)
        & ~result["manifold_qc_status"].eq("not_audited")
        & result["manifold_qc_status"].notna()
    )
    tier1 = result[result["final_tier"].eq(TIER1)]
    all_tier1_audited = bool(tier1["tier1_manifold_qc_resolved"].all())
    result["all_tier1_manifold_audited"] = all_tier1_audited
    result["final_evidence_tier_v3"] = result.apply(v3_evidence_tier, axis=1)
    result["final_candidate_status_v3"] = result.apply(
        v3_candidate_status, axis=1
    )

    if len(tier1) != 41:
        raise ValueError(f"Expected 41 Tier-1 genes, found {len(tier1)}")
    if not all_tier1_audited:
        unresolved = result.loc[
            result["final_tier"].eq(TIER1)
            & ~result["tier1_manifold_qc_resolved"],
            "gene",
        ].tolist()
        raise ValueError(f"Unresolved Tier-1 manifold QC: {unresolved}")
    if result["gene"].duplicated().any():
        raise ValueError("Shortlist v3 contains duplicate genes")
    if result[
        result["final_tier"].eq(BROAD)
        & result["final_candidate_status_v3"].str.startswith("promoted")
    ].shape[0]:
        raise ValueError("Broad-state caution genes cannot be promoted")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out, index=False)

    tier1 = result[result["final_tier"].eq(TIER1)].sort_values(
        "therapeutic_like_score_percentile", ascending=False
    )
    anchors = result[result["final_tier"].eq(PRIOR)].sort_values(
        "therapeutic_like_score_percentile", ascending=False
    )
    cautions = result[result["final_tier"].eq(BROAD)].sort_values(
        "therapeutic_like_score_percentile", ascending=False
    )
    display = [
        "gene",
        "therapeutic_like_score_percentile",
        "manifold_qc_status",
        "manifold_violation_fraction",
        "manifold_qc_source",
        "final_evidence_tier_v3",
        "final_candidate_status_v3",
    ]
    lines = [
        "# Discovery Final Candidate Shortlist v3",
        "",
        "## Summary",
        "",
        f"- Total retained genes: {len(result)}",
        f"- Total Tier-1 genes: {len(tier1)}",
        f"- Tier-1 manifold audited: {int(tier1['tier1_manifold_qc_resolved'].sum())}/{len(tier1)}",
        f"- Tier-1 manifold safe: {int(tier1['manifold_qc_status'].eq('manifold_safe').sum())}",
        f"- Tier-1 borderline: {int(tier1['manifold_qc_status'].eq('borderline_manifold_shift').sum())}",
        f"- Tier-1 manifold warnings: {int(tier1['manifold_qc_status'].eq('manifold_violation_warning').sum())}",
        "",
        "## Final promoted model hypotheses",
        "",
        *markdown_table(tier1, display),
        "",
        "## Biological anchors",
        "",
        *markdown_table(anchors, display),
        "",
        "## Broad-state caution examples",
        "",
        *markdown_table(cautions, display),
        "",
        "## Interpretation boundaries",
        "",
        "- All Tier-1 genes have now received targeted manifold QC.",
        "- A manifold-QC pass removes a technical perturbation-support concern; it does not provide biological validation.",
        "- No candidate has FDR-supported coherent cleaner 1-hop graph-neighborhood support; graph evidence remains penalty/context only.",
        "- Broad-state caution genes remain unpromoted even when manifold-safe.",
        "- Candidate status remains model-implied and does not prove causality, druggability, spatial plaque proximity, or therapeutic efficacy.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print(tier1["manifold_qc_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
