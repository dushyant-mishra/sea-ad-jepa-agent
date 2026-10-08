from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


PRIOR_CANDIDATES = [
    "TLR2",
    "APP",
    "APOE",
    "CD4",
    "P2RY12",
    "BCL2",
    "MAPK1",
    "CX3CR1",
    "STAT3",
    "CSF1R",
    "UGCG",
    "ROCK1",
    "CTSD",
    "P2RY13",
    "PLCG2",
    "TREM2",
    "TYROBP",
    "C1QA",
    "C1QB",
    "C1QC",
    "C3",
    "CD74",
    "HLA-DRA",
    "SPP1",
]

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

CLASSES = [
    "tau_lowering_neuron_preserving",
    "dual_pathology_lowering_neuron_preserving",
    "amyloid_lowering_candidate",
    "broad_reactive_state_shift",
    "gliosis_inflating",
    "neuron_risk",
    "mixed_or_unclear",
]

METRICS = {
    "therapeutic_like": "therapeutic_like_score_percentile",
    "tau_lowering": "tau_lowering_score_percentile",
    "neuron_preservation": "neuron_preservation_score_percentile",
    "gliosis_penalty": "gliosis_penalty_percentile",
    "broad_shift": "broad_shift_score_percentile",
    "amyloid_lowering": "amyloid_lowering_score_percentile",
    "dual_pathology_lowering": "dual_pathology_lowering_score_percentile",
}

