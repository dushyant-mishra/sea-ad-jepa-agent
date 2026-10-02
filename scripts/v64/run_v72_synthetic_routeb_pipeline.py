#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path, gz: bool = False):
    opener = gzip.open if gz else open
    with opener(path, "rt", newline="") as fh:
        return list(csv.DictReader(fh))


def suffix_collision_guard(rows):
    suffix = defaultdict(set)
    for r in rows:
        suffix[r["barcode"].rsplit("-", 1)[-1]].add(r["donor"])
    collisions = {k: sorted(v) for k, v in suffix.items() if len(v) > 1}
    if not collisions:
        raise ValueError("FAIL__NO_SUFFIX_COLLISION_POSITIVE_CONTROL")
    return collisions


def run(scenic_root: Path, out_root: Path, min_bin_count: int = 2) -> dict:
    metadata = read_csv(scenic_root / "metadata.csv.gz", gz=True)
    authority = read_csv(scenic_root / "barcode_to_donor.csv")
    auth = {r["barcode"]: r["donor"] for r in authority}
    collisions = suffix_collision_guard(authority)

    meta = {}
    for r in metadata:
        bc = r["barcode"]
        if bc not in auth:
            raise ValueError(f"FAIL__METADATA_BARCODE_NOT_IN_AUTHORITY:{bc}")
        if auth[bc] != r["donor"]:
            raise ValueError(f"FAIL__DONOR_AUTHORITY_MISMATCH:{bc}")
        meta[bc] = r

    out_root.mkdir(parents=True, exist_ok=True)
    pseudobulk_dir = out_root / "pseudobulk"
    pseudobulk_dir.mkdir(exist_ok=True)

    handles = {}
    counts = Counter()
    bins = defaultdict(Counter)
    records = 0
    with gzip.open(scenic_root / "fragments.tsv.gz", "rt") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 5:
                raise ValueError("FAIL__MALFORMED_FRAGMENT")
            chrom, start_s, end_s, bc, count_s = f[:5]
            if bc not in meta:
                raise ValueError(f"FAIL__FRAGMENT_BARCODE_NOT_IN_AUTHORITY:{bc}")
            r = meta[bc]
            key = f"{r['donor']}__{r['subcluster']}"
            if key not in handles:
                handles[key] = open(pseudobulk_dir / f"{key}.bed", "w", newline="\n")
            start, end, count = int(start_s), int(end_s), int(count_s)
            handles[key].write(f"{chrom}\t{start}\t{end}\n")
            counts[key] += 1
            # deterministic synthetic peak-caller fixture: fixed 500-bp coverage bins.
            bstart = (start // 500) * 500
            bins[key][(chrom, bstart, bstart + 500)] += count
            records += 1

    for h in handles.values():
        h.close()

    pseudobulks = {}
    called = {}
    for key in sorted(handles):
        bed = pseudobulk_dir / f"{key}.bed"
        n_disk = sum(1 for _ in open(bed))
        if n_disk != counts[key]:
            raise ValueError(f"FAIL__PSEUDOBULK_REREAD_COUNT:{key}")
        pseudobulks[key] = {
            "path": str(bed),
            "records": n_disk,
            "sha256": sha256_file(bed),
        }
        called[key] = sorted([
            interval for interval, coverage in bins[key].items()
            if coverage >= min_bin_count
        ])

    peak_dir = out_root / "synthetic_peak_calls"
    peak_dir.mkdir(exist_ok=True)
    peak_meta = {}
    all_intervals = set()
    for key in sorted(called):
        p = peak_dir / f"{key}.bed"
        with open(p, "w", newline="\n") as fh:
            for chrom, start, end in called[key]:
                fh.write(f"{chrom}\t{start}\t{end}\n")
                all_intervals.add((chrom, start, end))
        peak_meta[key] = {
            "path": str(p),
            "n_peaks": len(called[key]),
            "sha256": sha256_file(p),
        }

    # Synthetic consensus adapter: union exact 500-bp bins, then donor recurrence.
    donor_by_key = {key: key.split("__", 1)[0] for key in called}
    donors = sorted(set(donor_by_key.values()))
    consensus = []
    for interval in sorted(all_intervals):
        donor_hits = {
            donor_by_key[key]
            for key, intervals in called.items()
            if interval in intervals
        }
        consensus.append((*interval, len(donor_hits), len(donor_hits)/max(len(donors), 1)))

    consensus_path = out_root / "consensus_regions.bed"
    with open(consensus_path, "w", newline="\n") as fh:
        for chrom, start, end, _, _ in consensus:
            fh.write(f"{chrom}\t{start}\t{end}\n")

    recurrence_path = out_root / "consensus_recurrence.csv"
    with open(recurrence_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["chrom","start","end","n_donors","fraction_donors"])
        w.writerows(consensus)

    receipt = {
        "schema": "V72_SYNTHETIC_ROUTEB_PIPELINE_RECEIPT_V1",
        "status": "PASS__SYNTHETIC_ROUTEB_PIPELINE",
        "scientific_scope": "INTERFACE_AND_ETL_QUALIFICATION_ONLY__NOT_MACS_OR_REAL_PEAK_CALLING",
        "donor_identity": {
            "authority": "barcode_to_donor.csv",
            "suffix_inference_forbidden": True,
            "suffix_collision_positive_control": collisions,
        },
        "pseudobulk_unit": "donor x subcluster",
        "records_scanned": records,
        "n_pseudobulks": len(pseudobulks),
        "pseudobulks": pseudobulks,
        "synthetic_peak_caller": {
            "method": "fixed 500-bp coverage bins",
            "min_bin_count": min_bin_count,
            "why_not_macs": "CI fixture qualifies routing, identity, disk custody and consensus interfaces. Real Route-B uses pycisTopic/MACS on Macha's execution lane.",
            "per_pseudobulk": peak_meta,
        },
        "consensus": {
            "n_regions": len(consensus),
            "recurrence_filter_applied": False,
            "bed": str(consensus_path),
            "bed_sha256": sha256_file(consensus_path),
            "recurrence_table": str(recurrence_path),
            "recurrence_sha256": sha256_file(recurrence_path),
        }
    }
    (out_root / "ROUTEB_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenic-root", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--min-bin-count", type=int, default=2)
    a = ap.parse_args(argv)
    r = run(Path(a.scenic_root), Path(a.out_root), a.min_bin_count)
    print(json.dumps({k:v for k,v in r.items() if k != "pseudobulks"}, indent=2))


if __name__ == "__main__":
    main()
