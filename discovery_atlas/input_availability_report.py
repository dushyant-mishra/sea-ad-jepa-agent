from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class InputSpec:
    key: str
    category: str
    role: str
    priority: str
    paths: tuple[str, ...]
    required_for_phase1: bool = False
    notes: str = ""


INPUT_SPECS: tuple[InputSpec, ...] = (
    InputSpec(
        "gene_multitarget_counterfactual_summary",
        "counterfactual_deltas",
        "Primary gene-level multi-pathology fingerprint input.",
        "core",
        ("results/tables/v2_1_multitarget_gene_counterfactual_summary.csv",),
        True,
        "Already contains AT8, A_beta_6e10, GFAP, Iba1, and NeuN deltas.",
    ),
    InputSpec(
        "module_multitarget_counterfactual_summary",
        "counterfactual_deltas",
        "Primary module-level multi-pathology fingerprint input.",
        "core",
        ("results/tables/v2_1_multitarget_module_counterfactual_summary.csv",),
        True,
        "Already contains multi-target module deltas.",
    ),
    InputSpec(
        "pathology_head_gene_counterfactual_summary",
        "counterfactual_deltas",
        "Frozen Stage B pathology-head counterfactual readout with manifold-safety columns.",
        "core",
        ("results/tables/pathology_head_gene_counterfactual_summary.csv",),
        True,
        "Useful for manifold violation and AT8/NeuN/GFAP/Iba1/6e10 deltas.",
    ),
    InputSpec(
        "pathology_head_module_counterfactual_summary",
        "counterfactual_deltas",
        "Frozen Stage B module-level pathology-head counterfactual readout.",
        "recommended",
        ("results/tables/pathology_head_module_counterfactual_summary.csv",),
    ),
    InputSpec(
        "ranked_target_matrix",
        "target_prioritization",
        "v2.1 ranked target matrix from latent decoding and counterfactual extraction.",
        "core",
        ("results/tables/v2_1_ranked_target_matrix.csv",),
        True,
    ),
    InputSpec(
        "validated_target_matrix_full_covariates",
        "artifact_validation",
        "Validated target matrix with manifold, covariate, and within-state artifact checks.",
        "core",
        ("results/tables/v2_1_target_validation_full_covariates_validated_target_matrix.csv",),
        True,
    ),
    InputSpec(
        "target_covariate_audit_wide",
        "artifact_validation",
        "Target-level donor covariate and technical-proxy audit.",
        "core",
        ("results/tables/v2_2_target_covariate_audit.csv",),
        True,
    ),
    InputSpec(
        "target_covariate_audit_long",
        "artifact_validation",
        "Long-form covariate audit with per-covariate p-values and warning flags.",
        "recommended",
        ("results/tables/v2_2_target_covariate_audit_long.csv",),
    ),
    InputSpec(
        "druggability_biomarker_summary",
        "translation",
        "UniProt localization and ChEMBL triage for artifact-cleared targets.",
        "recommended",
        ("results/tables/v2_2_druggability_summary.csv",),
        True,
    ),
    InputSpec(
        "consensus_graph_edges",
        "graph_topology",
        "Consensus graph edges for 1-hop and 2-hop target-neighborhood coherence.",
        "core",
        ("results/tables/v2_graph_consensus_edges.csv",),
        True,
        "Contains STRING/WGCNA support labels.",
    ),
    InputSpec(
        "consensus_graph_stats",
        "graph_topology",
        "Summary statistics for the consensus graph.",
        "recommended",
        ("results/tables/v2_graph_consensus_stats.csv",),
    ),
    InputSpec(
        "string_graph_edges",
        "graph_topology",
        "STRING graph source for graph-source ablations.",
        "optional",
        ("results/tables/v2_graph_string_edges_t700.csv", "results/tables/v2_graph_string_edges_t*.csv"),
    ),
    InputSpec(
        "wgcna_graph_edges",
        "graph_topology",
        "WGCNA/TOM graph source for graph-source ablations.",
        "optional",
        ("results/tables/v2_graph_wgcna_edges.csv",),
    ),
    InputSpec(
        "module_definitions",
        "modules",
        "Gene-module definitions for module scoring and module fingerprints.",
        "core",
        ("src/sea_ad_jepa/gene_sets.py", "src/sea_ad_jepa/*gene*set*.py"),
        True,
    ),
    InputSpec(
        "donor_pathology_metadata",
        "metadata",
        "Donor-level pathology and covariates for context dependency and audits.",
        "core",
        (
            "data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv",
            "results/tables/sea_ad_full_metadata_targets_with_covariates.csv",
            "results/tables/sea_ad_full_metadata_covariate_audit.csv",
        ),
        True,
        "Data directory is gitignored, but local processed metadata can still be used.",
    ),
    InputSpec(
        "donor_level_counterfactual_outputs",
        "donor_context",
        "By-donor counterfactual deltas for donor-context dependency.",
        "recommended",
        (
            "results/tables/v2_1_upgrade_fine_08_gene_counterfactual_*_by_donor.csv",
            "results/tables/pathology_head_gene_counterfactual_donor.csv",
            "results/tables/pathology_head_module_counterfactual_donor.csv",
        ),
        False,
        "Needed for true perturbation-by-context analysis.",
    ),
    InputSpec(
        "baseline_prediction_leaderboard",
        "baselines",
        "Existing donor-held-out baseline metrics for minimal Graph-JEPA sanity check.",
        "recommended",
        (
            "results/tables/multitarget_oof_jepa_vs_pseudobulk_summary.csv",
            "results/tables/latent_space_evaluation_jepa_vs_pca_summary.csv",
            "results/tables/microglia_pvm_model_comparison.csv",
        ),
    ),
    InputSpec(
        "stage_c_sweep_leaderboards",
        "baselines",
        "Stage C sweep and checkpoint summaries for current active model context.",
        "optional",
        (
            "results/tables/stage_c_finetuning_combined_leaderboard.csv",
            "results/tables/stage_c_upgrade_fine_summary.csv",
            "results/tables/stage_c_checkpoint_evaluation_summary.csv",
        ),
    ),
    InputSpec(
        "negative_control_outputs",
        "negative_controls",
        "Existing shuffled-label, decoy, degree-matched, or random-graph control outputs.",
        "recommended",
        (
            "results/tables/*negative*control*.csv",
            "results/tables/*shuffled*.csv",
            "results/tables/*random*graph*.csv",
            "results/tables/*decoy*.csv",
            "results/tables/*housekeeping*.csv",
        ),
        False,
        "Likely incomplete; missing values should become TODO controls.",
    ),
    InputSpec(
        "target_rank_stability_outputs",
        "robustness",
        "Bootstrap, jackknife, seed, or leave-one-donor-out target-rank stability.",
        "recommended",
        (
            "results/tables/*rank*stability*.csv",
            "results/tables/*bootstrap*.csv",
            "results/tables/*jackknife*.csv",
            "results/tables/*loo*.csv",
            "results/tables/v2_1_gse174367_loo_stability.csv",
        ),
        False,
        "External LOO exists, but target-rank stability may still be missing.",
    ),
    InputSpec(
        "latent_jacobian_outputs",
        "latent_interpretation",
        "Latent Jacobian edges and module annotations for mechanism-context notes.",
        "optional",
        (
            "results/tables/v2_1_upgrade_fine_08_latent_jacobian_top_edges.csv",
            "results/tables/v2_1_upgrade_fine_08_latent_jacobian_module_annotations.csv",
            "results/tables/latent_jacobian_top_edges.csv",
        ),
    ),
    InputSpec(
        "abeta_responsive_outputs",
        "amyloid_axis",
        "Frozen A beta ElasticNet and responder-cell outputs for bounded amyloid notes.",
        "optional",
        (
            "results/tables/v2_2_abeta_frozen_embedding_elasticnet_sweep.csv",
            "results/tables/v2_2_abeta_responsive_microglia_*summary.csv",
            "results/tables/v2_2_abeta_mil_head*_metrics.csv",
        ),
    ),
)


