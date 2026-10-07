#!/usr/bin/env python
"""LANE D - artifact receipts.

Records every Lane D output by absolute path, byte size and SHA-256. Compact
artifacts are committed to git; heavy matrices are referenced here by digest
rather than duplicated into the repository.
"""
import argparse
import csv
import hashlib
import os

COMMITTED = {
    "laneD_file_authentication_v1.csv",
    "laneD_recorded_shape_checks_v1.csv",
    "laneD_stage75f_authentication_v1.csv",
    "laneD_sample_donor_overlap_v1.csv",
    "laneD_physical_asset_inventory_v1.csv",
    "laneD_duplicate_copy_scan_v1.csv",
    "laneD_missing_resource_acquisition_plan_v1.csv",
    "laneD_gene_collision_register_v1.csv",
    "laneD_provenance_manifest_v1.json",
    "laneD_coordinate_map_audit_v1.json",
    "laneD_peak_to_gene_manifest_v1.json",
    "laneD_environment_and_asset_manifest_v1.json",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipts-path", required=True)
    a = ap.parse_args()
    rows = []
    for fn in sorted(os.listdir(a.out_dir)):
        if fn.startswith("_"):
            continue
        p = os.path.join(a.out_dir, fn)
        if not os.path.isfile(p):
            continue
        committed = fn in COMMITTED
        rows.append(dict(
            artifact=fn,
            absolute_path=p.replace(os.sep, "/"),
            size_bytes=os.path.getsize(p),
            sha256=sha256(p),
            committed_to_git=committed,
            disposition=("committed" if committed else
                         "referenced_by_path_size_sha256_not_committed")))
    os.makedirs(os.path.dirname(a.receipts_path), exist_ok=True)
    with open(a.receipts_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} receipts -> {a.receipts_path}")
    for r in rows:
        if not r["committed_to_git"]:
            print(f"  HEAVY {r['artifact']}  {r['size_bytes']}  {r['sha256'][:16]}...")


if __name__ == "__main__":
    main()
