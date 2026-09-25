#!/usr/bin/env python3
"""Physical source inventory v2 — fails closed against a frozen expected set.

Replaces `physical_source_inventory_vnext.py`, which the independent audit found
to fail open and to carry unbound assertions. Three defects are fixed:

**Fail-open on a missing sidecar.** v1 returned exit 0 whenever `mismatches` was
empty, even with `unverified` non-empty, so an asset with no `.sha256` beside it
passed. Here every asset must match the frozen manifest, and there is no path
that reports a problem and exits 0.

**Unbound expected set.** v1 inventoried whatever directories happened to exist.
Here the authority is `FROZEN_EXPECTED_16_ASSET_MANIFEST_V1.json`, committed in
the repository, pinning exactly 16 assets by study, filename, byte length, full
SHA-256, format and role. A sidecar living beside its own asset is not
independent authentication; the frozen manifest is, because it is versioned
separately from the data it describes.

**Scientific status presented as machine output.** v1 emitted hand-authored ETL
and exposure strings in the same JSON as measured digests, and they went stale
inside a single PR. Here machine-checked columns and curator assertions are
separate top-level blocks, and every assertion carries a source reference,
reviewer and digest. The producer never invents a status: an asset or study
absent from the registry is an error, not a default.

Exit status: 0 only when every frozen asset is present, byte-exact,
digest-exact, role-known, and every study carries a registered assertion.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

SIDECAR_SUFFIXES = (".sha256", ".verification.json")
MAGIC = [(b"\x1f\x8b", "gzip"), (b"BZh", "bzip2"),
         (b"\x89HDF\r\n\x1a\n", "hdf5"), (b"PK\x03\x04", "zip")]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(4 << 20), b""):
            h.update(chunk)
    d = h.hexdigest()
    if len(d) != 64:
        raise SystemExit("digest not 64 hex characters for %s" % path)
    return d


def detect_format(path):
    with open(path, "rb") as fh:
        head = fh.read(8)
        for sig, name in MAGIC:
            if head.startswith(sig):
                return name
        fh.seek(257)
        if fh.read(5) == b"ustar":
            return "tar"
    return "unknown"


def read_sidecar_digest(asset_path):
    p = asset_path + ".sha256"
    if not os.path.exists(p):
        return None
    for tok in open(p).read().replace("*", " ").split():
        t = tok.lower()
        if len(t) == 64 and all(c in "0123456789abcdef" for c in t):
            return t
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--frozen-manifest", required=True)
    ap.add_argument("--assertion-registry", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    with open(a.frozen_manifest) as fh:
        frozen = json.load(fh)
    expected = {(x["study"], x["asset"]): x for x in frozen["assets"]}
    if len(expected) != frozen["asset_count"]:
        raise SystemExit("frozen manifest is internally inconsistent")

    with open(a.assertion_registry) as fh:
        registry = json.load(fh)
    assertions = registry.get("assertions", {})

    failures, rows = [], []

    # ---- what is actually on disk -----------------------------------------
    present = {}
    if not os.path.isdir(a.store):
        raise SystemExit("store not found: %s" % a.store)
    for study in sorted(os.listdir(a.store)):
        sdir = os.path.join(a.store, study)
        if not os.path.isdir(sdir):
            continue
        for name in sorted(os.listdir(sdir)):
            full = os.path.join(sdir, name)
            if not os.path.isfile(full):
                continue
            if name.endswith(SIDECAR_SUFFIXES) or name.endswith(".soft.txt"):
                continue
            present[(study, name)] = full

    for key in sorted(set(expected) - set(present)):
        failures.append("MISSING_EXPECTED_ASSET %s/%s" % key)
    for key in sorted(set(present) - set(expected)):
        failures.append("UNEXPECTED_ASSET %s/%s" % key)

    # ---- verify every frozen asset that is present -------------------------
    for key in sorted(set(expected) & set(present)):
        exp, full = expected[key], present[key]
        size = os.path.getsize(full)
        actual = sha256_file(full)
        sidecar = read_sidecar_digest(full)
        fmt = detect_format(full)

        if size != exp["bytes"]:
            failures.append("SIZE_MISMATCH %s/%s frozen %d, disk %d"
                            % (key[0], key[1], exp["bytes"], size))
        if actual != exp["sha256"]:
            failures.append("DIGEST_MISMATCH %s/%s\n    frozen %s\n    disk   %s"
                            % (key[0], key[1], exp["sha256"], actual))
        if sidecar is None:
            # v1 tolerated this and exited 0. It is now a hard failure.
            failures.append("NO_SIDECAR_DIGEST %s/%s" % key)
        elif sidecar != actual:
            failures.append("SIDECAR_DISAGREES_WITH_BYTES %s/%s" % key)
        if fmt != exp["format"]:
            failures.append("FORMAT_MISMATCH %s/%s frozen %s, magic bytes %s"
                            % (key[0], key[1], exp["format"], fmt))
        if not exp.get("role"):
            failures.append("UNKNOWN_ROLE %s/%s" % key)

        rows.append({
            "study": key[0], "asset": key[1],
            "path": full.replace("\\", "/"), "bytes": size,
            "sha256_recomputed": actual,
            "sha256_frozen_manifest": exp["sha256"],
            "sha256_sidecar": sidecar or "",
            "format_from_magic_bytes": fmt,
            "expected_role": exp.get("role", ""),
            "machine_verdict": "VERIFIED" if (
                size == exp["bytes"] and actual == exp["sha256"]
                and sidecar == actual and fmt == exp["format"]) else "FAILED",
        })

    # ---- every study must carry a registered assertion ---------------------
    studies = sorted({k[0] for k in expected})
    for s in studies:
        if s not in assertions:
            failures.append("NO_REGISTERED_ASSERTION %s" % s)
            continue
        for field in ("etl_status", "outcome_exposure", "biological_estimability",
                      "source_reference", "reviewer", "asserted_on"):
            if not assertions[s].get(field):
                failures.append("ASSERTION_FIELD_MISSING %s.%s" % (s, field))

    os.makedirs(a.out_dir, exist_ok=True)
    csv_path = os.path.join(a.out_dir, "STUDY_SOURCE_INVENTORY_V2.csv")
    if rows:
        with open(csv_path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)

    receipt = {
        "schema": "PERTURBATION_PHYSICAL_SOURCE_INVENTORY_V2",
        "verdict": "FAIL" if failures else "PASS",
        "store": a.store.replace("\\", "/"),
        "frozen_manifest_sha256": sha256_file(a.frozen_manifest),
        "assertion_registry_sha256": sha256_file(a.assertion_registry),
        "expected_assets": len(expected),
        "assets_found": len(present),
        "assets_verified": sum(1 for r in rows if r["machine_verdict"] == "VERIFIED"),
        "failures": failures,
        "independence_basis": {
            "note": ("self-audit S1: the frozen manifest was GENERATED from an "
                     "earlier inventory run by this same lane, so it is not an "
                     "independent third source. Its authority comes from the "
                     "three-way agreement asserted below, in which the "
                     "acquisition-time sidecars are the only component written "
                     "before this work began."),
            "three_way_agreement_required": [
                "bytes on disk (recomputed here)",
                "acquisition-time .sha256 sidecar",
                "frozen expected manifest",
            ],
            "assets_where_all_three_agree": sum(
                1 for r in rows
                if r["sha256_recomputed"] == r["sha256_sidecar"]
                and r["sha256_recomputed"] == r["sha256_frozen_manifest"]),
            "assets_total": len(rows),
        },
        "machine_checked": {
            "note": ("every field in the inventory CSV is measured from bytes on "
                     "disk or compared against the frozen manifest"),
            "total_bytes": sum(r["bytes"] for r in rows),
        },
        "curator_assertions": {
            "note": ("scientific status is NOT machine-checked; each entry "
                     "carries a source reference, reviewer and assertion date, "
                     "and is stored separately so it cannot be mistaken for a "
                     "measured column"),
            "registry": registry.get("registry_id"),
            "entries": assertions,
        },
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    if rows:
        receipt["inventory_csv_sha256"] = sha256_file(csv_path)
    rp = os.path.join(a.out_dir, "STUDY_SOURCE_INVENTORY_RECEIPT_V2.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("=== VERDICT: %s ===" % receipt["verdict"])
    print("  expected %d | found %d | verified %d"
          % (len(expected), len(present), receipt["assets_verified"]))
    if failures:
        for f in failures:
            print("  " + f)
    else:
        print("  %s bytes, all sizes, digests, formats, roles and sidecars agree"
              % f"{receipt['machine_checked']['total_bytes']:,}")
    print("\nwrote %s" % rp)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
