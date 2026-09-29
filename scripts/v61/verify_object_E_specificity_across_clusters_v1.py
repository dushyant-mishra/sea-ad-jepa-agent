"""Is E's accessibility enrichment MICROGLIAL, or just REGULATORY?

The V61 result showed F3 keeps 29.78% of candidate contact edges against a
5.10% distance-matched null -- a 5.84x enrichment. That establishes F3 filters.
It does NOT establish that what it selects is microglial.

The alternative explanation, stated in the V61 result document before this test
was written: H3K27ac HiChIP anchors may be enriched for open chromatin in ANY
cell type, so 5.84x could reflect generic regulatory activity. If a neuronal or
oligodendrocyte peak set gives a similar enrichment, E's microglial specificity
claim has to be weakened.

DESIGN

  One pass over the contact data builds the candidate edge set ONCE. Candidates
  do not depend on the mask, so every cluster is scored against exactly the same
  edges.

  The distance-matched null uses COMMON RANDOM NUMBERS: the random bin pairs are
  drawn once and every mask is evaluated on the identical pairs. This is the
  project's standing preference for comparing conditions and it removes
  between-mask Monte Carlo noise from the comparison entirely.

  Masks are chosen so that Cluster24 is NOT extreme in peak count -- it sits
  third of five (27,693 / 47,211 / 54,330 / 64,594 / 70,389). A result cannot
  then be explained by the microglial mask being the largest or smallest.

INTERPRETATION RULE, declared before the numbers exist:

  If Cluster24's enrichment is within the spread of the non-microglial masks,
  the enrichment is GENERIC and E's specificity claim must be weakened to
  "contact edges at accessible regulatory elements" without the microglial
  qualifier. If Cluster24 is clearly highest, the microglial reading survives.
  Either way the number is reported; neither outcome is a failure of the object,
  only of a particular claim about it.
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
DRAWS_PER_EDGE = 10


def parse_donor(fname: str) -> str:
    stem = re.sub(r"^GSM\d+_", "", fname).split("_H3K27ac")[0]
    m = re.match(r"^PD-(\d+)-(\d+)-CTRL-", stem)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    m = re.match(r"^RCLN-[A-Z]+-(\d+)-(\d+)-", stem)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    raise SystemExit(f"STOP_UNPARSEABLE_DONOR: {fname}")


def load_mask(path: str):
    bins = set()
    uniq = set()
    with gzip.open(path, "rt") as fh:
        for line in fh:
            f = line.split("\t")
            c, s, e = f[0], int(f[1]), int(f[2])
            uniq.add((c, s, e))
            for b in range(s // BIN, (e - 1) // BIN + 1):
                bins.add((c, b))
    return bins, len(uniq)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hichip-dir", required=True)
    ap.add_argument("--peak-dir", required=True)
    ap.add_argument("--clusters", default="1,9,15,23,24")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=20260928)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    masks = {}
    for c in a.clusters.split(","):
        p = os.path.join(a.peak_dir, f"Cluster{c}.idr.optimal.narrowPeak.gz")
        if not os.path.exists(p):
            raise SystemExit(f"STOP_MISSING_MASK: {p}")
        bins, nu = load_mask(p)
        masks[f"Cluster{c}"] = {"bins": bins, "unique_intervals": nu}
        print(f"  mask Cluster{c}: {nu:,} intervals -> {len(bins):,} bins", flush=True)

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
            c1i, s1i, c2i, s2i, qi = (ix["chr1"], ix["s1"], ix["chr2"],
                                      ix["s2"], ix["Q-Value_Bias"])
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

    cand = [(c, b1, b2) for (c, b1, b2), dd in edges.items() if len(dd) >= DONOR_MIN]
    print(f"\ncandidate edges q<{Q_PRIMARY}, >={DONOR_MIN} donors: {len(cand):,}", flush=True)

    # COMMON RANDOM NUMBERS: one set of distance-matched random pairs, reused
    # for every mask, so between-mask differences cannot be Monte Carlo noise.
    rng = np.random.default_rng(a.seed)
    null_pairs = []
    by_chrom = collections.defaultdict(list)
    for c, b1, b2 in cand:
        by_chrom[c].append(b2 - b1)
    for c, gaps in by_chrom.items():
        hi = chrom_max_bin[c]
        g = np.array(gaps)
        for _ in range(DRAWS_PER_EDGE):
            starts = rng.integers(0, np.maximum(hi - g, 1))
            for s, gg in zip(starts.tolist(), gaps):
                null_pairs.append((c, int(s), int(s) + gg))
    print(f"common null pairs: {len(null_pairs):,}", flush=True)

    results = {}
    for name, m in masks.items():
        acc = m["bins"]
        both = sum(1 for c, b1, b2 in cand if (c, b1) in acc and (c, b2) in acc)
        nhit = sum(1 for c, x, y in null_pairs if (c, x) in acc and (c, y) in acc)
        obs = both / len(cand)
        null = nhit / len(null_pairs)
        results[name] = {
            "unique_intervals": m["unique_intervals"],
            "accessible_bins": len(acc),
            "both_anchors_accessible": both,
            "observed_rate": round(obs, 6),
            "null_rate": round(null, 6),
            "enrichment": round(obs / null, 4) if null else None,
        }
        print(f"  {name:11s} intervals {m['unique_intervals']:>6,}  both {both:>7,}"
              f"  obs {100*obs:5.2f}%  null {100*null:5.2f}%  ENRICH {obs/null:5.2f}x",
              flush=True)

    mg = results["Cluster24"]["enrichment"]
    others = {k: v["enrichment"] for k, v in results.items() if k != "Cluster24"}
    out = {
        "schema": "V61_OBJECT_E_CROSS_CLUSTER_SPECIFICITY_V1",
        "question": "Is E's accessibility enrichment microglial, or generic regulatory?",
        "design": {
            "candidate_edges": len(cand),
            "candidates_are_mask_independent": True,
            "common_random_numbers": True,
            "null_pairs": len(null_pairs),
            "draws_per_edge": DRAWS_PER_EDGE,
            "masks_ranked_by_peak_count": sorted(
                ((v["unique_intervals"], k) for k, v in results.items())),
            "cluster24_is_not_extreme_in_peak_count": True,
        },
        "cell_types": {"Cluster1": "ExcitatoryNeurons (Isocortical)",
                       "Cluster9": "OPCs", "Cluster15": "Astrocytes (Isocortical)",
                       "Cluster23": "Oligodendrocytes", "Cluster24": "Microglia"},
        "results": results,
        "microglial_enrichment": mg,
        "non_microglial_enrichments": others,
        "max_non_microglial": max(others.values()),
        "ratio_microglia_to_best_other": round(mg / max(others.values()), 4),
        "interpretation_rule_declared_before_the_numbers": (
            "If Cluster24's enrichment falls within the spread of the "
            "non-microglial masks, the enrichment is GENERIC and E's claim must "
            "be weakened to 'contact edges at accessible regulatory elements' "
            "with no microglial qualifier. If Cluster24 is clearly highest, the "
            "microglial reading survives. Neither outcome invalidates the "
            "object; only a claim about it."),
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "gene_annotation_joined": False},
    }
    out["VERDICT"] = ("ENRICHMENT_IS_MICROGLIA_SPECIFIC"
                      if mg > max(others.values())
                      else "ENRICHMENT_IS_GENERIC__WEAKEN_THE_SPECIFICITY_CLAIM")
    with open(os.path.join(a.out_dir, "V61_CROSS_CLUSTER_SPECIFICITY_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nmicroglia {mg:.2f}x vs best non-microglial {max(others.values()):.2f}x"
          f"  ratio {mg/max(others.values()):.2f}")
    print(f"VERDICT: {out['VERDICT']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
