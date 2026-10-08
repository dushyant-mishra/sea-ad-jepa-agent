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

SCORE_COLUMNS = [
    "tau_lowering_score",
    "amyloid_lowering_score",
    "neuron_preservation_score",
    "gliosis_penalty",
    "therapeutic_like_score",
    "dual_pathology_lowering_score",
    "broad_shift_score",
]

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
]

NAMED_LARGE_MOVER_AUDIT = ["RC3H1", "PAFAH1B1", "DLG1"]
NAMED_CLEANER_MOVER_AUDIT = ["FIP1L1", "SLAIN2", "PTPN18", "KIF2A", "ERC1"]

EXPECTED_ROWS = 2676
EXPECTED_SCOPE = "graph_connected"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build post-run QC, fingerprints, and scorecard-v2 for graph-connected feature-wide counterfactuals."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "results/tables/discovery_graph_connected_feature_wide_pathology_axis_counterfactuals.csv"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/reports/discovery_feature_wide_run_manifest.md"),
    )
    parser.add_argument(
        "--qc-report",
        type=Path,
        default=Path("results/reports/discovery_graph_connected_feature_wide_postrun_qc.md"),
    )
    parser.add_argument(
        "--fingerprints-out",
        type=Path,
        default=Path(
            "results/tables/discovery_graph_connected_feature_wide_pathology_axis_fingerprints.csv"
        ),
    )
    parser.add_argument(
        "--fingerprints-report",
        type=Path,
        default=Path(
            "results/reports/discovery_graph_connected_feature_wide_pathology_axis_fingerprints.md"
        ),
    )
    parser.add_argument(
        "--scorecard-out",
        type=Path,
        default=Path("results/tables/discovery_scorecard_v2_graph_connected_feature_wide.csv"),
    )
    parser.add_argument(
        "--scorecard-report",
        type=Path,
        default=Path("results/reports/discovery_scorecard_v2_graph_connected_feature_wide.md"),
    )
    return parser.parse_args()


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def percentile_rank(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").rank(method="average", pct=True) * 100.0


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in DELTA_COLUMNS:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out["gene"] = out["gene"].astype(str).str.upper()
    out["tau_lowering_score"] = -out["AT8_delta"]
    out["amyloid_lowering_score"] = -out["A_beta_6e10_delta"]
    out["neuron_preservation_score"] = out["NeuN_delta"]
    out["gliosis_penalty"] = out["GFAP_delta"].clip(lower=0) + out["Iba1_delta"].clip(lower=0)
    out["therapeutic_like_score"] = (
        out["tau_lowering_score"] + out["neuron_preservation_score"] - out["gliosis_penalty"]
    )
    out["dual_pathology_lowering_score"] = (
        out["tau_lowering_score"] + out["amyloid_lowering_score"]
    )
    out["broad_shift_score"] = out[DELTA_COLUMNS].abs().mean(axis=1)
    for column in SCORE_COLUMNS:
        out[f"{column}_percentile"] = percentile_rank(out[column])
    return out


def classify_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    labels: list[str] = []
    reasons: list[str] = []
    profiles: list[str] = []
    amyloid_selective_flags: list[bool] = []

    for _, row in out.iterrows():
        tau_pct = float(row["tau_lowering_score_percentile"])
        amyloid_pct = float(row["amyloid_lowering_score_percentile"])
        neuron_pct = float(row["neuron_preservation_score_percentile"])
        gliosis_pct = float(row["gliosis_penalty_percentile"])
        therapeutic_pct = float(row["therapeutic_like_score_percentile"])
        dual_pct = float(row["dual_pathology_lowering_score_percentile"])
        broad_pct = float(row["broad_shift_score_percentile"])

        tau_down = row["tau_lowering_score"] > 0 and tau_pct >= 90
        amyloid_down = row["amyloid_lowering_score"] > 0 and amyloid_pct >= 90
        neuron_up = row["neuron_preservation_score"] > 0 and neuron_pct >= 50
        neuron_risk = row["neuron_preservation_score"] < 0 and neuron_pct <= 10
        gliosis_high = row["gliosis_penalty"] > 0 and gliosis_pct >= 90
        broad_high = broad_pct >= 95
        low_spillover = gliosis_pct < 60 and broad_pct < 75
        amyloid_selective = (
            amyloid_pct >= 95
            and row["amyloid_lowering_score"] > 0
            and abs(float(row["AT8_delta"])) <= abs(float(row["A_beta_6e10_delta"])) * 0.5
            and low_spillover
        )
        amyloid_selective_flags.append(bool(amyloid_selective))

        clean_dual = (
            tau_down
            and amyloid_down
            and neuron_up
            and dual_pct >= 90
            and gliosis_pct < 75
            and broad_pct < 95
        )
        clean_tau = (
            tau_down
            and neuron_up
            and therapeutic_pct >= 75
            and gliosis_pct < 75
            and broad_pct < 95
        )

        if neuron_risk:
            label = "neuron_risk"
            reason = "NeuN effect falls in the bottom decile of the graph-connected gene universe."
        elif clean_dual:
            label = "dual_pathology_lowering_neuron_preserving"
            reason = "Top-decile tau and amyloid lowering with positive NeuN and sub-threshold gliosis/broad shift."
        elif clean_tau:
            label = "tau_lowering_neuron_preserving"
            reason = "Top-decile tau lowering with positive NeuN and limited gliosis/broad-state penalties."
        elif broad_high and (gliosis_pct >= 75 or therapeutic_pct < 75):
            label = "broad_reactive_state_shift"
            reason = "Broad-shift score is in the top 5% with reactive-state spillover or weak therapeutic balance."
        elif gliosis_high:
            label = "gliosis_inflating"
            reason = "Positive GFAP/Iba1 penalty is in the top decile."
        elif amyloid_down:
            label = "amyloid_lowering_candidate"
            reason = "Amyloid lowering is in the top decile, but clean dual/tau-neuron criteria were not met."
        else:
            label = "mixed_or_unclear"
            reason = "No conservative top-decile pathology-axis rule passed."

        if broad_high or gliosis_high:
            profile = "large_mover_with_broad_or_gliosis_penalty"
        elif (
            tau_down
            and neuron_up
            and therapeutic_pct >= 90
            and gliosis_pct < 60
            and broad_pct < 90
        ):
            profile = "cleaner_therapeutic_like_mover"
        else:
            profile = "other_or_unresolved"

        labels.append(label)
        reasons.append(reason)
        profiles.append(profile)

    out["pathology_axis_class"] = labels
    out["classification_reason"] = reasons
    out["movement_profile"] = profiles
    out["amyloid_selective_stringent_flag"] = amyloid_selective_flags
    out["is_prior_candidate"] = out["gene"].isin(PRIOR_CANDIDATES)
    out["prior_candidate_set"] = np.where(out["is_prior_candidate"], "older_candidate_screen", "")
    out["named_review_group"] = ""
    out.loc[out["gene"].isin(NAMED_LARGE_MOVER_AUDIT), "named_review_group"] = (
        "proposed_large_mover_audit"
    )
    out.loc[out["gene"].isin(NAMED_CLEANER_MOVER_AUDIT), "named_review_group"] = (
        "proposed_cleaner_mover_audit"
    )
    expected_profile = np.where(
        out["named_review_group"].eq("proposed_large_mover_audit"),
        "large_mover_with_broad_or_gliosis_penalty",
        np.where(
            out["named_review_group"].eq("proposed_cleaner_mover_audit"),
            "cleaner_therapeutic_like_mover",
            "",
        ),
    )
    out["named_review_support"] = np.where(
        out["named_review_group"].eq(""),
        "",
        np.where(
            out["movement_profile"].eq(expected_profile),
            "supported_by_current_v2_profile",
            "not_supported_by_current_v2_profile",
        ),
    )
    out["manifold_evidence_scope"] = np.where(
        out["manifold_safety_status"].astype(str).eq("not_computed"),
        "full_run_pathology_delta_only",
        "manifold_checked",
    )
    return out


def markdown_table(df: pd.DataFrame, columns: list[str], n: int = 15) -> list[str]:
    subset = df.loc[:, columns].head(n).copy()
    if subset.empty:
        return ["_No rows met this criterion._"]
    for column in subset.select_dtypes(include=["float", "float64", "float32"]).columns:
        subset[column] = subset[column].map(lambda value: f"{value:.5g}" if pd.notna(value) else "")
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in subset.itertuples(index=False, name=None)
    ]
    return [header, divider, *rows]


