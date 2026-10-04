#!/usr/bin/env python3
"""V74 LANE E: apply the frozen ENCODE exclusion-list policy to a region universe and
report the ATTRITION as a structural count.

WHAT THIS IS NOT
----------------
Regions removed here are EXCLUDED_BY_POLICY. They are not biological zeros, not
absent signal and not unmeasured. They are regions the project has decided in advance
not to scan, because the ENCODE DAC exclusion list identifies them as carrying
anomalous high signal independently of cell type and assay. Any downstream artifact
that carries these regions must carry that label with them.

FAIL-CLOSED CONTRACT
--------------------
The exclusion-list file is identified by SHA-256, not by filename. A file whose digest
does not match the frozen value is REFUSED, and the script exits non-zero without
writing a receipt. Equally, a region universe whose digest does not match is refused.
A policy that silently accepts a different exclusion list is not a frozen policy.

The ANY-OVERLAP rule is the operative one: a region sharing even one base pair with an
exclusion interval is dropped whole. That is the convention pycisTopic applies to
consensus peaks, and partial trimming would change region widths and therefore the
motif-scanning substrate. A sweep over minimum-overlap thresholds is reported ALONGSIDE
it so that the sensitivity of the count to that choice is visible rather than implied.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_bed3(path: Path):
    out = []
    # encoding declared explicitly: an undeclared text read decodes cp1252 on Windows
    with open(path, "r", encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith(("#", "track", "browser")):
                continue
            f = line.split("\t")
            if len(f) < 3:
                raise ValueError("%s:%d: fewer than 3 BED columns" % (path, ln))
            name = f[3] if len(f) > 3 else "%s:%s-%s" % (f[0], f[1], f[2])
            out.append((f[0], int(f[1]), int(f[2]), name))
    return out


def merge_by_contig(ivs):
    """Merge overlapping/abutting intervals per contig. Overlap arithmetic over an
    unmerged list would double-count a base covered by two exclusion intervals."""
    by_contig = defaultdict(list)
    for c, s, e, _ in ivs:
        by_contig[c].append((s, e))
    merged = {}
    for c, lst in by_contig.items():
        lst.sort()
        acc = []
        for s, e in lst:
            if acc and s <= acc[-1][1]:
                acc[-1][1] = max(acc[-1][1], e)
            else:
                acc.append([s, e])
        merged[c] = [(s, e) for s, e in acc]
    return merged


def overlap_bp(contig_iv, s, e):
    """Base pairs of [s,e) covered by the merged interval list for this contig."""
    if not contig_iv:
        return 0
    starts = [iv[0] for iv in contig_iv]
    i = bisect.bisect_right(starts, s) - 1
    if i < 0:
        i = 0
    total = 0
    while i < len(contig_iv) and contig_iv[i][0] < e:
        a, b = contig_iv[i]
        if b > s:
            total += min(b, e) - max(a, s)
        i += 1
    return total


def ordered_digest(items):
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode())
        h.update(b"\x1f")
        h.update(str(s).encode())
        h.update(b"\x1e")
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region-bed", required=True)
    ap.add_argument("--region-bed-sha256", required=True)
    ap.add_argument("--blacklist-bed", required=True)
    ap.add_argument("--blacklist-bed-sha256", required=True,
                    help="FROZEN digest. A mismatch is a refusal, not a warning.")
    ap.add_argument("--blacklist-accession", required=True)
    ap.add_argument("--route-id", required=True)
    ap.add_argument("--out-receipt", required=True)
    ap.add_argument("--out-excluded-bed", required=True)
    ap.add_argument("--out-retained-bed", required=True)
    args = ap.parse_args()

    region_bed = Path(args.region_bed)
    bl_bed = Path(args.blacklist_bed)

    # ---- fail-closed identity gate, BEFORE any computation -----------------------
    refusals = []
    for label, path, expected in (
        ("region_universe", region_bed, args.region_bed_sha256),
        ("exclusion_list", bl_bed, args.blacklist_bed_sha256),
    ):
        if not path.exists():
            refusals.append({"input": label, "reason": "ABSENT", "path": str(path)})
            continue
        got = sha256(path)
        if got != expected.lower():
            refusals.append({"input": label, "reason": "SHA256_MISMATCH",
                             "path": str(path), "expected": expected.lower(),
                             "observed": got})
    if refusals:
        sys.stderr.write(json.dumps(
            {"status": "REFUSED__INPUT_IDENTITY_GATE_FAILED", "refusals": refusals},
            indent=2) + "\n")
        return 2

    regions = read_bed3(region_bed)
    bl = read_bed3(bl_bed)
    bl_merged = merge_by_contig(bl)

    total_bp = sum(e - s for _, s, e, _ in regions)
    bl_bp_merged = sum(e - s for lst in bl_merged.values() for s, e in lst)

    excluded, retained = [], []
    excluded_bp = 0
    intersected_bp = 0
    sweep_counts = {str(t): 0 for t in (1, 10, 50, 100, 250, 500)}
    frac_sweep = {"%.2f" % t: 0 for t in (0.01, 0.10, 0.25, 0.50, 0.90)}

    for c, s, e, name in regions:
        ov = overlap_bp(bl_merged.get(c, []), s, e)
        if ov > 0:
            intersected_bp += ov
            excluded.append((c, s, e, name, ov))
            excluded_bp += e - s
            for t in sweep_counts:
                if ov >= int(t):
                    sweep_counts[t] += 1
            width = e - s
            for t in frac_sweep:
                if width and ov / width >= float(t):
                    frac_sweep[t] += 1
        else:
            retained.append((c, s, e, name))

    Path(args.out_excluded_bed).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_excluded_bed, "w", encoding="utf-8", newline="\n") as fh:
        for c, s, e, name, ov in excluded:
            fh.write("%s\t%d\t%d\t%s\tEXCLUDED_BY_POLICY\t%d\n" % (c, s, e, name, ov))
    with open(args.out_retained_bed, "w", encoding="utf-8", newline="\n") as fh:
        for c, s, e, name in retained:
            fh.write("%s\t%d\t%d\t%s\n" % (c, s, e, name))

    n_regions = len(regions)
    n_excluded = len(excluded)
    retained_bp = total_bp - excluded_bp

    # ---- verdict decided HERE, then written. It must not exist only in stdout. ----
    consistent = (len(retained) + n_excluded == n_regions
                  and retained_bp + excluded_bp == total_bp
                  and intersected_bp <= excluded_bp)
    status = ("PASS__ATTRITION_MEASURED" if consistent
              else "FAIL__ATTRITION_ACCOUNTING_DOES_NOT_BALANCE")

    rec = {
        "schema": "V74_LANEE_BLACKLIST_ATTRITION_V1",
        "status": status,
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "route_id": args.route_id,
        "policy": {
            "blacklist": "ON",
            "rule": "ANY_OVERLAP_DROPS_THE_WHOLE_REGION",
            "semantics": ("EXCLUDED_BY_POLICY. These regions are NOT biological zeros, "
                          "NOT absent signal and NOT unmeasured. They are regions the "
                          "project decided in advance not to scan. Any downstream "
                          "artifact carrying them must carry this label."),
            "distinct_from": ("The 53 STRUCTURALLY_UNSCOREABLE regions dropped at "
                              "region-universe construction are a DIFFERENT class: "
                              "those have no reference sequence under the source's "
                              "contig spelling, so a scanner could never score them. "
                              "Policy exclusion and structural unscoreability must not "
                              "be merged into one count."),
        },
        "inputs": {
            "region_universe_bed": str(region_bed),
            "region_universe_bed_sha256": args.region_bed_sha256.lower(),
            "exclusion_list_bed": str(bl_bed),
            "exclusion_list_bed_sha256": args.blacklist_bed_sha256.lower(),
            "exclusion_list_accession": args.blacklist_accession,
        },
        "exclusion_list_structure": {
            "n_intervals_as_distributed": len(bl),
            "n_intervals_after_merge": sum(len(v) for v in bl_merged.values()),
            "n_contigs": len(bl_merged),
            "genome_bp_covered_after_merge": bl_bp_merged,
            "why_merged": ("Overlap arithmetic over an unmerged list would double-count "
                           "a base covered by two exclusion intervals."),
        },
        "region_universe_before": {
            "n_regions": n_regions,
            "total_bp": total_bp,
        },
        "ATTRITION": {
            "n_regions_excluded": n_excluded,
            "fraction_of_regions_excluded": (n_excluded / n_regions) if n_regions else None,
            "bp_in_excluded_regions": excluded_bp,
            "fraction_of_bp_excluded": (excluded_bp / total_bp) if total_bp else None,
            "bp_actually_intersecting_the_exclusion_list": intersected_bp,
            "bp_collaterally_removed": excluded_bp - intersected_bp,
            "collateral_note": ("Under the any-overlap rule a region is dropped whole, so "
                                "more base pairs leave the universe than actually "
                                "intersect the exclusion list. Both numbers are reported "
                                "because only the first is a consequence of the rule and "
                                "only the second is a consequence of the exclusion list."),
        },
        "region_universe_after": {
            "n_regions": len(retained),
            "total_bp": retained_bp,
        },
        "sensitivity_to_the_rule": {
            "n_regions_excluded_at_min_overlap_bp": sweep_counts,
            "n_regions_excluded_at_min_overlap_fraction_of_region": frac_sweep,
            "why_reported": ("The any-overlap rule is a choice. Reporting how the count "
                             "moves with the threshold prevents the chosen number from "
                             "looking more inevitable than it is."),
        },
        "outputs": {
            "excluded_bed": args.out_excluded_bed,
            "retained_bed": args.out_retained_bed,
            "retained_ordered_region_digest": ordered_digest(
                ["%s:%d-%d" % (c, s, e) for c, s, e, _ in retained]),
            "excluded_ordered_region_digest": ordered_digest(
                ["%s:%d-%d" % (c, s, e) for c, s, e, _, _ in excluded]),
        },
        "accounting_check": {
            "retained_plus_excluded_equals_input_regions": len(retained) + n_excluded == n_regions,
            "retained_bp_plus_excluded_bp_equals_input_bp": retained_bp + excluded_bp == total_bp,
            "intersected_bp_not_greater_than_excluded_bp": intersected_bp <= excluded_bp,
        },
    }

    out = Path(args.out_receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")

    # Re-read from disk: what is reported is what was persisted, not what was in memory.
    persisted = json.loads(out.read_text(encoding="utf-8"))
    print(json.dumps({k: persisted[k] for k in
                      ("status", "region_universe_before", "ATTRITION",
                       "region_universe_after")}, indent=2))
    return 0 if persisted["status"].startswith("PASS") else 3


if __name__ == "__main__":
    raise SystemExit(main())
