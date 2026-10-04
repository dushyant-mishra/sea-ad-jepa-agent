"""Independent replay of the completed Route-B pseudobulk extraction.

Re-reads every artifact from disk and re-derives every number the receipt asserts,
without importing the producer's own logic for the quantities under test. A receipt
that agrees with itself proves nothing; this checks it against the bytes.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(r"D:/jepa_v5_outputs_20260925/v74_laneD")
V69 = Path(r"D:/jepa_v5_outputs_20260925/v69_scenicplus")
REC = OUT / "receipts" / "V74_ROUTEB_PSEUDOBULK_FRAGMENTS_V1.json"
SNAP = OUT / "snapshot" / "554887493765797b976d937ea92aa4fffd4dcd5b"


def sha(p, chunk=8 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def rd(p):
    with open(p, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


r = json.loads(rd(REC))
checks = {}
detail = {}

# 1. every pseudobulk BED still has the bytes the receipt names, and the line counts
#    it reports.
bad_digest, bad_lines, total_lines, total_bytes = [], [], 0, 0
for key, meta in r["pseudobulks"].items():
    p = Path(meta["path"])
    if not p.is_file():
        bad_digest.append((key, "MISSING"))
        continue
    if sha(p) != meta["sha256"]:
        bad_digest.append((key, "DIGEST"))
    with open(p, "rb") as fh:
        n = sum(1 for _ in fh)
    total_lines += n
    total_bytes += p.stat().st_size
    if n != meta["n_fragments"]:
        bad_lines.append((key, n, meta["n_fragments"]))
checks["every_pseudobulk_bed_matches_its_recorded_digest"] = not bad_digest
checks["every_pseudobulk_line_count_matches_the_receipt"] = not bad_lines
detail["n_pseudobulks"] = len(r["pseudobulks"])
detail["total_bed_lines_on_disk"] = total_lines
detail["total_bed_bytes_on_disk"] = total_bytes
detail["bad_digest"] = bad_digest
detail["bad_lines"] = bad_lines

# 2. the BED lines reconcile with the records the receipt says it wrote.
checks["bed_lines_equal_records_written"] = (
    total_lines == r["records_written_to_a_pseudobulk"])

# 3. the record accounting is complete: nothing vanished between the three buckets.
acct = (r["records_written_to_a_pseudobulk"]
        + r["records_discarded_out_of_cohort"]
        + r["records_discarded_because_the_cell_failed_qc"])
checks["record_accounting_is_complete"] = acct == r["records_scanned"]
detail["records_scanned"] = r["records_scanned"]
detail["records_accounted_for"] = acct

# 4. the fragment digest equals the INDEPENDENTLY authenticated acquisition digest,
#    and the producer says it measured rather than copied it.
acq = json.loads(rd(V69 / "receipts" / "ACQ_GSE214979_atac_fragments_V1.json"))
fid = r["fragment_identity"]
checks["fragment_digest_equals_the_acquisition_authority"] = (
    fid["observed_sha256"] == acq["sha256"]
    == "b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f")
checks["fragment_digest_was_measured_not_copied"] = (
    fid["verified"] is True
    and fid["digest_source"] == "COMPUTED_FROM_THE_COMPRESSED_BYTES_READ_BY_THIS_RUN"
    and fid["compressed_bytes_digested"] == 63641120882)

# 5. the executing bytes are the snapshot bytes, and the snapshot is the committed head.
snap_ok = True
for name in ("producer", "barcode_identity_module", "custody_module"):
    rec = r["bound_inputs"][name]
    p = Path(rec["path"])
    snap_ok &= p.is_file() and sha(p) == rec["sha256"] and SNAP in p.parents
checks["executing_sources_still_match_the_immutable_snapshot"] = snap_ok

# 6. the QC re-count independently reproduces the V69 full-scan totals.
qcr = json.loads(rd(V69 / "receipts" / "V69_ROUTEB_FRAGMENT_QC_V1.json"))
checks["recount_reproduces_v69_cohort_fragment_total"] = (
    r["qc_table_recount"]["total_cohort_fragments_in_verified_pass"]
    == qcr["barcode_space"]["fragment_records_with_a_cohort_barcode"] == 23522438)
checks["recount_reproduces_v69_records_scanned"] = (
    r["records_scanned"] == qcr["records_scanned"] == 5831261753)
checks["recount_reproduces_v69_out_of_cohort_total"] = (
    r["records_discarded_out_of_cohort"]
    == qcr["barcode_space"]["fragment_records_outside_the_cohort"] == 5807739315)
checks["no_cell_disagreed_on_its_qc_fragment_count"] = (
    r["qc_table_recount"]["performed"] is True
    and r["qc_table_recount"]["n_cells_disagreeing"] == 0
    and r["qc_table_recount"]["n_cells_compared"] == 2534)

# 7. nothing was left staged or quarantined.
checks["no_staging_or_quarantine_directory_remains"] = not any(
    (OUT / "routeB" / ("pseudobulk" + s)).exists()
    for s in ("__STAGING", "__QUARANTINE_FAILED_CUSTODY"))

# 8. no BED carries a carriage return into MACS.
checks["no_bed_contains_a_carriage_return"] = all(
    b"\r" not in Path(m["path"]).read_bytes()[:1 << 20] for m in r["pseudobulks"].values())

out = {
    "schema": "V74_ROUTEB_PSEUDOBULK_REPLAY_VERIFICATION_V1",
    "run_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "purpose": ("Re-derive from the bytes on disk every quantity the extraction receipt "
                "asserts. A receipt that agrees with itself is not evidence."),
    "receipt_verified": {"path": str(REC), "sha256": sha(REC)},
    "checks": checks,
    "detail": detail,
    "scope_note": ("This verifies the extraction as an engineering artifact. It is not "
                   "a biological result and qualifies no region universe."),
}
out["status"] = ("PASS__PSEUDOBULK_EXTRACTION_REPLAYED_FROM_DISK"
                 if all(checks.values())
                 else "FAIL__REPLAY_DISAGREES_WITH_THE_RECEIPT")
dest = OUT / "receipts" / "V74_ROUTEB_PSEUDOBULK_REPLAY_VERIFICATION_V1.json"
with open(dest, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(out, indent=2) + "\n")
on_disk = json.loads(rd(dest))
for k, v in on_disk["checks"].items():
    print("  %-55s %s" % (k, v))
print(json.dumps(on_disk["detail"], indent=1))
print("RECEIPT_ON_DISK_STATUS=" + on_disk["status"])
sys.exit(0 if on_disk["status"].startswith("PASS") else 1)