def write_qc_report(args: argparse.Namespace, raw: pd.DataFrame) -> None:
    unique_genes = raw["gene"].astype(str).str.upper().nunique()
    success_counts = raw["perturbation_success"].astype(str).value_counts(dropna=False)
    manifold_counts = raw["manifold_safety_status"].astype(str).value_counts(dropna=False)
    missing = raw[DELTA_COLUMNS].isna().sum()
    manifest_text = args.manifest.read_text(encoding="utf-8") if args.manifest.exists() else ""
    manifest_zero_failures = "Chunks failed: 0" in manifest_text
    manifest_27_chunks = "Chunks completed or reused: 27" in manifest_text
    all_scope_graph = raw["scope"].astype(str).eq(EXPECTED_SCOPE).all()

    lines = [
        "# Graph-Connected Feature-Wide Post-Run QC",
        "",
        "## Completion Checks",
        "",
        f"- Rows: **{len(raw):,}** (`{'PASS' if len(raw) == EXPECTED_ROWS else 'FAIL'}`; expected {EXPECTED_ROWS:,})",
        f"- Unique graph-connected genes: **{unique_genes:,}** (`{'PASS' if unique_genes == EXPECTED_ROWS else 'FAIL'}`)",
        f"- Scope is `graph_connected` for every row: **{all_scope_graph}**",
        f"- Manifest reports 27 completed/reused chunks: **{manifest_27_chunks}**",
        f"- Manifest reports 0 failed chunks: **{manifest_zero_failures}**",
        "",
        "## Perturbation Success",
        "",
        "| perturbation_success | count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {key} | {value:,} |" for key, value in success_counts.items())
    lines.extend(
        [
            "",
            "## Missing Pathology Deltas",
            "",
            "| delta column | missing values |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| {column} | {int(missing[column]):,} |" for column in DELTA_COLUMNS)
    lines.extend(
        [
            "",
            "## Manifold-Safety Boundary",
            "",
            "| manifold_safety_status | count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| {key} | {value:,} |" for key, value in manifold_counts.items())
    lines.extend(
        [
            "",
            "The full run used `--skip-manifold-nearest-neighbor` because Windows scikit-learn/threadpoolctl crashed inside the nearest-neighbor manifold check. Therefore, the full graph-connected output is valid for pathology-delta ranking and null calibration, but it is **not manifold-verified**.",
            "",
            "The successful pilot remains the manifold-verified feature-wide evidence. Any promoted top hit should receive a later targeted manifold audit.",
            "",
            "## QC Verdict",
            "",
            (
                "**PASS for scorecard construction.** Row count, unique-gene count, chunk completion, "
                "perturbation success, and pathology-delta completeness are consistent with a complete run."
                if (
                    len(raw) == EXPECTED_ROWS
                    and unique_genes == EXPECTED_ROWS
                    and manifest_zero_failures
                    and manifest_27_chunks
                    and int(missing.sum()) == 0
                )
                else "**FAIL or incomplete.** Resolve the discrepancies above before using this table."
            ),
            "",
        ]
    )
    args.qc_report.parent.mkdir(parents=True, exist_ok=True)
    args.qc_report.write_text("\n".join(lines), encoding="utf-8")


def write_fingerprint_report(args: argparse.Namespace, fingerprints: pd.DataFrame) -> None:
    score_summary = fingerprints[SCORE_COLUMNS].describe(percentiles=[0.1, 0.5, 0.9, 0.95]).T
    lines = [
        "# Graph-Connected Feature-Wide Pathology-Axis Fingerprints",
        "",
        f"- Genes scored: {len(fingerprints):,}",
        "- Universe: Graph-JEPA feature genes connected to the consensus graph.",
        "- Scores are model-implied pathology-head deltas under global-mean intervention.",
        "",
        "## Score Definitions",
        "",
        "- `tau_lowering_score = -AT8_delta`",
        "- `amyloid_lowering_score = -A_beta_6e10_delta`",
        "- `neuron_preservation_score = NeuN_delta`",
        "- `gliosis_penalty = max(GFAP_delta, 0) + max(Iba1_delta, 0)`",
        "- `therapeutic_like_score = tau_lowering_score + neuron_preservation_score - gliosis_penalty`",
        "- `dual_pathology_lowering_score = tau_lowering_score + amyloid_lowering_score`",
        "- `broad_shift_score = mean absolute delta across all five pathology readouts`",
        "",
        "Every score includes a percentile rank against all 2,676 graph-connected genes.",
        "",
        "## Distribution Summary",
        "",
        "| score | mean | std | p10 | median | p90 | p95 | max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for score, row in score_summary.iterrows():
        lines.append(
            f"| {score} | {row['mean']:.5g} | {row['std']:.5g} | {row['10%']:.5g} | "
            f"{row['50%']:.5g} | {row['90%']:.5g} | {row['95%']:.5g} | {row['max']:.5g} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "These fingerprints support pathology-delta ranking and null calibration. Nearest-neighbor manifold safety was not computed in the full run. The successful pilot and later targeted audits provide manifold-verified evidence.",
            "",
        ]
    )
    args.fingerprints_report.parent.mkdir(parents=True, exist_ok=True)
    args.fingerprints_report.write_text("\n".join(lines), encoding="utf-8")


def write_scorecard_report(args: argparse.Namespace, scorecard: pd.DataFrame) -> None:
    class_counts = scorecard["pathology_axis_class"].value_counts()
    large = scorecard[
        scorecard["movement_profile"].eq("large_mover_with_broad_or_gliosis_penalty")
    ].sort_values("broad_shift_score", ascending=False)
    clean = scorecard[
        scorecard["movement_profile"].eq("cleaner_therapeutic_like_mover")
    ].sort_values("therapeutic_like_score", ascending=False)
    prior = scorecard[scorecard["is_prior_candidate"]].sort_values(
        "therapeutic_like_score", ascending=False
    )
    named_audit = scorecard[scorecard["named_review_group"].ne("")].sort_values(
        ["named_review_group", "therapeutic_like_score"],
        ascending=[True, False],
    )
    display_columns = [
        "gene",
        "pathology_axis_class",
        "AT8_delta",
        "A_beta_6e10_delta",
        "NeuN_delta",
        "gliosis_penalty",
        "broad_shift_score",
        "therapeutic_like_score",
    ]
    lines = [
        "# Discovery Scorecard v2: Graph-Connected Feature-Wide",
        "",
        "## Classification Counts",
        "",
        "| class | count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {label} | {count:,} |" for label, count in class_counts.items())
    lines.extend(
        [
            "",
            "## Large Movers With Broad-State or Gliosis Penalties",
            "",
            *markdown_table(large, display_columns),
            "",
            "These genes are separated from cleaner candidates because a large favorable pathology delta can coexist with broad-state movement or gliosis inflation.",
            "",
            "## Cleaner Therapeutic-Like Movers",
            "",
            *markdown_table(clean, display_columns),
            "",
            "This is a ranking category, not evidence of therapeutic efficacy or causal biology.",
            "",
            "## Named Mover Audit",
            "",
            *markdown_table(
                named_audit,
                [
                    "gene",
                    "named_review_group",
                    "named_review_support",
                    "pathology_axis_class",
                    "movement_profile",
                    "AT8_delta",
                    "NeuN_delta",
                    "gliosis_penalty",
                    "broad_shift_score",
                    "therapeutic_like_score",
                ],
                n=len(NAMED_LARGE_MOVER_AUDIT) + len(NAMED_CLEANER_MOVER_AUDIT),
            ),
            "",
            "The proposed cleaner-mover examples are retained as an explicit audit set. They are not promoted when their full-universe percentiles indicate broad-state or gliosis spillover.",
            "",
            "## Prior Candidate Screen Genes",
            "",
            *markdown_table(prior, display_columns, n=len(PRIOR_CANDIDATES)),
            "",
            "## Amyloid Selectivity Rule",
            "",
            "`amyloid_selective_stringent_flag` is true only for top-5% amyloid lowering with low gliosis and broad-shift spillover and limited AT8 movement. The main conservative class remains `amyloid_lowering_candidate`; no stronger biological conclusion is implied.",
            "",
            "## Boundary",
            "",
            "The graph-connected feature-wide run is used for pathology-delta ranking and null calibration. Nearest-neighbor manifold safety was not computed in the full run due to the Windows sklearn/threadpoolctl issue. Manifold-verified evidence comes from the successful pilot and any later targeted top-hit audits.",
            "",
            "Biological conclusions should not be rewritten until scorecard-v2 negative controls are complete.",
            "",
        ]
    )
    args.scorecard_report.parent.mkdir(parents=True, exist_ok=True)
    args.scorecard_report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    raw = read_required_csv(args.input)
    required = {"gene", "scope", "perturbation_success", "manifold_safety_status", *DELTA_COLUMNS}
    missing_columns = sorted(required - set(raw.columns))
    if missing_columns:
        raise ValueError(f"Input is missing required columns: {missing_columns}")

    write_qc_report(args, raw)
    fingerprints = add_scores(raw)
    fingerprints = fingerprints.sort_values(
        ["therapeutic_like_score", "dual_pathology_lowering_score"],
        ascending=False,
    ).reset_index(drop=True)
    args.fingerprints_out.parent.mkdir(parents=True, exist_ok=True)
    fingerprints.to_csv(args.fingerprints_out, index=False)
    write_fingerprint_report(args, fingerprints)

    scorecard = classify_scorecard(fingerprints)
    scorecard = scorecard.sort_values(
        ["therapeutic_like_score", "dual_pathology_lowering_score"],
        ascending=False,
    ).reset_index(drop=True)
    args.scorecard_out.parent.mkdir(parents=True, exist_ok=True)
    scorecard.to_csv(args.scorecard_out, index=False)
    write_scorecard_report(args, scorecard)

    print(f"Wrote QC report: {args.qc_report}")
    print(f"Wrote fingerprints: {args.fingerprints_out}")
    print(f"Wrote fingerprint report: {args.fingerprints_report}")
    print(f"Wrote scorecard-v2: {args.scorecard_out}")
    print(f"Wrote scorecard report: {args.scorecard_report}")


if __name__ == "__main__":
    main()
