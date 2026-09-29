#!/usr/bin/env python3
"""V64 Nott C3 descriptive liftover + provenance auditor.

This executor performs only the mechanical evidence collection already required by
the frozen C3 lineage. It intentionally DOES NOT emit a C3 PASS/FAIL because the
authority chain still lacks:
  1) a numeric interval-length-change tolerance;
  2) a required exact round-trip recovery fraction.

It uses UCSC command-line liftOver with the prospectively frozen implementation
defaults on this parallel lane:
  - minMatch=0.95
  - no -multiple
  - no nearest-neighbour rescue

Inputs:
  * Nott interaction TSV/TSV.GZ with the first six fields representing
    chr1,start1,end1,chr2,start2,end2 unless overridden.
  * authenticated hg19->hg38 and hg38->hg19 chain files.
  * zero or more six-column FILER ATAC tracks where columns 1-3 are FILER hg38
    and columns 4-6 are retained source coordinates.

Outputs:
  * denominator-preserving JSON receipt;
  * mapped/unmapped intermediate BEDs under --out-dir.

No biological outcome, target identity, AD locus, Morabito, or NIH-CARD
correspondence is read.

TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


def open_text(path):
    return gzip.open(path, "rt", newline="") if str(path).endswith(".gz") else open(path, "rt", newline="")


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_colspec(spec):
    idx = [int(x) for x in spec.split(",")]
    if len(idx) != 6 or min(idx) < 1:
        raise SystemExit("STOP_BAD_CONTACT_COLSPEC")
    return [x - 1 for x in idx]


def read_contacts(path, cols, delimiter="\t", skip_header=1):
    rows = []
    malformed = 0
    with open_text(path) as fh:
        r = csv.reader(fh, delimiter=delimiter)
        for i, row in enumerate(r, start=1):
            if i <= skip_header:
                continue
            try:
                c1, s1, e1, c2, s2, e2 = [row[j] for j in cols]
                s1, e1, s2, e2 = map(int, (s1, e1, s2, e2))
                if e1 <= s1 or e2 <= s2:
                    raise ValueError
            except Exception:
                malformed += 1
                continue
            rows.append({
                "pair_index": len(rows),
                "source_row_number": i,
                "a1": (c1, s1, e1),
                "a2": (c2, s2, e2),
            })
    return rows, malformed


def write_anchor_bed(contacts, path):
    with open(path, "w", newline="") as fh:
        for p in contacts:
            for ai in (1, 2):
                chrom, start, end = p[f"a{ai}"]
                ident = f"P{p['pair_index']:09d}_A{ai}"
                fh.write(f"{chrom}\t{start}\t{end}\t{ident}\n")


def read_bed_by_id(path):
    out = defaultdict(list)
    if not os.path.exists(path):
        return out
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 4:
                continue
            try:
                rec = (f[0], int(f[1]), int(f[2]))
            except ValueError:
                continue
            out[f[3]].append(rec)
    return out


def read_unmapped_ids(path):
    ids = []
    if not os.path.exists(path):
        return ids
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) >= 4:
                ids.append(f[3])
    return ids


def run_liftover(exe, source_bed, chain, mapped_bed, unmapped_bed, min_match):
    cmd = [exe, f"-minMatch={min_match}", source_bed, chain, mapped_bed, unmapped_bed]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    if cp.returncode != 0:
        raise SystemExit(
            "STOP_LIFTOVER_FAILED\n"
            + " ".join(cmd)
            + "\nSTDOUT:\n" + cp.stdout
            + "\nSTDERR:\n" + cp.stderr
        )
    return {"command": cmd, "stdout": cp.stdout, "stderr": cp.stderr}


def anchor_id(pair_index, ai):
    return f"P{pair_index:09d}_A{ai}"


def contact_forward_summary(contacts, mapped, unmapped_ids):
    unmapped = set(unmapped_ids)
    pair_rows = []
    counts = Counter()
    length_deltas = []
    chrom_changes = []
    ambiguous = []

    for p in contacts:
        rec = {"pair_index": p["pair_index"], "source_row_number": p["source_row_number"]}
        accepted = True
        for ai in (1, 2):
            ident = anchor_id(p["pair_index"], ai)
            src = p[f"a{ai}"]
            vals = mapped.get(ident, [])
            if len(vals) == 0:
                rec[f"a{ai}_status"] = "UNMAPPED"
                counts["unmapped_anchors"] += 1
                accepted = False
                continue
            if len(vals) != 1:
                rec[f"a{ai}_status"] = "AMBIGUOUS_MULTIPLE_OUTPUTS"
                counts["ambiguous_anchors"] += 1
                ambiguous.append(ident)
                accepted = False
                continue
            dst = vals[0]
            rec[f"a{ai}_mapped"] = dst
            rec[f"a{ai}_status"] = "MAPPED"
            counts["mapped_anchors_single"] += 1
            if dst[0] != src[0]:
                counts["chromosome_changed_anchors"] += 1
                chrom_changes.append((ident, src[0], dst[0]))
                accepted = False
            delta = (dst[2] - dst[1]) - (src[2] - src[1])
            rec[f"a{ai}_length_delta_bp"] = delta
            length_deltas.append(delta)

        if accepted:
            counts["pairs_both_anchors_single_same_chromosome"] += 1
            rec["retained_for_roundtrip_descriptive"] = True
        else:
            counts["pairs_not_retained_for_roundtrip"] += 1
            rec["retained_for_roundtrip_descriptive"] = False
        pair_rows.append(rec)

    n = len(contacts)
    counts["pairs_attempted"] = n
    counts["anchors_attempted"] = 2 * n
    counts["unmapped_ids_listed_by_liftOver"] = len(unmapped)
    return pair_rows, counts, length_deltas, chrom_changes, ambiguous


def write_mapped_for_reverse(pair_rows, path):
    original = {}
    with open(path, "w") as fh:
        for p in pair_rows:
            if not p.get("retained_for_roundtrip_descriptive"):
                continue
            for ai in (1, 2):
                ident = anchor_id(p["pair_index"], ai)
                chrom, start, end = p[f"a{ai}_mapped"]
                fh.write(f"{chrom}\t{start}\t{end}\t{ident}\n")
                original[ident] = None
    return original


def source_anchor_map(contacts):
    out = {}
    for p in contacts:
        out[anchor_id(p["pair_index"], 1)] = p["a1"]
        out[anchor_id(p["pair_index"], 2)] = p["a2"]
    return out


def roundtrip_summary(pair_rows, source_by_id, reverse_mapped, reverse_unmapped):
    eligible_pairs = [p for p in pair_rows if p.get("retained_for_roundtrip_descriptive")]
    counts = Counter()
    pair_exact = 0
    deltas = []
    for p in eligible_pairs:
        exact_pair = True
        for ai in (1, 2):
            ident = anchor_id(p["pair_index"], ai)
            vals = reverse_mapped.get(ident, [])
            if len(vals) != 1:
                exact_pair = False
                counts["roundtrip_anchor_not_single"] += 1
                continue
            got = vals[0]
            src = source_by_id[ident]
            if got == src:
                counts["roundtrip_anchor_exact"] += 1
            else:
                exact_pair = False
                counts["roundtrip_anchor_discordant"] += 1
                if got[0] == src[0]:
                    deltas.append((got[1] - src[1], got[2] - src[2]))
                else:
                    counts["roundtrip_anchor_chromosome_changed"] += 1
        if exact_pair:
            pair_exact += 1
    counts["roundtrip_pairs_attempted"] = len(eligible_pairs)
    counts["roundtrip_pairs_exact_both_anchors"] = pair_exact
    counts["roundtrip_unmapped_ids_listed_by_liftOver"] = len(reverse_unmapped)
    return counts, deltas


def read_six_col_atac(path):
    rows = []
    malformed = 0
    with open_text(path) as fh:
        r = csv.reader(fh, delimiter="\t")
        for i, row in enumerate(r, start=1):
            if not row or row[0].startswith("#"):
                continue
            try:
                if len(row) < 6:
                    raise ValueError
                ref = (row[0], int(row[1]), int(row[2]))
                src = (row[3], int(row[4]), int(row[5]))
                if ref[2] <= ref[1] or src[2] <= src[1]:
                    raise ValueError
            except Exception:
                malformed += 1
                continue
            rows.append((i, ref, src))
    return rows, malformed


def atac_provenance_audit(exe, path, chain, out_dir, min_match):
    name = Path(path).name.replace(".gz", "").replace(".", "_")
    rows, malformed = read_six_col_atac(path)
    src_bed = os.path.join(out_dir, f"{name}.source_hg19.bed")
    mapped_bed = os.path.join(out_dir, f"{name}.relift_hg38.bed")
    unmapped_bed = os.path.join(out_dir, f"{name}.relift_unmapped.bed")

    ref_by_id = {}
    src_by_id = {}
    with open(src_bed, "w") as fh:
        for j, (rownum, ref, src) in enumerate(rows):
            ident = f"R{j:09d}"
            fh.write(f"{src[0]}\t{src[1]}\t{src[2]}\t{ident}\n")
            ref_by_id[ident] = ref
            src_by_id[ident] = src

    run_liftover(exe, src_bed, chain, mapped_bed, unmapped_bed, min_match)
    mapped = read_bed_by_id(mapped_bed)
    unmapped = read_unmapped_ids(unmapped_bed)

    c = Counter()
    coord_deltas = []
    length_deltas = []
    for ident, ref in ref_by_id.items():
        vals = mapped.get(ident, [])
        if len(vals) == 0:
            c["unmapped"] += 1
            continue
        if len(vals) != 1:
            c["ambiguous"] += 1
            continue
        got = vals[0]
        c["successfully_relifted_single"] += 1
        length_deltas.append((got[2] - got[1]) - (src_by_id[ident][2] - src_by_id[ident][1]))
        if got == ref:
            c["exact_interval_match"] += 1
        elif got[0] == ref[0]:
            c["same_chromosome_coordinate_discordant"] += 1
            coord_deltas.append((got[1] - ref[1], got[2] - ref[2]))
        else:
            c["chromosome_discordant"] += 1

    denom = len(rows) + malformed
    c["rows_attempted_valid"] = len(rows)
    c["malformed_rows"] = malformed
    c["original_denominator"] = denom
    c["liftOver_unmapped_ids"] = len(unmapped)

    return {
        "file": str(path),
        "sha256": sha256(path),
        "counts": dict(c),
        "fractions_original_denominator": {
            "successfully_relifted_single": c["successfully_relifted_single"] / max(1, denom),
            "exact_interval_match": c["exact_interval_match"] / max(1, denom),
            "same_chromosome_coordinate_discordant": c["same_chromosome_coordinate_discordant"] / max(1, denom),
            "unmapped": c["unmapped"] / max(1, denom),
        },
        "length_delta_bp_summary": summarize_ints(length_deltas),
        "coordinate_delta_bp_summary": summarize_pairs(coord_deltas),
    }


def summarize_ints(vals):
    if not vals:
        return {"n": 0}
    vals = sorted(vals)
    n = len(vals)
    def q(frac):
        return vals[min(n - 1, int(frac * (n - 1)))]
    return {
        "n": n,
        "min": vals[0],
        "p25": q(0.25),
        "median": q(0.50),
        "p75": q(0.75),
        "max": vals[-1],
        "n_zero": sum(v == 0 for v in vals),
    }


def summarize_pairs(vals):
    if not vals:
        return {"n": 0}
    starts = [x for x, _ in vals]
    ends = [y for _, y in vals]
    return {"n": len(vals), "start_delta": summarize_ints(starts), "end_delta": summarize_ints(ends)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contacts", required=True)
    ap.add_argument("--contact-cols", default="1,2,3,4,5,6",
                    help="1-based chr1,start1,end1,chr2,start2,end2 columns")
    ap.add_argument("--skip-header", type=int, default=1)
    ap.add_argument("--hg19-to-hg38-chain", required=True)
    ap.add_argument("--hg38-to-hg19-chain", required=True)
    ap.add_argument("--liftover-exe", default="liftOver")
    ap.add_argument("--min-match", type=float, default=0.95)
    ap.add_argument("--atac", action="append", default=[],
                    help="repeat for PU1/NeuN/Olig2 six-column FILER tracks")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    if args.min_match != 0.95:
        raise SystemExit("STOP_MINMATCH_NOT_FROZEN_0.95")
    if not (0 < args.min_match <= 1):
        raise SystemExit("STOP_BAD_MINMATCH")
    if os.path.exists(args.out_dir) and os.listdir(args.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(args.out_dir, exist_ok=True)

    exe = shutil.which(args.liftover_exe) or args.liftover_exe
    cols = parse_colspec(args.contact_cols)
    contacts, malformed = read_contacts(
        args.contacts, cols, skip_header=args.skip_header
    )
    if len(contacts) != 104802:
        raise SystemExit(
            f"STOP_CONTACT_DENOMINATOR_MISMATCH parsed={len(contacts)} malformed={malformed} expected=104802"
        )

    source_bed = os.path.join(args.out_dir, "nott_contacts_hg19_anchors.bed")
    forward_bed = os.path.join(args.out_dir, "nott_contacts_hg38_anchors.bed")
    forward_unmapped = os.path.join(args.out_dir, "nott_contacts_hg19_to_hg38_unmapped.bed")
    write_anchor_bed(contacts, source_bed)
    fwd_cmd = run_liftover(
        exe, source_bed, args.hg19_to_hg38_chain,
        forward_bed, forward_unmapped, args.min_match
    )
    mapped = read_bed_by_id(forward_bed)
    unmapped_ids = read_unmapped_ids(forward_unmapped)
    pair_rows, fwd_counts, length_deltas, chrom_changes, ambiguous = contact_forward_summary(
        contacts, mapped, unmapped_ids
    )

    reverse_source = os.path.join(args.out_dir, "nott_contacts_hg38_for_roundtrip.bed")
    write_mapped_for_reverse(pair_rows, reverse_source)
    reverse_bed = os.path.join(args.out_dir, "nott_contacts_roundtrip_hg19.bed")
    reverse_unmapped = os.path.join(args.out_dir, "nott_contacts_hg38_to_hg19_unmapped.bed")
    rev_cmd = run_liftover(
        exe, reverse_source, args.hg38_to_hg19_chain,
        reverse_bed, reverse_unmapped, args.min_match
    )
    reverse_mapped = read_bed_by_id(reverse_bed)
    reverse_unmapped_ids = read_unmapped_ids(reverse_unmapped)
    rt_counts, rt_deltas = roundtrip_summary(
        pair_rows, source_anchor_map(contacts), reverse_mapped, reverse_unmapped_ids
    )

    atac_receipts = [
        atac_provenance_audit(
            exe, p, args.hg19_to_hg38_chain, args.out_dir, args.min_match
        )
        for p in args.atac
    ]

    attempted = fwd_counts["pairs_attempted"]
    retained = fwd_counts["pairs_both_anchors_single_same_chromosome"]
    rt_attempted = rt_counts["roundtrip_pairs_attempted"]
    rt_exact = rt_counts["roundtrip_pairs_exact_both_anchors"]

    out = {
        "schema": "V64_NOTT_C3_DESCRIPTIVE_LIFTOVER_AUDIT_V1",
        "date": "2026-09-29",
        "status": "DESCRIPTIVE_EVIDENCE_ONLY__C3_PASS_FAIL_NOT_EMITTED",
        "governance": {
            "training": "OFF",
            "td60": "BLOCKED",
            "protected_outcomes_opened": False,
        },
        "inputs": {
            "contacts": {
                "path": args.contacts,
                "sha256": sha256(args.contacts),
                "pairs_expected_and_parsed": 104802,
            },
            "hg19_to_hg38_chain": {
                "path": args.hg19_to_hg38_chain,
                "sha256": sha256(args.hg19_to_hg38_chain),
            },
            "hg38_to_hg19_chain": {
                "path": args.hg38_to_hg19_chain,
                "sha256": sha256(args.hg38_to_hg19_chain),
            },
            "liftover_executable": exe,
            "minMatch": args.min_match,
            "multiple": False,
        },
        "forward_contact_liftover": {
            "counts": dict(fwd_counts),
            "pair_retention_fraction_original_denominator": retained / attempted,
            "anchor_length_delta_bp": summarize_ints(length_deltas),
            "chromosome_change_examples_first20": chrom_changes[:20],
            "ambiguous_anchor_ids_first20": ambiguous[:20],
            "command": fwd_cmd["command"],
        },
        "roundtrip": {
            "counts": dict(rt_counts),
            "exact_pair_fraction_forward_retained_denominator":
                rt_exact / max(1, rt_attempted),
            "exact_pair_fraction_original_104802_denominator":
                rt_exact / 104802,
            "coordinate_delta_bp_for_nonexact_same_chromosome":
                summarize_pairs(rt_deltas),
            "command": rev_cmd["command"],
        },
        "ATAC_source_coordinate_provenance": atac_receipts,
        "qualification": {
            "C3_pass": None,
            "reason": (
                "The authority chain requires a predeclared interval-length-change "
                "tolerance and a required round-trip exact-recovery fraction; neither "
                "numeric value is currently frozen. This receipt must not manufacture "
                "those values after seeing the evidence."
            ),
            "still_missing": [
                "interval_length_change_tolerance_bp",
                "required_roundtrip_exact_recovery_fraction",
            ],
        },
    }
    out_path = os.path.join(args.out_dir, "V64_NOTT_C3_DESCRIPTIVE_LIFTOVER_AUDIT_V1.json")
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({
        "pairs_attempted": attempted,
        "pairs_forward_retained": retained,
        "forward_retention_fraction": retained / attempted,
        "roundtrip_pairs_attempted": rt_attempted,
        "roundtrip_pairs_exact": rt_exact,
        "roundtrip_exact_fraction_forward_retained": rt_exact / max(1, rt_attempted),
        "C3_pass": None,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
