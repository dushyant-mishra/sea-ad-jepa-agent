from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


NAMED_GENES = [
    "RC3H1",
    "PAFAH1B1",
    "DLG1",
    "FIP1L1",
    "SLAIN2",
    "PTPN18",
    "KIF2A",
    "ERC1",
    "GSK3B",
    "TLR2",
    "APP",
    "APOE",
    "CD4",
]

CLEANER_CLASSES = {
    "tau_lowering_neuron_preserving",
    "dual_pathology_lowering_neuron_preserving",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run graph-neighborhood coherence against the full scorecard-v2 gene universe."
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_graph_connected_feature_wide.csv"),
    )
    parser.add_argument(
        "--edges",
        type=Path,
        default=Path("results/tables/v2_graph_consensus_edges.csv"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_graph_neighborhood_coherence.csv"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_scorecard_v2_graph_neighborhood_coherence.md"),
    )
    parser.add_argument("--n-nulls", type=int, default=1000)
    parser.add_argument("--degree-bins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=31)
    return parser.parse_args()


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def read_graph(path: Path, universe: set[str]) -> dict[str, set[str]]:
    edges = read_required_csv(path)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for source, target in edges[["source", "target"]].itertuples(index=False, name=None):
        source = str(source).upper()
        target = str(target).upper()
        if source == target or source not in universe or target not in universe:
            continue
        adjacency[source].add(target)
        adjacency[target].add(source)
    return dict(adjacency)


def empirical_p(observed: float, null: np.ndarray, higher_is_better: bool = True) -> float:
    valid = null[np.isfinite(null)]
    if valid.size == 0 or not np.isfinite(observed):
        return float("nan")
    extreme = np.sum(valid >= observed) if higher_is_better else np.sum(valid <= observed)
    return float((int(extreme) + 1) / (valid.size + 1))


def z_score(observed: float, null: np.ndarray) -> float:
    valid = null[np.isfinite(null)]
    if valid.size < 2 or not np.isfinite(observed):
        return float("nan")
    sd = float(np.std(valid, ddof=1))
    if sd == 0:
        return float("nan")
    return float((observed - float(np.mean(valid))) / sd)


def benjamini_hochberg(values: pd.Series) -> pd.Series:
    p = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    adjusted = np.full(p.shape, np.nan)
    valid = np.flatnonzero(np.isfinite(p))
    if valid.size == 0:
        return pd.Series(adjusted, index=values.index)
    order = valid[np.argsort(p[valid])]
    ranked = p[order] * valid.size / np.arange(1, valid.size + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted[order] = np.minimum(ranked, 1.0)
    return pd.Series(adjusted, index=values.index)


def add_degree_bins(scorecard: pd.DataFrame, adjacency: dict[str, set[str]], n_bins: int) -> pd.DataFrame:
    out = scorecard.copy()
    out["degree"] = out["gene"].map(lambda gene: len(adjacency.get(gene, set())))
    ranks = out["degree"].rank(method="average")
    out["degree_bin"] = pd.qcut(
        ranks,
        q=min(n_bins, len(out)),
        labels=False,
        duplicates="drop",
    ).astype(int)
    return out


def precompute_neighborhood_metrics(
    scorecard: pd.DataFrame,
    adjacency: dict[str, set[str]],
) -> pd.DataFrame:
    indexed = scorecard.set_index("gene")
    classes = sorted(indexed["pathology_axis_class"].astype(str).unique())
    rows: list[dict[str, object]] = []
    for gene, record in indexed.iterrows():
        neighbors = sorted(adjacency.get(gene, set()).intersection(indexed.index))
        target_class = str(record["pathology_axis_class"])
        neighbor_frame = indexed.loc[neighbors] if neighbors else indexed.iloc[0:0]
        same_class = (
            int(neighbor_frame["pathology_axis_class"].eq(target_class).sum())
            if not neighbor_frame.empty
            else 0
        )
        row: dict[str, object] = {
                "gene": gene,
                "pathology_axis_class": target_class,
                "degree": int(record["degree"]),
                "degree_bin": int(record["degree_bin"]),
                "n_scored_neighbors": len(neighbors),
                "n_same_class_neighbors": same_class,
                "same_class_neighbor_fraction": (
                    float(same_class / len(neighbors)) if neighbors else np.nan
                ),
                "mean_neighbor_therapeutic_like_percentile": (
                    float(neighbor_frame["therapeutic_like_score_percentile"].mean())
                    if not neighbor_frame.empty
                    else np.nan
                ),
                "mean_neighbor_broad_shift_percentile": (
                    float(neighbor_frame["broad_shift_score_percentile"].mean())
                    if not neighbor_frame.empty
                    else np.nan
                ),
                "therapeutic_like_score_percentile": float(
                    record["therapeutic_like_score_percentile"]
                ),
                "tau_lowering_score_percentile": float(
                    record["tau_lowering_score_percentile"]
                ),
                "neuron_preservation_score_percentile": float(
                    record["neuron_preservation_score_percentile"]
                ),
                "gliosis_penalty_percentile": float(record["gliosis_penalty_percentile"]),
                "broad_shift_score_percentile": float(record["broad_shift_score_percentile"]),
        }
        for class_name in classes:
            row[f"neighbor_class_fraction::{class_name}"] = (
                float(neighbor_frame["pathology_axis_class"].astype(str).eq(class_name).mean())
                if not neighbor_frame.empty
                else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def null_pool(
    metrics: pd.DataFrame,
    gene: str,
    degree_bin: int,
) -> tuple[pd.DataFrame, bool, int | None]:
    pool = metrics[(metrics["degree_bin"] == degree_bin) & metrics["gene"].ne(gene)]
    if not pool.empty:
        return pool, False, degree_bin
    available = sorted(metrics.loc[metrics["gene"].ne(gene), "degree_bin"].unique())
    if not available:
        return metrics.iloc[0:0], False, None
    nearest = min(available, key=lambda value: abs(int(value) - degree_bin))
    return (
        metrics[(metrics["degree_bin"] == nearest) & metrics["gene"].ne(gene)],
        True,
        int(nearest),
    )


def classify_status(row: pd.Series) -> str:
    if row["degree"] == 0 or row["n_scored_neighbors"] == 0:
        return "not_testable"
    same_class_supported = (
        row["same_class_neighbor_FDR"] <= 0.05 and row["same_class_neighbor_z"] > 1.0
    )
    therapeutic_supported = (
        row["neighbor_therapeutic_FDR"] <= 0.05 and row["neighbor_therapeutic_z"] > 1.0
    )
    broad_supported = row["neighbor_broad_shift_FDR"] <= 0.05 and row[
        "neighbor_broad_shift_z"
    ] > 1.0
    if row["pathology_axis_class"] == "broad_reactive_state_shift" and (
        same_class_supported
        or broad_supported
        or row["mean_neighbor_broad_shift_percentile"] >= 75
    ):
        return "broad_reactive_neighborhood"
    if row["pathology_axis_class"] in CLEANER_CLASSES and same_class_supported and (
        therapeutic_supported or row["mean_neighbor_therapeutic_like_percentile"] >= 65
    ):
        return "coherent_cleaner_neighborhood"
    if row["therapeutic_like_score_percentile"] >= 90 and not (
        same_class_supported or therapeutic_supported
    ):
        return "isolated_high_score_gene"
    if same_class_supported or therapeutic_supported or broad_supported:
        return "no_graph_support"
    return "no_graph_support"


def evidence_basis(row: pd.Series) -> str:
    if row["coherence_status"] == "not_testable":
        return "not_testable"
    degree_matched_supported = any(
        [
            row["same_class_neighbor_FDR"] <= 0.05 and row["same_class_neighbor_z"] > 1.0,
            row["neighbor_therapeutic_FDR"] <= 0.05 and row["neighbor_therapeutic_z"] > 1.0,
            row["neighbor_broad_shift_FDR"] <= 0.05 and row["neighbor_broad_shift_z"] > 1.0,
        ]
    )
    if degree_matched_supported:
        return "degree_matched_enrichment"
    if row["coherence_status"] == "broad_reactive_neighborhood":
        return "absolute_neighbor_profile_only"
    if row["coherence_status"] == "isolated_high_score_gene":
        return "high_focal_score_without_neighbor_enrichment"
    return "no_degree_matched_enrichment"


def run_nulls(
    metrics: pd.DataFrame,
    n_nulls: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for _, row in metrics.iterrows():
        pool, used_fallback, matched_bin = null_pool(
            metrics,
            str(row["gene"]),
            int(row["degree_bin"]),
        )
        if pool.empty:
            rows.append(
                {
                    **row.to_dict(),
                    "degree_matched_null_pool_size": 0,
                    "degree_bin_fallback_used": used_fallback,
                    "matched_degree_bin": matched_bin,
                    "same_class_neighbor_p": np.nan,
                    "same_class_neighbor_z": np.nan,
                    "neighbor_therapeutic_p": np.nan,
                    "neighbor_therapeutic_z": np.nan,
                    "neighbor_broad_shift_p": np.nan,
                    "neighbor_broad_shift_z": np.nan,
                }
            )
            continue
        sampled = pool.iloc[rng.integers(0, len(pool), size=n_nulls)]
        target_class = str(row["pathology_axis_class"])

        same_null = sampled[
            f"neighbor_class_fraction::{target_class}"
        ].to_numpy(dtype=float)
        therapeutic_null = sampled[
            "mean_neighbor_therapeutic_like_percentile"
        ].to_numpy(dtype=float)
        broad_null = sampled["mean_neighbor_broad_shift_percentile"].to_numpy(dtype=float)
        rows.append(
            {
                **row.to_dict(),
                "degree_matched_null_pool_size": len(pool),
                "degree_bin_fallback_used": used_fallback,
                "matched_degree_bin": matched_bin,
                "same_class_neighbor_p": empirical_p(
                    float(row["same_class_neighbor_fraction"]), same_null
                ),
                "same_class_neighbor_z": z_score(
                    float(row["same_class_neighbor_fraction"]), same_null
                ),
                "neighbor_therapeutic_p": empirical_p(
                    float(row["mean_neighbor_therapeutic_like_percentile"]),
                    therapeutic_null,
                ),
                "neighbor_therapeutic_z": z_score(
                    float(row["mean_neighbor_therapeutic_like_percentile"]),
                    therapeutic_null,
                ),
                "neighbor_broad_shift_p": empirical_p(
                    float(row["mean_neighbor_broad_shift_percentile"]),
                    broad_null,
                ),
                "neighbor_broad_shift_z": z_score(
                    float(row["mean_neighbor_broad_shift_percentile"]),
                    broad_null,
                ),
            }
        )
    out = pd.DataFrame(rows)
    out["same_class_neighbor_FDR"] = benjamini_hochberg(out["same_class_neighbor_p"])
    out["neighbor_therapeutic_FDR"] = benjamini_hochberg(out["neighbor_therapeutic_p"])
    out["neighbor_broad_shift_FDR"] = benjamini_hochberg(out["neighbor_broad_shift_p"])
    out["coherence_status"] = out.apply(classify_status, axis=1)
    out["coherence_evidence_basis"] = out.apply(evidence_basis, axis=1)
    out["degree_matched_enrichment_supported"] = out["coherence_evidence_basis"].eq(
        "degree_matched_enrichment"
    )
    out["is_named_audit_gene"] = out["gene"].isin(NAMED_GENES)
    return out


def markdown_table(df: pd.DataFrame, columns: list[str], n: int | None = None) -> list[str]:
    subset = df.loc[:, columns].copy()
    if n is not None:
        subset = subset.head(n)
    if subset.empty:
        return ["_No rows._"]
    for column in subset.columns:
        if pd.api.types.is_numeric_dtype(subset[column]):
            subset[column] = subset[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.5g}"
            )
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in subset.itertuples(index=False, name=None)
    )
    return lines


def write_report(df: pd.DataFrame, args: argparse.Namespace) -> None:
    counts = df["coherence_status"].value_counts()
    named = df[df["is_named_audit_gene"]].sort_values("gene")
    cleaner = df[df["coherence_status"].eq("coherent_cleaner_neighborhood")].sort_values(
        ["same_class_neighbor_FDR", "neighbor_therapeutic_FDR"]
    )
    broad = df[df["coherence_status"].eq("broad_reactive_neighborhood")].sort_values(
        ["same_class_neighbor_FDR", "neighbor_broad_shift_FDR"]
    )
    isolated = df[df["coherence_status"].eq("isolated_high_score_gene")].sort_values(
        "therapeutic_like_score_percentile", ascending=False
    )
    display = [
        "gene",
        "pathology_axis_class",
        "coherence_status",
        "coherence_evidence_basis",
        "degree",
        "n_scored_neighbors",
        "same_class_neighbor_fraction",
        "mean_neighbor_therapeutic_like_percentile",
        "mean_neighbor_broad_shift_percentile",
        "same_class_neighbor_FDR",
        "neighbor_therapeutic_FDR",
        "neighbor_broad_shift_FDR",
    ]
    lines = [
        "# Scorecard v2 Graph-Neighborhood Coherence",
        "",
        "## Configuration",
        "",
        f"- Scorecard: `{args.scorecard}`",
        f"- Consensus edges: `{args.edges}`",
        f"- Genes tested: {len(df):,}",
        f"- Degree-matched null draws per gene: {args.n_nulls:,}",
        "- Degree bins preserve tied graph degrees.",
        "",
        "## Coherence Status Counts",
        "",
    ]
    lines.extend(f"- `{status}`: {count:,}" for status, count in counts.items())
    lines.extend(
        [
            "",
            "## Explicit Named-Gene Audit",
            "",
            *markdown_table(named, display),
            "",
            "## Coherent Cleaner Neighborhoods",
            "",
            *markdown_table(cleaner, display, n=25),
            "",
            "## Broad-Reactive Neighborhoods",
            "",
            *markdown_table(broad, display, n=25),
            "",
            "Broad-reactive status can be assigned from a high absolute mean neighbor broad-shift percentile. Check `coherence_evidence_basis`: `absolute_neighbor_profile_only` means the neighborhood did not survive the degree-matched enrichment test.",
            "",
            "## Isolated High-Score Genes",
            "",
            *markdown_table(isolated, display, n=25),
            "",
            "## Degree-Matching Diagnostics",
            "",
            f"- Genes using nearest degree-bin fallback: {int(df['degree_bin_fallback_used'].sum()):,}",
            f"- Genes with no testable degree-matched pool: {int(df['degree_matched_null_pool_size'].eq(0).sum()):,}",
            f"- Genes surviving any degree-matched neighborhood FDR test: {int(df['degree_matched_enrichment_supported'].sum()):,}",
            "",
            "## Boundary",
            "",
            "Graph-neighborhood coherence is supportive evidence only. It does not imply regulatory causality because STRING/WGCNA edges are associative. Coherence can reflect annotation density, co-expression, protein interaction priors, or shared disease-state correlation.",
            "",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    scorecard = read_required_csv(args.scorecard)
    scorecard["gene"] = scorecard["gene"].astype(str).str.upper()
    if len(scorecard) != 2676 or scorecard["gene"].nunique() != 2676:
        raise ValueError("Scorecard-v2 must contain exactly 2,676 unique graph-connected genes.")
    required = {
        "pathology_axis_class",
        "therapeutic_like_score_percentile",
        "tau_lowering_score_percentile",
        "neuron_preservation_score_percentile",
        "gliosis_penalty_percentile",
        "broad_shift_score_percentile",
    }
    missing = sorted(required - set(scorecard.columns))
    if missing:
        raise ValueError(f"Scorecard-v2 is missing required columns: {missing}")

    universe = set(scorecard["gene"])
    adjacency = read_graph(args.edges, universe)
    scorecard = add_degree_bins(scorecard, adjacency, args.degree_bins)
    metrics = precompute_neighborhood_metrics(scorecard, adjacency)
    out = run_nulls(metrics, args.n_nulls, args.seed)
    out = out.sort_values(
        ["coherence_status", "same_class_neighbor_FDR", "neighbor_therapeutic_FDR"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    write_report(out, args)

    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print("\nCoherence status counts:")
    print(out["coherence_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
