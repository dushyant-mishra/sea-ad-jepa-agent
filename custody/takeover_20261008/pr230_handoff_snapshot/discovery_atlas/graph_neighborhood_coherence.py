from __future__ import annotations

import argparse
import math
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd


DEFAULT_SCORECARD = Path("results/tables/discovery_candidate_scorecard_v1.csv")
DEFAULT_EDGES = Path("results/tables/v2_graph_consensus_edges.csv")
DEFAULT_OUT = Path("results/tables/discovery_graph_neighborhood_coherence.csv")
DEFAULT_REPORT = Path("results/reports/discovery_graph_neighborhood_coherence.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit whether Discovery Atlas candidate genes sit in coherent graph neighborhoods "
            "relative to degree-matched null nodes."
        )
    )
    parser.add_argument("--scorecard", type=Path, default=DEFAULT_SCORECARD)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--n-nulls", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument(
        "--degree-window",
        type=float,
        default=0.20,
        help="Initial relative degree window for null matching. The script widens if needed.",
    )
    parser.add_argument(
        "--min-null-pool",
        type=int,
        default=100,
        help="Minimum desired degree-matched null pool size before sampling.",
    )
    return parser.parse_args()


def read_scorecard(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing scorecard: {path}")
    df = pd.read_csv(path)
    if "candidate" not in df.columns:
        raise ValueError(f"Scorecard must contain a candidate column: {path}")
    df["candidate"] = df["candidate"].astype(str).str.upper()
    return df.set_index("candidate", drop=False)


def read_graph(path: Path) -> dict[str, set[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing graph edge file: {path}")
    usecols = ["source", "target"]
    edges = pd.read_csv(path, usecols=usecols)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for source, target in edges[usecols].itertuples(index=False, name=None):
        source = str(source).upper()
        target = str(target).upper()
        if source == target:
            continue
        adjacency[source].add(target)
        adjacency[target].add(source)
    return dict(adjacency)


def mean_or_nan(values: list[float]) -> float:
    valid = [v for v in values if math.isfinite(v)]
    if not valid:
        return float("nan")
    return float(sum(valid) / len(valid))


def std_or_nan(values: list[float]) -> float:
    valid = [v for v in values if math.isfinite(v)]
    if len(valid) < 2:
        return float("nan")
    mu = sum(valid) / len(valid)
    return float(math.sqrt(sum((v - mu) ** 2 for v in valid) / (len(valid) - 1)))


def empirical_p(observed: float, null_values: list[float], higher_is_enriched: bool = True) -> float:
    valid = [v for v in null_values if math.isfinite(v)]
    if not valid or not math.isfinite(observed):
        return float("nan")
    if higher_is_enriched:
        extreme = sum(v >= observed for v in valid)
    else:
        extreme = sum(v <= observed for v in valid)
    return float((extreme + 1) / (len(valid) + 1))


def z_score(observed: float, null_values: list[float]) -> float:
    mu = mean_or_nan(null_values)
    sd = std_or_nan(null_values)
    if not math.isfinite(observed) or not math.isfinite(mu) or not math.isfinite(sd) or sd == 0:
        return float("nan")
    return float((observed - mu) / sd)


def degree_matched_pool(
    gene: str,
    degrees: dict[str, int],
    *,
    degree_window: float,
    min_pool: int,
) -> list[str]:
    degree = degrees.get(gene, 0)
    if degree == 0:
        return [node for node, deg in degrees.items() if deg == 0 and node != gene]

    window = max(degree_window, 0.01)
    nodes: list[str] = []
    while window <= 2.0:
        low = max(1, math.floor(degree * (1.0 - window)))
        high = max(low, math.ceil(degree * (1.0 + window)))
        nodes = [node for node, deg in degrees.items() if low <= deg <= high and node != gene]
        if len(nodes) >= min_pool:
            break
        window *= 1.5
    if not nodes:
        nodes = [node for node in degrees if node != gene]
    return nodes


def neighborhood_metrics(
    gene: str,
    target_class: str,
    adjacency: dict[str, set[str]],
    scorecard: pd.DataFrame,
) -> dict[str, float]:
    neighbors = adjacency.get(gene, set())
    scored_neighbors = sorted(n for n in neighbors if n in scorecard.index)
    same_class_neighbors = [
        n for n in scored_neighbors if str(scorecard.at[n, "pathology_axis_class"]) == target_class
    ]

    sort_scores = [
        float(scorecard.at[n, "discovery_sort_score"])
        for n in scored_neighbors
        if "discovery_sort_score" in scorecard.columns and pd.notna(scorecard.at[n, "discovery_sort_score"])
    ]
    therapeutic_scores = [
        float(scorecard.at[n, "therapeutic_like_score"])
        for n in scored_neighbors
        if "therapeutic_like_score" in scorecard.columns
        and pd.notna(scorecard.at[n, "therapeutic_like_score"])
    ]
    amyloid_scores = [
        float(scorecard.at[n, "amyloid_selectivity_score"])
        for n in scored_neighbors
        if "amyloid_selectivity_score" in scorecard.columns
        and pd.notna(scorecard.at[n, "amyloid_selectivity_score"])
    ]

    return {
        "degree": float(len(neighbors)),
        "n_scored_neighbors": float(len(scored_neighbors)),
        "n_same_class_neighbors": float(len(same_class_neighbors)),
        "same_class_neighbor_fraction": (
            float(len(same_class_neighbors) / len(scored_neighbors)) if scored_neighbors else float("nan")
        ),
        "mean_neighbor_discovery_sort_score": mean_or_nan(sort_scores),
        "mean_neighbor_therapeutic_like_score": mean_or_nan(therapeutic_scores),
        "mean_neighbor_amyloid_selectivity_score": mean_or_nan(amyloid_scores),
    }


def classify_coherence(row: pd.Series) -> str:
    if row["degree"] == 0:
        return "not_in_graph_or_isolated"
    if row["n_scored_neighbors"] == 0:
        return "no_scored_candidate_neighbors"
    if row["same_class_neighbor_p"] <= 0.05 and row["same_class_neighbor_z"] > 1.0:
        return "coherent_same_axis_neighborhood"
    if row["scored_neighbor_p"] <= 0.05 and row["scored_neighbor_z"] > 1.0:
        return "candidate_enriched_neighborhood"
    return "no_graph_enrichment"


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> tuple[pd.DataFrame, str]:
    rng = random.Random(args.seed)
    scorecard = read_scorecard(args.scorecard)
    adjacency = read_graph(args.edges)
    degrees = {node: len(neighbors) for node, neighbors in adjacency.items()}

    rows: list[dict[str, object]] = []
    for gene, record in scorecard.iterrows():
        target_class = str(record["pathology_axis_class"])
        observed = neighborhood_metrics(gene, target_class, adjacency, scorecard)
        pool = degree_matched_pool(
            gene,
            degrees,
            degree_window=args.degree_window,
            min_pool=args.min_null_pool,
        )
        null_nodes = [rng.choice(pool) for _ in range(args.n_nulls)] if pool else []
        null_metrics = [
            neighborhood_metrics(node, target_class, adjacency, scorecard) for node in null_nodes
        ]

        scored_null = [m["n_scored_neighbors"] for m in null_metrics]
        same_class_null = [m["n_same_class_neighbors"] for m in null_metrics]
        sort_score_null = [m["mean_neighbor_discovery_sort_score"] for m in null_metrics]

        row: dict[str, object] = {
            "candidate": gene,
            "pathology_axis_class": target_class,
            "covariate_audit_status": record.get("covariate_audit_status", ""),
            "degree_matched_null_pool_size": len(pool),
            **observed,
            "expected_scored_neighbors": mean_or_nan(scored_null),
            "scored_neighbor_z": z_score(observed["n_scored_neighbors"], scored_null),
            "scored_neighbor_p": empirical_p(observed["n_scored_neighbors"], scored_null),
            "expected_same_class_neighbors": mean_or_nan(same_class_null),
            "same_class_neighbor_z": z_score(observed["n_same_class_neighbors"], same_class_null),
            "same_class_neighbor_p": empirical_p(observed["n_same_class_neighbors"], same_class_null),
            "neighbor_discovery_sort_score_z": z_score(
                observed["mean_neighbor_discovery_sort_score"], sort_score_null
            ),
            "neighbor_discovery_sort_score_p": empirical_p(
                observed["mean_neighbor_discovery_sort_score"], sort_score_null
            ),
        }
        rows.append(row)

    out = pd.DataFrame(rows)
    out["coherence_status"] = out.apply(classify_coherence, axis=1)
    out = out.sort_values(
        ["coherence_status", "same_class_neighbor_z", "scored_neighbor_z"],
        ascending=[True, False, False],
    )
    return out, build_report(out, args)


def build_report(df: pd.DataFrame, args: argparse.Namespace) -> str:
    counts = df["coherence_status"].value_counts().to_dict()
    lines = [
        "# Discovery Atlas Graph-Neighborhood Coherence",
        "",
        "This report tests whether candidate genes sit in graph neighborhoods enriched for other scored candidates or for candidates with the same pathology-axis class. Nulls are degree-matched, so high-degree hub genes do not automatically look coherent.",
        "",
        "## Configuration",
        "",
        f"- Scorecard: `{args.scorecard}`",
        f"- Graph edges: `{args.edges}`",
        f"- Null draws per candidate: `{args.n_nulls}`",
        f"- Initial degree window: `{args.degree_window}`",
        "",
        "## Coherence Status Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: {value}")

    display_cols = [
        "candidate",
        "pathology_axis_class",
        "coherence_status",
        "degree",
        "n_scored_neighbors",
        "n_same_class_neighbors",
        "scored_neighbor_z",
        "scored_neighbor_p",
        "same_class_neighbor_z",
        "same_class_neighbor_p",
        "covariate_audit_status",
    ]
    top = df[display_cols].head(20).copy()
    for col in top.select_dtypes(include=["float64", "float32"]).columns:
        top[col] = top[col].map(lambda x: "" if pd.isna(x) else f"{x:.4g}")

    lines.extend(
        [
            "",
            "## Candidate Neighborhood Table",
            "",
            markdown_table(top),
            "",
            "## Interpretation Boundary",
            "",
            "Graph-neighborhood coherence is supportive evidence, not causal proof. A target can be biologically important without a candidate-enriched one-hop neighborhood, and a coherent graph neighborhood can still reflect annotation bias, hub biology, or disease-state correlation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    df, report = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    args.report.write_text(report, encoding="utf-8")

    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    print("\nCoherence status counts:")
    print(df["coherence_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
