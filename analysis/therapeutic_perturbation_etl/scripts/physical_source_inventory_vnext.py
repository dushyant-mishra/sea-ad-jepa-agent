#!/usr/bin/env python3
"""Physical inventory of the authenticated perturbation source store.

Rehashes every primary asset from its bytes on disk and reconciles the result
against the `.sha256` sidecar recorded at acquisition. Format is determined from
magic bytes, not from the filename extension, because an extension is a claim
and the leading bytes are evidence.

Four axes are reported separately for each study, because conflating them is how
a directory listing turns into an unearned `ETL_COMPLETE`:

  PHYSICAL_AUTHENTICITY   do the bytes on disk match what was acquired
  ETL_STATUS              has a producer actually consumed them
  BIOLOGICAL_ESTIMABILITY what independent units exist, if any
  OUTCOME_EXPOSURE        has any response value been read

A study can be physically perfect and still be `NOT_ESTIMABLE`. A study can be
fully ETL'd and still have every outcome unread. Nothing here infers one axis
from another.

Sidecar files (`.sha256`, `.verification.json`) and series SOFT records are
catalogued but are not primary assets; they are acquisition metadata.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

SIDECAR_SUFFIXES = (".sha256", ".verification.json")
EXPECTED_MANIFEST_SCHEMA = "PERTURBATION_EXPECTED_SOURCE_ROOTS_REVIEW_V1"

MAGIC = [
    (b"\x1f\x8b", "gzip"),
    (b"BZh", "bzip2"),
    (b"\x89HDF\r\n\x1a\n", "hdf5"),
    (b"PK\x03\x04", "zip"),
    (b"RDX", "r-rdata-uncompressed"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(4 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_format(path):
    """Format from leading bytes; tar is detected at its offset-257 signature."""
    with open(path, "rb") as fh:
        head = fh.read(8)
        for sig, name in MAGIC:
            if head.startswith(sig):
                return name
        fh.seek(257)
        if fh.read(5) in (b"ustar", b"ustar"):
            return "tar"
    return "unknown"


def read_sidecar_digest(asset_path):
    """Recorded digest from `<asset>.sha256`, or None."""
    p = asset_path + ".sha256"
    if not os.path.exists(p):
        return None
    txt = open(p).read().strip()
    for tok in txt.replace("*", " ").split():
        t = tok.lower()
        if len(t) == 64 and all(c in "0123456789abcdef" for c in t):
            return t
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, help="authenticated source store root")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--expected-manifest", required=True,
                    help="separately reviewed exact study/asset/byte/SHA-256 inventory")
    ap.add_argument("--readiness", required=True,
                    help="JSON of per-study scientific readiness assertions")
    a = ap.parse_args()
    with open(a.expected_manifest, encoding="utf-8") as fh:
        expected = json.load(fh)
    if expected.get("schema") != EXPECTED_MANIFEST_SCHEMA:
        raise SystemExit("STOP_EXPECTED_SOURCE_MANIFEST_SCHEMA")
    expected_rows = expected.get("assets")
    if not isinstance(expected_rows, list) or not expected_rows:
        raise SystemExit("STOP_EMPTY_EXPECTED_SOURCE_MANIFEST")
    expected_by_key = {}
    for row in expected_rows:
        if set(row) != {"study", "asset", "bytes", "sha256"}:
            raise SystemExit("STOP_BAD_EXPECTED_SOURCE_ROW")
        key = (row["study"], row["asset"])
        if key in expected_by_key or "/" in key[1] or "\\" in key[1] or key[1] in (".", ".."):
            raise SystemExit("STOP_DUPLICATE_OR_UNSAFE_EXPECTED_SOURCE")
        if type(row["bytes"]) is not int or row["bytes"] < 0 or len(row["sha256"]) != 64:
            raise SystemExit("STOP_BAD_EXPECTED_SIZE_OR_SHA")
        expected_by_key[key] = row
    out_path = os.path.abspath(a.out_dir)
    source_path = os.path.abspath(a.store)
    if os.path.commonpath((out_path, source_path)) == source_path:
        raise SystemExit("STOP_OUTPUT_INSIDE_SOURCE_STORE")
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    if not os.path.isdir(a.store):
        raise SystemExit("STOP_SOURCE_STORE_MISSING")
    os.makedirs(a.out_dir, exist_ok=True)

    with open(a.readiness) as fh:
        readiness = json.load(fh)

    studies = sorted(d for d in os.listdir(a.store)
                     if os.path.isdir(os.path.join(a.store, d)))
    rows, per_study = [], {}
    mismatches, unverified, unexpected = [], [], []
    actual_keys = set()

    for study in studies:
        sdir = os.path.join(a.store, study)
        assets, sidecars, soft = [], [], []
        for name in sorted(os.listdir(sdir)):
            full = os.path.join(sdir, name)
            if not os.path.isfile(full):
                continue
            if name.endswith(SIDECAR_SUFFIXES):
                sidecars.append(name)
            elif name.endswith(".soft.txt"):
                soft.append(name)
            else:
                assets.append(name)

        for name in assets:
            full = os.path.join(sdir, name)
            key = (study, name)
            actual_keys.add(key)
            reviewed = expected_by_key.get(key)
            if reviewed is None:
                unexpected.append("%s/%s" % key)
            size = os.path.getsize(full)
            print("  hashing %-58s %14d B" % (name[:58], size), flush=True)
            actual = sha256_file(full)
            recorded = read_sidecar_digest(full)
            if reviewed is None:
                status = "UNREVIEWED_SOURCE"
            elif size != reviewed["bytes"] or actual != reviewed["sha256"]:
                status = "REVIEWED_SOURCE_ROOT_MISMATCH"
                mismatches.append("%s/%s" % key)
            elif recorded is None:
                status = "NO_SIDECAR_DIGEST"
                unverified.append("%s/%s" % (study, name))
            elif recorded == actual and reviewed is not None:
                status = "VERIFIED"
            else:
                status = "DIGEST_MISMATCH"
                mismatches.append("%s/%s" % (study, name))
            rows.append({
                "study": study,
                "asset": name,
                "path": os.path.join(sdir, name).replace("\\", "/"),
                "bytes": size,
                "sha256_recomputed": actual,
                "sha256_recorded_sidecar": recorded or "",
                "authenticity": status,
                "format_from_magic_bytes": detect_format(full),
            })

        r = readiness.get(study, {})
        per_study[study] = {
            "primary_assets": len(assets),
            "sidecar_files": len(sidecars),
            "series_soft_records": len(soft),
            "total_primary_bytes": sum(x["bytes"] for x in rows
                                       if x["study"] == study),
            "physical_authenticity": (
                "ALL_VERIFIED" if all(x["authenticity"] == "VERIFIED"
                                      for x in rows if x["study"] == study)
                else "SEE_ASSET_ROWS"),
            "etl_status": r.get("etl_status", "UNRECORDED"),
            "biological_estimability": r.get("biological_estimability", "UNRECORDED"),
            "outcome_exposure": r.get("outcome_exposure", "UNRECORDED"),
            "independent_units": r.get("independent_units", "UNRECORDED"),
            "limitation": r.get("limitation", ""),
            "blocking_missing_source": r.get("blocking_missing_source", ""),
        }

    missing = ["%s/%s" % key for key in sorted(set(expected_by_key) - actual_keys)]
    unexpected_studies = sorted(set(studies) - {k[0] for k in expected_by_key})
    if missing or unexpected or unexpected_studies or mismatches or unverified:
        raise SystemExit("STOP_INVENTORY_SOURCE_CENSUS_OR_AUTHENTICITY:" + json.dumps({
            "missing": missing, "unexpected": unexpected, "unexpected_studies": unexpected_studies,
            "mismatch": mismatches, "no_sidecar": unverified}, sort_keys=True))
    if len(rows) != len(expected_by_key) or sum(x["bytes"] for x in rows) != expected["total_primary_bytes"]:
        raise SystemExit("STOP_INVENTORY_COUNT_OR_BYTES_MISMATCH")
    csv_path = os.path.join(a.out_dir, "STUDY_SOURCE_INVENTORY_VNEXT.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    receipt = {
        "schema": "PERTURBATION_PHYSICAL_SOURCE_INVENTORY_VNEXT",
        "store": a.store.replace("\\", "/"),
        "studies": len(studies),
        "primary_assets": len(rows),
        "total_primary_bytes": sum(r["bytes"] for r in rows),
        "expected_manifest_sha256": sha256_file(a.expected_manifest),
        "expected_manifest_review_status": expected.get("review_status", "UNREVIEWED"),
        "readiness_assertions_are_self_reported_not_reconciled": True,
        "authenticity_summary": {
            "verified": sum(1 for r in rows if r["authenticity"] == "VERIFIED"),
            "digest_mismatch": len(mismatches),
            "no_sidecar_digest": len(unverified),
            "mismatched_assets": mismatches,
            "unverifiable_assets": unverified,
        },
        "axes_are_independent": (
            "physical authenticity, ETL status, biological estimability and "
            "outcome exposure are reported separately; none is inferred from "
            "another, and no study receives a blanket ETL_COMPLETE"),
        "per_study": per_study,
        "inventory_csv_sha256": None,
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    receipt["inventory_csv_sha256"] = sha256_file(csv_path)
    rp = os.path.join(a.out_dir, "STUDY_SOURCE_INVENTORY_RECEIPT_VNEXT.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("\n=== PHYSICAL AUTHENTICITY ===")
    s = receipt["authenticity_summary"]
    print("  %d assets, %s bytes" % (len(rows), f"{receipt['total_primary_bytes']:,}"))
    print("  verified %d | digest mismatch %d | no sidecar %d"
          % (s["verified"], s["digest_mismatch"], s["no_sidecar_digest"]))
    for m in mismatches:
        print("    MISMATCH  %s" % m)
    for u in unverified:
        print("    NO DIGEST %s" % u)
    print("\n=== PER STUDY (four independent axes) ===")
    for st, v in per_study.items():
        print("  %-10s assets=%-2d  auth=%-13s etl=%-22s estimability=%s"
              % (st, v["primary_assets"], v["physical_authenticity"],
                 v["etl_status"], v["biological_estimability"]))
    print("\nwrote %s\nwrote %s" % (csv_path, rp))
    return 0  # All known failure states exited before emitting a receipt.


if __name__ == "__main__":
    sys.exit(main())