def expand_matches(root: Path, patterns: Iterable[str]) -> list[Path]:
    matches: list[Path] = []
    for pattern in patterns:
        path = root / pattern
        if any(ch in pattern for ch in "*?[]"):
            matches.extend(sorted(root.glob(pattern)))
        elif path.exists():
            matches.append(path)
    unique: list[Path] = []
    seen = set()
    for match in matches:
        key = match.as_posix()
        if key not in seen:
            unique.append(match)
            seen.add(key)
    return unique


def inspect_table(path: Path | None) -> dict[str, str | int]:
    if path is None or path.suffix.lower() not in {".csv", ".tsv"}:
        return {"rows": "", "columns": "", "detected_columns": ""}
    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    try:
        df_head = pd.read_csv(path, sep=sep, nrows=5)
        row_count = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore")) - 1
        return {
            "rows": max(row_count, 0),
            "columns": len(df_head.columns),
            "detected_columns": "; ".join(map(str, df_head.columns[:18])),
        }
    except Exception as exc:  # noqa: BLE001
        return {"rows": "", "columns": "", "detected_columns": f"inspect_failed: {exc}"}


def classify_status(spec: InputSpec, matches: list[Path]) -> tuple[str, str]:
    if not matches:
        if spec.priority == "optional":
            return "optional", "Optional input not found; skip until needed."
        return "missing", "Required/recommended input is absent; write TODO row in downstream atlas."
    if any(ch in pattern for pattern in spec.paths for ch in "*?[]") or len(matches) > 1:
        return "available_but_needs_parsing", "Multiple matching files or globbed inputs; downstream script must choose/merge deliberately."
    if matches[0].suffix.lower() in {".md", ".py"}:
        return "available_but_needs_parsing", "Input exists but requires text/code parsing rather than direct table loading."
    return "available", "Ready for direct table loading."


