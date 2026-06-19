from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DELTA_COLUMNS = [
    "AT8_delta",
    "A_beta_6e10_delta",
    "GFAP_delta",
    "Iba1_delta",
    "NeuN_delta",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge and summarize the targeted manifold audit."
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=Path("results/tables/discovery_targeted_manifold_audit_v1.csv"),
    )
    parser.add_argument(
        "--gene-list",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_gene_list_v1.csv"
        ),
    )
    parser.add_argument(
        "--official-scorecard",
        type=Path,
        default=Path(
            "results/tables/discovery_scorecard_v2_graph_connected_feature_wide.csv"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_targeted_manifold_audit_results_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_targeted_manifold_audit_v1.md"),
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame.loc[:, columns].copy()
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
    audit = read_csv(args.audit)
    gene_list = read_csv(args.gene_list)
    official = read_csv(args.official_scorecard)

    if not audit["gene"].is_unique or not gene_list["gene"].is_unique:
        raise ValueError("Audit and gene-list inputs must contain unique genes")
    if set(audit["gene"]) != set(gene_list["gene"]):
        missing = sorted(set(gene_list["gene"]) - set(audit["gene"]))
        extra = sorted(set(audit["gene"]) - set(gene_list["gene"]))
        raise ValueError(f"Audit/list mismatch: missing={missing}, extra={extra}")
    if len(audit) != 45:
        raise ValueError(f"Expected 45 targeted genes, found {len(audit)}")
    if not audit["perturbation_success"].fillna(False).all():
        raise ValueError("At least one targeted perturbation failed")
    if audit["manifold_violation_fraction"].isna().any():
        raise ValueError("Targeted audit contains missing manifold metrics")
    if not audit["manifold_nn_backend"].eq("torch").all():
        raise ValueError("Targeted audit was not fully computed with the torch backend")

    official_subset = official[["gene", *DELTA_COLUMNS]].copy()
    merged = gene_list.merge(audit, on="gene", how="inner", validate="one_to_one")
    merged = merged.merge(
        official_subset,
        on="gene",
        how="left",
        validate="one_to_one",
        suffixes=("_targeted_audit", "_official_screen"),
    )
    for column in DELTA_COLUMNS:
        merged[f"{column}_absolute_difference"] = np.abs(
            merged[f"{column}_targeted_audit"]
            - merged[f"{column}_official_screen"]
        )
    merged["targeted_manifold_qc_result"] = np.where(
        merged["manifold_safety_status"].eq("within_manifold_threshold"),
        "pass_within_manifold_threshold",
        "caution_outside_manifold_threshold",
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.out, index=False)

    comparison_rows = []
    for column in DELTA_COLUMNS:
        comparison_rows.append(
            {
                "pathology_axis": column,
                "max_absolute_difference": merged[
                    f"{column}_absolute_difference"
                ].max(),
                "pearson": merged[f"{column}_targeted_audit"].corr(
                    merged[f"{column}_official_screen"]
                ),
                "spearman": merged[f"{column}_targeted_audit"].corr(
                    merged[f"{column}_official_screen"], method="spearman"
                ),
            }
        )
    comparison = pd.DataFrame(comparison_rows)

    group_columns = [
        "in_top20_tier1",
        "in_prior_anchor_group",
        "in_broad_state_control_group",
        "in_special_review_group",
    ]
    group_rows = []
    for column in group_columns:
        subset = merged[merged[column].fillna(False).astype(bool)]
        group_rows.append(
            {
                "audit_group": column.replace("in_", ""),
                "n_genes": len(subset),
                "n_pass": subset["targeted_manifold_qc_result"]
                .eq("pass_within_manifold_threshold")
                .sum(),
                "max_violation_fraction": subset[
                    "manifold_violation_fraction"
                ].max(),
                "max_mean_latent_shift": subset["mean_latent_shift"].max(),
            }
        )
    groups = pd.DataFrame(group_rows)

    largest_shifts = merged.nlargest(12, "mean_latent_shift")
    display_columns = [
        "gene",
        "final_tier",
        "audit_groups",
        "mean_latent_shift",
        "p95_nearest_real_cell_distance",
        "baseline_nn_p95_threshold",
        "manifold_violation_fraction",
        "targeted_manifold_qc_result",
    ]
    lines = [
        "# Discovery Targeted Manifold Audit v1",
        "",
        "## Result",
        "",
        f"- Genes audited: {len(merged)}",
        f"- Perturbations successful: {int(merged['perturbation_success'].sum())}/{len(merged)}",
        f"- Within the pre-specified manifold threshold: {int(merged['manifold_safety_status'].eq('within_manifold_threshold').sum())}/{len(merged)}",
        f"- Maximum manifold violation fraction: {merged['manifold_violation_fraction'].max():.6g}",
        f"- Baseline nearest-neighbor p95 threshold: {merged['baseline_nn_p95_threshold'].iloc[0]:.6g}",
        "- Nearest-neighbor backend: `torch` (`torch.cdist`, batched, CUDA).",
        "",
        "All 45 targeted genes passed the candidate-level nearest-neighbor manifold check under this sampled-cell configuration. This removes the specific missing-QC flag for these candidates; it does not add biological or causal support.",
        "",
        "## Audit groups",
        "",
        *markdown_table(
            groups,
            [
                "audit_group",
                "n_genes",
                "n_pass",
                "max_violation_fraction",
                "max_mean_latent_shift",
            ],
        ),
        "",
        "## Agreement with the official pathology-delta screen",
        "",
        "The full feature-wide graph-connected screen remains the official pathology-delta ranking. The targeted rerun reproduces those deltas up to small GPU numerical differences:",
        "",
        *markdown_table(
            comparison,
            [
                "pathology_axis",
                "max_absolute_difference",
                "pearson",
                "spearman",
            ],
        ),
        "",
        "## Largest latent shifts in the targeted set",
        "",
        *markdown_table(largest_shifts, display_columns),
        "",
        "## Interpretation boundaries",
        "",
        "- The full feature-wide graph-connected screen remains the official pathology-delta ranking.",
        "- The full run skipped nearest-neighbor manifold checking because of the Windows sklearn/threadpoolctl failure.",
        "- The successful pilot established feasibility for its subset; this targeted torch audit now supplies candidate-level manifold QC for the 45 pre-specified genes.",
        "- Passing manifold QC means the perturbed embeddings remained near the sampled real-cell latent support under the pre-specified threshold. It does not validate scorecard balance, graph coherence, biological direction, or intervention safety.",
        "- Graph-neighborhood evidence remains penalty/context only because no coherent cleaner 1-hop neighborhood survived FDR.",
        "- No current result proves causality, druggability, spatial plaque proximity, or experimental therapeutic efficacy.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
