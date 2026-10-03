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

================================  V74 CUSTODY REPAIR  ================================

Four custody defects in the V69 form of this producer are closed here. Each was a way
for a wrong input to produce a normal-looking output.

  C1. SIZE WAS CHECKED, IDENTITY WAS NOT. The producer compared the fragment file's
      byte LENGTH to the acquisition receipt and then copied the receipt's SHA-256 into
      its own receipt, so the receipt asserted a digest nothing had verified. The file
      is now digested AS IT IS READ (v69_custody.HashingReader) and the run fails closed
      at end of stream unless the digest equals the authenticated b7c5aa2d... value.
      Outputs are staged and promoted only after that comparison, so a custody failure
      cannot leave plausible BEDs behind.

      Note on cost: this adds no extra read. The alternative -- rehash the file, then
      read it again -- costs a second 63.6 GB pass AND leaves a time-of-check /
      time-of-use gap between the two.

      Note on what was NOT available: the completed V69_ROUTEB_FRAGMENT_QC_V1 full-file
      scan does NOT constitute a prior cryptographic binding. That producer also copied
      the digest from the acquisition receipt rather than computing one, so its
      `fragments_sha256` field is an assertion of the same unverified kind.

  C2. THE BARCODE AUTHORITY WAS COLLAPSED WITHOUT BEING AUDITED. `dict(zip(barcode,
      donor))` keeps the last row and reports nothing. The source table is now audited
      before collapse (audit_barcode_authority_frame): exact duplicate rows are benign
      and counted, a barcode bound to two donors or two subclusters fails closed.

  C3. INPUTS WERE BOUND BY PATH, NOT CONTENT. Paths are mutable. Every input --
      barcode authority, cohort freeze receipt, QC receipt, per-barcode QC table,
      acquisition receipt, the producer source itself and the modules it imports -- is
      now bound by SHA-256 and byte size, verified against its authority where one
      exists, and recorded in the receipt under `bound_inputs`.

  C4. A COHORT CELL ABSENT FROM THE QC TABLE WAS TREATED AS A QC FAILURE. The V69 code
      computed the excluded set as "cohort barcodes not in the passing set", which
      silently merged `measured and failed` with `never measured`. Absence from the QC
      table is now its own named fail-closed state.

  C5. THE PER-CELL QC VERDICTS INHERITED AN UNVERIFIED PROVENANCE. Repairing C1 in this
      producer alone would still leave the per-cell QC table resting on a scan whose
      input bytes were never digested -- V69_ROUTEB_FRAGMENT_QC_V1 copied its
      `fragments_sha256` from the acquisition receipt exactly as this producer did.
      Requiring those two copied assertions to be equal proves only that two fields
      agree, not that either scan read the authenticated bytes.

      So this producer now RE-COUNTS fragments per cohort barcode inside the verified
      pass and requires exact agreement with the QC table, cell by cell. Agreement
      retroactively binds the QC table to bytes this run digested; any disagreement
      fails closed. The cost is one dictionary lookup per record and one integer per
      cohort cell.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v69_barcode_identity import (  # noqa: E402
    BarcodeIdentityError, assert_donor_map_is_not_suffix_derived,
    audit_barcode_authority_frame)
from v69_custody import (  # noqa: E402
    UNMEASURED, UNVERIFIED_PARTIAL, CustodyError, HashingReader, StagedOutputDir,
    bind_file, sha256_file)

MIN_UNIQUE_FRAGMENTS_PER_BARCODE = 1000   # frozen, SECTION_2

_HERE = Path(__file__).resolve().parent
SCHEMA = "V69_ROUTEB_PSEUDOBULK_FRAGMENTS_V1"


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def _bind_producer_sources() -> dict:
    """Bind the code that is executing, not the code that is checked in somewhere."""
    return {
        "producer": bind_file(Path(__file__).resolve(), label="producer",
                              role="EXECUTING_SOURCE"),
        "barcode_identity_module": bind_file(_HERE / "v69_barcode_identity.py",
                                             label="v69_barcode_identity.py",
                                             role="IMPORTED_SOURCE"),
        "custody_module": bind_file(_HERE / "v69_custody.py",
                                    label="v69_custody.py", role="IMPORTED_SOURCE"),
    }


