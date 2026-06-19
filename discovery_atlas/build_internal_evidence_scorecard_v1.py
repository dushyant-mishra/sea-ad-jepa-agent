from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


TIER1 = "scorecard_supported_isolated_hypothesis"
BROAD = "broad_state_caution"
PRIOR = "biological_anchor_prior_candidate"

CLAIM_BOUNDARY = (
    "Internal model evidence only. No current result proves causality, druggability, "
    "spatial plaque proximity, external cohort generalization, or experimental efficacy."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an internal evidence scorecard from completed gates."
    )
    parser.add_argument(
        "--shortlist",
        type=Path,
        default=Path("results/tables/discovery_final_candidate_shortlist_v3.csv"),
    )
    parser.add_argument(
        "--predictive-baselines",
        type=Path,
        default=Path(
            "results/tables/discovery_baseline_predictive_representation_comparison.csv"
        ),
    )
    parser.add_argument(
        "--ranking-baselines",
        type=Path,
        default=Path(
            "results/tables/discovery_baseline_discovery_ranking_comparison.csv"
        ),
    )
    parser.add_argument(
        "--robustness",
        type=Path,
        default=Path(
            "results/tables/discovery_internal_robustness_stability_v1.csv"
        ),
    )
    parser.add_argument(
        "--open-validation-plan",
        type=Path,
        default=Path("results/reports/open_validation_framework_plan_v1.md"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_internal_evidence_scorecard_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_internal_evidence_scorecard_v1.md"
        ),
    )
    return parser.parse_args()


def model_evidence(row: pd.Series) -> str:
    if row["final_tier"] == TIER1:
        return "pass"
    if row["final_tier"] == BROAD:
        return "not_promoted_caution_control"
    if row["final_tier"] == PRIOR:
        return "biological_anchor_not_model_promoted"
    return "not_promoted"


def manifold_evidence(row: pd.Series) -> str:
    audited = str(row["manifold_qc_status"]) != "not_audited"
    if row["final_tier"] == TIER1:
        return "pass" if row["manifold_qc_status"] == "manifold_safe" else "not_passed"
    if audited:
        return "descriptive_qc_only"
    return "not_audited"


