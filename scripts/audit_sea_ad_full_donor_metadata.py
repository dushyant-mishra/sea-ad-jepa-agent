from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sea_ad_jepa.data import normalize_donor_id


DEFAULT_METADATA = Path("data/raw/metadata/sea-ad_cohort_donor_metadata_072524.xlsx")
DEFAULT_TARGETS = Path("data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
DEFAULT_OUT_TABLE = Path("results/tables/sea_ad_full_metadata_covariate_audit.csv")
DEFAULT_OUT_JOINED = Path("results/tables/sea_ad_full_metadata_targets_with_covariates.csv")
DEFAULT_OUT_REPORT = Path("results/reports/sea_ad_full_metadata_covariate_audit.md")


COVARIATE_PATTERNS = {
    "postmortem_interval": ["pmi", "postmortem", "post mortem"],
    "rna_quality": ["rin", "rna integrity", "rna quality"],
    "tissue_quality": ["brain ph", "ph", "rapid frozen", "fresh brain weight"],
    "technical_batch": ["batch", "library", "chemistry", "assay", "prep", "sequencing"],
    "demographic": ["age", "sex", "race", "hispanic", "education"],
    "genetic": ["apoe"],
    "clinical_cognitive": ["cognitive", "casi", "mmse", "moca", "dementia", "clinical"],
    "neuropathology": ["braak", "thal", "cerad", "ad neuropath", "caa", "lewy", "late", "microinfarct"],
}


def column_bucket(column: str) -> str | None:
    lower = column.lower()
    for bucket, patterns in COVARIATE_PATTERNS.items():
        if any(pattern in lower for pattern in patterns):
            return bucket
    return None


def summarize_column(df: pd.DataFrame, sheet: str, column: str) -> dict[str, object]:
    series = df[column]
    non_null = int(series.notna().sum())
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_non_null = int(numeric.notna().sum())
    row: dict[str, object] = {
        "sheet": sheet,
        "column": column,
        "bucket": column_bucket(column) or "other",
        "n_rows": int(len(df)),
        "n_non_null": non_null,
        "missing_fraction": float(1.0 - non_null / max(len(df), 1)),
        "n_unique": int(series.nunique(dropna=True)),
        "numeric_non_null": numeric_non_null,
        "is_numeric_like": bool(numeric_non_null >= max(3, int(0.5 * non_null))) if non_null else False,
    }
    if row["is_numeric_like"]:
        row.update(
            {
                "numeric_min": float(numeric.min()),
                "numeric_median": float(numeric.median()),
                "numeric_max": float(numeric.max()),
            }
        )
    else:
        examples = series.dropna().astype(str).unique()[:8]
        row["example_values"] = "; ".join(examples)
    return row


def write_report(
    report_path: Path,
    audit: pd.DataFrame,
    joined: pd.DataFrame | None,
    metadata_path: Path,
    targets_path: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# SEA-AD Full Donor Metadata Covariate Audit",
        "",
        "This audit checks whether the local SEA-AD donor workbook contains the covariates needed to harden v2.1 target validation.",
        "",
        f"Metadata workbook: `{metadata_path}`",
        f"Joined target table: `{targets_path}`",
        "",
        "## Covariate Fields Found",
        "",
    ]

    priority_buckets = [
        "postmortem_interval",
        "rna_quality",
        "tissue_quality",
        "technical_batch",
        "demographic",
        "genetic",
        "clinical_cognitive",
        "neuropathology",
    ]
    for bucket in priority_buckets:
        subset = audit[audit["bucket"] == bucket].copy()
        if subset.empty:
            lines.append(f"- `{bucket}`: none found")
            continue
        cols = ", ".join(f"`{c}`" for c in subset["column"].tolist())
        lines.append(f"- `{bucket}`: {cols}")

    lines.extend(["", "## Join Check", ""])
    if joined is None:
        lines.append("No target table join was produced because the target table was unavailable or missing `Donor ID`.")
    else:
        lines.append(f"- joined donor rows: `{len(joined)}`")
        key_cols = [c for c in ["PMI", "RIN", "Brain pH", "Braak", "Thal", "APOE Genotype", "Cognitive Status"] if c in joined.columns]
        for col in key_cols:
            lines.append(f"- `{col}` non-null rows: `{int(joined[col].notna().sum())}`")

    lines.extend(
        [
            "",
            "## Next Use",
            "",
            "Use `results/tables/sea_ad_full_metadata_targets_with_covariates.csv` as the covariate-enriched donor table for rerunning the v2.1 target validation.",
            "",
            "Important interpretation boundary: PMI, RIN, and brain pH are covariates for artifact control. They are not disease targets.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit SEA-AD donor metadata for covariates needed by v2.1 validation.")
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA), help="SEA-AD donor metadata workbook.")
    parser.add_argument("--targets", default=str(DEFAULT_TARGETS), help="Existing joined donor pathology target CSV.")
    parser.add_argument("--out-table", default=str(DEFAULT_OUT_TABLE), help="Output covariate audit CSV.")
    parser.add_argument("--out-joined", default=str(DEFAULT_OUT_JOINED), help="Output target table joined with full covariates.")
    parser.add_argument("--out-report", default=str(DEFAULT_OUT_REPORT), help="Output Markdown audit report.")
    args = parser.parse_args()

    metadata_path = Path(args.metadata)
    targets_path = Path(args.targets)
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing donor metadata workbook: {metadata_path}. "
            "Run scripts/download_metadata.ps1 or download the donor metadata workbook from the SEA-AD data page."
        )

    xl = pd.ExcelFile(metadata_path)
    audit_rows: list[dict[str, object]] = []
    metadata_frames: list[pd.DataFrame] = []
    for sheet in xl.sheet_names:
        df = pd.read_excel(metadata_path, sheet_name=sheet)
        metadata_frames.append(df.assign(__sheet=sheet))
        for column in df.columns:
            audit_rows.append(summarize_column(df, sheet, str(column)))

    audit = pd.DataFrame(audit_rows).sort_values(["bucket", "sheet", "column"])
    out_table = Path(args.out_table)
    out_table.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(out_table, index=False)

    joined = None
    donor_meta = metadata_frames[0].copy()
    if "Donor ID" in donor_meta.columns and targets_path.exists():
        targets = pd.read_csv(targets_path)
        if "Donor ID" in targets.columns:
            donor_meta["Donor ID"] = normalize_donor_id(donor_meta["Donor ID"])
            targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
            extra_cols = [c for c in donor_meta.columns if c not in targets.columns or c == "Donor ID"]
            joined = targets.merge(donor_meta[extra_cols], on="Donor ID", how="left")
            out_joined = Path(args.out_joined)
            out_joined.parent.mkdir(parents=True, exist_ok=True)
            joined.to_csv(out_joined, index=False)

    write_report(Path(args.out_report), audit, joined, metadata_path, targets_path)
    print(f"Wrote {out_table}")
    if joined is not None:
        print(f"Wrote {args.out_joined}")
    print(f"Wrote {args.out_report}")


if __name__ == "__main__":
    main()
