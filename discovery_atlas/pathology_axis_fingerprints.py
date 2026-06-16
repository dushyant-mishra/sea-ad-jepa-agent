from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DELTA_COLUMNS = ["AT8_delta", "A_beta_6e10_delta", "GFAP_delta", "Iba1_delta", "NeuN_delta"]


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def positive_part(series: pd.Series) -> pd.Series:
    return series.clip(lower=0.0)


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in DELTA_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["tau_lowering_score"] = -out["AT8_delta"]
    out["amyloid_lowering_score"] = -out["A_beta_6e10_delta"]
    out["neuron_preservation_score"] = out["NeuN_delta"]
    out["gliosis_penalty"] = positive_part(out["GFAP_delta"]) + positive_part(out["Iba1_delta"])
    out["broad_shift_score"] = out[DELTA_COLUMNS].abs().mean(axis=1)
    out["therapeutic_like_score"] = (
        out["tau_lowering_score"] + out["neuron_preservation_score"] - out["gliosis_penalty"]
    )
    out["amyloid_selectivity_score"] = (
        out["amyloid_lowering_score"] - out["AT8_delta"].abs() - out["gliosis_penalty"]
    )
    out["tau_selectivity_score"] = (
        out["tau_lowering_score"] - out["A_beta_6e10_delta"].abs() - out["gliosis_penalty"]
    )
    out["dual_pathology_lowering_score"] = out["tau_lowering_score"] + out["amyloid_lowering_score"]
    out["neuron_risk_score"] = -out["NeuN_delta"]
    return out


def robust_threshold(series: pd.Series, floor: float = 0.002) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna().abs()
    if values.empty:
        return floor
    return max(float(values.quantile(0.50)), floor)


def classify_rows(df: pd.DataFrame, artifact_col: str | None = None) -> pd.DataFrame:
    out = df.copy()
    tau_thr = robust_threshold(out["tau_lowering_score"])
    amy_thr = robust_threshold(out["amyloid_lowering_score"])
    neun_thr = robust_threshold(out["neuron_preservation_score"])
    gliosis_thr = robust_threshold(out["gliosis_penalty"])
    broad_thr = robust_threshold(out["broad_shift_score"])

    classes: list[str] = []
    for _, row in out.iterrows():
        artifact = bool(row.get(artifact_col, False)) if artifact_col else False
        tau_down = row["tau_lowering_score"] >= tau_thr
        amy_down = row["amyloid_lowering_score"] >= amy_thr
        neuron_up = row["neuron_preservation_score"] >= neun_thr
        neuron_down = row["neuron_preservation_score"] <= -neun_thr
        gliosis_high = row["gliosis_penalty"] >= gliosis_thr
        broad_high = row["broad_shift_score"] >= broad_thr
        homeostatic_like = neuron_up and row["GFAP_delta"] <= 0 and row["Iba1_delta"] <= 0

        if artifact:
            label = "artifact_or_covariate_sensitive"
        elif neuron_down:
            label = "neuron_risk"
        elif tau_down and neuron_up and not gliosis_high:
            label = "tau_lowering_neuron_preserving"
        elif tau_down and amy_down and neuron_up:
            label = "dual_pathology_lowering"
        elif amy_down and not tau_down and not gliosis_high:
            label = "amyloid_lowering_selective"
        elif homeostatic_like:
            label = "homeostatic_restoring"
        elif gliosis_high and broad_high:
            label = "broad_reactive_state_shift"
        elif gliosis_high:
            label = "gliosis_inflating"
        else:
            label = "mixed_or_unclear"
        classes.append(label)

    out["pathology_axis_class"] = classes
    out["classification_threshold_tau_lowering"] = tau_thr
    out["classification_threshold_amyloid_lowering"] = amy_thr
    out["classification_threshold_neuron_preservation"] = neun_thr
    out["classification_threshold_gliosis_penalty"] = gliosis_thr
    return out


def load_covariate_flags(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["candidate", "covariate_audit_status", "covariate_warning_details"])
    df = pd.read_csv(path)
    gene_col = "Gene" if "Gene" in df.columns else "gene"
    return pd.DataFrame(
        {
            "candidate": df[gene_col].astype(str),
            "covariate_audit_status": df.get("Status", "not_available"),
            "covariate_warning_details": df.get("Warning Details", ""),
        }
    )