def _audit_qc_table(qc_tbl: pd.DataFrame) -> dict:
    """The QC table is a second barcode-keyed authority and gets the same treatment."""
    for col in ("barcode", "passes_min_fragments", "n_fragments"):
        if col not in qc_tbl.columns:
            raise FailClosed("FAIL__QC_TABLE_MISSING_COLUMN", missing_column=col,
                             present_columns=list(qc_tbl.columns))
    sub = qc_tbl[["barcode", "passes_min_fragments", "n_fragments"]].astype(str)
    n_rows = len(sub)
    n_bc = int(sub["barcode"].nunique())
    distinct = sub.drop_duplicates()
    if n_bc != n_rows:
        per_bc = distinct.groupby("barcode").size()
        conflicting = per_bc[per_bc > 1]
        if len(conflicting):
            raise FailClosed(
                "FAIL__QC_TABLE_BARCODE_DUPLICATED_WITH_CONFLICTING_VALUES",
                n_conflicting_barcodes=int(len(conflicting)),
                examples=sorted(conflicting.index.tolist())[:10],
                note=("A barcode with two different QC verdicts cannot be collapsed; "
                      "dict(zip(...)) would have kept the last one."))
    return {
        "n_rows": int(n_rows),
        "n_distinct_barcodes": n_bc,
        "n_exact_duplicate_rows_collapsed": int(n_rows - len(distinct)),
        "exact_duplicate_policy": "COLLAPSE_EXACT_DUPLICATE_ROWS",
        "conflicting_duplicate_policy": "FAIL_CLOSED",
    }


