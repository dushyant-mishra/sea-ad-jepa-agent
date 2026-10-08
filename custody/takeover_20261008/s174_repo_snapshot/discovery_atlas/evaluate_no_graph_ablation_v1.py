from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import torch

from discovery_atlas.baseline_comparison_gate import (
    graph_jepa_donor_latent,
    load_donor_matrices,
    markdown_table,
    predictive_comparison,
)
from sea_ad_jepa.data import normalize_donor_id
from scripts.train_graph_jepa_stage_a_fast import choose_device


TARGETS = [
    "percent AT8 positive area_Grey matter",
    "percent 6e10 positive area_Grey matter",
    "percent GFAP positive area_Grey matter",
    "percent Iba1 positive area_Grey matter",
    "percent NeuN positive area_Grey matter",
]
SIMPLE_BASELINES = [
    "module_mean_baseline",
    "pca_expression_baseline",
    "raw_expression_regularized_baseline",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the trained no-graph Graph-JEPA against the real graph."
    )
    parser.add_argument(
        "--h5ad",
        type=Path,
        default=Path(
            "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"
        ),
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv"),
    )
    parser.add_argument(
        "--real-checkpoint",
        type=Path,
        default=Path(
            "results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt"
        ),
    )
    parser.add_argument(
        "--no-graph-checkpoint",
        type=Path,
        default=Path(
            "results/models/ablation_no_graph_stage_b_v1/stage_b_adversarial.pt"
        ),
    )
    parser.add_argument(
        "--real-edge-csv",
        type=Path,
        default=Path("results/tables/v2_graph_consensus_edge_index.csv"),
    )
    parser.add_argument(
        "--no-graph-edge-csv",
        type=Path,
        default=Path(
            "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv"
        ),
    )
    parser.add_argument(
        "--baseline-table",
        type=Path,
        default=Path(
            "results/tables/discovery_baseline_predictive_representation_comparison.csv"
        ),
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=Path("results/reports/discovery_baseline_comparison_gate.md"),
    )
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--small-difference-threshold", type=float, default=0.01
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/no_graph_ablation_predictive_representation_comparison_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/no_graph_ablation_predictive_representation_comparison_v1.md"
        ),
    )
    return parser.parse_args()


def conclusion_label(real_mean: float, no_graph_mean: float, threshold: float) -> str:
    difference = real_mean - no_graph_mean
    if abs(difference) < 1e-8:
        return "no_graph_matches_real_graph"
    if abs(difference) < threshold:
        return "inconclusive_small_difference"
    if difference > 0:
        return "real_graph_outperforms_no_graph"
    return "no_graph_outperforms_real_graph"


def target_winner(real_value: float, no_graph_value: float, threshold: float) -> str:
    difference = real_value - no_graph_value
    if abs(difference) < threshold:
        return "small_difference_no_target_winner"
    return "real_graph" if difference > 0 else "no_graph_identity"