def load_druggability(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "candidate",
                "localization",
                "druggability_status",
                "is_membrane",
                "is_secreted",
                "known_compounds_count",
                "max_clinical_trial_phase",
            ]
        )
    df = pd.read_csv(path)
    return pd.DataFrame(
        {
            "candidate": df["Target_Gene"].astype(str),
            "localization": df.get("Subcellular_Location", ""),
            "druggability_status": df.get("Translational_Strategy", ""),
            "is_membrane": df.get("Is_Membrane", False),
            "is_secreted": df.get("Is_Secreted", False),
            "known_compounds_count": df.get("Known_Compounds_Count", np.nan),
            "max_clinical_trial_phase": df.get("Max_Clinical_Trial_Phase", np.nan),
        }
    )


def standardize_entity(df: pd.DataFrame, entity_col: str, entity_type: str) -> pd.DataFrame:
    out = df.copy()
    out = out.rename(columns={entity_col: "candidate"})
    out["candidate"] = out["candidate"].astype(str)
    out["entity_type"] = entity_type
    return out


def build_fingerprint(
    df: pd.DataFrame,
    entity_col: str,
    entity_type: str,
    covariate_flags: pd.DataFrame,
    druggability: pd.DataFrame,
) -> pd.DataFrame:
    fp = standardize_entity(df, entity_col, entity_type)
    fp = add_scores(fp)

    if entity_type == "gene":
        fp = fp.merge(covariate_flags, on="candidate", how="left")
        fp = fp.merge(druggability, on="candidate", how="left")
    else:
        fp["covariate_audit_status"] = "not_applicable"
        fp["covariate_warning_details"] = ""
        fp["druggability_status"] = "not_applicable"
        fp["localization"] = ""
        fp["is_membrane"] = np.nan
        fp["is_secreted"] = np.nan
        fp["known_compounds_count"] = np.nan
        fp["max_clinical_trial_phase"] = np.nan

    fp["covariate_audit_status"] = fp["covariate_audit_status"].fillna("not_audited")
    fp["covariate_warning_details"] = fp["covariate_warning_details"].fillna("")
    fp["is_covariate_warning"] = fp["covariate_audit_status"].astype(str).str.contains("WARNING", case=False, na=False)
    fp = classify_rows(fp, artifact_col="is_covariate_warning")

    score_cols = [
        "therapeutic_like_score",
        "amyloid_selectivity_score",
        "tau_selectivity_score",
        "dual_pathology_lowering_score",
        "broad_shift_score",
    ]
    fp["discovery_sort_score"] = (
        fp["therapeutic_like_score"]
        + fp["amyloid_selectivity_score"].clip(lower=0)
        + fp["tau_selectivity_score"].clip(lower=0)
        - 0.25 * fp["broad_shift_score"]
    )
    fp = fp.sort_values("discovery_sort_score", ascending=False)

    ordered = [
        "entity_type",
        "candidate",
        "pathology_axis_class",
        *DELTA_COLUMNS,
        "tau_lowering_score",
        "amyloid_lowering_score",
        "neuron_preservation_score",
        "gliosis_penalty",
        "broad_shift_score",
        "therapeutic_like_score",
        "amyloid_selectivity_score",
        "tau_selectivity_score",
        "dual_pathology_lowering_score",
        "discovery_sort_score",
        "covariate_audit_status",
        "covariate_warning_details",
        "druggability_status",
        "localization",
        "is_membrane",
        "is_secreted",
        "known_compounds_count",
        "max_clinical_trial_phase",
    ]
    remaining = [c for c in fp.columns if c not in ordered]
    return fp[ordered + remaining]


