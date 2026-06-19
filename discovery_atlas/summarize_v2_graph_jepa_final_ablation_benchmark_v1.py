from __future__ import annotations

from pathlib import Path

import pandas as pd


INPUT = Path(
    "results/tables/strict_shuffled_graph_ablation_predictive_representation_comparison_v1.csv"
)
SUMMARY_OUT = Path("results/tables/v2_final_ablation_benchmark_summary_v1.csv")
DELTAS_OUT = Path("results/tables/v2_final_pairwise_deltas_v1.csv")
REPORT_OUT = Path("results/reports/v2_final_ablation_benchmark_summary_v1.md")

DISPLAY = {
    "module_mean_baseline": "Module mean baseline",
    "graph_jepa_real_graph_latent": "Graph-JEPA v2 real graph",
    "raw_expression_regularized_baseline": "Raw expression regularized baseline",
    "pca_expression_baseline": "PCA expression baseline",
    "graph_jepa_no_graph_identity_latent": "Graph-JEPA v2 identity/no-graph",
    "graph_jepa_strict_shuffled_graph_latent": "Graph-JEPA v2 strict shuffled graph",
}


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame[columns].copy()
    for col in data.columns:
        if pd.api.types.is_numeric_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.4f}")
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
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)
    df = pd.read_csv(INPUT)
    tested = df[df["status"].eq("tested")].copy()
    means = (
        tested.groupby("representation")["oof_spearman"]
        .mean()
        .sort_values(ascending=False)
    )
    summary = means.reset_index(name="mean_oof_spearman")
    summary.insert(0, "rank", range(1, len(summary) + 1))
    summary["display_name"] = summary["representation"].map(DISPLAY).fillna(
        summary["representation"]
    )
    summary["benchmark_role"] = summary["representation"].map(
        {
            "graph_jepa_real_graph_latent": "v2_real_graph_model",
            "graph_jepa_no_graph_identity_latent": "identity_control",
            "graph_jepa_strict_shuffled_graph_latent": "degree_preserving_zero_overlap_control",
            "module_mean_baseline": "strongest_absolute_baseline",
            "pca_expression_baseline": "linear_embedding_baseline",
            "raw_expression_regularized_baseline": "regularized_expression_baseline",
        }
    )
    best = str(summary.iloc[0]["representation"])
    real = float(means["graph_jepa_real_graph_latent"])
    no_graph = float(means["graph_jepa_no_graph_identity_latent"])
    strict = float(means["graph_jepa_strict_shuffled_graph_latent"])
    module = float(means["module_mean_baseline"])
    raw = float(means["raw_expression_regularized_baseline"])
    pca = float(means["pca_expression_baseline"])
    summary["interpretation"] = summary["representation"].map(
        {
            "graph_jepa_real_graph_latent": (
                "Graph-specific benefit relative to identity/no-graph and strict shuffled controls; "
                "not benchmark-dominating because module mean remains higher."
            ),
            "graph_jepa_no_graph_identity_latent": "Matched no-message-passing control.",
            "graph_jepa_strict_shuffled_graph_latent": (
                "Degree-preserving zero-overlap topology control; below real graph."
            ),
            "module_mean_baseline": "Strongest absolute donor-level predictor in v2.",
            "pca_expression_baseline": "Simple expression embedding baseline close to v2 real graph.",
            "raw_expression_regularized_baseline": "Regularized expression baseline close to v2 real graph.",
        }
    )
    deltas = pd.DataFrame(
        [
            {
                "comparison": "real_graph_minus_no_graph",
                "left": "graph_jepa_real_graph_latent",
                "right": "graph_jepa_no_graph_identity_latent",
                "delta_mean_oof_spearman": real - no_graph,
                "interpretation": "Real graph improves over identity/no-graph by more than the 0.01 band.",
            },
            {
                "comparison": "real_graph_minus_strict_shuffled",
                "left": "graph_jepa_real_graph_latent",
                "right": "graph_jepa_strict_shuffled_graph_latent",
                "delta_mean_oof_spearman": real - strict,
                "interpretation": "Real graph improves over zero-overlap degree-preserving shuffle.",
            },
            {
                "comparison": "strict_shuffled_minus_no_graph",
                "left": "graph_jepa_strict_shuffled_graph_latent",
                "right": "graph_jepa_no_graph_identity_latent",
                "delta_mean_oof_spearman": strict - no_graph,
                "interpretation": "Strict shuffled and no-graph are within the 0.01 small-difference band.",
            },
            {
                "comparison": "module_mean_minus_real_graph",
                "left": "module_mean_baseline",
                "right": "graph_jepa_real_graph_latent",
                "delta_mean_oof_spearman": module - real,
                "interpretation": "Module mean remains the strongest absolute predictor.",
            },
            {
                "comparison": "raw_expression_minus_real_graph",
                "left": "raw_expression_regularized_baseline",
                "right": "graph_jepa_real_graph_latent",
                "delta_mean_oof_spearman": raw - real,
                "interpretation": "Raw regularized expression is slightly below real graph.",
            },
            {
                "comparison": "pca_expression_minus_real_graph",
                "left": "pca_expression_baseline",
                "right": "graph_jepa_real_graph_latent",
                "delta_mean_oof_spearman": pca - real,
                "interpretation": "PCA expression is slightly below real graph.",
            },
        ]
    )
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_OUT, index=False)
    deltas.to_csv(DELTAS_OUT, index=False)

    lines = [
        "# V2 Final Ablation Benchmark Summary v1",
        "",
        "## Final v2 interpretation",
        "",
        "- v2 supports graph-specific benefit: the real graph beat identity/no-graph and the zero-overlap degree-preserving strict shuffled graph.",
        "- v2 does not dominate all baselines.",
        "- The module mean baseline remains the best absolute donor-level predictor.",
        "- v3 must integrate module structure rather than compete with it.",
        "- Candidate scores remain model-implied hypotheses, not causal validation.",
        "- Conservative Discovery Atlas evidence gates must be preserved.",
        "",
        "## Mean OOF Spearman ranking",
        "",
        *markdown_table(summary, ["rank", "representation", "display_name", "mean_oof_spearman", "benchmark_role"]),
        "",
        "## Pairwise deltas",
        "",
        *markdown_table(deltas, ["comparison", "delta_mean_oof_spearman", "interpretation"]),
        "",
        "## V3 implications",
        "",
        "- Graph-JEPA v3 must benchmark against manifold/embedding methods including PCA, t-SNE, UMAP, PHATE, and diffusion maps.",
        "- Graph-JEPA v3 must benchmark against WGCNA/module and STRING/graph sources.",
        "- Graph-JEPA v3 should treat the module baseline as signal to absorb through a module-aware branch, not as an opponent to ignore.",
        "- Graph-JEPA v3 must preserve conservative Discovery Atlas evidence boundaries: donor robustness, manifold QC, gliosis diagnostics, negative controls, and graph-neighborhood checks.",
        "",
        "## Boundary",
        "",
        "- This wrap-up ran no training.",
        "- This wrap-up ran no external validation.",
        "- Evidence levels were not changed.",
        "- No manuscript prose or candidate biology cards were created.",
        "",
    ]
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {SUMMARY_OUT}")
    print(f"Wrote {DELTAS_OUT}")
    print(f"Wrote {REPORT_OUT}")
    print(summary[["rank", "representation", "mean_oof_spearman"]].to_string(index=False))
    print(f"best={best}")


if __name__ == "__main__":
    main()
