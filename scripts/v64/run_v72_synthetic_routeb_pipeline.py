#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha256(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_metadata(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_barcode = {}
    for r in rows:
        if r["barcode"] in by_barcode:
            raise ValueError("DUPLICATE_BARCODE")
        by_barcode[r["barcode"]] = (r["donor"], r["subcluster"])
    return by_barcode


def region_for_fragment(start: int, end: int, width=500):
    mid = (int(start) + int(end)) // 2
    bin_start = (mid // width) * width
    return bin_start, bin_start + width


def run(challenge_root: Path, out_dir: Path):
    scenic = challenge_root / "observable_raw/SCENICPLUS_LIKE"
    metadata = load_metadata(scenic / "metadata.csv")

    suffix_to_donors = defaultdict(set)
    for bc, (donor, _) in metadata.items():
        suffix_to_donors[bc.rsplit("-", 1)[-1]].add(donor)
    if not any(len(v) > 1 for v in suffix_to_donors.values()):
        raise ValueError("SUFFIX_COLLISION_POSITIVE_CONTROL_ABSENT")

    out_dir.mkdir(parents=True, exist_ok=True)
    pseudobulk_dir = out_dir / "pseudobulk"
    pseudobulk_dir.mkdir(exist_ok=True)

    handles = {}
    counts = defaultdict(int)
    donor_regions = defaultdict(set)
    out_of_cohort = 0
    scanned = 0

    try:
        with gzip.open(scenic / "fragments.tsv.gz", "rt", encoding="utf-8") as fh:
            for line in fh:
                f = line.rstrip("\n").split("\t")
                if len(f) != 5:
                    raise ValueError("FRAGMENT_FIELD_COUNT")
                chrom, start, end, barcode, count = f
                scanned += 1
                meta = metadata.get(barcode)
                if meta is None:
                    out_of_cohort += 1
                    continue
                donor, subcluster = meta
                key = f"{donor}__{subcluster}"
                if key not in handles:
                    handles[key] = open(
                        pseudobulk_dir / f"PSEUDOBULK_{key}.bed",
                        "w", encoding="utf-8", newline="\n"
                    )
                # MACS BEDPE semantics are represented by the actual fragment interval.
                handles[key].write(f"{chrom}\t{start}\t{end}\n")
                counts[key] += 1
                rs, re = region_for_fragment(int(start), int(end))
                donor_regions[donor].add((chrom, rs, re))
    finally:
        for handle in handles.values():
            handle.close()

    pseudobulks = {}
    for key in sorted(handles):
        p = pseudobulk_dir / f"PSEUDOBULK_{key}.bed"
        with open(p, encoding="utf-8") as fh:
            n_lines = sum(1 for _ in fh)
        if n_lines != counts[key]:
            raise ValueError(f"PSEUDOBULK_REREAD_MISMATCH:{key}")
        donor, subcluster = key.split("__", 1)
        pseudobulks[key] = {
            "donor": donor,
            "subcluster": subcluster,
            "n_fragments": n_lines,
            "path": str(p),
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        }

    # Deterministic CI peak-call adapter: fixed 500-bp bins hit by fragments.
    # This proves the raw→pseudobulk→region-universe interface and donor recurrence.
    all_regions = sorted(set().union(*donor_regions.values())) if donor_regions else []
    consensus_path = out_dir / "V72_ROUTE_B_CI_CONSENSUS_REGIONS.bed"
    recurrence_path = out_dir / "V72_ROUTE_B_CI_CONSENSUS_RECURRENCE.csv"
    with open(consensus_path, "w", encoding="utf-8", newline="\n") as bed, \
         open(recurrence_path, "w", encoding="utf-8", newline="") as csvfh:
        w = csv.writer(csvfh)
        w.writerow(["region", "chrom", "start", "end", "n_donors", "fraction_donors"])
        donors = sorted(donor_regions)
        for chrom, start, end in all_regions:
            n = sum((chrom, start, end) in donor_regions[d] for d in donors)
            name = f"{chrom}:{start}-{end}"
            bed.write(f"{chrom}\t{start}\t{end}\t{name}\n")
            w.writerow([name, chrom, start, end, n, n / len(donors)])

    # Re-read derived outputs before writing PASS.
    consensus_lines = [
        x.rstrip("\n").split("\t")
        for x in open(consensus_path, encoding="utf-8")
        if x.strip()
    ]
    if len(consensus_lines) != len(all_regions):
        raise ValueError("CONSENSUS_REREAD_MISMATCH")
    recurrence_rows = list(csv.DictReader(open(recurrence_path, encoding="utf-8")))
    if len(recurrence_rows) != len(all_regions):
        raise ValueError("RECURRENCE_REREAD_MISMATCH")

    receipt = {
        "schema": "V72_SYNTHETIC_ROUTEB_CI_RECEIPT_V1",
        "status": "PASS__RAW_TO_CONSENSUS_INTERFACE_QUALIFIED",
        "is_macrophysical_peak_caller": False,
        "peak_calling_adapter": "DETERMINISTIC_500BP_FRAGMENT_HIT_BINNING_FOR_SMALL_CI_ONLY",
        "real_routeb_still_requires_macs_pycistopic": True,
        "donor_identity_source": "EXPLICIT_METADATA_JOIN",
        "barcode_suffix_inference_forbidden": True,
        "fragment_records_scanned": scanned,
        "out_of_cohort_records_counted_and_discarded": out_of_cohort,
        "n_pseudobulks": len(pseudobulks),
        "pseudobulks": pseudobulks,
        "consensus": {
            "n_regions": len(all_regions),
            "recurrence_filter_applied": False,
            "bed_path": str(consensus_path),
            "bed_sha256": sha256(consensus_path),
            "recurrence_path": str(recurrence_path),
            "recurrence_sha256": sha256(recurrence_path),
        },
        "outputs_verified_by_reread": True,
    }
    receipt_path = out_dir / "V72_SYNTHETIC_ROUTEB_CI_RECEIPT_V1.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("challenge_root")
    ap.add_argument("out_dir")
    a = ap.parse_args()
    r = run(Path(a.challenge_root), Path(a.out_dir))
    print(json.dumps({k: v for k, v in r.items() if k != "pseudobulks"}, indent=2))


if __name__ == "__main__":
    main()