def write_report(gene_fp: pd.DataFrame, module_fp: pd.DataFrame, out_path: Path) -> None:
    lines: list[str] = []
    lines.append("# Discovery Atlas Pathology-Axis Fingerprints")
    lines.append("")
    lines.append("This report is Phase 1 of the Graph-JEPA Discovery Atlas. It converts existing multi-target counterfactual outputs into continuous pathology-axis scores and conservative categorical labels.")
    lines.append("")
    lines.append("## Score Definitions")
    lines.append("")
    lines.append("- `tau_lowering_score = -AT8_delta`")
    lines.append("- `amyloid_lowering_score = -A_beta_6e10_delta`")
    lines.append("- `neuron_preservation_score = NeuN_delta`")
    lines.append("- `gliosis_penalty = max(GFAP_delta, 0) + max(Iba1_delta, 0)`")
    lines.append("- `therapeutic_like_score = tau_lowering_score + neuron_preservation_score - gliosis_penalty`")
    lines.append("- `amyloid_selectivity_score = amyloid_lowering_score - abs(AT8_delta) - gliosis_penalty`")
    lines.append("- `tau_selectivity_score = tau_lowering_score - abs(A_beta_6e10_delta) - gliosis_penalty`")
    lines.append("")
    lines.append("## Gene Class Counts")
    lines.append("")
    for label, count in gene_fp["pathology_axis_class"].value_counts().items():
        lines.append(f"- `{label}`: {count}")
    lines.append("")
    lines.append("## Module Class Counts")
    lines.append("")
    for label, count in module_fp["pathology_axis_class"].value_counts().items():
        lines.append(f"- `{label}`: {count}")
    lines.append("")
    lines.append("## Top Gene Fingerprints by Discovery Sort Score")
    lines.append("")
    lines.extend(markdown_table(gene_fp.head(12)[["candidate", "pathology_axis_class", "therapeutic_like_score", "amyloid_selectivity_score", "tau_selectivity_score", "gliosis_penalty", "covariate_audit_status"]]))
    lines.append("")
    lines.append("## Top Module Fingerprints by Discovery Sort Score")
    lines.append("")
    lines.extend(markdown_table(module_fp.head(10)[["candidate", "pathology_axis_class", "therapeutic_like_score", "amyloid_selectivity_score", "tau_selectivity_score", "gliosis_penalty"]]))
    lines.append("")
    lines.append("## A Beta Boundary Note")
    lines.append("")
    lines.append("The `A_beta_6e10_delta` and `amyloid_selectivity_score` columns are the first inputs for the planned A beta boundary analysis. They should be treated as model-implied amyloid-associated signals, not plaque-proximal microglial validation. A dedicated A beta boundary module should test whether the signal behaves as a discrete population, continuous donor-level axis, graph-neighborhood signal, or spatial-data-limited boundary case.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("These fingerprints classify model-implied counterfactual readouts. They do not prove biological causality or therapeutic efficacy.")
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
        vals = []
        for col in headers:
            val = row[col]
            if isinstance(val, float):
                vals.append(f"{val:.6g}")
            else:
                vals.append(str(val).replace("|", "\\|"))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Graph-JEPA Discovery Atlas pathology-axis fingerprints.")
    parser.add_argument("--gene-input", default="results/tables/v2_1_multitarget_gene_counterfactual_summary.csv")
    parser.add_argument("--module-input", default="results/tables/v2_1_multitarget_module_counterfactual_summary.csv")
    parser.add_argument("--covariate-audit", default="results/tables/v2_2_target_covariate_audit.csv")
    parser.add_argument("--druggability", default="results/tables/v2_2_druggability_summary.csv")
    parser.add_argument("--gene-out", default="results/tables/discovery_pathology_axis_gene_fingerprints.csv")
    parser.add_argument("--module-out", default="results/tables/discovery_pathology_axis_module_fingerprints.csv")
    parser.add_argument("--scorecard-out", default="results/tables/discovery_candidate_scorecard_v1.csv")
    parser.add_argument("--report-out", default="results/reports/discovery_pathology_axis_fingerprints.md")
    args = parser.parse_args()

    gene_df = safe_read_csv(Path(args.gene_input))
    module_df = safe_read_csv(Path(args.module_input))
    covariate_flags = load_covariate_flags(Path(args.covariate_audit))
    druggability = load_druggability(Path(args.druggability))

    gene_fp = build_fingerprint(gene_df, "perturbation", "gene", covariate_flags, druggability)
    module_fp = build_fingerprint(module_df, "module", "module", covariate_flags, druggability)

    Path(args.gene_out).parent.mkdir(parents=True, exist_ok=True)
    gene_fp.to_csv(args.gene_out, index=False)
    module_fp.to_csv(args.module_out, index=False)

    scorecard_cols = [
        "candidate",
        "pathology_axis_class",
        "AT8_delta",
        "A_beta_6e10_delta",
        "GFAP_delta",
        "Iba1_delta",
        "NeuN_delta",
        "therapeutic_like_score",
        "amyloid_selectivity_score",
        "tau_selectivity_score",
        "broad_shift_score",
        "covariate_audit_status",
        "druggability_status",
        "localization",
        "discovery_sort_score",
    ]
    gene_fp[scorecard_cols].to_csv(args.scorecard_out, index=False)

    write_report(gene_fp, module_fp, Path(args.report_out))

    print("Gene pathology-axis classes:")
    print(gene_fp["pathology_axis_class"].value_counts().to_string())
    print("\nModule pathology-axis classes:")
    print(module_fp["pathology_axis_class"].value_counts().to_string())
    print(f"\nWrote {args.gene_out}")
    print(f"Wrote {args.module_out}")
    print(f"Wrote {args.scorecard_out}")
    print(f"Wrote {args.report_out}")


if __name__ == "__main__":
    main()
