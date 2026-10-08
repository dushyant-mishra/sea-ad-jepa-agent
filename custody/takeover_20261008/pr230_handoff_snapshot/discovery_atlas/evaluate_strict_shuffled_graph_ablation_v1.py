from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd

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
GRAPH_REPS = [
    "graph_jepa_real_graph_latent",
    "graph_jepa_no_graph_identity_latent",
    "graph_jepa_strict_shuffled_graph_latent",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate real, no-graph, and strict-shuffled Graph-JEPA ablations."
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
        default=Path("results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt"),
    )
    parser.add_argument(
        "--no-graph-checkpoint",
        type=Path,
        default=Path("results/models/ablation_no_graph_stage_b_v1/stage_b_adversarial.pt"),
    )
    parser.add_argument(
        "--strict-shuffled-checkpoint",
        type=Path,
        default=Path(
            "results/models/ablation_strict_shuffled_graph_stage_b_v1/stage_b_adversarial.pt"
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
        default=Path("results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv"),
    )
    parser.add_argument(
        "--strict-shuffled-edge-csv",
        type=Path,
        default=Path("results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv"),
    )
    parser.add_argument(
        "--baseline-table",
        type=Path,
        default=Path("results/tables/discovery_baseline_predictive_representation_comparison.csv"),
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=Path("results/reports/discovery_baseline_comparison_gate.md"),
    )
    parser.add_argument(
        "--no-graph-evaluation-table",
        type=Path,
        default=Path("results/tables/no_graph_ablation_predictive_representation_comparison_v1.csv"),
    )
    parser.add_argument(
        "--no-graph-evaluation-report",
        type=Path,
        default=Path("results/reports/no_graph_ablation_predictive_representation_comparison_v1.md"),
    )
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--small-difference-threshold", type=float, default=0.01)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/strict_shuffled_graph_ablation_predictive_representation_comparison_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/strict_shuffled_graph_ablation_predictive_representation_comparison_v1.md"
        ),
    )
    return parser.parse_args()


def small_difference(delta: float, threshold: float) -> bool:
    return abs(float(delta)) < threshold


def pair_label(a: str, b: str, delta: float, threshold: float) -> str:
    if small_difference(delta, threshold):
        return "inconclusive_small_difference"
    if a == "real_graph" and b == "no_graph":
        return "real_graph_outperforms_no_graph" if delta > 0 else "inconclusive_small_difference"
    if a == "real_graph" and b == "strict_shuffled":
        return (
            "real_graph_outperforms_strict_shuffled"
            if delta > 0
            else "strict_shuffled_outperforms_real_graph"
        )
    return "inconclusive_small_difference"


def conclusion_labels(means: pd.Series, threshold: float) -> list[str]:
    real = float(means["graph_jepa_real_graph_latent"])
    no_graph = float(means["graph_jepa_no_graph_identity_latent"])
    strict = float(means["graph_jepa_strict_shuffled_graph_latent"])
    module = float(means["module_mean_baseline"])
    labels = [
        pair_label("real_graph", "no_graph", real - no_graph, threshold),
        pair_label("real_graph", "strict_shuffled", real - strict, threshold),
    ]
    if small_difference(strict - real, threshold):
        labels.append("strict_shuffled_matches_real_graph")
    if not small_difference(strict - no_graph, threshold) and strict > no_graph:
        labels.append("connectivity_helps_but_topology_unclear")
    if not small_difference(real - no_graph, threshold) and not small_difference(real - strict, threshold) and real > no_graph and real > strict:
        labels.append("graph_specific_benefit_supported")
    if module >= max(float(value) for value in means.values):
        labels.append("module_mean_remains_best_absolute_predictor")
    return list(dict.fromkeys(labels))


def winner_label(values: pd.Series, threshold: float) -> str:
    ordered = values.sort_values(ascending=False)
    top = ordered.index[0]
    runner_up_delta = float(ordered.iloc[0] - ordered.iloc[1]) if len(ordered) > 1 else np.nan
    if len(ordered) > 1 and small_difference(runner_up_delta, threshold):
        return "inconclusive_small_difference"
    return str(top)