def max_level(row: pd.Series) -> object:
    if row["final_tier"] != TIER1:
        return "not_promoted"
    level = 0
    if row["manifold_qc_evidence"] == "pass":
        level = 1
    if row["internal_robustness_evidence"] == "pass":
        level = 2
    return level


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame[columns].copy()
    if data.empty:
        return ["_No rows._"]
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
    predictive = pd.read_csv(args.predictive_baselines)
    pd.read_csv(args.ranking_baselines)
    robustness = pd.read_csv(args.robustness)
    if not args.open_validation_plan.exists():
        raise FileNotFoundError(args.open_validation_plan)

    tested = predictive[predictive["status"].eq("tested")]
    mean_spearman = tested.groupby("representation")["oof_spearman"].mean()
    if mean_spearman.idxmax() == "graph_jepa_real_graph_latent":
        raise ValueError(
            "Baseline conclusion changed; update Level-3 evidence rules deliberately."
        )
    target_winners = (
        tested.sort_values(["target", "oof_spearman"], ascending=[True, False])
        .groupby("target", as_index=False)
        .first()
    )
    graph_wins = target_winners[
        target_winners["representation"].eq("graph_jepa_real_graph_latent")
    ]["target"].tolist()
    baseline_notes = (
        "Overall superiority not established. Graph-JEPA had the highest tested "
        "OOF Spearman for: "
        + (", ".join(graph_wins) if graph_wins else "no individual target")
        + "."
    )

    result = shortlist.merge(
        robustness[
            [
                "gene",
                "level_2_evidence_status",
                "overall_internal_robustness_status",
            ]
        ],
        on="gene",
        how="left",
        validate="one_to_one",
    )
    result["model_implied_evidence"] = result.apply(model_evidence, axis=1)
    result["manifold_qc_evidence"] = result.apply(manifold_evidence, axis=1)
    result["internal_robustness_evidence"] = result[
        "level_2_evidence_status"
    ].fillna("not_testable")
    result["baseline_comparison_evidence"] = "competitive_not_superior"
    result["baseline_comparison_notes"] = baseline_notes
    result["external_cohort_evidence"] = "not_run"
    result["cell_state_evidence"] = "not_run"
    result["spatial_evidence"] = "not_run"
    result["experimental_evidence"] = "not_run"
    result["current_max_evidence_level"] = result.apply(max_level, axis=1)
    result["evidence_status_summary"] = result.apply(
        lambda row: (
            f"model={row['model_implied_evidence']}; "
            f"manifold={row['manifold_qc_evidence']}; "
            f"robustness={row['internal_robustness_evidence']}; "
            "baseline=competitive_not_superior"
        ),
        axis=1,
    )
    result["claim_boundary"] = CLAIM_BOUNDARY

    if not result["gene"].is_unique:
        raise ValueError("Evidence scorecard contains duplicate genes")
    tier1 = result[result["final_tier"].eq(TIER1)]
    broad = result[result["final_tier"].eq(BROAD)]
    if not tier1["manifold_qc_evidence"].eq("pass").all():
        raise ValueError("All Tier-1 genes must have manifold-QC pass")
    if broad["model_implied_evidence"].eq("pass").any():
        raise ValueError("Broad-state cautions cannot pass model evidence")
    forbidden = [
        "external_cohort_evidence",
        "cell_state_evidence",
        "spatial_evidence",
        "experimental_evidence",
    ]
    if any(result[column].eq("pass").any() for column in forbidden):
        raise ValueError("Unrun higher evidence levels cannot pass")
    if result["baseline_comparison_evidence"].eq("pass").any():
        raise ValueError("Baseline Level 3 cannot pass globally")

    columns = [
        "gene",
        "final_tier",
        "final_evidence_tier_v3",
        "final_candidate_status_v3",
        "model_implied_evidence",
        "manifold_qc_evidence",
        "internal_robustness_evidence",
        "baseline_comparison_evidence",
        "baseline_comparison_notes",
        "external_cohort_evidence",
        "cell_state_evidence",
        "spatial_evidence",
        "experimental_evidence",
        "current_max_evidence_level",
        "evidence_status_summary",
        "claim_boundary",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result[columns].to_csv(args.out, index=False)

    anchors = result[result["final_tier"].eq(PRIOR)]
    display = [
        "gene",
        "model_implied_evidence",
        "manifold_qc_evidence",
        "internal_robustness_evidence",
        "baseline_comparison_evidence",
        "current_max_evidence_level",
    ]
    lines = [
        "# Discovery Internal Evidence Scorecard v1",
        "",
        "## Current maximum evidence-level counts",
        "",
        *[
            f"- `{level}`: {count}"
            for level, count in result["current_max_evidence_level"]
            .astype(str)
            .value_counts()
            .items()
        ],
        "",
        "## Tier-1 internal evidence",
        "",
        *markdown_table(tier1, display),
        "",
        "## Prior biological anchors",
        "",
        *markdown_table(anchors, display),
        "",
        "## Broad-state caution controls",
        "",
        *markdown_table(broad, display),
        "",
        "## Why Level 3 is not globally passed",
        "",
        "The baseline gate found Graph-JEPA competitive but not superior overall. Module means slightly led average out-of-fold Spearman. Therefore `baseline_comparison_evidence` is `competitive_not_superior` and does not raise `current_max_evidence_level`.",
        "",
        baseline_notes,
        "",
        "## What remains before external validation",
        "",
        "- No external cohort concordance has been run.",
        "- No dedicated cell-state/subtype concordance gate has been run.",
        "- No spatial or plaque-context evidence has been run.",
        "- No experimental perturbation validation has been run.",
        "",
        "## Claim boundary",
        "",
        CLAIM_BOUNDARY,
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(result["current_max_evidence_level"].astype(str).value_counts().to_string())
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
