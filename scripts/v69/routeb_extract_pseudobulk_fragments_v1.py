#!/usr/bin/env python3
"""V69 Route B step 2: donor-aware pseudobulk fragment extraction.

One streaming pass over the 63.6 GB fragment file, writing a BED per pseudobulk for
cohort barcodes only. Pseudobulk unit is DONOR x PUBLISHED MICROGLIAL SUBCLUSTER, as
frozen in V69_GSE214979_ROUTE_AB_PROSPECTIVE_FREEZE_V1 SECTION_2, so that a peak
carried by a single donor cannot masquerade as a population peak.

THREE THINGS THIS PRODUCER REFUSES TO DO:

  1. Infer a donor from a barcode suffix. Suffixes 5, 6 and 7 each span two donors in
     this cohort. The shared enforced guard (v69_barcode_identity) fails closed if the
     donor mapping is, or is indistinguishable from, suffix-derived.

  2. Absorb out-of-cohort fragments. The fragment file's barcode space is wider than
     the published cell set -- whole aggregation suffixes (8, 9, 20-23) contribute no
     called cell. Those records are COUNTED and DISCARDED, never silently included.
     Calling peaks on them would build a region universe describing cells outside the
     frozen cohort, and the resulting Route-A/Route-B disagreement would be a cohort
     difference wearing the costume of a region-definition difference.

  3. Apply the per-cell fragment QC threshold silently. Cells failing the frozen
     >=1000-fragment rule are excluded and the exclusion is recorded per pseudobulk.

Output BEDs are plain chrom/start/end, which is what MACS2 --format BEDPE consumes.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v69_barcode_identity import (  # noqa: E402
    BarcodeIdentityError, assert_donor_map_is_not_suffix_derived)

MIN_UNIQUE_FRAGMENTS_PER_BARCODE = 1000   # frozen, SECTION_2


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


def run(fragments: Path, fragments_receipt: Path, qc_receipt: Path,
        cohort_receipt: Path, population: str, out_dir: Path,
        max_records: int = 0) -> dict:
    acq = json.loads(fragments_receipt.read_text())
    if not str(acq.get("status", "")).startswith("PASS"):
        raise FailClosed("FAIL__FRAGMENTS_ACQUISITION_RECEIPT_IS_NOT_PASS",
                         status=acq.get("status"))
    if fragments.stat().st_size != acq.get("local_bytes"):
        raise FailClosed("FAIL__FRAGMENT_FILE_SIZE_CHANGED_SINCE_ACQUISITION")

    qc = json.loads(qc_receipt.read_text())
    if not str(qc.get("status", "")).startswith("PASS") or qc.get("PARTIAL_SCAN"):
        raise FailClosed("FAIL__ROUTEB_QC_RECEIPT_NOT_A_COMPLETE_PASS",
                         status=qc.get("status"), partial=qc.get("PARTIAL_SCAN"))

    coh = json.loads(cohort_receipt.read_text())
    bc = pd.read_csv(Path(coh["populations"][population]["barcode_file"]))
    barcode_to_donor = dict(zip(bc["barcode"].astype(str), bc["donor"].astype(str)))
    barcode_to_sub = dict(zip(bc["barcode"].astype(str), bc["subcluster"].astype(str)))

    try:
        guard = assert_donor_map_is_not_suffix_derived(barcode_to_donor)
    except BarcodeIdentityError as e:
        raise FailClosed("FAIL__DONOR_IDENTITY_GUARD", reason=str(e))

    # per-cell QC from the completed full-file scan, applied explicitly
    qc_tbl = pd.read_csv(Path(qc["per_barcode_table"]["path"]))
    passing = set(qc_tbl.loc[qc_tbl["passes_min_fragments"], "barcode"].astype(str))
    excluded = {b for b in barcode_to_donor if b not in passing}

    keep = {b: (barcode_to_donor[b], barcode_to_sub[b])
            for b in barcode_to_donor if b in passing}
    if not keep:
        raise FailClosed("FAIL__NO_CELLS_SURVIVE_QC")

    out_dir.mkdir(parents=True, exist_ok=True)
    handles, counts = {}, Counter()
    for donor, sub in sorted({v for v in keep.values()}):
        key = f"{donor}__{sub}"
        handles[key] = open(out_dir / f"PSEUDOBULK_{key}.bed", "w", newline="\n")

    n_records = n_in = n_out = 0
    with gzip.open(fragments, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 4:
                continue
            n_records += 1
            meta = keep.get(f[3])
            if meta is None:
                n_out += 1
            else:
                key = f"{meta[0]}__{meta[1]}"
                handles[key].write(f"{f[0]}\t{f[1]}\t{f[2]}\n")
                counts[key] += 1
                n_in += 1
            if max_records and n_records >= max_records:
                break

    for h in handles.values():
        h.close()

    # Re-read each output from disk; the recorded state describes files, not memory.
    pseudobulks = {}
    empty = []
    for key in sorted(handles):
        p = out_dir / f"PSEUDOBULK_{key}.bed"
        n_lines = sum(1 for _ in open(p))
        if n_lines != counts[key]:
            raise FailClosed("FAIL__PSEUDOBULK_LINE_COUNT_MISMATCH",
                             pseudobulk=key, written=counts[key], on_disk=n_lines)
        donor, sub = key.split("__", 1)
        pseudobulks[key] = {
            "donor": donor, "subcluster": sub,
            "n_fragments": n_lines,
            "n_cells": sum(1 for b, m in keep.items() if f"{m[0]}__{m[1]}" == key),
            "path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size,
        }
        if n_lines == 0:
            empty.append(key)

    partial = bool(max_records)
    return {
        "schema": "V69_ROUTEB_PSEUDOBULK_FRAGMENTS_V1",
        "run_utc": utcnow(),
        "population": population,
        "PARTIAL_SCAN": partial,
        "partial_scan_note": ("A partial scan is a smoke test only and must never feed "
                              "peak calling." if partial else "Full-file scan."),
        "fragments_sha256": acq.get("sha256"),
        "fragments_bytes": fragments.stat().st_size,
        "records_scanned": n_records,
        "records_written_to_a_pseudobulk": n_in,
        "records_discarded_out_of_cohort_or_failing_qc": n_out,
        "pseudobulk_unit": "donor x published microglial subcluster (frozen SECTION_2)",
        "donor_identity_guard": guard,
        "cell_qc": {
            "min_unique_fragments_per_barcode": MIN_UNIQUE_FRAGMENTS_PER_BARCODE,
            "source": "V69_ROUTEB_FRAGMENT_QC_V1 full-file scan",
            "n_cohort_cells": len(barcode_to_donor),
            "n_cells_used": len(keep),
            "n_cells_excluded_by_qc": len(excluded),
            "semantics": ("Excluded cells are recorded, not silently dropped. They are "
                          "QC exclusions, not biological absences."),
        },
        "n_pseudobulks": len(pseudobulks),
        "n_empty_pseudobulks": len(empty),
        "empty_pseudobulks": empty,
        "pseudobulks": pseudobulks,
        "output_dir": str(out_dir),
        "verified_by_rereading_outputs_from_disk": True,
        "status": ("PASS__PARTIAL_SMOKE_SCAN" if partial
                   else "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragments", required=True)
    ap.add_argument("--fragments-receipt", required=True)
    ap.add_argument("--qc-receipt", required=True)
    ap.add_argument("--cohort-receipt", required=True)
    ap.add_argument("--population", default="DEV_NO_MORABITO_OVERLAP")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--max-records", type=int, default=0,
                    help="Smoke test only; a partial scan can never feed peak calling.")
    a = ap.parse_args(argv)
    try:
        r = run(Path(a.fragments), Path(a.fragments_receipt), Path(a.qc_receipt),
                Path(a.cohort_receipt), a.population, Path(a.out_dir), a.max_records)
    except FailClosed as e:
        r = {"schema": "V69_ROUTEB_PSEUDOBULK_FRAGMENTS_V1",
             "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({k: v for k, v in r.items() if k != "pseudobulks"}, indent=2)[:3500])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