def main() -> None:
    args = parse_args()
    required = [
        args.h5ad,
        args.metadata,
        args.real_checkpoint,
        args.no_graph_checkpoint,
        args.strict_shuffled_checkpoint,
        args.real_edge_csv,
        args.no_graph_edge_csv,
        args.strict_shuffled_edge_csv,
        args.baseline_table,
        args.baseline_report,
        args.no_graph_evaluation_table,
        args.no_graph_evaluation_report,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing evaluation inputs: {missing}")

    expression, x_cells, genes, metadata = load_donor_matrices(args.h5ad, args.metadata)
    missing_targets = [target for target in TARGETS if target not in metadata.columns]
    if missing_targets:
        raise ValueError(f"Missing donor pathology targets: {missing_targets}")
    target_frame = metadata[TARGETS].apply(pd.to_numeric, errors="coerce")

    adata = ad.read_h5ad(args.h5ad, backed="r")
    donor_ids = normalize_donor_id(adata.obs["Donor ID"]).reset_index(drop=True)
    adata.file.close()
    device = choose_device(args.device)
    print(f"Evaluation device: {device}")

    latents = {
        "graph_jepa_real_graph_latent": graph_jepa_donor_latent(
            x_cells,
            genes,
            donor_ids,
            expression.index.tolist(),
            args.real_checkpoint,
            args.real_edge_csv,
            device,
            args.batch_size,
        ),
        "graph_jepa_no_graph_identity_latent": graph_jepa_donor_latent(
            x_cells,
            genes,
            donor_ids,
            expression.index.tolist(),
            args.no_graph_checkpoint,
            args.no_graph_edge_csv,
            device,
            args.batch_size,
        ),
        "graph_jepa_strict_shuffled_graph_latent": graph_jepa_donor_latent(
            x_cells,
            genes,
            donor_ids,
            expression.index.tolist(),
            args.strict_shuffled_checkpoint,
            args.strict_shuffled_edge_csv,
            device,
            args.batch_size,
        ),
    }
    shapes = {name: value.shape for name, value in latents.items()}
    if len(set(shapes.values())) != 1:
        raise ValueError(f"Graph latent shape mismatch: {shapes}")

    graph_results = predictive_comparison(latents, target_frame, args.seed)
    graph_results = graph_results[graph_results["status"].eq("tested")].copy()

    frozen = pd.read_csv(args.baseline_table)
    frozen = frozen[
        frozen["representation"].isin(SIMPLE_BASELINES)
        & frozen["status"].eq("tested")
        & frozen["target"].isin(TARGETS)
    ].copy()
    if len(frozen) != len(SIMPLE_BASELINES) * len(TARGETS):
        raise ValueError("Frozen simple baseline table is incomplete")

    comparison = pd.concat([graph_results, frozen], ignore_index=True)
    comparison["evaluation_source"] = np.where(
        comparison["representation"].isin(GRAPH_REPS),
        "fresh_checkpoint_evaluation",
        "frozen_existing_baseline_table",
    )
    means = comparison.groupby("representation")["oof_spearman"].mean().sort_values(ascending=False)
    real = float(means["graph_jepa_real_graph_latent"])
    no_graph = float(means["graph_jepa_no_graph_identity_latent"])
    strict = float(means["graph_jepa_strict_shuffled_graph_latent"])
    module = float(means["module_mean_baseline"])
    labels = conclusion_labels(means, args.small_difference_threshold)

    comparison["mean_oof_spearman"] = comparison["representation"].map(means)
    comparison["delta_real_minus_no_graph"] = real - no_graph
    comparison["delta_real_minus_strict_shuffled"] = real - strict
    comparison["delta_strict_shuffled_minus_no_graph"] = strict - no_graph
    comparison["delta_module_mean_minus_real_graph"] = module - real
    comparison["controlled_conclusion_labels"] = "|".join(labels)

    target_matrix = comparison.pivot(
        index="target", columns="representation", values="oof_spearman"
    )
    target_winners = target_matrix.apply(
        lambda row: winner_label(row, args.small_difference_threshold), axis=1
    ).reset_index(name="target_specific_winner")
    graph_target = target_matrix[GRAPH_REPS].copy()
    graph_target["target_specific_graph_winner"] = graph_target.apply(
        lambda row: winner_label(row, args.small_difference_threshold), axis=1
    )
    target_summary = (
        target_matrix.reset_index()
        .merge(target_winners, on="target", how="left")
        .merge(
            graph_target[["target_specific_graph_winner"]].reset_index(),
            on="target",
            how="left",
        )
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.out, index=False)

    lines = [
        "# Strict-Shuffled Graph Ablation Predictive Representation Comparison v1",
        "",
        "## Evaluation setup",
        "",
        "- No model training was run.",
        f"- Donor folds: same five-fold shuffled KFold logic as the baseline gate, seed `{args.seed}`.",
        "- Readout: fold-local StandardScaler plus Ridge; JEPA latents use alpha 10.",
        "- Targets: AT8, 6e10 / Aβ, GFAP, Iba1, and NeuN.",
        "- Simple baseline rows are copied unchanged from the frozen baseline comparison table.",
        "",
        "## Models/checkpoints evaluated",
        "",
        f"- Real graph: `{args.real_checkpoint}`",
        f"- Identity/no-graph: `{args.no_graph_checkpoint}`",
        f"- Strict shuffled graph: `{args.strict_shuffled_checkpoint}`",
        "",
        "## Edge definitions",
        "",
        f"- Real graph edges: `{args.real_edge_csv}`",
        f"- Identity/no-graph edges: `{args.no_graph_edge_csv}`",
        f"- Strict shuffled edges: `{args.strict_shuffled_edge_csv}`",
        "- Strict shuffled graph is degree-preserving with zero original-edge overlap.",
        "",
        "## Mean OOF Spearman ranking",
        "",
        *[f"- `{name}`: {value:.4f}" for name, value in means.items()],
        "",
        "## Target-specific winners",
        "",
        *markdown_table(
            target_summary,
            [
                "target",
                "target_specific_winner",
                "target_specific_graph_winner",
                "graph_jepa_real_graph_latent",
                "graph_jepa_no_graph_identity_latent",
                "graph_jepa_strict_shuffled_graph_latent",
                "module_mean_baseline",
                "pca_expression_baseline",
                "raw_expression_regularized_baseline",
            ],
        ),
        "",
        "## Real graph vs no graph",
        "",
        f"- Mean delta: {real - no_graph:.4f}",
        f"- Label: `{pair_label('real_graph', 'no_graph', real - no_graph, args.small_difference_threshold)}`",
        "",
        "## Real graph vs strict shuffled",
        "",
        f"- Mean delta: {real - strict:.4f}",
        f"- Label: `{pair_label('real_graph', 'strict_shuffled', real - strict, args.small_difference_threshold)}`",
        "",
        "## Strict shuffled vs no graph",
        "",
        f"- Mean delta: {strict - no_graph:.4f}",
        "",
        "## Baseline context",
        "",
        f"- Module mean minus real graph: {module - real:.4f}",
        f"- Module mean remains strongest absolute predictor: `{means.index[0] == 'module_mean_baseline'}`",
        f"- PCA expression mean OOF Spearman: {float(means['pca_expression_baseline']):.4f}",
        f"- Raw expression regularized mean OOF Spearman: {float(means['raw_expression_regularized_baseline']):.4f}",
        "",
        "## Controlled conclusion labels",
        "",
        *[f"- `{label}`" for label in labels],
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
        "## Interpretation boundaries",
        "",
        "- Donor-level association only.",
        "- No causal claims.",
        "- No target validation.",
        "- No external validation.",
        "- No evidence level changes.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print(means.to_string())
    print("Labels:", ", ".join(labels))


if __name__ == "__main__":
    main()
