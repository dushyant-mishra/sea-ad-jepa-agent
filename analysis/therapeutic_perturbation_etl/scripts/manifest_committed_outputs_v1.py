#!/usr/bin/env python3
"""Emit and verify a full content manifest for committed perturbation outputs.

Every file under `analysis/therapeutic_perturbation_etl/outputs/` is recorded by
repo-relative path, exact byte size, full 64-character SHA-256 of its bytes, the
commit and tree it was manifested at, and the producer or regeneration path that
created it.

Two rules this exists to enforce, because both have been violated in this
project before:

  * **A Git blob SHA is not a file SHA-256.** Git hashes `blob <len>\\0<bytes>`
    with SHA-1 (or SHA-256 in a sha256 repository), so it never equals the
    SHA-256 of the file contents. The blob id is recorded separately and
    explicitly labelled, so nobody can mistake one for the other.
  * **A 16-character prefix is not a digest.** Earlier documents in this
    directory quoted truncated digests. Truncation is fine for reading; it is
    not fine for verification, and no full hash here is ever reconstructed from
    a prefix. Every digest below was computed from the bytes on disk.

`--mode verify` fails closed on a missing file, an unmanifested extra file, a
byte-size mismatch or a digest mismatch, and is intended to run in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

OUTPUTS_REL = "analysis/therapeutic_perturbation_etl/outputs"
MANIFEST_REL = ("analysis/therapeutic_perturbation_etl/evidence/"
                "COMMITTED_OUTPUTS_SHA256_MANIFEST_V1.json")

# Producer or regeneration path for each committed output. A file with no entry
# is refused at emit time rather than recorded with unknown provenance.
PROVENANCE = {
    "gse178317/gse178317_cell_guide_umi_counts_v2.npz": {
        "producer": "scripts/recover_gse178317_guide_assignments_v2.py --stage count",
        "regeneration": ("streams 221,434,278 spots from SRA runs SRR14828091-94, "
                         "about 47 minutes; requires sra-toolkit vdb-dump"),
        "kind": "binary",
    },
    "gse178317/gse178317_cell_guide_assignments_v2.csv.gz": {
        "producer": "scripts/recover_gse178317_guide_assignments_v2.py --stage call",
        "regeneration": "seconds, from the committed count NPZ",
        "kind": "binary",
    },
    "gse178317/gse178317_target_engagement_v2.csv": {
        "producer": "scripts/build_gse178317_intervention_effects_v2.py",
        "regeneration": "from committed assignments plus deposited GEX h5",
        "kind": "text",
    },
    "gse178317/gse178317_top_effects_v2.csv.gz": {
        "producer": "scripts/build_gse178317_intervention_effects_v2.py",
        "regeneration": "from committed assignments plus deposited GEX h5",
        "kind": "binary",
    },
    "gse178317/gse178317_vs_crisprbrain_engagement_v1.csv": {
        "producer": "scripts/validate_gse178317_against_crisprbrain_v1.py (FAIL-CLOSED)",
        "regeneration": ("superseded; the authoritative comparison is "
                         "scripts/compare_gse178317_vs_crisprbrain_support_qualified_v3.py"),
        "kind": "text",
    },
    "crisprbrain/iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz": {
        "producer": "scripts/acquire_crisprbrain_screens_v1.py",
        "regeneration": "pip install crisprbrain; refetch, minutes",
        "kind": "binary",
    },
    "crisprbrain/iTF-Microglia-CROP-seq-CRISPRi.csv.gz": {
        "producer": "scripts/acquire_crisprbrain_screens_v1.py",
        "regeneration": "pip install crisprbrain; refetch, minutes",
        "kind": "binary",
    },
    "crisprbrain/iPSC-Microglia-CROP-seq-CRISPRi.csv.gz": {
        "producer": "scripts/acquire_crisprbrain_screens_v1.py",
        "regeneration": "pip install crisprbrain; refetch, minutes",
        "kind": "binary",
    },
    "crisprbrain/iTF-Microglia-CITE-seq-CRISPRi.csv.gz": {
        "producer": "scripts/acquire_crisprbrain_screens_v1.py",
        "regeneration": "pip install crisprbrain; refetch, minutes",
        "kind": "binary",
    },
    "crisprbrain/iPSC-Microglia-CITE-seq-CRISPRi.csv.gz": {
        "producer": "scripts/acquire_crisprbrain_screens_v1.py",
        "regeneration": "pip install crisprbrain; refetch, minutes",
        "kind": "binary",
    },
    "README.md": {
        "producer": "authored",
        "regeneration": "n/a",
        "kind": "text",
    },
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    d = h.hexdigest()
    if len(d) != 64:
        raise SystemExit("digest is not 64 characters: %r" % d)
    return d


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def scan(repo):
    root = os.path.join(repo, OUTPUTS_REL)
    if not os.path.isdir(root):
        raise SystemExit("outputs root not found: %s" % root)
    found = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            found[rel] = full
    return found


def emit(repo, out_path):
    found = scan(repo)
    missing_prov = sorted(set(found) - set(PROVENANCE))
    if missing_prov:
        raise SystemExit(
            "no provenance entry for: %s; refusing to record an output with "
            "unknown provenance" % ", ".join(missing_prov))

    entries = []
    for rel in sorted(found):
        full = found[rel]
        size = os.path.getsize(full)
        digest = sha256_file(full)
        repo_rel = "%s/%s" % (OUTPUTS_REL, rel)
        try:
            blob = git(repo, "rev-parse", "HEAD:%s" % repo_rel)
        except subprocess.CalledProcessError:
            blob = None
        p = PROVENANCE[rel]
        entries.append({
            "path": repo_rel,
            "bytes": size,
            "sha256": digest,
            "git_blob_id_NOT_A_CONTENT_SHA256": blob,
            "kind": p["kind"],
            "producer": p["producer"],
            "regeneration": p["regeneration"],
        })

    manifest = {
        "schema": "PERTURBATION_COMMITTED_OUTPUTS_SHA256_MANIFEST_V1",
        "outputs_root": OUTPUTS_REL,
        "commit": git(repo, "rev-parse", "HEAD"),
        "tree": git(repo, "rev-parse", "HEAD^{tree}"),
        "file_count": len(entries),
        "total_bytes": sum(e["bytes"] for e in entries),
        "digest_rules": {
            "sha256_is_of_file_bytes": True,
            "git_blob_id_is_not_a_content_sha256": (
                "git hashes 'blob <len>\\0<bytes>', so the blob id never equals "
                "the SHA-256 of the contents; it is recorded only to locate the "
                "object"),
            "no_digest_inferred_from_a_prefix": (
                "every digest here was computed from the bytes on disk; "
                "truncated prefixes appearing in prose are for reading only"),
        },
        "files": entries,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print("manifested %d files, %s bytes" % (len(entries),
                                             f"{manifest['total_bytes']:,}"))
    for e in entries:
        print("  %-62s %10d  %s" % (e["path"].split("outputs/")[-1],
                                    e["bytes"], e["sha256"]))
    print("\nwrote %s" % out_path)
    return 0


def verify(repo, manifest_path):
    with open(manifest_path) as fh:
        manifest = json.load(fh)
    found = scan(repo)
    manifested = {e["path"].split("outputs/", 1)[1]: e for e in manifest["files"]}

    problems = []
    for rel in sorted(set(manifested) - set(found)):
        problems.append("MISSING          %s" % rel)
    for rel in sorted(set(found) - set(manifested)):
        problems.append("UNMANIFESTED     %s" % rel)
    for rel in sorted(set(found) & set(manifested)):
        e = manifested[rel]
        size = os.path.getsize(found[rel])
        if size != e["bytes"]:
            problems.append("SIZE MISMATCH    %s  manifest %d, on disk %d"
                            % (rel, e["bytes"], size))
            continue
        d = sha256_file(found[rel])
        if d != e["sha256"]:
            problems.append("DIGEST MISMATCH  %s\n                   manifest %s"
                            "\n                   on disk  %s"
                            % (rel, e["sha256"], d))

    if problems:
        print("=== VERDICT: FAIL ===")
        for p in problems:
            print("  " + p)
        return 1
    print("=== VERDICT: PASS ===")
    print("  %d files verified, %s bytes, all sizes and SHA-256 digests match"
          % (len(found), f"{sum(os.path.getsize(v) for v in found.values()):,}"))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["emit", "verify"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--manifest", default=None)
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    path = a.manifest or os.path.join(repo, MANIFEST_REL)
    return emit(repo, path) if a.mode == "emit" else verify(repo, path)


if __name__ == "__main__":
    sys.exit(main())
