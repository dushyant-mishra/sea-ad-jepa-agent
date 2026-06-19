from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ORDER = {
    "no_graph_jepa": 1,
    "shuffled_graph_jepa": 2,
    "expression_only_autoencoder": 3,
}

QUESTIONS = {
    "no_graph_jepa": "Does graph message passing add value beyond the same JEPA architecture without informative graph connectivity?",
    "shuffled_graph_jepa": "Does the biological graph topology matter beyond an arbitrary graph with matched architecture and training budget?",
    "expression_only_autoencoder": "Does Graph-JEPA provide value beyond a learned expression-only representation?",
}

COMPUTE_RISKS = {
    "no_graph_jepa": "Requires a clearly defined identity/no-graph topology and matched Stage A/B training; GPU time and storage comparable to Graph-JEPA training.",
    "shuffled_graph_jepa": "Requires deterministic degree-aware or edge-count-matched shuffling, multiple seeds, and matched training; topology generation can introduce hidden confounds.",
    "expression_only_autoencoder": "Requires an explicit architecture/objective and matched latent dimension; architectural divergence complicates fairness and may require new training code.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare an approval-gated ablation training decision packet."
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path(
            "results/tables/discovery_ablation_artifact_inventory_v1.csv"
        ),
    )
    parser.add_argument(
        "--predictive-baselines",
        type=Path,
        default=Path(
            "results/tables/discovery_baseline_predictive_representation_comparison.csv"
        ),
    )
    parser.add_argument(
        "--annotated-scorecard",
        type=Path,
        default=Path(
            "results/tables/discovery_internal_evidence_scorecard_v1_annotated.csv"
        ),
    )
    parser.add_argument(
        "--gliosis-diagnostics",
        type=Path,
        default=Path(
            "results/tables/discovery_level2_gliosis_failure_diagnostics_v1.csv"
        ),
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=Path("results/reports/discovery_baseline_comparison_gate.md"),
    )
    parser.add_argument(
        "--readiness-report",
        type=Path,
        default=Path(
            "results/reports/discovery_ablation_artifact_readiness_v1.md"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_ablation_training_decision_packet_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_ablation_training_decision_packet_v1.md"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inventory = pd.read_csv(args.inventory)
    predictive = pd.read_csv(args.predictive_baselines)
    scorecard = pd.read_csv(args.annotated_scorecard)
    diagnostics = pd.read_csv(args.gliosis_diagnostics)
    for path in [args.baseline_report, args.readiness_report]:
        if not path.exists():
            raise FileNotFoundError(path)

    targets = ["no_graph_jepa", "shuffled_graph_jepa", "expression_only_autoencoder"]
    rows = []
    metrics = (
        "donor_level_pathology_prediction|ranking_calibration|"
        "cleaner_vs_broad_separation|tier1_manifold_safety|"
        "internal_robustness_gliosis_diagnostic"
    )
    for artifact in targets:
        source = inventory[inventory["artifact_name"].eq(artifact)]
        if source.empty:
            raise ValueError(f"Missing inventory row: {artifact}")
        source_row = source.iloc[0]
        rows.append(
            {
                "artifact_name": artifact,
                "current_status": source_row["status"],
                "scientific_question": QUESTIONS[artifact],
                "required_training_or_artifact": (
                    "matched identity/no-graph JEPA artifact"
                    if artifact == "no_graph_jepa"
                    else "matched deterministic shuffled-graph JEPA artifact"
                    if artifact == "shuffled_graph_jepa"
                    else "matched expression-only autoencoder artifact"
                ),
                "recommended_training_order": ORDER[artifact],
                "candidate_script": source_row[
                    "training_script_candidate"
                ],
                "candidate_config": source_row["config_candidate"],
                "confirmed_script_flags": source_row["confirmed_script_flags"],
                "smoke_test_command": source_row["smoke_test_command"],
                "confirmed_command_template": source_row[
                    "full_training_command_template"
                ],
                "comparison_metrics_after_training": metrics,
                "expected_runtime_risk": COMPUTE_RISKS[artifact],
                "approval_required_before_training": True,
                "decision_status": "do_not_train_until_approved",
            }
        )
    packet = pd.DataFrame(rows).sort_values("recommended_training_order")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    packet.to_csv(args.out, index=False)

    tested = predictive[predictive["status"].eq("tested")]
    means = tested.groupby("representation")["oof_spearman"].mean().sort_values(
        ascending=False
    )
    level_counts = scorecard["current_max_evidence_level"].value_counts()
    failure_counts = diagnostics["failure_pattern"].value_counts()

    lines = [
        "# Discovery Ablation Training Decision Packet v1",
        "",
        "## Decision context",
        "",
        "- Graph-JEPA superiority over simpler tested baselines was not established.",
        *[
            f"- Mean OOF Spearman — `{representation}`: {value:.4f}"
            for representation, value in means.items()
        ],
        f"- Current evidence levels: {dict(level_counts)}",
        f"- Level-2 failure patterns: {dict(failure_counts)}",
        "",
        "## Missing ablation artifacts",
        "",
        *[
            f"- `{row.artifact_name}`: `{row.current_status}`"
            for row in packet.itertuples(index=False)
        ],
        "",
        "## Recommended training order",
        "",
        "1. `no_graph_jepa` — directly tests whether graph message passing contributes beyond the same broad JEPA setup.",
        "2. `shuffled_graph_jepa` — tests whether biological topology is specifically useful rather than arbitrary connectivity.",
        "3. `expression_only_autoencoder` — tests a learned expression-only representation but requires greater architectural divergence.",
        "",
        "## Scientific questions and command readiness",
        "",
        "| order | artifact | scientific question | script | smoke command | full command template |",
        "| --- | --- | --- | --- | --- | --- |",
        *[
            "| "
            + " | ".join(
                str(value).replace("|", "/")
                for value in [
                    row.recommended_training_order,
                    row.artifact_name,
                    row.scientific_question,
                    row.candidate_script,
                    row.smoke_test_command,
                    row.confirmed_command_template,
                ]
            )
            + " |"
            for row in packet.itertuples(index=False)
        ],
        "",
        "## Required post-training comparisons",
        "",
        "- Donor-level pathology prediction under identical donor folds.",
        "- Discovery ranking calibration and top-k overlap.",
        "- Cleaner-versus-broad separation.",
        "- Tier-1 targeted manifold safety using the same audit settings.",
        "- Donor-bootstrap internal robustness and the same strict gliosis diagnostic.",
        "",
        "## Compute and design risks",
        "",
        *[
            f"- `{row.artifact_name}`: {row.expected_runtime_risk}"
            for row in packet.itertuples(index=False)
        ],
        "",
        "## Do not train until approved",
        "",
        "No ablation training was run while preparing this packet. Every proposed training action requires explicit approval, a frozen comparison protocol, matched compute budgets, and pre-specified seeds and outputs.",
        "",
        "## Boundary",
        "",
        "Missing ablations are not negative evidence. This packet is a technical decision aid and does not modify candidate evidence levels or scientific claims.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(packet[["artifact_name", "current_status", "recommended_training_order"]].to_string(index=False))
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