OUTPUT_MEDIANS = [
    "therapeutic_like",
    "tau_lowering",
    "neuron_preservation",
    "gliosis_penalty",
    "broad_shift",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run graph-connected feature-wide negative controls for Discovery Scorecard v2."
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
        "--summary-out",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_negative_controls.csv"),
    )
    parser.add_argument(
        "--degree-out",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_degree_matched_nulls.csv"),
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path("results/reports/discovery_scorecard_v2_negative_controls.md"),
    )
    parser.add_argument("--n-nulls", type=int, default=1000)
    parser.add_argument("--degree-bins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=23)
    return parser.parse_args()


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def normalize_genes(values: pd.Series | list[str]) -> pd.Series:
    return pd.Series(values, dtype=str).str.upper()


def graph_degrees(edge_path: Path) -> dict[str, int]:
    edges = read_required_csv(edge_path)
    counts = Counter(
        pd.concat(
            [
                edges["source"].astype(str).str.upper(),
                edges["target"].astype(str).str.upper(),
            ],
            ignore_index=True,
        )
    )
    return dict(counts)


def add_degree_bins(scorecard: pd.DataFrame, degrees: dict[str, int], n_bins: int) -> pd.DataFrame:
    out = scorecard.copy()
    out["degree"] = out["gene"].map(lambda gene: int(degrees.get(gene, 0)))
    # Preserve degree ties so genes with identical graph degree cannot be split
    # across different matching bins solely because of row order.
    ranked = out["degree"].rank(method="average")
    out["degree_bin"] = pd.qcut(
        ranked,
        q=min(n_bins, len(out)),
        labels=False,
        duplicates="drop",
    ).astype(int)
    return out


def median_metrics(frame: pd.DataFrame) -> dict[str, float]:
    return {
        metric: float(pd.to_numeric(frame[column], errors="coerce").median())
        for metric, column in METRICS.items()
    }


def primary_metric_for_set(test_name: str) -> tuple[str, bool]:
    if test_name == "class::amyloid_lowering_candidate":
        return "amyloid_lowering", True
    if test_name == "class::broad_reactive_state_shift":
        return "broad_shift", True
    if test_name == "class::gliosis_inflating":
        return "gliosis_penalty", True
    if test_name == "class::neuron_risk":
        return "neuron_preservation", False
    if test_name == "class::mixed_or_unclear":
        return "therapeutic_like", True
    return "therapeutic_like", True


def empirical_p(observed: float, null_values: np.ndarray, higher_is_better: bool) -> float:
    valid = null_values[np.isfinite(null_values)]
    if valid.size == 0 or not math.isfinite(observed):
        return float("nan")
    if higher_is_better:
        extreme = int(np.sum(valid >= observed))
    else:
        extreme = int(np.sum(valid <= observed))
    return float((extreme + 1) / (valid.size + 1))


def z_score(observed: float, null_values: np.ndarray) -> float:
    valid = null_values[np.isfinite(null_values)]
    if valid.size < 2 or not math.isfinite(observed):
        return float("nan")
    sd = float(np.std(valid, ddof=1))
    if sd == 0:
        return float("nan")
    return float((observed - float(np.mean(valid))) / sd)


def benjamini_hochberg(values: pd.Series) -> pd.Series:
    p = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    adjusted = np.full(p.shape, np.nan, dtype=float)
    valid_idx = np.flatnonzero(np.isfinite(p))
    if valid_idx.size == 0:
        return pd.Series(adjusted, index=values.index)
    order = valid_idx[np.argsort(p[valid_idx])]
    ranked = p[order] * valid_idx.size / np.arange(1, valid_idx.size + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted[order] = np.minimum(ranked, 1.0)
    return pd.Series(adjusted, index=values.index)


def build_test_sets(scorecard: pd.DataFrame) -> dict[str, list[str]]:
    universe = set(scorecard["gene"])
    sets: dict[str, list[str]] = {
        "prior_candidate_set": sorted(universe.intersection(PRIOR_CANDIDATES)),
    }
    for label in CLASSES:
        sets[f"class::{label}"] = sorted(
            scorecard.loc[scorecard["pathology_axis_class"].eq(label), "gene"].tolist()
        )
    cleaner_labels = {
        "tau_lowering_neuron_preserving",
        "dual_pathology_lowering_neuron_preserving",
    }
    sets["cleaner_therapeutic_like_classes"] = sorted(
        scorecard.loc[scorecard["pathology_axis_class"].isin(cleaner_labels), "gene"].tolist()
    )
    for gene in NAMED_GENES:
        sets[f"named_gene::{gene}"] = [gene] if gene in universe else []
    return sets


def sample_random_set(
    scorecard: pd.DataFrame,
    n_genes: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    indices = rng.choice(len(scorecard), size=n_genes, replace=n_genes > len(scorecard))
    return scorecard.iloc[indices]


def nearest_nonempty_bin(
    target_bin: int,
    pools: dict[int, np.ndarray],
) -> tuple[int | None, bool]:
    if target_bin in pools and pools[target_bin].size:
        return target_bin, False
    available = [degree_bin for degree_bin, values in pools.items() if values.size]
    if not available:
        return None, False
    nearest = min(available, key=lambda degree_bin: abs(degree_bin - target_bin))
    return nearest, True


def sample_degree_matched_set(
    scorecard: pd.DataFrame,
    genes: list[str],
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, int, list[str]]:
    observed = scorecard.set_index("gene").loc[genes]
    excluded = set(genes)
    pools = {
        int(degree_bin): group.loc[~group["gene"].isin(excluded), "gene"].to_numpy(dtype=str)
        for degree_bin, group in scorecard.groupby("degree_bin")
    }
    sampled: list[str] = []
    fallback_genes: list[str] = []
    for gene, row in observed.iterrows():
        degree_bin = int(row["degree_bin"])
        selected_bin, used_fallback = nearest_nonempty_bin(degree_bin, pools)
        if selected_bin is None:
            continue
        if used_fallback:
            fallback_genes.append(str(gene))
        sampled.append(str(rng.choice(pools[selected_bin])))
    if not sampled:
        return scorecard.iloc[0:0], len(genes), fallback_genes
    return scorecard.set_index("gene").loc[sampled].reset_index(), len(genes) - len(sampled), fallback_genes


def null_distributions(
    scorecard: pd.DataFrame,
    test_name: str,
    genes: list[str],
    n_nulls: int,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    random_rows: list[dict[str, float | int]] = []
    degree_rows: list[dict[str, float | int | str]] = []
    fallback_union: set[str] = set()
    max_unmatched = 0
    for iteration in range(1, n_nulls + 1):
        random_frame = sample_random_set(scorecard, len(genes), rng)
        random_rows.append({"iteration": iteration, **median_metrics(random_frame)})

        degree_frame, unmatched, fallback_genes = sample_degree_matched_set(scorecard, genes, rng)
        max_unmatched = max(max_unmatched, unmatched)
        fallback_union.update(fallback_genes)
        degree_rows.append(
            {
                "test_set": test_name,
                "iteration": iteration,
                "n_genes": len(genes),
                "n_matched": len(degree_frame),
                "n_unmatched": unmatched,
                "nearest_bin_fallback_count": len(fallback_genes),
                "nearest_bin_fallback_genes": ";".join(sorted(fallback_genes)),
                **median_metrics(degree_frame),
            }
        )
    diagnostics = {
        "degree_matching_max_unmatched": max_unmatched,
        "degree_matching_nearest_bin_fallback_genes": ";".join(sorted(fallback_union)),
        "degree_matching_nearest_bin_fallback_count": len(fallback_union),
    }
    return pd.DataFrame(random_rows), pd.DataFrame(degree_rows), diagnostics


def summary_row(
    test_name: str,
    genes: list[str],
    observed: dict[str, float],
    null_type: str,
    null_df: pd.DataFrame,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    primary_metric, higher_is_better = primary_metric_for_set(test_name)
    null_values = pd.to_numeric(null_df[primary_metric], errors="coerce").to_numpy(dtype=float)
    row: dict[str, object] = {
        "test_set": test_name,
        "null_type": null_type,
        "n_genes": len(genes),
        "genes": ";".join(genes),
        "primary_metric": primary_metric,
        "primary_metric_direction": "higher" if higher_is_better else "lower",
        "empirical_p_value": empirical_p(observed[primary_metric], null_values, higher_is_better),
        "z_score_vs_null": z_score(observed[primary_metric], null_values),
        "null_mean_primary_metric": float(np.nanmean(null_values)) if np.isfinite(null_values).any() else np.nan,
        "null_sd_primary_metric": float(np.nanstd(null_values, ddof=1))
        if np.isfinite(null_values).sum() > 1
        else np.nan,
        **diagnostics,
    }
    for metric in OUTPUT_MEDIANS:
        row[f"median_{metric}_percentile"] = observed[metric]
        row[f"null_median_{metric}_percentile"] = (
            float(pd.to_numeric(null_df[metric], errors="coerce").median())
            if metric in null_df
            else np.nan
        )
    return row


def high_degree_null(
    scorecard: pd.DataFrame,
    n_genes: int,
    n_nulls: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    cutoff = float(scorecard["degree"].quantile(0.90))
    hubs = scorecard[scorecard["degree"] >= cutoff]
    rows = []
    for iteration in range(1, n_nulls + 1):
        indices = rng.choice(len(hubs), size=n_genes, replace=n_genes > len(hubs))
        rows.append({"iteration": iteration, **median_metrics(hubs.iloc[indices])})
    return pd.DataFrame(rows)


def broad_reference_null(
    scorecard: pd.DataFrame,
    n_genes: int,
    n_nulls: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    broad = scorecard[scorecard["pathology_axis_class"].eq("broad_reactive_state_shift")]
    rows = []
    for iteration in range(1, n_nulls + 1):
        indices = rng.choice(len(broad), size=n_genes, replace=n_genes > len(broad))
        rows.append({"iteration": iteration, **median_metrics(broad.iloc[indices])})
    return pd.DataFrame(rows)


def assign_interpretations(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    out["FDR"] = np.nan
    for null_type, index in out.groupby("null_type").groups.items():
        out.loc[index, "FDR"] = benjamini_hochberg(out.loc[index, "empirical_p_value"])

    interpretations: dict[str, str] = {}
    for test_name, group in out.groupby("test_set"):
        n_genes = int(group["n_genes"].iloc[0])
        if n_genes == 0:
            interpretations[test_name] = "not_testable"
            continue
        if n_genes < 3:
            interpretations[test_name] = "too_few_genes"
            continue
        degree_row = group[group["null_type"].eq("degree_matched")]
        random_row = group[group["null_type"].eq("random")]
        broad_pct = float(group["median_broad_shift_percentile"].iloc[0])
        therapeutic_pct = float(group["median_therapeutic_like_percentile"].iloc[0])
        degree_match_failed = (
            degree_row.empty
            or int(degree_row["degree_matching_max_unmatched"].fillna(0).max()) > 0
        )
        if degree_match_failed:
            interpretations[test_name] = "not_testable"
        elif test_name == "class::mixed_or_unclear":
            interpretations[test_name] = "not_enriched"
        elif test_name == "class::broad_reactive_state_shift" or (
            broad_pct >= 90 and therapeutic_pct < 90
        ):
            interpretations[test_name] = "broad_shift_confounded"
        elif not degree_row.empty and float(degree_row["FDR"].iloc[0]) <= 0.05:
            interpretations[test_name] = "enriched_vs_degree_matched_null"
        elif not random_row.empty and float(random_row["FDR"].iloc[0]) <= 0.05:
            interpretations[test_name] = "enriched_vs_random_only"
        else:
            interpretations[test_name] = "not_enriched"
    out["interpretation"] = out["test_set"].map(interpretations)
    out["evidence_tier"] = "supporting_null_context"
    out.loc[out["test_set"].eq("prior_candidate_set"), "evidence_tier"] = (
        "strongest_independent_set_test"
    )
    out.loc[
        out["test_set"].eq("cleaner_therapeutic_like_classes")
        & out["null_type"].eq("broad_reactive_reference"),
        "evidence_tier",
    ] = "strongest_direct_cleaner_vs_broad_test"
    out.loc[out["test_set"].str.startswith("class::"), "evidence_tier"] = (
        "calibration_not_independent_validation"
    )
    out.loc[out["test_set"].str.startswith("named_gene::"), "evidence_tier"] = (
        "descriptive_singleton_context"
    )
    out["comparison_interpretation"] = ""
    cleaner_broad = out["test_set"].eq("cleaner_therapeutic_like_classes") & out[
        "null_type"
    ].eq("broad_reactive_reference")
    out.loc[cleaner_broad, "comparison_interpretation"] = np.where(
        out.loc[cleaner_broad, "FDR"] <= 0.05,
        "cleaner_than_broad_reference",
        "not_cleaner_than_broad_reference",
    )
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


def write_report(
    summary: pd.DataFrame,
    degree_nulls: pd.DataFrame,
    scorecard: pd.DataFrame,
    out_path: Path,
) -> None:
    set_level = summary.sort_values(["test_set", "null_type"])
    named = set_level[set_level["test_set"].str.startswith("named_gene::")]
    prior = set_level[set_level["test_set"].eq("prior_candidate_set")]
    classes = set_level[set_level["test_set"].str.startswith("class::")]
    cleaner = set_level[
        set_level["test_set"].isin(
            ["cleaner_therapeutic_like_classes", "class::broad_reactive_state_shift"]
        )
    ]
    fallback_rows = degree_nulls[degree_nulls["nearest_bin_fallback_count"] > 0]
    interpretation_counts = (
        summary.drop_duplicates("test_set")["interpretation"].value_counts()
    )
    display = [
        "test_set",
        "null_type",
        "n_genes",
        "primary_metric",
        "median_therapeutic_like_percentile",
        "median_tau_lowering_percentile",
        "median_neuron_preservation_percentile",
        "median_gliosis_penalty_percentile",
        "median_broad_shift_percentile",
        "empirical_p_value",
        "z_score_vs_null",
        "FDR",
        "evidence_tier",
        "interpretation",
        "comparison_interpretation",
    ]
    lines = [
        "# Discovery Scorecard v2 Negative Controls",
        "",
        "## Executive Summary",
        "",
        f"- Null universe: {len(scorecard):,} graph-connected feature genes.",
        "- Random nulls per tested set: 1,000.",
        "- Degree-matched nulls per tested set: 1,000.",
        "- Degree matching uses graph-degree quantile bins and the nearest populated bin when an exact bin has no eligible decoy.",
        "",
        "Interpretation counts:",
        "",
    ]
    lines.extend(f"- `{label}`: {count}" for label, count in interpretation_counts.items())
    lines.extend(
        [
            "",
            "## Evidence Tier 1: Strongest Set Tests",
            "",
            "These comparisons are the most meaningful because the tested groups were nominated independently of the specific null draw.",
            "",
            "### Prior Candidate Set",
            "",
            *markdown_table(prior, display),
            "",
            "The prior set is tested against random, degree-matched, and high-degree hub controls. Degree matching is the primary graph-aware comparator; hub-control enrichment alone does not override failure against random and degree-matched backgrounds.",
            "",
            "### Cleaner Therapeutic-Like Classes Versus Broad-Reactive Reference",
            "",
            *markdown_table(
                cleaner[
                    cleaner["test_set"].eq("cleaner_therapeutic_like_classes")
                    & cleaner["null_type"].eq("broad_reactive_reference")
                ],
                display,
            ),
            "",
            "The `comparison_interpretation` field is the direct gate: `cleaner_than_broad_reference` or `not_cleaner_than_broad_reference`.",
            "",
            "## Evidence Tier 2: Class Calibration",
            "",
            *markdown_table(classes, display),
            "",
            "Class-level tests are calibration checks, not independent validation: the classes were defined from these same scorecard percentiles. Enrichment of a class on its defining metric is expected and only confirms that the classification rules partitioned the feature-wide universe as designed.",
            "",
            "## Supporting Cleaner and Broad Null Context",
            "",
            *markdown_table(cleaner, display),
            "",
            "The `broad_reactive_reference` row compares the cleaner class union directly with bootstrap samples from broad-reactive genes.",
            "",
            "## Evidence Tier 3: Named-Gene Descriptive Context",
            "",
            *markdown_table(named, display),
            "",
            "Singleton named-gene tests are labeled `too_few_genes`; their empirical context is descriptive and should not be treated as set enrichment.",
            "",
            "## Degree-Matching Diagnostics",
            "",
            f"- Degree-null iterations with nearest-bin fallback: {len(fallback_rows):,} / {len(degree_nulls):,}.",
            f"- Tested sets with at least one fallback gene: {degree_nulls.loc[degree_nulls['nearest_bin_fallback_count'] > 0, 'test_set'].nunique():,}.",
            "",
            "Nearest-bin fallback is recorded explicitly in `discovery_scorecard_v2_degree_matched_nulls.csv`. Unmatched genes cause `not_testable`; nearest-bin fallback alone does not.",
            "",
            "## Boundary",
            "",
            "The negative controls test whether scorecard-v2 candidate groups are enriched relative to the graph-connected feature-wide universe. They do not prove causality or experimental validity. The full feature-wide run used skipped nearest-neighbor manifold checking, so manifold safety remains supported by the successful pilot and any future targeted top-hit audits.",
            "",
            "Biological conclusions are intentionally unchanged. The next step is scorecard-v2 interpretation and targeted top-hit manifold audit.",
            "",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    scorecard = read_required_csv(args.scorecard)
    scorecard["gene"] = scorecard["gene"].astype(str).str.upper()
    for column in METRICS.values():
        scorecard[column] = pd.to_numeric(scorecard[column], errors="coerce")
    if len(scorecard) != 2676 or scorecard["gene"].nunique() != 2676:
        raise ValueError("Scorecard-v2 must contain exactly 2,676 unique graph-connected genes.")

    degrees = graph_degrees(args.edges)
    scorecard = add_degree_bins(scorecard, degrees, args.degree_bins)
    test_sets = build_test_sets(scorecard)

    summary_rows: list[dict[str, object]] = []
    degree_frames: list[pd.DataFrame] = []
    for test_name, genes in test_sets.items():
        if not genes:
            empty_observed = {metric: np.nan for metric in METRICS}
            diagnostics = {
                "degree_matching_max_unmatched": len(genes),
                "degree_matching_nearest_bin_fallback_genes": "",
                "degree_matching_nearest_bin_fallback_count": 0,
            }
            summary_rows.append(
                summary_row(
                    test_name,
                    genes,
                    empty_observed,
                    "random",
                    pd.DataFrame([{metric: np.nan for metric in METRICS}]),
                    diagnostics,
                )
            )
            summary_rows.append(
                summary_row(
                    test_name,
                    genes,
                    empty_observed,
                    "degree_matched",
                    pd.DataFrame([{metric: np.nan for metric in METRICS}]),
                    diagnostics,
                )
            )
            continue

        observed_frame = scorecard.set_index("gene").loc[genes].reset_index()
        observed = median_metrics(observed_frame)
        random_nulls, degree_nulls, diagnostics = null_distributions(
            scorecard,
            test_name,
            genes,
            args.n_nulls,
            rng,
        )
        degree_frames.append(degree_nulls)
        summary_rows.append(
            summary_row(test_name, genes, observed, "random", random_nulls, diagnostics)
        )
        summary_rows.append(
            summary_row(test_name, genes, observed, "degree_matched", degree_nulls, diagnostics)
        )

        if test_name == "prior_candidate_set":
            hub_nulls = high_degree_null(scorecard, len(genes), args.n_nulls, rng)
            summary_rows.append(
                summary_row(
                    test_name,
                    genes,
                    observed,
                    "high_degree_hub_control",
                    hub_nulls,
                    diagnostics,
                )
            )
        if test_name == "cleaner_therapeutic_like_classes":
            broad_nulls = broad_reference_null(scorecard, len(genes), args.n_nulls, rng)
            summary_rows.append(
                summary_row(
                    test_name,
                    genes,
                    observed,
                    "broad_reactive_reference",
                    broad_nulls,
                    diagnostics,
                )
            )

    summary = assign_interpretations(pd.DataFrame(summary_rows))
    degree_all = pd.concat(degree_frames, ignore_index=True)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_out, index=False)
    degree_all.to_csv(args.degree_out, index=False)
    write_report(summary, degree_all, scorecard, args.report_out)

    print(f"Wrote {args.summary_out}")
    print(f"Wrote {args.degree_out}")
    print(f"Wrote {args.report_out}")
    print("\nUnique test-set interpretation counts:")
    print(summary.drop_duplicates("test_set")["interpretation"].value_counts().to_string())


if __name__ == "__main__":
    main()
