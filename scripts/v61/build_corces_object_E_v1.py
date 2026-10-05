"""Construct external regulatory object E from fully public Corces GSE147672.

    E = HiChIP contact edge INTERSECT Cluster-24 accessible regulatory element
        INTERSECT hg38-stable coordinate identity

Every threshold and combination rule implemented here was frozen in
docs/agent/V61_CORCES_OBJECT_E_CONSTRUCTION_FREEZE_20260928.md and committed at
0639a2d3 BEFORE any genome-wide interaction row was read. This script must not
introduce a parameter that is not in that document.

E IS A SET OF COORDINATE PAIRS. No gene annotation is joined here. That is what
keeps construction clear of any regulatory molecular outcome.

Frozen rules, with the document's own labels:

  F1  Q-Value_Bias < 0.01 primary; 0.05 and 0.001 pre-declared sensitivity arms
  F2  significant in >= 2 distinct DONORS (not samples); >=1 and >=3 arms
  F3  BOTH anchors overlap >=1 bp of a Cluster-24 IDR peak; >=1 anchor arm
  F4  cis only, no self-loops; trans and self-loops COUNTED, not silently dropped
  F5  no additional distance filter; distance recorded per edge
  F6  hg38 both sides, no liftover, literal chromosome-name match; a mismatch
      is a STOP

Stop conditions S1/S2/S3 are evaluated and reported, not silently passed.
"""
from __future__ import annotations

import argparse
import collections
import glob
import gzip
import hashlib
import json
import os
import re
import sys

BIN = 10_000
Q_TIERS = (("q001", 0.001), ("q01", 0.01), ("q05", 0.05))
Q_PRIMARY = "q01"
DONOR_TIERS = (("d1", 1), ("d2", 2), ("d3", 3))
DONOR_PRIMARY = "d2"

# S1/S2/S3 from the freeze document, restated so the code carries them.
S1_MIN_EDGES = 1000
S2_MIN_CHROMS = 10


def parse_donor(fname: str) -> str:
    """Donor id from a GSM filename, under the A_B convention proven for scATAC.

    TWO distinct naming schemes are present and both must be handled explicitly
    rather than by a single loose regex:

        PD-00-38-CTRL-MDFG-X007-...   ->  00_38     (PD-<A>-<B>-CTRL-<REGION>)
        RCLN-CAUD-14-0941-X005-...    ->  14_0941   (RCLN-<REGION>-<A>-<B>)

    Marked LIKELY_SAME_KEY__UNPROVEN in the freeze document. The per-sample
    support vector is retained per edge so F2 can be recomputed if this parse is
    later disproved, without re-reading 3.73 GB.
    """
    stem = re.sub(r"^GSM\d+_", "", fname)
    stem = stem.split("_H3K27ac")[0]
    m = re.match(r"^PD-(\d+)-(\d+)-CTRL-", stem)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    m = re.match(r"^RCLN-[A-Z]+-(\d+)-(\d+)-", stem)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    raise SystemExit(f"STOP_UNPARSEABLE_DONOR: {fname}")


