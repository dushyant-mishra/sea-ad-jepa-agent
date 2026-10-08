#!/usr/bin/env python3
"""I-1 pairing witness, rerun at the FULL frozen 200 permutations. Successor.

Responds to canonical audit 4108366746f3157b330880459b4344426f43f29d, which found two
execution/receipt discrepancies in Part 2.

DEFECT S42, MINE, AND NOW LIVING ON CANONICAL. In
scripts/v64/nihcard_e2_outcome_blind_preconditions_v2.py I declared

    N_PERM = 200                      # frozen V2, pairing witness

and then wrote

    perm = [... for _ in range(min(N_PERM, 20))]
    "permutations_per_sample": min(N_PERM, 20)

So the constant said 200, the code did 20, and the emitted artifact truthfully
reported 20 while the frozen contract specified 200. That is worse than an ordinary
drift: a reader checking the constant would conclude the frozen number was honoured.
I capped it for speed and left the cap in.

WHY THIS SUCCESSOR RATHER THAN AN EDIT. The defective executor is on canonical. A lane
must not silently rewrite a canonical executor, so the repair is a successor script
that supersedes the I-1 computation only. Everything else in the preconditions
executor stands.

WHAT CHANGED BESIDES THE COUNT
  - full 200 permutations per sample, as frozen
  - TIE-AWARE AVERAGE RANKS for Spearman (the S35 lesson applied here too; the
    original used a double argsort)
  - permutation is applied to the RANK VECTOR rather than re-ranking a permuted
    value vector. These are identical by construction -- permuting values then
    ranking gives the same multiset in the same order as permuting ranks -- and it
    makes 200 permutations cheap rather than expensive, which is what let the cap
    creep in originally.
  - both frozen arms are run: RNA total_counts x ATAC Unique_nr_frag, and the
    declared second arm RNA n_genes_by_counts x ATAC cisTopic_nr_frag

FROZEN INTERPRETATION, UNCHANGED AND APPLIED AFTER THE FACT TO NOTHING:
  observed far above the permuted null      CORROBORATES nucleus-level alignment
  observed indistinguishable from the null  INCONCLUSIVE, NOT refutation
No effect threshold was predeclared and none is invented here.

FIREWALL. obs metadata only. No gene, no peak, no E2 edge, no correspondence.
TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict

import numpy as np
from scipy.stats import rankdata

N_PERM = 200            # frozen; NOT capped
SEED = 20260929         # frozen
MIN_NUCLEI_PER_SAMPLE = 8


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def corr(a, b):
    ac = a - a.mean()
    bc = b - b.mean()
    d = np.sqrt((ac ** 2).sum() * (bc ** 2).sum())
    return float((ac * bc).sum() / d) if d > 0 else np.nan


def witness(rd, ad, sample, rng, log, label):
    by = defaultdict(list)
    for i, s in enumerate(sample):
        by[s].append(i)
    obs, nulls, per_sample = [], [], {}
    for s, idx in by.items():
        idx = np.asarray(idx)
        if len(idx) < MIN_NUCLEI_PER_SAMPLE:
            continue
        rx = rankdata(rd[idx], method="average")
        ry = rankdata(ad[idx], method="average")
        o = corr(rx, ry)
        if np.isnan(o):
            continue
        # permuting the RANK vector is identical to ranking a permuted value vector
        p = np.array([corr(rx, ry[rng.permutation(len(idx))]) for _ in range(N_PERM)])
        obs.append(o)
        nulls.append(float(np.nanmean(p)))
        per_sample[str(s)] = {"n": int(len(idx)), "observed": float(o),
                              "null_mean": float(np.nanmean(p)),
                              "null_p975": float(np.nanquantile(p, 0.975))}
    obs = np.array(obs)
    nulls = np.array(nulls)
    frac_above = float(np.mean([per_sample[k]["observed"] > per_sample[k]["null_p975"]
                                for k in per_sample]))
    log(f"  [{label}] samples {len(obs):,} | observed median {np.median(obs):+.6f} | "
        f"permuted-null median {np.median(nulls):+.6f} | "
        f"samples with observed above own null p97.5: {frac_above:.4f}")
    return {"samples_evaluated": int(len(obs)),
            "permutations_per_sample": N_PERM,
            "observed_median_spearman": float(np.median(obs)),
            "observed_p25": float(np.quantile(obs, .25)),
            "observed_p75": float(np.quantile(obs, .75)),
            "within_sample_permuted_median": float(np.median(nulls)),
            "permuted_null_min": float(nulls.min()),
            "permuted_null_max": float(nulls.max()),
            "fraction_of_samples_observed_above_own_null_p97_5": frac_above,
            "per_sample": per_sample}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", required=True)
    ap.add_argument("--atac", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    import anndata
    rna = anndata.read_h5ad(a.rna, backed="r")
    atac = anndata.read_h5ad(a.atac, backed="r")
    rn = np.asarray(rna.obs_names, dtype=object)
    an = np.asarray(atac.obs_names, dtype=object)
    sid = atac.obs["sample_id"].astype(str).values

    # R1 exact key recovery, recomputed here so the witness is bound to the same map
    strip = np.array([n[: -(len(s) + 1)] for n, s in zip(an, sid)], dtype=object)
    ridx = {n: i for i, n in enumerate(rn)}
    order = np.array([ridx[x] for x in strip], dtype=int)
    if len(set(order.tolist())) != len(rn):
        raise SystemExit("STOP_R1_NOT_A_BIJECTION")
    log(f"R1 bijection reconfirmed over {len(rn):,} nuclei")

    rng = np.random.default_rng(SEED)
    arms = {}
    arms["primary_total_counts_x_Unique_nr_frag"] = witness(
        rna.obs["total_counts"].astype(float).values[order],
        atac.obs["Unique_nr_frag"].astype(float).values,
        sid, rng, log, "primary")
    arms["second_n_genes_by_counts_x_cisTopic_nr_frag"] = witness(
        rna.obs["n_genes_by_counts"].astype(float).values[order],
        atac.obs["cisTopic_nr_frag"].astype(float).values,
        sid, rng, log, "second ")

    out = {
        "schema": "V64_NIH_CARD_PAIRING_I1_FULL_PERMUTATION_SUCCESSOR_V1",
        "date": "2026-09-30",
        "supersedes_i1_only": "the I-1 block of "
                              "V64_NIH_CARD_E2_OUTCOME_BLIND_PRECONDITIONS_V2.json",
        "responds_to_audit": "4108366746f3157b330880459b4344426f43f29d",
        "S42_defect_repaired": {
            "what": "N_PERM was declared 200 and frozen, then capped to min(N_PERM, 20) "
                    "in the loop and in the emitted field",
            "where": "scripts/v64/nihcard_e2_outcome_blind_preconditions_v2.py lines "
                     "255 and 260, authored by me and now resident on canonical",
            "severity": "the constant said 200 while the code did 20, so a reader "
                        "checking the constant would wrongly conclude the frozen number "
                        "was honoured",
            "repair": "this successor runs the full 200 with no cap",
            "canonical_executor_left_untouched": True},
        "inputs": {
            "rna": {"path": a.rna, "bytes": os.path.getsize(a.rna)},
            "atac": {"path": a.atac, "bytes": os.path.getsize(a.atac)},
            "authenticated_by": "results/v64/V64_NIH_CARD_LOCAL_BYTE_AUTHENTICATION_V1.json"},
        "method": {
            "statistic": "within-sample Spearman via TIE-AWARE AVERAGE RANKS",
            "null": "within-sample permutation, sample identity held fixed",
            "permutations_per_sample": N_PERM, "seed": SEED,
            "min_nuclei_per_sample": MIN_NUCLEI_PER_SAMPLE,
            "permutation_applied_to_rank_vector": True,
            "why_that_is_equivalent": "permuting values then ranking yields the same "
                                      "rank multiset in the same order as permuting the "
                                      "ranks; it is an exact identity, not an "
                                      "approximation, and it is what makes 200 "
                                      "permutations cheap"},
        "arms": arms,
        "frozen_interpretation": {
            "far_above_null": "CORROBORATES nucleus-level alignment",
            "indistinguishable_from_null": "INCONCLUSIVE, NOT refutation",
            "no_effect_threshold_predeclared_or_invented": True},
        "e2_correspondence_outcome_opened": False,
        "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                       "stage_4": "NOT_AUTHORISED"},
    }
    p = os.path.join(a.out_dir,
                     "V64_NIH_CARD_PAIRING_I1_FULL_PERMUTATION_SUCCESSOR_V1.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    log(f"\nwritten {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
