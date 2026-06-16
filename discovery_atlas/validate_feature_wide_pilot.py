from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PILOT_COLUMNS = [
    "gene",
    "scope",
    "AT8_delta",
    "A_beta_6e10_delta",
    "GFAP_delta",
    "Iba1_delta",
    "NeuN_delta",
    "manifold_safety_status",
    "prediction_safety_status",
    "perturbation_success",
    "failure_reason",
]

REFERENCE_MAP = {
    "mean_delta_percent AT8 positive area_Grey matter": "AT8_delta",
    "mean_delta_percent 6e10 positive area_Grey matter": "A_beta_6e10_delta",
    "mean_delta_percent GFAP positive area_Grey matter": "GFAP_delta",
    "mean_delta_percent Iba1 positive area_Grey matter": "Iba1_delta",
    "mean_delta_percent NeuN positive area_Grey matter": "NeuN_delta",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate pilot feature-wide counterfactual output.")
    parser.add_argument(
        "--pilot",
        type=Path,
        default=Path("results/tables/discovery_pilot_feature_wide_pathology_axis_counterfactuals.csv"),
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("results/tables/pathology_head_gene_counterfactual_summary.csv"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/reports/discovery_pilot_feature_wide_counterfactual_validation.md"),
    )
    parser.add_argument(
        "--comparison-out",
        type=Path,
        default=Path("results/tables/discovery_pilot_feature_wide_reference_comparison.csv"),
    )
    parser.add_argument(
        "--observed-runtime-seconds",
        type=float,
        default=0.0,
        help="Optional approximate wall-clock runtime for the pilot inference.",
    )
    return parser.parse_args()


def read_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                vals.append("" if pd.isna(val) else f"{val:.4g}")
            else:
                vals.append(str(val).replace("|", "\\|"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def reference_to_delta(reference: pd.DataFrame) -> pd.DataFrame:
    ref = pd.DataFrame()
    ref["gene"] = reference["perturbation"].astype(str).str.upper()
    for old, new in REFERENCE_MAP.items():
        if old in reference.columns:
            ref[new] = pd.to_numeric(reference[old], errors="coerce")
    return ref


def compare_to_reference(pilot: pd.DataFrame, reference: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ref = reference_to_delta(reference)
    merged = pilot.merge(ref, on="gene", how="inner", suffixes=("_pilot", "_reference"))
    rows = []
    for target in REFERENCE_MAP.values():
        p_col = f"{target}_pilot"
        r_col = f"{target}_reference"
        if p_col not in merged.columns or r_col not in merged.columns:
            continue
        p = pd.to_numeric(merged[p_col], errors="coerce")
        r = pd.to_numeric(merged[r_col], errors="coerce")
        valid = p.notna() & r.notna()
        if not valid.any():
            continue
        rows.append(
            {
                "target": target,
                "n_overlap": int(valid.sum()),
                "sign_agreement": float((np.sign(p[valid]) == np.sign(r[valid])).mean()),
                "median_abs_diff": float((p[valid] - r[valid]).abs().median()),
                "spearman": float(p[valid].corr(r[valid], method="spearman")),
            }
        )
    return merged, pd.DataFrame(rows)


def write_report(
    pilot: pd.DataFrame,
    comparison_rows: pd.DataFrame,
    args: argparse.Namespace,
    missing_columns: list[str],
) -> None:
    n_rows = len(pilot)
    n_success = int(pilot["perturbation_success"].fillna(False).sum())
    n_failed = n_rows - n_success
    safety_counts = pilot["manifold_safety_status"].value_counts(dropna=False).reset_index()
    safety_counts.columns = ["manifold_safety_status", "count"]
    runtime_lines: list[str] = []
    if args.observed_runtime_seconds > 0 and n_rows > 0:
        runtime_lines = [
            f"- Approximate observed runtime: {args.observed_runtime_seconds / 60.0:.1f} minutes",
            f"- Approximate runtime per gene: {args.observed_runtime_seconds / n_rows:.1f} seconds/gene",
        ]
    else:
        runtime_lines = ["- Runtime was not supplied to the validation script."]

    lines = [
        "# Discovery Pilot Feature-Wide Counterfactual Validation",
        "",
        "## Executive Summary",
        "",
        f"- Pilot rows: {n_rows:,}",
        f"- Successful perturbations: {n_success:,}",
        f"- Failed perturbations: {n_failed:,}",
        f"- Missing required columns: {', '.join(missing_columns) if missing_columns else 'none'}",
        *runtime_lines,
        "",
        "## Manifold Safety",
        "",
        markdown_table(safety_counts),
        "",
        "## Reference Reproduction Check",
        "",
        "The pilot is compared against `pathology_head_gene_counterfactual_summary.csv`, the closest existing frozen pathology-head gene counterfactual output. Differences can still arise from sampled cells, target set, or wrapper settings.",
        "",
        markdown_table(comparison_rows),
        "",
        "## Output Schema",
        "",
        markdown_table(pd.DataFrame({"column": PILOT_COLUMNS, "present": [c in pilot.columns for c in PILOT_COLUMNS]})),
        "",
        "## Claim Boundary",
        "",
        "This pilot validates the feature-wide scoring workflow and output schema. It does not validate biological causality. Feature-wide means the Graph-JEPA feature-gene universe, not the whole genome.",
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    pilot = read_required(args.pilot)
    pilot["gene"] = pilot["gene"].astype(str).str.upper()
    missing_columns = [col for col in PILOT_COLUMNS if col not in pilot.columns]

    reference = read_required(args.reference)
    comparison, comparison_rows = compare_to_reference(pilot, reference)
    args.comparison_out.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.comparison_out, index=False)

    write_report(pilot, comparison_rows, args, missing_columns)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.comparison_out}")
    print("\nComparison summary:")
    print(comparison_rows.to_string(index=False))


if __name__ == "__main__":
    main()
