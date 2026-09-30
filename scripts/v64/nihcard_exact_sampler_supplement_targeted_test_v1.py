#!/usr/bin/env python3
"""Targeted real-edge validation of the SUPPLEMENT path. Additional to the contract.

WHY THIS EXISTS. The frozen contract validates the sampler on 32 randomly sampled real
edges. That test executed cleanly, but a measurement made afterwards shows it has almost
no power over the part of the construction that actually needed validating:

    edge-sides in the full build                        41,418
    edge-sides carrying at least one supplement start       76   (0.1835%)
    supplement starts those 76 carry                   177,442

The supplement is extremely concentrated. P(a 64-draw random sample contains no
supplement-contributing edge-side) = 0.889, and indeed the contract run contained none:
the supplement path ran on 3 of 64 comparisons and contributed 0 starts. So the clean
64/64 result validates the AFFINE-INTERIOR shortcut on real data and says essentially
nothing about the supplement.

That matters because the 177,442 recovered starts are the entire justification for the
supplement's existence and for the claim that canonical finding E1 was a real gap.

WHAT THIS TEST ADDS, AND WHAT IT DOES NOT WEAKEN. It samples deterministically from the
76 edge-sides that DO carry supplement starts and runs the identical exact-set-equality
comparison against a full-band real-liftOver oracle. No threshold is relaxed, no gate is
altered, and the contract's own 32-edge requirement stands untouched and already
satisfied. This is strictly additional evidence, added because the coverage gap was
measured rather than because any result was unwelcome.

WHAT IT TESTS THAT IS NOT CIRCULAR. The supplement starts were themselves produced by
pushing candidates through the real binary, so agreement on those starts alone would be
near-tautological. The non-trivial content is the SAFE region: this test enumerates the
whole band, including the positions the affine argument certified WITHOUT consulting
liftOver, and requires the union to match exactly. A safe-region misclassification on an
edge-side that also has supplement material is precisely what no previous test could see.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED. Coordinates and tracks only.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                  # noqa: E402
import nihcard_exact_sampler_qualification_v1 as Q               # noqa: E402

QUAL = "D:/jepa_v5_outputs_20260925/v64_qual"
SUPP = "results/v64/nihcard_exact_supplement"
NIH = "C:/Users/dushy/jepa_c3/nihcard_peaks.bed"
SEED = 20260929
N_TARGET = 8


def supplement_bearing_edge_sides():
    """Every edge-side the committed build recorded as carrying supplement starts."""
    import glob
    out = {}
    for p in sorted(glob.glob(os.path.join(SUPP, "shard_*.json.gz"))):
        for k, v in json.load(gzip.open(p, "rt")).items():
            if v["supp"]:
                out[k] = dict(interior=v["interior"], supp=sorted(v["supp"]))
    return out


def main() -> int:
    workdir = os.path.join(B.WIN, "qualwork_supptarget")
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir)

    bearing = supplement_bearing_edge_sides()
    keys = sorted(bearing, key=lambda k: (int(k.split("|")[0]), int(k.split("|")[1])))
    rng = np.random.default_rng(SEED)
    pick = sorted(rng.choice(len(keys), min(N_TARGET, len(keys)), replace=False))
    chosen = [keys[int(i)] for i in pick]
    print(f"supplement-bearing edge-sides: {len(keys)}; testing {len(chosen)}: {chosen}")

    fchain = f"{B.WIN}/hg19ToHg38.over.chain.gz"
    rchain = f"{B.WIN}/hg38ToHg19.over.chain.gz"
    fwd, rev = B.Idx(B.parse_chain(fchain)), B.Idx(B.parse_chain(rchain))
    pu1, nih = B.load_bed(f"{B.WIN}/ATAC_PU1.bed.gz"), B.load_bed(NIH)

    with gzip.open(B.E2, "rb") as fh:
        raw = fh.read()
    if B.sha_bytes(raw) != B.E2_SHA:
        raise SystemExit("STOP: E2 digest mismatch")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    rows = [l.split("\t") for l in el[1:]]
    by_prom = defaultdict(list)
    for r in rows:
        pk = f'{r[ix["chrom"]]}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
        by_prom[pk].append((int(r[ix["distal_start_hg19"]]),
                            int(r[ix["distal_end_hg19"]])))

    results = []
    for key in chosen:
        i, side = int(key.split("|")[0]), int(key.split("|")[1])
        r = rows[i]
        c = r[ix["chrom"]]
        P = (int(r[ix["promoter_start_hg19"]]) + int(r[ix["promoter_end_hg19"]])) // 2
        d0 = int(r[ix["contact_distance_bp_hg19_source"]])
        tol = max(int(B.DIST_TOL_FRAC * d0), B.DIST_TOL_ABS)
        pk = f'{c}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
        ex = B.norm([(x - Q.W + 1, y - 1) for x, y in by_prom[pk]])
        lo, hi = B.band_of(P, d0, tol, side)
        band = B.sub([(lo, hi)], ex)

        safe, interior = B.safe_and_interior(c, lo, hi, fwd, rev, pu1, nih)
        interior_b = B.inter(interior, band)
        supp_cand = B.sub(band, B.inter(safe, band))
        m = Q.lift_brute(workdir, f"t{i}_{'p' if side > 0 else 'm'}_c", c,
                         Q.enumerate_iv(supp_cand), fchain, rchain, print)
        supp = sorted(s for s, v in m.items()
                      if B.overlaps(pu1, v[0], v[1], v[2])
                      and B.overlaps(nih, v[0], v[1], v[2]))
        A_exact = sorted(set(Q.enumerate_iv(interior_b)) | set(supp))

        om = Q.lift_brute(workdir, f"t{i}_{'p' if side > 0 else 'm'}_o", c,
                          Q.enumerate_iv(band), fchain, rchain, print)
        oracle = sorted(s for s, v in om.items()
                        if B.overlaps(pu1, v[0], v[1], v[2])
                        and B.overlaps(nih, v[0], v[1], v[2]))

        committed = bearing[key]
        rec = dict(comparison_id=key, chrom=c, d0=d0, tol=tol,
                   band_positions=B.card(band),
                   safe_affine_positions=B.card(B.inter(safe, band)),
                   supplement_candidates=B.card(supp_cand),
                   A_interior_card=B.card(interior_b),
                   A_supplement_card=len(supp),
                   A_exact_card=len(A_exact), oracle_card=len(oracle),
                   exact_set_equality=(A_exact == oracle),
                   algebra_only=len(set(A_exact) - set(oracle)),
                   oracle_only=len(set(oracle) - set(A_exact)),
                   supplement_actually_contributed=len(supp) > 0,
                   committed_build_supp_card=len(committed["supp"]),
                   matches_committed_build=(supp == committed["supp"]),
                   share_of_A_exact_from_supplement=(
                       round(len(supp) / len(A_exact), 6) if A_exact else None))
        print(f"  {key} band={rec['band_positions']:,} A={rec['A_exact_card']:,} "
              f"oracle={rec['oracle_card']:,} supp={rec['A_supplement_card']:,} "
              f"eq={rec['exact_set_equality']} matches_build={rec['matches_committed_build']}")
        results.append(rec)

    all_eq = all(r["exact_set_equality"] for r in results)
    all_match = all(r["matches_committed_build"] for r in results)
    contributed = [r for r in results if r["supplement_actually_contributed"]]
    out = dict(
        schema="V64_EXACT_SAMPLER_SUPPLEMENT_TARGETED_TEST_V1", date="2026-09-30",
        status_relative_to_contract="ADDITIONAL. The frozen 32-edge requirement is "
            "untouched and already satisfied; nothing here relaxes a gate.",
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        liftover_sha256=B.sha_file(f"{B.WIN}/liftOver_v479"),
        why_needed=dict(
            supplement_bearing_edge_sides=len(keys), total_edge_sides=41418,
            fraction=round(len(keys) / 41418, 6),
            supplement_starts_they_carry=177442,
            prob_random_64_sample_contains_none=round((1 - len(keys) / 41418) ** 64, 4),
            observed_in_contract_run="supplement path ran on 3 of 64 comparisons and "
                                     "contributed 0 starts"),
        seed=SEED, tested=chosen, results=results,
        all_exact_set_equality=all_eq,
        all_match_committed_build=all_match,
        comparisons_where_supplement_contributed=len(contributed),
        total_supplement_starts_validated=sum(r["A_supplement_card"] for r in results),
        total_band_positions_challenged=sum(r["band_positions"] for r in results),
        what_this_establishes=(
            "On real edge-sides where the supplement genuinely contributes, the union "
            "A_interior + A_supplement equals a full-band real-liftOver enumeration "
            "exactly. The non-trivial content is the safe region, which the affine "
            "argument certified without consulting liftOver; the oracle enumerated it "
            "anyway and agreed."),
        status="PASS" if (all_eq and all_match and contributed) else "FAIL",
        governance=dict(training="OFF", phase_B="STOPPED", stage_4="NOT_AUTHORISED",
                        td60="BLOCKED", Morabito="PROTECTED",
                        correspondence_opened=False))
    with open(os.path.join(QUAL, "edges_supplement_targeted.receipt.json"), "w",
              newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nall_equal={all_eq} all_match_build={all_match} "
          f"contributed={len(contributed)} status={out['status']}")
    shutil.rmtree(workdir, ignore_errors=True)
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
