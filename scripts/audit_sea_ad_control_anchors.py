from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


AT8 = "percent AT8 positive area_Grey matter"
ABETA = "percent 6e10 positive area_Grey matter"
GFAP = "percent GFAP positive area_Grey matter"
IBA1 = "percent Iba1 positive area_Grey matter"
NEUN = "percent NeuN positive area_Grey matter"


def normalize_donor_id(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def braak_numeric(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().upper().replace("BRAAK", "").strip()
    roman = {
        "0": 0,
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
        "V": 5,
        "VI": 6,
    }
    return float(roman.get(text, np.nan))


def thal_numeric(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().upper().replace("THAL", "").strip()
    try:
        return float(text)
    except ValueError:
        return np.nan


def adnc_rank(value: object) -> float:
    if pd.isna(value):
        return np.nan
    ranks = {"NOT AD": 0, "LOW": 1, "INTERMEDIATE": 2, "HIGH": 3}
    return float(ranks.get(str(value).strip().upper(), np.nan))


def checked_to_bool(value: object) -> bool:
    return str(value).strip().lower() == "checked"


def safe_quantile_threshold(series: pd.Series, q: float) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return float("nan")
    return float(values.quantile(q))


def build_audit_table(targets: pd.DataFrame, donor_meta: pd.DataFrame, counts: pd.DataFrame) -> pd.DataFrame:
    targets = targets.copy()
    donor_meta = donor_meta.copy()
    counts = counts.copy()
    for df in (targets, donor_meta, counts):
        df["Donor ID"] = normalize_donor_id(df["Donor ID"])

    keep_meta_cols = [
        "Donor ID",
        "Age at Death",
        "Sex",
        "APOE Genotype",
        "Cognitive Status",
        "Last CASI Score",
        "Last MMSE Score",
        "Last MOCA Score",
        "PMI",
        "Brain pH",
        "Overall AD neuropathological Change",
        "Thal",
        "Braak",
        "CERAD score",
        "Overall CAA Score",
        "LATE",
        "RIN",
        "Atherosclerosis",
        "Arteriolosclerosis",
        "Consensus Clinical Dx (choice=Control)",
        "Consensus Clinical Dx (choice=Alzheimers disease)",
        "Consensus Clinical Dx (choice=Alzheimers Possible/ Probable)",
        "Severely Affected Donor",
    ]
    meta = donor_meta[[col for col in keep_meta_cols if col in donor_meta]].copy()
    target_cols = [
        "Donor ID",
        AT8,
        ABETA,
        GFAP,
        IBA1,
        NEUN,
        "guhcl pTau_Grey matter",
        "guhcl abeta42_Grey matter",
        "ripa pTau_Grey matter",
        "ripa abeta42_Grey matter",
    ]
    target = targets[[col for col in target_cols if col in targets]].copy()
    df = meta.merge(target, on="Donor ID", how="outer", suffixes=("", "_target"))
    df = df.merge(counts, on="Donor ID", how="outer")

    df["braak_numeric"] = df["Braak"].map(braak_numeric) if "Braak" in df else np.nan
    df["thal_numeric"] = df["Thal"].map(thal_numeric) if "Thal" in df else np.nan
    df["adnc_rank"] = df["Overall AD neuropathological Change"].map(adnc_rank) if "Overall AD neuropathological Change" in df else np.nan
    if "Consensus Clinical Dx (choice=Control)" in df:
        df["clinical_control_checked"] = df["Consensus Clinical Dx (choice=Control)"].map(checked_to_bool)
    else:
        df["clinical_control_checked"] = df.get("Cognitive Status", pd.Series(index=df.index, dtype=object)).astype(str).str.lower().eq("no dementia")
    df["no_dementia"] = df.get("Cognitive Status", pd.Series(index=df.index, dtype=object)).astype(str).str.lower().eq("no dementia")

    at8_low = safe_quantile_threshold(df[AT8], 0.25) if AT8 in df else np.nan
    abeta_low = safe_quantile_threshold(df[ABETA], 0.25) if ABETA in df else np.nan
    df["low_at8_q25"] = pd.to_numeric(df.get(AT8), errors="coerce") <= at8_low
    df["low_abeta_q25"] = pd.to_numeric(df.get(ABETA), errors="coerce") <= abeta_low
    df["low_braak"] = df["braak_numeric"] <= 2
    df["low_thal"] = df["thal_numeric"] <= 2
    df["not_ad_or_low_adnc"] = df["adnc_rank"] <= 1
    df["sufficient_microglia_cells"] = pd.to_numeric(df.get("microglia_pvm_n_cells"), errors="coerce") >= 200

    df["internal_low_pathology_anchor_relaxed"] = (
        df["not_ad_or_low_adnc"].fillna(False)
        & df["low_abeta_q25"].fillna(False)
        & df["low_at8_q25"].fillna(False)
        & df["no_dementia"].fillna(False)
        & df["sufficient_microglia_cells"].fillna(False)
    )
    df["internal_low_pathology_anchor_strict"] = (
        df["low_braak"].fillna(False)
        & df["low_thal"].fillna(False)
        & df["not_ad_or_low_adnc"].fillna(False)
        & df["low_abeta_q25"].fillna(False)
        & df["low_at8_q25"].fillna(False)
        & df["no_dementia"].fillna(False)
        & df["sufficient_microglia_cells"].fillna(False)
    )
    df.attrs["at8_q25"] = at8_low
    df.attrs["abeta_q25"] = abeta_low
    return df


def summarize_group(df: pd.DataFrame, mask: pd.Series, label: str) -> dict[str, object]:
    sub = df[mask.fillna(False)].copy()
    row: dict[str, object] = {"group": label, "n_donors": int(sub.shape[0])}
    for col in [
        "Age at Death",
        "PMI",
        "Brain pH",
        "RIN",
        "microglia_pvm_n_cells",
        AT8,
        ABETA,
        GFAP,
        IBA1,
        NEUN,
        "braak_numeric",
        "thal_numeric",
        "adnc_rank",
    ]:
        if col in sub:
            values = pd.to_numeric(sub[col], errors="coerce")
            row[f"{col}_mean"] = float(values.mean()) if values.notna().any() else np.nan
            row[f"{col}_median"] = float(values.median()) if values.notna().any() else np.nan
    if "Cognitive Status" in sub:
        row["cognitive_status_counts"] = "; ".join(f"{k}:{v}" for k, v in sub["Cognitive Status"].fillna("NA").value_counts().items())
    if "Overall AD neuropathological Change" in sub:
        row["adnc_counts"] = "; ".join(f"{k}:{v}" for k, v in sub["Overall AD neuropathological Change"].fillna("NA").value_counts().items())
    return row


def write_report(df: pd.DataFrame, summary: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    strict = df[df["internal_low_pathology_anchor_strict"]]
    relaxed = df[df["internal_low_pathology_anchor_relaxed"]]
    display_cols = [
        "group",
        "n_donors",
        "Age at Death_median",
        "PMI_median",
        "RIN_median",
        "microglia_pvm_n_cells_median",
        f"{AT8}_median",
        f"{ABETA}_median",
        "braak_numeric_median",
        "thal_numeric_median",
        "adnc_rank_median",
        "cognitive_status_counts",
        "adnc_counts",
    ]
    display = summary[[col for col in display_cols if col in summary]].copy()
    lines = [
        "# SEA-AD Low-Pathology Anchor Audit",
        "",
        "This audit asks whether SEA-AD already contains enough low-AD-pathology Microglia-PVM donors to serve as an internal v2 homeostatic reference.",
        "",
        "Terminology: these donors are **low-pathology internal reference donors**, not pristine healthy controls. They are aged postmortem donors and may still carry aging, vascular, agonal, PMI, or systemic stress signatures.",
        "",
        "## Thresholds",
        "",
        f"- AT8 q25 threshold: {df.attrs.get('at8_q25', np.nan):.6g}",
        f"- 6e10/A beta q25 threshold: {df.attrs.get('abeta_q25', np.nan):.6g}",
        "- Sufficient Microglia-PVM cells: >= 200",
        "- Relaxed anchor: ADNC Not AD/Low, low AT8, low 6e10, no dementia, sufficient Microglia-PVM cells",
        "- Strict anchor: relaxed anchor plus Braak <= II and Thal <= 2",
        "",
        "## Counts",
        "",
        f"- Total metadata/pathology donors: {df['Donor ID'].nunique()}",
        f"- Relaxed low-pathology anchors: {relaxed.shape[0]}",
        f"- Strict low-pathology anchors: {strict.shape[0]}",
        "",
        "## Group Summary",
        "",
        display.to_string(index=False),
        "",
        "## Recommendation",
        "",
    ]
    if strict.shape[0] >= 20:
        lines.append("SEA-AD has enough strict low-pathology donors for an internal v2 anchor.")
    elif relaxed.shape[0] >= 20:
        lines.append("SEA-AD likely has enough relaxed low-pathology donors for an internal aging/postmortem anchor, but not enough strict donors. Use this as Stage B calibration, not as the only healthy baseline.")
    else:
        lines.append("SEA-AD does not have enough low-pathology donors to serve as the only homeostatic anchor. Use SEA-AD low-pathology donors for matched internal calibration and add external healthy microglia, such as CELLxGENE/Siletti, for broad Stage A pretraining.")
    lines.extend(
        [
            "",
            "Recommended v2 curriculum:",
            "",
            "1. Broad healthy/normal microglia pretraining from external public data.",
            "2. SEA-AD low-pathology internal anchor calibration.",
            "3. SEA-AD disease-deviation fine-tuning.",
            "4. External observational and perturbational validation.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit SEA-AD low-pathology donors as possible internal v2 anchors.")
    parser.add_argument("--targets", default="data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    parser.add_argument("--donor-metadata", default="data/raw/metadata/sea-ad_cohort_donor_metadata_072524.xlsx")
    parser.add_argument("--counts", default="data/processed/sea_ad_mtg_microglia_pvm_counts_expanded_modules.csv")
    parser.add_argument("--out-donors", default="results/tables/sea_ad_low_pathology_anchor_audit_donors.csv")
    parser.add_argument("--out-summary", default="results/tables/sea_ad_low_pathology_anchor_audit_summary.csv")
    parser.add_argument("--out-report", default="results/reports/sea_ad_low_pathology_anchor_audit.md")
    args = parser.parse_args()

    targets = pd.read_csv(args.targets)
    donor_meta = pd.read_excel(args.donor_metadata)
    counts = pd.read_csv(args.counts)
    audit = build_audit_table(targets, donor_meta, counts)
    summary = pd.DataFrame(
        [
            summarize_group(audit, pd.Series(True, index=audit.index), "all_donors"),
            summarize_group(audit, audit["internal_low_pathology_anchor_relaxed"], "relaxed_low_pathology_anchor"),
            summarize_group(audit, audit["internal_low_pathology_anchor_strict"], "strict_low_pathology_anchor"),
            summarize_group(audit, ~audit["internal_low_pathology_anchor_relaxed"].fillna(False), "non_anchor"),
        ]
    )
    Path(args.out_donors).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_report).parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(args.out_donors, index=False)
    summary.to_csv(args.out_summary, index=False)
    write_report(audit, summary, Path(args.out_report))
    print(summary[["group", "n_donors"]].to_string(index=False))
    print(f"AT8 q25 threshold: {audit.attrs.get('at8_q25', np.nan):.6g}")
    print(f"6e10 q25 threshold: {audit.attrs.get('abeta_q25', np.nan):.6g}")
    print(f"Wrote {args.out_donors}")
    print(f"Wrote {args.out_summary}")
    print(f"Wrote {args.out_report}")


if __name__ == "__main__":
    main()