def main() -> None:
    args = parse_args()
    required = [
        args.h5ad,
        args.metadata,
        args.real_checkpoint,
        args.no_graph_checkpoint,
        args.real_edge_csv,
        args.no_graph_edge_csv,
        args.baseline_table,
        args.baseline_report,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing evaluation inputs: {missing}")

    expression, x_cells, genes, metadata = load_donor_matrices(
        args.h5ad, args.metadata
    )
    missing_targets = [target for target in TARGETS if target not in metadata.columns]
    if missing_targets:
        raise ValueError(f"Missing donor pathology targets: {missing_targets}")
    target_frame = metadata[TARGETS].apply(pd.to_numeric, errors="coerce")

    adata = ad.read_h5ad(args.h5ad, backed="r")
    donor_ids = normalize_donor_id(adata.obs["Donor ID"]).reset_index(drop=True)
    adata.file.close()
    device = choose_device(args.device)
    print(f"Evaluation device: {device}")

    real_latent = graph_jepa_donor_latent(
        x_cells,
        genes,
        donor_ids,
        expression.index.tolist(),
        args.real_checkpoint,
        args.real_edge_csv,
        device,
        args.batch_size,
    )
    no_graph_latent = graph_jepa_donor_latent(
        x_cells,
        genes,
        donor_ids,
        expression.index.tolist(),
        args.no_graph_checkpoint,
        args.no_graph_edge_csv,
        device,
        args.batch_size,
    )
    if real_latent.shape != no_graph_latent.shape:
        raise ValueError(
            f"Latent shape mismatch: real={real_latent.shape}, no_graph={no_graph_latent.shape}"
        )

    evaluated = predictive_comparison(
        {
            "graph_jepa_real_graph_latent": real_latent,
            "graph_jepa_no_graph_identity_latent": no_graph_latent,
        },
        target_frame,
        args.seed,
    )
    evaluated = evaluated[evaluated["status"].eq("tested")].copy()

    frozen = pd.read_csv(args.baseline_table)
    frozen = frozen[
        frozen["representation"].isin(SIMPLE_BASELINES)
        & frozen["status"].eq("tested")
        & frozen["target"].isin(TARGETS)
    ].copy()
    expected_baseline_rows = len(SIMPLE_BASELINES) * len(TARGETS)
    if len(frozen) != expected_baseline_rows:
        raise ValueError(
            f"Expected {expected_baseline_rows} frozen baseline rows, found {len(frozen)}"
        )
    comparison = pd.concat([evaluated, frozen], ignore_index=True)
    comparison["evaluation_source"] = np.where(
        comparison["representation"].str.startswith("graph_jepa"),
        "fresh_checkpoint_evaluation",
        "frozen_existing_baseline_table",
    )

    means = comparison.groupby("representation")["oof_spearman"].mean()
    real_mean = float(means["graph_jepa_real_graph_latent"])
    no_graph_mean = float(means["graph_jepa_no_graph_identity_latent"])
    difference = real_mean - no_graph_mean
    label = conclusion_label(
        real_mean, no_graph_mean, args.small_difference_threshold
    )
    comparison["mean_oof_spearman"] = comparison["representation"].map(means)
    comparison["real_minus_no_graph_mean_oof_spearman"] = difference
    comparison["conclusion_label"] = label

    pair = evaluated.pivot(
        index="target", columns="representation", values="oof_spearman"
    ).reset_index()
    real_column = "graph_jepa_real_graph_latent"
    no_graph_column = "graph_jepa_no_graph_identity_latent"
    pair["real_minus_no_graph_oof_spearman"] = (
        pair[real_column] - pair[no_graph_column]
    )
    pair["target_specific_winner"] = pair.apply(
        lambda row: target_winner(
            float(row[real_column]),
            float(row[no_graph_column]),
            args.small_difference_threshold,
        ),
        axis=1,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.out, index=False)

    sorted_means = means.sort_values(ascending=False)
    lines = [
        "# No-Graph Ablation Predictive Representation Comparison v1",
        "",
        "## Evaluation setup",
        "",
        f"- Real-graph checkpoint: `{args.real_checkpoint}`",
        f"- No-graph checkpoint: `{args.no_graph_checkpoint}`",
        f"- Real graph edge index: `{args.real_edge_csv}`",
        f"- No-graph identity edge set: `{args.no_graph_edge_csv}`",
        f"- Donor folds: identical five-fold shuffled KFold logic, seed `{args.seed}`.",
        "- Readout: fold-local StandardScaler followed by ridge regression with alpha 10 for both JEPA latents.",
        "- Targets: AT8, 6e10 / Aβ, GFAP, Iba1, and NeuN.",
        "- Simpler comparator rows are copied unchanged from the frozen baseline table.",
        "- No model training occurred during this evaluation.",
        "",
        "## Real graph vs no-graph mean performance",
        "",
        f"- `graph_jepa_real_graph_latent`: {real_mean:.4f} mean OOF Spearman",
        f"- `graph_jepa_no_graph_identity_latent`: {no_graph_mean:.4f} mean OOF Spearman",
        f"- Real minus no-graph: {difference:.4f}",
        f"- Small-difference threshold: {args.small_difference_threshold:.3f}",
        f"- Controlled conclusion: `{label}`",
        "",
        "All representation means:",
        "",
        *[f"- `{name}`: {value:.4f}" for name, value in sorted_means.items()],
        "",
        "## Target-specific comparison",
        "",
        *markdown_table(
            pair,
            [
                "target",
                real_column,
                no_graph_column,
                "real_minus_no_graph_oof_spearman",
                "target_specific_winner",
            ],
        ),
        "",
        "## Full predictive metrics",
        "",
        *markdown_table(
            comparison,
            [
                "representation",
                "target",
                "n_donors",
                "r2_mean",
                "oof_pearson",
                "oof_spearman",
                "mae_mean",
                "rmse_mean",
            ],
        ),
        "",
        "## Interpretation",
        "",
        "This result isolates the predictive association contribution of informative "
        "graph propagation under the completed single-seed ablation. It does not yet "
        "test whether biological topology is superior to a degree-preserving shuffled graph.",
        "",
        "## Boundary",
        "",
        "- This is donor-level association, not a causal test.",
        "- No evidence levels changed.",
        "- No shuffled-graph result is available yet.",
        "- No external validation was run.",
        "- No claim is made about causality, druggability, spatial plaque proximity, or experimental therapeutic efficacy.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print(f"Real graph mean OOF Spearman: {real_mean:.6f}")
    print(f"No graph mean OOF Spearman: {no_graph_mean:.6f}")
    print(f"Conclusion: {label}")


if __name__ == "__main__":
    main()
