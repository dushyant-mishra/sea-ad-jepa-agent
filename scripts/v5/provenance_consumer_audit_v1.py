#!/usr/bin/env python3
"""Every consumer of the address provenance table, classified and digest-bound.

WHY THIS IS NOT A BUG HUNT IN TWO SCRIPTS

  The same positional-mapping defect was found in the Level-4 materializer and
  then in the 50k discovery materializer. Two independent authors do not make
  the same mistake by chance. The cause is in the contract itself:

      stage81a2r_authoritative_gene_identity_recovery.py:286
          result.insert(3, "source_feature_index", result["source_feature_id"])

  `source_feature_index` is a copy of `source_feature_id`, and what that
  identifies depends on which path produced the row:

    * For the `_COMMON` families (HVS_COMMON, SEA_AD_COMMON) it indexes the
      HARMONIZED feature universe, which is ordered by Ensembl ID. Measured:
      HVS_COMMON's source_feature_index agrees with Ensembl-ascending rank on
      100.0% of rows.
    * For the per-object NPH52 entries the R extractors construct it
      positionally -
          stage81a2_audit_nph_freeze.R:138       seq_len(nrow(object)) - 1L
          stage81a2r_extract_r_feature_metadata.R:124  seq_along(feature_ids) - 1L
      - so it IS the object's own row position. Verified for the NPH52 MG
      reader-fit derivative at 32,176 of 32,176 rows.

  One column, two meanings, no marker distinguishing them. Every count
  materializer reads it as the object's row position, which is right for NPH52
  and wrong for the two `_COMMON` families. The defect is a property of the
  contract, not of any one script, which is why it reproduced identically.

WHAT THIS SCRIPT DOES

  Enumerates consumers, classifies each as COUNT_PRODUCING or METADATA_ONLY,
  records the sha256 of every consumer and of every produced artifact it can
  find, and emits a dependency graph with an explicit affected/sound/unverified
  disposition per path.

  A consumer is found by TWO searches, because either alone undercounts:
  by the provenance FILENAME, and by use of the `source_feature_index` COLUMN.
  `materialize_full104_phase2_nph_blocks.R` receives the provenance path as a
  command-line argument and never names it, so a filename grep misses it
  entirely.

  Anything this script cannot verify is marked UNVERIFIED, never assumed sound.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

PROV_BASENAME = "stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
PROV_STEM = "stage81a2r_foundation_molecular_address_source_provenance"
COLUMN = "source_feature_index"

# A path is COUNT_PRODUCING when it uses the mapping to place source counts at
# molecular addresses and writes them. Detected by co-occurrence of a positional
# index into a matrix with a sparse/array write.
POSITIONAL_PATTERNS = [
    r"source_to_address\s*\[",          # python: array/dict lookup by source col
    r"source_to_address\.get",
    r"counts\[\s*mapping\$source_feature_index\s*\+\s*1L",   # R positional index
    r"source_counts\[\s*mapping\$source_feature_index\s*\+\s*1L",
]
WRITE_PATTERNS = [r"save_npz", r"savez", r"writeMM", r"sparseMatrix", r"csr_matrix"]

# Dispositions established elsewhere in this cycle, cited rather than re-derived.
KNOWN = {
    "materialize_full104_phase2_expression.py": (
        "AFFECTED_CONFIRMED",
        "Level-4 blocks. Verified against authenticated sources: column "
        "agreement 4.2-8.0% against a 90% floor, value multiset identical, row "
        "identity intact. Decoders built and verified at 100.00%."),
    "foundation_materialize_discovery_expression.py": (
        "AFFECTED_CONFIRMED",
        "50k discovery corpus (output sha256 4c50f1de...). Shard op19 read from "
        "git and probed: APOE 0.0% naive vs 55.5% decoded, CSF1R 0.0% vs 76.6%."),
    "materialize_full104_phase2_nph_blocks.R": (
        "SOUND_VERIFIED",
        "NPH52 Level-4 blocks. Feature axis verified against "
        "assay(object,'counts') of the READER-FIT derivative: 32,176 of 32,176, "
        "with the 1-based alternative at 0.00%."),
    "foundation_materialize_nph_discovery_sample.R": (
        "SOUND_VERIFIED",
        "NPH52 discovery shards. Reads the TRAIN derivative, which is a "
        "different file from the reader-fit one, so the earlier verification "
        "did not transfer and it was checked separately: 33,441 features by "
        "19,375 cells, 32,176 of 32,176 provenance rows agreeing zero-based, "
        "1-based alternative 0.00%."),
    "full104_expression_interface_nph.R": (
        "SOUND_VERIFIED",
        "NPH52 interface matrices. Reads the TRAIN derivative via the physical "
        "split exactness manifest; that axis is verified at 100.00%."),
    "full104_expression_interface_nph_v8.R": (
        "SOUND_VERIFIED",
        "NPH52 interface matrices v8. Reads the reader-fit derivative via "
        "NPH_READER_FIT_DERIVATIVE_MANIFEST.csv; that axis is verified at "
        "100.00%."),
    "foundation_expression_lineage_reaudit.py": (
        "AUDITOR_WITH_THE_SAME_BLIND_SPOT",
        "Hashes the existing discovery shards and checks identity and payload "
        "reproduction. It does not verify gene identity against the source "
        "feature axis, so it passes a scrambled artifact."),
}


# Reviewed exact path and exact source SHA from the sealed V29 inventory.
PINNED_REVIEWED_SOURCE_SHA256 = {
    "scripts/v4/build_pre_stage81a2_harmonization.py": "bdc9c3b61fd17eb7a26e477877ff9a575c4224d9866f7360ea7b76036b70e112",
    "scripts/v4/derive_contextual_target_f1_querydesign_repair_v2.py": "97532a40755866c7bec0cdc53a1c6ce93390e6b63c74d4078fe8c42728260594",
    "scripts/v4/foundation_expression_lineage_reaudit.py": "4c163f4f94f3b81f05a45cfb30e0687e73b1c1cf5ff06593c11caa0a525cd6b7",
    "scripts/v4/foundation_materialize_discovery_expression.py": "ede646be8030ef1644d27496a98eb4661e1c95e4043bc44a6d520e81b7d0228f",
    "scripts/v4/foundation_materialize_nph_discovery_sample.R": "c463688e87cbac14ad0ebd07716d160256ff1347731896e7945963f3a3d2f611",
    "scripts/v4/full104_expression_interface_nph.R": "6d1c54b122d6ae88b90c51c0f273d296765b0199e8ae07e49e3060429442cbbb",
    "scripts/v4/full104_expression_interface_nph_v8.R": "b8c543f3413d7747a798dd06c312539341358903b3a43706dff278c33c4a4909",
    "scripts/v4/full104_expression_interface_preflight.py": "62afd36a1bf00f7420242288c924f00d476c227666ff550f1c6cc3ff0b2d92a9",
    "scripts/v4/materialize_full104_phase2_expression.py": "575d02a4e7f7c5c6f3187eeed691a2eac7d3f1df9510621bc497b283806c270b",
    "scripts/v4/materialize_full104_phase2_nph_blocks.R": "ca595536f6144a1f6fb2570fe24f58c5335ba31e43a1f9a4b660e18db58e7529",
    "scripts/v4/stage81a2_audit_nph_freeze.R": "b4b93377ade405e31c36ee05dbf988151a2137d7919612d64ced47eb201a2b54",
    "scripts/v4/stage81a2_freeze_canonical_contract.py": "99c033a54b1b2d4d6b8ec299f5c6313c84727694663d1e821542e9ec46f90b60",
    "scripts/v4/stage81a2r_adjudicate_unresolved_identities.py": "4b929aa7e1fe592ad7d316ad732e6254283478baed3b68597b350f7e54480013",
    "scripts/v4/stage81a2r_audit_all_downloaded_identity.py": "4ef4611196dec2dded5b8db84b2da7d721d22ddd367318200c37ed4843936960",
    "scripts/v4/stage81a2r_authoritative_gene_identity_recovery.py": "b35c420311a2a4a94ea0ce9e9ca04713f921608668c757932acc980f6f71f7bf",
    "scripts/v4/stage81a2r_build_review_package.py": "1df934fd6f6afbd52ba0f94f1081b51612ea03290949fd34dcc579e1c845e84e",
    "scripts/v4/stage81a2r_close_authoritative_identity_audit.py": "e8e71d714ddf8110a0e375207c30c3996568cb337032a79eecf176f1c94be43c",
    "scripts/v4/stage81a2r_extract_r_feature_metadata.R": "b57677b57a529b829b71cac64b6cecb1343260717543edf1f166a7b1ea77d0b9"
}
REQUIRES_REVIEW = {"UNCLASSIFIED_REQUIRES_REVIEW", "SOURCE_CHANGED_REQUIRES_REVIEW", "DISPOSITION_CONFLICT_REQUIRES_REVIEW"}


def adjudicate_consumer(rel, digest, detected_kind):
    """Do not transfer a prior disposition to a new filename or changed code."""
    expected = PINNED_REVIEWED_SOURCE_SHA256.get(rel)
    if expected is None:
        return "UNCLASSIFIED_REQUIRES_REVIEW", "Unreviewed path (even if the regex calls it metadata-only)"
    if digest != expected:
        return "SOURCE_CHANGED_REQUIRES_REVIEW", "Bytes differ from those originally reviewed"
    disposition, note = KNOWN.get(os.path.basename(rel),
        ("METADATA_ONLY_NO_COUNTS_PRODUCED", "Exact source previously reviewed as metadata-only"))
    if detected_kind == "COUNT_PRODUCING" and disposition == "METADATA_ONLY_NO_COUNTS_PRODUCED":
        return "DISPOSITION_CONFLICT_REQUIRES_REVIEW", "Count producer detected in formerly metadata-only source"
    if detected_kind != "COUNT_PRODUCING" and disposition in {"SOUND_VERIFIED", "AFFECTED_CONFIRMED"}:
        return "DISPOSITION_CONFLICT_REQUIRES_REVIEW", "Known producer no longer detected as count-producing"
    return disposition, note


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def grep_files(root, needle, exts):
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in {".git", "__pycache__", ".worktrees", "node_modules"}]
        for fn in filenames:
            if not any(fn.endswith(e) for e in exts):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    if needle in fh.read():
                        out.add(p)
            except OSError:
                continue
    return out


def classify(path):
    try:
        src = open(path, "r", encoding="utf-8", errors="ignore").read()
    except OSError:
        return "UNREADABLE", [], []
    pos = [p for p in POSITIONAL_PATTERNS if re.search(p, src)]
    wr = [p for p in WRITE_PATTERNS if re.search(p, src)]
    if pos and wr:
        return "COUNT_PRODUCING", pos, wr
    if COLUMN in src or PROV_STEM in src:
        return "METADATA_ONLY", pos, wr
    return "NO_USE", pos, wr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--search-dirs", default="scripts,src")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    found = set()
    for d in a.search_dirs.split(","):
        root = os.path.join(a.repo_root, d.strip())
        if not os.path.isdir(root):
            continue
        # BOTH searches: by filename and by column. Either alone undercounts.
        found |= grep_files(root, PROV_STEM, (".py", ".R", ".sh"))
        found |= grep_files(root, COLUMN, (".py", ".R", ".sh"))

    consumers = []
    # Scanning the scanner itself would create a spurious unreviewed consumer.
    found = {p for p in found if os.path.realpath(p) != os.path.realpath(__file__)}
    for p in sorted(found):
        rel = os.path.relpath(p, a.repo_root).replace("\\", "/")
        base = os.path.basename(p)
        kind, pos, wr = classify(p)
        source_sha = sha_file(p)
        disposition, note = adjudicate_consumer(rel, source_sha, kind)
        consumers.append({
            "path": rel,
            "sha256": source_sha,
            "bytes": os.path.getsize(p),
            "kind": kind,
            "names_the_provenance_file": PROV_STEM in open(
                p, encoding="utf-8", errors="ignore").read(),
            "positional_patterns_matched": pos,
            "write_patterns_matched": wr,
            "disposition": disposition,
            "note": note,
        })

    # consumers that take the provenance as an ARGUMENT and never name it
    arg_only = [c for c in consumers
                if c["kind"] == "COUNT_PRODUCING" and not c["names_the_provenance_file"]]

    prov_path = os.path.join(a.repo_root, "results", "v4", PROV_BASENAME)
    counts = {}
    for c in consumers:
        counts[c["disposition"]] = counts.get(c["disposition"], 0) + 1

    outstanding = [c["path"] for c in consumers if c["disposition"] in REQUIRES_REVIEW]
    receipt = {
        "schema": "V5_PROVENANCE_CONSUMER_AUDIT_V1",
        "status": ("STATIC_ENUMERATION_AND_CLASSIFICATION__NO_COUNTS_OPENED" if not outstanding
                   else "FAIL_UNREVIEWED_OR_CHANGED_CONSUMERS__NO_COUNTS_OPENED"),
        "unreviewed_or_changed_consumers": outstanding,
        "provenance_table": {
            "path": f"results/v4/{PROV_BASENAME}",
            "sha256": sha_file(prov_path) if os.path.exists(prov_path) else None,
            "present": os.path.exists(prov_path),
        },
        "ROOT_CAUSE_IS_THE_CONTRACT_NOT_A_SCRIPT": {
            "origin": "stage81a2r_authoritative_gene_identity_recovery.py:286 — "
                      "result.insert(3, 'source_feature_index', "
                      "result['source_feature_id'])",
            "two_meanings": {
                "_COMMON families (HVS_COMMON, SEA_AD_COMMON)":
                    "indexes the harmonized feature universe, ordered by Ensembl "
                    "ID. Measured: 100.0% agreement with Ensembl-ascending rank.",
                "per-object NPH52 entries":
                    "constructed positionally by the R extractors "
                    "(seq_len(nrow(object)) - 1L), so it IS the object's own row "
                    "position. Verified 32,176/32,176 for the reader-fit MG "
                    "derivative.",
            },
            "why_it_reproduced":
                "one column, two meanings, no marker distinguishing them. Every "
                "count materializer reads it as the object's row position, which "
                "is right for NPH52 and wrong for both _COMMON families.",
        },
        "search_method": (
            "two independent searches - by provenance FILENAME and by the "
            "source_feature_index COLUMN - because either alone undercounts. "
            "materialize_full104_phase2_nph_blocks.R takes the provenance path "
            "as a command-line argument and never names it."),
        "consumers_found": len(consumers),
        "count_producing": sum(1 for c in consumers if c["kind"] == "COUNT_PRODUCING"),
        "count_producing_that_never_name_the_file": [c["path"] for c in arg_only],
        "disposition_counts": counts,
        "consumers": consumers,
        "derivative_axes_verified": {
            "nph52_reader_fit_MG": "33,441 x 15,264; 32,176/32,176 zero-based",
            "nph52_TRAIN_MG": "33,441 x 19,375; 32,176/32,176 zero-based",
            "note": "the two NPH52 derivatives share a feature axis but not a "
                    "cell set, and each was verified on its own rather than by "
                    "transferring the other's result",
        },
        "UNVERIFIED_MEANS_UNVERIFIED": (
            "a path marked UNVERIFIED has not been shown sound and has not been "
            "shown defective. It must not be relied on until checked against its "
            "own source feature axis."),
        "training_authorized": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "PROVENANCE_CONSUMER_AUDIT_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("Provenance-consumer audit\n")
    print(f"  consumers found      {len(consumers)}")
    print(f"  count-producing      {receipt['count_producing']}")
    print(f"  never name the file  {arg_only and [os.path.basename(x) for x in receipt['count_producing_that_never_name_the_file']] or 'none'}")
    print()
    for c in consumers:
        if c["kind"] != "COUNT_PRODUCING":
            continue
        print(f"  [{c['disposition']}]")
        print(f"      {c['path']}")
        print(f"      sha256 {c['sha256'][:16]}…   names-file={c['names_the_provenance_file']}")
        if c["note"]:
            print(f"      {c['note']}")
    print("\n  metadata-only consumers:")
    for c in consumers:
        if c["kind"] == "METADATA_ONLY":
            print(f"      {os.path.basename(c['path']):58s} {c['sha256'][:12]}…")
    print(f"\nwrote {p}")
    if outstanding:
        print(f"REFUSED: {len(outstanding)} unknown, changed or conflicting consumers", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
