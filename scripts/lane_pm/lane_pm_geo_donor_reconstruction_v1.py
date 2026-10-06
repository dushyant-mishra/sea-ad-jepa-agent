#!/usr/bin/env python
"""Lane PM: reconstruct DONOR identity from GEO GSM records for GSE272082.

GEO deposits a library per row; it does NOT deposit an explicit donor key for
GSE272082. Library names (NIH01, NIH02, ...) look like donor names and are not:
several libraries are different brain regions of ONE person. The independent
unit is the person, so this script reconstructs donors by grouping libraries on
the invariant donor attributes the deposit does record -- (Sex, age at death,
post-mortem interval) -- and reports the grouping as an INFERENCE, flagged as
such, never as a stated fact.

It also cross-checks the two places the deposit states disease state (the sample
TITLE and the sample CHARACTERISTICS) and reports any disagreement rather than
silently preferring one.

Usage:
    python scripts/lane_pm/lane_pm_geo_donor_reconstruction_v1.py \
        --gsm-text <GSE272082_gsm_full.txt> --out-dir <results/lane_pm>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

NOT_STATED = "NOT_STATED_IN_DEPOSIT"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_gsm_records(text: str) -> list[dict]:
    """Parse GEO `targ=gsm&form=text` output into one dict per sample.

    Characteristics are matched by the VALUE BEING BOUND (the key name to the
    left of the first colon), not by one hard-coded spelling of a line, so a
    deposit that writes 'age' or 'age on_death' is handled identically.
    """
    records: list[dict] = []
    cur: dict | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("^SAMPLE"):
            if cur:
                records.append(cur)
            cur = {"gsm": line.split("=", 1)[1].strip(), "characteristics": {}}
            continue
        if cur is None or not line.startswith("!Sample_"):
            continue
        key, _, val = line[len("!Sample_"):].partition("=")
        key, val = key.strip(), val.strip()
        if key == "characteristics_ch1":
            ck, _, cv = val.partition(":")
            cur["characteristics"][ck.strip().lower()] = cv.strip()
        elif key in ("title", "source_name_ch1", "library_strategy", "platform_id"):
            cur[key] = val
    if cur:
        records.append(cur)
    return records


def char_lookup(chars: dict, *candidates: str) -> str:
    """Find a characteristic by any of several key spellings; NOT_STATED if absent."""
    for cand in candidates:
        for k, v in chars.items():
            if cand in k:
                return v
    return NOT_STATED


def build_frame(records: list[dict]) -> pd.DataFrame:
    rows = []
    for r in records:
        title = r.get("title", "")
        chars = r["characteristics"]
        library = title.split(",")[0].strip()
        title_disease = NOT_STATED
        m = re.search(r",\s*(sEOAD|control|AD|Ctrl)\s*,", title, flags=re.I)
        if m:
            title_disease = m.group(1)
        rows.append(
            {
                "gsm": r["gsm"],
                "library": library,
                "assay": r.get("library_strategy", NOT_STATED),
                "region": r.get("source_name_ch1", NOT_STATED),
                "disease_state_from_characteristics": char_lookup(chars, "disease"),
                "disease_state_from_title": title_disease,
                "sex": char_lookup(chars, "sex"),
                "age_at_death": char_lookup(chars, "age"),
                "pmi_hours": char_lookup(chars, "pmi"),
            }
        )
    return pd.DataFrame(rows)


def reconstruct_donors(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Group libraries into donors on invariant person-level attributes."""
    key_cols = ["sex", "age_at_death", "pmi_hours", "disease_state_from_characteristics"]
    df = df.copy()
    df["donor_key"] = df[key_cols].astype(str).agg("|".join, axis=1)

    # One row per (donor, library) -- collapse the GEX/ATAC pair of each library.
    per_lib = (
        df.groupby(["donor_key", "library"], as_index=False)
        .agg(
            region=("region", "first"),
            assays=("assay", lambda s: "+".join(sorted(set(s)))),
            n_gsm=("gsm", "nunique"),
            sex=("sex", "first"),
            age_at_death=("age_at_death", "first"),
            pmi_hours=("pmi_hours", "first"),
            disease_state=("disease_state_from_characteristics", "first"),
        )
    )

    donors = (
        per_lib.groupby("donor_key", as_index=False)
        .agg(
            n_region_samples=("library", "nunique"),
            libraries=("library", lambda s: ",".join(sorted(s))),
            regions=("region", lambda s: ",".join(sorted(set(s)))),
            sex=("sex", "first"),
            age_at_death=("age_at_death", "first"),
            pmi_hours=("pmi_hours", "first"),
            disease_state=("disease_state", "first"),
        )
        .sort_values(["disease_state", "libraries"])
        .reset_index(drop=True)
    )
    donors.insert(0, "donor_index", range(1, len(donors) + 1))
    return donors, per_lib


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gsm-text", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--label", default="GSE272082")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    src_sha = sha256_file(args.gsm_text)
    records = parse_gsm_records(args.gsm_text.read_text(encoding="utf-8", errors="replace"))
    df = build_frame(records)
    donors, per_lib = reconstruct_donors(df)

    # Disease-label disagreement between the two places GEO states it.
    def norm(x: str) -> str:
        x = str(x).strip().lower()
        return {"ctrl": "control"}.get(x, x)

    conflicts = df[
        (df["disease_state_from_title"] != NOT_STATED)
        & (df["disease_state_from_title"].map(norm) != df["disease_state_from_characteristics"].map(norm))
    ][["gsm", "library", "disease_state_from_title", "disease_state_from_characteristics"]]

    df.to_csv(args.out_dir / f"lane_pm_{args.label.lower()}_sample_table_v1.csv", index=False)
    donors.to_csv(args.out_dir / f"lane_pm_{args.label.lower()}_donor_reconstruction_v1.csv", index=False)
    conflicts.to_csv(args.out_dir / f"lane_pm_{args.label.lower()}_label_conflicts_v1.csv", index=False)

    report = {
        "series": args.label,
        "source_file": args.gsm_text.name,
        "source_sha256": src_sha,
        "n_gsm_records": int(len(df)),
        "n_libraries": int(df["library"].nunique()),
        "n_donors_reconstructed": int(len(donors)),
        "donor_reconstruction_method": (
            "INFERRED by grouping libraries on (sex, age at death, PMI, disease "
            "state). GEO does not deposit an explicit donor key for this series; "
            "the grouping is an inference, not a deposited fact."
        ),
        "region_sample_counts": df.drop_duplicates("library")["region"].value_counts().to_dict(),
        "donors_per_group": donors["disease_state"].value_counts().to_dict(),
        "n_disease_label_conflicts": int(len(conflicts)),
        "disease_label_conflicts": conflicts.to_dict(orient="records"),
        "microglia_counts": NOT_STATED,
        "microglia_counts_note": (
            "No cell-type annotation, cell metadata, or per-cell-type count is "
            "deposited for this series, and the publication does not break "
            "microglia down per donor or per region. Not estimated."
        ),
        "effective_independent_n": int(len(donors)),
        "effective_n_note": (
            "Region samples from one person are NOT independent units. The "
            "independent n is the donor count, not the region-sample count."
        ),
    }
    (args.out_dir / f"lane_pm_{args.label.lower()}_donor_report_v1.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