def run(fragments: Path, fragments_receipt: Path, qc_receipt: Path,
        cohort_receipt: Path, population: str, out_dir: Path,
        max_records: int = 0) -> dict:
    bound = _bind_producer_sources()

    # ---- C3: bind the authority documents themselves, by content ------------------
    bound["fragments_acquisition_receipt"] = bind_file(
        fragments_receipt, label="ACQ_GSE214979_atac_fragments_V1.json",
        role="FRAGMENT_BYTE_AUTHORITY")
    bound["routeb_qc_receipt"] = bind_file(
        qc_receipt, label="V69_ROUTEB_FRAGMENT_QC_V1.json", role="QC_AUTHORITY")
    bound["cohort_freeze_receipt"] = bind_file(
        cohort_receipt, label="V69_GSE214979_COHORT_FREEZE_V1.json",
        role="COHORT_AUTHORITY")

    acq = json.loads(Path(fragments_receipt).read_text())
    if not str(acq.get("status", "")).startswith("PASS"):
        raise FailClosed("FAIL__FRAGMENTS_ACQUISITION_RECEIPT_IS_NOT_PASS",
                         status=acq.get("status"))
    expected_frag_sha = acq.get("sha256")
    expected_frag_bytes = acq.get("local_bytes")
    if not expected_frag_sha or not isinstance(expected_frag_sha, str):
        raise FailClosed("FAIL__ACQUISITION_RECEIPT_CARRIES_NO_FRAGMENT_DIGEST",
                         note=("Without an authenticated digest there is nothing to "
                               "bind the 63.6 GB input to. Size alone is not identity."))
    observed_bytes = Path(fragments).stat().st_size
    if observed_bytes != expected_frag_bytes:
        # Fast fail only. A size match proves nothing; the digest below is the check.
        raise FailClosed("FAIL__FRAGMENT_FILE_SIZE_CHANGED_SINCE_ACQUISITION",
                         receipt_bytes=expected_frag_bytes,
                         observed_bytes=observed_bytes)

    qc = json.loads(Path(qc_receipt).read_text())
    if not str(qc.get("status", "")).startswith("PASS") or qc.get("PARTIAL_SCAN"):
        raise FailClosed("FAIL__ROUTEB_QC_RECEIPT_NOT_A_COMPLETE_PASS",
                         status=qc.get("status"), partial=qc.get("PARTIAL_SCAN"))
    if str(qc.get("fragments_sha256", "")).strip().lower() != \
            str(expected_frag_sha).strip().lower():
        raise FailClosed("FAIL__QC_SCAN_IS_BOUND_TO_A_DIFFERENT_FRAGMENT_FILE",
                         qc_fragments_sha256=qc.get("fragments_sha256"),
                         acquisition_sha256=expected_frag_sha)

    bound["routeb_qc_per_barcode_table"] = bind_file(
        Path(qc["per_barcode_table"]["path"]), label="per_barcode_qc_table",
        role="PER_CELL_QC_AUTHORITY",
        expected_sha256=qc["per_barcode_table"].get("sha256"))

    coh = json.loads(Path(cohort_receipt).read_text())
    if population not in coh.get("populations", {}):
        raise FailClosed("FAIL__POPULATION_NOT_IN_COHORT_FREEZE",
                         population=population,
                         available=sorted(coh.get("populations", {})))
    pop = coh["populations"][population]
    bound["cohort_barcode_authority"] = bind_file(
        Path(pop["barcode_file"]), label="barcode_authority_csv",
        role="BARCODE_DONOR_SUBCLUSTER_AUTHORITY",
        expected_sha256=pop.get("barcode_file_sha256"))

    # ---- C2: audit the barcode authority BEFORE collapsing it to a dict -----------
    bc = pd.read_csv(Path(pop["barcode_file"]))
    try:
        barcode_to_donor, barcode_to_sub, authority_evidence = \
            audit_barcode_authority_frame(bc)
    except BarcodeIdentityError as e:
        raise FailClosed(getattr(e, "status", "FAIL__BARCODE_AUTHORITY_AUDIT"),
                         reason=str(e), **getattr(e, "detail", {}))

    declared_cells = pop.get("n_cells")
    if declared_cells is not None and int(declared_cells) != len(barcode_to_donor):
        raise FailClosed("FAIL__BARCODE_AUTHORITY_DOES_NOT_RECONCILE_WITH_COHORT_FREEZE",
                         cohort_freeze_n_cells=int(declared_cells),
                         distinct_barcodes_in_authority=len(barcode_to_donor))

    try:
        guard = assert_donor_map_is_not_suffix_derived(
            barcode_to_donor, authority_evidence=authority_evidence)
    except BarcodeIdentityError as e:
        raise FailClosed("FAIL__DONOR_IDENTITY_GUARD", reason=str(e))

    # ---- per-cell QC from the completed full-file scan, applied explicitly ---------
    qc_tbl = pd.read_csv(Path(qc["per_barcode_table"]["path"]))
    qc_table_audit = _audit_qc_table(qc_tbl)
    qc_tbl["barcode"] = qc_tbl["barcode"].astype(str)

    # C4: a cohort cell with no row in the QC table has NO QC verdict. That is a
    # structural absence, not a measured failure, and it is not silently excluded.
    verdict_for = dict(zip(qc_tbl["barcode"], qc_tbl["passes_min_fragments"]))
    unmeasured = sorted(b for b in barcode_to_donor if b not in verdict_for)
    if unmeasured:
        raise FailClosed("FAIL__COHORT_BARCODE_HAS_NO_QC_VERDICT",
                         n_barcodes_without_a_qc_row=len(unmeasured),
                         examples=unmeasured[:10],
                         note=("Absent from the QC table is NOT_MEASURED. Treating it "
                               "as a QC failure would encode a structural absence as a "
                               "measured exclusion."))

    passing = {b for b, v in verdict_for.items() if bool(v)}
    excluded = sorted(b for b in barcode_to_donor if b not in passing)

    keep = {b: (barcode_to_donor[b], barcode_to_sub[b])
            for b in barcode_to_donor if b in passing}
    if not keep:
        raise FailClosed("FAIL__NO_CELLS_SURVIVE_QC")

    # One lookup per fragment record serves three purposes: pseudobulk routing, the
    # out-of-cohort / failed-QC split, and the C5 re-count. The third element is the
    # QC verdict, so a cohort cell that FAILED QC is still counted here -- the re-check
    # covers every cohort cell, not only the surviving ones.
    cohort = {b: (barcode_to_donor[b], barcode_to_sub[b], b in passing)
              for b in barcode_to_donor}

    # ---- C1: stream, digesting the bytes actually consumed ------------------------
    staged = StagedOutputDir(out_dir)
    stage_dir = staged.open()
    handles, counts = {}, Counter()
    for donor, sub in sorted({v for v in keep.values()}):
        key = f"{donor}__{sub}"
        handles[key] = open(stage_dir / f"PSEUDOBULK_{key}.bed", "w", newline="\n")

    partial = bool(max_records)
    n_records = n_in = n_out_of_cohort = n_failed_qc = 0
    recount = Counter()
    reader = HashingReader(fragments)
    try:
        with gzip.GzipFile(fileobj=reader, mode="rb") as gz:
            for raw in gz:
                line = raw.decode("utf-8", "strict")
                if line.startswith("#"):
                    continue
                f = line.rstrip("\n").split("\t")
                if len(f) < 4:
                    continue
                n_records += 1
                meta = cohort.get(f[3])
                if meta is None:
                    n_out_of_cohort += 1
                else:
                    recount[f[3]] += 1
                    if meta[2]:
                        key = f"{meta[0]}__{meta[1]}"
                        handles[key].write(f"{f[0]}\t{f[1]}\t{f[2]}\n")
                        counts[key] += 1
                        n_in += 1
                    else:
                        n_failed_qc += 1
                if max_records and n_records >= max_records:
                    break
        if not partial:
            reader.drain()
    except Exception as e:                      # truncated / corrupt gzip stream
        for h in handles.values():
            h.close()
        reader.close()
        q = staged.quarantine_failed()
        raise FailClosed("FAIL__FRAGMENT_STREAM_DECOMPRESSION_FAILED",
                         error_type=type(e).__name__, error=str(e)[:400],
                         compressed_bytes_consumed=reader.n_bytes,
                         quarantined_outputs=q)
    finally:
        for h in handles.values():
            h.close()

    complete = reader.complete
    n_consumed = reader.n_bytes
    observed_sha = reader.hexdigest()
    reader.close()

    if partial:
        fragment_identity = {
            "expected_sha256": str(expected_frag_sha).strip().lower(),
            "observed_sha256": UNVERIFIED_PARTIAL,
            "verified": False,
            "compressed_bytes_digested": n_consumed,
            "file_bytes": observed_bytes,
            "why_not_verified": ("--max-records truncated the stream, so no whole-file "
                                 "digest exists. This is recorded as unverified rather "
                                 "than filled in from the acquisition receipt."),
        }
    else:
        if not complete or n_consumed != observed_bytes:
            q = staged.quarantine_failed()
            raise FailClosed("FAIL__FRAGMENT_STREAM_NOT_FULLY_CONSUMED",
                             compressed_bytes_digested=n_consumed,
                             file_bytes=observed_bytes, quarantined_outputs=q)
        if observed_sha.lower() != str(expected_frag_sha).strip().lower():
            q = staged.quarantine_failed()
            raise FailClosed(
                "FAIL__FRAGMENT_BYTES_DO_NOT_MATCH_AUTHENTICATED_DIGEST",
                expected_sha256=str(expected_frag_sha).strip().lower(),
                observed_sha256=observed_sha, file_bytes=observed_bytes,
                quarantined_outputs=q,
                note=("The file has the authenticated LENGTH but not the authenticated "
                      "BYTES. Every output of this run has been quarantined."))
        fragment_identity = {
            "expected_sha256": str(expected_frag_sha).strip().lower(),
            "observed_sha256": observed_sha,
            "verified": True,
            "digest_source": "COMPUTED_FROM_THE_COMPRESSED_BYTES_READ_BY_THIS_RUN",
            "compressed_bytes_digested": n_consumed,
            "file_bytes": observed_bytes,
        }

    # ---- C5: re-derive the per-cell QC counts from the bytes this run digested ----
    if partial:
        qc_recount = {
            "performed": False,
            "why_not": ("A partial scan cannot reproduce whole-file per-cell counts, "
                        "so this run does not bind the QC table to verified bytes."),
            "n_cells_compared": 0,
            "n_cells_disagreeing": UNMEASURED,
        }
    else:
        declared = dict(zip(qc_tbl["barcode"],
                            qc_tbl["n_fragments"].astype("int64").tolist()))
        disagree = {}
        for bcode in barcode_to_donor:
            d, o = int(declared[bcode]), int(recount.get(bcode, 0))
            if d != o:
                disagree[bcode] = {"qc_table": d, "verified_pass": o}
        if disagree:
            q = staged.quarantine_failed()
            raise FailClosed(
                "FAIL__QC_TABLE_FRAGMENT_COUNTS_DISAGREE_WITH_THE_VERIFIED_PASS",
                n_cells_compared=len(barcode_to_donor),
                n_cells_disagreeing=len(disagree),
                examples=dict(sorted(disagree.items())[:10]),
                quarantined_outputs=q,
                note=("The QC table was produced by a scan whose input bytes were "
                      "never digested. This pass digested its input and re-counted; "
                      "the two disagree, so the per-cell QC verdicts cannot be "
                      "trusted and no pseudobulk may be built from them."))
        qc_recount = {
            "performed": True,
            "what_it_establishes": (
                "The per-cell fragment counts in V69_ROUTEB_FRAGMENT_QC_V1 were "
                "re-derived from the bytes THIS run digested and agree exactly. That "
                "retroactively binds the QC table -- whose own receipt copied its "
                "fragments_sha256 from the acquisition receipt rather than measuring "
                "it -- to the authenticated fragment bytes."),
            "n_cells_compared": len(barcode_to_donor),
            "n_cells_disagreeing": 0,
            "total_cohort_fragments_in_verified_pass": int(sum(recount.values())),
        }

    out_dir = staged.promote()

    # Re-read each output from disk; the recorded state describes files, not memory.
    pseudobulks = {}
    empty = []
    cells_per_key = Counter(f"{m[0]}__{m[1]}" for m in keep.values())
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
            "n_cells": int(cells_per_key[key]),
            "path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size,
        }
        if n_lines == 0:
            empty.append(key)

    return {
        "schema": SCHEMA,
        "run_utc": utcnow(),
        "population": population,
        "PARTIAL_SCAN": partial,
        "partial_scan_note": ("A partial scan is a smoke test only and must never feed "
                              "peak calling." if partial else "Full-file scan."),
        "custody_contract": "V74_ROUTEB_CUSTODY_V1",
        "fragment_identity": fragment_identity,
        "fragments_sha256": fragment_identity["observed_sha256"],
        "fragments_bytes": observed_bytes,
        "bound_inputs": bound,
        "barcode_authority_audit": authority_evidence,
        "qc_table_audit": qc_table_audit,
        "records_scanned": n_records,
        "records_written_to_a_pseudobulk": n_in,
        "records_discarded_out_of_cohort": n_out_of_cohort,
        "records_discarded_because_the_cell_failed_qc": n_failed_qc,
        "records_discarded_out_of_cohort_or_failing_qc": n_out_of_cohort + n_failed_qc,
        "discard_split_note": ("V69 reported a single conflated discard count. Out-of-cohort and failed-QC are different facts about different cells and are now reported separately."),
        "qc_table_recount": qc_recount,
        "pseudobulk_unit": "donor x published microglial subcluster (frozen SECTION_2)",
        "donor_identity_guard": guard,
        "cell_qc": {
            "min_unique_fragments_per_barcode": MIN_UNIQUE_FRAGMENTS_PER_BARCODE,
            "source": "V69_ROUTEB_FRAGMENT_QC_V1 full-file scan",
            "n_cohort_cells": len(barcode_to_donor),
            "n_cells_used": len(keep),
            "n_cells_excluded_by_qc": len(excluded),
            "n_cells_with_no_qc_verdict": 0,
            "qc_counts_rederived_from_the_verified_pass": qc_recount["performed"],
            "semantics": ("Excluded cells are recorded, not silently dropped. They are "
                          "QC exclusions, not biological absences. A cohort cell with "
                          "no row in the QC table is a separate fail-closed state and "
                          "is never counted as an exclusion."),
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


def _emit(receipt: dict, path: Path) -> int:
    """Write the receipt, then read it back and report from the bytes on disk.

    The verdict must exist in the object being written, never only in stdout. Printing
    from the re-read file makes it impossible for a run to announce a status that the
    receipt does not contain.
    """
    if "status" not in receipt:
        receipt["status"] = "FAIL__RECEIPT_HAS_NO_STATUS_FIELD"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    on_disk = json.loads(path.read_text())
    print(json.dumps({k: v for k, v in on_disk.items()
                      if k not in ("pseudobulks", "bound_inputs")}, indent=2)[:3500])
    print("RECEIPT_ON_DISK_STATUS=" + str(on_disk["status"]))
    return 0 if str(on_disk["status"]).startswith("PASS") else 1


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
        r = {"schema": SCHEMA, "run_utc": utcnow(), "status": e.status, **e.detail}
    except CustodyError as e:
        r = {"schema": SCHEMA, "run_utc": utcnow(), "status": e.status, **e.detail}
    return _emit(r, Path(a.receipt))


if __name__ == "__main__":
    raise SystemExit(main())
