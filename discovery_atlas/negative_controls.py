from __future__ import annotations

import argparse
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


PRIMARY_CANDIDATES = [
    "TLR2",
    "APP",
    "APOE",
    "CD4",
    "P2RY12",
    "P2RY13",
    "CX3CR1",
    "CSF1R",
    "CTSD",
    "BCL2",
    "MAPK1",
    "STAT3",
    "UGCG",
    "ROCK1",
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

HOUSEKEEPING_FALLBACK = [
    "ACTB",
    "GAPDH",
    "B2M",
    "RPLP0",
    "RPL13A",
    "RPS18",
    "HPRT1",
    "TBP",
    "TUBB",
    "EEF1A1",
]

SCORE_COLUMNS = [
    "therapeutic_like_score",
    "amyloid_selectivity_score",
    "tau_selectivity_score",
    "broad_shift_score",
    "gliosis_penalty",
    "discovery_sort_score",
]

USEFUL_HIGH_COLUMNS = {
    "therapeutic_like_score",
    "amyloid_selectivity_score",
    "tau_selectivity_score",
    "discovery_sort_score",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run first-pass Discovery Atlas negative controls."
    )
    parser.add_argument(
        "--fingerprints",
        type=Path,
        default=Path("results/tables/discovery_pathology_axis_gene_fingerprints.csv"),
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=Path("results/tables/discovery_candidate_scorecard_v1.csv"),
    )
    parser.add_argument(
        "--graph-coherence",
        type=Path,
        default=Path("results/tables/discovery_graph_neighborhood_coherence.csv"),
    )
    parser.add_argument(
        "--edges",
        type=Path,
        default=Path("results/tables/v2_graph_consensus_edges.csv"),
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("results/tables/discovery_negative_control_summary.csv"),
    )
    parser.add_argument(
        "--degree-out",
        type=Path,
        default=Path("results/tables/discovery_degree_matched_decoy_controls.csv"),
    )
    parser.add_argument(
        "--shuffle-out",
        type=Path,
        default=Path("results/tables/discovery_label_shuffle_controls.csv"),
    )
    parser.add_argument(
        "--housekeeping-out",
        type=Path,
        default=Path("results/tables/discovery_housekeeping_hub_controls.csv"),
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path("results/reports/discovery_negative_controls.md"),
    )
    parser.add_argument("--n-nulls", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--min-null-pool", type=int, default=20)
    return parser.parse_args()


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def normalize_gene(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper()


def read_graph(path: Path) -> tuple[dict[str, set[str]], dict[str, int]]:
    edges = read_required_csv(path)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for source, target in edges[["source", "target"]].itertuples(index=False, name=None):
        source = str(source).upper()
        target = str(target).upper()
        if source == target:
            continue
        adjacency[source].add(target)
        adjacency[target].add(source)
    degrees = {gene: len(neighbors) for gene, neighbors in adjacency.items()}
    return dict(adjacency), degrees


def mean_or_nan(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    if not vals:
        return float("nan")
    return float(sum(vals) / len(vals))


def sd_or_nan(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    if len(vals) < 2:
        return float("nan")
    mu = sum(vals) / len(vals)
    return float(math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1)))


def empirical_p(observed: float, null_values: list[float], higher_is_better: bool = True) -> float:
    valid = [float(v) for v in null_values if math.isfinite(float(v))]
    if not valid or not math.isfinite(float(observed)):
        return float("nan")
    if higher_is_better:
        extreme = sum(v >= observed for v in valid)
    else:
        extreme = sum(v <= observed for v in valid)
    return float((extreme + 1) / (len(valid) + 1))


def percentile(observed: float, null_values: list[float]) -> float:
    valid = [float(v) for v in null_values if math.isfinite(float(v))]
    if not valid or not math.isfinite(float(observed)):
        return float("nan")
    return float(100.0 * sum(v <= observed for v in valid) / len(valid))


def z_score(observed: float, null_values: list[float]) -> float:
    mu = mean_or_nan(null_values)
    sd = sd_or_nan(null_values)
    if not math.isfinite(float(observed)) or not math.isfinite(mu) or not math.isfinite(sd) or sd == 0:
        return float("nan")
    return float((observed - mu) / sd)


def degree_pool(
    gene: str,
    scored_genes: set[str],
    degrees: dict[str, int],
    *,
    min_pool: int,
) -> list[str]:
    degree = degrees.get(gene, 0)
    if degree == 0:
        pool = [g for g in scored_genes if degrees.get(g, 0) == 0 and g != gene]
        return pool
    window = 0.20
    pool: list[str] = []
    while window <= 4.0:
        low = max(1, math.floor(degree * (1.0 - window)))
        high = max(low, math.ceil(degree * (1.0 + window)))
        pool = [g for g in scored_genes if low <= degrees.get(g, 0) <= high and g != gene]
        if len(pool) >= min_pool:
            return pool
        window *= 1.5
    return [g for g in scored_genes if g != gene]


def magnitude_pool(
    gene: str,
    score_df: pd.DataFrame,
    base_pool: list[str],
    *,
    min_pool: int,
) -> list[str]:
    if gene not in score_df.index or "broad_shift_score" not in score_df.columns:
        return base_pool
    observed = float(score_df.at[gene, "broad_shift_score"])
    if not math.isfinite(observed):
        return base_pool
    window = 0.25
    while window <= 5.0:
        low = observed * (1.0 - window)
        high = observed * (1.0 + window)
        pool = [
            g
            for g in base_pool
            if g in score_df.index
            and pd.notna(score_df.at[g, "broad_shift_score"])
            and low <= float(score_df.at[g, "broad_shift_score"]) <= high
        ]
        if len(pool) >= min_pool:
            return pool
        window *= 1.5
    return base_pool


def sample_with_replacement(pool: list[str], n: int, rng: random.Random) -> list[str]:
    if not pool:
        return []
    return [rng.choice(pool) for _ in range(n)]


def degree_matched_controls(
    candidates: list[str],
    score_df: pd.DataFrame,
    degrees: dict[str, int],
    rng: random.Random,
    *,
    n_nulls: int,
    min_pool: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    summary_parts: dict[str, dict[str, object]] = {gene: {} for gene in candidates}
    scored_genes = set(score_df.index)
    for gene in candidates:
        candidate_summary = summary_parts[gene]
        degree = degrees.get(gene, 0)
        candidate_summary["candidate"] = gene
        candidate_summary["degree"] = degree
        if gene not in score_df.index:
            candidate_summary["degree_control_status"] = "not_testable_missing_fingerprint"
            continue

        degree_only_pool = degree_pool(gene, scored_genes, degrees, min_pool=min_pool)
        degree_magnitude_pool = magnitude_pool(gene, score_df, degree_only_pool, min_pool=min_pool)
        null_pool_size = len(degree_magnitude_pool)
        candidate_summary["degree_null_pool_size"] = len(degree_only_pool)
        candidate_summary["degree_magnitude_null_pool_size"] = null_pool_size
        candidate_summary["null_pool_size"] = null_pool_size
        candidate_summary["null_pool_scope"] = "score_available_candidate_space_degree_and_broad_shift_matched"
        if null_pool_size < 20:
            pool_warning = "not_testable"
            interpretation = "fewer than 20 score-available matched decoys; requires expanded decoy perturbations"
        elif null_pool_size < 50:
            pool_warning = "thin_null_pool"
            interpretation = "20-49 score-available matched decoys; preliminary candidate-space falsification only"
        else:
            pool_warning = "preliminary_decoy_control"
            interpretation = "50+ score-available matched decoys; still not genome-wide"
        candidate_summary["null_pool_warning"] = pool_warning
        candidate_summary["control_interpretation"] = interpretation
        if not degree_only_pool:
            candidate_summary["degree_control_status"] = "not_testable_no_decoys"
            continue

        degree_draws = sample_with_replacement(degree_only_pool, n_nulls, rng)
        mag_draws = sample_with_replacement(degree_magnitude_pool, n_nulls, rng)
        candidate_summary["degree_control_status"] = "testable"
        for score_col in SCORE_COLUMNS:
            observed = float(score_df.at[gene, score_col]) if score_col in score_df.columns else float("nan")
            degree_values = [float(score_df.at[g, score_col]) for g in degree_draws if g in score_df.index]
            mag_values = [float(score_df.at[g, score_col]) for g in mag_draws if g in score_df.index]
            higher_is_better = score_col in USEFUL_HIGH_COLUMNS
            row = {
                "candidate": gene,
                "score": score_col,
                "degree": degree,
                "observed": observed,
                "null_pool_size": null_pool_size,
                "null_pool_scope": "score_available_candidate_space_degree_and_broad_shift_matched",
                "null_pool_warning": pool_warning,
                "control_interpretation": interpretation,
                "degree_null_pool_size": len(degree_only_pool),
                "degree_magnitude_null_pool_size": null_pool_size,
                "degree_null_mean": mean_or_nan(degree_values),
                "degree_null_sd": sd_or_nan(degree_values),
                "degree_z": z_score(observed, degree_values),
                "degree_empirical_p": empirical_p(observed, degree_values, higher_is_better),
                "degree_percentile": percentile(observed, degree_values),
                "degree_magnitude_null_mean": mean_or_nan(mag_values),
                "degree_magnitude_null_sd": sd_or_nan(mag_values),
                "degree_magnitude_z": z_score(observed, mag_values),
                "degree_magnitude_empirical_p": empirical_p(observed, mag_values, higher_is_better),
                "degree_magnitude_percentile": percentile(observed, mag_values),
            }
            rows.append(row)
            if score_col in USEFUL_HIGH_COLUMNS:
                prefix = score_col.replace("_score", "")
                candidate_summary[f"{score_col}_decoy_percentile"] = row["degree_magnitude_percentile"]
                candidate_summary[f"{score_col}_empirical_p"] = row["degree_magnitude_empirical_p"]
                candidate_summary[f"{score_col}_z"] = row["degree_magnitude_z"]
                candidate_summary[f"{prefix}_decoy_percentile"] = row["degree_magnitude_percentile"]
                candidate_summary[f"{prefix}_empirical_p"] = row["degree_magnitude_empirical_p"]
    return pd.DataFrame(rows), pd.DataFrame(summary_parts.values())


def same_class_neighbor_count(
    gene: str,
    label_map: dict[str, str],
    adjacency: dict[str, set[str]],
) -> tuple[int, int, float]:
    label = label_map.get(gene)
    scored_neighbors = [n for n in adjacency.get(gene, set()) if n in label_map]
    if label is None or not scored_neighbors:
        return 0, len(scored_neighbors), float("nan")
    count = sum(label_map[n] == label for n in scored_neighbors)
    return count, len(scored_neighbors), float(count / len(scored_neighbors))


def label_shuffle_controls(
    candidates: list[str],
    score_df: pd.DataFrame,
    graph_coherence: pd.DataFrame,
    adjacency: dict[str, set[str]],
    rng: random.Random,
    *,
    n_nulls: int,
) -> pd.DataFrame:
    label_map = score_df["pathology_axis_class"].astype(str).to_dict()
    genes = list(label_map)
    labels = [label_map[g] for g in genes]
    coherence_map = {}
    if not graph_coherence.empty and "candidate" in graph_coherence.columns:
        graph_coherence = graph_coherence.copy()
        graph_coherence["candidate"] = normalize_gene(graph_coherence["candidate"])
        coherence_map = graph_coherence.set_index("candidate")["coherence_status"].to_dict()

    rows: list[dict[str, object]] = []
    for gene in candidates:
        observed_count, n_neighbors, observed_fraction = same_class_neighbor_count(gene, label_map, adjacency)
        if gene not in label_map:
            rows.append(
                {
                    "candidate": gene,
                    "observed_same_class_neighbors": np.nan,
                    "observed_same_class_neighbor_fraction": np.nan,
                    "n_scored_neighbors": n_neighbors,
                    "shuffle_mean_same_class_neighbors": np.nan,
                    "shuffle_sd_same_class_neighbors": np.nan,
                    "shuffle_z": np.nan,
                    "shuffle_empirical_p": np.nan,
                    "label_shuffle_support": "not_testable_missing_fingerprint",
                    "observed_graph_coherence_status": coherence_map.get(gene, "not_available"),
                }
            )
            continue

        null_counts: list[float] = []
        for _ in range(n_nulls):
            shuffled = labels[:]
            rng.shuffle(shuffled)
            shuffled_map = dict(zip(genes, shuffled))
            count, _, _ = same_class_neighbor_count(gene, shuffled_map, adjacency)
            null_counts.append(float(count))

        p_value = empirical_p(float(observed_count), null_counts, higher_is_better=True)
        z = z_score(float(observed_count), null_counts)
        if n_neighbors == 0:
            support = "not_testable_no_scored_neighbors"
        elif math.isfinite(p_value) and p_value <= 0.05 and math.isfinite(z) and z > 1:
            support = "survives_label_shuffle"
        elif math.isfinite(p_value):
            support = "not_extreme_vs_shuffled_labels"
        else:
            support = "not_testable"
        rows.append(
            {
                "candidate": gene,
                "observed_same_class_neighbors": observed_count,
                "observed_same_class_neighbor_fraction": observed_fraction,
                "n_scored_neighbors": n_neighbors,
                "shuffle_mean_same_class_neighbors": mean_or_nan(null_counts),
                "shuffle_sd_same_class_neighbors": sd_or_nan(null_counts),
                "shuffle_z": z,
                "shuffle_empirical_p": p_value,
                "label_shuffle_support": support,
                "observed_graph_coherence_status": coherence_map.get(gene, "not_available"),
            }
        )
    return pd.DataFrame(rows)


def housekeeping_and_hub_controls(
    score_df: pd.DataFrame,
    degrees: dict[str, int],
    *,
    top_n_hubs: int = 20,
) -> pd.DataFrame:
    top_hubs = [gene for gene, _ in sorted(degrees.items(), key=lambda item: item[1], reverse=True)[:top_n_hubs]]
    rows: list[dict[str, object]] = []
    for gene in HOUSEKEEPING_FALLBACK:
        rows.append({"control_gene": gene, "control_type": "housekeeping_fallback"})
    for gene in top_hubs:
        rows.append({"control_gene": gene, "control_type": "top_degree_hub"})
    out = pd.DataFrame(rows).drop_duplicates(["control_gene", "control_type"])
    out["control_gene"] = normalize_gene(out["control_gene"])
    out["degree"] = out["control_gene"].map(lambda g: degrees.get(g, 0))
    if score_df.empty:
        return out
    score_cols = [
        "pathology_axis_class",
        "pathology_axis_label_confidence",
        "therapeutic_like_score",
        "amyloid_selectivity_score",
        "tau_selectivity_score",
        "discovery_sort_score",
    ]
    available_cols = [c for c in score_cols if c in score_df.columns]
    merged = out.merge(
        score_df[available_cols].reset_index().rename(columns={"candidate": "control_gene"}),
        on="control_gene",
        how="left",
    )
    merged["appears_in_fingerprint_table"] = merged["pathology_axis_class"].notna()
    return merged


def status_from_summary(row: pd.Series) -> tuple[str, str]:
    if row.get("candidate_missing", False):
        return "not_testable_due_to_thin_null_pool", "candidate is missing from the fingerprint table"
    if row.get("pathology_axis_class") == "artifact_or_covariate_sensitive":
        return "requires_expanded_decoy_perturbations", "candidate has a covariate/artifact-sensitive fingerprint; decoy support cannot clear it"
    if row.get("housekeeping_or_hub_warning", False):
        return "requires_expanded_decoy_perturbations", "candidate overlaps housekeeping/high-degree hub controls"
    if str(row.get("degree_control_status", "")).startswith("not_testable"):
        return "not_testable_due_to_thin_null_pool", str(row.get("degree_control_status", "not testable"))
    if row.get("null_pool_warning") == "not_testable":
        return "not_testable_due_to_thin_null_pool", str(row.get("control_interpretation", "thin or missing null pool"))

    useful_p_values = [
        row.get("therapeutic_like_empirical_p"),
        row.get("amyloid_selectivity_empirical_p"),
        row.get("tau_selectivity_empirical_p"),
        row.get("discovery_sort_empirical_p"),
    ]
    useful_percentiles = [
        row.get("therapeutic_like_decoy_percentile"),
        row.get("amyloid_selectivity_decoy_percentile"),
        row.get("tau_selectivity_decoy_percentile"),
        row.get("discovery_sort_decoy_percentile"),
    ]
    extreme_scores = [
        p
        for p, pct in zip(useful_p_values, useful_percentiles)
        if pd.notna(p) and pd.notna(pct) and float(p) <= 0.10 and float(pct) >= 80.0
    ]
    graph_status = str(row.get("observed_graph_coherence_status", ""))
    shuffle_status = str(row.get("label_shuffle_support", ""))
    graph_supported = graph_status in {
        "coherent_same_axis_neighborhood",
        "candidate_enriched_neighborhood",
    }
    shuffle_supported = shuffle_status == "survives_label_shuffle"
    thin_pool = row.get("null_pool_warning") == "thin_null_pool"

    if len(extreme_scores) >= 1 or graph_supported or shuffle_supported:
        qualifier = "thin score-available candidate-space null pool; " if thin_pool else ""
        return "preliminary_support", qualifier + "some decoy or graph-control evidence supports the candidate"
    if all(pd.notna(p) and float(p) > 0.25 for p in useful_p_values if pd.notna(p)):
        return "not_extreme_within_scored_candidate_space", "candidate is not extreme versus available score-available matched decoys and lacks graph-control support"
    return "requires_expanded_decoy_perturbations", "available scored-candidate controls are inconclusive"


def build_summary(
    candidates: list[str],
    score_df: pd.DataFrame,
    degree_summary: pd.DataFrame,
    shuffle_df: pd.DataFrame,
    house_df: pd.DataFrame,
    degrees: dict[str, int],
) -> pd.DataFrame:
    base = pd.DataFrame({"candidate": candidates})
    base["candidate"] = normalize_gene(base["candidate"])
    base["degree"] = base["candidate"].map(lambda g: degrees.get(g, 0))
    if not score_df.empty:
        score_cols = [
            "pathology_axis_class",
            "therapeutic_like_score",
            "amyloid_selectivity_score",
            "tau_selectivity_score",
            "discovery_sort_score",
        ]
        base = base.merge(score_df[score_cols].reset_index(), on="candidate", how="left")
    base["candidate_missing"] = base["pathology_axis_class"].isna() if "pathology_axis_class" in base else True

    if not degree_summary.empty:
        base = base.merge(degree_summary.drop(columns=["degree"], errors="ignore"), on="candidate", how="left")
    if not shuffle_df.empty:
        keep = [
            "candidate",
            "observed_graph_coherence_status",
            "label_shuffle_support",
        ]
        base = base.merge(shuffle_df[keep], on="candidate", how="left")

    warning_genes = set(
        house_df.loc[
            house_df.get("appears_in_fingerprint_table", pd.Series(False, index=house_df.index)).fillna(False),
            "control_gene",
        ].astype(str)
    )
    base["housekeeping_or_hub_warning"] = base["candidate"].isin(warning_genes)

    statuses = base.apply(status_from_summary, axis=1)
    base["negative_control_status"] = [s[0] for s in statuses]
    base["negative_control_interpretation"] = [s[1] for s in statuses]

    requested = [
        "candidate",
        "degree",
        "pathology_axis_class",
        "therapeutic_like_score",
        "therapeutic_like_decoy_percentile",
        "therapeutic_like_empirical_p",
        "amyloid_selectivity_score",
        "amyloid_selectivity_decoy_percentile",
        "amyloid_selectivity_empirical_p",
        "tau_selectivity_score",
        "tau_selectivity_decoy_percentile",
        "tau_selectivity_empirical_p",
        "discovery_sort_score",
        "discovery_sort_decoy_percentile",
        "discovery_sort_empirical_p",
        "observed_graph_coherence_status",
        "label_shuffle_support",
        "housekeeping_or_hub_warning",
        "null_pool_size",
        "null_pool_scope",
        "null_pool_warning",
        "control_interpretation",
        "negative_control_status",
        "negative_control_interpretation",
    ]
    for col in requested:
        if col not in base.columns:
            base[col] = np.nan
    return base[requested]


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals: list[str] = []
        for col in df.columns:
            value = row[col]
            if isinstance(value, float):
                vals.append("" if pd.isna(value) else f"{value:.4g}")
            else:
                vals.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_report(
    summary: pd.DataFrame,
    degree_controls: pd.DataFrame,
    label_shuffle: pd.DataFrame,
    house_controls: pd.DataFrame,
    out_path: Path,
) -> None:
    status_counts = summary["negative_control_status"].value_counts()
    lines = [
        "# Discovery Atlas Negative Controls",
        "",
        "## Executive Summary",
        "",
        "This report asks whether candidate scores and graph-neighborhood labels look stronger than simple matched nonsense. It is a falsification layer, not validation.",
        "",
        "**Important scope limit:** pathology-axis scores currently exist only for the scored candidate/fingerprint table. Degree-matched decoys are therefore `score-available candidate-space` decoys, not genome-wide null controls. Stronger nulls require counterfactual scores for a larger gene universe or rerunning perturbations for degree/expression-matched decoy genes.",
        "",
        "Negative-control status counts:",
        "",
    ]
    for status, count in status_counts.items():
        lines.append(f"- `{status}`: {count}")

    lines.extend(
        [
            "",
            "## What Controls Were Run",
            "",
            "- Score-available degree-matched decoys.",
            "- Score-available degree plus broad-shift-magnitude matched decoys, used for summary percentiles and p-values when available.",
            "- Shuffled pathology-axis labels for same-axis graph-neighborhood support.",
            "- Fallback housekeeping genes and top-degree hub controls. These are descriptive unless the control gene also has fingerprint scores.",
            "",
            "Null-pool interpretation:",
            "",
            "- `<20` possible decoys: `not_testable`.",
            "- `20-49` possible decoys: `thin_null_pool` and preliminary only.",
            "- `50+` possible decoys: interpretable preliminary decoy control, still not genome-wide.",
            "",
            "## Candidate-Level Interpretation",
            "",
            markdown_table(
                summary[
                    [
                        "candidate",
                        "pathology_axis_class",
                        "negative_control_status",
                        "observed_graph_coherence_status",
                        "label_shuffle_support",
                        "null_pool_size",
                        "null_pool_warning",
                        "discovery_sort_decoy_percentile",
                        "housekeeping_or_hub_warning",
                    ]
                ]
            ),
            "",
            "## Degree-Matched Decoy Results",
            "",
            "The table reports candidate-vs-null statistics for each score. Summary status uses the degree plus broad-shift-magnitude matched null when possible.",
            "",
            markdown_table(degree_controls.head(20)),
            "",
            "## Shuffled-Label Graph-Coherence Results",
            "",
            markdown_table(label_shuffle.head(30)),
            "",
            "## Housekeeping / High-Degree Hub Checks",
            "",
            markdown_table(house_controls.head(40)),
            "",
            "## Claim Boundary",
            "",
            "These preliminary controls do not prove causality. They also do not prove a target is biologically irrelevant when it fails. They only test whether the current Discovery Atlas signal is stronger than simple matched expectations inside the score-available candidate space. Strong discovery-tier claims should wait until scorecard v2 and, ideally, expanded decoy perturbations.",
            "",
            "## Next Steps",
            "",
            "Build scorecard v2 by merging fingerprints, covariate audit, druggability, graph coherence, and negative controls into one candidate table.",
            "",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    fingerprints = read_required_csv(args.fingerprints)
    fingerprints["candidate"] = normalize_gene(fingerprints["candidate"])
    score_df = fingerprints.set_index("candidate", drop=False)
    for col in SCORE_COLUMNS:
        if col in score_df.columns:
            score_df[col] = pd.to_numeric(score_df[col], errors="coerce")

    scorecard = read_optional_csv(args.scorecard)
    if not scorecard.empty:
        scorecard["candidate"] = normalize_gene(scorecard["candidate"])
        score_df = score_df.combine_first(scorecard.set_index("candidate", drop=False))

    graph_coherence = read_optional_csv(args.graph_coherence)
    adjacency, degrees = read_graph(args.edges)

    candidates = sorted(set(PRIMARY_CANDIDATES) | set(score_df.index))
    degree_controls, degree_summary = degree_matched_controls(
        candidates,
        score_df,
        degrees,
        rng,
        n_nulls=args.n_nulls,
        min_pool=args.min_null_pool,
    )
    label_shuffle = label_shuffle_controls(
        candidates,
        score_df,
        graph_coherence,
        adjacency,
        rng,
        n_nulls=args.n_nulls,
    )
    house_controls = housekeeping_and_hub_controls(score_df, degrees)
    summary = build_summary(candidates, score_df, degree_summary, label_shuffle, house_controls, degrees)

    for path, df in [
        (args.degree_out, degree_controls),
        (args.shuffle_out, label_shuffle),
        (args.housekeeping_out, house_controls),
        (args.summary_out, summary),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)

    write_report(summary, degree_controls, label_shuffle, house_controls, args.report_out)

    print(f"Wrote {args.summary_out}")
    print(f"Wrote {args.degree_out}")
    print(f"Wrote {args.shuffle_out}")
    print(f"Wrote {args.housekeeping_out}")
    print(f"Wrote {args.report_out}")
    print("\nNegative-control status counts:")
    print(summary["negative_control_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
