from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


METRICS = (
    "mean_oof_spearman|target_specific_oof_spearman|oof_pearson|mae|rmse|"
    "cleaner_vs_broad_separation|tier1_overlap|graph_neighborhood_artifact_behavior|"
    "manifold_safety|level2_gliosis_robustness"
)

REQUIRED_OUTPUTS = (
    "model_checkpoint|training_history_csv|run_manifest|"
    "predictive_representation_comparison|discovery_ranking_calibration|"
    "tier1_manifold_audit|internal_robustness_table|gliosis_diagnostic_table"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze an approval-gated ablation training and comparison protocol."
    )
    parser.add_argument(
        "--decision-packet",
        type=Path,
        default=Path(
            "results/tables/discovery_ablation_training_decision_packet_v1.csv"
        ),
    )
    parser.add_argument(
        "--edge-manifest",
        type=Path,
        default=Path(
            "results/tables/ablation_edge_sets/graph_ablation_edge_set_manifest_v1.csv"
        ),
    )
    parser.add_argument(
        "--decision-report",
        type=Path,
        default=Path(
            "results/reports/discovery_ablation_training_decision_packet_v1.md"
        ),
    )
    parser.add_argument(
        "--edge-report",
        type=Path,
        default=Path("results/reports/graph_ablation_edge_set_manifest_v1.md"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_ablation_training_protocol_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_ablation_training_protocol_v1.md"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    packet = pd.read_csv(args.decision_packet)
    edges = pd.read_csv(args.edge_manifest)
    for path in [args.decision_report, args.edge_report]:
        if not path.exists():
            raise FileNotFoundError(path)

    edge_paths = edges.set_index("edge_set_name")["path"].to_dict()
    no_graph_edge = edge_paths["no_graph_identity_edges_v1"]
    shuffled_edge = edge_paths["shuffled_graph_edges_v1"]
    h5ad = "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"

    rows = [
        {
            "ablation_name": "real_graph_reference",
            "training_order": 0,
            "input_edge_set": "results/tables/v2_graph_consensus_edge_index.csv",
            "training_status": "existing_reference",
            "approval_required": True,
            "frozen_command_template": "not_run_existing_checkpoint=results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt",
            "required_outputs": REQUIRED_OUTPUTS,
            "comparison_metrics": METRICS,
            "compute_risk": "none_for_existing_reference; evaluation only",
            "notes": "Frozen reference for matched comparisons; do not retrain implicitly.",
        },
        {
            "ablation_name": "no_graph_jepa",
            "training_order": 1,
            "input_edge_set": no_graph_edge,
            "training_status": "not_run_ready_for_approval",
            "approval_required": True,
            "frozen_command_template": (
                "python scripts/train_graph_jepa_stage_a_fast.py "
                f"--h5ad {h5ad} --edge-csv {no_graph_edge} "
                "--out-dir results/models/ablation_no_graph_stage_a_v1 "
                "--epochs <MATCHED_EPOCHS> --seed <FROZEN_SEED> "
                "--history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv "
                "--log-file results/logs/ablation_no_graph_stage_a_v1.log"
            ),
            "required_outputs": REQUIRED_OUTPUTS,
            "comparison_metrics": METRICS,
            "compute_risk": "high; matched Stage A and Stage B GPU training plus downstream audits",
            "notes": "First recommended training; cleanest test of informative graph message passing.",
        },
        {
            "ablation_name": "shuffled_graph_jepa",
            "training_order": 2,
            "input_edge_set": shuffled_edge,
            "training_status": "not_run_ready_for_approval",
            "approval_required": True,
            "frozen_command_template": (
                "python scripts/train_graph_jepa_stage_a_fast.py "
                f"--h5ad {h5ad} --edge-csv {shuffled_edge} "
                "--out-dir results/models/ablation_shuffled_graph_stage_a_v1 "
                "--epochs <MATCHED_EPOCHS> --seed <FROZEN_SEED> "
                "--history-csv results/tables/ablation_shuffled_graph_stage_a_v1_history.csv "
                "--log-file results/logs/ablation_shuffled_graph_stage_a_v1.log"
            ),
            "required_outputs": REQUIRED_OUTPUTS,
            "comparison_metrics": METRICS,
            "compute_risk": "high; matched multi-seed training recommended to assess topology specificity",
            "notes": "Degree-preserving deterministic edge input is ready; tests topology specificity.",
        },
        {
            "ablation_name": "expression_only_autoencoder",
            "training_order": 3,
            "input_edge_set": "not_applicable",
            "training_status": "not_run_requires_design_and_script_readiness",
            "approval_required": True,
            "frozen_command_template": "not_available_until_expression_only_architecture_and_cli_are_frozen",
            "required_outputs": REQUIRED_OUTPUTS,
            "comparison_metrics": METRICS,
            "compute_risk": "high_and_architecturally_divergent; requires new objective and fairness review",
            "notes": "Later-stage learned expression baseline; current candidate script help fails.",
        },
    ]
    protocol = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    protocol.to_csv(args.out, index=False)

    packet_order = packet.set_index("artifact_name")[
        "recommended_training_order"
    ].to_dict()
    for ablation in ["no_graph_jepa", "shuffled_graph_jepa", "expression_only_autoencoder"]:
        observed = int(
            protocol.loc[
                protocol["ablation_name"].eq(ablation), "training_order"
            ].iloc[0]
        )
        if observed != int(packet_order[ablation]):
            raise ValueError(f"Protocol order differs from decision packet: {ablation}")

    lines = [
        "# Discovery Ablation Training Protocol v1",
        "",
        "## Scope",
        "",
        "This protocol freezes future ablation inputs, fairness requirements, outputs, and evaluation metrics. No training was run.",
        "",
        "## Ablations and order",
        "",
        "0. `real_graph_reference` — existing frozen comparator.",
        "1. `no_graph_jepa` — first recommended future training; cleanest test of informative graph message passing.",
        "2. `shuffled_graph_jepa` — tests biological topology specificity with preserved degree sequence.",
        "3. `expression_only_autoencoder` — later learned expression comparator after architecture and CLI are frozen.",
        "",
        "## Training fairness contract",
        "",
        f"- Same H5AD: `{h5ad}`",
        "- Exact same 2,957-feature order.",
        "- Same frozen random seed set for matched runs.",
        "- Same latent dimension and encoder capacity where applicable.",
        "- Same Stage A and Stage B epoch schedules, masks, optimization settings, and checkpoint selection.",
        "- Same pathology-head evaluation pipeline.",
        "- Same donor-level cross-validation folds.",
        "- Same downstream scorecard and ranking scripts.",
        "- Same targeted manifold audit settings.",
        "- Same donor-bootstrap robustness and strict gliosis diagnostic.",
        "",
        "## Required outputs per trained ablation",
        "",
        *[f"- `{item}`" for item in REQUIRED_OUTPUTS.split("|")],
        "",
        "## Exact comparison metrics",
        "",
        *[f"- `{item}`" for item in METRICS.split("|")],
        "",
        "## Frozen command templates",
        "",
        *[
            f"### {row.ablation_name}\n\n"
            f"- Status: `{row.training_status}`\n"
            f"- Edge set: `{row.input_edge_set}`\n"
            f"- Compute risk: {row.compute_risk}\n\n"
            "```text\n"
            f"{row.frozen_command_template}\n"
            "```\n"
            for row in protocol.itertuples(index=False)
        ],
        "",
        "## Approval gate",
        "",
        "Before any training, require:",
        "",
        "- explicit user approval;",
        "- a command with no unresolved placeholders;",
        "- a unique output directory and history path;",
        "- frozen seed or seed set;",
        "- matched epoch and optimization settings;",
        "- expected runtime and storage estimate;",
        "- confirmation that no existing artifact will be overwritten.",
        "",
        "## First recommended future command",
        "",
        "The first recommended future training is `no_graph_jepa`. Its command template is recorded in the protocol table and above, but it must not be executed until placeholders are resolved and approval is given.",
        "",
        "## Boundary",
        "",
        "- No training was run.",
        "- This protocol does not claim ablation outcomes.",
        "- This protocol does not change evidence levels.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(protocol[["ablation_name", "training_order", "input_edge_set", "training_status"]].to_string(index=False))
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
