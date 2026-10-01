#!/usr/bin/env python3
"""V69: audit GSE214979 cell metadata and freeze the microglial development cohort.

PATHOLOGY-BLIND CONSTRUCTION
----------------------------
Columns carrying diagnosis/pathology/disease state are enumerated by NAME into a
forbidden list and are never read into any selection, ordering or thresholding
decision. The audit reports that the forbidden columns exist and reports nothing
about their values beyond their column names.

Two populations are frozen:
  (a) ALL_MICROGLIA                      -- every published-annotation microglial nucleus
  (b) DEV_NO_MORABITO_OVERLAP (default)  -- (a) minus prospectively excluded donors

Donor exclusion {1224, 1230, 1238} is recorded as CONSERVATIVE_PROSPECTIVE. This
script VERIFIES one structural fact about that set (whether it coincides with a
single source repository) and explicitly does NOT claim verified individual-level
overlap with Morabito GSE174367, which deposits pseudonymous Sample-NN identifiers.

Barcode membership is pinned by an ORDERED content digest, not by set membership,
because every downstream matrix indexes cells positionally.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

# Columns that may never influence selection. Enumerated by NAME only.
FORBIDDEN_PATTERN = re.compile(
    r"(diagn|patholog|braak|cerad|disease|status|apoe|plaque|tangle|amyloid|tau)", re.I
)
# Published cell-type annotation column and the microglial label.
CELLTYPE_COLUMN = "predicted.id"
MICROGLIA_LABEL = "Microglia"
SUBCLUSTER_COLUMN = "subs"
MICROGLIA_SUBCLUSTER_PREFIX = "Mic_"
DONOR_COLUMN = "id"
BARCODE_COLUMN = "Unnamed: 0"
EXCLUDED_DONORS = ("1224", "1230", "1238")


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ordered_digest(items) -> str:
    """Digest that is sensitive to ORDER, so a reordered dictionary cannot pass."""
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode())
        h.update(b"\x1f")
        h.update(str(s).encode())
        h.update(b"\x1e")
    return h.hexdigest()


def audit(meta_path: Path, out_dir: Path) -> dict:
    df = pd.read_csv(meta_path, compression="gzip", low_memory=False)
    forbidden = sorted(c for c in df.columns if FORBIDDEN_PATTERN.search(c))

    missing = [c for c in (CELLTYPE_COLUMN, SUBCLUSTER_COLUMN, DONOR_COLUMN, BARCODE_COLUMN)
               if c not in df.columns]
    if missing:
        return {"schema": "V69_GSE214979_COHORT_FREEZE_V1",
                "status": "FAIL__DECLARED_COLUMNS_ABSENT", "missing_columns": missing,
                "observed_columns": list(df.columns)}

    barcodes = df[BARCODE_COLUMN].astype(str)
    if barcodes.duplicated().any():
        return {"schema": "V69_GSE214979_COHORT_FREEZE_V1",
                "status": "FAIL__DUPLICATE_BARCODES_IN_METADATA",
                "n_duplicated": int(barcodes.duplicated().sum())}

    celltype = df[CELLTYPE_COLUMN].astype(str)
    subs = df[SUBCLUSTER_COLUMN].astype(str)
    donor = df[DONOR_COLUMN].astype(str)

    # Cross-check: the coarse published label and the published subcluster prefix
    # must agree exactly, otherwise the "published annotation" is ambiguous.
    by_label = celltype.eq(MICROGLIA_LABEL)
    by_subcluster = subs.str.startswith(MICROGLIA_SUBCLUSTER_PREFIX)
    annotation_concordant = bool(by_label.equals(by_subcluster))
    if not annotation_concordant:
        return {"schema": "V69_GSE214979_COHORT_FREEZE_V1",
                "status": "FAIL__PUBLISHED_MICROGLIA_ANNOTATION_AMBIGUOUS",
                "n_label_only": int((by_label & ~by_subcluster).sum()),
                "n_subcluster_only": int((~by_label & by_subcluster).sum())}

    micro = by_label.to_numpy()
    excl = donor.isin(EXCLUDED_DONORS).to_numpy()
    dev = micro & ~excl

    # Structural verification of the exclusion set: does it coincide with one repository?
    repo_col = "Repository" if "Repository" in df.columns else None
    exclusion_structural_basis = {"verified_claim": None, "evidence": None}
    if repo_col:
        repo_of_excluded = sorted(set(df.loc[donor.isin(EXCLUDED_DONORS), repo_col].astype(str)))
        donors_in_those_repos = sorted(set(
            donor[df[repo_col].astype(str).isin(repo_of_excluded)]))
        coincides = sorted(EXCLUDED_DONORS) == donors_in_those_repos
        exclusion_structural_basis = {
            "verified_claim": (
                "EXCLUSION_SET_EQUALS_SINGLE_SOURCE_REPOSITORY" if coincides
                else "EXCLUSION_SET_DOES_NOT_EQUAL_A_SINGLE_SOURCE_REPOSITORY"),
            "evidence": {
                "repository_values_of_excluded_donors": repo_of_excluded,
                "all_donors_in_those_repositories": donors_in_those_repos,
                "sets_coincide": bool(coincides),
            },
        }

    def pop(mask, name):
        sel = df.loc[mask]
        bc = sel[BARCODE_COLUMN].astype(str).tolist()
        per_donor = sel[DONOR_COLUMN].astype(str).value_counts().sort_index().to_dict()
        p = out_dir / ("GSE214979_" + name + "_barcodes.csv")
        pd.DataFrame({"row_index": range(len(bc)),
                      "barcode": bc,
                      "donor": sel[DONOR_COLUMN].astype(str).tolist(),
                      "subcluster": sel[SUBCLUSTER_COLUMN].astype(str).tolist()}
                     ).to_csv(p, index=False)
        return {
            "population_id": name,
            "n_cells": int(mask.sum()),
            "n_donors": int(sel[DONOR_COLUMN].nunique()),
            "cells_per_donor": {k: int(v) for k, v in per_donor.items()},
            "barcode_file": str(p),
            "barcode_file_sha256": sha256_file(p),
            "ordered_barcode_digest": ordered_digest(bc),
            "unordered_barcode_digest": ordered_digest(sorted(bc)),
            "subcluster_counts": {k: int(v) for k, v in
                                  sel[SUBCLUSTER_COLUMN].astype(str).value_counts()
                                  .sort_index().items()},
        }

    out_dir.mkdir(parents=True, exist_ok=True)
    pop_all = pop(micro, "ALL_MICROGLIA")
    pop_dev = pop(dev, "DEV_NO_MORABITO_OVERLAP")

    receipt = {
        "schema": "V69_GSE214979_COHORT_FREEZE_V1",
        "frozen_utc": utcnow(),
        "source_metadata_path": str(meta_path),
        "source_metadata_sha256": sha256_file(meta_path),
        "metadata_rows": int(len(df)),
        "metadata_columns": list(df.columns),
        "selection_authority": {
            "celltype_column": CELLTYPE_COLUMN,
            "microglia_label": MICROGLIA_LABEL,
            "subcluster_column": SUBCLUSTER_COLUMN,
            "subcluster_prefix": MICROGLIA_SUBCLUSTER_PREFIX,
            "annotation_concordance": "EXACT_AGREEMENT_BETWEEN_LABEL_AND_SUBCLUSTER_PREFIX",
            "donor_column": DONOR_COLUMN,
            "barcode_column": BARCODE_COLUMN,
        },
        "pathology_blindness": {
            "forbidden_columns_enumerated_by_name_only": forbidden,
            "forbidden_columns_read_into_selection": False,
            "note": ("These column names are recorded so an auditor can confirm they "
                     "exist and were available; no value from them enters any mask, "
                     "threshold, ordering or parameter in this producer."),
        },
        "donor_census": {
            "n_donors_total": int(donor.nunique()),
            "cells_per_donor": {k: int(v) for k, v in
                                donor.value_counts().sort_index().items()},
        },
        "prospective_donor_exclusion": {
            "excluded_donors": sorted(EXCLUDED_DONORS),
            "all_present_in_this_cohort": sorted(
                d for d in EXCLUDED_DONORS if d in set(donor)),
            "status": "CONSERVATIVE_PROSPECTIVE__INDIVIDUAL_OVERLAP_NOT_VERIFIED",
            "structural_basis": exclusion_structural_basis,
            "why_not_verified": (
                "Morabito GSE174367 deposits pseudonymous Sample-NN donor identifiers. "
                "No shared stable identifier layer (BioSample, SRA/GSM, biospecimen or "
                "genotype key) linking GSE214979 numeric donor ids to Morabito Sample-NN "
                "was resolved in this lane, so individual-level overlap is UNVERIFIED in "
                "both directions. The exclusion is retained as the conservative choice."),
            "prior_repository_authority":
                "docs/agent/V58_REGULATORY_INDEPENDENCE_HANDOFF_20260928.md records "
                "UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP for GSE214979 vs Morabito.",
        },
        "populations": {"ALL_MICROGLIA": pop_all,
                        "DEV_NO_MORABITO_OVERLAP": pop_dev},
        "default_development_population": "DEV_NO_MORABITO_OVERLAP",
        "substrate_scale_warning": (
            "The microglial substrate is small: see populations[*].n_cells. Donors, not "
            "nuclei, are the replication unit; nuclei improve per-donor measurement "
            "precision and never increase biological n."),
        "status": "PASS__COHORT_FROZEN_PATHOLOGY_BLIND",
    }
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    r = audit(Path(a.metadata), Path(a.out_dir))
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2)[:6000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
