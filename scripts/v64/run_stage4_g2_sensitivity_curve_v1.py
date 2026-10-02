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
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import build_stage4_synthetic_worlds_v1 as BW                        # noqa: E402

EXEC = "scripts/v64/stage4_executor_v1.py"
BUILDER = "scripts/v64/build_stage4_synthetic_worlds_v1.py"
PRECOMMIT = "results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_PRECOMMIT_V1.json"
WORLD = "HIDDEN_CONFOUND_K"
OUT = os.path.join(BW.ROOT, "_results")


def run_id_for(K, draw_index, seed_base):
    """Deterministic scientific run identity, independent of worker/completion order."""
    rid = "g2_k%03d_d%02d_s%06d" % (int(K), int(draw_index), int(seed_base))
    if len(rid) > 40 or not rid.replace("_", "").isalnum():
        raise ValueError("run id violates the executor's bounded synthetic namespace")
    return rid
G1 = "G1_PRIMARY_LCB95_ABOVE_ZERO"
G2 = "G2_CONTROL_VS_CONTROL_NOT_DISTINGUISHABLE_FROM_ZERO"
G3 = "G3_COVARIATE_BALANCE"
BIOLOGY_MEDIAN_DELTA_AT_282 = 0.5692     # measured in the V2 sweep, not re-derived here
BIOLOGY_G2_RATE_AT_282 = 0.62            # the rate G2 passes on GENUINE biology
BIOLOGY_G2_COUNT_AT_282 = (25, 40)       # the draws behind it, so its own interval is used


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def one_draw(K, donors, seed_base, draw_index):
    run_id = run_id_for(K, draw_index, seed_base)
    env = dict(os.environ, JEPA_SYNTHETIC_RUN_ID=run_id)
    b = subprocess.run([sys.executable, BUILDER, "--only", WORLD, "--confound-blocks",
                        str(K), "--donors", str(donors), "--seed-base", str(seed_base)],
                       capture_output=True, text=True, env=env)
    if b.returncode != 0:
        txt = b.stdout + b.stderr
        if "violates the frozen control construction" in txt:
            raise SystemExit("STOP: world build violated the frozen matching rule. "
                             "Repair the generator; do not exclude the draw.\n"
                             + txt[-400:])
        return dict(ok=False, err=txt[-300:])
    r = subprocess.run([sys.executable, EXEC, "--synthetic-world", WORLD],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        return dict(ok=False, err=(r.stdout + r.stderr)[-300:])
    run_root = os.path.join(BW.ROOT, "_runs", run_id)
    result_path = os.path.join(run_root, "_results",
                               "V64_STAGE4_RESULT_%s.json" % WORLD)
    R = json.load(open(result_path))
    g, a = R["FIVE_GATE_DECISION"], R["ADJUSTED"]["GENE_BALANCED"]
    man = R["world_manifest"]["planted_truth"]
    return dict(ok=True, all_five=bool(g["ALL_FIVE_PASS"]),
                g1=bool(g[G1]["passed"]), g2=bool(g[G2]["passed"]),
                g3=bool(g[G3]["passed"]), delta=a["delta"], lcb95=a["lcb95"],
                cvc=R["CONTROL_A_VS_CONTROL_B"]["delta"],
                K_in_manifest=man.get("confound_blocks_K"),
                partition_semantics=man.get("partition_semantics"),
                realised_occupied_factors=man.get("realised_occupied_factors"),
                block_size_min=man.get("block_size_min"),
                block_size_max=man.get("block_size_max"),
                endpoint_singletons_verified=man.get("endpoint_singletons_verified"),
                run_id=run_id, draw_index=draw_index, seed_base=seed_base,
                result_path=result_path, result_sha256=B.sha_file(result_path))


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
    workers = max(1, int(os.environ.get("V64_G2_WORKERS", "1")))
    print("  workers=%d; worker identity/completion order do not enter run identity" % workers)
    for K in Ks:
        specs = [(i, 800000 + 1000 * i) for i in range(n_draws)]
        completed = {}
        if workers == 1:
            for i, seed in specs:
                completed[i] = one_draw(K, donors, seed, i)
                if (i + 1) % 10 == 0:
                    print("    K=%-4d %2d/%d (%.0f s)" % (
                        K, i + 1, n_draws, time.time() - t0), flush=True)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(one_draw, K, donors, seed, i): i
                           for i, seed in specs}
                done = 0
                for fut in as_completed(futures):
                    i = futures[fut]
                    try:
                        completed[i] = fut.result()
                    except Exception as e:
                        completed[i] = dict(ok=False, err="worker exception: %r" % e,
                                            draw_index=i,
                                            seed_base=800000 + 1000 * i,
                                            run_id=run_id_for(
                                                K, i, 800000 + 1000 * i))
                    done += 1
                    if done % 10 == 0:
                        print("    K=%-4d %2d/%d (%.0f s)" % (
                            K, done, n_draws, time.time() - t0), flush=True)
        ordered = [completed[i] for i, _ in specs]
        ok = [d for d in ordered if d["ok"]]
        bad = [d for d in ordered if not d["ok"]]
        if len({d.get("run_id") for d in ordered}) != len(ordered):
            raise SystemExit("STOP: duplicate synthetic run id across draws")
        mismatched = [d["K_in_manifest"] for d in ok if d["K_in_manifest"] != K]
        if mismatched:
            raise SystemExit("STOP: the manifest reports K=%s where %d was requested. "
                             "A fixture that does not build what it was asked for makes "
                             "every rate meaningless." % (mismatched[:3], K))
        occupancy_bad = [
            d for d in ok
            if d["partition_semantics"] != "EXACT_K_OCCUPIED_BALANCED_BLOCKS"
            or d["realised_occupied_factors"] != K
            or d["block_size_min"] is None or d["block_size_max"] is None
            or d["block_size_max"] - d["block_size_min"] > 1
            or (K == BW.N_EDGES and d["endpoint_singletons_verified"] is not True)
        ]
        if occupancy_bad:
            raise SystemExit("STOP: repaired exact-K geometry guard failed: %s"
                             % occupancy_bad[0])
        g2k = sum(1 for d in ok if d["g2"])
        lo, hi = wilson(g2k, n_draws)
        dl = np.array([d["delta"] for d in ok], float)
        cells[str(K)] = dict(
            K=K, edges_per_block_nominal=round(BW.N_EDGES / K, 2),
            partition_semantics="EXACT_K_OCCUPIED_BALANCED_BLOCKS",
            realised_occupied_factors=(K if ok else None),
            block_size_min=(min(d["block_size_min"] for d in ok) if ok else None),
            block_size_max=(max(d["block_size_max"] for d in ok) if ok else None),
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
              % (K, c["edges_per_block_nominal"], g2k, n_draws, c["g2_pass_rate"], lo, hi,
                 c["all_five_pass_rate"], c["control_vs_control_median"]), flush=True)

    rates = [cells[str(K)]["g2_pass_rate"] for K in Ks]
    monotone = all(rates[i] <= rates[i + 1] + 1e-12 for i in range(len(rates) - 1))
    top = cells[str(Ks[-1])]
    # AMENDMENT_1: convergence is interval overlap, not a band I chose. The reference has
    # its own uncertainty -- 25 of 40 draws -- and ignoring it would hold the measurement
    # to a precision the reference does not have.
    bio_lo, bio_hi = wilson(*BIOLOGY_G2_COUNT_AT_282)
    k_lo, k_hi = top["g2_wilson95"]
    converges = not (k_hi < bio_lo or k_lo > bio_hi)
    if monotone and converges:
        reading = ("Under the HISTORICAL EXECUTOR'S current G2 implementation, "
                   "the repaired exact-K curve is monotone and its K=max interval overlaps "
                   "the biology reference. This characterises that implementation only. "
                   "S102 remains open: no final Stage-4 G2 rule, equivalence margin or "
                   "regulatory safeguard is established by this curve.")
    elif not monotone:
        reading = ("the G2 pass rate is NOT monotone in K. The gate responds to something "
                   "neither hypothesis predicts and no protection claim may be made in "
                   "either direction until it is understood.")
    else:
        reading = ("Under the HISTORICAL EXECUTOR'S current G2 implementation, "
                   "G2 continues to reject the repaired confound family. This is an "
                   "operating characteristic, not proof of final Stage-4 protection; "
                   "S102 remains open and the scientific G2 rule is still unspecified.")

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
        schema="V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED", date="2026-10-02",
        historical_v1_preserved=True,
        historical_v1_scope=("V1 remains a measurement of the sampling-with-replacement "
                             "factor-pool generator and is not an exact-K partition curve"),
        execution_workers=workers,
        synthetic_run_namespace="JEPA_SYNTHETIC_RUN_ID",
        S102_status="OPEN__CURVE_CHARACTERISES_HISTORICAL_EXECUTOR_G2_ONLY",
        executes_precommitment=dict(path=PRECOMMIT, sha256=pc_sha),
        design_was_frozen_before_any_draw=True,
        thresholds_or_draw_counts_changed_after_seeing_results=False,
        convergence_test=dict(
            definition="the K=max cell's Wilson 95 percent interval overlaps the biology "
                       "reference's Wilson 95 percent interval",
            frozen_in="AMENDMENT_1 of the pre-commitment, before any draw",
            biology_reference_interval=[round(bio_lo, 4), round(bio_hi, 4)],
            k_max_interval=top["g2_wilson95"],
            THIS_TEST_IS_WEAK_AND_IS_NOT_THE_PRIMARY_EVIDENCE=
                "with 20 draws per cell against a 25-of-40 reference, the overlap test "
                "fails only if the K=max rate lands at or below about 3 of 20 or at 20 of "
                "20. It therefore declares convergence across most of the range and must "
                "be read as corroboration, never as confirmation. The PRIMARY evidence is "
                "the SHAPE of the curve across all five K values: a monotone rise from "
                "near the V2 hidden-confound rate to near the biology rate is "
                "unmistakable in a way a single endpoint comparison is not, and the "
                "reading below requires monotonicity AND overlap together."),
        reference_values_from_the_V2_sweep=dict(
            biology_g2_pass_rate_at_282=BIOLOGY_G2_RATE_AT_282,
            biology_draws_behind_it="25 of 40",
            biology_median_delta_at_282=BIOLOGY_MEDIAN_DELTA_AT_282,
            note="measured in V64_STAGE4_CALIBRATION_SWEEP_V2, not re-derived here"),
        donor_count=donors, draws_per_K=n_draws, cells=cells,
        primary_evidence="the shape of the G2 pass rate across the five K values",
        corroborating_evidence="the endpoint overlap test, which is weak by construction",
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
    p = "results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED.json"
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
