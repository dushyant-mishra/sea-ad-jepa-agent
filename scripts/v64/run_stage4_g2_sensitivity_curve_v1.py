#!/usr/bin/env python3
"""Does G2 detect cross-modal confounding, or only structure shared across edges?

Executes the design frozen in V64_STAGE4_G2_SENSITIVITY_PRECOMMIT_V1.json, bound here by
SHA-256. Nothing in this file chooses a K value, a draw count or an interpretation.

The V2 calibration showed the control-versus-control gate rejecting the hidden-confound
world most of the time, which looked like protection. But that world's confound is a
SINGLE factor shared by every edge, and a contrast between two independent control draws
is exactly the instrument that sees shared structure. This varies K, the number of
independent confound factors, and watches what G2 does.

The degenerate end is a tautology and is labelled as one: at K equal to the edge count,
every edge has its own metacell-varying cross-modal factor, which is the same statistical
object as the planted biology. A low rejection rate there is not a defect.

No real substrate is read. No correspondence value is computed on real data.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import build_stage4_synthetic_worlds_v1 as BW                        # noqa: E402

EXEC = "scripts/v64/stage4_executor_v1.py"
BUILDER = "scripts/v64/build_stage4_synthetic_worlds_v1.py"
PRECOMMIT = "results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_PRECOMMIT_V1.json"
WORLD = "HIDDEN_CONFOUND_K"
OUT = os.path.join(BW.ROOT, "_results")
G1 = "G1_PRIMARY_LCB95_ABOVE_ZERO"
G2 = "G2_CONTROL_VS_CONTROL_NOT_DISTINGUISHABLE_FROM_ZERO"
G3 = "G3_COVARIATE_BALANCE"
BIOLOGY_MEDIAN_DELTA_AT_282 = 0.5692     # measured in the V2 sweep, not re-derived here
BIOLOGY_G2_RATE_AT_282 = 0.62            # the rate G2 passes on GENUINE biology


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def one_draw(K, donors, seed_base):
    b = subprocess.run([sys.executable, BUILDER, "--only", WORLD, "--confound-blocks",
                        str(K), "--donors", str(donors), "--seed-base", str(seed_base)],
                       capture_output=True, text=True)
    if b.returncode != 0:
        txt = b.stdout + b.stderr
        if "violates the frozen control construction" in txt:
            raise SystemExit("STOP: world build violated the frozen matching rule. "
                             "Repair the generator; do not exclude the draw.\n"
                             + txt[-400:])
        return dict(ok=False, err=txt[-300:])
    r = subprocess.run([sys.executable, EXEC, "--synthetic-world", WORLD],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return dict(ok=False, err=(r.stdout + r.stderr)[-300:])
    R = json.load(open(os.path.join(OUT, "V64_STAGE4_RESULT_%s.json" % WORLD)))
    g, a = R["FIVE_GATE_DECISION"], R["ADJUSTED"]["GENE_BALANCED"]
    man = R["world_manifest"]["planted_truth"]
    return dict(ok=True, all_five=bool(g["ALL_FIVE_PASS"]),
                g1=bool(g[G1]["passed"]), g2=bool(g[G2]["passed"]),
                g3=bool(g[G3]["passed"]), delta=a["delta"], lcb95=a["lcb95"],
                cvc=R["CONTROL_A_VS_CONTROL_B"]["delta"],
                K_in_manifest=man.get("confound_blocks_K"))


def main() -> int:
    pc = json.load(open(PRECOMMIT))
    pc_sha = B.sha_file(PRECOMMIT)
    Ks = pc["design"]["K_values"]
    donors = pc["design"]["donor_count"]
    n_draws = pc["design"]["draws_per_K"]
    print("executing pre-committed design %s" % pc_sha[:16])
    print("  K values %s at %d donors, %d draws each, %d runs"
          % (Ks, donors, n_draws, len(Ks) * n_draws))

    cells, t0 = {}, time.time()
    for K in Ks:
        ok, bad = [], []
        for i in range(n_draws):
            d = one_draw(K, donors, 800000 + 1000 * i)
            (ok if d["ok"] else bad).append(d)
            if (i + 1) % 10 == 0:
                print("    K=%-4d %2d/%d (%.0f s)" % (K, i + 1, n_draws,
                                                      time.time() - t0), flush=True)
        mismatched = [d["K_in_manifest"] for d in ok if d["K_in_manifest"] != K]
        if mismatched:
            raise SystemExit("STOP: the manifest reports K=%s where %d was requested. "
                             "A fixture that does not build what it was asked for makes "
                             "every rate meaningless." % (mismatched[:3], K))
        g2k = sum(1 for d in ok if d["g2"])
        lo, hi = wilson(g2k, n_draws)
        dl = np.array([d["delta"] for d in ok], float)
        cells[str(K)] = dict(
            K=K, edges_per_block=round(BW.N_EDGES / K, 2),
            draws_attempted=n_draws, draws_succeeded=len(ok), draws_failed=len(bad),
            g2_pass_count=g2k, g2_pass_rate=g2k / n_draws,
            g2_wilson95=[round(lo, 4), round(hi, 4)],
            resolution="UNRESOLVED" if (hi - lo) / 2 > 0.25 else "RESOLVED",
            g1_pass_rate=sum(1 for d in ok if d["g1"]) / n_draws,
            g3_pass_rate=sum(1 for d in ok if d["g3"]) / n_draws,
            all_five_pass_rate=sum(1 for d in ok if d["all_five"]) / n_draws,
            delta_median=float(np.median(dl)) if dl.size else None,
            delta_ratio_to_biology=round(float(np.median(dl))
                                         / BIOLOGY_MEDIAN_DELTA_AT_282, 4)
            if dl.size else None,
            control_vs_control_median=float(np.median([abs(d["cvc"]) for d in ok]))
            if ok else None,
            failures=[d["err"] for d in bad][:2])
        c = cells[str(K)]
        print("  K=%-4d (%.0f edges/block)  G2 pass %2d/%d = %.3f  Wilson [%.3f, %.3f]"
              "  ALL_FIVE %.3f  |cvc| med %.4f"
              % (K, c["edges_per_block"], g2k, n_draws, c["g2_pass_rate"], lo, hi,
                 c["all_five_pass_rate"], c["control_vs_control_median"]), flush=True)

    rates = [cells[str(K)]["g2_pass_rate"] for K in Ks]
    monotone = all(rates[i] <= rates[i + 1] + 1e-12 for i in range(len(rates) - 1))
    top = cells[str(Ks[-1])]
    converges = abs(top["g2_pass_rate"] - BIOLOGY_G2_RATE_AT_282) <= 0.20
    if monotone and converges:
        reading = ("G2 responds to SHARED structure across edges, not to cross-modal "
                   "confounding as such. At K equal to the edge count it passes the "
                   "confounded world at the rate it passes genuine biology, so it "
                   "contributes nothing against an edge-specific cross-modal artifact. "
                   "The V2 hidden-confound rejection rate must not be cited as a "
                   "safeguard.")
    elif not monotone:
        reading = ("the G2 pass rate is NOT monotone in K. The gate responds to something "
                   "neither hypothesis predicts and no protection claim may be made in "
                   "either direction until it is understood.")
    else:
        reading = ("G2 keeps rejecting the confounded world even as the confound becomes "
                   "edge-specific, so it detects something other than sharing and offers "
                   "real protection. The V2 caveat is discharged.")

    print("")
    print("restoring the canonical worlds ...")
    subprocess.run([sys.executable, BUILDER, "--seed-base",
                    str(BW.CANONICAL_SEED_BASE)], capture_output=True, text=True)
    restored = {}
    for w in BW.WORLDS:
        m = json.load(open(os.path.join(BW.ROOT, w, "WORLD_MANIFEST.json")))
        restored[w] = dict(seed=m["seed"],
                           eligible_donors=m["geometry"]["eligible_donors"],
                           digests_match=all(B.sha_file(os.path.join(BW.ROOT, w, f)) == d
                                             for f, d in m["digests"].items()))
    canonical_ok = all(v["digests_match"] and v["eligible_donors"] == 60
                       for v in restored.values())
    print("  canonical four restored and digest-verified: %s" % canonical_ok)

    out = dict(
        schema="V64_STAGE4_G2_SENSITIVITY_CURVE_V1", date="2026-10-02",
        executes_precommitment=dict(path=PRECOMMIT, sha256=pc_sha),
        design_was_frozen_before_any_draw=True,
        thresholds_or_draw_counts_changed_after_seeing_results=False,
        reference_values_from_the_V2_sweep=dict(
            biology_g2_pass_rate_at_282=BIOLOGY_G2_RATE_AT_282,
            biology_median_delta_at_282=BIOLOGY_MEDIAN_DELTA_AT_282,
            note="measured in V64_STAGE4_CALIBRATION_SWEEP_V2, not re-derived here"),
        donor_count=donors, draws_per_K=n_draws, cells=cells,
        g2_rate_monotone_in_K=monotone,
        g2_rate_at_max_K_converges_on_biology_rate=converges,
        READING=reading,
        degenerate_end_note="at K equal to the edge count the confounded world is the "
                            "same statistical object as the planted biology, so a low "
                            "rejection rate there is a tautology and not a defect",
        what_this_cannot_establish=pc["what_this_cannot_establish"],
        canonical_four_restored=restored, canonical_state_verified=canonical_ok,
        wall_clock_seconds=round(time.time() - t0, 1),
        real_substrate_read=False, computed_correspondence_values=0,
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        status="COMPLETE" if canonical_ok else "CANONICAL_RESTORE_FAILED")
    p = "results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_CURVE_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print("G2 pass rate by K: " + "  ".join("%d:%.2f" % (K, cells[str(K)]["g2_pass_rate"])
                                            for K in Ks))
    print("monotone in K: %s | converges on the biology rate of %.2f: %s"
          % (monotone, BIOLOGY_G2_RATE_AT_282, converges))
    print("receipt sha256 " + B.sha_file(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