def build_rows(root: Path) -> list[dict[str, str | int | bool]]:
    rows: list[dict[str, str | int | bool]] = []
    for spec in INPUT_SPECS:
        matches = expand_matches(root, spec.paths)
        status, action = classify_status(spec, matches)
        primary = matches[0] if matches else None
        table_info = inspect_table(primary)
        rows.append(
            {
                "input_key": spec.key,
                "category": spec.category,
                "priority": spec.priority,
                "required_for_phase1": spec.required_for_phase1,
                "status": status,
                "primary_path": primary.as_posix() if primary else "",
                "n_matched_paths": len(matches),
                "matched_paths": " | ".join(path.as_posix() for path in matches[:20]),
                "rows": table_info["rows"],
                "columns": table_info["columns"],
                "detected_columns": table_info["detected_columns"],
                "role": spec.role,
                "notes": spec.notes,
                "recommended_action": action,
            }
        )
    return rows


def write_report(rows: list[dict[str, str | int | bool]], out_path: Path) -> None:
    df = pd.DataFrame(rows)
    counts = df["status"].value_counts().to_dict()
    phase1 = df[df["required_for_phase1"].eq(True)]
    blockers = phase1[phase1["status"].isin(["missing", "blocked"])]

    lines: list[str] = []
    lines.append("# Discovery Atlas Input Availability")
    lines.append("")
    lines.append(
        "This report is Step 0 for the Graph-JEPA Discovery Atlas. It records which existing repo outputs can support the next analyses without retraining or fabricating missing evidence."
    )
    lines.append("")
    lines.append("## Status Summary")
    lines.append("")
    for status in ["available", "available_but_needs_parsing", "missing", "optional", "blocked"]:
        lines.append(f"- `{status}`: {counts.get(status, 0)}")
    lines.append("")
    lines.append("## Phase 1 Gate")
    lines.append("")
    if blockers.empty:
        lines.append(
            "Phase 1 is clear: all required minimal inputs are present. Some inputs still need deliberate parsing, but there is no blocker for pathology-axis fingerprints and a first discovery scorecard."
        )
    else:
        lines.append("Phase 1 has blockers. Do not build fingerprint claims until these are resolved:")
        for _, row in blockers.iterrows():
            lines.append(f"- `{row['input_key']}`: {row['recommended_action']}")
    lines.append("")
    lines.append("## Minimal Viable Phase 1 Inputs")
    lines.append("")
    for _, row in phase1.iterrows():
        lines.append(f"- `{row['input_key']}` - **{row['status']}**")
        if row["primary_path"]:
            lines.append(f"  - path: `{row['primary_path']}`")
        lines.append(f"  - role: {row['role']}")
    lines.append("")
    lines.append("## Recommended Next Analyses")
    lines.append("")
    lines.append("1. Build gene and module pathology-axis fingerprints from `v2_1_multitarget_*_counterfactual_summary.csv`.")
    lines.append("2. Merge covariate and druggability annotations into a first discovery scorecard.")
    lines.append("3. Add graph-neighborhood coherence using `v2_graph_consensus_edges.csv`.")
    lines.append("4. Treat donor-context dependency and pairwise interaction screens as optional until by-donor or paired-perturbation inputs are confirmed.")
    lines.append("5. Add negative controls before making strong discovery-tier claims; current negative-control inputs are incomplete unless new files are added.")
    lines.append("")
    lines.append("## Full Input Table")
    lines.append("")
    display_cols = ["input_key", "category", "priority", "status", "primary_path", "role", "recommended_action"]
    lines.extend(markdown_table(df[display_cols]))
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def markdown_table(df: pd.DataFrame) -> list[str]:
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in df.iterrows():
        values = []
        for header in headers:
            value = str(row[header]).replace("\n", " ").replace("|", "\\|")
            values.append(value)
        lines.append("| " + " | ".join(values) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit existing inputs for the Graph-JEPA Discovery Atlas.")
    parser.add_argument("--out-csv", default="results/tables/discovery_atlas_input_availability_summary.csv")
    parser.add_argument("--out-report", default="results/reports/discovery_atlas_input_availability.md")
    args = parser.parse_args()

    root = Path.cwd()
    rows = build_rows(root)

    out_csv = root / args.out_csv
    out_report = root / args.out_report
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    write_report(rows, out_report)

    df = pd.DataFrame(rows)
    print("Discovery Atlas input availability")
    print(df["status"].value_counts().to_string())
    print("")
    print("Phase 1 required inputs:")
    print(df[df["required_for_phase1"].eq(True)][["input_key", "status", "primary_path"]].to_string(index=False))
    print(f"\nWrote {out_csv}")
    print(f"Wrote {out_report}")


if __name__ == "__main__":
    main()