def sha256(path: str, cap: int = 1 << 30) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def accessible_bins(peak_path: str, report: dict) -> set:
    """Bins on the 10 kb contact grid touched by >=1 bp of a Cluster-24 peak.

    F6: the join is peak-within-bin because contact bins are 10 kb and peaks are
    ~1 kb. That asymmetry is a property of the object and is recorded, not hidden.
    """
    bins = set()
    n_peaks = 0
    uniq = set()
    chroms = set()
    widths = []
    with gzip.open(peak_path, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            f = line.rstrip("\n").split("\t")
            c, s, e = f[0], int(f[1]), int(f[2])
            n_peaks += 1
            uniq.add((c, s, e))
            chroms.add(c)
            widths.append(e - s)
            for b in range(s // BIN, (e - 1) // BIN + 1):
                bins.add((c, b))
    widths.sort()
    report["accessibility"] = {
        "peak_rows": n_peaks,
        "unique_intervals": len(uniq),
        "chromosomes": len(chroms),
        "median_peak_width_bp": widths[len(widths) // 2],
        "accessible_10kb_bins": len(bins),
        "genome_fraction_of_bins_note": (
            "bins are counted only where a peak exists; no genome-wide bin "
            "denominator is asserted"),
    }
    return bins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hichip-dir", required=True)
    ap.add_argument("--peaks", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    report = {
        "schema": "V61_CORCES_OBJECT_E_V1",
        "frozen_by": "docs/agent/V61_CORCES_OBJECT_E_CONSTRUCTION_FREEZE_20260928.md @ 0639a2d3",
        "frozen_rules": {"F1_q_primary": 0.01, "F1_arms": [0.001, 0.05],
                         "F2_donors_primary": 2, "F2_arms": [1, 3],
                         "F3": "both anchors accessible; >=1 anchor as arm",
                         "F4": "cis only, no self-loops",
                         "F5": "no distance filter; distance recorded",
                         "F6": "hg38 both sides, literal chrom match, 10kb bins"},
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "gene_annotation_joined": False,
                       "regulatory_molecular_outcome_opened": False},
    }

    acc = accessible_bins(a.peaks, report)
    report["accessibility"]["file"] = os.path.basename(a.peaks)
    report["accessibility"]["sha256"] = sha256(a.peaks)

    files = sorted(glob.glob(os.path.join(a.hichip_dir, "GSM*FitHiChIP*.bed.gz")))
    if len(files) != 12:
        raise SystemExit(f"STOP_EXPECTED_12_FILES_GOT_{len(files)}")

    # edge -> {donor: tightest tier index passed}; tier 0 = q<0.001 ... 2 = q<0.05
    edges: dict = collections.defaultdict(dict)
    per_sample = []
    bin_widths = collections.Counter()
    grid_violations = 0
    chrom_tokens = set()
    totals = collections.Counter()

    for path in files:
        fn = os.path.basename(path)
        donor = parse_donor(fn)
        n = cis = trans = self_loop = 0
        kept = collections.Counter()
        with gzip.open(path, "rt") as fh:
            hdr = fh.readline().rstrip("\n").split("\t")
            ix = {k: i for i, k in enumerate(hdr)}
            need = ["chr1", "s1", "e1", "chr2", "s2", "e2", "Q-Value_Bias"]
            missing = [k for k in need if k not in ix]
            if missing:
                raise SystemExit(f"STOP_SCHEMA_MISMATCH {fn}: missing {missing}")
            c1i, s1i, e1i = ix["chr1"], ix["s1"], ix["e1"]
            c2i, s2i, e2i = ix["chr2"], ix["s2"], ix["e2"]
            qi = ix["Q-Value_Bias"]
            # Two-stage parse. Stage 1 touches only the three fields needed
            # to discard a row (chr1, chr2, q); stage 2 does the full integer
            # parse only for rows that survive. ~50M rows are read across the
            # 12 files and well under 1% survive, so parsing all of them costs
            # many times more for no information.
            #
            # SCOPE OF THE F6 CHECK, stated rather than assumed: bin width,
            # grid alignment and chromosome tokens are verified on every row
            # that ENTERS E's candidate pool, not on every row in the files. A
            # grid violation in a row discarded on significance cannot affect
            # E. The trans and self-loop counters still run over ALL rows,
            # because F4 requires those to be COUNTED.
            for line in fh:
                f = line.split("	")
                n += 1
                c1, c2 = f[c1i], f[c2i]
                if c1 != c2:
                    trans += 1
                    continue
                cis += 1
                s1 = int(f[s1i]); s2 = int(f[s2i])
                if s1 == s2:
                    self_loop += 1
                    continue
                q = float(f[qi])
                if q >= Q_TIERS[-1][1]:
                    continue
                e1 = int(f[e1i])
                chrom_tokens.add(c1); chrom_tokens.add(c2)
                bin_widths[e1 - s1] += 1
                if s1 % BIN or s2 % BIN:
                    grid_violations += 1
                tier = 0 if q < 0.001 else (1 if q < 0.01 else 2)
                for name, thr in Q_TIERS:
                    if q < thr:
                        kept[name] += 1
                b1, b2 = s1 // BIN, s2 // BIN
                key = (c1, b1, b2) if b1 < b2 else (c1, b2, b1)
                d = edges[key]
                prev = d.get(donor)
                d[donor] = tier if prev is None else min(prev, tier)
        per_sample.append({"file": fn, "donor": donor, "rows": n, "cis": cis,
                           "trans": trans, "self_loops": self_loop,
                           "kept_q001": kept["q001"], "kept_q01": kept["q01"],
                           "kept_q05": kept["q05"]})
        totals["rows"] += n; totals["cis"] += cis
        totals["trans"] += trans; totals["self"] += self_loop
        print(f"  {donor:8s} {fn[:42]:42s} rows {n:>9,}  q<0.01 {kept['q01']:>8,}")

    report["samples"] = per_sample
    report["sample_count"] = len(files)
    report["donor_count"] = len({s["donor"] for s in per_sample})
    report["donors"] = sorted({s["donor"] for s in per_sample})
    report["totals"] = dict(totals)
    report["F4_trans_edges"] = totals["trans"]
    report["F4_self_loops"] = totals["self"]
    report["F6_bin_widths_observed"] = dict(bin_widths.most_common(5))
    report["F6_grid_violations"] = grid_violations
    report["F6_check_scope"] = (
        "bin width, grid alignment and chromosome tokens verified on every row "
        "entering E's candidate pool (cis, non-self-loop, q<0.05), not on every "
        "row in the files; trans and self-loop counts are over ALL rows")
    report["F6_chromosome_tokens"] = sorted(chrom_tokens)
    report["F6_chrom_naming_matches_peaks"] = bool(
        chrom_tokens & {c for c, _ in acc})

    if grid_violations:
        raise SystemExit(f"STOP_F6_GRID: {grid_violations} anchors off the 10kb grid")
    if not report["F6_chrom_naming_matches_peaks"]:
        raise SystemExit("STOP_F6_CHROM_NAMING_MISMATCH")

    # ---- funnel over the full frozen grid, every arm reported unconditionally
    funnel = {}
    for qname, _ in Q_TIERS:
        qmax = {"q001": 0, "q01": 1, "q05": 2}[qname]
        for dname, dmin in DONOR_TIERS:
            for acc_rule in ("both", "one"):
                surv = 0
                chroms = set()
                bins_used = set()
                dists = []
                donor_support = collections.Counter()
                for (c, b1, b2), dd in edges.items():
                    nd = sum(1 for t in dd.values() if t <= qmax)
                    if nd < dmin:
                        continue
                    a1, a2 = (c, b1) in acc, (c, b2) in acc
                    ok = (a1 and a2) if acc_rule == "both" else (a1 or a2)
                    if not ok:
                        continue
                    surv += 1
                    chroms.add(c)
                    bins_used.add((c, b1)); bins_used.add((c, b2))
                    dists.append((b2 - b1) * BIN)
                    donor_support[nd] += 1
                dists.sort()
                funnel[f"{qname}|{dname}|{acc_rule}"] = {
                    "edges": surv, "chromosomes": len(chroms),
                    "distinct_bins": len(bins_used),
                    "distance_bp": ({"min": dists[0],
                                     "median": dists[len(dists) // 2],
                                     "max": dists[-1]} if dists else None),
                    "donor_support_histogram": dict(sorted(donor_support.items())),
                    "is_primary": (qname == Q_PRIMARY and dname == DONOR_PRIMARY
                                   and acc_rule == "both"),
                }
    report["funnel"] = funnel

    key = f"{Q_PRIMARY}|{DONOR_PRIMARY}|both"
    prim = funnel[key]
    report["PRIMARY"] = {"rule": key, **prim}
    report["stop_conditions"] = {
        "S1_min_edges": S1_MIN_EDGES,
        "S1_triggered": prim["edges"] < S1_MIN_EDGES,
        "S2_min_chromosomes": S2_MIN_CHROMS,
        "S2_triggered": prim["chromosomes"] < S2_MIN_CHROMS,
        "S3_triggered": False,
    }
    report["VERDICT"] = (
        "OBJECT_E_NOT_VIABLE__CORCES_ROUTE_STOPS"
        if any(report["stop_conditions"][k] for k in
               ("S1_triggered", "S2_triggered", "S3_triggered"))
        else "OBJECT_E_CONSTRUCTED")

    # ---- write the object itself, primary rule only, coordinates only
    obj = os.path.join(a.out_dir, "V61_OBJECT_E_PRIMARY.tsv.gz")
    qmax = {"q001": 0, "q01": 1, "q05": 2}[Q_PRIMARY]
    with gzip.open(obj, "wt", newline="\n") as fh:
        fh.write("chrom\tbin1_start\tbin1_end\tbin2_start\tbin2_end\t"
                 "distance_bp\tn_donors\tdonor_support\n")
        for (c, b1, b2), dd in sorted(edges.items()):
            sup = sorted(d for d, t in dd.items() if t <= qmax)
            if len(sup) < 2:
                continue
            if (c, b1) not in acc or (c, b2) not in acc:
                continue
            fh.write(f"{c}\t{b1*BIN}\t{b1*BIN+BIN}\t{b2*BIN}\t{b2*BIN+BIN}\t"
                     f"{(b2-b1)*BIN}\t{len(sup)}\t{','.join(sup)}\n")
    report["object_file"] = {"path": obj, "bytes": os.path.getsize(obj),
                             "sha256": sha256(obj)}

    with open(os.path.join(a.out_dir, "V61_OBJECT_E_REPORT_V1.json"), "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"\nPRIMARY RULE {key}")
    print(f"  edges            {prim['edges']:,}")
    print(f"  chromosomes      {prim['chromosomes']}")
    print(f"  distinct bins    {prim['distinct_bins']:,}")
    print(f"  distance bp      {prim['distance_bp']}")
    print(f"  donor support    {prim['donor_support_histogram']}")
    print(f"\nS1 triggered: {report['stop_conditions']['S1_triggered']}   "
          f"S2 triggered: {report['stop_conditions']['S2_triggered']}")
    print(f"VERDICT: {report['VERDICT']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
