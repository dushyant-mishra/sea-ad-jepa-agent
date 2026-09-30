#!/usr/bin/env python3
"""Positive control: prove the real-edge equality test CAN fail, on a real edge.

THE FAILURE MODE THIS GUARDS AGAINST. A comparison that reports 64/64 EQUAL is worthless
if it would report EQUAL no matter what the sampler produced. The fixtures already show
the comparator firing (F3 returned FAIL on the pre-S50 code), but the fixtures run on
synthetic 400 kb chains with hand-built tracks. This control runs the comparator on a
REAL edge-side, at real band scale, against the real liftOver oracle, and injects known
divergences to confirm both directions are detected.

THE DESIGN. Pick the real edge-side with the largest non-empty oracle among the 32
sampled edges. Compute A_exact and the oracle exactly as the qualification does, confirm
they agree, then form three mutants of A_exact:

  DROP     remove one admissible start   -> must show oracle_only = 1
  INJECT   add one start the oracle rejected -> must show algebra_only = 1
  BOTH     do both                       -> must show 1 and 1

If any mutant still compares EQUAL, the comparator is blind in that direction and the
whole 64/64 result is uninterpretable. The injected start is drawn from the band
positions the oracle actually rejected, so it is a genuine near-miss rather than an
absurd value a weaker test might catch by accident.

TRAINING=OFF. PHASE B=STOPPED. Coordinates and tracks only.
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
NIH = "C:/Users/dushy/jepa_c3/nihcard_peaks.bed"


def main() -> int:
    workdir = os.path.join(B.WIN, "qualwork_poscontrol")
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir)

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

    # choose the target from the completed shard receipts: largest non-empty oracle
    best = None
    for s in range(4):
        p = os.path.join(QUAL, f"edges_s{s:02d}.receipt.json")
        if not os.path.exists(p):
            continue
        for c in json.load(open(p))["edge_side_checks"]:
            if c.get("oracle_card", 0) > 0 and (best is None or
                                                c["oracle_card"] > best["oracle_card"]):
                best = c
    if best is None:
        raise SystemExit("STOP: no non-empty comparison available to control against")

    i, side = best["edge_index"], best["side"]
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
    m = Q.lift_brute(workdir, "pc_c", c, Q.enumerate_iv(supp_cand), fchain, rchain, print)
    supp = sorted(s for s, v in m.items()
                  if B.overlaps(pu1, v[0], v[1], v[2])
                  and B.overlaps(nih, v[0], v[1], v[2]))
    A_exact = sorted(set(Q.enumerate_iv(interior_b)) | set(supp))

    om = Q.lift_brute(workdir, "pc_o", c, Q.enumerate_iv(band), fchain, rchain, print)
    oracle = sorted(s for s, v in om.items()
                    if B.overlaps(pu1, v[0], v[1], v[2])
                    and B.overlaps(nih, v[0], v[1], v[2]))

    baseline_equal = A_exact == oracle
    band_all = set(Q.enumerate_iv(band))
    rejected = sorted(band_all - set(oracle))
    if not baseline_equal or not A_exact or not rejected:
        raise SystemExit(f"STOP: control target unusable "
                         f"(equal={baseline_equal} |A|={len(A_exact)} "
                         f"|rejected|={len(rejected)})")

    rng = np.random.default_rng(20260929)
    dropped = int(A_exact[int(rng.integers(0, len(A_exact)))])
    injected = int(rejected[int(rng.integers(0, len(rejected)))])

    def compare(mut):
        return dict(equal=(sorted(mut) == oracle),
                    algebra_only=len(set(mut) - set(oracle)),
                    oracle_only=len(set(oracle) - set(mut)))

    mut_drop = [x for x in A_exact if x != dropped]
    mut_inject = sorted(A_exact + [injected])
    mut_both = sorted([x for x in A_exact if x != dropped] + [injected])
    res = dict(DROP=compare(mut_drop), INJECT=compare(mut_inject),
               BOTH=compare(mut_both))

    ok = (res["DROP"] == dict(equal=False, algebra_only=0, oracle_only=1)
          and res["INJECT"] == dict(equal=False, algebra_only=1, oracle_only=0)
          and res["BOTH"] == dict(equal=False, algebra_only=1, oracle_only=1))

    rec = dict(
        schema="V64_EXACT_SAMPLER_REAL_EDGE_POSITIVE_CONTROL_V1", date="2026-09-30",
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        target=dict(comparison_id=f"e{i}|{side:+d}", chrom=c, d0=d0, tol=tol,
                    band_positions=B.card(band), A_exact_card=len(A_exact),
                    oracle_card=len(oracle),
                    why_this_one="largest non-empty oracle among the 32 sampled edges, "
                                 "so the control runs at the largest real scale available"),
        baseline_unmutated_equal=baseline_equal,
        band_positions_the_oracle_REJECTED=len(rejected),
        mutations=dict(dropped_admissible_start=dropped,
                       injected_start_the_oracle_rejected=injected,
                       injected_is_a_genuine_near_miss=True,
                       note="the injected start lies inside the same band and failed the "
                            "real liftOver gates, so detecting it requires the comparator "
                            "to be exact rather than merely plausible"),
        results=res,
        expected=dict(DROP=dict(equal=False, algebra_only=0, oracle_only=1),
                      INJECT=dict(equal=False, algebra_only=1, oracle_only=0),
                      BOTH=dict(equal=False, algebra_only=1, oracle_only=1)),
        sensitivity_retained=ok,
        interpretation=("The comparator detects a single missing start and a single "
                        "spurious start, in both directions, on a real edge-side at "
                        "full band scale. The 64/64 equality result is therefore a "
                        "measurement and not a tautology."
                        if ok else
                        "STOP. The comparator failed to detect an injected divergence, "
                        "so the 64/64 equality result cannot be interpreted."),
        governance=dict(training="OFF", phase_B="STOPPED", stage_4="NOT_AUTHORISED",
                        td60="BLOCKED", Morabito="PROTECTED",
                        correspondence_opened=False))
    with open(os.path.join(QUAL, "edges_positive_control.receipt.json"), "w",
              newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print(json.dumps({k: rec[k] for k in
                      ("target", "baseline_unmutated_equal", "results",
                       "sensitivity_retained")}, indent=2))
    shutil.rmtree(workdir, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
