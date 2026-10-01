#!/usr/bin/env python3
"""V69 Route B step 1: donor-aware fragment QC, computed FROM THE FRAGMENTS.

WHY ROUTE B EXISTS. A prior attempt on this project (Stage75C/F) could not recover
region-to-gene evidence from a PROCESSED peak matrix: every edge carries
edge_atac_peak_support_status = "not_gene_mappable_from_processed_peak_matrix", and
its preflight concluded ready_for_true_scenicplus_egrn = False with
proximity_only_not_regulatory = True. Route B reconstructs the region universe from
raw fragments because of that observed failure, not as a precaution.

WHAT THIS STEP DOES. One streaming pass over the fragment file, emitting per-barcode
fragment statistics restricted to the FROZEN cohort barcodes, plus the donor split
needed for donor-aware pseudobulk peak calling.

TWO FACTS ABOUT THIS DATASET THAT THE CODE MUST RESPECT:

  1. Barcode suffixes are NOT donors. Suffixes 5, 6 and 7 each carry two donors
     (4313+4482; HCT17HEX+HCTZZT; 4305+4443). Donor identity comes ONLY from the
     metadata keyed on the FULL barcode string. Any suffix-based donor inference is
     a defect, and this producer fails closed if asked to do it.

  2. The fragment file's barcode space is LARGER than the filtered cell metadata.
     Fragments carry barcodes that never became called cells. Those are counted and
     discarded explicitly; they are not silently absorbed, and they are not treated
     as cohort cells.

QC THRESHOLDS are the frozen SCENIC+/pycisTopic protocol defaults and are NOT tuned
here. They are applied to statistics computed from the fragments themselves, never to
the depositor's submitted TSS.enrichment / nCount_ATAC columns -- reusing those would
make Route B a relabelling of Route A rather than an independent reconstruction.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import sys
import hashlib
import json
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v69_barcode_identity import (  # noqa: E402
    BarcodeIdentityError, assert_donor_map_is_not_suffix_derived)

import numpy as np
import pandas as pd

# Frozen in V69_GSE214979_ROUTE_AB_PROSPECTIVE_FREEZE_V1, SECTION_2.
MIN_UNIQUE_FRAGMENTS_PER_BARCODE = 1000
MIN_DONORS_FOR_DONOR_STABILITY = 8
# Bound on the retained out-of-cohort barcode set, so memory stays finite on a file
# with billions of records. Reaching it censors the reported count, which the receipt
# must then flag rather than present as a measurement.
OUTSIDE_BARCODE_CAP = 2_000_000


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


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def run(fragments: Path, fragments_receipt: Path, cohort_receipt: Path,
        population: str, out_dir: Path, max_records: int = 0) -> dict:
    acq = json.loads(fragments_receipt.read_text())
    if not str(acq.get("status", "")).startswith("PASS"):
        raise FailClosed("FAIL__FRAGMENTS_ACQUISITION_RECEIPT_IS_NOT_PASS",
                         status=acq.get("status"),
                         note=("Route B must not run on an incompletely downloaded "
                               "63.6 GB fragment file. A truncated file would silently "
                               "produce a biased region universe."))
    observed = fragments.stat().st_size
    if observed != acq.get("local_bytes"):
        raise FailClosed("FAIL__FRAGMENT_FILE_SIZE_CHANGED_SINCE_ACQUISITION",
                         receipt_bytes=acq.get("local_bytes"), observed_bytes=observed)

    coh = json.loads(cohort_receipt.read_text())
    pop = coh["populations"][population]
    bc = pd.read_csv(Path(pop["barcode_file"]))
    barcode_to_donor = dict(zip(bc["barcode"].astype(str), bc["donor"].astype(str)))

    # ENFORCED guard (scripts/v69/v69_barcode_identity.py). A guard recorded in a
    # receipt is documentation; this one lives in the code that reads barcodes and
    # fails closed if the donor mapping is, or is indistinguishable from,
    # suffix-derived.
    try:
        guard_evidence = assert_donor_map_is_not_suffix_derived(barcode_to_donor)
    except BarcodeIdentityError as e:
        raise FailClosed("FAIL__DONOR_IDENTITY_GUARD", reason=str(e))
    multi_donor_suffixes = guard_evidence["suffixes_carrying_more_than_one_donor"]

    out_dir.mkdir(parents=True, exist_ok=True)

    counts = defaultdict(int)          # cohort barcode -> fragment count
    n_records = 0
    n_in_cohort = 0
    n_outside_cohort = 0
    outside_barcodes = set()
    chroms = defaultdict(int)

    with gzip.open(fragments, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 4:
                continue
            n_records += 1
            b = f[3]
            if b in barcode_to_donor:
                counts[b] += 1
                n_in_cohort += 1
                chroms[f[0]] += 1
            else:
                n_outside_cohort += 1
                if len(outside_barcodes) < OUTSIDE_BARCODE_CAP:
                    outside_barcodes.add(b)
            if max_records and n_records >= max_records:
                break

    per_bc = pd.DataFrame({
        "barcode": list(barcode_to_donor.keys()),
    })
    per_bc["donor"] = per_bc["barcode"].map(barcode_to_donor)
    per_bc["n_fragments"] = per_bc["barcode"].map(counts).fillna(0).astype(np.int64)
    per_bc["passes_min_fragments"] = (
        per_bc["n_fragments"] >= MIN_UNIQUE_FRAGMENTS_PER_BARCODE)

    p = out_dir / ("V69_ROUTEB_FRAGMENT_QC_%s.csv.gz" % population)
    per_bc.to_csv(p, index=False, compression="gzip")

    donor_tbl = per_bc.groupby("donor").agg(
        n_cells=("barcode", "size"),
        n_cells_passing=("passes_min_fragments", "sum"),
        total_fragments=("n_fragments", "sum"),
        median_fragments=("n_fragments", "median"),
    ).reset_index()
    donors_passing = int((donor_tbl["n_cells_passing"] > 0).sum())

    partial = bool(max_records)
    return {
        "schema": "V69_ROUTEB_FRAGMENT_QC_V1",
        "run_utc": utcnow(),
        "population": population,
        "PARTIAL_SCAN": partial,
        "partial_scan_note": ("A partial scan is a smoke test only and must never be "
                              "used to build a region universe or to pass QC."
                              if partial else "Full-file scan."),
        "fragments_path": str(fragments),
        "fragments_sha256": acq.get("sha256"),
        "fragments_bytes": observed,
        "records_scanned": n_records,
        "barcode_space": {
            "fragment_records_with_a_cohort_barcode": n_in_cohort,
            "fragment_records_outside_the_cohort": n_outside_cohort,
            "distinct_non_cohort_barcodes_retained": len(outside_barcodes),
            "distinct_non_cohort_barcode_cap": OUTSIDE_BARCODE_CAP,
            "distinct_non_cohort_barcode_count_is_censored": bool(
                len(outside_barcodes) >= OUTSIDE_BARCODE_CAP),
            "censoring_note": ("The set of out-of-cohort barcodes is bounded to keep "
                               "memory finite. If the cap was reached this is a LOWER "
                               "BOUND, not a count, and must never be cited as the "
                               "number of distinct non-cohort barcodes."),
            "semantics": ("Fragments outside the frozen cohort are COUNTED and "
                          "DISCARDED. They are neither silently absorbed nor treated "
                          "as cohort cells. The fragment file's barcode space is "
                          "larger than the filtered cell metadata."),
        },
        "donor_identity_guard": guard_evidence,
        "qc_thresholds": {
            "min_unique_fragments_per_barcode": MIN_UNIQUE_FRAGMENTS_PER_BARCODE,
            "source": "SCENIC+/pycisTopic protocol default, frozen in "
                      "V69_GSE214979_ROUTE_AB_PROSPECTIVE_FREEZE_V1 SECTION_2, not tuned here.",
            "computed_from": "THE FRAGMENTS, not the depositor's submitted QC columns.",
            "still_to_apply": ["TSS enrichment >= 4.0 (needs a SHA-pinned GRCh38 TSS "
                               "annotation, recorded as UNACQUIRED)",
                               "FRiP >= 0.4 against the Route-B consensus peaks "
                               "(computable only after those peaks exist)"],
        },
        "per_barcode_table": {"path": str(p), "sha256": sha256_file(p)},
        "cells": {
            "n_cohort_cells": int(len(per_bc)),
            "n_passing_min_fragments": int(per_bc["passes_min_fragments"].sum()),
            "fragments_per_cell": {
                "min": int(per_bc["n_fragments"].min()),
                "median": float(per_bc["n_fragments"].median()),
                "max": int(per_bc["n_fragments"].max()),
            },
        },
        "donors": {
            "n_donors": int(len(donor_tbl)),
            "n_donors_with_at_least_one_passing_cell": donors_passing,
            "min_donors_for_donor_stability": MIN_DONORS_FOR_DONOR_STABILITY,
            "substrate_sufficient_for_donor_stability":
                bool(donors_passing >= MIN_DONORS_FOR_DONOR_STABILITY) if not partial
                else "UNDETERMINED_PARTIAL_SCAN",
            "per_donor": donor_tbl.to_dict(orient="records"),
        },
        "chromosome_distribution_of_cohort_fragments": dict(
            sorted(chroms.items(), key=lambda kv: -kv[1])[:30]),
        "status": ("PASS__PARTIAL_SMOKE_SCAN" if partial
                   else "PASS__ROUTEB_FRAGMENT_QC_COMPLETE"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragments", required=True)
    ap.add_argument("--fragments-receipt", required=True)
    ap.add_argument("--cohort-receipt", required=True)
    ap.add_argument("--population", default="DEV_NO_MORABITO_OVERLAP")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--max-records", type=int, default=0,
                    help="Smoke-test only. A partial scan can never pass QC.")
    a = ap.parse_args(argv)
    try:
        r = run(Path(a.fragments), Path(a.fragments_receipt), Path(a.cohort_receipt),
                a.population, Path(a.out_dir), a.max_records)
    except FailClosed as e:
        r = {"schema": "V69_ROUTEB_FRAGMENT_QC_V1", "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({k: v for k, v in r.items() if k != "donors"}, indent=2)[:4000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
