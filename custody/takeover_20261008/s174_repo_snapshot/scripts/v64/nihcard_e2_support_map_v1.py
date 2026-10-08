#!/usr/bin/env python3
"""LANE D: outcome-blind E2 support / attrition map.

Answers, without ever using the biological correspondence:

    If NIH-CARD later shows weak correspondence, how much of that might be because
    the cohort could not measure E2 adequately?

Two phases:

  PHASE 1  BASELINE_E2_SIDE -- everything computable from committed artifacts alone.
           Runs today. No NIH-CARD bytes required.
  PHASE 2  NIH_CARD_DEPENDENT -- gene resolution, consensus-peak overlap, matched
           controls, per-edge donor counts, metacell support, depth/cohort strata.
           Requires authenticated NIH-CARD bytes and refuses to run without them.

Every phase-2 count must reconcile to 20,709. Edges are never rescued to improve
retention: a low retention number is the answer to the question, not a problem.

NO E2 CORRESPONDENCE OUTCOME IS COMPUTED in either phase. There is no code path in
this file that takes a gene's RNA vector and a distal element's ATAC vector together.

TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from collections import Counter

import numpy as np

E2_EDGES = "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz"
E2_SHA = "bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c"
N_E2 = 20709
RNA_MD5 = "f628b17aab355f80b912e3c715543cbd"
ATAC_MD5 = "b71589e0033e391e2fe97c1ae3928a7f"
RNA_BYTES = 18439154935
ATAC_BYTES = 14508702462


def summarise(v):
    if len(v) == 0:
        return None
    s = np.sort(np.asarray(v, float))
    q = lambda f: float(s[min(len(s) - 1, max(0, int(round(f * (len(s) - 1)))))])
    return {"n": int(len(s)), "min": float(s[0]), "p25": q(.25), "median": q(.50),
            "p75": q(.75), "p95": q(.95), "max": float(s[-1]),
            "mean": float(s.mean())}


def load_edges():
    with gzip.open(E2_EDGES, "rb") as fh:
        raw = fh.read()
    if hashlib.sha256(raw).hexdigest() != E2_SHA:
        raise SystemExit("STOP_E2_EDGE_TABLE_DIGEST")
    lines = raw.decode().rstrip("\n").split("\n")
    hdr = lines[0].split("\t")
    ix = {k: i for i, k in enumerate(hdr)}
    return [{k: f[i] for k, i in ix.items()} for f in (l.split("\t") for l in lines[1:])]


def phase1(edges):
    n = len(edges)
    if n != N_E2:
        raise SystemExit(f"STOP_EDGE_COUNT {n} != {N_E2}")
    genes = Counter(e["nearest_ensembl"] for e in edges)
    proms = Counter((e["chrom"], e["promoter_start_hg38"], e["promoter_end_hg38"])
                    for e in edges)
    d19 = [float(e["contact_distance_bp_hg19_source"]) for e in edges]
    d38 = [float(e["contact_distance_bp"]) for e in edges]
    delta = [b - a for a, b in zip(d19, d38)]
    pk = [float(e["distal_pu1_peak_overlap"]) for e in edges]
    gstat = Counter(e["gene_name_status"] for e in edges)
    deg = [proms[(e["chrom"], e["promoter_start_hg38"], e["promoter_end_hg38"])]
           for e in edges]
    return {
        "e2_edges": n,
        "distinct_genes_nearest_ensembl": len(genes),
        "distinct_promoter_anchors": len(proms),
        "gene_name_status": dict(gstat),
        "genes_with_more_than_one_edge": sum(1 for v in genes.values() if v > 1),
        "edges_in_multi_edge_genes": sum(v for v in genes.values() if v > 1),
        "chromosome_distribution": dict(sorted(Counter(e["chrom"] for e in edges).items())),
        "chromosomes": len(set(e["chrom"] for e in edges)),
        "source_hg19_distance_bp": summarise(d19),
        "harmonised_hg38_distance_bp": summarise(d38),
        "hg38_minus_hg19_distance_bp": summarise(delta),
        "edges_distance_unchanged_by_lift": int(sum(1 for d in delta if d == 0)),
        "edges_abs_distance_change_gt_1000bp": int(sum(1 for d in delta if abs(d) > 1000)),
        "edges_hg38_distance_over_1Mb": int(sum(1 for x in d38 if x > 1e6)),
        "NO_EXCLUSION_ON_HG38_WINDOW": (
            "Edges whose harmonised hg38 separation leaves the hg19 10 kb - 1 Mb source "
            "window are RETAINED. Source hg19 distance is the primary convention; hg38 "
            "is a declared sensitivity."),
        "edges_per_gene": summarise(list(genes.values())),
        "promoter_degree_per_edge": summarise(deg),
        "promoter_degree_per_promoter": summarise(list(proms.values())),
        "nott_pu1_peaks_per_distal_interval": summarise(pk),
    }


def phase2_preflight(rna, atac):
    for name, p, m, b in (("final_rna_data.h5ad", rna, RNA_MD5, RNA_BYTES),
                          ("final_atac_data.h5ad", atac, ATAC_MD5, ATAC_BYTES)):
        if not p or not os.path.exists(p):
            raise SystemExit(f"STOP_PHASE2_REQUIRES_AUTHENTICATED_BYTES: {name} absent")
        if os.path.getsize(p) != b:
            raise SystemExit(f"STOP_TRUNCATED {name}: {os.path.getsize(p)} != {b}")
        h = hashlib.md5()
        with open(p, "rb") as fh:
            for c in iter(lambda: fh.read(1 << 22), b""):
                h.update(c)
        if h.hexdigest() != m:
            raise SystemExit(f"STOP_MD5_MISMATCH {name}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rna", default=None)
    ap.add_argument("--atac", default=None)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    edges = load_edges()
    p1 = phase1(edges)
    print(f"E2 edges {p1['e2_edges']:,} | genes {p1['distinct_genes_nearest_ensembl']:,} "
          f"| promoters {p1['distinct_promoter_anchors']:,} "
          f"| chromosomes {p1['chromosomes']}")
    print(f"source hg19 distance: median {p1['source_hg19_distance_bp']['median']:,.0f} "
          f"range [{p1['source_hg19_distance_bp']['min']:,.0f}, "
          f"{p1['source_hg19_distance_bp']['max']:,.0f}]")
    print(f"distance unchanged by lift: {p1['edges_distance_unchanged_by_lift']:,}; "
          f">1 kb change {p1['edges_abs_distance_change_gt_1000bp']:,}; "
          f">1 Mb after lift {p1['edges_hg38_distance_over_1Mb']}")
    print(f"PU.1 peaks per distal interval: median "
          f"{p1['nott_pu1_peaks_per_distal_interval']['median']:.0f}, max "
          f"{p1['nott_pu1_peaks_per_distal_interval']['max']:.0f}")

    phase2 = {"status": "NOT_RUN__REQUIRES_AUTHENTICATED_NIH_CARD_BYTES",
              "blocking_reason": (
                  "The local final_atac_data.h5ad copy was previously truncated at "
                  "6,059,254,368 of 14,508,702,462 bytes while curl exited 0. Phase 2 "
                  "refuses to run until both files match their published byte length "
                  "AND full-file md5."),
              "required_stages": [
                  "gene resolves to exactly one NIH-CARD var['gene_ids'] entry",
                  "distal interval overlaps >= 1 consensus peak; count per interval",
                  "admissible matched control exists (promoter-fixed, hg19-placed, "
                  "C3-lifted, symmetric NIH-CARD and Nott PU.1 support)",
                  "qualifying donors per edge and metacell-support distribution",
                  "distinct genes and promoter anchors remaining at every stage",
                  "support by donor-depth quartile and by cohort ALWAYS alongside depth",
                  "mutually exclusive reason counts reconciling to 20,709"]}
    if a.rna and a.atac:
        phase2_preflight(a.rna, a.atac)
        phase2["status"] = "AUTHENTICATED__READY"

    out = {"schema": "V64_NIH_CARD_E2_SUPPORT_MAP_V1", "date": "2026-09-29", "lane": "D",
           "e2_edge_table_uncompressed_sha256": E2_SHA,
           "PHASE1_BASELINE_E2_SIDE": p1,
           "PHASE2_NIH_CARD_DEPENDENT": phase2,
           "reconciliation_requirement": "every phase-2 stage must reconcile to 20,709",
           "no_rescue_rule": "edges are never rescued to improve retention; low "
                             "retention is the answer to the question, not a problem",
           "e2_correspondence_outcome_opened": False,
           "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                          "stage_4": "NOT_AUTHORISED",
                          "uses_AD_loci": False, "uses_JEPA_targets": False,
                          "uses_SEA_AD": False, "uses_disease_labels": False}}
    with open(os.path.join(a.out_dir, "V64_NIH_CARD_E2_SUPPORT_MAP_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nphase 2: {phase2['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
