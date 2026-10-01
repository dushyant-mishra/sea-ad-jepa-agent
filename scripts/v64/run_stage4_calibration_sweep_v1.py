#!/usr/bin/env python3
"""Measure how often the frozen decision rule calls a no-effect world significant.

This executes the design frozen in V64_STAGE4_CALIBRATION_PRECOMMIT_V1.json. That file was
written and committed before any draw below was made, and its SHA-256 is recorded in the
output, so the design can be checked against what was actually run rather than taken on
trust. Nothing in this file chooses a threshold, a draw count or an interpretation; all
three come from the pre-commitment.

WHY IT MATTERS. The four-draw robustness run saw the TRUE_NULL world cross LCB95 > 0 once
and the MEASURED_TECHNICAL residue reach significance three times out of four. Those look
alike and are not alike: one is what a 95 percent bound does under a true null, the other
would be a bias surviving the adjustment. Four draws cannot separate them. Rates can.

Every draw is built to disk in the real Phase-B format and run through the real executor
entrypoint. No shortcut path, because a calibration measured on different code would
calibrate different code.
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
PRECOMMIT = "results/v64/phase_b_design/V64_STAGE4_CALIBRATION_PRECOMMIT_V1.json"
OUT = os.path.join(BW.ROOT, "_results")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def one_draw(world, donors, seed_base):
    b = subprocess.run([sys.executable, BUILDER, "--only", world,
                        "--donors", str(donors), "--seed-base", str(seed_base)],
                       capture_output=True, text=True)
    if b.returncode != 0:
        return dict(ok=False, stage="build", err=(b.stdout + b.stderr)[-300:])
    r = subprocess.run([sys.executable, EXEC, "--synthetic-world", world],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return dict(ok=False, stage="run", err=(r.stdout + r.stderr)[-300:])
    R = json.load(open(os.path.join(OUT, "V64_STAGE4_RESULT_%s.json" % world)))
    a = R["ADJUSTED"]["GENE_BALANCED"]
    raw = R["RAW_UNADJUSTED_GENE_BALANCED"]["delta"]
    return dict(ok=True, delta=a["delta"], lcb95=a["lcb95"], raw=raw,
                cvc=R["CONTROL_A_VS_CONTROL_B"]["delta"],
                donors_eligible=R["eligibility"]["donors_eligible"],
                removed=(1.0 - abs(a["delta"]) / abs(raw)) if raw else None)


def main() -> int:
    pc = json.load(open(PRECOMMIT))
    pc_sha = B.sha_file(PRECOMMIT)
    worlds = pc["design"]["worlds"]
    counts = pc["design"]["donor_counts"]
    n_draws = pc["design"]["draws_per_cell"]
    print("executing the pre-committed design %s" % pc_sha[:16])
    print("  worlds=%s donor_counts=%s draws_per_cell=%d total=%d runs"
          % (worlds, counts, n_draws, len(worlds) * len(counts) * n_draws))

    cells, t0 = {}, time.time()
    for world in worlds:
        for donors in counts:
            key = "%s@%d" % (world, donors)
            draws, failures = [], []
            for i in range(n_draws):
                d = one_draw(world, donors, 600000 + 1000 * i)
                (draws if d["ok"] else failures).append(d)
                if (i + 1) % 10 == 0:
                    print("    %-28s %2d/%d  (%.0f s elapsed)"
                          % (key, i + 1, n_draws, time.time() - t0), flush=True)
            # every attempted draw is in the denominator, failures included
            k = sum(1 for d in draws if d["lcb95"] > 0)
            lo, hi = wilson(k, n_draws)
            half = (hi - lo) / 2
            lcb = np.array([d["lcb95"] for d in draws], float)
            dlt = np.array([d["delta"] for d in draws], float)
            cells[key] = dict(
                world=world, donors_configured=donors,
                donors_eligible=draws[0]["donors_eligible"] if draws else None,
                draws_attempted=n_draws, draws_succeeded=len(draws),
                draws_failed=len(failures),
                crossings=k, rate=k / n_draws,
                wilson95=[round(lo, 4), round(hi, 4)],
                half_width=round(half, 4),
                resolution="UNRESOLVED" if half > 0.20 else "RESOLVED",
                delta_median=float(np.median(dlt)) if len(dlt) else None,
                delta_range=[float(dlt.min()), float(dlt.max())] if len(dlt) else None,
                lcb95_median=float(np.median(lcb)) if len(lcb) else None,
                removed_median=(float(np.median([d["removed"] for d in draws
                                                 if d["removed"] is not None]))
                                if world == "MEASURED_TECHNICAL" and draws else None),
                max_abs_control_vs_control=float(np.max(np.abs(
                    [d["cvc"] for d in draws]))) if draws else None,
                failures=[f["err"] for f in failures][:3])
            c = cells[key]
            print("  %-28s %2d/%d crossings  rate=%.3f  Wilson [%.3f, %.3f]  %s"
                  % (key, k, n_draws, c["rate"], lo, hi, c["resolution"]), flush=True)

    # ---------------------------------- read the result against the frozen interpretation
    readings = []
    for donors in counts:
        nul = cells["TRUE_NULL@%d" % donors]
        tec = cells["MEASURED_TECHNICAL@%d" % donors]
        nominal_ok = nul["wilson95"][0] <= 0.05 <= nul["wilson95"][1]
        readings.append(dict(
            donors=donors,
            true_null_rate=nul["rate"], true_null_wilson=nul["wilson95"],
            true_null_consistent_with_nominal_0_05=bool(nominal_ok),
            measured_technical_rate=tec["rate"],
            measured_technical_wilson=tec["wilson95"],
            technical_exceeds_null=bool(tec["wilson95"][0] > nul["wilson95"][1]),
            reading=("the decision rule is calibrated under a true null"
                     if nominal_ok else
                     "the decision rule is ANTI-CONSERVATIVE under a true null, which is "
                     "a defect in the frozen design and is reported, not repaired")))
    if len(counts) == 2:
        a, b = (cells["MEASURED_TECHNICAL@%d" % c] for c in counts)
        direction = ("RISES" if b["rate"] > a["rate"] else
                     "FALLS" if b["rate"] < a["rate"] else "UNCHANGED")
        scale_reading = dict(
            from_donors=counts[0], to_donors=counts[1],
            technical_rate_from=a["rate"], technical_rate_to=b["rate"],
            direction=direction,
            reading=("the residue is a BIAS rather than noise: the bound tightens with n "
                     "while the bias does not, so the real run at 282 donors is MORE "
                     "exposed than the 60-donor qualification suggested"
                     if direction == "RISES" else
                     "the effect behaves like noise and the reduced-scale qualification "
                     "was conservative" if direction == "FALLS" else
                     "no change in rate across donor count"))
    else:
        scale_reading = None

    # ------------------------------------------------- restore the canonical worlds
    print("")
    print("restoring the canonical worlds ...")
    subprocess.run([sys.executable, BUILDER, "--seed-base",
                    str(BW.CANONICAL_SEED_BASE)], capture_output=True, text=True)
    restored = {}
    for w in BW.WORLDS:
        mp = os.path.join(BW.ROOT, w, "WORLD_MANIFEST.json")
        m = json.load(open(mp))
        restored[w] = dict(
            seed=m["seed"], eligible_donors=m["geometry"]["eligible_donors"],
            digests_match=all(B.sha_file(os.path.join(BW.ROOT, w, f)) == d
                              for f, d in m["digests"].items()))
    canonical_ok = all(v["digests_match"] and v["eligible_donors"] == 60
                       for v in restored.values())
    print("  canonical state restored and digest-verified: %s" % canonical_ok)

    out = dict(
        schema="V64_STAGE4_CALIBRATION_SWEEP_V1", date="2026-10-01",
        executes_precommitment=dict(path=PRECOMMIT, sha256=pc_sha),
        design_was_frozen_before_any_draw=True,
        thresholds_or_draw_counts_changed_after_seeing_results=False,
        cells=cells, readings=readings, scale_reading=scale_reading,
        canonical_worlds_restored=restored,
        canonical_state_verified=canonical_ok,
        what_this_cannot_establish=pc["what_this_cannot_establish"],
        wall_clock_seconds=round(time.time() - t0, 1),
        real_substrate_read=False, computed_correspondence_values=0,
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        status="COMPLETE" if canonical_ok else "CANONICAL_RESTORE_FAILED")
    p = "results/v64/phase_b_design/V64_STAGE4_CALIBRATION_SWEEP_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    for r in readings:
        print("  %d donors: true-null %.3f %s | technical %.3f %s | technical>null=%s"
              % (r["donors"], r["true_null_rate"], r["true_null_wilson"],
                 r["measured_technical_rate"], r["measured_technical_wilson"],
                 r["technical_exceeds_null"]))
    if scale_reading:
        print("  technical rate %d -> %d donors: %.3f -> %.3f  %s"
              % (scale_reading["from_donors"], scale_reading["to_donors"],
                 scale_reading["technical_rate_from"],
                 scale_reading["technical_rate_to"], scale_reading["direction"]))
    print("receipt sha256 " + B.sha_file(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
