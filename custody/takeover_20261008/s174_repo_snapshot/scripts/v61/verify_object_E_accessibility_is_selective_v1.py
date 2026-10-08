"""Does F3 do real work, or would almost any contact edge pass it?

E is microglial ONLY because of F3 -- the requirement that both anchors overlap
a Cluster-24 accessible element. The contact layer carries no microglial
information: FitHiChIP was run 'peak-to-all' using peaks from the
one-dimensional HiChIP data, which is bulk. So if F3 passes nearly every
candidate edge, E is not a microglial object at all and the whole construction
is decorative.

This is a self-audit check on my own object, of the kind the project requires:
a filter that cannot fail is the defect it is supposed to prevent.

Two measurements, both unconditional:

  1. THE FUNNEL AT THE ACCESSIBILITY STEP. Of all q<0.01, >=2-donor candidate
     edges, how many have both anchors accessible, exactly one, or neither?
     If 'both' is near 100%, F3 is not a filter.

  2. A DISTANCE-MATCHED NULL. For every surviving edge, draw random bin pairs
     on the SAME chromosome at the SAME distance and ask how often both bins
     are accessible. This is the rate F3 would pass by chance given the
     accessible-bin marginal and the distance distribution. Observed / null is
     the enrichment.

     Distance matching matters because accessible bins are clustered, so nearby
     bin pairs are both-accessible far more often than distant ones. An
     unmatched null would overstate the enrichment.

No gene annotation is joined. No real cohort measurement is used.
"""
from __future__ import annotations

import argparse
import collections
import glob
import gzip
import json
import os
import re
import sys

import numpy as np

BIN = 10_000
Q_PRIMARY = 0.01
DONOR_MIN = 2
DRAWS_PER_EDGE = 20


def parse_donor(fname: str) -> str:
    stem = re.sub(r"^GSM\d+_", "", fname).split("_H3K27ac")[0]
    m = re.match(r"^PD-(\d+)-(\d+)-CTRL-", stem)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    m = re.match(r"^RCLN-[A-Z]+-(\d+)-(\d+)-", stem)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    raise SystemExit(f"STOP_UNPARSEABLE_DONOR: {fname}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hichip-dir", required=True)
    ap.add_argument("--peaks", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=20260928)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    acc = set()
    with gzip.open(a.peaks, "rt") as fh:
        for line in fh:
            f = line.split("\t")
            c, s, e = f[0], int(f[1]), int(f[2])
            for b in range(s // BIN, (e - 1) // BIN + 1):
                acc.add((c, b))

    files = sorted(glob.glob(os.path.join(a.hichip_dir, "GSM*FitHiChIP*.bed.gz")))
    if len(files) != 12:
        raise SystemExit(f"STOP_EXPECTED_12_FILES_GOT_{len(files)}")

    edges: dict = collections.defaultdict(set)
    chrom_max_bin: dict = collections.defaultdict(int)
    for path in files:
        donor = parse_donor(os.path.basename(path))
        with gzip.open(path, "rt") as fh:
            hdr = fh.readline().rstrip("\n").split("\t")
            ix = {k: i for i, k in enumerate(hdr)}
            c1i, s1i, c2i, s2i = ix["chr1"], ix["s1"], ix["chr2"], ix["s2"]
            qi = ix["Q-Value_Bias"]
            for line in fh:
                f = line.split("\t")
                if f[c1i] != f[c2i]:
                    continue
                if float(f[qi]) >= Q_PRIMARY:
                    continue
                s1 = int(f[s1i]); s2 = int(f[s2i])
                if s1 == s2:
                    continue
                b1, b2 = s1 // BIN, s2 // BIN
                c = f[c1i]
                if b2 > chrom_max_bin[c]:
                    chrom_max_bin[c] = b2
                edges[(c, min(b1, b2), max(b1, b2))].add(donor)
        print(f"  read {os.path.basename(path)[:38]}", flush=True)

    both = one = neither = 0
    surviving = []
    for (c, b1, b2), dd in edges.items():
        if len(dd) < DONOR_MIN:
            continue
        a1, a2 = (c, b1) in acc, (c, b2) in acc
        if a1 and a2:
            both += 1
            surviving.append((c, b1, b2))
        elif a1 or a2:
            one += 1
        else:
            neither += 1
    cand = both + one + neither

    rng = np.random.default_rng(a.seed)
    by_chrom = collections.defaultdict(list)
    for c, b1, b2 in surviving:
        by_chrom[c].append(b2 - b1)
    null_hits = null_tot = 0
    per_chrom = {}
    for c, gaps in by_chrom.items():
        hi = chrom_max_bin[c]
        g = np.array(gaps)
        hits = tot = 0
        for _ in range(DRAWS_PER_EDGE):
            starts = rng.integers(0, np.maximum(hi - g, 1))
            for s, gg in zip(starts.tolist(), gaps):
                tot += 1
                if (c, s) in acc and (c, s + gg) in acc:
                    hits += 1
        per_chrom[c] = {"edges": len(gaps), "null_rate": hits / tot if tot else None}
        null_hits += hits
        null_tot += tot

    null_rate = null_hits / null_tot
    obs_rate = both / cand
    out = {
        "schema": "V61_OBJECT_E_ACCESSIBILITY_SELECTIVITY_V1",
        "question": "Does F3 (both anchors accessible in Cluster 24) actually filter?",
        "rule": {"q": Q_PRIMARY, "min_donors": DONOR_MIN, "draws_per_edge": DRAWS_PER_EDGE},
        "accessible_bins": len(acc),
        "funnel_at_the_accessibility_step": {
            "candidate_edges_q01_d2": cand,
            "both_anchors_accessible": both,
            "exactly_one_accessible": one,
            "neither_accessible": neither,
            "observed_both_rate": round(obs_rate, 6),
        },
        "distance_matched_null": {
            "draws": null_tot,
            "null_both_rate": round(null_rate, 6),
            "enrichment_observed_over_null": round(obs_rate / null_rate, 4) if null_rate else None,
            "per_chromosome": {k: {"edges": v["edges"],
                                  "null_rate": round(v["null_rate"], 6)}
                               for k, v in sorted(per_chrom.items())},
        },
        "interpretation_rule_declared_before_the_numbers_were_read": (
            "F3 is doing real work if the observed both-accessible rate is "
            "materially below 1.0 (so it rejects candidates) AND materially "
            "above the distance-matched null (so what it keeps is not what "
            "chance would keep). Both must hold. A high rate alone would mean "
            "the filter passes everything; an enrichment alone would not rule "
            "out that it rejects nothing."),
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "gene_annotation_joined": False},
    }
    out["F3_REJECTS"] = bool(obs_rate < 0.90)
    out["F3_IS_ENRICHED"] = bool(null_rate and obs_rate / null_rate > 1.5)
    out["VERDICT"] = ("F3_IS_A_REAL_FILTER" if out["F3_REJECTS"] and out["F3_IS_ENRICHED"]
                      else "F3_IS_NOT_DOING_THE_WORK_E_IS_NOT_MICROGLIAL")

    with open(os.path.join(a.out_dir, "V61_OBJECT_E_SELECTIVITY_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\ncandidates q<0.01, >=2 donors : {cand:,}")
    print(f"  both anchors accessible     : {both:,}  ({100*obs_rate:.2f}%)")
    print(f"  exactly one                 : {one:,}")
    print(f"  neither                     : {neither:,}")
    print(f"distance-matched null rate    : {100*null_rate:.2f}%")
    print(f"ENRICHMENT                    : {obs_rate/null_rate:.2f}x")
    print(f"VERDICT: {out['VERDICT']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
